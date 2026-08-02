from fastapi import APIRouter, Depends
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.prediction import Prediction
from app.models.user import User
from app.api.deps import get_current_user

router = APIRouter(prefix="/api/analytics", tags=["Analytics"])


@router.get("/trends")
def prediction_trends(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    rows = (
        db.query(
            func.date(Prediction.created_at).label("day"),
            func.avg(Prediction.recommended_speed).label("avg_speed"),
            func.count(Prediction.id).label("count"),
        )
        .filter(Prediction.user_id == current_user.id)
        .group_by(func.date(Prediction.created_at))
        .order_by(func.date(Prediction.created_at))
        .all()
    )
    return [{"day": str(r.day), "avg_speed": round(r.avg_speed, 1), "count": r.count} for r in rows]


@router.get("/risk-distribution")
def risk_distribution(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    rows = (
        db.query(Prediction.risk_level, func.count(Prediction.id))
        .filter(Prediction.user_id == current_user.id)
        .group_by(Prediction.risk_level)
        .all()
    )
    return {level: count for level, count in rows}
