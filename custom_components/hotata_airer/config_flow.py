"""Config flow for Hotata Airer integration."""

from __future__ import annotations

import hashlib
import time
from typing import Any

import voluptuous as vol

from homeassistant.config_entries import ConfigFlow, ConfigFlowResult
from homeassistant.const import CONF_NAME
from homeassistant.core import HomeAssistant
from homeassistant.helpers import httpx_client

from .const import (
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
    IMEI,
    PHONE_MODEL,
    SYS_VERSION,
)
from .hub import HotataHub


async def _test_credentials(
    hass: HomeAssistant,
    access_token: str,
    refresh_token: str,
    user_id: str,
    iot_id: str,
) -> dict[str, Any] | None:
    """Test if credentials are valid by querying device properties."""
    async with httpx_client.get_async_client(hass) as client:
        # Build query payload using shared logic
        payload = HotataHub.build_base_payload(user_id, iot_id)
        payload["sign"] = HotataHub.generate_sign(payload)
        headers = {"content-type": "application/json"}
        if access_token:
            headers["authorization"] = access_token

        try:
            resp = await client.post(
                API_PROPERTY_GET,
                json=payload,
                headers=headers,
                timeout=10,
            )
            data = resp.json()

            if data.get("code") == "000":
                return data

            if data.get("code") == "401":
                # Try refreshing token
                refresh_payload = HotataHub.build_base_payload(user_id)
                refresh_payload["refreshToken"] = refresh_token
                refresh_payload["sign"] = HotataHub.generate_sign(refresh_payload)

                resp2 = await client.post(
                    API_REFRESH_TOKEN,
                    json=refresh_payload,
                    headers={"content-type": "application/json"},
                    timeout=10,
                )
                refresh_data = resp2.json()

                if refresh_data.get("code") == "000":
                    d = refresh_data.get("data", {})
                    token_type = d.get("tokenType", "bearer").strip()
                    new_token = f"{token_type} {d['accessToken']}"
                    new_refresh = d.get("refreshToken", refresh_token)
                    # Retry with new token
                    payload = HotataHub.build_base_payload(user_id, iot_id)
                    payload["sign"] = HotataHub.generate_sign(payload)
                    headers["authorization"] = new_token
                    resp3 = await client.post(
                        API_PROPERTY_GET,
                        json=payload,
                        headers=headers,
                        timeout=10,
                    )
                    data3 = resp3.json()
                    if data3.get("code") == "000":
                        return {
                            **data3,
                            "_new_access_token": new_token,
                            "_new_refresh_token": new_refresh,
                        }
                return None
            return None
        except Exception:
            return None


class HotataAirerConfigFlow(ConfigFlow, domain="hotata_airer"):
    """Handle a config flow for Hotata Airer."""

    VERSION = 1

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Handle the initial step."""
        if self._async_current_entries():
            return self.async_abort(reason="already_configured")

        errors: dict[str, str] = {}

        if user_input is not None:
            result = await _test_credentials(
                self.hass,
                user_input[CONF_ACCESS_TOKEN],
                user_input[CONF_REFRESH_TOKEN],
                user_input[CONF_USER_ID],
                user_input[CONF_IOT_ID],
            )
            if result is not None:
                # If token was refreshed during test, save the new one
                new_token = result.get("_new_access_token")
                new_refresh = result.get("_new_refresh_token")
                if new_token:
                    user_input[CONF_ACCESS_TOKEN] = new_token
                if new_refresh:
                    user_input[CONF_REFRESH_TOKEN] = new_refresh

                return self.async_create_entry(
                    title=user_input.get(CONF_NAME, DEFAULT_NAME),
                    data=user_input,
                )
            errors["base"] = "invalid_auth"

        schema = vol.Schema(
            {
                vol.Required(CONF_ACCESS_TOKEN): str,
                vol.Required(CONF_REFRESH_TOKEN): str,
                vol.Required(CONF_USER_ID): str,
                vol.Required(CONF_IOT_ID): str,
                vol.Optional(CONF_NAME, default=DEFAULT_NAME): str,
            }
        )

        return self.async_show_form(
            step_id="user",
            data_schema=schema,
            errors=errors,
        )

    async def async_step_reconfigure(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Handle reconfiguration of the integration."""
        reconfigure_entry = self._get_reconfigure_entry()

        errors: dict[str, str] = {}

        if user_input is not None:
            result = await _test_credentials(
                self.hass,
                user_input[CONF_ACCESS_TOKEN],
                user_input[CONF_REFRESH_TOKEN],
                user_input[CONF_USER_ID],
                user_input[CONF_IOT_ID],
            )
            if result is not None:
                new_token = result.get("_new_access_token")
                new_refresh = result.get("_new_refresh_token")
                if new_token:
                    user_input[CONF_ACCESS_TOKEN] = new_token
                if new_refresh:
                    user_input[CONF_REFRESH_TOKEN] = new_refresh

                return self.async_update_reload_and_abort(
                    reconfigure_entry,
                    data_updates=user_input,
                )
            errors["base"] = "invalid_auth"

        schema = vol.Schema(
            {
                vol.Required(
                    CONF_ACCESS_TOKEN,
                    default=reconfigure_entry.data.get(CONF_ACCESS_TOKEN, ""),
                ): str,
                vol.Required(
                    CONF_REFRESH_TOKEN,
                    default=reconfigure_entry.data.get(CONF_REFRESH_TOKEN, ""),
                ): str,
                vol.Required(
                    CONF_USER_ID,
                    default=reconfigure_entry.data.get(CONF_USER_ID, ""),
                ): str,
                vol.Required(
                    CONF_IOT_ID,
                    default=reconfigure_entry.data.get(CONF_IOT_ID, ""),
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
