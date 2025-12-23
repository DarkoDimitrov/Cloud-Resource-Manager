from sqlalchemy.orm import Session
from datetime import datetime
from typing import List

from ..models import Instance, Provider
from ..adapters import get_adapter
from ..utils.encryption import decrypt_credentials


def sync_provider_instances(db: Session, provider: Provider) -> int:
    """Sync instances from a cloud provider.

    Args:
        db: Database session
        provider: Provider configuration

    Returns:
        Number of instances synced
    """
    try:
        # Store provider ID for later refetch
        provider_id = str(provider.id)

        # Decrypt credentials
        credentials = decrypt_credentials(provider.credentials)

        # Get adapter
        adapter = get_adapter(provider.provider_type, credentials)

        # Fetch instances from cloud
        cloud_instances = adapter.list_instances()

        # Update or create instances in database
        count = 0
        for cloud_inst in cloud_instances:
            # Check if instance exists
            existing = db.query(Instance).filter(
                Instance.provider_id == provider_id,
                Instance.provider_instance_id == cloud_inst["provider_instance_id"]
            ).first()

            if existing:
                # Update existing instance (don't update provider_id)
                for key, value in cloud_inst.items():
                    if key != 'provider_id':  # Don't overwrite provider_id
                        setattr(existing, key, value)
                existing.last_updated = datetime.utcnow()
            else:
                # Create new instance (ensure provider_id is set correctly)
                instance_data = dict(cloud_inst)
                instance_data.pop('provider_id', None)  # Remove provider_id if present
                new_instance = Instance(
                    provider_id=provider_id,
                    **instance_data
                )
                db.add(new_instance)

            count += 1

        # Refetch provider to ensure it's attached to the session
        db_provider = db.query(Provider).filter(Provider.id == provider_id).first()
        if db_provider:
            db_provider.last_sync = datetime.utcnow()

        db.commit()
        return count

    except Exception as e:
        db.rollback()
        import traceback
        print(f"Failed to sync instances for provider {provider_id}: {e}")
        print("Full traceback:")
        traceback.print_exc()
        raise


def refresh_instance(db: Session, instance: Instance) -> bool:
    """Refresh a single instance from cloud provider.

    Args:
        db: Database session
        instance: Instance to refresh

    Returns:
        True if successful
    """
    try:
        # Get provider
        provider = db.query(Provider).filter(Provider.id == instance.provider_id).first()
        if not provider:
            raise ValueError(f"Provider not found for instance {instance.id}")

        # Decrypt credentials
        credentials = decrypt_credentials(provider.credentials)

        # Get adapter
        adapter = get_adapter(provider.provider_type, credentials)

        # Fetch instance from cloud
        cloud_inst = adapter.get_instance(instance.provider_instance_id)

        # Update instance
        for key, value in cloud_inst.items():
            if hasattr(instance, key):
                setattr(instance, key, value)

        instance.last_updated = datetime.utcnow()

        db.commit()
        return True

    except Exception as e:
        db.rollback()
        print(f"Failed to refresh instance {instance.id}: {e}")
        raise


def start_instance(db: Session, instance: Instance) -> bool:
    """Start a stopped instance.

    Args:
        db: Database session
        instance: Instance to start

    Returns:
        True if successful
    """
    try:
        # Get provider
        provider = db.query(Provider).filter(Provider.id == instance.provider_id).first()
        if not provider:
            raise ValueError(f"Provider not found for instance {instance.id}")

        # Decrypt credentials
        credentials = decrypt_credentials(provider.credentials)

        # Get adapter
        adapter = get_adapter(provider.provider_type, credentials)

        # Start instance
        success = adapter.start_instance(instance.provider_instance_id)

        if success:
            # Update status (will be synced properly later)
            instance.status = "starting"
            instance.last_updated = datetime.utcnow()
            db.commit()

        return success

    except Exception as e:
        print(f"Failed to start instance {instance.id}: {e}")
        raise


def stop_instance(db: Session, instance: Instance) -> bool:
    """Stop a running instance.

    Args:
        db: Database session
        instance: Instance to stop

    Returns:
        True if successful
    """
    try:
        # Get provider
        provider = db.query(Provider).filter(Provider.id == instance.provider_id).first()
        if not provider:
            raise ValueError(f"Provider not found for instance {instance.id}")

        # Decrypt credentials
        credentials = decrypt_credentials(provider.credentials)

        # Get adapter
        adapter = get_adapter(provider.provider_type, credentials)

        # Stop instance
        success = adapter.stop_instance(instance.provider_instance_id)

        if success:
            # Update status (will be synced properly later)
            instance.status = "stopping"
            instance.last_updated = datetime.utcnow()
            db.commit()

        return success

    except Exception as e:
        print(f"Failed to stop instance {instance.id}: {e}")
        raise


def resize_instance(db: Session, instance: Instance, new_instance_type: str) -> bool:
    """Resize an instance to a different type.

    Args:
        db: Database session
        instance: Instance to resize
        new_instance_type: New instance type/flavor

    Returns:
        True if successful
    """
    try:
        # Get provider
        provider = db.query(Provider).filter(Provider.id == instance.provider_id).first()
        if not provider:
            raise ValueError(f"Provider not found for instance {instance.id}")

        # Decrypt credentials
        credentials = decrypt_credentials(provider.credentials)

        # Get adapter
        adapter = get_adapter(provider.provider_type, credentials)

        # Resize instance
        success = adapter.resize_instance(instance.provider_instance_id, new_instance_type)

        if success:
            # Update instance type
            instance.instance_type = new_instance_type
            instance.last_updated = datetime.utcnow()
            db.commit()

        return success

    except Exception as e:
        print(f"Failed to resize instance {instance.id}: {e}")
        raise
