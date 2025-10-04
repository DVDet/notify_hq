"""Config flow for Notify HQ integration with categories and zone-aware alert levels."""
from __future__ import annotations

import logging
import voluptuous as vol
from typing import Dict, List

from homeassistant import config_entries
from homeassistant.core import callback
from homeassistant.helpers import entity_registry

from .const import DOMAIN, ALERT_LEVELS, DEFAULT_ALERT_LEVEL

_LOGGER = logging.getLogger(__name__)


def _get_zone_names(hass) -> List[str]:
    """
    Return a list of zone keys to use in the options UI.
    We'll return short names like 'home', 'office', or zone entity_id suffix without 'zone.'.
    """
    zone_names = []
    for state in hass.states.async_all("zone"):
        # state.entity_id is 'zone.home' or 'zone.office'
        eid = state.entity_id
        if eid and eid.startswith("zone."):
            zone_names.append(eid.split(".", 1)[1])
    # Ensure 'home' exists as a sensible default
    if "home" not in zone_names:
        zone_names.insert(0, "home")
    return zone_names


class NotifyHQConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle the config flow for Notify HQ."""

    VERSION = 3

    async def async_step_user(self, user_input=None):
        """Initial step for creating the integration (no configuration required)."""
        if user_input is not None:
            await self.async_set_unique_id(DOMAIN)
            self._abort_if_unique_id_configured()
            return self.async_create_entry(title="Notify HQ", data={})
        return self.async_show_form(step_id="user", data_schema=vol.Schema({}))

    @staticmethod
    @callback
    def async_get_options_flow(config_entry):
        return NotifyHQOptionsFlowHandler(config_entry)


class NotifyHQOptionsFlowHandler(config_entries.OptionsFlow):
    """Options flow for Notify HQ - configure categories and per-zone alert levels."""

    def __init__(self, config_entry: config_entries.ConfigEntry):
        self.config_entry = config_entry
        self._categories: List[str] = []
        self._alert_levels: Dict[str, Dict[str, str]] = config_entry.options.get("alert_levels", {})

    async def async_step_init(self, user_input=None):
        """Step 1: ask for a comma-separated list of categories."""
        if user_input is not None:
            cats = [c.strip() for c in user_input.get("categories", "").split(",") if c.strip()]
            self._categories = cats
            return await self.async_step_zone_levels()

        categories_csv = self.config_entry.options.get("categories", "")
        data_schema = vol.Schema({
            vol.Optional("categories", default=categories_csv): str
        })
        return self.async_show_form(step_id="init", data_schema=data_schema)

    async def async_step_zone_levels(self, user_input=None):
        """Step 2: present a dropdown for every category × zone to pick an alert level."""
        hass = self.hass
        zone_names = _get_zone_names(hass)

        if user_input is not None:
            # Build alert_levels structure
            alert_levels: Dict[str, Dict[str, str]] = {}
            for cat in self._categories:
                cat_key_map: Dict[str, str] = {}
                for zone in zone_names:
                    field_name = f"level__{cat}__{zone}"
                    # default to 'active' if not provided
                    selected = user_input.get(field_name, DEFAULT_ALERT_LEVEL)
                    cat_key_map[zone] = selected
                alert_levels[cat] = cat_key_map

            options = {
                "categories": ",".join(self._categories),
                "alert_levels": alert_levels,
            }

            # Persist options and trigger reload so switches update live
            await self.hass.config_entries.async_update_entry(self.config_entry, options=options)
            await self.hass.config_entries.async_reload(self.config_entry.entry_id)

            return self.async_create_entry(title="", data=options)

        # Build schema dynamically
        schema_dict = {}
        # If there are no categories, allow user to save empty
        if not self._categories:
            return self.async_show_form(step_id="zone_levels", data_schema=vol.Schema({}))

        for cat in self._categories:
            # existing levels for this category
            existing = self._alert_levels.get(cat, {})
            for zone in zone_names:
                default = existing.get(zone, DEFAULT_ALERT_LEVEL)
                schema_dict[vol.Optional(f"level__{cat}__{zone}", default=default)] = vol.In(ALERT_LEVELS)

        return self.async_show_form(step_id="zone_levels", data_schema=vol.Schema(schema_dict))
