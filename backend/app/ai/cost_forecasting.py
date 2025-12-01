from prophet import Prophet
import pandas as pd
from typing import Dict, Any, List
from sqlalchemy.orm import Session
from datetime import datetime, timedelta

from ..models import Instance
from ..config import get_settings

settings = get_settings()


class CostForecastingService:
    """Cost forecasting using Facebook Prophet."""

    def __init__(self):
        """Initialize cost forecasting service."""
        self.model = None

    def forecast_costs(
        self,
        db: Session,
        provider_type: str = None,
        days: int = 30
    ) -> Dict[str, Any]:
        """Forecast future costs using time series analysis.

        Args:
            db: Database session
            provider_type: Optional provider filter
            days: Number of days to forecast

        Returns:
            Forecast data dictionary
        """
        try:
            # Get historical cost data (simulated for MVP)
            historical_data = self._get_historical_costs(db, provider_type)

            if len(historical_data) < 30:  # Need minimum data
                return {
                    "status": "insufficient_data",
                    "message": "Need at least 30 days of historical data",
                    "forecast_days": days,
                    "predictions": []
                }

            # Prepare data for Prophet
            df = pd.DataFrame(historical_data)
            df.columns = ['ds', 'y']  # Prophet requires these column names

            # Train model
            model = Prophet(
                daily_seasonality=True,
                weekly_seasonality=True,
                yearly_seasonality=False
            )
            model.fit(df)

            # Make predictions
            future = model.make_future_dataframe(periods=days)
            forecast = model.predict(future)

            # Get only future predictions
            future_forecast = forecast[forecast['ds'] > df['ds'].max()]

            # Build predictions list
            predictions = []
            for _, row in future_forecast.iterrows():
                predictions.append({
                    "date": row['ds'].strftime("%Y-%m-%d"),
                    "cost": max(0, row['yhat']),  # Ensure non-negative
                    "lower_bound": max(0, row['yhat_lower']),
                    "upper_bound": max(0, row['yhat_upper'])
                })

            # Determine trend
            trend = self._analyze_trend(forecast)

            # Check for budget alerts
            budget_alert, projected_overrun = self._check_budget_alert(
                predictions,
                budget=None  # TODO: Get budget from settings
            )

            return {
                "status": "success",
                "provider": provider_type or "all",
                "forecast_days": days,
                "predictions": predictions,
                "trend": trend,
                "budget_alert": budget_alert,
                "projected_overrun": projected_overrun
            }

        except Exception as e:
            print(f"Cost forecasting failed: {e}")
            return {
                "status": "error",
                "message": str(e),
                "forecast_days": days,
                "predictions": []
            }

    def _get_historical_costs(
        self,
        db: Session,
        provider_type: str = None
    ) -> List[List]:
        """Get historical cost data.

        Args:
            db: Database session
            provider_type: Optional provider filter

        Returns:
            List of [date, cost] pairs
        """
        # For MVP, generate synthetic historical data
        # In production, this would query actual billing data

        end_date = datetime.utcnow().date()
        start_date = end_date - timedelta(days=90)

        # Get current total cost
        instances = db.query(Instance).all()
        current_cost = sum(inst.monthly_cost for inst in instances) / 30  # Daily cost

        # Generate synthetic historical data with some variation
        import random
        historical_data = []

        current = start_date
        while current <= end_date:
            # Add some randomness to simulate real data
            daily_cost = current_cost * random.uniform(0.85, 1.15)
            historical_data.append([current, daily_cost])
            current += timedelta(days=1)

        return historical_data

    def _analyze_trend(self, forecast: pd.DataFrame) -> str:
        """Analyze cost trend from forecast.

        Args:
            forecast: Prophet forecast DataFrame

        Returns:
            Trend description (increasing, decreasing, stable)
        """
        try:
            # Compare last 7 days of history with next 7 days of forecast
            recent_trend = forecast['trend'].tail(14)

            if len(recent_trend) < 14:
                return "stable"

            historical_avg = recent_trend.head(7).mean()
            forecast_avg = recent_trend.tail(7).mean()

            diff_pct = ((forecast_avg - historical_avg) / historical_avg) * 100

            if diff_pct > 5:
                return "increasing"
            elif diff_pct < -5:
                return "decreasing"
            else:
                return "stable"

        except Exception as e:
            print(f"Trend analysis failed: {e}")
            return "stable"

    def _check_budget_alert(
        self,
        predictions: List[Dict[str, Any]],
        budget: float = None
    ) -> tuple:
        """Check if forecast exceeds budget.

        Args:
            predictions: Forecast predictions
            budget: Monthly budget

        Returns:
            Tuple of (alert_triggered, projected_overrun)
        """
        if not budget or not predictions:
            return False, 0.0

        # Calculate projected monthly cost
        projected_monthly = sum(p['cost'] for p in predictions[:30])

        if projected_monthly > budget:
            overrun = projected_monthly - budget
            return True, overrun
        else:
            return False, 0.0


# Global service instance
cost_forecasting_service = CostForecastingService()
