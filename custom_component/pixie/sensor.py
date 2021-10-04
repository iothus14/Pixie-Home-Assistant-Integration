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

    board_temperature_sensor = PixieBoardTemperatureSensor(hass, config_entry)
    uptime_sensor = PixieUptimeSensor(hass, config_entry)

    sensors = [ board_temperature_sensor, uptime_sensor ]

    async_add_entities(sensors)


class PixieBoardTemperatureSensor(SensorEntity):
    """Defines a Pixie board temperature sensor."""

    _attr_native_unit_of_measurement = TEMP_CELSIUS
    _attr_device_class = DEVICE_CLASS_TEMPERATURE
    _attr_icon = "mdi:thermometer"
    _attr_entity_registry_enabled_default = False

    def __init__(self, hass, config_entry):
        self._device_id = config_entry.data[CONF_DEVICE_ID]
        self._channel = config_entry.data[CONF_CHANNEL]
        self._attr_name = f"Pixie {self._device_id} {self._channel} Board Temperature"
        self._attr_unique_id = f"pixie_{self._device_id}_{self._channel}_board_temperature"

        self._board_temperature = None

        self.qos = 0
        self.retain = False
        self.availability_topic = f"pixie_{self._device_id}/status"
        self.attribute_topic = f"pixie_{self._device_id}/attributes"

    async def async_added_to_hass(self):
        """Subscribe to MQTT events."""

        @callback
        async def availability_received(msg):
            if msg.payload == "online":
                self._available = True
            else:
                self._available = False

            self.async_write_ha_state()

        @callback
        async def message_received(msg):
            """Run when new MQTT message has been received."""

            _LOGGER.debug("MQTT message received: %s", msg.payload)
            try:
                data = json.loads(msg.payload)
            except vol.MultipleInvalid as error:
                _LOGGER.debug("Skipping update because of malformatted data: %s", error)
                return

            if PIXIE_ATTR_BOARD_TEMPERATURE in data:
                self._board_temperature = data[PIXIE_ATTR_BOARD_TEMPERATURE]

            self.async_write_ha_state()

        _LOGGER.info("Subscribe to the topic %s", self.availability_topic)
        await mqtt.async_subscribe( self.hass, self.availability_topic, availability_received, self.qos )

        _LOGGER.info("Subscribe to the topic %s", self.attribute_topic)
        return await mqtt.async_subscribe( self.hass, self.attribute_topic, message_received, self.qos )

    @property
    def native_value(self):
        """Return the state of the sensor."""
        return self._board_temperature


class PixieUptimeSensor(SensorEntity):
    """Defines a Pixie uptime sensor."""

    _attr_entity_registry_enabled_default = False
    _attr_icon = "mdi:clock-outline"

    def __init__(self, hass, config_entry):
        """Initialize a Pixie uptime sensor."""
        self._device_id = config_entry.data[CONF_DEVICE_ID]
        self._channel = config_entry.data[CONF_CHANNEL]
        self._attr_name = f"Pixie {self._device_id} {self._channel} Uptime"
        self._attr_unique_id = f"pixie_{self._device_id}_{self._channel}_uptime"

        self._uptime = None

        self.qos = 0
        self.retain = False
        self.availability_topic = f"pixie_{self._device_id}/status"
        self.attribute_topic = f"pixie_{self._device_id}/attributes"

    async def async_added_to_hass(self):
        """Subscribe to MQTT events."""

        @callback
        async def availability_received(msg):
            if msg.payload == "online":
                self._available = True
            else:
                self._available = False

            self.async_write_ha_state()

        @callback
        async def message_received(msg):
            """Run when new MQTT message has been received."""

            _LOGGER.debug("MQTT message received: %s", msg.payload)
            try:
                data = json.loads(msg.payload)
            except vol.MultipleInvalid as error:
                _LOGGER.debug("Skipping update because of malformatted data: %s", error)
                return

            if PIXIE_ATTR_UPTIME in data:
                self._uptime = data[PIXIE_ATTR_UPTIME]
                    

            self.async_write_ha_state()

        _LOGGER.info("Subscribe to the topic %s", self.availability_topic)
        await mqtt.async_subscribe( self.hass, self.availability_topic, availability_received, self.qos )

        _LOGGER.info("Subscribe to the topic %s", self.attribute_topic)
        return await mqtt.async_subscribe( self.hass, self.attribute_topic, message_received, self.qos )


    @property
    def native_value(self):
        """Return the state of the sensor."""
        return self._uptime

