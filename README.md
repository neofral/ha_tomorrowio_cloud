# tomorrowio_cloud
With this integration you can get the hourly cloud coverage which is not done with weather-forecast update action in Home Assistant

I spent many hours trying to get a simple code work and finally it's here.

After istalling, please put this in configuration.yaml:
sensor:
  - platform: tomorrowio_cloud
    api_key: YOUR_API_KEY  # Replace with your actual API key
    latitude: home_latitude  # Replace with your location 
    longitude: home_longitude # Replace with your location


After restarting Home Assistant you should see sensor.cloud_coverage_hour_1 to sensor.cloud_coverage_hour_24.
You can use this data to predict cloud coverage and adjust charging of your battery using low tarrif (night tarrif).

