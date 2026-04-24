"""Constants for Hotata Airer integration."""

POLL_INTERVAL = 5
API_BASE = "https://saas.keyoo.com/app-api/v2.0"
API_REFRESH_TOKEN = f"{API_BASE}/login/spLogin/refreshToken"
API_DEVICE_LIST = f"{API_BASE}/sp/device/getSpDeviceList"
API_PROPERTY_GET = f"{API_BASE}/device/property/get"
API_PROPERTY_SET = f"{API_BASE}/device/property/set2"
API_INVOKE2 = f"{API_BASE}/device/service/invoke2"
API_ONLINE_STATUS = f"{API_BASE}/device/synOnlineStatus"

# App fixed parameters (from APK/HAR analysis)
APP_KEY = "miniapp-hotata-prod"
APP_SECRET = "B322B40A-DBD2-26A2-F935-6E760917CB73"
APP_VERSION = "miniapp_4.4.5.1"
IMEI = "Windows 10 x64_w4.1.7.33_s3.14.3"
PHONE_MODEL = "microsoft"
SYS_VERSION = "Windows 10 x64"

DEFAULT_NAME = "好太太晾衣机"

# Config entry keys
CONF_REFRESH_TOKEN = "refresh_token"
CONF_ACCESS_TOKEN = "access_token"
CONF_USER_ID = "userId"
CONF_IOT_ID = "iotId"
CONF_NAME = "name"

DOMAIN = "hotata_airer"
