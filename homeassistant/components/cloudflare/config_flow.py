"""Config flow for Cloudflare integration."""
import logging
from typing import Any, Dict, Optional

from pycfdns import CloudflareUpdater
import voluptuous as vol

from homeassistant.config_entries import CONN_CLASS_CLOUD_PUSH, ConfigFlow
from homeassistant.const import CONF_API_KEY, CONF_EMAIL, CONF_ZONE
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.typing import ConfigType

from .const import CONF_RECORDS
from .const import DOMAIN  # pylint:disable=unused-import

_LOGGER = logging.getLogger(__name__)

DATA_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_EMAIL): str,
        vol.Required(CONF_API_KEY): str,
        vol.Required(CONF_ZONE): str,
    }
)


async def validate_input(hass: HomeAssistant, data: Dict):
    """Validate the user input allows us to connect.

    Data has the keys from DATA_SCHEMA with values provided by the user.
    """
    cfupdate = CloudflareUpdater(
        async_get_clientsession(),
        data[CONF_EMAIL],
        data[CONF_API_KEY],
        data[CONF_ZONE],
        data.get(CONF_RECORDS, []),
    )

    try:
        zone_id = await cfupdate.get_zone_id()
    except Exception as error:  # pylint: disable=broad-except
        raise InvalidZone from error

    return {"title": data[CONF_ZONE]}


class CloudflareConfigFlow(ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Cloudflare."""

    VERSION = 1
    CONNECTION_CLASS = CONN_CLASS_CLOUD_PUSH

    async def async_step_import(
        self, user_input: Optional[ConfigType] = None
    ) -> Dict[str, Any]:
        """Handle a flow initiated by configuration file."""
        return await self.async_step_user(user_input)

    async def async_step_user(self, user_input=None):
        """Handle a flow initiated by the user."""
        if self._async_current_entries():
            return self.async_abort(reason="single_instance_allowed")

        errors = {}

        if user_input is not None:
            try:
                info = await validate_input(self.hass, user_input)
            except InvalidZone:
                errors["base"] = "invalid_zone"
            except Exception:  # pylint: disable=broad-except
                _LOGGER.exception("Unexpected exception")
                errors["base"] = "unknown"
            else:
                await self.async_set_unique_id(user_input[CONF_ZONE])
                return self.async_create_entry(title=info["title"], data=user_input)

        return self.async_show_form(
            step_id="user", data_schema=DATA_SCHEMA, errors=errors
        )


class InvalidZone(HomeAssistantError):
    """Error to indicate we cant validate zone exists in account."""
