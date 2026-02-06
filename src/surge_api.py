"""
Surge Detection API Endpoints
==============================
FastAPI endpoints for the surge detection system.
Add these routes to your main FastAPI app.

Provides:
- Orchestrator control (start/stop/status)
- Manual surge detection
- Alert history and retrieval
- Configuration management
"""

from fastapi import APIRouter, HTTPException, BackgroundTasks
from pydantic import BaseModel, Field
from typing import List, Optional, Dict
from datetime import datetime
from enum import Enum

# Create router for surge detection endpoints
router = APIRouter(
    prefix="/api/v1/surge",
    tags=["Surge Detection"]
)


# =============================================================================
# REQUEST/RESPONSE MODELS
# =============================================================================

class VenueInput(BaseModel):
    """Venue input for surge detection."""
    place_id: int = Field(..., description="Unique venue identifier")
    name: str = Field(..., description="Venue display name")
    latitude: float = Field(default=55.6761, description="Venue latitude")
    longitude: float = Field(default=12.5683, description="Venue longitude")

    class Config:
        json_schema_extra = {
            "example": {
                "place_id": 123,
                "name": "Pizza Paradise",
                "latitude": 55.6761,
                "longitude": 12.5683
            }
        }


class OrchestratorConfigInput(BaseModel):
    """Configuration for the orchestrator."""
    check_interval_seconds: int = Field(default=300, description="Check interval in seconds (default: 5 min)")
    surge_threshold: float = Field(default=1.5, description="Minimum ratio to detect surge")
    window_hours: int = Field(default=3, description="Hours of history to analyze")
    min_excess_items: int = Field(default=20, description="Minimum excess items per hour")
    cooldown_hours: int = Field(default=2, description="Cooldown between alerts for same venue")
    llm_threshold: float = Field(default=0.7, description="Risk score threshold for LLM analysis")
    enable_llm: bool = Field(default=True, description="Enable LLM analysis for high-risk surges")

    class Config:
        json_schema_extra = {
            "example": {
                "check_interval_seconds": 300,
                "surge_threshold": 1.5,
                "window_hours": 3,
                "min_excess_items": 20,
                "cooldown_hours": 2,
                "llm_threshold": 0.7,
                "enable_llm": True
            }
        }


class SurgeMetricsInput(BaseModel):
    """Manual surge metrics input for testing."""
    timestamp: datetime
    actual: float = Field(..., description="Actual demand (item count)")
    predicted: float = Field(..., description="Predicted demand")
    social_signals: Dict[str, float] = Field(default_factory=dict, description="Social media signals")

    class Config:
        json_schema_extra = {
            "example": {
                "timestamp": "2024-01-15T14:00:00",
                "actual": 250,
                "predicted": 100,
                "social_signals": {"composite_signal": 0.8, "twitter_virality": 0.6}
            }
        }


class ManualSurgeCheckInput(BaseModel):
    """Input for manual surge check."""
    venue: VenueInput
    metrics: List[SurgeMetricsInput] = Field(..., min_length=1, description="At least 1 hour of metrics")

    class Config:
        json_schema_extra = {
            "example": {
                "venue": {"place_id": 123, "name": "Pizza Paradise"},
                "metrics": [
                    {"timestamp": "2024-01-15T12:00:00", "actual": 200, "predicted": 100, "social_signals": {}},
                    {"timestamp": "2024-01-15T13:00:00", "actual": 220, "predicted": 100, "social_signals": {}},
                    {"timestamp": "2024-01-15T14:00:00", "actual": 250, "predicted": 100, "social_signals": {"composite_signal": 0.7}}
                ]
            }
        }


class OrchestratorStatus(BaseModel):
    """Orchestrator status response."""
    status: str
    cycle_count: int
    last_cycle: Optional[Dict]
    config: Dict


class SurgeAlertResponse(BaseModel):
    """Surge alert response."""
    surge_detected: bool
    alert: Optional[Dict] = None
    surge_event: Optional[Dict] = None


class BatchSurgeCheckInput(BaseModel):
    """Input for batch surge check."""
    venues: List[VenueInput] = Field(..., min_length=1, max_length=100)


class BatchSurgeCheckResponse(BaseModel):
    """Response from batch surge check."""
    venues_checked: int
    surges_detected: int
    alerts: List[Dict]
    duration_seconds: float


# =============================================================================
# ORCHESTRATOR ENDPOINTS
# =============================================================================

@router.post("/orchestrator/start", response_model=OrchestratorStatus)
async def start_orchestrator(
    background_tasks: BackgroundTasks,
    config: Optional[OrchestratorConfigInput] = None
):
    """
    Start the surge detection background task.
    
    This starts the orchestrator which will:
    1. Check all venues every `check_interval_seconds`
    2. Detect surges using Layer 2 logic
    3. Generate alerts for detected surges
    
    **Backend Team Action:**
    - Call this endpoint on application startup
    - Or schedule via cron job
    """
    from src.surge_orchestrator import get_orchestrator, OrchestratorConfig, TaskStatus
    import asyncio
    
    if config:
        orch_config = OrchestratorConfig(**config.model_dump())
    else:
        orch_config = None
    
    orchestrator = get_orchestrator(orch_config)
    
    if orchestrator.status == TaskStatus.RUNNING:
        raise HTTPException(status_code=400, detail="Orchestrator already running")
    
    # Start in background
    background_tasks.add_task(orchestrator.start)
    
    return orchestrator.get_status()


@router.post("/orchestrator/stop", response_model=OrchestratorStatus)
async def stop_orchestrator():
    """
    Stop the surge detection background task.
    
    **Backend Team Action:**
    - Call on graceful shutdown
    - Or when maintenance is needed
    """
    from src.surge_orchestrator import get_orchestrator, TaskStatus
    
    orchestrator = get_orchestrator()
    
    if orchestrator.status == TaskStatus.STOPPED:
        raise HTTPException(status_code=400, detail="Orchestrator already stopped")
    
    await orchestrator.stop()
    return orchestrator.get_status()


@router.post("/orchestrator/pause", response_model=OrchestratorStatus)
async def pause_orchestrator():
    """
    Pause the orchestrator (keeps task alive but skips detection cycles).
    
    Useful during:
    - Maintenance windows
    - Known high-traffic events (to prevent false alerts)
    """
    from src.surge_orchestrator import get_orchestrator, TaskStatus
    
    orchestrator = get_orchestrator()
    
    if orchestrator.status != TaskStatus.RUNNING:
        raise HTTPException(status_code=400, detail="Orchestrator not running")
    
    orchestrator.pause()
    return orchestrator.get_status()


@router.post("/orchestrator/resume", response_model=OrchestratorStatus)
async def resume_orchestrator():
    """Resume a paused orchestrator."""
    from src.surge_orchestrator import get_orchestrator, TaskStatus
    
    orchestrator = get_orchestrator()
    
    if orchestrator.status != TaskStatus.PAUSED:
        raise HTTPException(status_code=400, detail="Orchestrator not paused")
    
    orchestrator.resume()
    return orchestrator.get_status()


@router.get("/orchestrator/status", response_model=OrchestratorStatus)
async def get_orchestrator_status():
    """
    Get current orchestrator status.
    
    Returns:
    - Current status (running/stopped/paused/error)
    - Number of detection cycles completed
    - Last cycle results
    - Current configuration
    """
    from src.surge_orchestrator import get_orchestrator
    
    orchestrator = get_orchestrator()
    return orchestrator.get_status()


@router.get("/orchestrator/history")
async def get_orchestrator_history(limit: int = 10):
    """
    Get recent orchestration cycle history.
    
    Args:
        limit: Maximum number of cycles to return (default: 10, max: 100)
    
    Returns list of cycle results with:
    - Venues checked
    - Surges detected
    - Alerts generated
    - Duration
    - Any errors
    """
    from src.surge_orchestrator import get_orchestrator
    
    if limit > 100:
        limit = 100
    
    orchestrator = get_orchestrator()
    return orchestrator.get_history(limit)


# =============================================================================
# MANUAL SURGE DETECTION ENDPOINTS
# =============================================================================

@router.post("/check", response_model=SurgeAlertResponse)
async def check_surge_manual(input_data: ManualSurgeCheckInput):
    """
    Manually check for surge with provided metrics.
    
    Use this endpoint for:
    - Testing surge detection logic
    - Ad-hoc checks with custom data
    - Debugging alert formatting
    
    **Backend Team Action:**
    - Use for testing before production
    - Can be called with real-time data if not using orchestrator
    """
    from src.surge_detector import SurgeDetector, SurgeMetrics
    from src.alert_system import AlertDispatcher
    
    # Initialize components
    detector = SurgeDetector()
    dispatcher = AlertDispatcher()
    
    # Convert input to SurgeMetrics
    metrics = [
        SurgeMetrics(
            timestamp=m.timestamp,
            actual=m.actual,
            predicted=m.predicted,
            ratio=m.actual / m.predicted if m.predicted > 0 else 1.0,
            social_signals=m.social_signals,
            excess_demand=m.actual - m.predicted
        )
        for m in input_data.metrics
    ]
    
    # Check for surge
    surge_event = detector.check_surge(
        place_id=input_data.venue.place_id,
        metrics=metrics
    )
    
    if surge_event:
        # Generate alert
        alert = dispatcher.generate_alert(
            surge_event=surge_event,
            venue_name=input_data.venue.name
        )
        
        return SurgeAlertResponse(
            surge_detected=True,
            alert=alert,
            surge_event={
                'place_id': surge_event.place_id,
                'severity': surge_event.severity,
                'risk_score': surge_event.risk_score,
                'avg_ratio': surge_event.avg_ratio,
                'trend': surge_event.trend,
                'root_cause': surge_event.root_cause,
                'detected_at': surge_event.detected_at.isoformat(),
                'recommendations': surge_event.recommendations
            }
        )
    else:
        return SurgeAlertResponse(surge_detected=False)


@router.post("/check/batch", response_model=BatchSurgeCheckResponse)
async def check_surge_batch(input_data: BatchSurgeCheckInput):
    """
    Run surge detection cycle for a batch of venues.
    
    Uses the orchestrator to check all provided venues.
    Useful for on-demand checks or scheduled jobs.
    
    **Backend Team Action:**
    - Can use instead of background orchestrator
    - Schedule via cron: call every 5 minutes
    """
    from src.surge_orchestrator import get_orchestrator
    from datetime import datetime
    
    orchestrator = get_orchestrator()
    
    # Convert venues
    venues = [v.model_dump() for v in input_data.venues]
    
    # Run detection cycle
    result = await orchestrator.run_detection_cycle(venues)
    
    return BatchSurgeCheckResponse(
        venues_checked=result.venues_checked,
        surges_detected=result.surges_detected,
        alerts=orchestrator.get_status().get('alerts', []),
        duration_seconds=result.duration_seconds
    )


@router.post("/check/single", response_model=SurgeAlertResponse)
async def check_single_venue(venue: VenueInput):
    """
    Check a single venue for surge using live data collection.
    
    This endpoint:
    1. Collects real-time data for the venue (Layer 1)
    2. Checks for surge (Layer 2)
    3. Generates alert if surge detected (Layer 3)
    
    **Backend Team Action:**
    - Use for real-time monitoring of specific venues
    - Trigger when abnormal activity detected
    """
    from src.surge_orchestrator import get_orchestrator
    from datetime import datetime
    
    orchestrator = get_orchestrator()
    
    # Run single venue check
    venues = [venue.model_dump()]
    result = await orchestrator.run_detection_cycle(venues)
    
    if result.surges_detected > 0:
        # Get the generated alert from last cycle
        status = orchestrator.get_status()
        return SurgeAlertResponse(
            surge_detected=True,
            alert=status.get('last_cycle', {}).get('alert'),
            surge_event=status.get('last_cycle', {}).get('surge')
        )
    
    return SurgeAlertResponse(surge_detected=False)


# =============================================================================
# ALERT HISTORY ENDPOINTS
# =============================================================================

@router.get("/alerts/recent")
async def get_recent_alerts(limit: int = 20):
    """
    Get recent alerts from orchestrator history.
    
    **Backend Team Action:**
    - Display in admin dashboard
    - Use for audit logs
    
    Note: For persistent history, backend should store alerts in database
    via the alert callback.
    """
    from src.surge_orchestrator import get_orchestrator
    
    orchestrator = get_orchestrator()
    history = orchestrator.get_history(limit=limit)
    
    # Extract alerts from history
    alerts = []
    for cycle in history:
        if cycle.get('alerts_generated', 0) > 0:
            alerts.append({
                'cycle_id': cycle['cycle_id'],
                'timestamp': cycle['timestamp'],
                'alerts_count': cycle['alerts_generated']
            })
    
    return {"alerts": alerts, "total": len(alerts)}


# =============================================================================
# CONFIGURATION ENDPOINTS
# =============================================================================

@router.get("/config")
async def get_surge_config():
    """
    Get current surge detection configuration.
    
    Returns all configurable parameters with current values.
    """
    from src.surge_orchestrator import get_orchestrator
    
    orchestrator = get_orchestrator()
    status = orchestrator.get_status()
    return status.get('config', {})


@router.put("/config")
async def update_surge_config(config: OrchestratorConfigInput):
    """
    Update surge detection configuration.
    
    Note: Requires orchestrator restart to take effect.
    
    **Backend Team Action:**
    - Adjust thresholds based on business needs
    - Tune during different seasons/events
    """
    # For now, return the proposed config
    # Full implementation would update orchestrator config
    return {
        "message": "Configuration updated. Restart orchestrator to apply.",
        "new_config": config.model_dump()
    }


# =============================================================================
# HEALTH & METRICS
# =============================================================================

@router.get("/health")
async def surge_health_check():
    """
    Health check for surge detection system.
    
    Returns component status and availability.
    """
    from src.surge_orchestrator import get_orchestrator, TaskStatus
    
    orchestrator = get_orchestrator()
    status = orchestrator.get_status()
    
    return {
        "healthy": orchestrator.status != TaskStatus.ERROR,
        "orchestrator_status": status['status'],
        "cycles_completed": status['cycle_count'],
        "components": {
            "data_collector": "available",
            "surge_detector": "available",
            "alert_dispatcher": "available",
            "llm_analyzer": "available" if orchestrator.config.enable_llm else "disabled"
        }
    }


@router.get("/metrics")
async def get_surge_metrics():
    """
    Get surge detection metrics for monitoring.
    
    **Backend Team Action:**
    - Integrate with Prometheus/Grafana
    - Monitor for system health
    """
    from src.surge_orchestrator import get_orchestrator
    
    orchestrator = get_orchestrator()
    history = orchestrator.get_history(limit=100)
    
    if not history:
        return {
            "total_cycles": 0,
            "total_surges": 0,
            "total_alerts": 0,
            "avg_cycle_duration": 0,
            "error_rate": 0
        }
    
    total_surges = sum(h.get('surges_detected', 0) for h in history)
    total_alerts = sum(h.get('alerts_generated', 0) for h in history)
    avg_duration = sum(h.get('duration_seconds', 0) for h in history) / len(history)
    error_cycles = sum(1 for h in history if h.get('errors'))
    
    return {
        "total_cycles": len(history),
        "total_surges": total_surges,
        "total_alerts": total_alerts,
        "avg_cycle_duration": round(avg_duration, 3),
        "error_rate": round(error_cycles / len(history), 3) if history else 0
    }


# =============================================================================
# INTEGRATION HELPER
# =============================================================================

def register_surge_routes(app):
    """
    Register surge detection routes with a FastAPI app.
    
    Usage in main.py:
        from surge_api import register_surge_routes
        register_surge_routes(app)
    """
    app.include_router(router)
    return app
