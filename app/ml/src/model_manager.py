"""
Hybrid Model Manager for Demand Prediction
==========================================
Orchestrates the ML model maintenance lifecycle:
- Weekly fine-tuning on new data
- Quarterly full retraining
- Emergency retrains on performance degradation
- Automatic version management

This is the main entry point for scheduled model maintenance.

Usage:
    # Run from command line
    python src/model_manager.py --update
    
    # Or programmatically
    from src.model_manager import HybridModelManager
    manager = HybridModelManager()
    manager.update_model()
"""

import os
import sys
import json
import shutil
import subprocess
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, Optional, Tuple
import joblib

# Add parent directory to path for running as script
_current_dir = Path(__file__).resolve().parent
_parent_dir = _current_dir.parent
if str(_parent_dir) not in sys.path:
    sys.path.insert(0, str(_parent_dir))


class HybridModelManager:
    """
    Manages the hybrid training strategy:
    - Tier 1: Weekly fine-tuning (fast, ~5-10 min)
    - Tier 2: Quarterly full retraining (thorough, ~30-60 min)
    - Tier 3: Emergency retraining on critical drift
    
    Attributes:
        model_dir: Directory containing model files
        logs_dir: Directory for logs
        full_retrain_interval_days: Days between full retrains
        fine_tune_interval_days: Days between fine-tunes
        drift_threshold_pct: % degradation to trigger retrain
    """
    
    def __init__(self,
                 model_dir: str = "data/models",
                 logs_dir: str = "logs",
                 full_retrain_interval_days: int = 90,
                 fine_tune_interval_days: int = 7,
                 drift_threshold_pct: float = 15.0,
                 critical_drift_pct: float = 25.0):
        """
        Initialize the hybrid model manager.
        
        Args:
            model_dir: Directory containing model files
            logs_dir: Directory for logs
            full_retrain_interval_days: Days between full retrains (default: 90)
            fine_tune_interval_days: Days between fine-tunes (default: 7)
            drift_threshold_pct: % degradation to suggest retraining
            critical_drift_pct: % degradation to force full retrain
        """
        self.model_dir = Path(model_dir)
        self.logs_dir = Path(logs_dir)
        self.full_retrain_interval = full_retrain_interval_days
        self.fine_tune_interval = fine_tune_interval_days
        self.drift_threshold = drift_threshold_pct
        self.critical_drift = critical_drift_pct
        
        # Ensure directories exist
        self.model_dir.mkdir(parents=True, exist_ok=True)
        self.logs_dir.mkdir(parents=True, exist_ok=True)
        (self.model_dir / "archive").mkdir(exist_ok=True)
        
        # Load state
        self.state_path = self.logs_dir / "model_manager_state.json"
        self.state = self._load_state()
        
        print(f"📊 HybridModelManager initialized")
        print(f"   Full retrain interval: {full_retrain_interval_days} days")
        print(f"   Fine-tune interval: {fine_tune_interval_days} days")
    
    def _load_state(self) -> Dict:
        """Load manager state from file."""
        if self.state_path.exists():
            with open(self.state_path, 'r') as f:
                return json.load(f)
        
        return {
            'last_full_retrain': None,
            'last_fine_tune': None,
            'fine_tune_count_since_retrain': 0,
            'total_updates': 0,
            'last_update_type': None,
            'last_update_time': None
        }
    
    def _save_state(self) -> None:
        """Save manager state to file."""
        with open(self.state_path, 'w') as f:
            json.dump(self.state, f, indent=2)
    
    def _get_model_metadata(self) -> Dict:
        """Get current model metadata."""
        metadata_path = self.model_dir / "rf_model_metadata.json"
        
        if metadata_path.exists():
            try:
                with open(metadata_path, 'r') as f:
                    return json.load(f)
            except Exception:
                # Fallback to joblib for legacy format
                try:
                    return joblib.load(metadata_path)
                except Exception:
                    pass
        
        return {}
    
    def _get_health_report(self) -> Dict:
        """Get model health from monitor."""
        try:
            from src.model_monitor import ModelMonitor
            monitor = ModelMonitor()
            return monitor.get_model_health(days=7)
        except Exception as e:
            print(f"⚠️  Could not get health report: {e}")
            return {'healthy': True, 'needs_retrain': False, 'status': 'unknown'}
    
    def should_full_retrain(self) -> Tuple[bool, str]:
        """
        Determine if full retraining is needed.
        
        Returns:
            Tuple of (should_retrain, reason)
        """
        # Check 1: Critical performance degradation
        health = self._get_health_report()
        if health.get('metrics', {}).get('avg_degradation_pct', 0) >= self.critical_drift:
            return True, f"Critical drift detected ({health['metrics']['avg_degradation_pct']:.1f}%)"
        
        # Check 2: Time since last full retrain
        metadata = self._get_model_metadata()
        training_date_str = metadata.get('training_date')
        
        if training_date_str:
            try:
                # Handle both date and datetime formats
                if 'T' in training_date_str:
                    training_date = datetime.fromisoformat(training_date_str).date()
                else:
                    training_date = datetime.strptime(training_date_str, '%Y-%m-%d').date()
                
                days_since = (datetime.now().date() - training_date).days
                
                if days_since >= self.full_retrain_interval:
                    return True, f"Time for scheduled retrain ({days_since} days since last)"
            except (ValueError, TypeError):
                pass
        
        # Check 3: Too many fine-tunes without full retrain
        fine_tune_count = self.state.get('fine_tune_count_since_retrain', 0)
        if fine_tune_count >= 12:  # ~3 months of weekly fine-tunes
            return True, f"Accumulated {fine_tune_count} fine-tunes, time to reset"
        
        return False, "No full retrain needed"
    
    def should_fine_tune(self) -> Tuple[bool, str]:
        """
        Determine if fine-tuning is needed.
        
        Returns:
            Tuple of (should_fine_tune, reason)
        """
        # Check 1: Performance degradation above threshold
        health = self._get_health_report()
        degradation = health.get('metrics', {}).get('avg_degradation_pct', 0)
        
        if degradation >= self.drift_threshold:
            return True, f"Performance degraded {degradation:.1f}%"
        
        # Check 2: Time since last fine-tune
        last_fine_tune_str = self.state.get('last_fine_tune')
        
        if last_fine_tune_str:
            last_fine_tune = datetime.fromisoformat(last_fine_tune_str)
            days_since = (datetime.now() - last_fine_tune).days
            
            if days_since >= self.fine_tune_interval:
                return True, f"Scheduled fine-tune ({days_since} days since last)"
        else:
            # Never fine-tuned, check if we have enough new data
            return True, "Initial fine-tune"
        
        return False, "No fine-tune needed"
    
    def _run_full_retrain(self) -> Dict:
        """Execute full model retraining."""
        print("\n" + "="*60)
        print("EXECUTING FULL MODEL RETRAIN")
        print("="*60)
        
        start_time = datetime.now()
        
        try:
            # Run training script
            result = subprocess.run(
                [sys.executable, 'src/train_model.py'],
                capture_output=True,
                text=True,
                timeout=3600  # 1 hour timeout
            )
            
            success = result.returncode == 0
            
            if success:
                # Update state
                self.state['last_full_retrain'] = datetime.now().isoformat()
                self.state['fine_tune_count_since_retrain'] = 0
                self.state['last_update_type'] = 'full_retrain'
                self.state['last_update_time'] = datetime.now().isoformat()
                self.state['total_updates'] = self.state.get('total_updates', 0) + 1
                self._save_state()
                
                duration = (datetime.now() - start_time).total_seconds()
                
                return {
                    'status': 'success',
                    'type': 'full_retrain',
                    'duration_seconds': duration,
                    'message': 'Full retraining completed successfully'
                }
            else:
                return {
                    'status': 'failed',
                    'type': 'full_retrain',
                    'error': result.stderr[-1000:] if result.stderr else 'Unknown error',
                    'message': 'Full retraining failed'
                }
                
        except subprocess.TimeoutExpired:
            return {
                'status': 'timeout',
                'type': 'full_retrain',
                'message': 'Full retraining timed out after 1 hour'
            }
        except Exception as e:
            return {
                'status': 'error',
                'type': 'full_retrain',
                'error': str(e),
                'message': f'Full retraining error: {e}'
            }
    
    def _run_fine_tune(self, days: int = 30) -> Dict:
        """Execute model fine-tuning."""
        print("\n" + "="*60)
        print("EXECUTING MODEL FINE-TUNE")
        print("="*60)
        
        try:
            from src.fine_tune_model import fine_tune_from_monitor_data, fine_tune_from_processed_data
            
            # Try monitor data first
            result = fine_tune_from_monitor_data(days=days, min_samples=100)
            
            if result is None:
                # Fall back to processed data
                print("⚠️  Insufficient monitor data, using processed data...")
                result = fine_tune_from_processed_data()
            
            if result and result.get('status') == 'success':
                # Update state
                self.state['last_fine_tune'] = datetime.now().isoformat()
                self.state['fine_tune_count_since_retrain'] = \
                    self.state.get('fine_tune_count_since_retrain', 0) + 1
                self.state['last_update_type'] = 'fine_tune'
                self.state['last_update_time'] = datetime.now().isoformat()
                self.state['total_updates'] = self.state.get('total_updates', 0) + 1
                self._save_state()
                
                return {
                    'status': 'success',
                    'type': 'fine_tune',
                    'duration_seconds': result['duration_seconds'],
                    'samples_used': result['samples_used'],
                    'metrics': result.get('metrics', {}),
                    'message': 'Fine-tuning completed successfully'
                }
            
            return {
                'status': 'failed',
                'type': 'fine_tune',
                'message': 'Fine-tuning failed - insufficient data'
            }
            
        except Exception as e:
            return {
                'status': 'error',
                'type': 'fine_tune',
                'error': str(e),
                'message': f'Fine-tuning error: {e}'
            }
    
    def update_model(self, force_type: Optional[str] = None) -> Dict:
        """
        Smart model update: decides between fine-tune and full retrain.
        
        This is the main entry point for scheduled maintenance.
        
        Args:
            force_type: Force specific update type ('fine_tune' or 'full_retrain')
        
        Returns:
            Update result dict
        """
        print("\n" + "="*60)
        print("MODEL UPDATE CHECK")
        print("="*60)
        print(f"   Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        # Get current health
        health = self._get_health_report()
        print(f"\n📊 Current Model Health:")
        print(f"   Status: {health.get('status', 'unknown')}")
        print(f"   Healthy: {'✅ Yes' if health.get('healthy', True) else '❌ No'}")
        
        if 'metrics' in health and health['metrics'].get('status') == 'ok':
            print(f"   Degradation: {health['metrics'].get('avg_degradation_pct', 0):.1f}%")
        
        # Determine action
        if force_type == 'full_retrain':
            action = 'full_retrain'
            reason = 'Forced full retrain'
        elif force_type == 'fine_tune':
            action = 'fine_tune'
            reason = 'Forced fine-tune'
        else:
            # Check if full retrain needed
            needs_full, full_reason = self.should_full_retrain()
            
            if needs_full:
                action = 'full_retrain'
                reason = full_reason
            else:
                # Check if fine-tune needed
                needs_fine, fine_reason = self.should_fine_tune()
                
                if needs_fine:
                    action = 'fine_tune'
                    reason = fine_reason
                else:
                    action = 'none'
                    reason = 'Model is up to date'
        
        print(f"\n🎯 Decision: {action.upper()}")
        print(f"   Reason: {reason}")
        
        # Execute action
        if action == 'full_retrain':
            result = self._run_full_retrain()
        elif action == 'fine_tune':
            result = self._run_fine_tune()
        else:
            result = {
                'status': 'skipped',
                'type': 'none',
                'reason': reason,
                'message': 'No update needed'
            }
        
        # Log result
        self._log_update_result(result)
        
        return result
    
    def _log_update_result(self, result: Dict) -> None:
        """Log update result to history file."""
        history_path = self.logs_dir / "update_history.json"
        
        history = []
        if history_path.exists():
            with open(history_path, 'r') as f:
                history = json.load(f)
        
        result['timestamp'] = datetime.now().isoformat()
        history.append(result)
        
        # Keep last 100 updates
        history = history[-100:]
        
        with open(history_path, 'w') as f:
            json.dump(history, f, indent=2)
    
    def deploy_if_better(self) -> Dict:
        """
        Deploy fine-tuned model if it's better than current.
        
        Returns:
            Deployment result dict
        """
        from src.deploy_model import deploy_finetuned_model
        return deploy_finetuned_model()
    
    def get_status(self) -> Dict:
        """
        Get current manager status.
        
        Returns:
            Status dict with all relevant info
        """
        metadata = self._get_model_metadata()
        health = self._get_health_report()
        
        needs_full, full_reason = self.should_full_retrain()
        needs_fine, fine_reason = self.should_fine_tune()
        
        return {
            'current_model': {
                'version': metadata.get('version', 'unknown'),
                'training_date': metadata.get('training_date', 'unknown'),
                'num_features': metadata.get('num_features', 'unknown')
            },
            'health': {
                'status': health.get('status', 'unknown'),
                'healthy': health.get('healthy', True),
                'degradation_pct': health.get('metrics', {}).get('avg_degradation_pct', 0)
            },
            'state': self.state,
            'next_actions': {
                'needs_full_retrain': needs_full,
                'full_retrain_reason': full_reason,
                'needs_fine_tune': needs_fine,
                'fine_tune_reason': fine_reason
            },
            'intervals': {
                'full_retrain_days': self.full_retrain_interval,
                'fine_tune_days': self.fine_tune_interval,
                'drift_threshold_pct': self.drift_threshold,
                'critical_drift_pct': self.critical_drift
            }
        }
    
    def print_status(self) -> None:
        """Print formatted status report."""
        status = self.get_status()
        
        print("\n" + "="*60)
        print("MODEL MANAGER STATUS")
        print("="*60)
        
        print("\n📦 Current Model:")
        print(f"   Version: {status['current_model']['version']}")
        print(f"   Training Date: {status['current_model']['training_date']}")
        print(f"   Features: {status['current_model']['num_features']}")
        
        print("\n🏥 Health:")
        print(f"   Status: {status['health']['status']}")
        print(f"   Healthy: {'✅ Yes' if status['health']['healthy'] else '❌ No'}")
        print(f"   Degradation: {status['health']['degradation_pct']:.1f}%")
        
        print("\n📊 Update History:")
        print(f"   Total Updates: {status['state'].get('total_updates', 0)}")
        print(f"   Last Update: {status['state'].get('last_update_type', 'None')} at {status['state'].get('last_update_time', 'Never')}")
        print(f"   Fine-tunes Since Retrain: {status['state'].get('fine_tune_count_since_retrain', 0)}")
        
        print("\n🔮 Next Actions:")
        if status['next_actions']['needs_full_retrain']:
            print(f"   🔄 FULL RETRAIN needed: {status['next_actions']['full_retrain_reason']}")
        elif status['next_actions']['needs_fine_tune']:
            print(f"   ⚡ FINE-TUNE needed: {status['next_actions']['fine_tune_reason']}")
        else:
            print("   ✅ No update needed")
        
        print("\n" + "="*60)


def run_scheduled_update():
    """Run scheduled model update (for cron/task scheduler)."""
    print("="*60)
    print("SCHEDULED MODEL UPDATE")
    print(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*60)
    
    manager = HybridModelManager()
    result = manager.update_model()
    
    print("\n" + "="*60)
    print(f"Result: {result['status'].upper()}")
    print(f"Type: {result['type']}")
    print(f"Message: {result.get('message', 'N/A')}")
    print("="*60)
    
    return result


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='Hybrid ML Model Manager')
    parser.add_argument('--update', action='store_true', help='Run smart model update')
    parser.add_argument('--force-retrain', action='store_true', help='Force full retraining')
    parser.add_argument('--force-finetune', action='store_true', help='Force fine-tuning')
    parser.add_argument('--status', action='store_true', help='Show current status')
    parser.add_argument('--deploy', action='store_true', help='Deploy fine-tuned model if better')
    
    args = parser.parse_args()
    
    manager = HybridModelManager()
    
    if args.status:
        manager.print_status()
    elif args.update:
        run_scheduled_update()
    elif args.force_retrain:
        manager.update_model(force_type='full_retrain')
    elif args.force_finetune:
        manager.update_model(force_type='fine_tune')
    elif args.deploy:
        result = manager.deploy_if_better()
        print(f"Deployment result: {result}")
    else:
        # Default: show status and suggest actions
        manager.print_status()
        print("\nUsage:")
        print("  python src/model_manager.py --update        # Smart update (fine-tune or retrain)")
        print("  python src/model_manager.py --status        # Show status")
        print("  python src/model_manager.py --force-retrain # Force full retrain")
        print("  python src/model_manager.py --force-finetune # Force fine-tune")
        print("  python src/model_manager.py --deploy        # Deploy fine-tuned model")
