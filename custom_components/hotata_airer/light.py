"""Light platform for Hotata Airer - controls lighting with brightness."""

from __future__ import annotations

import logging
from typing import Any

from homeassistant.components.light import (
    ATTR_BRIGHTNESS,
    ColorMode,
    LightEntity,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.util.color import brightness_to_value, value_to_brightness

from .hub import HotataHub

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the light platform."""
    hub: HotataHub = hass.data["hotata_airer"][entry.entry_id]
    async_add_entities([HotataLight(hub)])


class HotataLight(LightEntity):
    """Representation of the Hotata airer light."""

    _attr_color_mode = ColorMode.BRIGHTNESS
    _attr_supported_color_modes = {ColorMode.BRIGHTNESS}
    _attr_translation_key = "light"
    _attr_has_entity_name = True
    _attr_assumed_state = True

    def __init__(self, hub: HotataHub) -> None:
        """Initialize the light."""
        self._hub = hub
        self._attr_name = "Light"
        self._attr_unique_id = f"{hub.iot_id}_light"
        self._attr_device_info = hub.device_info
        self._is_on: bool = False
        self._brightness: int = 255  # HA scale (1-255)

    async def async_added_to_hass(self) -> None:
        """When entity is added to hass."""
        self._is_on = self._hub.state.light_on or False
        b = self._hub.state.light_brightness
        if b is not None:
            self._brightness = value_to_brightness(b, 1, 100)
        self.async_write_ha_state()  # Write initial state
        self._hub.add_listener(self._handle_update)

    async def _handle_update(self) -> None:
        """Handle state update from hub."""
        if self._hub._token_expired:
            self._attr_available = False
            self.async_write_ha_state()
            return
        self._attr_available = True
        changed = False

        new_on = self._hub.state.light_on
        if new_on is not None and new_on != self._is_on:
            self._is_on = new_on
            changed = True

        new_b = self._hub.state.light_brightness
        if new_b is not None:
            ha_b = value_to_brightness(new_b, 1, 100)
            if ha_b != self._brightness:
                self._brightness = ha_b
                changed = True

        if changed:
            self.async_write_ha_state()

    @property
    def is_on(self) -> bool:
        """Return True if light is on."""
        return self._is_on

    @property
    def brightness(self) -> int:
        """Return the brightness in HA scale (1-255)."""
        return self._brightness

    async def async_turn_on(self, **kwargs: Any) -> None:
        """Turn the light on, optionally with brightness."""
        # Send brightness first if specified
        if ATTR_BRIGHTNESS in kwargs:
            target = brightness_to_value(kwargs[ATTR_BRIGHTNESS], 1, 100)
            await self._hub.set_brightness(int(target))
            self._brightness = kwargs[ATTR_BRIGHTNESS]

        # Then turn on light if not already on
        if not self._is_on:
            await self._hub.control_switch("LightSwitch", True)
            self._is_on = True

        self.async_write_ha_state()

    async def async_turn_off(self, **kwargs: Any) -> None:
        """Turn the light off."""
        await self._hub.control_switch("LightSwitch", False)
        self._is_on = False
        self.async_write_ha_state()
