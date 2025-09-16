"""NotifyHq platform that has two fake switches."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from homeassistant.components.switch import SwitchEntity, SwitchEntityDescription
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_DEVICE_ID, STATE_ON
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers import device_registry as dr
from homeassistant.helpers.entity import DeviceInfo, EntityCategory
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.restore_state import RestoreEntity

from . import DOMAIN
from .const import DATA
from .device import NotifyHqDevice
from .entity import NotifyHqEntityDescription

CONF_INITIAL = "initial"


@dataclass(frozen=True, kw_only=True)
class NotifyHqSwitchEntityDescription(
    NotifyHqEntityDescription,
    SwitchEntityDescription,
):
    """Describes Battery Notes switch entity."""

    unique_id_suffix: str


@callback
def async_add_to_device(hass: HomeAssistant, entry: ConfigEntry) -> str | None:
    """Add our config entry to the device."""
    device_registry = dr.async_get(hass)

    device_id = entry.data.get(CONF_DEVICE_ID)

    if device_id:
        if device_registry.async_get(device_id):
            device_registry.async_update_device(
                device_id, add_config_entry_id=entry.entry_id
            )
            return device_id
    return None


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the demo switch platform."""
    device_id = config_entry.data.get(CONF_DEVICE_ID, None)

    device: NotifyHqDevice = hass.data[DOMAIN][DATA].devices[config_entry.entry_id]

    if not device.fake_device:
        device_id = async_add_to_device(hass, config_entry)

        if not device_id:
            return

    description = NotifyHqSwitchEntityDescription(
        unique_id_suffix="_allow_notifications_switch",
        key="allow_notifications",
        translation_key="allow_notifications",
        entity_category=EntityCategory.CONFIG,
        entity_registry_enabled_default=True,
    )

    async_add_entities(
        [
            NotifyHqSwitch(
                hass,
                description,
                f"{config_entry.entry_id}{description.unique_id_suffix}",
                device_id,
            )
        ]
    )


class NotifyHqSwitch(SwitchEntity, RestoreEntity):
    """Representation of a demo switch."""

    _attr_should_poll = False
    # _attr_is_on = False

    def __init__(
        self,
        hass: HomeAssistant,
        description: NotifyHqSwitchEntityDescription,
        unique_id: str,
        device_id: str,
    ) -> None:
        """Initialize the NotifyHq switch."""

        super().__init__()

        device_registry = dr.async_get(hass)

        self._attr_unique_id = unique_id
        self._device_id = device_id
        self.entity_description = description

        if device_id and (device := device_registry.async_get(device_id)):
            self.entity_id = f"switch.{device.name.lower()}_{description.key}"
            self._attr_device_info = DeviceInfo(
                connections=device.connections,
                identifiers=device.identifiers,
            )

    async def async_added_to_hass(self) -> None:
        """Call when entity about to be added to hass."""
        # Don't restore if we got an initial value.
        await super().async_added_to_hass()

        state = await self.async_get_last_state()
        self._attr_is_on = state is not None and state.state == STATE_ON

    @callback
    def _schedule_immediate_update(self):
        self.async_schedule_update_ha_state(True)

    async def async_turn_on(self, **kwargs: Any) -> None:
        """Turn the entity on."""
        self._attr_is_on = True
        self.async_write_ha_state()

    async def async_turn_off(self, **kwargs: Any) -> None:
        """Turn the entity off."""
        self._attr_is_on = False
        self.async_write_ha_state()
