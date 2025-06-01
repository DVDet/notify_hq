"""DataUpdateCoordinator for battery notes."""

from __future__ import annotations

import logging

from homeassistant.helpers import entity_registry as er
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator

from .const import ATTR_REMOVE, DOMAIN

_LOGGER = logging.getLogger(__name__)


class NotifyHqCoordinator(DataUpdateCoordinator):
    """Define an object to hold Battery Notes device."""

    device_id: str | None = None
    source_entity_id: str | None = None
    device_name: str
    _source_entity_name: str | None = None

    def __init__(self, hass):
        """Initialize."""

        super().__init__(hass, _LOGGER, name=DOMAIN)

    @property
    def source_entity_name(self):
        """Get the current name of the source_entity_id."""
        if not self._source_entity_name:
            self._source_entity_name = ""

            if self.source_entity_id:
                entity_registry = er.async_get(self.hass)
                registry_entry = entity_registry.async_get(self.source_entity_id)
                self._source_entity_name = (
                    registry_entry.name or registry_entry.original_name
                )

        return self._source_entity_name

    async def _async_update_data(self):
        """Update data."""
        self.async_set_updated_data(None)

        _LOGGER.debug("Update coordinator")

    def async_update_device_config(self, device_id: str, data: dict):
        """Conditional create, update or remove device from store."""

        if ATTR_REMOVE in data:
            self.store.async_delete_device(device_id)
        elif self.store.async_get_device(device_id):
            self.store.async_update_device(device_id, data)
        else:
            self.store.async_create_device(device_id, data)

    def async_update_entity_config(self, entity_id: str, data: dict):
        """Conditional create, update or remove entity from store."""

        if ATTR_REMOVE in data:
            self.store.async_delete_entity(entity_id)
        elif self.store.async_get_entity(entity_id):
            self.store.async_update_entity(entity_id, data)
        else:
            self.store.async_create_entity(entity_id, data)
