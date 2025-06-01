"""Constants for the Detailed Hello World Push integration."""

import json
from logging import Logger, getLogger
from pathlib import Path
from typing import Final

import voluptuous as vol

from homeassistant.const import Platform
from homeassistant.helpers import config_validation as cv

LOGGER: Logger = getLogger(__package__)

MIN_HA_VERSION = "2024.12"

manifestfile = Path(__file__).parent / "manifest.json"
with open(file=manifestfile, encoding="UTF-8") as json_file:  # noqa: PTH123
    manifest_data = json.load(json_file)

DOMAIN = manifest_data.get("domain")
NAME = manifest_data.get("name")
VERSION = manifest_data.get("version")
ISSUEURL = manifest_data.get("issue_tracker")
MANUFACTURER = "@Andrew-CodeChimp"

DOMAIN_CONFIG = "config"

CONF_SOURCE_ENTITY_ID = "source_entity_id"
CONF_SENSORS = "sensors"
CONF_ENABLE_AUTODISCOVERY = "enable_autodiscovery"
CONF_USER_LIBRARY = "user_library"
CONF_MODEL = "model"
CONF_MODEL_ID = "model_id"
CONF_MANUFACTURER = "manufacturer"
CONF_DEVICE_NAME = "device_name"
CONF_LIBRARY_URL = "library_url"
CONF_SHOW_ALL_DEVICES = "show_all_devices"

DATA_CONFIGURED_ENTITIES = "configured_entities"
DATA_DISCOVERED_ENTITIES = "discovered_entities"
DATA_DOMAIN_ENTITIES = "domain_entities"
DATA_LIBRARY = "library"
DATA_LIBRARY_UPDATER = "library_updater"
DATA_LIBRARY_LAST_UPDATE = "library_last_update"
DATA_COORDINATOR = "coordinator"
DATA_STORE = "store"
DATA = "data"

ATTR_DEVICE_ID = "device_id"
ATTR_SOURCE_ENTITY_ID = "source_entity_id"
ATTR_REMOVE = "remove"
ATTR_DEVICE_NAME = "device_name"
CONF_PERSISTENT = "persistent"
CONF_NAME = "name"
ATTR_UNIQUE_ID = "unique_id"
COMPONENT_DOMAIN = "notifyhq"
CONF_CLASS = "class"
CONF_INITIAL_VALUE = "initial_value"

SERVICE_BATTERY_REPLACED_SCHEMA = vol.Schema(
    {
        vol.Optional(ATTR_DEVICE_ID): cv.string,
        vol.Optional(ATTR_SOURCE_ENTITY_ID): cv.string,
        vol.Optional(SERVICE_DATA_DATE_TIME_REPLACED): cv.datetime,
    }
)

SERVICE_CHECK_BATTERY_LAST_REPORTED_SCHEMA = vol.Schema(
    {
        vol.Required(SERVICE_DATA_DAYS_LAST_REPORTED): cv.positive_int,
    }
)

PLATFORMS: Final = [
    Platform.SWITCH,
]
