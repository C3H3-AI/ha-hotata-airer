"""Binary sensor platform for Hotata Airer - device online status."""

from __future__ import annotations

import logging
from dataclasses import dataclass

from homeassistant.components.binary_sensor import (
    BinarySensorDeviceClass,
    BinarySensorEntity,
    BinarySensorEntityDescription,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .hub import HotataHub

_LOGGER = logging.getLogger(__name__)


@dataclass(frozen=True)
class HotataBinarySensorDescription(BinarySensorEntityDescription):
    """Description for a Hotata binary sensor."""
    pass


BINARY_SENSOR_DESCRIPTIONS: tuple[HotataBinarySensorDescription, ...] = (
    HotataBinarySensorDescription(
        key="online",
        name="Online Status",
        device_class=BinarySensorDeviceClass.CONNECTIVITY,
        icon="mdi:cloud-outline",
    ),
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the binary sensor platform."""
    hub: HotataHub = hass.data["hotata_airer"][entry.entry_id]
    entities = [HotataBinarySensor(hub, desc) for desc in BINARY_SENSOR_DESCRIPTIONS]
    async_add_entities(entities)


class HotataBinarySensor(BinarySensorEntity):
    """Representation of a Hotata binary sensor (online status)."""

    _attr_has_entity_name = True

    def __init__(
        self,
        hub: HotataHub,
        description: HotataBinarySensorDescription,
    ) -> None:
        """Initialize the binary sensor."""
        self._hub = hub
        self.entity_description = description
        self._attr_unique_id = f"{hub.iot_id}_{description.key}"
        self._attr_device_info = hub.device_info
        self._attr_is_on: bool | None = None

    async def async_added_to_hass(self) -> None:
        """When entity is added to hass."""
        self._attr_is_on = self._hub.state.online
        self.async_write_ha_state()
        self._hub.add_listener(self._handle_update)

    async def _handle_update(self) -> None:
        """Handle state update from hub."""
        if self._hub._token_expired:
            self._attr_available = False
            self.async_write_ha_state()
            return
        self._attr_available = True
        new_val = self._hub.state.online
        if new_val != self._attr_is_on:
            self._attr_is_on = new_val
            self.async_write_ha_state()

    @property
    def is_on(self) -> bool | None:
        """Return true if the device is online."""
        return self._attr_is_on
