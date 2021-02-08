import homeassistant.helpers.config_validation as cv
import voluptuous as vol
from homeassistant import config_entries
from typing import Optional, Dict, Any

from .const import *

DEVICE_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_STATION): cv.string,
    }
)


def validate_station_code(code: str) -> bool:
    return len(code) == 19


class MeteoclimaticConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    async def async_step_user(self, user_input: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        errors: Dict[str, str] = {}
        if user_input is not None:
            station_code = user_input[CONF_STATION]
            try:
                validate_station_code(station_code)
            except ValueError:
                errors["base"] = "code"
            if not errors:
                return self.async_create_entry(title=f"Meteoclimatic {station_code}", data={CONF_STATION: station_code})

        return self.async_show_form(step_id="user", data_schema=DEVICE_SCHEMA, errors=errors)
