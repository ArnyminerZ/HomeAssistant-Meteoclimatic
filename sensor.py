import logging

import homeassistant.helpers.config_validation as cv
import voluptuous as vol
from dateutil import parser
from homeassistant import config_entries, core
from homeassistant.components.sensor import PLATFORM_SCHEMA
from homeassistant.const import (
    ATTR_NAME,
)
from homeassistant.helpers import ConfigType
from homeassistant.helpers.entity import Entity
from homeassistant.helpers.typing import HomeAssistantType, DiscoveryInfoType
from meteoclimatic import MeteoclimaticClient
from typing import Callable, Optional, Dict, Any

from .const import *

PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend(
    {
        vol.Required(CONF_STATION): cv.string,
    }
)

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
        hass: core.HomeAssistant,
        config_entry: config_entries.ConfigEntry,
        async_add_entities,
):
    """Set up the sensor platform."""
    config = hass.data[DOMAIN][config_entry.entry_id]
    if config_entry.options:
        config.update(config_entry.options)
    await async_setup_platform(hass, config, async_add_entities, None)


async def async_setup_platform(
        hass: HomeAssistantType,
        config: ConfigType,
        async_add_entities: Callable,
        discovery_info: Optional[DiscoveryInfoType] = None,
) -> None:
    """Set up the sensor platform."""
    sensors = [MeteoclimaticSensor(config[CONF_STATION])]
    async_add_entities(sensors, update_before_end=True)


class MeteoclimaticSensor(Entity):
    """Representation of a Meteoclimatic Station"""

    def __init__(self, station_code: str):
        super().__init__()
        self.client = MeteoclimaticClient()
        self.station_code = station_code
        self.observation = None

        self.attrs: Dict[str, Any] = {
            ATTR_NAME: station_code,
        }
        self._name = station_code
        self._available = False
        self._condition = None
        self._temperature = None
        self._temperature_unit = "ºC"
        self._pressure = None
        self._humidity = None
        self._wind_speed = None
        self._wind_bearing = None

    @property
    def name(self) -> str:
        return self._name

    @property
    def unique_id(self) -> str:
        return self.station_code

    @property
    def available(self) -> bool:
        return self._available

    @property
    def device_state_attributes(self) -> Dict[str, Any]:
        attrs = self.attrs
        if self.observation is not None:
            timestamp = parser.parse(self.observation.reception_time)
            station = self.observation.station

            attrs[ATTR_UPDATE_TIME] = timestamp
            attrs[ATTR_STATION_NAME] = station.name
            attrs[ATTR_STATION_CODE] = station.code
            attrs[ATTR_STATION_URL] = station.url
        return attrs

    @property
    def state(self):
        return self._condition

    @property
    def state(self):
        return self._condition

    @property
    def temperature(self):
        return self._temperature

    @property
    def temperature_unit(self):
        return self._temperature_unit

    @property
    def pressure(self):
        return self._pressure

    @property
    def humidity(self):
        return self._humidity

    @property
    def wind_speed(self):
        return self._wind_speed

    @property
    def wind_bearing(self):
        return self._wind_bearing

    async def async_update(self):
        self.observation = self.client.weather_at_station(self.station_code)

        timestamp = parser.parse(self.observation.reception_time)
        weather = self.observation.weather
        self._temperature = weather.temp_current
        self._humidity = weather.humidity_current
        self._pressure = weather.pressure_current
        self._wind_speed = weather.wind_current
        self._wind_bearing = weather.wind_bearing
        rain = weather.rain

        if rain > 0:
            if self._temperature < 5:
                self._condition = 'snowy'
            elif self._temperature < 0:
                self._condition = 'snowy-rainy'
            elif rain > 50:
                self._condition = 'pouring'
            else:
                self._condition = 'rainy'
        elif self._humidity > 60:
            if self._wind_speed > 30:
                self._condition = 'windy-variant'
            elif self._humidity > 80:
                self._condition = 'partlycloudy'
            elif self._humidity > 60:
                self._condition = 'cloudy'
        elif self._wind_speed > 30:
            self._condition = 'windy'
        elif 7 < timestamp.hour < 19:
            self._condition = 'clear-night'
        else:
            self._condition = 'sunny'
