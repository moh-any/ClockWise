"""
Surge Detection Orchestrator
=============================
Background task that integrates all three layers:
- Layer 1: Data Collection (data_collector.py)
- Layer 2: Surge Detection (surge_detector.py)  
- Layer 3: Alert Generation (alert_system.py)

Runs every 5 minutes, checking all venues for surges.
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Callable
from dataclasses import dataclass, field
from enum import Enum

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class TaskStatus(Enum):
    """Status of the background orchestration task."""
    STOPPED = "stopped"
    RUNNING = "running"
    PAUSED = "paused"
    ERROR = "error"


@dataclass
class OrchestratorConfig:
    """Configuration for the surge orchestrator."""
    check_interval_seconds: int = 300  # 5 minutes
    surge_threshold: float = 1.5
    window_hours: int = 3
    min_excess_items: int = 20
    cooldown_hours: int = 2
    llm_threshold: float = 0.7
    enable_llm: bool = True
    demo_mode: bool = False


@dataclass
class OrchestrationResult:
    """Result of a single orchestration cycle."""
    cycle_id: int
    timestamp: datetime
    venues_checked: int
    surges_detected: int
    alerts_generated: int
    errors: List[str] = field(default_factory=list)
    duration_seconds: float = 0.0


class SurgeOrchestrator:
    """
    Main orchestrator for surge detection pipeline.
    
    Integrates:
    - Layer 1: RealTimeDataCollector (collect metrics)
    - Layer 2: SurgeDetector (detect surges)
    - Layer 3: AlertDispatcher (format alerts)
    
    Runs as background task with configurable interval.
    """
    
    def __init__(self, config: Optional[OrchestratorConfig] = None):
        """Initialize orchestrator with optional configuration."""
        self.config = config or OrchestratorConfig()
        self.status = TaskStatus.STOPPED
        self._task: Optional[asyncio.Task] = None
        self._cycle_count = 0
        self._last_result: Optional[OrchestrationResult] = None
        self._alert_callback: Optional[Callable] = None
        
        # Initialize components
        self._init_components()
        
        # Results history (last 100 cycles)
        self._history: List[OrchestrationResult] = []
        
        logger.info(f"SurgeOrchestrator initialized (interval: {self.config.check_interval_seconds}s)")
    
    def _init_components(self):
        """Initialize all layer components."""
        from src.data_collector import RealTimeDataCollector
        from src.surge_detector import SurgeDetector, SurgeMetrics
        from src.alert_system import AlertDispatcher
        
        # Layer 1: Data Collector
        self.data_collector = RealTimeDataCollector(
            update_interval_seconds=self.config.check_interval_seconds,
            demo_mode=self.config.demo_mode
        )
        
        # Layer 2: Surge Detector
        self.surge_detector = SurgeDetector(
            surge_threshold=self.config.surge_threshold,
            window_hours=self.config.window_hours,
            min_excess_items=self.config.min_excess_items,
            cooldown_hours=self.config.cooldown_hours
        )
        
        # Layer 3: Alert Dispatcher
        self.alert_dispatcher = AlertDispatcher(
            llm_threshold=self.config.llm_threshold,
            enable_llm=self.config.enable_llm
        )
        
        logger.info("All layer components initialized")
    
    def set_alert_callback(self, callback: Callable):
        """
        Set callback function for when alerts are generated.
        
        TODO: Backend team implements this to handle alert delivery:
        - Send emails
        - Store in database
        - Notify admin panel
        
        Callback signature: callback(alert: dict, venue_info: dict)
        """
        self._alert_callback = callback
        logger.info("Alert callback registered")
    
    async def start(self):
        """Start the background orchestration task."""
        if self.status == TaskStatus.RUNNING:
            logger.warning("Orchestrator already running")
            return
        
        self.status = TaskStatus.RUNNING
        self._task = asyncio.create_task(self._run_loop())
        logger.info("🚀 Surge orchestrator started")
    
    async def stop(self):
        """Stop the background orchestration task."""
        if self.status == TaskStatus.STOPPED:
            logger.warning("Orchestrator already stopped")
            return
        
        self.status = TaskStatus.STOPPED
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
        logger.info("⏹️ Surge orchestrator stopped")
    
    def pause(self):
        """Pause orchestration (keeps task alive but skips cycles)."""
        self.status = TaskStatus.PAUSED
        logger.info("⏸️ Surge orchestrator paused")
    
    def resume(self):
        """Resume orchestration after pause."""
        if self.status == TaskStatus.PAUSED:
            self.status = TaskStatus.RUNNING
            logger.info("▶️ Surge orchestrator resumed")
    
    async def _run_loop(self):
        """Main background loop - runs every check_interval_seconds."""
        while self.status in [TaskStatus.RUNNING, TaskStatus.PAUSED]:
            try:
                if self.status == TaskStatus.RUNNING:
                    result = await self.run_detection_cycle()
                    self._last_result = result
                    self._history.append(result)
                    
                    # Keep only last 100 results
                    if len(self._history) > 100:
                        self._history = self._history[-100:]
                    
                    logger.info(
                        f"Cycle {result.cycle_id} complete: "
                        f"{result.venues_checked} venues, "
                        f"{result.surges_detected} surges, "
                        f"{result.alerts_generated} alerts "
                        f"({result.duration_seconds:.2f}s)"
                    )
                
                # Wait for next cycle
                await asyncio.sleep(self.config.check_interval_seconds)
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in orchestration loop: {e}")
                self.status = TaskStatus.ERROR
                await asyncio.sleep(60)  # Wait before retry
    
    async def run_detection_cycle(self, venues: Optional[List[Dict]] = None) -> OrchestrationResult:
        """
        Run a single detection cycle for all venues.
        
        This is the main orchestration method that:
        1. Collects data for each venue (Layer 1)
        2. Checks for surges (Layer 2)
        3. Generates alerts for detected surges (Layer 3)
        
        Args:
            venues: Optional list of venue dicts. If None, loads from database.
        
        Returns:
            OrchestrationResult with cycle statistics
        """
        from src.surge_detector import SurgeMetrics
        
        start_time = datetime.now()
        self._cycle_count += 1
        
        result = OrchestrationResult(
            cycle_id=self._cycle_count,
            timestamp=start_time,
            venues_checked=0,
            surges_detected=0,
            alerts_generated=0
        )
        
        # Get venues to check
        if venues is None:
            venues = self._get_active_venues()
        
        result.venues_checked = len(venues)
        
        # Process each venue
        for venue in venues:
            try:
                # Layer 1: Collect data
                metrics = await self._collect_venue_metrics(venue)
                
                if not metrics:
                    continue
                
                # Layer 2: Check for surge
                surge_event = self.surge_detector.check_surge(
                    place_id=venue['place_id'],
                    metrics=metrics
                )
                
                if surge_event:
                    result.surges_detected += 1
                    
                    # Layer 3: Generate alert
                    alert = self.alert_dispatcher.generate_alert(
                        surge_event=surge_event,
                        venue_name=venue.get('name', f"Venue {venue['place_id']}")
                    )
                    
                    result.alerts_generated += 1
                    
                    # Deliver alert via callback
                    if self._alert_callback:
                        try:
                            self._alert_callback(alert, venue)
                        except Exception as e:
                            result.errors.append(f"Alert callback failed for {venue['place_id']}: {e}")
                    
            except Exception as e:
                result.errors.append(f"Error processing venue {venue.get('place_id')}: {e}")
                logger.error(f"Error processing venue {venue.get('place_id')}: {e}")
        
        result.duration_seconds = (datetime.now() - start_time).total_seconds()
        return result
    
    async def _collect_venue_metrics(self, venue: Dict) -> List['SurgeMetrics']:
        """
        Collect metrics for a single venue using Layer 1.
        
        Args:
            venue: Venue dictionary with place_id, name, lat, lon
        
        Returns:
            List of SurgeMetrics for the analysis window
        """
        from src.surge_detector import SurgeMetrics
        
        place_id = venue['place_id']
        time_window = timedelta(hours=self.config.window_hours)
        
        # Collect actual orders
        actual_orders = self.data_collector.collect_actual_orders(place_id, time_window)
        
        # Collect predictions
        predictions = self.data_collector.collect_predictions(place_id, time_window)
        
        # Collect social signals
        social_signals = self.data_collector.social.get_composite_signal(
            place_id=place_id,
            venue_name=venue.get('name', ''),
            latitude=venue.get('latitude', 55.6761),
            longitude=venue.get('longitude', 12.5683)
        )
        
        # Build metrics list
        metrics = []
        for timestamp, actual in actual_orders.items():
            predicted = predictions.get(timestamp, {'item_count': actual['item_count']})
            
            if predicted['item_count'] > 0:
                ratio = actual['item_count'] / predicted['item_count']
            else:
                ratio = 1.0
            
            metrics.append(SurgeMetrics(
                timestamp=timestamp,
                actual=actual['item_count'],
                predicted=predicted['item_count'],
                ratio=ratio,
                social_signals=social_signals,
                excess_demand=actual['item_count'] - predicted['item_count']
            ))
        
        # Sort by timestamp
        metrics.sort(key=lambda m: m.timestamp)
        
        return metrics
    
    def _get_active_venues(self) -> List[Dict]:
        """
        Get list of active venues to monitor via API endpoint.
        
        Calls: GET /api/v1/venues/active
        
        Backend team implements the endpoint to return active venues.
        """
        import requests
        
        try:
            response = requests.get(
                "http://localhost:8000/api/v1/venues/active",
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                return data.get('venues', [])
            else:
                logger.warning(f"Venues API returned {response.status_code}, using fallback")
                return self._get_fallback_venues()
                
        except Exception as e:
            logger.warning(f"Could not fetch venues via API: {e}")
            return self._get_fallback_venues()
    
    def _get_fallback_venues(self) -> List[Dict]:
        """Fallback venues for demo/testing when API unavailable."""
        return [
            {'place_id': 1, 'name': 'Demo Restaurant 1', 'latitude': 55.6761, 'longitude': 12.5683},
            {'place_id': 2, 'name': 'Demo Restaurant 2', 'latitude': 55.6800, 'longitude': 12.5700},
        ]
    
    def get_status(self) -> Dict:
        """Get current orchestrator status."""
        return {
            'status': self.status.value,
            'cycle_count': self._cycle_count,
            'last_cycle': self._last_result.__dict__ if self._last_result else None,
            'config': {
                'check_interval_seconds': self.config.check_interval_seconds,
                'surge_threshold': self.config.surge_threshold,
                'window_hours': self.config.window_hours,
                'llm_enabled': self.config.enable_llm
            }
        }
    
    def get_history(self, limit: int = 10) -> List[Dict]:
        """Get recent orchestration history."""
        return [r.__dict__ for r in self._history[-limit:]]


# =============================================================================
# SINGLETON INSTANCE FOR API
# =============================================================================

_orchestrator: Optional[SurgeOrchestrator] = None


def get_orchestrator(config: Optional[OrchestratorConfig] = None) -> SurgeOrchestrator:
    """Get or create the singleton orchestrator instance."""
    global _orchestrator
    if _orchestrator is None:
        _orchestrator = SurgeOrchestrator(config)
    return _orchestrator


# =============================================================================
# STANDALONE EXECUTION
# =============================================================================

async def main():
    """Run orchestrator as standalone background task."""
    import os
    
    # Load environment
    from dotenv import load_dotenv
    load_dotenv()
    
    print("=" * 70)
    print("SURGE DETECTION ORCHESTRATOR")
    print("=" * 70)
    print(f"Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    # Define alert callback
    def handle_alert(alert: dict, venue: dict):
        """Example callback - backend team implements actual delivery."""
        print(f"\n🚨 ALERT for {venue['name']}")
        print(f"   Severity: {alert['severity']}")
        print(f"   Subject: {alert['subject']}")
        print(f"   Channel: {alert['channels']}")
        print(f"   Timestamp: {alert['timestamp']}")
        
        # Backend team would:
        # 1. Store alert in database
        # 2. Send email via SendGrid/SMTP
        # 3. Update admin dashboard
    
    # Create and start orchestrator
    config = OrchestratorConfig(
        check_interval_seconds=60,  # 1 minute for demo
        demo_mode=True
    )
    
    orchestrator = get_orchestrator(config)
    orchestrator.set_alert_callback(handle_alert)
    
    try:
        await orchestrator.start()
        
        # Run for 5 minutes (demo)
        await asyncio.sleep(300)
        
    except KeyboardInterrupt:
        print("\n⏹️ Stopping orchestrator...")
    finally:
        await orchestrator.stop()
        print("✅ Orchestrator stopped cleanly")


if __name__ == "__main__":
    asyncio.run(main())
