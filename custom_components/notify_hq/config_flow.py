"""Config flow for Notify HQ."""

import voluptuous as vol
from homeassistant import config_entries
from .const import DOMAIN

class NotifyHQConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Notify HQ."""

    VERSION = 1

    async def async_step_user(self, user_input=None):
        """Step when the user adds a new category."""
        errors = {}

        if user_input is not None:
            category = user_input["category"].strip()
            # Check if this category is already configured
            for entry in self._async_current_entries():
                if entry.title.lower() == category.lower():
                    errors["category"] = "already_configured"
                    break

            if not errors:
                return self.async_create_entry(
                    title=category,
                    data={"category": category}
                )

        schema = vol.Schema({
            vol.Required("category", description="Enter notification category"): str
        })

        return self.async_show_form(
            step_id="user",
            data_schema=schema,
            errors=errors
        )
