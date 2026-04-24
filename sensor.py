"""Sensor platform for Hotata Airer - all remaining time sensors."""

from __future__ import annotations

import logging

from homeassistant.components.sensor import SensorEntity
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
    """Set up the sensor platform."""
    hub: HotataHub = hass.data["hotata_airer"][entry.entry_id]
    async_add_entities([
        PositionSensor(hub),
        LightRemainingTimeSensor(hub),
        DisinfectionRemainingTimeSensor(hub),
        DryingRemainingTimeSensor(hub),
        AirDryingRemainingTimeSensor(hub),
        IonsRemainingTimeSensor(hub),
        MotorControlModeSensor(hub),
    ])


class PositionSensor(SensorEntity):
    """Position sensor (0=up, value increases as lowered)."""

    _attr_native_unit_of_measurement = "%"
    _attr_state_class = "measurement"
    _attr_has_entity_name = True

    def __init__(self, hub: HotataHub) -> None:
        """Initialize the sensor."""
        self._hub = hub
        self._attr_name = "位置"
        self._attr_unique_id = f"{hub.iot_id}_position"
        self._attr_device_info = hub.device_info

    async def async_added_to_hass(self) -> None:
        """When entity is added to hass."""
        self.async_write_ha_state()
        self._hub.add_listener(self._handle_update)

    async def _handle_update(self) -> None:
        """Handle state update."""
        self.async_write_ha_state()

    @property
    def native_value(self) -> int | None:
        """Return the position value."""
        return self._hub.state.position

    @property
    def available(self) -> bool:
        """Return if entity is available."""
        return not self._hub.token_expired


class LightRemainingTimeSensor(SensorEntity):
    """Light remaining time sensor."""

    _attr_native_unit_of_measurement = "min"
    _attr_state_class = "measurement"
    _attr_has_entity_name = True

    def __init__(self, hub: HotataHub) -> None:
        """Initialize the sensor."""
        self._hub = hub
        self._attr_name = "灯光定时"
        self._attr_unique_id = f"{hub.iot_id}_light_time"
        self._attr_device_info = hub.device_info

    async def async_added_to_hass(self) -> None:
        """When entity is added to hass."""
        self.async_write_ha_state()
        self._hub.add_listener(self._handle_update)

    async def _handle_update(self) -> None:
        """Handle state update."""
        self.async_write_ha_state()

    @property
    def native_value(self) -> int | None:
        """Return the remaining time value."""
        return self._hub.state.light_remaining_time

    @property
    def available(self) -> bool:
        """Return if entity is available."""
        return not self._hub.token_expired


class DisinfectionRemainingTimeSensor(SensorEntity):
    """Disinfection remaining time sensor."""

    _attr_native_unit_of_measurement = "min"
    _attr_state_class = "measurement"
    _attr_has_entity_name = True

    def __init__(self, hub: HotataHub) -> None:
        """Initialize the sensor."""
        self._hub = hub
        self._attr_name = "消毒定时"
        self._attr_unique_id = f"{hub.iot_id}_disinfection_time"
        self._attr_device_info = hub.device_info

    async def async_added_to_hass(self) -> None:
        """When entity is added to hass."""
        self.async_write_ha_state()
        self._hub.add_listener(self._handle_update)

    async def _handle_update(self) -> None:
        """Handle state update."""
        self.async_write_ha_state()

    @property
    def native_value(self) -> int | None:
        """Return the remaining time value."""
        return self._hub.state.disinfection_remaining_time

    @property
    def available(self) -> bool:
        """Return if entity is available."""
        return not self._hub.token_expired


class DryingRemainingTimeSensor(SensorEntity):
    """Drying remaining time sensor."""

    _attr_native_unit_of_measurement = "min"
    _attr_state_class = "measurement"
    _attr_has_entity_name = True

    def __init__(self, hub: HotataHub) -> None:
        """Initialize the sensor."""
        self._hub = hub
        self._attr_name = "烘干定时"
        self._attr_unique_id = f"{hub.iot_id}_drying_time"
        self._attr_device_info = hub.device_info

    async def async_added_to_hass(self) -> None:
        """When entity is added to hass."""
        self.async_write_ha_state()
        self._hub.add_listener(self._handle_update)

    async def _handle_update(self) -> None:
        """Handle state update."""
        self.async_write_ha_state()

    @property
    def native_value(self) -> int | None:
        """Return the remaining time value."""
        return self._hub.state.drying_remaining_time

    @property
    def available(self) -> bool:
        """Return if entity is available."""
        return not self._hub.token_expired


class AirDryingRemainingTimeSensor(SensorEntity):
    """Air drying remaining time sensor."""

    _attr_native_unit_of_measurement = "min"
    _attr_state_class = "measurement"
    _attr_has_entity_name = True

    def __init__(self, hub: HotataHub) -> None:
        """Initialize the sensor."""
        self._hub = hub
        self._attr_name = "风干定时"
        self._attr_unique_id = f"{hub.iot_id}_air_drying_time"
        self._attr_device_info = hub.device_info

    async def async_added_to_hass(self) -> None:
        """When entity is added to hass."""
        self.async_write_ha_state()
        self._hub.add_listener(self._handle_update)

    async def _handle_update(self) -> None:
        """Handle state update."""
        self.async_write_ha_state()

    @property
    def native_value(self) -> int | None:
        """Return the remaining time value."""
        return self._hub.state.air_drying_remaining_time

    @property
    def available(self) -> bool:
        """Return if entity is available."""
        return not self._hub.token_expired


class IonsRemainingTimeSensor(SensorEntity):
    """Ions (负离子) remaining time sensor."""

    _attr_native_unit_of_measurement = "min"
    _attr_state_class = "measurement"
    _attr_has_entity_name = True

    def __init__(self, hub: HotataHub) -> None:
        """Initialize the sensor."""
        self._hub = hub
        self._attr_name = "负离子定时"
        self._attr_unique_id = f"{hub.iot_id}_ions_time"
        self._attr_device_info = hub.device_info

    async def async_added_to_hass(self) -> None:
        """When entity is added to hass."""
        self.async_write_ha_state()
        self._hub.add_listener(self._handle_update)

    async def _handle_update(self) -> None:
        """Handle state update."""
        self.async_write_ha_state()

    @property
    def native_value(self) -> int | None:
        """Return the remaining time value."""
        return self._hub.state.ions_remaining_time

    @property
    def available(self) -> bool:
        """Return if entity is available."""
        return not self._hub.token_expired


class MotorControlModeSensor(SensorEntity):
    """Motor control mode sensor (0=stop, 1=up, 2=down)."""

    _attr_has_entity_name = True

    def __init__(self, hub: HotataHub) -> None:
        """Initialize the sensor."""
        self._hub = hub
        self._attr_name = "电机模式"
        self._attr_unique_id = f"{hub.iot_id}_motor_mode"
        self._attr_device_info = hub.device_info

    async def async_added_to_hass(self) -> None:
        """When entity is added to hass."""
        self.async_write_ha_state()
        self._hub.add_listener(self._handle_update)

    async def _handle_update(self) -> None:
        """Handle state update."""
        self.async_write_ha_state()

    @property
    def native_value(self) -> str | None:
        """Return the motor mode as string."""
        mode_map = {0: "停止", 1: "上升", 2: "下降"}
        mode = self._hub.state.motor_control_mode
        if mode is not None:
            return mode_map.get(mode, str(mode))
        return None

    @property
    def available(self) -> bool:
        """Return if entity is available."""
        return not self._hub.token_expired