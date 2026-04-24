"""Cover platform for Hotata Airer."""

from __future__ import annotations

import logging
from typing import Any

from homeassistant.components.cover import (
    CoverDeviceClass,
    CoverEntity,
    CoverEntityFeature,
)
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
    """Set up the cover platform."""
    hub: HotataHub = hass.data["hotata_airer"][entry.entry_id]
    async_add_entities([HotataCover(hub)])


class HotataCover(CoverEntity):
    """Representation of the Hotata airer cover."""

    _attr_device_class = CoverDeviceClass.BLIND
    _attr_supported_features = (
        CoverEntityFeature.OPEN
        | CoverEntityFeature.CLOSE
        | CoverEntityFeature.STOP
    )
    _attr_has_entity_name = True
    _attr_assumed_state = True

    def __init__(self, hub: HotataHub) -> None:
        """Initialize the cover."""
        self._hub = hub
        self._attr_name = "晾衣机"
        self._attr_unique_id = f"{hub.iot_id}_cover"
        self._attr_device_info = hub.device_info
        self._position: int | None = None

    async def async_added_to_hass(self) -> None:
        """When entity is added to hass."""
        self._position = self._hub.state.position
        self.async_write_ha_state()
        self._hub.add_listener(self._handle_update)

    async def _handle_update(self) -> None:
        """Handle state update from hub."""
        new_pos = self._hub.state.position
        if new_pos != self._position:
            self._position = new_pos
            self.async_write_ha_state()

    @property
    def current_cover_position(self) -> int | None:
        """Return current position."""
        return self._position

    @property
    def is_closed(self) -> bool:
        """Return True if the cover is closed."""
        return self._position is not None and self._position == 0

    @property
    def available(self) -> bool:
        """Return if entity is available."""
        return not self._hub.token_expired

    async def async_open_cover(self, **kwargs: Any) -> None:
        """Open the cover."""
        if await self._hub.control_cover("up"):
            self._position = 100
            self.async_write_ha_state()

    async def async_close_cover(self, **kwargs: Any) -> None:
        """Close the cover."""
        if await self._hub.control_cover("down"):
            self._position = 0
            self.async_write_ha_state()

    async def async_stop_cover(self, **kwargs: Any) -> None:
        """Stop the cover."""
        await self._hub.control_cover("stop")
        self.async_write_ha_state()
