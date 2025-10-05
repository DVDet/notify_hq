"""Select platform for Notify HQ."""
from homeassistant.components.select import SelectEntity
from homeassistant.helpers.device_registry import async_get as dr_async_get
from .const import DOMAIN, ALERT_LEVELS

class NotifyHQAlertLevelSelect(SelectEntity):
    """Select alert level per mobile device."""

    def __init__(self, category: str, device_id: tuple, mobile_name: str):
        self._category = category
        self._device_id = device_id
        self._mobile_name = mobile_name
        self._attr_name = f"{category} Alert Level"
        self._attr_unique_id = f"{DOMAIN}_{device_id[1]}_{category}_alert_level"
        self._attr_options = ALERT_LEVELS
        self._attr_current_option = "active"

    @property
    def device_info(self):
        return {"identifiers": {self._device_id}, "name": self._mobile_name}

    async def async_select_option(self, option: str):
        self._attr_current_option = option
        self.async_write_ha_state()


async def async_setup_entry(hass, entry, async_add_entities):
    """Set up select entities for mobile devices."""
    dev_reg = dr_async_get(hass)
    category_name = entry.title
    selects = []

    for dev in dev_reg.devices.values():
        if not dev.identifiers:
            continue
        mobile_ids = [i for i in dev.identifiers if i[0] == "mobile_app"]
        for device_id in mobile_ids:
            mobile_name = dev.name or "Unnamed Mobile"
            selects.append(NotifyHQAlertLevelSelect(category_name, device_id, mobile_name))

    async_add_entities(selects, True)
