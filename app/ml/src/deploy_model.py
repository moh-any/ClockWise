"""
Model Deployment Script for Demand Prediction
==============================================
Handles safe deployment of new models with:
- Automatic archiving of current production model
- Validation before deployment
- Rollback capability
- Version tracking

Usage:
    # Deploy fine-tuned model
    python src/deploy_model.py --fine-tuned
    
    # Deploy specific model file
    python src/deploy_model.py --model-path data/models/new_model.joblib
    
    # Rollback to previous version
    python src/deploy_model.py --rollback
    
    # Show deployment history
    python src/deploy_model.py --history
"""

import sys
import shutil
import json
import joblib
from pathlib import Path
from datetime import datetime
from typing import Dict, Optional, Tuple
import pandas as pd
import numpy as np

# Add parent directory to path for running as script
_current_dir = Path(__file__).resolve().parent
_parent_dir = _current_dir.parent
if str(_parent_dir) not in sys.path:
    sys.path.insert(0, str(_parent_dir))


class ModelDeployer:
    """
    Handles safe model deployment with archiving and rollback.
    
    Attributes:
        model_dir: Directory containing model files
        archive_dir: Directory for archived models
        production_model: Path to production model
        production_metadata: Path to production metadata
    """
    
    def __init__(self, model_dir: str = "data/models"):
        """
        Initialize model deployer.
        
        Args:
            model_dir: Directory containing model files
        """
        self.model_dir = Path(model_dir)
        self.archive_dir = self.model_dir / "archive"
        self.production_model = self.model_dir / "rf_model.joblib"
        self.production_metadata = self.model_dir / "rf_model_metadata.json"
        self.deployment_history = self.model_dir / "deployment_history.json"
        
        # Ensure archive directory exists
        self.archive_dir.mkdir(parents=True, exist_ok=True)
    
    def archive_current_model(self) -> Optional[str]:
        """
        Archive the current production model before deploying new one.
        
        Returns:
            Archive timestamp or None if no model to archive
        """
        if not self.production_model.exists():
            print("⚠️  No production model to archive")
            return None
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Archive model
        archive_model_path = self.archive_dir / f"rf_model_{timestamp}.joblib"
        shutil.copy(self.production_model, archive_model_path)
        
        # Archive metadata
        if self.production_metadata.exists():
            archive_metadata_path = self.archive_dir / f"rf_model_metadata_{timestamp}.json"
            shutil.copy(self.production_metadata, archive_metadata_path)
        
        print(f"📦 Archived current model: rf_model_{timestamp}.joblib")
        
        return timestamp
    
    def validate_model(self, model_path: Path, metadata_path: Optional[Path] = None) -> Tuple[bool, str]:
        """
        Validate a model file before deployment.
        
        Args:
            model_path: Path to model file
            metadata_path: Optional path to metadata file
        
        Returns:
            Tuple of (is_valid, message)
        """
        # Check file exists
        if not model_path.exists():
            return False, f"Model file not found: {model_path}"
        
        # Try to load model
        try:
            model = joblib.load(model_path)
        except Exception as e:
            return False, f"Failed to load model: {e}"
        
        # Check model structure
        if isinstance(model, list):
            # CatBoost multi-output: list of models
            if len(model) < 2:
                return False, f"Expected 2 models (item_count, order_count), got {len(model)}"
            
            # Check each model has predict method
            for i, m in enumerate(model):
                if not hasattr(m, 'predict'):
                    return False, f"Model {i} missing predict method"
        elif hasattr(model, 'predict'):
            # Single model or sklearn wrapper
            pass
        else:
            return False, "Model missing predict method"
        
        # Validate metadata if provided
        if metadata_path and metadata_path.exists():
            try:
                # Try JSON first (current format), fall back to joblib
                try:
                    with open(metadata_path, 'r') as f:
                        metadata = json.load(f)
                except (json.JSONDecodeError, UnicodeDecodeError):
                    metadata = joblib.load(metadata_path)
                
                # Check required fields
                if 'num_features' not in metadata:
                    return False, "Metadata missing num_features"
                    
            except Exception as e:
                return False, f"Failed to load metadata: {e}"
        
        return True, "Model validation passed"
    
    def compare_models(self, 
                       current_model_path: Path,
                       new_model_path: Path,
                       test_data_path: str = "data/processed/combined_features.csv") -> Dict:
        """
        Compare new model performance against current production model.
        
        Args:
            current_model_path: Path to current production model
            new_model_path: Path to new candidate model
            test_data_path: Path to test data
        
        Returns:
            Comparison results dict
        """
        from sklearn.metrics import mean_absolute_error
        
        try:
            # Load test data
            df = pd.read_csv(test_data_path)
            
            # Use last 20% as test set
            test_size = int(len(df) * 0.2)
            df_test = df.tail(test_size)
            
            # Prepare features and targets
            target_cols = ['item_count', 'order_count']
            drop_cols = target_cols + ['datetime', 'total_revenue', 'avg_order_value', 'avg_items_per_order']
            
            X_test = df_test.drop([c for c in drop_cols if c in df_test.columns], axis=1, errors='ignore')
            y_test = df_test[target_cols]
            
            # Handle missing columns
            if 'longitude' in X_test.columns:
                X_test = X_test.drop(['longitude', 'latitude'], axis=1, errors='ignore')
            
            X_test = X_test.fillna(0)
            
            results = {}
            
            # Evaluate current model
            if current_model_path.exists():
                current_model = joblib.load(current_model_path)
                current_preds = self._predict_with_model(current_model, X_test)
                
                if current_preds is not None:
                    results['current'] = {
                        'item_mae': mean_absolute_error(y_test['item_count'], current_preds[:, 0]),
                        'order_mae': mean_absolute_error(y_test['order_count'], current_preds[:, 1])
                    }
            
            # Evaluate new model
            new_model = joblib.load(new_model_path)
            new_preds = self._predict_with_model(new_model, X_test)
            
            if new_preds is not None:
                results['new'] = {
                    'item_mae': mean_absolute_error(y_test['item_count'], new_preds[:, 0]),
                    'order_mae': mean_absolute_error(y_test['order_count'], new_preds[:, 1])
                }
            
            # Calculate improvement
            if 'current' in results and 'new' in results:
                item_improvement = (results['current']['item_mae'] - results['new']['item_mae']) / results['current']['item_mae'] * 100
                order_improvement = (results['current']['order_mae'] - results['new']['order_mae']) / results['current']['order_mae'] * 100
                
                results['improvement'] = {
                    'item_pct': round(item_improvement, 2),
                    'order_pct': round(order_improvement, 2),
                    'is_better': item_improvement > 0 or order_improvement > 0
                }
            
            results['test_samples'] = len(X_test)
            
            return results
            
        except Exception as e:
            return {'error': str(e)}
    
    def _predict_with_model(self, model, X_test) -> Optional[np.ndarray]:
        """Make predictions handling different model types."""
        try:
            if isinstance(model, list):
                # CatBoost multi-output: list of individual models
                preds = []
                for m in model:
                    pred = m.predict(X_test)
                    pred = np.expm1(pred)  # Inverse log transform
                    preds.append(pred)
                return np.column_stack(preds)
            else:
                # sklearn wrapper
                return model.predict(X_test)
        except Exception as e:
            print(f"⚠️  Prediction failed: {e}")
            return None
    
    def deploy(self,
               model_path: Path,
               metadata_path: Optional[Path] = None,
               force: bool = False,
               validate: bool = True,
               compare: bool = True) -> Dict:
        """
        Deploy a new model to production.
        
        Args:
            model_path: Path to new model file
            metadata_path: Optional path to metadata file
            force: Skip validation and comparison
            validate: Run validation checks
            compare: Compare against current model
        
        Returns:
            Deployment result dict
        """
        print("="*60)
        print("MODEL DEPLOYMENT")
        print("="*60)
        print(f"Candidate model: {model_path}")
        
        # Validate
        if validate and not force:
            print("\n🔍 Validating model...")
            is_valid, message = self.validate_model(model_path, metadata_path)
            
            if not is_valid:
                return {
                    'status': 'failed',
                    'reason': 'validation_failed',
                    'message': message
                }
            
            print(f"   ✅ {message}")
        
        # Compare performance
        comparison = None
        if compare and not force and self.production_model.exists():
            print("\n📊 Comparing models...")
            comparison = self.compare_models(self.production_model, model_path)
            
            if 'error' not in comparison and 'improvement' in comparison:
                imp = comparison['improvement']
                print(f"   Item MAE improvement: {imp['item_pct']:.2f}%")
                print(f"   Order MAE improvement: {imp['order_pct']:.2f}%")
                print(f"   Better than current: {'✅ Yes' if imp['is_better'] else '❌ No'}")
                
                if not imp['is_better'] and not force:
                    return {
                        'status': 'rejected',
                        'reason': 'no_improvement',
                        'message': 'New model is not better than current',
                        'comparison': comparison
                    }
        
        # Archive current model
        print("\n📦 Archiving current model...")
        archive_timestamp = self.archive_current_model()
        
        # Deploy new model
        print("\n🚀 Deploying new model...")
        shutil.copy(model_path, self.production_model)
        
        if metadata_path and metadata_path.exists():
            shutil.copy(metadata_path, self.production_metadata)
        
        # Update deployment history
        self._log_deployment(model_path, archive_timestamp, comparison)
        
        print("\n✅ Deployment complete!")
        print(f"   Production model: {self.production_model}")
        print(f"   Archived as: rf_model_{archive_timestamp}.joblib")
        
        return {
            'status': 'success',
            'deployed_model': str(model_path),
            'archived_timestamp': archive_timestamp,
            'comparison': comparison
        }
    
    def deploy_finetuned_model(self) -> Dict:
        """
        Deploy the fine-tuned model if it exists and is better.
        
        Returns:
            Deployment result dict
        """
        finetuned_model = self.model_dir / "rf_model_finetuned.joblib"
        finetuned_metadata = self.model_dir / "rf_model_finetuned_metadata.json"
        
        if not finetuned_model.exists():
            return {
                'status': 'failed',
                'reason': 'not_found',
                'message': 'Fine-tuned model not found. Run fine_tune_model.py first.'
            }
        
        metadata_path = finetuned_metadata if finetuned_metadata.exists() else None
        
        result = self.deploy(
            model_path=finetuned_model,
            metadata_path=metadata_path,
            validate=True,
            compare=True
        )
        
        # Clean up fine-tuned files after successful deployment
        if result['status'] == 'success':
            finetuned_model.unlink(missing_ok=True)
            if metadata_path:
                metadata_path.unlink(missing_ok=True)
            print("🗑️  Cleaned up fine-tuned model files")
        
        return result
    
    def rollback(self, steps: int = 1) -> Dict:
        """
        Rollback to a previous model version.
        
        Args:
            steps: Number of versions to rollback (default: 1 = previous version)
        
        Returns:
            Rollback result dict
        """
        print("="*60)
        print("MODEL ROLLBACK")
        print("="*60)
        
        # Find archived models sorted by date (newest first)
        archived_models = sorted(
            self.archive_dir.glob("rf_model_*.joblib"),
            key=lambda p: p.stat().st_mtime,
            reverse=True
        )
        
        if not archived_models:
            return {
                'status': 'failed',
                'reason': 'no_archives',
                'message': 'No archived models found for rollback'
            }
        
        if steps > len(archived_models):
            return {
                'status': 'failed',
                'reason': 'insufficient_history',
                'message': f'Only {len(archived_models)} archived versions available'
            }
        
        # Get the target archive
        target_model = archived_models[steps - 1]
        timestamp = target_model.stem.replace('rf_model_', '')
        target_metadata = self.archive_dir / f"rf_model_metadata_{timestamp}.json"
        
        print(f"Rolling back to: {target_model.name}")
        
        # Archive current before rollback (in case we need to undo)
        rollback_archive = self.archive_current_model()
        
        # Restore archived model
        shutil.copy(target_model, self.production_model)
        
        if target_metadata.exists():
            shutil.copy(target_metadata, self.production_metadata)
        
        # Log rollback
        self._log_deployment(
            target_model,
            rollback_archive,
            {'action': 'rollback', 'target_version': timestamp}
        )
        
        print(f"\n✅ Rolled back to version: {timestamp}")
        
        return {
            'status': 'success',
            'rolled_back_to': timestamp,
            'previous_archived': rollback_archive
        }
    
    def _log_deployment(self, 
                        model_path: Path,
                        archive_timestamp: Optional[str],
                        comparison: Optional[Dict]) -> None:
        """Log deployment to history file."""
        history = []
        if self.deployment_history.exists():
            with open(self.deployment_history, 'r') as f:
                history = json.load(f)
        
        entry = {
            'timestamp': datetime.now().isoformat(),
            'deployed_model': str(model_path),
            'archived_version': archive_timestamp,
            'comparison': comparison
        }
        
        history.append(entry)
        
        # Keep last 50 deployments
        history = history[-50:]
        
        with open(self.deployment_history, 'w') as f:
            json.dump(history, f, indent=2)
    
    def get_deployment_history(self, limit: int = 10) -> list:
        """
        Get deployment history.
        
        Args:
            limit: Maximum entries to return
        
        Returns:
            List of deployment entries
        """
        if not self.deployment_history.exists():
            return []
        
        with open(self.deployment_history, 'r') as f:
            history = json.load(f)
        
        return history[-limit:]
    
    def get_available_archives(self) -> list:
        """
        List available archived model versions.
        
        Returns:
            List of archive info dicts
        """
        archives = []
        
        for model_path in sorted(self.archive_dir.glob("rf_model_*.joblib"), reverse=True):
            timestamp = model_path.stem.replace('rf_model_', '')
            metadata_path = self.archive_dir / f"rf_model_metadata_{timestamp}.json"
            
            info = {
                'timestamp': timestamp,
                'model_file': model_path.name,
                'has_metadata': metadata_path.exists(),
                'size_mb': round(model_path.stat().st_size / (1024 * 1024), 2)
            }
            
            # Try to get version from metadata
            if metadata_path.exists():
                try:
                    # Try JSON first (current format), fall back to joblib
                    try:
                        with open(metadata_path, 'r') as f:
                            metadata = json.load(f)
                    except (json.JSONDecodeError, UnicodeDecodeError):
                        metadata = joblib.load(metadata_path)
                    info['version'] = metadata.get('version', 'unknown')
                except:
                    pass
            
            archives.append(info)
        
        return archives
    
    def print_status(self) -> None:
        """Print current deployment status."""
        print("\n" + "="*60)
        print("DEPLOYMENT STATUS")
        print("="*60)
        
        # Current production model
        print("\n📦 Production Model:")
        if self.production_model.exists():
            print(f"   Path: {self.production_model}")
            print(f"   Size: {self.production_model.stat().st_size / (1024*1024):.2f} MB")
            
            if self.production_metadata.exists():
                # Try JSON first (current format), fall back to joblib
                try:
                    with open(self.production_metadata, 'r') as f:
                        metadata = json.load(f)
                except (json.JSONDecodeError, UnicodeDecodeError):
                    metadata = joblib.load(self.production_metadata)
                print(f"   Version: {metadata.get('version', 'unknown')}")
                print(f"   Training Date: {metadata.get('training_date', 'unknown')}")
                print(f"   Features: {metadata.get('num_features', 'unknown')}")
        else:
            print("   ❌ No production model found")
        
        # Available archives
        archives = self.get_available_archives()
        print(f"\n📚 Archived Versions: {len(archives)}")
        for arch in archives[:5]:
            print(f"   - {arch['timestamp']} ({arch['size_mb']} MB)")
        
        # Recent deployments
        history = self.get_deployment_history(5)
        print(f"\n📋 Recent Deployments: {len(history)}")
        for entry in reversed(history):
            print(f"   - {entry['timestamp'][:16]}: {Path(entry['deployed_model']).name}")
        
        print("\n" + "="*60)


# Convenience functions

def deploy_finetuned_model() -> Dict:
    """Deploy the fine-tuned model if better."""
    deployer = ModelDeployer()
    return deployer.deploy_finetuned_model()


def rollback_model(steps: int = 1) -> Dict:
    """Rollback to a previous model version."""
    deployer = ModelDeployer()
    return deployer.rollback(steps)


def show_deployment_status():
    """Print deployment status."""
    deployer = ModelDeployer()
    deployer.print_status()


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='Model Deployment Manager')
    parser.add_argument('--fine-tuned', action='store_true', help='Deploy fine-tuned model')
    parser.add_argument('--model-path', type=str, help='Deploy specific model file')
    parser.add_argument('--rollback', action='store_true', help='Rollback to previous version')
    parser.add_argument('--rollback-steps', type=int, default=1, help='Number of versions to rollback')
    parser.add_argument('--history', action='store_true', help='Show deployment history')
    parser.add_argument('--archives', action='store_true', help='List available archives')
    parser.add_argument('--status', action='store_true', help='Show deployment status')
    parser.add_argument('--force', action='store_true', help='Force deployment without checks')
    
    args = parser.parse_args()
    
    deployer = ModelDeployer()
    
    if args.status:
        deployer.print_status()
    elif args.history:
        print("\nDeployment History:")
        for entry in deployer.get_deployment_history(10):
            print(f"  {entry['timestamp']}: {Path(entry['deployed_model']).name}")
    elif args.archives:
        print("\nAvailable Archives:")
        for arch in deployer.get_available_archives():
            print(f"  {arch['timestamp']}: {arch.get('version', 'unknown')} ({arch['size_mb']} MB)")
    elif args.rollback:
        result = deployer.rollback(args.rollback_steps)
        print(f"\nResult: {result['status']}")
    elif args.fine_tuned:
        result = deployer.deploy_finetuned_model()
        print(f"\nResult: {result['status']}")
        if result.get('message'):
            print(f"Message: {result['message']}")
    elif args.model_path:
        model_path = Path(args.model_path)
        result = deployer.deploy(model_path, force=args.force)
        print(f"\nResult: {result['status']}")
    else:
        deployer.print_status()
        print("\nUsage:")
        print("  python src/deploy_model.py --fine-tuned    # Deploy fine-tuned model")
        print("  python src/deploy_model.py --rollback      # Rollback to previous")
        print("  python src/deploy_model.py --status        # Show status")
        print("  python src/deploy_model.py --history       # Show deployment history")
        print("  python src/deploy_model.py --archives      # List available archives")
