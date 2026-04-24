"""Switch platform for Hotata Airer - controls all switches including Power."""

from __future__ import annotations

import logging
from typing import Any

from homeassistant.components.switch import SwitchEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .hub import HotataHub

_LOGGER = logging.getLogger(__name__)

SWITCH_PROPERTIES = {
    "电源": "PowerSwitch",
    "烘干": "DryingSwitch",
    "风干": "AirDryingSwitch",
    "消毒": "DisinfectionSwitch",
    "负离子": "IonsSwitch",
}


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the switch platform."""
    hub: HotataHub = hass.data["hotata_airer"][entry.entry_id]
    entities = [HotataSwitch(hub, key, prop) for key, prop in SWITCH_PROPERTIES.items()]
    async_add_entities(entities)


class HotataSwitch(SwitchEntity):
    """Representation of a Hotata airer switch."""

    _attr_assumed_state = True

    def __init__(self, hub: HotataHub, name: str, property_name: str) -> None:
        """Initialize the switch."""
        self._hub = hub
        self._name = name
        self._property_name = property_name
        self._attr_unique_id = f"{hub.iot_id}_switch_{property_name}"
        self._attr_device_info = hub.device_info

    @property
    def name(self) -> str:
        """Return the name of the switch."""
        return self._name

    async def async_added_to_hass(self) -> None:
        """When entity is added to hass."""
        self.async_write_ha_state()
        self._hub.add_listener(self._handle_update)

    async def _handle_update(self) -> None:
        """Handle state update from hub."""
        self.async_write_ha_state()

    @property
    def is_on(self) -> bool:
        """Return True if switch is on."""
        state_map = {
            "PowerSwitch": self._hub.state.power_on,
            "DryingSwitch": self._hub.state.drying_on,
            "AirDryingSwitch": self._hub.state.air_drying_on,
            "DisinfectionSwitch": self._hub.state.disinfection_on,
            "IonsSwitch": self._hub.state.ions_on,
        }
        val = state_map.get(self._property_name)
        return val or False

    @property
    def available(self) -> bool:
        """Return if entity is available."""
        return not self._hub.token_expired

    async def async_turn_on(self, **kwargs: Any) -> None:
        """Turn on the switch."""
        await self._hub.control_switch(self._property_name, True)
        self.async_write_ha_state()

    async def async_turn_off(self, **kwargs: Any) -> None:
        """Turn off the switch."""
        await self._hub.control_switch(self._property_name, False)
        self.async_write_ha_state()