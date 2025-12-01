from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List

from ..database import get_db
from ..schemas.anomaly import NLQueryRequest, NLQueryResponse, AnomalyResponse, AnomalyListResponse
from ..schemas.billing import CostForecastResponse
from ..ai.nl_query_service import nl_query_service
from ..ai.anomaly_detection import anomaly_detection_service
from ..ai.cost_forecasting import cost_forecasting_service
from ..models import Instance, Anomaly
from ..config import get_settings

settings = get_settings()
router = APIRouter()


@router.post("/query", response_model=NLQueryResponse)
def natural_language_query(request: NLQueryRequest, db: Session = Depends(get_db)):
    """Process natural language query about infrastructure.

    This endpoint allows users to ask questions in plain English:
    - "Show me all instances in AWS us-east-1 that cost more than $100/month"
    - "Which instances have high CPU but low memory usage?"
    - "What's my total spend on OpenStack this month?"
    """
    if not settings.enable_nl_query:
        raise HTTPException(
            status_code=503,
            detail="Natural language query is disabled"
        )

    try:
        result = nl_query_service.query(db, request.query)

        return {
            "query": request.query,
            "answer": result["answer"],
            "data": result.get("data"),
            "suggestions": result.get("suggestions", [])
        }

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Query processing failed: {str(e)}"
        )


@router.get("/anomalies", response_model=AnomalyListResponse)
def list_anomalies(
    severity: str = None,
    last_hours: int = 24,
    db: Session = Depends(get_db)
):
    """List detected anomalies with optional filters."""
    if not settings.enable_anomaly_detection:
        raise HTTPException(
            status_code=503,
            detail="Anomaly detection is disabled"
        )

    try:
        from datetime import datetime, timedelta

        query = db.query(Anomaly).filter(
            Anomaly.status == "active",
            Anomaly.detected_at >= datetime.utcnow() - timedelta(hours=last_hours)
        )

        if severity:
            query = query.filter(Anomaly.severity == severity)

        anomalies = query.order_by(Anomaly.detected_at.desc()).all()

        # Count by severity
        critical_count = sum(1 for a in anomalies if a.severity == "critical")
        warning_count = sum(1 for a in anomalies if a.severity == "warning")

        return {
            "total_anomalies": len(anomalies),
            "critical_count": critical_count,
            "warning_count": warning_count,
            "anomalies": anomalies
        }

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to list anomalies: {str(e)}"
        )


@router.post("/anomalies/detect/{instance_id}")
def detect_anomalies(
    instance_id: str,
    metric_type: str = "cpu",
    db: Session = Depends(get_db)
):
    """Run anomaly detection for a specific instance."""
    if not settings.enable_anomaly_detection:
        raise HTTPException(
            status_code=503,
            detail="Anomaly detection is disabled"
        )

    # Get instance
    instance = db.query(Instance).filter(Instance.id == instance_id).first()
    if not instance:
        raise HTTPException(status_code=404, detail=f"Instance {instance_id} not found")

    try:
        # Run anomaly detection
        anomalies = anomaly_detection_service.detect_anomalies(db, instance, metric_type)

        # Create alerts for detected anomalies
        created_alerts = []
        for anomaly_data in anomalies:
            alert = anomaly_detection_service.create_anomaly_alert(db, anomaly_data)
            created_alerts.append(alert)

        return {
            "instance_id": instance_id,
            "metric_type": metric_type,
            "anomalies_detected": len(created_alerts),
            "anomalies": created_alerts
        }

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Anomaly detection failed: {str(e)}"
        )


@router.post("/anomalies/{anomaly_id}/resolve")
def resolve_anomaly(anomaly_id: str, db: Session = Depends(get_db)):
    """Mark an anomaly as resolved."""
    from datetime import datetime

    anomaly = db.query(Anomaly).filter(Anomaly.id == anomaly_id).first()
    if not anomaly:
        raise HTTPException(status_code=404, detail=f"Anomaly {anomaly_id} not found")

    try:
        anomaly.status = "resolved"
        anomaly.resolved_at = datetime.utcnow()
        db.commit()
        db.refresh(anomaly)

        return {
            "anomaly_id": anomaly_id,
            "status": "resolved",
            "resolved_at": anomaly.resolved_at
        }

    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail=f"Failed to resolve anomaly: {str(e)}"
        )


@router.get("/forecast")
def forecast_costs(
    provider: str = None,
    days: int = 30,
    db: Session = Depends(get_db)
):
    """Get cost forecast using ML time series analysis.

    Predicts future costs based on historical patterns and provides:
    - Daily cost predictions with confidence intervals
    - Trend analysis (increasing, decreasing, stable)
    - Budget overrun alerts
    """
    if not settings.enable_cost_forecasting:
        raise HTTPException(
            status_code=503,
            detail="Cost forecasting is disabled"
        )

    try:
        forecast = cost_forecasting_service.forecast_costs(db, provider, days)

        return forecast

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Cost forecasting failed: {str(e)}"
        )


@router.get("/insights")
def generate_insights(db: Session = Depends(get_db)):
    """Generate AI-powered insights about infrastructure.

    Returns comprehensive analysis of:
    - Cost drivers and trends
    - Performance issues
    - Optimization opportunities
    - Prioritized action items
    """
    # TODO: Implement insights generation using Claude API
    return {
        "status": "not_implemented",
        "message": "Insights generation coming soon"
    }
