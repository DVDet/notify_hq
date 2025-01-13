"""Config flow for Hello World integration."""

from __future__ import annotations

import logging
from typing import Any

import voluptuous as vol

from homeassistant import config_entries, exceptions
from homeassistant.components.sensor import SensorDeviceClass
from homeassistant.const import CONF_DEVICE_ID, CONF_NAME, Platform
from homeassistant.core import HomeAssistant, split_entity_id
from homeassistant.helpers import selector
import homeassistant.helpers.device_registry as dr
import homeassistant.helpers.entity_registry as er

from .const import (
    CONF_BATTERY_LOW_TEMPLATE,
    CONF_BATTERY_LOW_THRESHOLD,
    CONF_BATTERY_QUANTITY,
    CONF_BATTERY_TYPE,
    CONF_DEVICE_NAME,
    CONF_MANUFACTURER,
    CONF_MODEL,
    CONF_MODEL_ID,
    CONF_SHOW_ALL_DEVICES,
    CONF_SOURCE_ENTITY_ID,
    DATA_LIBRARY_UPDATER,
    DOMAIN,
    DOMAIN_CONFIG,
)
from .hub import Hub

_LOGGER = logging.getLogger(__name__)
CONFIG_VERSION = 1

# This is the schema that used to display the UI to the user. This simple
# schema has a single required host field, but it could include a number of fields
# such as username, password etc. See other components in the HA core code for
# further examples.
# Note the input displayed to the user will be translated. See the
# translations/<lang>.json file and strings.json. See here for further information:
# https://developers.home-assistant.io/docs/config_entries_config_flow_handler/#translations
# At the time of writing I found the translations created by the scaffold didn't
# quite work as documented and always gave me the "Lokalise key references" string
# (in square brackets), rather than the actual translated value. I did not attempt to
# figure this out or look further into it.
DATA_SCHEMA = vol.Schema({("host"): str})
DEVICE_SCHEMA_ALL = vol.Schema(
    {
        vol.Required(CONF_DEVICE_ID): selector.DeviceSelector(
            config=selector.DeviceFilterSelectorConfig()
        ),
        vol.Optional(CONF_NAME): selector.TextSelector(
            selector.TextSelectorConfig(type=selector.TextSelectorType.TEXT),
        ),
    }
)

DEVICE_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_DEVICE_ID): selector.DeviceSelector(
            config=selector.DeviceSelectorConfig(
                entity=[
                    selector.EntityFilterSelectorConfig(
                        domain=Platform.SENSOR,
                        device_class=SensorDeviceClass.BATTERY,
                    ),
                    selector.EntityFilterSelectorConfig(
                        domain=Platform.BINARY_SENSOR,
                        device_class=SensorDeviceClass.BATTERY,
                    ),
                ]
            )
        ),
        vol.Optional(CONF_NAME): selector.TextSelector(
            selector.TextSelectorConfig(type=selector.TextSelectorType.TEXT),
        ),
    }
)


async def validate_input(hass: HomeAssistant, data: dict) -> dict[str, Any]:
    """Validate the user input allows us to connect.

    Data has the keys from DATA_SCHEMA with values provided by the user.
    """
    # Validate the data can be used to set up a connection.

    # This is a simple example to show an error in the UI for a short hostname
    # The exceptions are defined at the end of this file, and are used in the
    # `async_step_user` method below.
    # if len(data["host"]) < 3:
    #     raise InvalidHost

    # hub = Hub(hass, data["host"])
    # # The dummy hub provides a `test_connection` method to ensure it's working
    # # as expected
    # result = await hub.test_connection()
    # if not result:
    #     # If there is an error, raise an exception to notify HA that there was a
    #     # problem. The UI will also show there was a problem
    #     raise CannotConnect

    # If your PyPI package is not built with async, pass your methods
    # to the executor:
    # await hass.async_add_executor_job(
    #     your_validate_func, data["username"], data["password"]
    # )

    # If you cannot connect:
    # throw CannotConnect
    # If the authentication is wrong:
    # InvalidAuth

    # Return info that you want to store in the config entry.
    # "Title" is what is displayed to the user for this hub device
    # It is stored internally in HA as part of the device config.
    # See `async_step_user` below for how this is used
    return {"title": data["host"]}


class ConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Hello World."""

    VERSION = CONFIG_VERSION

    async def async_step_user(self, user_input=None):
        """Handle the initial step."""
        # This goes through the steps to take the user through the setup process.
        # Using this it is possible to update the UI and prompt for additional
        # information. This example provides a single form (built from `DATA_SCHEMA`),
        # and when that has some validated input, it calls `async_create_entry` to
        # actually create the HA config entry. Note the "title" value is returned by
        # `validate_input` above.
        errors = {}
        if user_input is not None:
            try:
                # info = await validate_input(self.hass, user_input)
                # self.data[CONF_BATTERY_TYPE] = user_input[CONF_BATTERY_TYPE]
                # self.data[CONF_BATTERY_QUANTITY] = int(
                #     user_input[CONF_BATTERY_QUANTITY]
                # )
                # self.data[CONF_BATTERY_LOW_THRESHOLD] = int(
                #     user_input[CONF_BATTERY_LOW_THRESHOLD]
                # )
                # self.data[CONF_BATTERY_LOW_TEMPLATE] = user_input.get(
                #     CONF_BATTERY_LOW_TEMPLATE, None
                # )

                # source_entity_id = self.data.get(CONF_SOURCE_ENTITY_ID, None)
                # device_id = self.data.get(CONF_DEVICE_ID, None)

                # if source_entity_id:
                #     entity_registry = er.async_get(self.hass)
                #     entity_entry = entity_registry.async_get(source_entity_id)
                #     _, source_object_id = split_entity_id(source_entity_id)
                #     entity_unique_id = (
                #         entity_entry.unique_id
                #         or entity_entry.entity_id
                #         or source_object_id
                #     )
                #     unique_id = f"bn_{entity_unique_id}"
                # else:
                # device_registry = dr.async_get(self.hass)
                # device_entry = device_registry.async_get(device_id)
                # unique_id = f"bn_{device_id}"

                # await self.async_set_unique_id(unique_id)
                # self._abort_if_unique_id_configured()
                self.data = user_input
                if CONF_NAME in self.data:
                    title = self.data.get(CONF_NAME)
                # elif source_entity_id:
                #     title = entity_entry.name or entity_entry.original_name
                # else:
                #     title = device_entry.name_by_user or device_entry.name

                return self.async_create_entry(
                    title=title,
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
            step_id="user", data_schema=DEVICE_SCHEMA_ALL, errors=errors
        )


class CannotConnect(exceptions.HomeAssistantError):
    """Error to indicate we cannot connect."""


class InvalidHost(exceptions.HomeAssistantError):
    """Error to indicate there is an invalid hostname."""
