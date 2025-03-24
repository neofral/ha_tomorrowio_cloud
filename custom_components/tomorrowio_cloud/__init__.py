DOMAIN = "tomorrowio_cloud"

async def async_setup_entry(hass, entry):
    """Set up the Tomorrow.io integration."""
    hass.data[DOMAIN] = entry.data
    return True
