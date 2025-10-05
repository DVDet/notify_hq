"""Config flow for Notify HQ."""
from __future__ import annotations
import voluptuous as vol
from homeassistant import config_entries
from .const import DOMAIN

class NotifyHQConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle Notify HQ config flow."""

    VERSION = 1

    async def async_step_user(self, user_input=None):
        errors = {}

        if user_input is not None:
            category_name = user_input["category_name"].strip()

            # Check if a config entry for this category already exists
            for entry in self._async_current_entries():
                if entry.title == category_name:
                    return self.async_abort(reason="category_exists")

            # Create a new entry (each category is its own entry)
            return self.async_create_entry(
                title=category_name,
                data={},
            )

        data_schema = vol.Schema({vol.Required("category_name"): str})
        return self.async_show_form(step_id="user", data_schema=data_schema, errors=errors)
