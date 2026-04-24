"""Switch platform for Hotata Airer - controls all device switches."""

from __future__ import annotations

import logging
from typing import Any

from homeassistant.components.switch import SwitchEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .hub import HotataHub

_LOGGER = logging.getLogger(__name__)

# Switch definitions: (property_name, translation_key, icon, default_state_key)
SWITCH_DEFS = [
    ("DisinfectionSwitch", "disinfection", "mdi:shield-check", "disinfection_on"),
    ("DryingSwitch", "drying", "mdi:heat-wave", "drying_on"),
    ("AirDryingSwitch", "air_drying", "mdi:air-filter", "air_drying_on"),
    ("IonsSwitch", "ions", "mdi:atom-variant", "ions_on"),
    ("PowerSwitch", "power", "mdi:power", "power_on"),
]


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the switch platform."""
    hub: HotataHub = hass.data["hotata_airer"][entry.entry_id]
    async_add_entities([
        HotataAirerSwitch(hub, prop_name, translation_key, icon, state_key)
        for prop_name, translation_key, icon, state_key in SWITCH_DEFS
    ])


class HotataAirerSwitch(SwitchEntity):
    """Representation of a Hotata airer switch."""

    _attr_has_entity_name = True
    _attr_assumed_state = True

    def __init__(
        self,
        hub: HotataHub,
        property_name: str,
        translation_key: str,
        icon: str,
        state_key: str,
    ) -> None:
        """Initialize the switch."""
        self._hub = hub
        self._property_name = property_name
        self._attr_translation_key = translation_key
        self._attr_icon = icon
        self._state_key = state_key

        self._attr_name = translation_key.replace("_", " ").title()
        self._attr_unique_id = f"{hub.iot_id}_{translation_key}"
        self._attr_device_info = hub.device_info
        self._is_on: bool = False

    async def async_added_to_hass(self) -> None:
        """When entity is added to hass."""
        self._is_on = getattr(self._hub.state, self._state_key, False) or False
        self.async_write_ha_state()  # Write initial state
        self._hub.add_listener(self._handle_update)

    async def _handle_update(self) -> None:
        """Handle state update from hub."""
        if self._hub._token_expired:
            self._attr_available = False
            self.async_write_ha_state()
            return
        self._attr_available = True
        new_state = getattr(self._hub.state, self._state_key, None)
        if new_state is not None and new_state != self._is_on:
            self._is_on = new_state
            self.async_write_ha_state()

    @property
    def is_on(self) -> bool:
        """Return True if switch is on."""
        return self._is_on

    async def async_turn_on(self, **kwargs: Any) -> None:
        """Turn on the switch."""
        if await self._hub.control_switch(self._property_name, True):
            self._is_on = True
            self.async_write_ha_state()

    async def async_turn_off(self, **kwargs: Any) -> None:
        """Turn off the switch."""
        if await self._hub.control_switch(self._property_name, False):
            self._is_on = False
            self.async_write_ha_state()
