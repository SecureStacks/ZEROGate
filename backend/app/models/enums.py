from enum import Enum

class UserRole(str, Enum):
    DEVELOPER = "Developer"
    HR = "HR"
    FINANCE = "Finance"
    ADMIN = "Admin"
    VENDOR = "Vendor"

class UserStatus(str, Enum):
    ACTIVE = "Active"
    DISABLED = "Disabled"

class DeviceType(str, Enum):
    LAPTOP = "Laptop"
    DESKTOP = "Desktop"
    MOBILE = "Mobile"
    SERVER = "Server"

class DevicePosture(str, Enum):
    HEALTHY = "Healthy"
    UNHEALTHY = "Unhealthy"
    UNKNOWN = "Unknown"
    COMPROMISED = "Compromised"

class ResourceSensitivity(str, Enum):
    LOW = "Low"
    MEDIUM = "Medium"
    HIGH = "High"
    CRITICAL = "Critical"

class IPReputation(str, Enum):
    TRUSTED = "Trusted"
    UNKNOWN = "Unknown"
    SUSPICIOUS = "Suspicious"
    MALICIOUS = "Malicious"

class NetworkType(str, Enum):
    CORPORATE = "Corporate"
    HOME = "Home"
    PUBLIC_WIFI = "Public WiFi"
    MOBILE = "Mobile"
    UNKNOWN = "Unknown"

class PolicyEffect(str, Enum):
    ALLOW = "ALLOW"
    DENY = "DENY"
    MFA_REQUIRED = "MFA_REQUIRED"
