from datetime import timedelta
import logging

import json
import voluptuous as vol

from homeassistant.components.sensor import DEVICE_CLASS_CURRENT, SensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import (
    DEVICE_CLASS_TEMPERATURE,
    DEVICE_CLASS_TIMESTAMP,
    TEMP_CELSIUS,
)
from homeassistant.core import HomeAssistant, HomeAssistantError, callback
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.components import mqtt
from homeassistant.util.dt import utcnow

from .const import (
    DOMAIN,
    CONF_DEVICE_ID,
    CONF_CHANNEL,
    PIXIE_ATTR_UPTIME,
    PIXIE_ATTR_BOARD_TEMPERATURE,
)

_LOGGER = logging.getLogger(__name__)

async def async_setup_entry( hass: HomeAssistant, config_entry: ConfigEntry, async_add_entities: AddEntitiesCallback ):
    """Set up Pixie sensors"""

    coordinator = hass.data[DOMAIN]["coordinator"]
    board_temperature_sensor = PixieBoardTemperatureSensor(coordinator)
    uptime_sensor = PixieUptimeSensor(coordinator)

    sensors = [ board_temperature_sensor, uptime_sensor ]

    async_add_entities(sensors)


class PixieBoardTemperatureSensor(SensorEntity):
    """Defines a Pixie board temperature sensor."""

    _attr_native_unit_of_measurement = TEMP_CELSIUS
    _attr_device_class = DEVICE_CLASS_TEMPERATURE
    _attr_icon = "mdi:thermometer"
    _attr_entity_registry_enabled_default = False

    def __init__(self, coordinator):
        self._coordinator = coordinator
        self._device_id = coordinator.device_id()
        self._channel = coordinator.channel()
        self._attr_name = f"Pixie {self._device_id} {self._channel} Board Temperature"
        self._attr_unique_id = f"pixie_{self._device_id}_{self._channel}_board_temperature"

    def state_update_callback(self):
        self.async_write_ha_state()

    async def async_added_to_hass(self):
        """Subscribe to MQTT events."""
        self._coordinator.board_temp_sensor_callback(self.state_update_callback)
        await self._coordinator.async_mqtt_handler()

    @property
    def native_value(self):
        """Return the state of the sensor."""
        return self._coordinator.board_temperature()

    @property
    def available(self):
        """Return the availability of the sensor."""
        return self._coordinator.available()


class PixieUptimeSensor(SensorEntity):
    """Defines a Pixie uptime sensor."""

    _attr_entity_registry_enabled_default = False
    _attr_icon = "mdi:clock-outline"

    def __init__(self, coordinator):
        self._coordinator = coordinator
        self._device_id = coordinator.device_id()
        self._channel = coordinator.channel()
        self._attr_name = f"Pixie {self._device_id} {self._channel} Uptime"
        self._attr_unique_id = f"pixie_{self._device_id}_{self._channel}_uptime"

    def state_update_callback(self):
        self.async_write_ha_state()

    async def async_added_to_hass(self):
        """Subscribe to MQTT events."""
        self._coordinator.uptime_sensor_callback(self.state_update_callback)
        await self._coordinator.async_mqtt_handler()

    @property
    def native_value(self):
        """Return the state of the sensor."""
        return self._coordinator.uptime()

    @property
    def available(self):
        """Return the availability of the sensor."""
        return self._coordinator.available()

