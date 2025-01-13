"""The Detailed Hello World Push integration."""

from __future__ import annotations

from dataclasses import dataclass, field

import voluptuous as vol

from homeassistant.config_entries import ConfigEntry

# from homeassistant.const import Platform
from homeassistant.core import HomeAssistant
from homeassistant.helpers import config_validation as cv
from homeassistant.helpers.typing import ConfigType
from homeassistant.util import dt as dt_util

from . import hub
from .config_flow import CONFIG_VERSION
from .const import (
    ATTR_REMOVE,
    CONF_BATTERY_INCREASE_THRESHOLD,
    CONF_BATTERY_QUANTITY,
    CONF_BATTERY_TYPE,
    CONF_DEFAULT_BATTERY_LOW_THRESHOLD,
    CONF_ENABLE_AUTODISCOVERY,
    CONF_ENABLE_REPLACED,
    CONF_HIDE_BATTERY,
    CONF_LIBRARY_URL,
    CONF_ROUND_BATTERY,
    CONF_SHOW_ALL_DEVICES,
    CONF_USER_LIBRARY,
    DATA,
    DATA_LIBRARY_UPDATER,
    DATA_STORE,
    DEFAULT_BATTERY_INCREASE_THRESHOLD,
    DEFAULT_BATTERY_LOW_THRESHOLD,
    DEFAULT_LIBRARY_URL,
    DOMAIN,
    DOMAIN_CONFIG,
    MIN_HA_VERSION,
    PLATFORMS,
)
from .device import NotifyHqDevice

# from .discovery import DiscoveryManager
# from .library_updater import LibraryUpdater
from .store import async_get_registry

CONFIG_SCHEMA = vol.Schema(
    {
        DOMAIN: vol.All(
            vol.Schema(
                {
                    vol.Optional(CONF_ENABLE_AUTODISCOVERY, default=True): cv.boolean,
                    vol.Optional(CONF_USER_LIBRARY, default=""): cv.string,
                    vol.Optional(CONF_SHOW_ALL_DEVICES, default=False): cv.boolean,
                    vol.Optional(CONF_ENABLE_REPLACED, default=True): cv.boolean,
                    vol.Optional(CONF_HIDE_BATTERY, default=False): cv.boolean,
                    vol.Optional(CONF_ROUND_BATTERY, default=False): cv.boolean,
                    vol.Optional(
                        CONF_DEFAULT_BATTERY_LOW_THRESHOLD,
                        default=DEFAULT_BATTERY_LOW_THRESHOLD,
                    ): cv.positive_int,
                    vol.Optional(
                        CONF_BATTERY_INCREASE_THRESHOLD,
                        default=DEFAULT_BATTERY_INCREASE_THRESHOLD,
                    ): cv.positive_int,
                    vol.Optional(
                        CONF_LIBRARY_URL,
                        default=DEFAULT_LIBRARY_URL,
                    ): cv.string,
                },
            ),
        ),
    },
    extra=vol.ALLOW_EXTRA,
)


@dataclass
class NotifyHqData:
    """Class for sharing data within the BatteryNotes integration."""

    devices: dict[str, NotifyHqDevice] = field(default_factory=dict)
    platforms: dict = field(default_factory=dict)


# List of platforms to support. There should be a matching .py file for each,
# eg <cover.py> and <sensor.py>
# PLATFORMS = [Platform.SWITCH] #Platform.SENSOR, Platform.COVER]

type HubConfigEntry = ConfigEntry[hub.Hub]


async def async_setup(hass: HomeAssistant, config: ConfigType) -> bool:
    """Integration setup."""

    domain_config: ConfigType = config.get(DOMAIN) or {
        CONF_ENABLE_AUTODISCOVERY: True,
        CONF_SHOW_ALL_DEVICES: False,
        CONF_ENABLE_REPLACED: True,
        CONF_HIDE_BATTERY: False,
        CONF_ROUND_BATTERY: False,
        CONF_DEFAULT_BATTERY_LOW_THRESHOLD: DEFAULT_BATTERY_LOW_THRESHOLD,
        CONF_BATTERY_INCREASE_THRESHOLD: DEFAULT_BATTERY_INCREASE_THRESHOLD,
        CONF_LIBRARY_URL: DEFAULT_LIBRARY_URL,
    }

    hass.data[DOMAIN] = {
        DOMAIN_CONFIG: domain_config,
    }

    store = await async_get_registry(hass)
    hass.data[DOMAIN][DATA_STORE] = store

    hass.data[DOMAIN][DATA] = NotifyHqData()

    # library_updater = LibraryUpdater(hass)

    # await library_updater.get_library_updates(dt_util.utcnow())

    # hass.data[DOMAIN][DATA_LIBRARY_UPDATER] = library_updater

    # if domain_config.get(CONF_ENABLE_AUTODISCOVERY):
    #     discovery_manager = DiscoveryManager(hass, domain_config)
    #     await discovery_manager.start_discovery()
    # else:
    #     _LOGGER.debug("Auto discovery disabled")

    # Register custom services
    # setup_services(hass)

    return True


async def async_setup_entry(hass: HomeAssistant, config_entry: ConfigEntry) -> bool:
    """Set up a config entry."""

    device: NotifyHqDevice = NotifyHqDevice(hass, config_entry)

    if not await device.async_setup():
        return False

    return True


# async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
#     """Unload a config entry."""
#     # This is called when an entry/configured device is to be removed. The class
#     # needs to unload itself, and remove callbacks. See the classes for further
#     # details
#     unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)

#     return unload_ok
