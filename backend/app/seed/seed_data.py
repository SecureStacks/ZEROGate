from sqlalchemy.orm import Session
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
from app.schemas.context import DemoScenarioSchema, NetworkContextSchema, BehavioralContextSchema

from app.core.security import get_password_hash
from app.core.config import settings

def seed_database(db: Session):
    """Seed the database with deterministic demo users, devices, resources, and access contexts."""
    
    # 1. Seed Users if not already present
    existing_users = {u.username: u for u in db.query(User).all()}
    
    user_password_hash = get_password_hash(settings.DEMO_USER_PASSWORD)
    admin_password_hash = get_password_hash(settings.ADMIN_PASSWORD)

    user_definitions = [
        {
            "username": "alice",
            "display_name": "Alice Chen",
            "email": "alice@zerogate.local",
            "hashed_password": user_password_hash,
            "role": UserRole.DEVELOPER,
            "department": "Engineering",
            "status": UserStatus.ACTIVE,
        },
        {
            "username": "bob",
            "display_name": "Bob Martinez",
            "email": "bob@zerogate.local",
            "hashed_password": user_password_hash,
            "role": UserRole.HR,
            "department": "Human Resources",
            "status": UserStatus.ACTIVE,
        },
        {
            "username": "carol",
            "display_name": "Carol Vance",
            "email": "carol@zerogate.local",
            "hashed_password": user_password_hash,
            "role": UserRole.FINANCE,
            "department": "Finance",
            "status": UserStatus.ACTIVE,
        },
        {
            "username": "admin",
            "display_name": "David Kim (Admin)",
            "email": "admin@zerogate.local",
            "hashed_password": admin_password_hash,
            "role": UserRole.ADMIN,
            "department": "IT",
            "status": UserStatus.ACTIVE,
        },
        {
            "username": "vendor-01",
            "display_name": "External Vendor 01",
            "email": "vendor01@zerogate.local",
            "hashed_password": user_password_hash,
            "role": UserRole.VENDOR,
            "department": "External",
            "status": UserStatus.ACTIVE,
        },
    ]

    for udef in user_definitions:
        if udef["username"] not in existing_users:
            user = User(**udef)
            db.add(user)
            db.flush()
            existing_users[udef["username"]] = user

    # 2. Seed Devices
    existing_devices = {d.device_name: d for d in db.query(Device).all()}
    
    device_definitions = [
        {
            "device_name": "Alice MacBook Pro (Corporate)",
            "device_type": DeviceType.LAPTOP,
            "operating_system": "macOS Sonoma 14.4",
            "owner_user_id": existing_users["alice"].id,
            "posture_status": DevicePosture.HEALTHY,
            "managed": True,
            "encrypted": True,
            "compromised": False,
        },
        {
            "device_name": "Alice Personal Tablet (BYOD)",
            "device_type": DeviceType.MOBILE,
            "operating_system": "iPadOS 17.2",
            "owner_user_id": existing_users["alice"].id,
            "posture_status": DevicePosture.UNKNOWN,
            "managed": False,
            "encrypted": True,
            "compromised": False,
        },
        {
            "device_name": "Alice Compromised Workstation",
            "device_type": DeviceType.DESKTOP,
            "operating_system": "Ubuntu 22.04 LTS (Rootkit Detected)",
            "owner_user_id": existing_users["alice"].id,
            "posture_status": DevicePosture.COMPROMISED,
            "managed": True,
            "encrypted": False,
            "compromised": True,
        },
        {
            "device_name": "Bob HR Workstation",
            "device_type": DeviceType.DESKTOP,
            "operating_system": "Windows 11 Enterprise",
            "owner_user_id": existing_users["bob"].id,
            "posture_status": DevicePosture.HEALTHY,
            "managed": True,
            "encrypted": True,
            "compromised": False,
        },
        {
            "device_name": "Carol Finance ThinkPad",
            "device_type": DeviceType.LAPTOP,
            "operating_system": "Windows 11 Enterprise",
            "owner_user_id": existing_users["carol"].id,
            "posture_status": DevicePosture.HEALTHY,
            "managed": True,
            "encrypted": True,
            "compromised": False,
        },
        {
            "device_name": "Admin Terminal",
            "device_type": DeviceType.LAPTOP,
            "operating_system": "macOS Sonoma 14.4 (Hardened)",
            "owner_user_id": existing_users["admin"].id,
            "posture_status": DevicePosture.HEALTHY,
            "managed": True,
            "encrypted": True,
            "compromised": False,
        },
        {
            "device_name": "Vendor Contractor Laptop",
            "device_type": DeviceType.LAPTOP,
            "operating_system": "Windows 10 Home (Unpatched)",
            "owner_user_id": existing_users["vendor-01"].id,
            "posture_status": DevicePosture.UNHEALTHY,
            "managed": False,
            "encrypted": False,
            "compromised": False,
        },
    ]

    for ddef in device_definitions:
        if ddef["device_name"] not in existing_devices:
            dev = Device(**ddef)
            db.add(dev)
            db.flush()
            existing_devices[ddef["device_name"]] = dev

    # 3. Seed Resources
    existing_resources = {r.name: r for r in db.query(Resource).all()}
    
    resource_definitions = [
        {
            "name": "Git Repository",
            "resource_type": "Source Code SCM",
            "sensitivity": ResourceSensitivity.HIGH,
            "network_segment": "Development",
            "host": "git.zerogate.internal",
            "port": 443,
            "protocol": "HTTPS",
            "description": "Core source code repositories and version control.",
            "enabled": True,
        },
        {
            "name": "HR Database",
            "resource_type": "Relational DB",
            "sensitivity": ResourceSensitivity.HIGH,
            "network_segment": "HR_Secure",
            "host": "hr-db.zerogate.internal",
            "port": 5432,
            "protocol": "PostgreSQL",
            "description": "Confidential employee records, payroll, and PII.",
            "enabled": True,
        },
        {
            "name": "Finance Database",
            "resource_type": "Relational DB",
            "sensitivity": ResourceSensitivity.CRITICAL,
            "network_segment": "Finance_Core",
            "host": "fin-db.zerogate.internal",
            "port": 5432,
            "protocol": "PostgreSQL",
            "description": "General ledger, financial transactions, and banking keys.",
            "enabled": True,
        },
        {
            "name": "CI/CD Server",
            "resource_type": "Build Automation",
            "sensitivity": ResourceSensitivity.HIGH,
            "network_segment": "Development",
            "host": "cicd.zerogate.internal",
            "port": 8080,
            "protocol": "HTTPS",
            "description": "Continuous integration pipelines and deployment runners.",
            "enabled": True,
        },
        {
            "name": "Cloud Infrastructure",
            "resource_type": "Cloud Console / IAM",
            "sensitivity": ResourceSensitivity.CRITICAL,
            "network_segment": "Cloud_Admin",
            "host": "cloud.zerogate.internal",
            "port": 443,
            "protocol": "HTTPS",
            "description": "Production Kubernetes clusters, VPCs, and root credentials.",
            "enabled": True,
        },
        {
            "name": "Internal API",
            "resource_type": "Microservice Gateway",
            "sensitivity": ResourceSensitivity.MEDIUM,
            "network_segment": "API_Gateway",
            "host": "api.zerogate.internal",
            "port": 8443,
            "protocol": "HTTPS",
            "description": "Core business backend APIs and microservices.",
            "enabled": True,
        },
    ]

    for rdef in resource_definitions:
        if rdef["name"] not in existing_resources:
            res = Resource(**rdef)
            db.add(res)
            db.flush()
            existing_resources[rdef["name"]] = res

    # 4. Seed sample Access Requests if table is empty
    if db.query(AccessRequest).count() == 0:
        sample_requests = [
            AccessRequest(
                user_id=existing_users["alice"].id,
                device_id=existing_devices["Alice MacBook Pro (Corporate)"].id,
                resource_id=existing_resources["Git Repository"].id,
                source_ip="10.0.4.15",
                ip_reputation=IPReputation.TRUSTED,
                network_type=NetworkType.CORPORATE,
                is_vpn=False,
                is_tor=False,
                is_known_network=True,
                source_segment="Development",
                country="India",
                city="Bengaluru",
                unusual_time=False,
                unusual_location=False,
                unusual_resource=False,
                failed_attempts=0,
                recent_resource_count=1,
            ),
            AccessRequest(
                user_id=existing_users["alice"].id,
                device_id=existing_devices["Alice Personal Tablet (BYOD)"].id,
                resource_id=existing_resources["Git Repository"].id,
                source_ip="198.51.100.42",
                ip_reputation=IPReputation.UNKNOWN,
                network_type=NetworkType.PUBLIC_WIFI,
                is_vpn=True,
                is_tor=False,
                is_known_network=False,
                source_segment="Development",
                country="India",
                city="Mumbai",
                unusual_time=False,
                unusual_location=False,
                unusual_resource=False,
                failed_attempts=0,
                recent_resource_count=1,
            ),
            AccessRequest(
                user_id=existing_users["alice"].id,
                device_id=existing_devices["Alice Compromised Workstation"].id,
                resource_id=existing_resources["HR Database"].id,
                source_ip="185.220.101.5",
                ip_reputation=IPReputation.MALICIOUS,
                network_type=NetworkType.UNKNOWN,
                is_vpn=False,
                is_tor=True,
                is_known_network=False,
                source_segment="Development",
                country="Unknown/Tor Exit",
                city="Anonymous",
                unusual_time=True,
                unusual_location=True,
                unusual_resource=True,
                failed_attempts=4,
                recent_resource_count=7,
            ),
        ]
        db.add_all(sample_requests)

    db.commit()


def get_demo_scenarios(db: Session) -> list[DemoScenarioSchema]:
    """Retrieve deterministic demo context scenarios with live entity IDs."""
    users = {u.username: u for u in db.query(User).all()}
    devices = {d.device_name: d for d in db.query(Device).all()}
    resources = {r.name: r for r in db.query(Resource).all()}

    alice = users.get("alice")
    alice_corp_mac = devices.get("Alice MacBook Pro (Corporate)")
    alice_tablet = devices.get("Alice Personal Tablet (BYOD)")
    alice_compromised = devices.get("Alice Compromised Workstation")
    git_repo = resources.get("Git Repository")
    hr_db = resources.get("HR Database")

    return [
        DemoScenarioSchema(
            id="scenario-a",
            name="Scenario A — Normal Developer Access",
            description="Alice accesses Git Repository from a healthy corporate device on a trusted internal network with low risk signals.",
            user_id=alice.id if alice else None,
            username="alice",
            user_role="Developer",
            device_id=alice_corp_mac.id if alice_corp_mac else None,
            device_name="Alice MacBook Pro (Corporate)",
            device_posture="Healthy",
            resource_id=git_repo.id if git_repo else None,
            resource_name="Git Repository",
            network=NetworkContextSchema(
                source_ip="10.0.4.15",
                ip_reputation=IPReputation.TRUSTED,
                network_type=NetworkType.CORPORATE,
                is_vpn=False,
                is_tor=False,
                is_known_network=True,
                source_segment="Development",
                country="India",
                city="Bengaluru",
            ),
            behavior=BehavioralContextSchema(
                unusual_time=False,
                unusual_location=False,
                unusual_resource=False,
                failed_attempts=0,
                recent_resource_count=1,
            ),
        ),
        DemoScenarioSchema(
            id="scenario-b",
            name="Scenario B — Suspicious Access & Step-up MFA",
            description="Alice accesses Git Repository from a new/unknown device over a public WiFi network via a suspicious IP.",
            user_id=alice.id if alice else None,
            username="alice",
            user_role="Developer",
            device_id=alice_tablet.id if alice_tablet else None,
            device_name="Alice Personal Tablet (BYOD)",
            device_posture="Unknown",
            resource_id=git_repo.id if git_repo else None,
            resource_name="Git Repository",
            network=NetworkContextSchema(
                source_ip="198.51.100.42",
                ip_reputation=IPReputation.UNKNOWN,
                network_type=NetworkType.PUBLIC_WIFI,
                is_vpn=False,
                is_tor=False,
                is_known_network=False,
                source_segment="Development",
                country="India",
                city="Mumbai",
            ),
            behavior=BehavioralContextSchema(
                unusual_time=False,
                unusual_location=False,
                unusual_resource=False,
                failed_attempts=0,
                recent_resource_count=1,
            ),
        ),
        DemoScenarioSchema(
            id="scenario-c",
            name="Scenario C — Breach Attempt & Lateral Movement Block",
            description="Compromised session using a compromised device and malicious IP attempting unauthorized access to the sensitive HR Database.",
            user_id=alice.id if alice else None,
            username="alice",
            user_role="Developer",
            device_id=alice_compromised.id if alice_compromised else None,
            device_name="Alice Compromised Workstation",
            device_posture="Compromised",
            resource_id=hr_db.id if hr_db else None,
            resource_name="HR Database",
            network=NetworkContextSchema(
                source_ip="185.220.101.5",
                ip_reputation=IPReputation.MALICIOUS,
                network_type=NetworkType.UNKNOWN,
                is_vpn=False,
                is_tor=True,
                is_known_network=False,
                source_segment="Development",
                country="Unknown/Tor Exit",
                city="Anonymous",
            ),
            behavior=BehavioralContextSchema(
                unusual_time=True,
                unusual_location=True,
                unusual_resource=True,
                failed_attempts=4,
                recent_resource_count=7,
            ),
        ),
    ]
