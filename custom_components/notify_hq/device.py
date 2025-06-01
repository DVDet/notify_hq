"""Battery Notes device, contains device level details."""

import logging

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_DEVICE_ID
from homeassistant.core import CALLBACK_TYPE, HomeAssistant
from homeassistant.helpers.entity_registry import RegistryEntry

from .const import CONF_SOURCE_ENTITY_ID, DATA, DATA_STORE, DOMAIN, PLATFORMS
from .coordinator import NotifyHqCoordinator
from .store import NotifyHqStorage

_LOGGER = logging.getLogger(__name__)


class NotifyHqDevice:
    """Manages a Battery Note device."""

    config: ConfigEntry
    store: NotifyHqStorage
    coordinator: NotifyHqCoordinator
    wrapped_battery: RegistryEntry | None = None
    device_name: str | None = None

    def __init__(self, hass: HomeAssistant, config: ConfigEntry) -> None:
        """Initialize the device."""
        self.hass = hass
        self.config = config
        self.reset_jobs: list[CALLBACK_TYPE] = []

    @property
    def fake_device(self) -> bool:
        """Return if an actual device registry entry."""
        if self.config.data.get(CONF_SOURCE_ENTITY_ID, None):
            if self.config.data.get(CONF_DEVICE_ID, None) is None:
                return True
        return False

    @property
    def name(self) -> str:
        """Return the name of the device."""
        return self.device_name or self.config.title

    @property
    def unique_id(self) -> str | None:
        """Return the unique id of the device."""
        return self.config.unique_id

    @staticmethod
    async def async_update(hass: HomeAssistant, entry: ConfigEntry) -> None:
        """Update the device and related entities.

        Triggered when the device is renamed on the frontend.
        """
        await hass.config_entries.async_reload(entry.entry_id)

    async def async_setup(self) -> bool:
        """Set up the device and related entities."""
        config = self.config

        device_id = config.data.get(CONF_DEVICE_ID, None)
        source_entity_id = config.data.get(CONF_SOURCE_ENTITY_ID, None)

        self.store = self.hass.data[DOMAIN][DATA_STORE]
        self.coordinator = NotifyHqCoordinator(self.hass)

        self.coordinator.device_id = device_id
        self.coordinator.source_entity_id = source_entity_id
        self.coordinator.device_name = self.device_name

        self.hass.data[DOMAIN][DATA].devices[config.entry_id] = self
        self.reset_jobs.append(config.add_update_listener(self.async_update))

        # Forward entry setup to related domains.
        await self.hass.config_entries.async_forward_entry_setups(config, PLATFORMS)

        return True

    async def async_unload(self) -> bool:
        """Unload the device and related entities."""

        while self.reset_jobs:
            self.reset_jobs.pop()()

        return True
