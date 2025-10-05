"""Notify HQ integration."""

from homeassistant.core import HomeAssistant
from homeassistant.config_entries import ConfigEntry
from .const import DOMAIN
from .notify_service import async_setup_entry as notify_setup_entry, async_unload_entry as notify_unload_entry

PLATFORMS = ["switch", "select"]

async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Notify HQ from a config entry."""

    # Set up the notify service
    await notify_setup_entry(hass, entry)

    # Forward entry setup to platforms
    for platform in PLATFORMS:
        await hass.config_entries.async_forward_entry_setup(entry, platform)

    return True

async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""

    # Unload notify service
    await notify_unload_entry(hass, entry)

    # Unload platforms
    unload_ok = all(
        await hass.config_entries.async_forward_entry_unload(entry, platform)
        for platform in PLATFORMS
    )

    return unload_ok
