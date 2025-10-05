"""Select platform for Notify HQ per-zone alert levels."""

from homeassistant.components.select import SelectEntity
from homeassistant.helpers.device_registry import async_get as dr_async_get
from .const import DOMAIN, ALERT_LEVELS

DEFAULT_ZONE = "away"

class NotifyHQZoneSelect(SelectEntity):
    """Selector for alert level per zone for a mobile device."""

    def __init__(self, category: str, zone: str, device_id: tuple, mobile_name: str, initial: str = "active"):
        self._category = category
        self._zone = zone
        self._device_id = device_id
        self._mobile_name = mobile_name
        self._attr_name = f"{category} - {zone} Alert Level"
        self._attr_unique_id = f"{DOMAIN}_{device_id[1]}_{category}_{zone}_alert_level"
        self._attr_options = ALERT_LEVELS
        self._attr_current_option = initial

    @property
    def device_info(self):
        return {"identifiers": {self._device_id}, "name": self._mobile_name}

    async def async_select_option(self, option: str):
        if option in ALERT_LEVELS:
            self._attr_current_option = option
            self.async_write_ha_state()


async def async_setup_entry(hass, entry, async_add_entities):
    """Set up per-zone alert level selectors for all mobile devices for a category."""

    dev_reg = dr_async_get(hass)
    category_name = entry.title
    selectors = []

    zones = [zone.entity_id.replace("zone.", "") for zone in hass.states.async_all("zone")]
    zones.append(DEFAULT_ZONE)

    for device in dev_reg.devices.values():
        if not device.identifiers:
            continue
        mobile_ids = [i for i in device.identifiers if i[0] == "mobile_app"]
        for device_id in mobile_ids:
            mobile_name = device.name or "Unnamed Mobile"
            for zone in zones:
                selectors.append(
                    NotifyHQZoneSelect(category_name, zone, device_id, mobile_name)
                )

    async_add_entities(selectors, True)

    hass.data.setdefault(DOMAIN, {}).setdefault(entry.entry_id, {})["selects"] = selectors
