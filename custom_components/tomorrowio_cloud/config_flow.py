from homeassistant import config_entries
import voluptuous as vol
from .const import DOMAIN, CONF_API_KEY, CONF_LATITUDE, CONF_LONGITUDE, CONF_CITY

class TomorrowioCloudConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    VERSION = 1

    async def async_step_user(self, user_input=None):
        """Handle a flow initiated by the user."""
        errors = {}
        
        if user_input is not None:
            return self.async_create_entry(
                title=f"Tomorrow.io Cloud Coverage - {user_input.get(CONF_CITY, 'Default')}",
                data=user_input
            )

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema({
                vol.Required(CONF_API_KEY): str,
                vol.Required(CONF_CITY): str,
                vol.Optional(CONF_LATITUDE): float,
                vol.Optional(CONF_LONGITUDE): float,
            }),
            errors=errors,
        )
