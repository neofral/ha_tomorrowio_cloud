import requests
import logging
from homeassistant.helpers.entity import Entity
from homeassistant.helpers.event import async_track_time_change
from geopy.geocoders import Nominatim
from geopy.exc import GeocoderTimedOut
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from .const import CONF_API_KEY, CONF_LATITUDE, CONF_LONGITUDE

_LOGGER = logging.getLogger(__name__)

BASE_URL = "https://api.tomorrow.io/v4/timelines"

async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the Tomorrow.io sensors from config entry."""
    config = config_entry.data
    api_key = config[CONF_API_KEY]
    latitude = config.get(CONF_LATITUDE, hass.config.latitude)
    longitude = config.get(CONF_LONGITUDE, hass.config.longitude)

    sensors = [
        TomorrowIoHourlyCloudCoverageSensor(api_key, latitude, longitude, hour)
        for hour in range(1, 25)
    ]
    async_add_entities(sensors, True)

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
        
        # Try to get city name synchronously during initialization
        try:
            geolocator = Nominatim(user_agent="home-assistant-tomorrowio")
            location = geolocator.reverse(f"{self.latitude}, {self.longitude}", timeout=10)
            if location and location.raw.get('address'):
                address = location.raw['address']
                self._city = (address.get('city') or 
                            address.get('town') or 
                            address.get('village') or 
                            address.get('suburb') or 
                            address.get('municipality'))
                if not self._city:
                    self._city = f"{self.latitude}_{self.longitude}"
            else:
                self._city = f"{self.latitude}_{self.longitude}"
        except Exception as e:
            _LOGGER.error("Error getting city name: %s", e)
            self._city = f"{self.latitude}_{self.longitude}"

        self._attr_unique_id = f"tomorrowio_cloud_coverage_{self._city}_{hour}"

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

    @property
    def device_info(self):
        """Return device information."""
        return {
            "identifiers": {("tomorrowio_cloud", f"tomorrowio_{self._city}")},
            "name": f"Tomorrow.io Cloud Coverage - {self._city}",
            "manufacturer": "Tomorrow.io",
            "model": "Cloud Coverage Forecast",
            "sw_version": "1.0",
        }

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