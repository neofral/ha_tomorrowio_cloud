import requests
import logging
from homeassistant.helpers.entity import Entity
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

    # Create and add 24 individual sensors, one for each hour
    sensors = [
        TomorrowIoHourlyCloudCoverageSensor(api_key, latitude, longitude, hour)
        for hour in range(1, 25)  # Hour 1 to Hour 24
    ]
    add_entities(sensors, True)

    # Schedule an update for all sensors at 23:50
    async def update_sensors_at_2350(now):
        for sensor in sensors:
            sensor.update()
            sensor.async_write_ha_state()

    async def force_update(call):
        """Force update of all sensors."""
        _LOGGER.info("Manually updating Tomorrow.io cloud coverage sensors")
        for sensor in sensors:
            sensor.update()
            sensor.async_write_ha_state()

    # Register the scheduled update and force update service
    async_track_time_change(hass, update_sensors_at_2350, hour=23, minute=50)
    hass.services.register("tomorrowio_cloud", "force_update", force_update)

class TomorrowIoHourlyCloudCoverageSensor(Entity):
    """Representation of a Tomorrow.io Hourly Cloud Coverage Sensor."""

    def __init__(self, api_key, latitude, longitude, hour):
        """Initialize the sensor."""
        self.api_key = api_key
        self.latitude = latitude
        self.longitude = longitude
        self.hour = hour
        self._state = None

    @property
    def name(self):
        """Return the name of the sensor with the hour number."""
        return f"Cloud Coverage - Hour {self.hour:02d}"

    @property
    def state(self):
        """Provide the cloud coverage for this hour."""
        return self._state

    @property
    def unit_of_measurement(self):
        """Return the unit of measurement for cloud coverage."""
        return "%"

    def update(self):
        """Fetch cloud coverage for the specified hour from Tomorrow.io."""
        params = {
            "apikey": self.api_key,
            "location": f"{self.latitude},{self.longitude}",
            "fields": ["cloudCover"],
            "timesteps": "1h",
            "units": "metric"
        }
        try:
            response = requests.get(BASE_URL, params=params, timeout=10)
            data = response.json()

            # Fetch the cloud coverage value for the specified hour (self.hour - 1 for indexing)
            self._state = data["data"]["timelines"][0]["intervals"][self.hour - 1]["values"]["cloudCover"]

        except Exception as e:
            _LOGGER.error("Error fetching Tomorrow.io data for Hour %d: %s", self.hour, e)