"""Entity for battery_notes."""

from __future__ import annotations

from dataclasses import dataclass
import logging

from homeassistant.const import ATTR_DEVICE_CLASS, ATTR_ENTITY_ID, STATE_CLOSED
from homeassistant.helpers.entity import EntityDescription
from homeassistant.helpers.restore_state import RestoreEntity
from homeassistant.util import slugify

from .const import *

_LOGGER = logging.getLogger(__name__)


@dataclass(frozen=True, kw_only=True)
class NotifyHqRequiredKeysMixin:
    """Mixin for required keys."""

    unique_id_suffix: str


@dataclass(frozen=True, kw_only=True)
class NotifyHqEntityDescription(EntityDescription, NotifyHqRequiredKeysMixin):
    """Generic Battery Notes entity description."""


class VirtualEntity(RestoreEntity):
    """A base class to add state restoring."""

    # Are we saving/restoring this entity
    _persistent: bool = True

    def __init__(self, config, domain, old_style: bool = False):
        """Initialize an Virtual Sensor."""
        _LOGGER.debug(f"creating-virtual-{domain}={config}")
        self._config = config
        self._persistent = config.get(CONF_PERSISTENT)

        # Build name, entity id and unique id. We do this because historically
        # the non-domain piece of the entity_id was prefixed with virtual_ so
        # we build the pieces manually to make sure.
        self._attr_name = config.get(CONF_NAME)

        self.entity_id = config.get(ATTR_ENTITY_ID)
        if self.entity_id == "NOTYET":
            if self._attr_name.startswith("+"):
                self._attr_name = self._attr_name[1:]
                self.entity_id = (
                    f"{domain}.{COMPONENT_DOMAIN}_{slugify(self._attr_name)}"
                )
            else:
                self.entity_id = f"{domain}.{slugify(self._attr_name)}"

        self._attr_unique_id = config.get(ATTR_UNIQUE_ID, None)
        if self._attr_unique_id == "NOTYET":
            self._attr_unique_id = slugify(self._attr_name)

        _LOGGER.info(f"VirtualEntity {self._attr_name} created")

    def _create_state(self, config):
        _LOGGER.info(f"VirtualEntity {self.unique_id}: creating initial state")
        self._attr_available = config.get(CONF_INITIAL_AVAILABILITY)

    def _restore_state(self, state, config):
        _LOGGER.info(f"VirtualEntity {self.unique_id}: restoring state")
        _LOGGER.debug(f"VirtualEntity:: state={pprint.pformat(state.state)}")
        _LOGGER.debug(f"VirtualEntity:: attr={pprint.pformat(state.attributes)}")
        self._attr_available = state.attributes.get(ATTR_AVAILABLE)

    def _update_attributes(self):
        self._attr_extra_state_attributes = {
            ATTR_PERSISTENT: self._persistent,
            ATTR_AVAILABLE: self._attr_available,
        }
        if _LOGGER.isEnabledFor(logging.DEBUG):
            self._attr_extra_state_attributes.update(
                {
                    ATTR_ENTITY_ID: self.entity_id,
                    ATTR_UNIQUE_ID: self.unique_id,
                }
            )

    async def async_added_to_hass(self) -> None:
        await super().async_added_to_hass()
        state = await self.async_get_last_state()
        if not self._persistent or not state:
            self._create_state(self._config)
        else:
            self._restore_state(state, self._config)
        self._update_attributes()

    async def async_will_remove_from_hass(self) -> None:
        """Call when entity is being removed from hass."""
        await super().async_will_remove_from_hass()

    def set_available(self, value):
        self._attr_available = value
        self._update_attributes()
        self.async_schedule_update_ha_state()
