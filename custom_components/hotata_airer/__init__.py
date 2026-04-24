"""Hotata Airer - Custom Home Assistant Integration."""

import logging

_LOGGER = logging.getLogger(__name__)

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant

from .hub import HotataHub

DOMAIN = "hotata_airer"


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Hotata Airer from a config entry."""
    hub = HotataHub(hass, entry)

    hass.data.setdefault(DOMAIN, {})[entry.entry_id] = hub

    await hass.config_entries.async_forward_entry_setups(entry, [
        "binary_sensor",
        "cover",
        "light",
        "switch",
        "sensor",
    ])

    _LOGGER.info("Starting Hotata Airer polling")
    await hub.start_polling()

    entry.async_on_unload(entry.add_update_listener(async_reload_entry))

    return True


async def async_reload_entry(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Handle options update."""
    await hass.config_entries.async_reload(entry.entry_id)


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    hub: HotataHub = hass.data[DOMAIN].pop(entry.entry_id)
    hub.stop_polling()

    unload_ok = await hass.config_entries.async_unload_platforms(entry, [
        "binary_sensor",
        "cover",
        "light",
        "switch",
        "sensor",
    ])

    return unload_ok
