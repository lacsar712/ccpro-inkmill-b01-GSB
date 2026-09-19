from datetime import datetime, timedelta

from flask import Blueprint, jsonify
from flask_jwt_extended import jwt_required
from sqlalchemy import case, func, select

from app.database import SessionLocal
from app.models.grind_pass import GrindPass
from app.models.mill import Mill
from app.models.viscosity_sample import ViscositySample
from app.models.workshop import Workshop

bp = Blueprint("dashboard", __name__, url_prefix="/api")


@bp.get("/dashboard")
@jwt_required()
def summary():
    db = SessionLocal()
    try:
        now = datetime.now()
        since_24h = now - timedelta(hours=24)
        since_7d = now - timedelta(days=7)

        workshop_total = db.scalar(select(func.count()).select_from(Workshop)) or 0
        grinding_mill_count = (
            db.scalar(
                select(func.count()).select_from(Mill).where(Mill.status == "grinding")
            )
            or 0
        )
        samples_last_24h = (
            db.scalar(
                select(func.count())
                .select_from(ViscositySample)
                .where(ViscositySample.sampled_at >= since_24h)
            )
            or 0
        )
        passes_last_7d = (
            db.scalar(
                select(func.count())
                .select_from(GrindPass)
                .where(GrindPass.started_at >= since_7d)
            )
            or 0
        )

        grinding_count = func.coalesce(
            func.sum(case((Mill.status == "grinding", 1), else_=0)), 0
        )
        by_workshop_rows = db.execute(
            select(
                Workshop.id,
                Workshop.name,
                func.count(Mill.id).label("mill_total"),
                grinding_count.label("grinding_total"),
            )
            .outerjoin(Mill, Mill.workshop_id == Workshop.id)
            .group_by(Workshop.id, Workshop.name)
            .order_by(Workshop.id)
        ).all()
        by_workshop = [
            {
                "workshopId": row.id,
                "workshopName": row.name,
                "grindingMillCount": int(row.grinding_total),
                "millTotal": int(row.mill_total),
            }
            for row in by_workshop_rows
        ]

        return jsonify(
            {
                "workshopTotal": workshop_total,
                "grindingMillCount": grinding_mill_count,
                "samplesLast24h": samples_last_24h,
                "passesLast7d": passes_last_7d,
                "byWorkshop": by_workshop,
            }
        )
    finally:
        db.close()
