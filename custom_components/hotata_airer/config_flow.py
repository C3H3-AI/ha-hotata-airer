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
        # 注意：不添加 userid/userId 空字段，完全模仿 cURL

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
            data = resp.json()
            _LOGGER.debug("Refresh token response: %s", data)

            if data.get("code") != "000":
                _LOGGER.error("Refresh token failed with code: %s", data.get("code"))
                return None

            d = data.get("data", {})
            # 尝试获取 userId，可能字段名为 "userId" 或 "userid"
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

        # Step 2: Get device list to find iotId
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


class HotataAirerSimpleConfigFlow(ConfigFlow, domain=DOMAIN):
    VERSION = 1

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        if self._async_current_entries():
            return self.async_abort(reason="already_configured")

        errors: dict[str, str] = {}

        if user_input is not None:
            credentials = await _init_from_refresh_token(
                self.hass,
                user_input[CONF_REFRESH_TOKEN],
            )

            if credentials is not None:
                return self.async_create_entry(
                    title=user_input.get(CONF_NAME, DEFAULT_NAME),
                    data={
                        **credentials,
                        CONF_NAME: user_input.get(CONF_NAME, DEFAULT_NAME),
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

    async def async_step_reconfigure(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        reconfigure_entry = self._get_reconfigure_entry()
        errors: dict[str, str] = {}

        if user_input is not None:
            credentials = await _init_from_refresh_token(
                self.hass,
                user_input[CONF_REFRESH_TOKEN],
            )

            if credentials is not None:
                return self.async_update_reload_and_abort(
                    reconfigure_entry,
                    data_updates={
                        **credentials,
                        CONF_NAME: user_input.get(CONF_NAME, reconfigure_entry.data.get(CONF_NAME, DEFAULT_NAME)),
                    },
                )
            errors["base"] = "invalid_auth"

        schema = vol.Schema(
            {
                vol.Required(
                    CONF_REFRESH_TOKEN,
                    default=reconfigure_entry.data.get(CONF_REFRESH_TOKEN, ""),
                ): str,
                vol.Optional(
                    CONF_NAME,
                    default=reconfigure_entry.data.get(CONF_NAME, DEFAULT_NAME),
                ): str,
            }
        )

        return self.async_show_form(
            step_id="reconfigure",
            data_schema=schema,
            errors=errors,
        )
