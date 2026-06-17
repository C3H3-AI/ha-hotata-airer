"""Config flow for Hotata Airer Simple integration."""

from __future__ import annotations

import hashlib
import logging
import time
from typing import Any

import voluptuous as vol
from homeassistant.config_entries import ConfigFlow, ConfigFlowResult
from homeassistant.const import CONF_NAME
from homeassistant.core import HomeAssistant
from homeassistant.helpers import httpx_client

from .const import (
    API_DEVICE_LIST,
    API_PROPERTY_GET,
    API_REFRESH_TOKEN,
    APP_KEY,
    APP_SECRET,
    APP_VERSION,
    CONF_ACCESS_TOKEN,
    CONF_IOT_ID,
    CONF_REFRESH_TOKEN,
    CONF_USER_ID,
    DEFAULT_NAME,
    DOMAIN,
    IMEI,
    PHONE_MODEL,
    SYS_VERSION,
)

_LOGGER = logging.getLogger(__name__)


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


async def _init_from_refresh_token(
    hass: HomeAssistant,
    refresh_token: str,
) -> dict[str, Any] | None:
    """Initialize credentials from Refresh Token only."""
    async with httpx_client.get_async_client(hass) as client:
        # Step 1: Refresh token
        ts = int(time.time() * 1000)
        refresh_payload = {
            "refreshToken": refresh_token,
            "appKey": APP_KEY,
            "appVersion": APP_VERSION,
            "timestamp": ts,
            "traceId": f"ha_refresh_{ts}",
            "sysVersion": SYS_VERSION,
            "phoneModel": PHONE_MODEL,
            "imei": IMEI,
        }
        refresh_payload["sign"] = generate_sign(refresh_payload)

        headers = {
            "content-type": "application/json",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        }

        _LOGGER.debug("Refresh token request payload: %s", refresh_payload)

        try:
            resp = await client.post(
                API_REFRESH_TOKEN,
                json=refresh_payload,
                headers=headers,
                timeout=10,
            )
            _LOGGER.debug("Refresh token response status: %s", resp.status_code)
            _LOGGER.debug("Refresh token response text: %s", resp.text[:500])

            try:
                data = resp.json()
            except Exception as json_err:
                _LOGGER.error("Failed to parse JSON response: %s. Response: %s", json_err, resp.text[:500])
                return None

            _LOGGER.debug("Refresh token response: %s", data)

            if data.get("code") != "000":
                _LOGGER.error("Refresh token failed with code: %s", data.get("code"))
                return None

            d = data.get("data", {})
            user_id = d.get("userId") or d.get("userid")
            if not user_id:
                _LOGGER.error("No userId in refresh response: %s", d)
                return None

            token_type = d.get("tokenType", "bearer").strip()
            access_token = f"{token_type} {d.get('accessToken')}"
            new_refresh_token = d.get("refreshToken") or refresh_token

            _LOGGER.debug("Got user_id=%s, access_token=%s...", user_id, access_token[:20])

        except Exception as e:
            _LOGGER.exception("Refresh token request error: %s", e)
            return None

        # Step 2: Get device list
        ts = int(time.time() * 1000)
        list_payload = {
            "userid": user_id,
            "userId": user_id,
            "appKey": APP_KEY,
            "appVersion": APP_VERSION,
            "timestamp": ts,
            "traceId": f"ha_list_{ts}",
            "sysVersion": SYS_VERSION,
            "phoneModel": PHONE_MODEL,
            "imei": IMEI,
        }
        list_payload["sign"] = generate_sign(list_payload)

        try:
            resp = await client.post(
                API_DEVICE_LIST,
                json=list_payload,
                headers={
                    "content-type": "application/json",
                    "authorization": access_token,
                    "User-Agent": headers["User-Agent"],
                },
                timeout=10,
            )
            list_data = resp.json()
            _LOGGER.debug("Device list response: %s", list_data)

            if list_data.get("code") != "000":
                _LOGGER.error("Get device list failed: %s", list_data)
                return None

            devices = list_data.get("data", [])
            if not devices:
                _LOGGER.error("No devices found")
                return None

            # Return tokens + first device
            iot_id = devices[0].get("iotid") or devices[0].get("iotId")
            if not iot_id:
                _LOGGER.error("No iotId in first device: %s", devices[0])
                return None

        except Exception as e:
            _LOGGER.exception("Device list request error: %s", e)
            return None

        # Step 3: Verify
        ts = int(time.time() * 1000)
        prop_payload = {
            "userid": user_id,
            "userId": user_id,
            "iotId": iot_id,
            "appKey": APP_KEY,
            "appVersion": APP_VERSION,
            "timestamp": ts,
            "traceId": f"ha_prop_{ts}",
            "sysVersion": SYS_VERSION,
            "phoneModel": PHONE_MODEL,
            "imei": IMEI,
        }
        prop_payload["sign"] = generate_sign(prop_payload)

        try:
            resp = await client.post(
                API_PROPERTY_GET,
                json=prop_payload,
                headers={
                    "content-type": "application/json",
                    "authorization": access_token,
                    "User-Agent": headers["User-Agent"],
                },
                timeout=10,
            )
            prop_data = resp.json()
            _LOGGER.debug("Property get response: %s", prop_data)

            if prop_data.get("code") != "000":
                _LOGGER.error("Property get failed: %s", prop_data)
                return None

        except Exception as e:
            _LOGGER.exception("Property get error: %s", e)
            return None

        return {
            CONF_ACCESS_TOKEN: access_token,
            CONF_REFRESH_TOKEN: new_refresh_token,
            CONF_USER_ID: user_id,
            CONF_IOT_ID: iot_id,
        }


async def _get_device_list(
    hass: HomeAssistant,
    access_token: str,
    user_id: str,
) -> list[dict[str, Any]]:
    """Fetch device list from API."""
    ts = int(time.time() * 1000)
    payload = {
        "userid": user_id,
        "userId": user_id,
        "appKey": APP_KEY,
        "appVersion": APP_VERSION,
        "timestamp": ts,
        "traceId": f"ha_list_{ts}",
        "sysVersion": SYS_VERSION,
        "phoneModel": PHONE_MODEL,
        "imei": IMEI,
    }
    payload["sign"] = generate_sign(payload)

    async with httpx_client.get_async_client(hass) as client:
        try:
            resp = await client.post(
                API_DEVICE_LIST,
                json=payload,
                headers={
                    "content-type": "application/json",
                    "authorization": access_token,
                },
                timeout=10,
            )
            data = resp.json()
            return data.get("data", []) if data.get("code") == "000" else []
        except Exception as e:
            _LOGGER.error("Device list error: %s", e)
            return []


class HotataAirerSimpleConfigFlow(ConfigFlow, domain=DOMAIN):
    VERSION = 1

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        errors: dict[str, str] = {}

        if user_input is not None:
            credentials = await _init_from_refresh_token(
                self.hass,
                user_input[CONF_REFRESH_TOKEN],
            )

            if credentials is not None:
                # Store for potential multi-device flow
                self._auth_data = credentials

                # Get device list for uniqueness check
                devices = await _get_device_list(
                    self.hass,
                    credentials[CONF_ACCESS_TOKEN],
                    credentials[CONF_USER_ID],
                )

                # Find devices not yet configured
                existing_ids = {
                    e.data.get(CONF_IOT_ID)
                    for e in self._async_current_entries()
                }
                unconfigured = [
                    d for d in devices
                    if (d.get("iotid") or d.get("iotId")) not in existing_ids
                ]

                if len(unconfigured) > 1:
                    # Multiple devices available → let user pick
                    self._all_devices = devices
                    return await self.async_step_pick_device()

                # Single (or first) device → create entry directly
                target = unconfigured[0] if unconfigured else devices[0]
                iot_id = target.get("iotid") or target.get("iotId")
                device_name = (
                    target.get("deviceName")
                    or target.get("name")
                    or f"好太太晾衣机 ({iot_id[:8]})"
                )

                await self.async_set_unique_id(iot_id)
                self._abort_if_unique_id_configured()

                return self.async_create_entry(
                    title=device_name,
                    data={
                        **credentials,
                        CONF_IOT_ID: iot_id,
                        CONF_NAME: device_name,
                    },
                )

            errors["base"] = "invalid_auth"

        schema = vol.Schema(
            {
                vol.Required(CONF_REFRESH_TOKEN): str,
                vol.Optional(CONF_NAME, default=DEFAULT_NAME): str,
            }
        )

        return self.async_show_form(
            step_id="user",
            data_schema=schema,
            errors=errors,
            description_placeholders={
                "help": "在好太太智家小程序中抓包获取 refreshToken"
            },
        )

    async def async_step_pick_device(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Step to select which device to add."""
        existing_ids = {
            e.data.get(CONF_IOT_ID)
            for e in self._async_current_entries()
        }

        unconfigured = [
            d for d in self._all_devices
            if (d.get("iotid") or d.get("iotId")) not in existing_ids
        ]

        if not unconfigured:
            return self.async_abort(reason="all_devices_configured")

        if user_input is not None:
            iot_id = user_input["iot_id"]
            device = next(
                d for d in self._all_devices
                if (d.get("iotid") or d.get("iotId")) == iot_id
            )
            device_name = (
                device.get("deviceName")
                or device.get("name")
                or f"好太太晾衣机 ({iot_id[:8]})"
            )

            await self.async_set_unique_id(iot_id)
            self._abort_if_unique_id_configured()

            return self.async_create_entry(
                title=device_name,
                data={
                    **self._auth_data,
                    CONF_IOT_ID: iot_id,
                    CONF_NAME: device_name,
                },
            )

        options = {}
        for d in unconfigured:
            iot_id = d.get("iotid") or d.get("iotId") or ""
            dname = d.get("deviceName") or d.get("name") or f"设备({iot_id[:8]})"
            options[iot_id] = dname

        schema = vol.Schema({
            vol.Required("iot_id"): vol.In(options),
        })

        return self.async_show_form(
            step_id="pick_device",
            data_schema=schema,
            description_placeholders={
                "count": str(len(options)),
            },
        )
