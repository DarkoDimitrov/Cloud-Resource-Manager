from sklearn.ensemble import IsolationForest
import numpy as np
from typing import List, Dict, Any
from sqlalchemy.orm import Session
from datetime import datetime, timedelta

from ..models import Instance, Metric, Anomaly
from ..config import get_settings

settings = get_settings()


class AnomalyDetectionService:
    """ML-based anomaly detection using Isolation Forest."""

    def __init__(self):
        """Initialize anomaly detection service."""
        self.model = IsolationForest(
            contamination=settings.anomaly_detection_sensitivity,
            random_state=42
        )
        self.trained = False

    def detect_anomalies(
        self,
        db: Session,
        instance: Instance,
        metric_type: str = "cpu"
    ) -> List[Dict[str, Any]]:
        """Detect anomalies for an instance.

        Args:
            db: Database session
            instance: Instance to check
            metric_type: Type of metric to analyze

        Returns:
            List of detected anomalies
        """
        try:
            # Get historical metrics
            end_time = datetime.utcnow()
            start_time = end_time - timedelta(days=settings.min_training_days)

            metrics = db.query(Metric).filter(
                Metric.instance_id == instance.id,
                Metric.metric_type == metric_type,
                Metric.timestamp >= start_time
            ).order_by(Metric.timestamp).all()

            if len(metrics) < 30:  # Need minimum data points
                return []

            # Prepare data
            values = np.array([m.value for m in metrics]).reshape(-1, 1)

            # Train model if not trained
            if not self.trained:
                self.model.fit(values)
                self.trained = True

            # Predict anomalies
            predictions = self.model.predict(values)
            anomaly_scores = self.model.score_samples(values)

            # Find anomalies (prediction = -1)
            anomalies = []
            for idx, (pred, score, metric) in enumerate(zip(predictions, anomaly_scores, metrics)):
                if pred == -1:  # Anomaly detected
                    # Determine severity based on score
                    severity = self._determine_severity(score)

                    anomaly_data = {
                        "instance_id": instance.id,
                        "metric_type": metric_type,
                        "severity": severity,
                        "anomaly_score": float(score),
                        "value": metric.value,
                        "timestamp": metric.timestamp,
                        "detected_at": datetime.utcnow()
                    }

                    anomalies.append(anomaly_data)

            return anomalies

        except Exception as e:
            print(f"Anomaly detection failed for instance {instance.id}: {e}")
            return []

    def _determine_severity(self, score: float) -> str:
        """Determine anomaly severity based on score.

        Args:
            score: Anomaly score from model

        Returns:
            Severity level (critical, warning, info)
        """
        if score < -0.5:
            return "critical"
        elif score < -0.3:
            return "warning"
        else:
            return "info"

    def create_anomaly_alert(
        self,
        db: Session,
        anomaly_data: Dict[str, Any]
    ) -> Anomaly:
        """Create an anomaly alert in the database.

        Args:
            db: Database session
            anomaly_data: Anomaly data dictionary

        Returns:
            Created Anomaly object
        """
        try:
            # Generate title and description
            title = f"Unusual {anomaly_data['metric_type']} activity detected"
            description = f"Detected anomalous {anomaly_data['metric_type']} pattern with severity {anomaly_data['severity']}"

            # Generate recommended action
            recommended_action = self._generate_recommendation(anomaly_data)

            anomaly = Anomaly(
                instance_id=anomaly_data["instance_id"],
                metric_type=anomaly_data["metric_type"],
                severity=anomaly_data["severity"],
                anomaly_score=anomaly_data["anomaly_score"],
                detected_at=anomaly_data.get("detected_at", datetime.utcnow()),
                title=title,
                description=description,
                recommended_action=recommended_action,
                extra_data={
                    "value": anomaly_data.get("value"),
                    "timestamp": anomaly_data.get("timestamp").isoformat() if anomaly_data.get("timestamp") else None
                }
            )

            db.add(anomaly)
            db.commit()
            db.refresh(anomaly)

            return anomaly

        except Exception as e:
            db.rollback()
            print(f"Failed to create anomaly alert: {e}")
            raise

    def _generate_recommendation(self, anomaly_data: Dict[str, Any]) -> str:
        """Generate recommended action for anomaly.

        Args:
            anomaly_data: Anomaly data

        Returns:
            Recommended action string
        """
        metric_type = anomaly_data.get("metric_type", "")
        severity = anomaly_data.get("severity", "")

        recommendations = {
            "cpu": {
                "critical": "Investigate application causing high CPU usage. Consider scaling up or optimizing code.",
                "warning": "Monitor CPU trends. May need resource adjustment.",
                "info": "CPU pattern unusual but not critical. Continue monitoring."
            },
            "memory": {
                "critical": "Memory usage anomaly detected. Check for memory leaks or increase instance memory.",
                "warning": "Monitor memory usage. May indicate memory leak or increased load.",
                "info": "Memory pattern unusual. Review application behavior."
            },
            "cost": {
                "critical": "Significant cost spike detected. Review recent changes and resource usage.",
                "warning": "Cost increase detected. Review resource allocation.",
                "info": "Minor cost anomaly. Continue monitoring."
            }
        }

        return recommendations.get(metric_type, {}).get(severity, "Review instance metrics and logs for unusual activity.")


# Global service instance
anomaly_detection_service = AnomalyDetectionService()
