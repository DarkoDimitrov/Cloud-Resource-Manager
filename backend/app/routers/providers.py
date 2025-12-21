from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from datetime import datetime

from ..database import get_db
from ..models import Provider
from ..schemas.provider import ProviderCreate, ProviderUpdate, ProviderResponse
from ..utils.encryption import encrypt_credentials, decrypt_credentials
from ..adapters import get_adapter

router = APIRouter()


@router.post("/", response_model=ProviderResponse, status_code=status.HTTP_201_CREATED)
def create_provider(provider: ProviderCreate, db: Session = Depends(get_db)):
    """Create a new cloud provider configuration."""
    try:
        # Encrypt credentials
        encrypted_creds = encrypt_credentials(provider.credentials)

        # Create provider
        db_provider = Provider(
            name=provider.name,
            provider_type=provider.provider_type,
            credentials=encrypted_creds,
            regions=provider.regions,
            enabled=provider.enabled
        )

        db.add(db_provider)
        db.commit()
        db.refresh(db_provider)

        # Test connection
        try:
            adapter = get_adapter(provider.provider_type, provider.credentials)
            if not adapter.test_connection():
                # Mark as disabled if connection fails
                db_provider.enabled = False
                db.commit()
                db.refresh(db_provider)
        except Exception as e:
            print(f"Failed to test provider connection: {e}")

        return db_provider

    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to create provider: {str(e)}"
        )


@router.get("/", response_model=List[ProviderResponse])
def list_providers(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    """List all cloud provider configurations."""
    providers = db.query(Provider).offset(skip).limit(limit).all()

    # Add instance count and cost (simplified - would be better as a join)
    for provider in providers:
        provider.instance_count = len(provider.instances)
        provider.monthly_cost = sum(inst.monthly_cost for inst in provider.instances)

    return providers


@router.get("/{provider_id}", response_model=ProviderResponse)
def get_provider(provider_id: str, db: Session = Depends(get_db)):
    """Get a specific provider configuration."""
    provider = db.query(Provider).filter(Provider.id == provider_id).first()

    if not provider:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Provider {provider_id} not found"
        )

    # Add instance count and cost
    provider.instance_count = len(provider.instances)
    provider.monthly_cost = sum(inst.monthly_cost for inst in provider.instances)

    return provider


@router.put("/{provider_id}", response_model=ProviderResponse)
def update_provider(
    provider_id: str,
    provider_update: ProviderUpdate,
    db: Session = Depends(get_db)
):
    """Update a provider configuration."""
    db_provider = db.query(Provider).filter(Provider.id == provider_id).first()

    if not db_provider:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Provider {provider_id} not found"
        )

    try:
        # Update fields
        if provider_update.name is not None:
            db_provider.name = provider_update.name

        if provider_update.credentials is not None:
            encrypted_creds = encrypt_credentials(provider_update.credentials)
            db_provider.credentials = encrypted_creds

        if provider_update.regions is not None:
            db_provider.regions = provider_update.regions

        if provider_update.enabled is not None:
            db_provider.enabled = provider_update.enabled

        db_provider.updated_at = datetime.utcnow()

        db.commit()
        db.refresh(db_provider)

        return db_provider

    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to update provider: {str(e)}"
        )


@router.delete("/{provider_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_provider(provider_id: str, db: Session = Depends(get_db)):
    """Delete a provider configuration."""
    db_provider = db.query(Provider).filter(Provider.id == provider_id).first()

    if not db_provider:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Provider {provider_id} not found"
        )

    try:
        db.delete(db_provider)
        db.commit()
        return None

    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to delete provider: {str(e)}"
        )


@router.post("/{provider_id}/test", status_code=status.HTTP_200_OK)
def test_provider_connection(provider_id: str, db: Session = Depends(get_db)):
    """Test connection to a cloud provider."""
    db_provider = db.query(Provider).filter(Provider.id == provider_id).first()

    if not db_provider:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Provider {provider_id} not found"
        )

    try:
        # Decrypt credentials
        credentials = decrypt_credentials(db_provider.credentials)

        # Test connection
        adapter = get_adapter(db_provider.provider_type, credentials)
        connection_ok = adapter.test_connection()

        return {
            "provider_id": provider_id,
            "status": "success" if connection_ok else "error",
            "message": "Connection successful" if connection_ok else "Connection failed"
        }

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Connection test failed: {str(e)}"
        )


@router.post("/{provider_id}/sync", status_code=status.HTTP_200_OK)
def sync_provider_instances(provider_id: str, db: Session = Depends(get_db)):
    """Sync instances from cloud provider."""
    from ..services.instance_service import sync_provider_instances as sync_service

    db_provider = db.query(Provider).filter(Provider.id == provider_id).first()

    if not db_provider:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Provider {provider_id} not found"
        )

    try:
        count = sync_service(db, db_provider)
        return {
            "provider_id": provider_id,
            "instances_synced": count,
            "synced_at": datetime.utcnow()
        }

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Sync failed: {str(e)}"
        )
