import requests
import logging
from datetime import datetime, timedelta
from homeassistant.helpers.entity import Entity
from homeassistant.util import dt as dt_util
from homeassistant.core import callback
from homeassistant.helpers.event import async_track_time_change

_LOGGER = logging.getLogger(__name__)

BASE_URL = "https://api.tomorrow.io/v4/timelines"

CONF_API_KEY = "api_key"
CONF_LATITUDE = "latitude"
CONF_LONGITUDE = "longitude"

def setup_platform(hass, config, add_entities, discovery_info=None):
    """Set up 24 Tomorrow.io cloud coverage sensors for the next 24 hours."""
    api_key = config[CONF_API_KEY]
    latitude = config.get(CONF_LATITUDE, hass.config.latitude)
    longitude = config.get(CONF_LONGITUDE, hass.config.longitude)

    # Create coordinator for centralized updates
    coordinator = TomorrowIoUpdateCoordinator(hass, api_key, latitude, longitude)

    # Create and add 24 individual sensors, one for each hour
    sensors = [
        TomorrowIoHourlyCloudCoverageSensor(coordinator, hour)
        for hour in range(1, 25)  # Hour 1 to Hour 24
    ]
    add_entities(sensors, True)

    # Schedule the daily update at 23:50
    async_track_time_change(hass, coordinator.async_update, hour=23, minute=50, second=0)

class TomorrowIoUpdateCoordinator:
    """Class to coordinate updates for all sensors."""

    def __init__(self, hass, api_key, latitude, longitude):
        """Initialize the coordinator."""
        self.hass = hass
        self.api_key = api_key
        self.latitude = latitude
        self.longitude = longitude
        self.data = {}
        self.sensors = []

    def register_sensor(self, sensor):
        """Register a sensor to receive updates."""
        self.sensors.append(sensor)

    @callback
    async def async_update(self, *_):
        """Fetch new state data for all sensors."""
        params = {
            "apikey": self.api_key,
            "location": f"{self.latitude},{self.longitude}",
            "fields": ["cloudCover"],
            "timesteps": "1h",
            "units": "metric"
        }
        try:
            response = await self.hass.async_add_executor_job(
                lambda: requests.get(BASE_URL, params=params, timeout=10)
            )
            data = response.json()
            self.data = data["data"]["timelines"][0]["intervals"]
            
            # Update all sensors
            for sensor in self.sensors:
                sensor.async_schedule_update_ha_state()

        except Exception as e:
            _LOGGER.error("Error fetching Tomorrow.io data: %s", e)

class TomorrowIoHourlyCloudCoverageSensor(Entity):
    """Representation of a Tomorrow.io Hourly Cloud Coverage Sensor."""

    def __init__(self, coordinator, hour):
        """Initialize the sensor."""
        self.coordinator = coordinator
        self.hour = hour
        self._state = None
        self.coordinator.register_sensor(self)

    @property
    def name(self):
        """Return the name of the sensor with the hour number."""
        return f"Cloud Coverage - Hour {self.hour}"

    @property
    def state(self):
        """Provide the cloud coverage for this hour."""
        return self._state

    @property
    def unit_of_measurement(self):
        """Return the unit of measurement for cloud coverage."""
        return "%"

    def update(self):
        """Update the sensor state."""
        if self.coordinator.data:
            try:
                self._state = self.coordinator.data[self.hour - 1]["values"]["cloudCover"]
            except (KeyError, IndexError):
                _LOGGER.error("Error updating sensor for Hour %d", self.hour)