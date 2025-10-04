"""Notify HQ integration."""
from __future__ import annotations

import logging
from typing import Any

from homeassistant.core import HomeAssistant, ServiceCall
from homeassistant.config_entries import ConfigEntry

from .const import DOMAIN, DEFAULT_ALERT_LEVEL

_LOGGER = logging.getLogger(__name__)


async def async_setup(hass: HomeAssistant, config: dict):
    """Legacy YAML setup (not used)."""
    return True


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry):
    """
    Set up Notify HQ for a config entry.
    Registers the notify_hq.notify service which:
     - iterates all notify.* services
     - checks global switch (switch.notify_hq_<service>)
     - if category provided, checks switch.notify_hq_<service>_<category>
     - determines zone for device and applies alert level (from options) per category/zone
    """

    async def _determine_zone_for_service(service: str) -> str | None:
        """
        Best-effort: find a device_tracker entity for the given notify service name.
        Attempt patterns and attribute matches; return zone entity_id (without 'zone.')
        or None.
        """
        # Try exact device_tracker prefix match
        candidates = []
        # candidate entity_ids: device_tracker.<service>
        candidates.append(f"device_tracker.{service}")
        # remove common prefix
        if service.startswith("mobile_app_"):
            candidates.append(f"device_tracker.{service[len('mobile_app_'):]}")
        # include possible raw suffixes
        if "_" in service:
            candidates.append(f"device_tracker.{service.split('_')[-1]}")
        # gather all trackers and then fuzzy-match attributes
        for ent_id in candidates:
            st = hass.states.get(ent_id)
            if st:
                # zone is usually in attribute 'source' or available via state -> entity is in zone; we find nearest zone by state
                return _zone_from_tracker_state(st)

        # fallback: search all device_tracker entities for ones that mention service name in attributes/entity_id
        for state in hass.states.async_all("device_tracker"):
            if service in state.entity_id:
                return _zone_from_tracker_state(state)
            # search in attributes (friendly_name, name, source, device_class)
            for v in ("friendly_name", "name", "source"):
                if v in state.attributes and isinstance(state.attributes[v], str) and service in state.attributes[v]:
                    return _zone_from_tracker_state(state)

        # not found
        return None

    def _zone_from_tracker_state(state):
        """Return a zone name like 'home' or 'office' based on tracker state's 'zone' attributes or state."""
        # Many trackers set state to 'home', 'not_home', or zone entity_id. We'll return state if that matches a zone
        st = state.state
        # If the state looks like an entity_id for zone (e.g. 'home') we return it directly
        # state could be 'home' or 'not_home' or zone entity_id like 'home' (Home Assistant often sets these as plain)
        if st and st.startswith("zone.") is False:
            # e.g., 'home' is common; we'll return 'home' as key
            return st
        # fallback to attributes for some trackers that set 'location_name' or 'zone'
        if "location_name" in state.attributes:
            return state.attributes.get("location_name")
        if "zone" in state.attributes:
            return state.attributes.get("zone")
        return None

    async def handle_notify(call: ServiceCall):
        """Send notification to all notify services that are enabled, applying category + zone alert levels."""
        message = call.data.get("message")
        title = call.data.get("title")
        category = call.data.get("category")

        if not message:
            _LOGGER.error("No message provided for notify_hq.notify")
            return

        notify_services = hass.services.services.get("notify", {})
        if not notify_services:
            _LOGGER.warning("No notify services available")
            return

        # options stored per-entry
        options = entry.options or {}
        categories_csv = options.get("categories", "")
        alert_levels = options.get("alert_levels", {})  # format: { category: { zone_name: level, ... }, ... }

        for service in notify_services:
            service_name = service  # e.g., mobile_app_david
            # Global check
            global_switch_id = f"switch.notify_hq_{service_name}"
            global_state = hass.states.get(global_switch_id)
            if global_state and global_state.state == "off":
                _LOGGER.debug("Global switch OFF for %s — skipping", service_name)
                continue

            # If category provided and category switch exists and is off -> skip
            if category:
                category_switch_id = f"switch.notify_hq_{service_name}_{category}"
                cat_state = hass.states.get(category_switch_id)
                if cat_state and cat_state.state == "off":
                    _LOGGER.debug("Category switch OFF for %s/%s — skipping", service_name, category)
                    continue

            # Determine zone for this service's device
            zone_name = await _determine_zone_for_service(service_name)
            # zone_name might be 'home', 'office', 'not_home', etc. We'll use exact matching against keys stored.
            # Determine chosen alert level:
            chosen_level = None
            if category and isinstance(alert_levels, dict):
                cat_map = alert_levels.get(category, {})
                # try zone-specific
                if zone_name and zone_name in cat_map:
                    chosen_level = cat_map.get(zone_name)
                # fallback to 'home' key or fallback default
                if not chosen_level and "home" in cat_map:
                    chosen_level = cat_map.get("home")
            if not chosen_level:
                chosen_level = DEFAULT_ALERT_LEVEL

            data: dict[str, Any] = {"message": message}
            if title:
                data["title"] = title

            # Attach interruption level in a way many mobile apps accept (iOS, Android companion)
            # Put in data["data"]["push"]["interruption-level"]
            data_payload = data.get("data", {})
            data_payload.setdefault("push", {})
            data_payload["push"]["interruption-level"] = chosen_level
            data["data"] = data_payload

            # Call the underlying notify service
            if hass.services.has_service("notify", service_name):
                try:
                    await hass.services.async_call("notify", service_name, data)
                    _LOGGER.info("Sent notify_hq -> notify.%s (level=%s, zone=%s, category=%s)", service_name, chosen_level, zone_name, category)
                except Exception:  # noqa: BLE001 - we want to catch and log
                    _LOGGER.exception("Failed to send notification via notify.%s", service_name)
            else:
                _LOGGER.warning("notify service notify.%s not found", service_name)

    hass.services.async_register(DOMAIN, "notify", handle_notify)

    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload Notify HQ: remove service registration (service name removed on reloads)."""
    hass.services.async_remove(DOMAIN, "notify")
    return True
