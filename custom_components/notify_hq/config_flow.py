"""Config flow for Hello World integration."""

from __future__ import annotations

import logging

import voluptuous as vol

from homeassistant import config_entries, exceptions
from homeassistant.config_entries import ConfigFlowResult
from homeassistant.const import CONF_DEVICE_ID, CONF_NAME, Integ_opt
from homeassistant.core import split_entity_id
from homeassistant.helpers import selector
import homeassistant.helpers.device_registry as dr
import homeassistant.helpers.entity_registry as er

from .const import CONF_SOURCE_ENTITY_ID, DOMAIN

_LOGGER = logging.getLogger(__name__)
CONFIG_VERSION = 1

DATA_SCHEMA = vol.Schema({("host"): str})
DEVICE_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_DEVICE_ID): selector.DeviceSelector(
            config=selector.DeviceFilterSelectorConfig(
                entity=[
                    selector.EntityFilterSelectorConfig(
                        integration=Integ_opt.MOBILE_APP,
                    ),
                ]
            )
        ),
    }
)

ENTITY_SCHEMA_ALL = vol.Schema(
    {
        vol.Required(CONF_SOURCE_ENTITY_ID): selector.EntitySelector(),
        vol.Optional(CONF_NAME): selector.TextSelector(
            selector.TextSelectorConfig(type=selector.TextSelectorType.TEXT),
        ),
    }
)

ENTITY_SCHEMA = vol.Schema(
    {
        # vol.Required(CONF_SOURCE_ENTITY_ID): selector.EntitySelector(
        #     selector.EntitySelectorConfig(
        #         domain=[Platform.SENSOR, Platform.BINARY_SENSOR],
        #         device_class=SensorDeviceClass.BATTERY,
        #     )
        # ),
        vol.Optional(CONF_NAME): selector.TextSelector(
            selector.TextSelectorConfig(type=selector.TextSelectorType.TEXT),
        ),
    }
)


class ConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Hello World."""

    VERSION = CONFIG_VERSION

    data: dict

    async def async_step_user(
        self,
        user_input: dict | None = None,
    ) -> ConfigFlowResult:
        # pylint: disable=unused-argument
        """Handle a flow initialized by the user."""

        return self.async_show_menu(step_id="user", menu_options=["device", "entity"])

    async def async_step_device(
        self,
        user_input: dict | None = None,
    ) -> ConfigFlowResult:
        """Handle a flow for a device or discovery."""
        errors = {}
        if user_input is not None:
            try:
                self.data = user_input

                source_entity_id = self.data.get(CONF_SOURCE_ENTITY_ID, None)
                device_id = self.data.get(CONF_DEVICE_ID, None)

                if source_entity_id:
                    entity_registry = er.async_get(self.hass)
                    entity_entry = entity_registry.async_get(source_entity_id)
                    source_entity_domain, source_object_id = split_entity_id(
                        source_entity_id
                    )
                    if entity_entry:
                        entity_unique_id = (
                            entity_entry.unique_id or entity_entry.entity_id
                        )
                    else:
                        entity_unique_id = source_object_id
                    unique_id = f"nhq_{entity_unique_id}"
                else:
                    device_registry = dr.async_get(self.hass)
                    device_entry = device_registry.async_get(device_id)
                    unique_id = f"nhq_{device_id}"
                    self.data.update({"device_name": device_entry.name})

                await self.async_set_unique_id(unique_id)
                self._abort_if_unique_id_configured()

                if CONF_NAME in self.data:
                    title = self.data.get(CONF_NAME)
                elif source_entity_id and entity_entry:
                    title = entity_entry.name or entity_entry.original_name
                else:
                    assert device_entry
                    title = device_entry.name_by_user or device_entry.name

                return self.async_create_entry(
                    title=str(title),
                    data=self.data,
                )
            except CannotConnect:
                errors["base"] = "cannot_connect"
            except InvalidHost:
                # The error string is set here, and should be translated.
                # This example does not currently cover translations, see the
                # comments on `DATA_SCHEMA` for further details.
                # Set the error on the `host` field, not the entire form.
                errors["host"] = "cannot_connect"
            except Exception:  # pylint: disable=broad-except
                _LOGGER.exception("Unexpected exception")
                errors["base"] = "unknown"

        # If there is no user input or there were errors, show the form again, including any errors that were found with the input.
        return self.async_show_form(
            step_id="device",
            data_schema=DEVICE_SCHEMA,
            errors=errors,
            last_step=False,
        )


class CannotConnect(exceptions.HomeAssistantError):
    """Error to indicate we cannot connect."""


class InvalidHost(exceptions.HomeAssistantError):
    """Error to indicate there is an invalid hostname."""
