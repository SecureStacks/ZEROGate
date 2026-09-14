import pytest
from app.models.enums import (
    UserRole,
    UserStatus,
    DeviceType,
    DevicePosture,
    ResourceSensitivity,
    IPReputation,
    NetworkType,
)
from app.models.user import User
from app.models.device import Device
from app.models.resource import Resource
from app.models.access_request import AccessRequest

def test_user_model_creation(db_session):
    user = User(
        username="test_user",
        display_name="Test User",
        email="test_user@zerogate.internal",
        role=UserRole.DEVELOPER,
        department="Engineering",
        status=UserStatus.ACTIVE,
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)

    assert user.id is not None
    assert user.username == "test_user"
    assert user.role == UserRole.DEVELOPER
    assert user.status == UserStatus.ACTIVE
    assert user.created_at is not None

def test_device_user_relationship(db_session):
    user = User(
        username="device_owner",
        display_name="Device Owner",
        email="owner@zerogate.internal",
        role=UserRole.HR,
        department="Human Resources",
    )
    db_session.add(user)
    db_session.commit()

    device = Device(
        device_name="Owner MacBook Pro",
        device_type=DeviceType.LAPTOP,
        operating_system="macOS 14",
        owner_user_id=user.id,
        posture_status=DevicePosture.HEALTHY,
        managed=True,
        encrypted=True,
        compromised=False,
    )
    db_session.add(device)
    db_session.commit()
    db_session.refresh(device)

    assert device.owner.username == "device_owner"
    assert len(user.devices) == 1
    assert user.devices[0].device_name == "Owner MacBook Pro"

def test_resource_model(db_session):
    resource = Resource(
        name="Test Secure Vault",
        resource_type="Secret Manager",
        sensitivity=ResourceSensitivity.CRITICAL,
        network_segment="Security_Core",
        host="vault.zerogate.internal",
        port=8200,
        protocol="HTTPS",
        enabled=True,
    )
    db_session.add(resource)
    db_session.commit()
    db_session.refresh(resource)

    assert resource.id is not None
    assert resource.sensitivity == ResourceSensitivity.CRITICAL
    assert resource.network_segment == "Security_Core"
    assert resource.enabled is True

def test_access_request_context_model(db_session):
    user = User(
        username="requester_user",
        display_name="Requester",
        email="requester@zerogate.internal",
        role=UserRole.FINANCE,
        department="Finance",
    )
    db_session.add(user)
    db_session.commit()

    device = Device(
        device_name="Requester Laptop",
        device_type=DeviceType.LAPTOP,
        owner_user_id=user.id,
        posture_status=DevicePosture.HEALTHY,
    )
    db_session.add(device)

    resource = Resource(
        name="Target DB",
        resource_type="DB",
        sensitivity=ResourceSensitivity.HIGH,
        network_segment="Finance_Segment",
    )
    db_session.add(resource)
    db_session.commit()

    access_req = AccessRequest(
        user_id=user.id,
        device_id=device.id,
        resource_id=resource.id,
        source_ip="192.168.1.50",
        ip_reputation=IPReputation.TRUSTED,
        network_type=NetworkType.CORPORATE,
        country="India",
        city="Bengaluru",
        unusual_time=False,
        unusual_location=False,
        unusual_resource=False,
        failed_attempts=0,
        source_segment="Development",
    )
    db_session.add(access_req)
    db_session.commit()
    db_session.refresh(access_req)

    assert access_req.id is not None
    assert access_req.user.username == "requester_user"
    assert access_req.device.device_name == "Requester Laptop"
    assert access_req.resource.name == "Target DB"
    assert access_req.ip_reputation == IPReputation.TRUSTED
