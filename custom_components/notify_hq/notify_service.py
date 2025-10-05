"""Notify HQ main notify service."""

from homeassistant.core import HomeAssistant, ServiceCall
from homeassistant.helpers.device_registry import async_get as dr_async_get
from homeassistant.helpers.entity_registry import async_get as er_async_get
from homeassistant.const import STATE_UNAVAILABLE
from .const import DOMAIN, ALERT_LEVELS, DEFAULT_ZONE

async def async_setup_entry(hass: HomeAssistant, entry):
    """Set up the notify_hq notify service for a category."""

    async def handle_notify(call: ServiceCall):
        """Handle sending notifications."""
        message = call.data.get("message")
        title = call.data.get("title")
        actions = call.data.get("actions")
        category = call.data.get("category")

        ent_reg = er_async_get(hass)
        dev_reg = dr_async_get(hass)

        # --- Check if the category is globally enabled ---
        global_unique_id = f"{DOMAIN}_{category.lower()}_enabled"
        global_entity_id = ent_reg.async_get_entity_id("switch", DOMAIN, global_unique_id)
        if not global_entity_id:
            return

        global_state = hass.states.get(global_entity_id)
        if not global_state or global_state.state != "on":
            return

        # --- Loop through all mobile_app devices ---
        for device in dev_reg.devices.values():
            if not device.identifiers:
                continue

            mobile_ids = [i for i in device.identifiers if i[0] == "mobile_app"]
            if not mobile_ids:
                continue

            device_id = mobile_ids[0][1]

            # --- Per-device switch (Allow Notifications) ---
            switch_unique_id = f"{DOMAIN}_{device_id}_{category.lower()}_notifications"
            switch_entity_id = ent_reg.async_get_entity_id("switch", DOMAIN, switch_unique_id)
            if not switch_entity_id:
                continue

            mobile_switch = hass.states.get(switch_entity_id)
            if not mobile_switch or mobile_switch.state != "on":
                continue

            # --- Determine current zone (default: away) ---
            tracker_id = f"device_tracker.{device.name.lower().replace(' ', '_')}"
            tracker = hass.states.get(tracker_id)
            zone_name = tracker.state.lower() if tracker and tracker.state not in [None, "not_home", "unavailable"] else "away"

            # --- Get alert level selector for this zone ---
            selector_unique_id = f"{DOMAIN}_{device_id}_{category.lower()}_{zone_name}_alert_level"
            selector_entity_id = ent_reg.async_get_entity_id("select", DOMAIN, selector_unique_id)
            if not selector_entity_id:
                continue

            alert_level_entity = hass.states.get(selector_entity_id)
            alert_level = (
                alert_level_entity.state
                if alert_level_entity and alert_level_entity.state in ALERT_LEVELS
                else "off"
            )

            if alert_level == "off":
                continue

            # --- Build payload ---
            payload = {
                "message": message,
                "data": {
                    "push": {"interruption-level": alert_level}
                },
            }
            if title:
                payload["title"] = title
            if actions:
                payload["data"]["actions"] = actions

            # --- Send notification ---
            device_notify_service = f"mobile_app_{device.name.lower().replace(' ', '_')}"
            await hass.services.async_call(
                "notify",
                device_notify_service,
                payload,
            )

    hass.services.async_register(DOMAIN, "notify", handle_notify)


async def async_unload_entry(hass: HomeAssistant, entry):
    """Unload notify service."""
    hass.services.async_remove(DOMAIN, "notify")
