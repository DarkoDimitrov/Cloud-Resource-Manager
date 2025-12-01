from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import or_, and_
from typing import Optional
from datetime import datetime

from ..database import get_db
from ..models import Instance, Provider
from ..schemas.instance import InstanceResponse, InstanceListResponse, InstanceStatsResponse

router = APIRouter()


@router.get("/", response_model=InstanceListResponse)
def list_instances(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    provider: Optional[str] = None,
    status: Optional[str] = None,
    region: Optional[str] = None,
    search: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """List all instances with optional filters."""
    query = db.query(Instance)

    # Apply filters
    if provider:
        query = query.join(Provider).filter(Provider.provider_type == provider)

    if status:
        query = query.filter(Instance.status == status)

    if region:
        query = query.filter(Instance.region == region)

    if search:
        search_pattern = f"%{search}%"
        query = query.filter(
            or_(
                Instance.name.ilike(search_pattern),
                Instance.provider_instance_id.ilike(search_pattern)
            )
        )

    # Get total count
    total = query.count()

    # Get paginated results
    instances = query.order_by(Instance.last_updated.desc()).offset(skip).limit(limit).all()

    return {
        "total": total,
        "limit": limit,
        "offset": skip,
        "instances": instances
    }


@router.get("/stats", response_model=InstanceStatsResponse)
def get_instance_stats(db: Session = Depends(get_db)):
    """Get aggregate instance statistics."""
    instances = db.query(Instance).all()

    total_instances = len(instances)
    running_instances = sum(1 for inst in instances if inst.status == "running")
    stopped_instances = sum(1 for inst in instances if inst.status in ["stopped", "shutoff"])
    total_monthly_cost = sum(inst.monthly_cost for inst in instances)

    # Group by provider
    by_provider = {}
    for inst in instances:
        provider = db.query(Provider).filter(Provider.id == inst.provider_id).first()
        if provider:
            provider_type = provider.provider_type
            by_provider[provider_type] = by_provider.get(provider_type, 0) + 1

    # Group by region
    by_region = {}
    for inst in instances:
        by_region[inst.region] = by_region.get(inst.region, 0) + 1

    return {
        "total_instances": total_instances,
        "running_instances": running_instances,
        "stopped_instances": stopped_instances,
        "total_monthly_cost": total_monthly_cost,
        "by_provider": by_provider,
        "by_region": by_region
    }


@router.get("/{instance_id}", response_model=InstanceResponse)
def get_instance(instance_id: str, db: Session = Depends(get_db)):
    """Get details for a specific instance."""
    instance = db.query(Instance).filter(Instance.id == instance_id).first()

    if not instance:
        raise HTTPException(status_code=404, detail=f"Instance {instance_id} not found")

    return instance


@router.post("/{instance_id}/refresh")
def refresh_instance(instance_id: str, db: Session = Depends(get_db)):
    """Refresh instance data from cloud provider."""
    from ..services.instance_service import refresh_instance as refresh_service

    instance = db.query(Instance).filter(Instance.id == instance_id).first()

    if not instance:
        raise HTTPException(status_code=404, detail=f"Instance {instance_id} not found")

    try:
        updated = refresh_service(db, instance)
        return {
            "instance_id": instance_id,
            "status": "refreshed",
            "refreshed_at": datetime.utcnow()
        }

    except Exception as e:
        raise HTTPException(
            status_code=400,
            detail=f"Failed to refresh instance: {str(e)}"
        )


@router.post("/{instance_id}/start")
def start_instance(instance_id: str, db: Session = Depends(get_db)):
    """Start a stopped instance."""
    from ..services.instance_service import start_instance as start_service

    instance = db.query(Instance).filter(Instance.id == instance_id).first()

    if not instance:
        raise HTTPException(status_code=404, detail=f"Instance {instance_id} not found")

    try:
        success = start_service(db, instance)

        if success:
            return {
                "instance_id": instance_id,
                "action": "start",
                "status": "success",
                "message": "Instance start initiated"
            }
        else:
            raise HTTPException(status_code=400, detail="Failed to start instance")

    except Exception as e:
        raise HTTPException(
            status_code=400,
            detail=f"Failed to start instance: {str(e)}"
        )


@router.post("/{instance_id}/stop")
def stop_instance(instance_id: str, db: Session = Depends(get_db)):
    """Stop a running instance."""
    from ..services.instance_service import stop_instance as stop_service

    instance = db.query(Instance).filter(Instance.id == instance_id).first()

    if not instance:
        raise HTTPException(status_code=404, detail=f"Instance {instance_id} not found")

    try:
        success = stop_service(db, instance)

        if success:
            return {
                "instance_id": instance_id,
                "action": "stop",
                "status": "success",
                "message": "Instance stop initiated"
            }
        else:
            raise HTTPException(status_code=400, detail="Failed to stop instance")

    except Exception as e:
        raise HTTPException(
            status_code=400,
            detail=f"Failed to stop instance: {str(e)}"
        )
