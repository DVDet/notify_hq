from homeassistant.helpers.entity_registry import async_get as er_async_get
from homeassistant.helpers.device_registry import async_get as dr_async_get
from .const import DOMAIN

SERVICE_NOTIFY = "notify"

async def async_setup_notify_service(hass):
    async def handle_notify(call):
        category = call.data.get("category")
        message = call.data.get("message", "")
        title = call.data.get("title")

        if not category or not message:
            return

        dev_reg = dr_async_get(hass)
        ent_reg = er_async_get(hass)

        # Check if category global switch is on
        entity_id_safe = category.replace(" ", "_").lower()
        global_switch = hass.states.get(f"switch.{entity_id_safe}_enabled")

        if not global_switch or global_switch.state != "on":
            return

        # Iterate all switches
        for entity in hass.states.async_all("switch"):
            # Get entity registry entry
            ent_entry = ent_reg.async_get(entity.entity_id)
            if not ent_entry or not ent_entry.device_id:
                continue

            # Get device entry
            device = dev_reg.async_get(ent_entry.device_id)
            if not device:
                continue

            # Only mobile_app devices
            if not any(ident[0] == "mobile_app" for ident in device.identifiers):
                continue

            # Only per-category notification switches
            if entity.entity_id.endswith(f"{category}_notifications") and entity.state == "on":
                mobile_name = device.name.replace(" ", "_").lower()
                service_name = f"mobile_app_{mobile_name}"
                payload = {"message": message}
                if title:
                    payload["title"] = title

                await hass.services.async_call(
                    "notify",
                    service_name,
                    payload,
                )

    hass.services.async_register(DOMAIN, SERVICE_NOTIFY, handle_notify)
