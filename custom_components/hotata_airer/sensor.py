"""Sensor platform for Hotata Airer - position and countdown timers."""

from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Any

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorEntityDescription,
    SensorStateClass,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import PERCENTAGE, UnitOfTime
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .hub import HotataHub

_LOGGER = logging.getLogger(__name__)


@dataclass(frozen=True)
class HotataSensorDescription(SensorEntityDescription):
    """Description for a Hotata sensor."""

    state_key: str = ""


SENSOR_DESCRIPTIONS: tuple[HotataSensorDescription, ...] = (
    HotataSensorDescription(
        key="position",
        name="Position",
        icon="mdi:arrow-up-down",
        native_unit_of_measurement=PERCENTAGE,
        state_class=SensorStateClass.MEASUREMENT,
        state_key="position",
    ),
    HotataSensorDescription(
        key="light_remaining",
        name="Light Remaining Time",
        icon="mdi:lightbulb-on",
        native_unit_of_measurement=UnitOfTime.MINUTES,
        device_class=SensorDeviceClass.DURATION,
        state_class=SensorStateClass.MEASUREMENT,
        state_key="light_remaining_time",
    ),
    HotataSensorDescription(
        key="disinfection_remaining",
        name="Disinfection Remaining Time",
        icon="mdi:shield-check",
        native_unit_of_measurement=UnitOfTime.MINUTES,
        device_class=SensorDeviceClass.DURATION,
        state_class=SensorStateClass.MEASUREMENT,
        state_key="disinfection_remaining_time",
    ),
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the sensor platform."""
    hub: HotataHub = hass.data["hotata_airer"][entry.entry_id]
    entities = [HotataSensor(hub, desc) for desc in SENSOR_DESCRIPTIONS]
    async_add_entities(entities)


class HotataSensor(SensorEntity):
    """Representation of a Hotata sensor."""

    _attr_has_entity_name = True

    def __init__(
        self,
        hub: HotataHub,
        description: HotataSensorDescription,
    ) -> None:
        """Initialize the sensor."""
        self._hub = hub
        self.entity_description = description
        self._attr_unique_id = f"{hub.iot_id}_{description.key}"
        self._attr_device_info = hub.device_info
        self._native_value: int | None = None

    async def async_added_to_hass(self) -> None:
        """When entity is added to hass."""
        state_key = self.entity_description.state_key
        self._native_value = getattr(self._hub.state, state_key, None)
        self.async_write_ha_state()  # Write initial state
        self._hub.add_listener(self._handle_update)

    async def _handle_update(self) -> None:
        """Handle state update from hub."""
        if self._hub._token_expired:
            self._attr_available = False
            self.async_write_ha_state()
            return
        self._attr_available = True
        state_key = self.entity_description.state_key
        new_val = getattr(self._hub.state, state_key, None)
        if new_val != self._native_value:
            self._native_value = new_val
            self.async_write_ha_state()

    @property
    def native_value(self) -> int | None:
        """Return the sensor value."""
        return self._native_value
