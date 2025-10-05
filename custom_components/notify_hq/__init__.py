"""Notify HQ integration."""
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.device_registry import async_get as dr_async_get

from .const import DOMAIN
from .notify_service import async_setup_notify_service

PLATFORMS = ["switch", "select"]

async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry):
    """Set up Notify HQ from a config entry (one entry per category)."""
    hass.data.setdefault(DOMAIN, {})

    category_name = entry.title  # Each entry title = category
    dev_reg = dr_async_get(hass)

    # Create the category device if it does not exist
    dev_reg.async_get_or_create(
        config_entry_id=entry.entry_id,
        identifiers={(DOMAIN, category_name)},
        manufacturer="Notify HQ",
        name=category_name,
        model="Notification Category",
    )

    # Forward platforms
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    # Register the notify service once
    if DOMAIN not in hass.data or not hass.data.get(f"{DOMAIN}_service_registered"):
        await async_setup_notify_service(hass)
        hass.data[f"{DOMAIN}_service_registered"] = True

    return True
