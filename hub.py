"""Core Hub for Hotata Airer Simple API communication."""

from __future__ import annotations

import asyncio
import hashlib
import json
import logging
import time
from dataclasses import dataclass, field
from datetime import timedelta
from typing import Any, Callable

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers import httpx_client
from homeassistant.helpers.event import async_track_time_interval

from .const import (
    API_INVOKE2,
    API_ONLINE_STATUS,
    API_PROPERTY_GET,
    API_PROPERTY_SET,
    API_REFRESH_TOKEN,
    APP_KEY,
    APP_SECRET,
    APP_VERSION,
    CONF_ACCESS_TOKEN,
    CONF_IOT_ID,
    CONF_REFRESH_TOKEN,
    CONF_USER_ID,
    DEFAULT_NAME,
    IMEI,
    PHONE_MODEL,
    POLL_INTERVAL,
    SYS_VERSION,
)

_LOGGER = logging.getLogger(__name__)


@dataclass
class HotataState:
    """Represents the current state of the airer."""

    online: bool = False
    power_on: bool | None = None
    light_on: bool | None = None
    light_brightness: int | None = None
    drying_on: bool | None = None
    air_drying_on: bool | None = None
    disinfection_on: bool | None = None
    ions_on: bool | None = None
    position: int | None = None
    light_remaining_time: int | None = None
    drying_remaining_time: int | None = None
    air_drying_remaining_time: int | None = None
    ions_remaining_time: int | None = None
    disinfection_remaining_time: int | None = None
    motor_control_mode: int | None = None
    raw: dict[str, Any] = field(default_factory=dict)


@dataclass
class Listener:
    """Callback listener for state updates."""

    async_callback: Callable[[], Any]


class HotataHub:
    """Hub for communicating with Hotata cloud API."""

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry) -> None:
        """Initialize the hub."""
        self.hass = hass
        self.entry = entry
        self.name = entry.data.get("name", DEFAULT_NAME)
        self._access_token: str = entry.data[CONF_ACCESS_TOKEN]
        self._refresh_token: str = entry.data[CONF_REFRESH_TOKEN]
        self.user_id: str = entry.data[CONF_USER_ID]
        self.iot_id: str = entry.data[CONF_IOT_ID]
        self._expire_at: float = 0

        self.state = HotataState()
        self._listeners: list[Listener] = []
        self._unsub_poll: Callable[[], None] | None = None
        self._unsub_token_refresh: Callable[[], None] | None = None
        self._token_expired: bool = False
        self._refresh_in_progress: bool = False
        self._last_state_hash: str = ""

    @property
    def device_info(self) -> dict[str, Any]:
        """Return device info for HA device registry."""
        return {
            "identifiers": {("hotata_airer", self.iot_id)},
            "name": self.name,
            "manufacturer": "Hotata (好太太)",
            "model": "Smart Airer",
        }

    @property
    def access_token(self) -> str:
        """Return current access token."""
        return self._access_token

    @property
    def refresh_token_value(self) -> str:
        """Return current refresh token value."""
        return self._refresh_token

    @property
    def token_expired(self) -> bool:
        """Return True if token is expired."""
        return self._token_expired

    def add_listener(self, async_callback: Callable[[], Any]) -> Callable[[], None]:
        """Register a listener for state updates."""
        listener = Listener(async_callback=async_callback)
        self._listeners.append(listener)

        @callback
        def remove() -> None:
            if listener in self._listeners:
                self._listeners.remove(listener)

        return remove

    async def _notify_listeners(self) -> None:
        """Notify all registered listeners of a state change."""
        for listener in self._listeners:
            try:
                await listener.async_callback()
            except Exception:
                _LOGGER.exception("Error notifying listener")

    @staticmethod
    def generate_sign(payload: dict[str, Any]) -> str:
        """Generate MD5 signature for API request."""
        p = payload.copy()
        p.pop("sign", None)

        arr = []
        for k in sorted(p.keys()):
            v = p[k]
            if v is None or v == "":
                continue
            if isinstance(v, (dict, list)):
                continue
            arr.append(f"{k}={v}")

        raw = "&".join(arr) + APP_SECRET
        return hashlib.md5(raw.encode("utf8")).hexdigest()

    @staticmethod
    def build_base_payload(user_id: str, iot_id: str | None = None) -> dict[str, Any]:
        """Build common payload fields."""
        ts = int(time.time() * 1000)
        payload: dict[str, Any] = {
            "userid": user_id,
            "userId": user_id,
            "appKey": APP_KEY,
            "appVersion": APP_VERSION,
            "timestamp": ts,
            "traceId": f"ha_{ts}",
            "sysVersion": SYS_VERSION,
            "phoneModel": PHONE_MODEL,
            "imei": IMEI,
        }
        if iot_id:
            payload["iotId"] = iot_id
        return payload

    def _build_headers(self) -> dict[str, str]:
        """Build request headers with current token."""
        headers = {"content-type": "application/json"}
        if self._access_token:
            headers["authorization"] = self._access_token
        return headers

    async def _ensure_token_valid(self) -> bool:
        """Check if token is valid, refresh if needed."""
        # 如果token已标记为过期，强制刷新
        if self._token_expired:
            _LOGGER.debug("Token marked as expired, forcing refresh")
            return await self.async_refresh_token()

        # 检查是否即将过期（2分钟内）
        if self._expire_at > 0 and time.time() < self._expire_at - 120:
            _LOGGER.debug(
                "Token still valid (expires in %ds), skipping refresh",
                int(self._expire_at - time.time())
            )
            return True

        # 需要刷新
        return await self.async_refresh_token()

    async def async_refresh_token(self) -> bool:
        """Refresh the access token."""
        # 防止并发刷新
        if self._refresh_in_progress:
            _LOGGER.debug("Token refresh already in progress, waiting")
            for _ in range(30):
                if not self._refresh_in_progress:
                    return not self._token_expired
                await asyncio.sleep(0.1)
            return False

        self._refresh_in_progress = True
        try:
            async with httpx_client.get_async_client(self.hass) as client:
                ts = int(time.time() * 1000)
                payload = {
                    "refreshToken": self._refresh_token,
                    "userid": self.user_id,
                    "userId": self.user_id,
                    "appKey": APP_KEY,
                    "appVersion": APP_VERSION,
                    "timestamp": ts,
                    "traceId": f"refresh_{ts}",
                    "sysVersion": SYS_VERSION,
                    "phoneModel": PHONE_MODEL,
                    "imei": IMEI,
                }
                payload["sign"] = self.generate_sign(payload)

                resp = await client.post(
                    API_REFRESH_TOKEN,
                    json=payload,
                    headers={"content-type": "application/json"},
                    timeout=10,
                )
                data = resp.json()
                _LOGGER.debug("Refresh API response: code=%s", data.get("code"))

                if data.get("code") == "000":
                    d = data.get("data", {})
                    token_type = d.get("tokenType", "bearer").strip()
                    self._access_token = f"{token_type} {d['accessToken']}"
                    if d.get("refreshToken"):
                        self._refresh_token = d["refreshToken"]
                    expires_in = int(d.get("expiresIn", 2591999))
                    self._expire_at = time.time() + expires_in
                    # Persist new tokens
                    self.hass.config_entries.async_update_entry(
                        self.entry,
                        data={
                            **self.entry.data,
                            CONF_ACCESS_TOKEN: self._access_token,
                            CONF_REFRESH_TOKEN: self._refresh_token,
                        }
                    )
                    self._token_expired = False
                    _LOGGER.info("Token refreshed successfully")
                    return True
                else:
                    _LOGGER.warning("Token refresh failed: %s", data)
                    self._token_expired = True
                    return False
        except Exception as err:
            _LOGGER.warning("Token refresh error: %s", err)
            self._token_expired = True
            return False
        finally:
            self._refresh_in_progress = False

    async def _query_properties(self) -> HotataState | None:
        """Query device properties from API."""
        if not await self._ensure_token_valid():
            return None

        payload = self.build_base_payload(self.user_id, self.iot_id)
        payload["sign"] = self.generate_sign(payload)

        async with httpx_client.get_async_client(self.hass) as client:
            try:
                resp = await client.post(
                    API_PROPERTY_GET,
                    json=payload,
                    headers=self._build_headers(),
                    timeout=10,
                )
                data = resp.json()

                # Handle auth failure — try refresh and retry once
                if data.get("code") == "401":
                    _LOGGER.warning("Got 401, attempting token refresh")
                    self._token_expired = True
                    if await self.async_refresh_token():
                        # 重新构建payload（timestamp会更新）
                        payload = self.build_base_payload(self.user_id, self.iot_id)
                        payload["sign"] = self.generate_sign(payload)
                        resp = await client.post(
                            API_PROPERTY_GET,
                            json=payload,
                            headers=self._build_headers(),
                            timeout=10,
                        )
                        data = resp.json()
                    else:
                        return None

                if data.get("code") == "000":
                    self._token_expired = False
                    self._parse_state(data)
                    return self.state
                else:
                    _LOGGER.warning("Query failed: %s", data)
                    return None
            except Exception as err:
                _LOGGER.error("Query error: %s", err)
                self._token_expired = True
                return None

    def _state_hash(self) -> str:
        """Compute hash of all state fields for change detection."""
        s = self.state
        key_fields = (
            f"{s.online}",
            f"{s.power_on}",
            f"{s.light_on}",
            f"{s.light_brightness}",
            f"{s.drying_on}",
            f"{s.air_drying_on}",
            f"{s.disinfection_on}",
            f"{s.ions_on}",
            f"{s.position}",
            f"{s.motor_control_mode}",
            f"{s.light_remaining_time}",
            f"{s.drying_remaining_time}",
            f"{s.air_drying_remaining_time}",
            f"{s.ions_remaining_time}",
            f"{s.disinfection_remaining_time}",
        )
        return "|".join(str(f) for f in key_fields)

    def _parse_state(self, raw: dict[str, Any]) -> None:
        """Parse API response into state object."""
        data_array = raw.get("data", [])
        state_map: dict[str, Any] = {}

        if isinstance(data_array, list):
            for item in data_array:
                if "attribute" in item:
                    state_map[item["attribute"]] = item["value"]

        self.state.raw = state_map

        def get_value(*keys: str) -> Any:
            for key in keys:
                v = state_map.get(key)
                if v is not None and v != "":
                    return v
            return None

        # Position
        pos = get_value("Position")
        if pos is not None:
            try:
                self.state.position = int(float(pos))
            except (ValueError, TypeError):
                pass

        # Motor Control Mode
        motor_mode = get_value("MotorControlMode")
        if motor_mode is not None:
            try:
                self.state.motor_control_mode = int(float(motor_mode))
            except (ValueError, TypeError):
                pass

        # Switch states
        switch_mapping = {
            "PowerSwitch": "power_on",
            "LightSwitch": "light_on",
            "DryingSwitch": "drying_on",
            "AirDryingSwitch": "air_drying_on",
            "DisinfectionSwitch": "disinfection_on",
            "IonsSwitch": "ions_on",
        }
        for attr_name, state_attr in switch_mapping.items():
            val = get_value(attr_name)
            if val is not None:
                setattr(self.state, state_attr, val in (True, 1, "1", "true"))

        # Light brightness
        brightness = get_value("LightBrightness")
        if brightness is not None:
            try:
                self.state.light_brightness = int(float(brightness))
            except (ValueError, TypeError):
                pass

        # Remaining times
        time_mapping = {
            "LightRemainingTime": "light_remaining_time",
            "DryingRemainingTime": "drying_remaining_time",
            "AirDryingRemainingTime": "air_drying_remaining_time",
            "IonsRemainingTime": "ions_remaining_time",
            "DisinfectionRemainingTime": "disinfection_remaining_time",
        }
        for attr, field_name in time_mapping.items():
            val = get_value(attr)
            if val is not None:
                try:
                    setattr(self.state, field_name, int(float(val)))
                except (ValueError, TypeError):
                    pass

    async def async_update(self) -> None:
        """Poll device state and notify listeners only on change."""
        await self._check_online_status()
        state = await self._query_properties()
        if state is not None:
            current_hash = self._state_hash()
            if current_hash != self._last_state_hash:
                self._last_state_hash = current_hash
                await self._notify_listeners()

    async def _check_online_status(self) -> None:
        """Query device online status from API."""
        if not await self._ensure_token_valid():
            return

        payload = self.build_base_payload(self.user_id, self.iot_id)
        payload["sign"] = self.generate_sign(payload)

        async with httpx_client.get_async_client(self.hass) as client:
            try:
                resp = await client.post(
                    API_ONLINE_STATUS,
                    json=payload,
                    headers=self._build_headers(),
                    timeout=10,
                )
                data = resp.json()

                if data.get("code") == "000":
                    online = data.get("data", {}).get("onlineStatus", False)
                    if online != self.state.online:
                        self.state.online = online
                        _LOGGER.info("Device online status changed to: %s", online)
            except Exception as err:
                _LOGGER.error("Online status check error: %s", err)

    # ---- Control commands ----

    async def control_cover(self, action: str) -> bool:
        """Control the airer motor: up, down, stop."""
        prop_map = {
            "up": {"MotorControlMode": 1},
            "down": {"MotorControlMode": 2},
            "stop": {"MotorControlMode": 0},
        }
        if action not in prop_map:
            _LOGGER.error("Unknown cover action: %s", action)
            return False
        return await self._property_set(prop_map[action])

    async def control_switch(self, property_name: str, turn_on: bool) -> bool:
        """Control any device switch property."""
        return await self._property_set({property_name: 1 if turn_on else 0})

    async def set_brightness(self, brightness: int) -> bool:
        """Set light brightness (1-100) via invoke2."""
        brightness = max(1, min(100, brightness))
        return await self._invoke2(
            "LightBrightnessControl",
            {"Brightness": brightness},
        )

    async def _property_set(self, properties: dict[str, Any]) -> bool:
        """Send property set command via propertySet2 API."""
        if not await self._ensure_token_valid():
            return False

        payload = self.build_base_payload(self.user_id, self.iot_id)
        payload["paramJson"] = json.dumps(properties)
        payload["sign"] = self.generate_sign(payload)

        return await self._send_request(API_PROPERTY_SET, payload)

    async def _invoke2(self, service_name: str, params: dict[str, Any]) -> bool:
        """Send service invoke command via invoke2 API."""
        if not await self._ensure_token_valid():
            return False

        payload = self.build_base_payload(self.user_id, self.iot_id)
        payload["serviceName"] = service_name
        payload["paramJson"] = json.dumps(params)
        payload["sign"] = self.generate_sign(payload)

        return await self._send_request(API_INVOKE2, payload)

    async def _send_request(self, url: str, payload: dict[str, Any]) -> bool:
        """Send a POST request and handle response with auto-retry on 401."""
        async with httpx_client.get_async_client(self.hass) as client:
            try:
                resp = await client.post(
                    url,
                    json=payload,
                    headers=self._build_headers(),
                    timeout=10,
                )
                data = resp.json()

                if data.get("code") == "000":
                    return True

                if data.get("code") == "401":
                    _LOGGER.warning("Got 401, attempting token refresh and retry")
                    self._token_expired = True
                    if await self.async_refresh_token():
                        # 重新构建payload，保留命令特定字段
                        new_payload = self.build_base_payload(self.user_id, self.iot_id)
                        if "paramJson" in payload:
                            new_payload["paramJson"] = payload["paramJson"]
                        if "serviceName" in payload:
                            new_payload["serviceName"] = payload["serviceName"]
                        new_payload["sign"] = self.generate_sign(new_payload)
                        resp = await client.post(
                            url,
                            json=new_payload,
                            headers=self._build_headers(),
                            timeout=10,
                        )
                        data = resp.json()
                        return data.get("code") == "000"
                    return False

                _LOGGER.warning("API error: %s", data)
                return False
            except Exception as err:
                _LOGGER.error("API request error: %s", err)
                return False

    # ---- Polling management ----

    async def start_polling(self) -> None:
        """Start periodic state polling and scheduled token refresh."""
        _LOGGER.info("Starting polling (interval=%ds)", POLL_INTERVAL)

        # 立即执行一次初始更新
        await self.async_update()

        self._unsub_poll = async_track_time_interval(
            self.hass, self._poll_callback, timedelta(seconds=POLL_INTERVAL)
        )
        # 定时刷新 token（预防性，每 6 小时一次）
        refresh_hours = 6
        _LOGGER.info("Starting scheduled token refresh (interval=%dh)", refresh_hours)
        self._unsub_token_refresh = async_track_time_interval(
            self.hass, self._token_refresh_callback, timedelta(hours=refresh_hours)
        )

    def stop_polling(self) -> None:
        """Stop periodic polling and token refresh."""
        if self._unsub_poll is not None:
            self._unsub_poll()
            self._unsub_poll = None
        if self._unsub_token_refresh is not None:
            self._unsub_token_refresh()
            self._unsub_token_refresh = None

    async def _token_refresh_callback(self, now: Any) -> None:
        """Scheduled token refresh (every 6 hours)."""
        # 只在token即将过期时刷新
        if self._expire_at > 0 and time.time() < self._expire_at - 120:
            _LOGGER.debug(
                "Token still valid (expires in %ds), skipping scheduled refresh",
                int(self._expire_at - time.time())
            )
            return
        _LOGGER.info("Scheduled token refresh triggered")
        await self.async_refresh_token()

    async def _poll_callback(self, now: Any) -> None:
        """Periodic poll callback."""
        try:
            await self.async_update()
        except Exception as err:
            _LOGGER.exception("Poll callback error: %s", err)


def _snake(name: str) -> str:
    """Convert CamelCase to snake_case."""
    mapping = {
        "PowerSwitch": "power_on",
        "LightSwitch": "light_on",
        "DryingSwitch": "drying_on",
        "AirDryingSwitch": "air_drying_on",
        "DisinfectionSwitch": "disinfection_on",
        "IonsSwitch": "ions_on",
    }
    return mapping.get(name, "".join(
        f"_{c.lower()}" if c.isupper() else c for c in name
    ).lstrip("_"))