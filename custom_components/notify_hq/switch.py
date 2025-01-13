"""NotifyHq platform that has two fake switches."""

from __future__ import annotations

from typing import Any

from homeassistant.components.switch import SwitchDeviceClass, SwitchEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from . import DOMAIN


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the demo switch platform."""
    async_add_entities(
        [NotifyHqSwitch("allow_notifications", "Decorative Lights", True, True)]
    )


class NotifyHqSwitch(SwitchEntity):
    """Representation of a demo switch."""

    _attr_has_entity_name = True
    _attr_name = None
    _attr_should_poll = False

    def __init__(
        self,
        unique_id: str,
        device_name: str,
        state: bool,
        assumed: bool,
        translation_key: str | None = None,
        device_class: SwitchDeviceClass | None = None,
    ) -> None:
        """Initialize the NotifyHq switch."""
        self._attr_assumed_state = assumed
        self._attr_device_class = device_class
        self._attr_translation_key = translation_key
        self._attr_is_on = state
        self._attr_unique_id = unique_id
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, unique_id)},
            name=device_name,
        )

    def turn_on(self, **kwargs: Any) -> None:
        """Turn the switch on."""
        self._attr_is_on = True
        self.schedule_update_ha_state()

    def turn_off(self, **kwargs: Any) -> None:
        """Turn the device off."""
        self._attr_is_on = False
        self.schedule_update_ha_state()


# """Switch platform for battery_notes."""

# from __future__ import annotations

# from dataclasses import dataclass
# from datetime import datetime
# import logging

# import voluptuous as vol

# from homeassistant.components.switch import (
#     PLATFORM_SCHEMA,
#     SwitchEntity,
#     SwitchEntityDescription,
# )
# from homeassistant.config_entries import ConfigEntry
# from homeassistant.const import CONF_DEVICE_ID, CONF_NAME
# from homeassistant.core import Event, HomeAssistant, callback, split_entity_id
# from homeassistant.helpers import (
#     config_validation as cv,
#     device_registry as dr,
#     entity_registry as er,
# )
# from homeassistant.helpers.entity import DeviceInfo, EntityCategory
# from homeassistant.helpers.entity_platform import AddEntitiesCallback
# from homeassistant.helpers.event import async_track_entity_registry_updated_event
# from homeassistant.helpers.reload import async_setup_reload_service

# from . import PLATFORMS
# from .const import (
#     ATTR_BATTERY_QUANTITY,
#     ATTR_BATTERY_TYPE,
#     ATTR_BATTERY_TYPE_AND_QUANTITY,
#     ATTR_DEVICE_ID,
#     ATTR_DEVICE_NAME,
#     ATTR_SOURCE_ENTITY_ID,
#     CONF_ENABLE_REPLACED,
#     CONF_SOURCE_ENTITY_ID,
#     DATA,
#     DOMAIN,
#     DOMAIN_CONFIG,
#     EVENT_BATTERY_REPLACED,
# )
# from .coordinator import NotifyHqCoordinator
# from .device import NotifyHqDevice
# from .entity import NotifyHqEntityDescription

# _LOGGER = logging.getLogger(__name__)


# @dataclass(frozen=True, kw_only=True)
# class NotifyHqSwitchEntityDescription(
#     NotifyHqEntityDescription,
#     SwitchEntityDescription,
# ):
#     """Describes Battery Notes switch entity."""

#     unique_id_suffix: str


# PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend(
#     {
#         vol.Optional(CONF_NAME): cv.string,
#         vol.Optional(CONF_DEVICE_ID): cv.string,
#         vol.Optional(CONF_SOURCE_ENTITY_ID): cv.string,
#     }
# )


# @callback
# def async_add_to_device(hass: HomeAssistant, entry: ConfigEntry) -> str | None:
#     """Add our config entry to the device."""
#     device_registry = dr.async_get(hass)

#     device_id = entry.data.get(CONF_DEVICE_ID)

#     if device_id:
#         if device_registry.async_get(device_id):
#             device_registry.async_update_device(
#                 device_id, add_config_entry_id=entry.entry_id
#             )
#             return device_id
#     return None


# async def async_setup_entry(
#     hass: HomeAssistant,
#     config_entry: ConfigEntry,
#     async_add_entities: AddEntitiesCallback,
# ) -> None:
#     """Initialize Battery Type config entry."""
#     entity_registry = er.async_get(hass)
#     device_registry = dr.async_get(hass)

#     device_id = config_entry.data.get(CONF_DEVICE_ID, None)

#     async def async_registry_updated(
#         event: Event[er.EventEntityRegistryUpdatedData],
#     ) -> None:
#         """Handle entity registry update."""
#         data = event.data
#         if data["action"] == "remove":
#             await hass.config_entries.async_remove(config_entry.entry_id)

#         if data["action"] != "update":
#             return

#         if "entity_id" in data["changes"]:
#             # Entity_id changed, reload the config entry
#             await hass.config_entries.async_reload(config_entry.entry_id)

#         if device_id and "device_id" in data["changes"]:
#             # If the tracked battery note is no longer in the device, remove our config entry
#             # from the device
#             if (
#                 not (entity_entry := entity_registry.async_get(data["entity_id"]))
#                 or not device_registry.async_get(device_id)
#                 or entity_entry.device_id == device_id
#             ):
#                 # No need to do any cleanup
#                 return

#             device_registry.async_update_device(
#                 device_id, remove_config_entry_id=config_entry.entry_id
#             )

#     coordinator = hass.data[DOMAIN][DATA].devices[config_entry.entry_id].coordinator

#     config_entry.async_on_unload(
#         async_track_entity_registry_updated_event(
#             hass, config_entry.entry_id, async_registry_updated
#         )
#     )

#     device: NotifyHqDevice = hass.data[DOMAIN][DATA].devices[config_entry.entry_id]

#     if not device.fake_device:
#         device_id = async_add_to_device(hass, config_entry)

#         if not device_id:
#             return

#     enable_replaced = True
#     # if DOMAIN_CONFIG in hass.data[DOMAIN]:
#     #     domain_config: dict = hass.data[DOMAIN][DOMAIN_CONFIG]
#     #     enable_replaced = domain_config.get(CONF_ENABLE_REPLACED, True)

#     description = NotifyHqSwitchEntityDescription(
#         unique_id_suffix="_allow_notifications_switch",
#         key="allow_notifications",
#         translation_key="allow_notifications",
#         entity_category=EntityCategory.DIAGNOSTIC,
#         entity_registry_enabled_default=enable_replaced,
#     )

#     async_add_entities(
#         [
#             NotifyHqSwitch(
#                 hass,
#                 coordinator,
#                 description,
#                 f"{config_entry.entry_id}{description.unique_id_suffix}",
#                 device_id,
#             )
#         ]
#     )


# async def async_setup_platform(
#     hass: HomeAssistant,
# ) -> None:
#     """Set up the battery note sensor."""

#     await async_setup_reload_service(hass, DOMAIN, PLATFORMS)


# class NotifyHqSwitch(SwitchEntity):
#     """Represents a battery replaced switch."""

#     _attr_should_poll = False

#     entity_description: NotifyHqSwitchEntityDescription

#     def __init__(
#         self,
#         hass: HomeAssistant,
#         coordinator: NotifyHqCoordinator,
#         description: NotifyHqSwitchEntityDescription,
#         unique_id: str,
#         device_id: str,
#     ) -> None:
#         """Create a battery replaced switch."""

#         super().__init__()

#         device_registry = dr.async_get(hass)

#         self.coordinator = coordinator

#         self._attr_has_entity_name = True

#         if coordinator.source_entity_id and not coordinator.device_id:
#             self._attr_translation_placeholders = {
#                 "device_name": coordinator.device_name + " "
#             }
#             self.entity_id = (
#                 f"switch.{coordinator.device_name.lower()}_{description.key}"
#             )
#         elif coordinator.source_entity_id and coordinator.device_id:
#             source_entity_domain, source_object_id = split_entity_id(
#                 coordinator.source_entity_id
#             )
#             self._attr_translation_placeholders = {
#                 "device_name": coordinator.source_entity_name + " "
#             }
#             self.entity_id = f"switch.{source_object_id}_{description.key}"
#         else:
#             self._attr_translation_placeholders = {"device_name": ""}
#             self.entity_id = f"switch.{coordinator.device_name}_{description.key}"

#         self.entity_description = description
#         self._attr_unique_id = unique_id
#         self._device_id = device_id
#         self._source_entity_id = coordinator.source_entity_id

#         if device_id and (device := device_registry.async_get(device_id)):
#             self._attr_device_info = DeviceInfo(
#                 connections=device.connections,
#                 identifiers=device.identifiers,
#             )

#     async def async_added_to_hass(self) -> None:
#         """Handle added to Hass."""
#         registry = er.async_get(self.hass)
#         if registry.async_get(self.entity_id) is not None:
#             registry.async_update_entity_options(
#                 self.entity_id,
#                 DOMAIN,
#                 {"entity_id": self._attr_unique_id},
#             )

#     @property
#     def is_on(self) -> bool:
#         """Return True if device is on."""
#         return self.device.is_on

#     async def async_turn_on(self, **kwargs):
#         """Turn Tuya switch on."""
#         self.device.is_on = True

#     async def async_turn_off(self, **kwargs):
#         """Turn Tuya switch off."""
#         self.device.is_on = False

#     # Default value is the "OFF" state
#     def entity_default_value(self):
#         """Return False as the default value for this entity type."""
#         return False
