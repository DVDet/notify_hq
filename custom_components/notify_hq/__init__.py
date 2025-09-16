"""The Detailed Hello World Push integration."""

from __future__ import annotations

from dataclasses import dataclass, field

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.typing import ConfigType

from .const import (
    CONF_ENABLE_AUTODISCOVERY,
    CONF_SHOW_ALL_DEVICES,
    DATA,
    DATA_STORE,
    DOMAIN,
    DOMAIN_CONFIG,
)
from .device import NotifyHqDevice
from .store import async_get_registry


@dataclass
class NotifyHqData:
    """Class for sharing data within the BatteryNotes integration."""

    devices: dict[str, NotifyHqDevice] = field(default_factory=dict)
    platforms: dict = field(default_factory=dict)


async def async_setup(hass: HomeAssistant, config: ConfigType) -> bool:
    """Integration setup."""

    domain_config: ConfigType = config.get(DOMAIN) or {
        CONF_ENABLE_AUTODISCOVERY: True,
        CONF_SHOW_ALL_DEVICES: False,
    }

    hass.data[DOMAIN] = {
        DOMAIN_CONFIG: domain_config,
    }

    store = await async_get_registry(hass)
    hass.data[DOMAIN][DATA_STORE] = store

    hass.data[DOMAIN][DATA] = NotifyHqData()

    return True


async def async_setup_entry(hass: HomeAssistant, config_entry: ConfigEntry) -> bool:
    """Set up a config entry."""

    device: NotifyHqDevice = NotifyHqDevice(hass, config_entry)

    if not await device.async_setup():
        return False

    return True
