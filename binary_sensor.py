"""Binary sensor platform for Hotata Airer."""

from __future__ import annotations

import logging

from homeassistant.components.binary_sensor import BinarySensorDeviceClass
from homeassistant.components.binary_sensor import BinarySensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .hub import HotataHub

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the binary sensor platform."""
    hub: HotataHub = hass.data["hotata_airer"][entry.entry_id]
    async_add_entities([OnlineSensor(hub), PowerSensor(hub)])


class OnlineSensor(BinarySensorEntity):
    """Device online status sensor."""

    _attr_device_class = BinarySensorDeviceClass.CONNECTIVITY
    _attr_has_entity_name = True

    def __init__(self, hub: HotataHub) -> None:
        """Initialize the sensor."""
        self._hub = hub
        self._attr_name = "在线状态"
        self._attr_unique_id = f"{hub.iot_id}_online"
        self._attr_device_info = hub.device_info

    async def async_added_to_hass(self) -> None:
        """When entity is added to hass."""
        self.async_write_ha_state()
        self._hub.add_listener(self._handle_update)

    async def _handle_update(self) -> None:
        """Handle state update."""
        self.async_write_ha_state()

    @property
    def is_on(self) -> bool | None:
        """Return True if device is online."""
        return self._hub.state.online

    @property
    def available(self) -> bool:
        """Return if entity is available."""
        return not self._hub.token_expired


class PowerSensor(BinarySensorEntity):
    """Power switch status sensor."""

    _attr_device_class = BinarySensorDeviceClass.POWER
    _attr_has_entity_name = True

    def __init__(self, hub: HotataHub) -> None:
        """Initialize the sensor."""
        self._hub = hub
        self._attr_name = "电源开关"
        self._attr_unique_id = f"{hub.iot_id}_power"
        self._attr_device_info = hub.device_info

    async def async_added_to_hass(self) -> None:
        """When entity is added to hass."""
        self.async_write_ha_state()
        self._hub.add_listener(self._handle_update)

    async def _handle_update(self) -> None:
        """Handle state update."""
        self.async_write_ha_state()

    @property
    def is_on(self) -> bool | None:
        """Return True if power is on."""
        return self._hub.state.power_on

    @property
    def available(self) -> bool:
        """Return if entity is available."""
        return not self._hub.token_expired
