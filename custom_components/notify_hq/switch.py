"""Switch platform for Notify HQ."""

from homeassistant.components.switch import SwitchEntity
from homeassistant.helpers.restore_state import RestoreEntity
from homeassistant.helpers.device_registry import async_get as dr_async_get
from .const import DOMAIN

class NotifyHQEnabledSwitch(SwitchEntity, RestoreEntity):
    """Global Enabled switch for a category."""

    def __init__(self, category: str):
        self._category = category
        self._attr_name = f"{category} Enabled"
        self._attr_unique_id = f"{DOMAIN}_{category}_enabled"
        self._attr_is_on = True

    @property
    def device_info(self):
        return {"identifiers": {(DOMAIN, self._category)}, "name": self._category}

    async def async_added_to_hass(self):
        if (old_state := await self.async_get_last_state()) is not None:
            self._attr_is_on = old_state.state == "on"

    async def async_turn_on(self, **kwargs):
        self._attr_is_on = True
        self.async_write_ha_state()

    async def async_turn_off(self, **kwargs):
        self._attr_is_on = False
        self.async_write_ha_state()


class NotifyHQMobileSwitch(SwitchEntity, RestoreEntity):
    """Switch to allow notifications for a category on a mobile device."""

    def __init__(self, category: str, device_id: tuple, mobile_name: str):
        self._category = category
        self._device_id = device_id
        self._mobile_name = mobile_name
        self._attr_name = f"{category} Allow Notifications"
        self._attr_unique_id = f"{DOMAIN}_{device_id[1]}_{category}_notifications"
        self._attr_is_on = False

    @property
    def device_info(self):
        return {"identifiers": {self._device_id}, "name": self._mobile_name}

    async def async_added_to_hass(self):
        if (old_state := await self.async_get_last_state()) is not None:
            self._attr_is_on = old_state.state == "on"

    async def async_turn_on(self, **kwargs):
        self._attr_is_on = True
        self.async_write_ha_state()

    async def async_turn_off(self, **kwargs):
        self._attr_is_on = False
        self.async_write_ha_state()


async def async_setup_entry(hass, entry, async_add_entities):
    """Set up switches for a category and its mobile devices."""

    dev_reg = dr_async_get(hass)
    category_name = entry.title
    switches = [NotifyHQEnabledSwitch(category_name)]

    for device in dev_reg.devices.values():
        if not device.identifiers:
            continue
        mobile_ids = [i for i in device.identifiers if i[0] == "mobile_app"]
        for device_id in mobile_ids:
            mobile_name = device.name or "Unnamed Mobile"
            switches.append(NotifyHQMobileSwitch(category_name, device_id, mobile_name))

    async_add_entities(switches, True)

    hass.data.setdefault(DOMAIN, {}).setdefault(entry.entry_id, {})["switches"] = switches
