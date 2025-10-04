"""Switch platform for Notify HQ with categories, zones, and alert level attributes."""
from __future__ import annotations

import logging
from typing import Any, Dict, Optional

from homeassistant.components.switch import SwitchEntity
from homeassistant.helpers.entity import EntityCategory
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.event import async_track_service_registered, async_track_service_removed
from homeassistant.config_entries import ConfigEntry

from .const import DOMAIN, DEFAULT_ALERT_LEVEL

_LOGGER = logging.getLogger(__name__)


async def async_setup_platform(hass: HomeAssistant, config, add_entities, discovery_info=None):
    """Set up Notify HQ switches (legacy platform entry — integration uses config entry)."""
    manager = NotificationSwitchManager(hass, add_entities)
    await manager.async_init()


class NotificationSwitchManager:
    """Manages Notify HQ switch entities and keeps them updated."""

    def __init__(self, hass: HomeAssistant, add_entities):
        self.hass = hass
        self.add_entities = add_entities
        # keys: service or service_category
        self.entities: Dict[str, NotifyHQSwitch] = {}
        self._state_listener = None
        self._service_registered_unsub = None
        self._service_removed_unsub = None

    async def async_init(self):
        # read categories & alert levels from config entry (if exists)
        categories = self._get_categories()
        alert_levels = self._get_alert_levels()

        # Create switches for all existing notify services
        for service in self.hass.services.services.get("notify", {}):
            self._add_service(service, categories, alert_levels)

        # Track new/remove notify services dynamically
        self._service_registered_unsub = async_track_service_registered(self.hass, self._service_registered)
        self._service_removed_unsub = async_track_service_removed(self.hass, self._service_removed)

        # Listen for device_tracker changes to update zone/alert attributes
        self._state_listener = self.hass.bus.async_listen("state_changed", self._state_changed)

    def _get_entry(self) -> Optional[ConfigEntry]:
        entries = list(self.hass.config_entries.async_entries(DOMAIN))
        return entries[0] if entries else None

    def _get_categories(self) -> list[str]:
        entry = self._get_entry()
        if not entry:
            return []
        cats = entry.options.get("categories", "")
        return [c.strip() for c in cats.split(",") if c.strip()]

    def _get_alert_levels(self) -> dict:
        entry = self._get_entry()
        if not entry:
            return {}
        return entry.options.get("alert_levels", {})

    @callback
    def _add_service(self, service: str, categories: list[str], alert_levels: dict):
        """Add switches for this notify service (global + per-category if categories present)."""
        # Global switch key is the service name
        if service in self.entities:
            return

        global_switch = NotifyHQSwitch(self.hass, service, category=None, alert_levels=alert_levels)
        self.entities[service] = global_switch
        self.add_entities([global_switch])

        # Create category switches only if categories defined
        for cat in categories:
            if not cat:
                continue
            key = f"{service}_{cat}"
            if key in self.entities:
                continue
            # get configured level for this category across zones (dict)
            cat_levels = alert_levels.get(cat, {}) if isinstance(alert_levels, dict) else {}
            # store per-category switch
            cat_switch = NotifyHQSwitch(self.hass, service, category=cat, alert_levels=cat_levels)
            self.entities[key] = cat_switch
            self.add_entities([cat_switch])

        _LOGGER.info("Notify HQ: created switches for notify.%s (global + %d categories)", service, len(categories))

    @callback
    def _remove_service(self, service: str):
        """Remove switches for a service."""
        # Remove global + category switches
        keys = [k for k in list(self.entities.keys()) if k == service or k.startswith(f"{service}_")]
        for key in keys:
            ent = self.entities.pop(key, None)
            if ent:
                try:
                    ent.async_remove()
                except Exception:
                    _LOGGER.exception("Error removing entity %s", key)
        _LOGGER.info("Notify HQ: removed switches for notify.%s", service)

    @callback
    def _service_registered(self, event):
        if event.data.get("domain") == "notify":
            categories = self._get_categories()
            alert_levels = self._get_alert_levels()
            self._add_service(event.data.get("service"), categories, alert_levels)

    @callback
    def _service_removed(self, event):
        if event.data.get("domain") == "notify":
            self._remove_service(event.data.get("service"))

    async def _state_changed(self, event) -> None:
        """
        Listen for device_tracker state changes to update current zone/alert_level on switches.
        We'll update switches for services whose device_tracker matched the changed entity, plus all switches to be safe.
        """
        entity_id = event.data.get("entity_id")
        if not entity_id:
            return

        # Only care about device_tracker state changes
        if not entity_id.startswith("device_tracker."):
            return

        # For best-effort, update all switches so their attributes recompute (cheap)
        for ent in list(self.entities.values()):
            try:
                ent.update_zone_and_level()
            except Exception:
                _LOGGER.exception("Error updating zone/level for %s", ent.entity_id)


class NotifyHQSwitch(SwitchEntity):
    """A per-device (and optional per-category) notification enable switch."""

    def __init__(self, hass: HomeAssistant, service: str, category: Optional[str], alert_levels: dict):
        """
        :param hass: HomeAssistant instance
        :param service: notify service short name (e.g., mobile_app_david)
        :param category: category string or None for global
        :param alert_levels: if category is provided, this is a dict mapping zone -> level.
                             For global switches, pass {}.
        """
        self.hass = hass
        self._service = service
        self._category = category
        self._alert_levels = alert_levels or {}
        self._current_zone: Optional[str] = None
        self._current_level: str = DEFAULT_ALERT_LEVEL

        # Unique id and name
        unique_suffix = f"{service}_{category}" if category else service
        self._attr_unique_id = f"{DOMAIN}_{unique_suffix}"
        pretty_name = service.replace("_", " ").title()
        if category:
            self._attr_name = f"Notify HQ: {pretty_name} [{category}]"
        else:
            self._attr_name = f"Notify HQ: {pretty_name}"

        self._is_on = True
        self._attr_entity_category = EntityCategory.CONFIG

        # Initialize zone/level from current state
        self.update_zone_and_level()

    @property
    def name(self):
        return self._attr_name

    @property
    def is_on(self) -> bool:
        return self._is_on

    @property
    def extra_state_attributes(self) -> Dict[str, Any]:
        """Expose device, category (if any), current zone and alert_level for the current zone."""
        attrs: Dict[str, Any] = {"device": self._service}
        if self._category:
            attrs["category"] = self._category
            attrs["alert_level"] = self._current_level or DEFAULT_ALERT_LEVEL
            if self._current_zone:
                attrs["current_zone"] = self._current_zone
        return attrs

    @property
    def device_info(self):
        # Optional: could be filled with device registry lookup if desired
        return None

    async def async_turn_on(self, **kwargs: Any) -> None:
        self._is_on = True
        self.async_write_ha_state()

    async def async_turn_off(self, **kwargs: Any) -> None:
        self._is_on = False
        self.async_write_ha_state()

    def update_zone_and_level(self) -> None:
        """
        Compute the current zone & alert level for this switch (best-effort).
        Uses device_tracker matching logic similar to the notify handler so attributes match runtime behavior.
        """
        # If global switch: no category-level alert (but still expose device attr)
        if not self._category:
            self._current_zone = None
            self._current_level = DEFAULT_ALERT_LEVEL
            # push new state attributes
            self.async_write_ha_state()
            return

        # Best-effort: find tracker for service
        zone = self._find_zone_for_service()
        self._current_zone = zone
        # choose level using exact zone key, or fallback to 'home', or global default
        level = None
        if zone and isinstance(self._alert_levels, dict):
            level = self._alert_levels.get(zone)
        if not level and isinstance(self._alert_levels, dict):
            level = self._alert_levels.get("home")
        if not level:
            level = DEFAULT_ALERT_LEVEL
        self._current_level = level
        self.async_write_ha_state()

    def _find_zone_for_service(self) -> Optional[str]:
        """Try to find the zone name for this service by matching device_tracker entities."""
        # Heuristics similar to __init__.py resolution:
        service = self._service
        # common candidates
        candidates = [f"device_tracker.{service}"]
        if service.startswith("mobile_app_"):
            candidates.append(f"device_tracker.{service[len('mobile_app_'):]}")
        if "_" in service:
            candidates.append(f"device_tracker.{service.split('_')[-1]}")

        # check direct candidates first
        for ent_id in candidates:
            st = self.hass.states.get(ent_id)
            if st:
                val = self._zone_from_tracker_state(st)
                if val:
                    return val

        # fallback: search trackers with matching substrings in entity_id or attrs
        for st in self.hass.states.async_all("device_tracker"):
            if service in st.entity_id:
                val = self._zone_from_tracker_state(st)
                if val:
                    return val
            for v in ("friendly_name", "name", "source"):
                if v in st.attributes and isinstance(st.attributes[v], str) and service in st.attributes[v]:
                    val = self._zone_from_tracker_state(st)
                    if val:
                        return val
        return None

    @staticmethod
    def _zone_from_tracker_state(st) -> Optional[str]:
        """Normalize tracker state to a zone key (try state -> location_name -> 'not_home')."""
        state_val = st.state
        # Many trackers set 'home', 'not_home', or a zone name; return state if not 'not_home'
        if state_val and state_val != "not_home":
            return state_val
        if "location_name" in st.attributes:
            return st.attributes.get("location_name")
        if "zone" in st.attributes:
            return st.attributes.get("zone")
        return None
