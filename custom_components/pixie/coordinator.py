import logging

import json
import voluptuous as vol

from homeassistant.const import CONF_ICON, CONF_NAME
from homeassistant.components.select import SelectEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.components import mqtt
from homeassistant.components.light import (
    ATTR_RGB_COLOR,
    ATTR_RGBW_COLOR,
    ATTR_BRIGHTNESS,
    ATTR_EFFECT,
    PLATFORM_SCHEMA,
    SUPPORT_BRIGHTNESS,
    SUPPORT_COLOR,
    SUPPORT_EFFECT,
    SUPPORT_TRANSITION,
    COLOR_MODE_RGB,
    COLOR_MODE_RGBW,
    LightEntity,
)


from .const import (
    DOMAIN,
    CONF_DEVICE_ID,
    CONF_CHANNEL,
    PIXIE_ATTR_STATE,
    PIXIE_ATTR_TRANSITION_NAME,
    PIXIE_ATTR_TRANSITION,
    PIXIE_ATTR_PICTURE,
    PIXIE_ATTR_EFFECT,
    PIXIE_ATTR_PARAMETER1,
    PIXIE_ATTR_PARAMETER2,
    PIXIE_ATTR_BRIGHTNESS,
    PIXIE_ATTR_BOARD_TEMPERATURE,
    PIXIE_ATTR_UPTIME,
    PIXIE_ATTR_FIRMWARE_VERSION,
    PIXIE_ATTR_MAC,
    PIXIE_ATTR_IP_ADDR,
    PIXIE_ATTR_URL,
    SERVICE_SET_PICTURE,
    SERVICE_SET_EFFECT,
    SERVICE_TURN_ON_TRANSITION,
    SERVICE_TURN_OFF_TRANSITION,
    PIXIE_EFFECT_LIST,
    PIXIE_PICTURE_LIST,
    PIXIE_TRANSITION_LIST,
)

_LOGGER = logging.getLogger(__name__)

class PixieCoordinator:
    def __init__(self, hass, config_entry):
        self.hass = hass

        self._state = False
        self._brightness = 255
        self._color_mode = COLOR_MODE_RGB
        self._white_value = 0
        self._parameter1 = 0
        self._parameter2 = 0
        self._rgb = (255, 255, 255)
        self._picture = None
        self._effect = None
        self._available = False
        self._board_temperature = None
        self._uptime = None
        self._device_id = config_entry.data[CONF_DEVICE_ID]
        self._channel = config_entry.data[CONF_CHANNEL]
        self._firmware_version = None
        self._ip_addr = None
        self._mac = None
        self._url = None
        
        self._available_version = None
        self._available_version_int = 0
        self._firmware_version_int = 0
        self._ota_state = None
        self._ota_in_progress = False

        self.qos = 0
        self.retain = False
        self.availability_topic = f"pixie_{self._device_id}/status"
        self.channel_topic = f"pixie_{self._device_id}/channel{self._channel}"
        self.request_topic = f"pixie_{self._device_id}/channel{self._channel}/get"
        self.command_topic = f"pixie_{self._device_id}/channel{self._channel}/set"
        self.attribute_request_topic = f"pixie_{self._device_id}/attributes/get"
        self.attribute_topic = f"pixie_{self._device_id}/attributes"
        self.all_channels_topic = f"pixie_{self._device_id}/channel"
        self.ota_check_topic = f"pixie_{self._device_id}/ota/check"
        self.ota_perform_topic = f"pixie_{self._device_id}/ota/perform"
        self.ota_reply_topic = f"pixie_{self._device_id}/ota"

        self._light_state_callback = None
        self._availability_callback = None
        self._uptime_callback = None
        self._board_temp_callback = None
        self._picture_callback = None
        self._effect_callback = None
        self._attr_callback = None
        self._ota_callback = None

        _LOGGER.info("Set up a coordinator for the device %s; channel %s;", self._device_id, self._channel)

    def uptime_sensor_callback(self, callback=None):
        self._uptime_callback = callback

    def board_temp_sensor_callback(self, callback=None):
        self._board_temp_callback = callback

    def picture_select_callback(self, callback=None):
        self._picture_callback = callback

    def effect_select_callback(self, callback=None):
        self._effect_callback = callback

    def light_state_callback(self, callback=None):
        self._light_state_callback = callback

    def attr_callback(self, callback=None):
        self._attr_callback = callback

    def ota_callback(self, callback=None):
        self._ota_callback = callback

    async def async_mqtt_handler(self):
        """Subscribe to MQTT events."""
        @callback
        async def availability_received(msg):
            _LOGGER.debug("[%s] MQTT availability message received: %s", self._device_id, msg.payload)
            if msg.payload == "online":
                self._available = True
            else:
                self._available = False

            if self._light_state_callback != None:
                self._light_state_callback()

            if self._uptime_callback != None:
                self._uptime_callback()

            if self._board_temp_callback != None:
                self._board_temp_callback()

            if self._picture_callback != None:
                self._picture_callback()

            if self._effect_callback != None:
                self._effect_callback()

        @callback
        async def attribute_message_received(msg):
            _LOGGER.debug("[%s] MQTT attribute message received: %s", self._device_id, msg.payload)
            try:
                data = json.loads(msg.payload)
            except vol.MultipleInvalid as error:
                _LOGGER.warning("[%s] Skipping update because of malformatted data: %s", self._device_id, error)
                return

            if PIXIE_ATTR_BOARD_TEMPERATURE in data:
                self._board_temperature = data[PIXIE_ATTR_BOARD_TEMPERATURE]
                if self._board_temp_callback != None:
                    self._board_temp_callback()

            if PIXIE_ATTR_UPTIME in data:
                self._uptime = data[PIXIE_ATTR_UPTIME]
                if self._uptime_callback != None:
                    self._uptime_callback()

            if PIXIE_ATTR_FIRMWARE_VERSION in data:
                self._firmware_version = data[PIXIE_ATTR_FIRMWARE_VERSION]
                if self._firmware_version != None:
                    self._attr_callback()

            if PIXIE_ATTR_IP_ADDR in data:
                self._ip_addr = data[PIXIE_ATTR_IP_ADDR]
                if self._ip_addr != None:
                    self._attr_callback()

            if PIXIE_ATTR_MAC in data:
                self._mac = data[PIXIE_ATTR_MAC]
                if self._mac != None:
                    self._attr_callback()

            if PIXIE_ATTR_URL in data:
                self._url = data[PIXIE_ATTR_URL]
                if self._url != None:
                    self._attr_callback()


        @callback
        async def message_received(msg):
            """Run when new MQTT message has been received."""

            _LOGGER.debug("[%s] MQTT message received: %s", self._device_id, msg.payload)
            try:
                data = json.loads(msg.payload)
            except vol.MultipleInvalid as error:
                _LOGGER.warning("[%s] Skipping update because of malformatted data: %s", self._device_id, error)
                return

            if PIXIE_ATTR_PICTURE in data:
                self._picture = data[PIXIE_ATTR_PICTURE]
            else:
                self._picture = None

            if PIXIE_ATTR_EFFECT in data:
                self._effect = data[PIXIE_ATTR_EFFECT]
            else:
                self._effect = None

            if data["state"].upper() == "ON":
                self._state = True
            elif data["state"].upper() == "OFF":
                self._state = False

            if "color" in data:
                r = int(data["color"]["r"])  # pylint: disable=invalid-name
                g = int(data["color"]["g"])  # pylint: disable=invalid-name
                b = int(data["color"]["b"])  # pylint: disable=invalid-name
                self._rgb = (r, g, b)

            if "parameter1" in data:
                self._parameter1 = int(data["parameter1"])

            if "parameter2" in data:
                self._parameter2 = int(data["parameter2"])

            if "brightness" in data:
                self._brightness = int(data["brightness"])

            if "white_value" in data:
                self._white_value = int(data["white_value"])

            if self._effect_callback != None:
                self._effect_callback()

            if self._picture_callback != None:
                self._picture_callback()

            if self._light_state_callback != None:
                self._light_state_callback()
        
        @callback
        async def ota_message_received(msg):
            _LOGGER.debug("[%s] MQTT OTA message received: %s", self._device_id, msg.payload)
            try:
                data = json.loads(msg.payload)
            except vol.MultipleInvalid as error:
                _LOGGER.warning("[%s] Skipping update because of malformatted data: %s", self._device_id, error)
                return
            
            if ("ota_state" in data) and ("ota_type" in data) and ("result" in data):
                if data["ota_state"] == "start" and data["ota_type"] == "update" and data["result"] == 1:
                    self._ota_in_progress = True
                    _LOGGER.info("[%s] OTA update has started", self._device_id)
                elif data["ota_state"] == "end" and data["ota_type"] == "update" and data["result"] == 1:
                    self._ota_in_progress = False
                    self._firmware_version = self._available_version
                    _LOGGER.info("[%s] OTA update has finished", self._device_id)
                elif data["ota_state"] == "end" and data["ota_type"] == "update" and data["result"] != 1:
                    _LOGGER.warning("[%s] OTA update has failed", self._device_id)
                    self._ota_in_progress = False
                elif data["ota_state"] == "end" and data["ota_type"] == "check" and data["result"] != 1:
                    _LOGGER.warning("[%s] OTA check update has failed", self._device_id)
                elif data["ota_state"] == "end" and data["ota_type"] == "check" and data["result"] == 1:

                    if "remote_version" in data:
                        rmt_ver = data["remote_version"].split('.')
                        if len(rmt_ver) == 3:
                            self._available_version_int = 100 * int(rmt_ver[0]) + 10 * int(rmt_ver[1]) + int(rmt_ver[2])
                            self._available_version = data["remote_version"]
                            _LOGGER.debug("[%s] Available firmware version: %s", self._device_id, self._available_version)

                    if "running_version" in data:
                        run_ver = data["running_version"].split('.')
                        if len(run_ver) == 3:
                            self._firmware_version_int = 100 * int(run_ver[0]) + 10 * int(run_ver[1]) + int(run_ver[2])
                            self._firmware_version = data["running_version"]
                            _LOGGER.debug("[%s] Running firmware version: %s", self._device_id, self._firmware_version)
            else:
                _LOGGER.warning("[%s]: Malformatted OTA message received: %s", self._device_id, msg.payload)

            if self._ota_callback != None:
                self._ota_callback()

        _LOGGER.info("Subscribe to the topic %s", self.availability_topic)
        await mqtt.async_subscribe( self.hass, self.availability_topic, availability_received, self.qos )

        _LOGGER.info("Subscribe to the topic %s", self.attribute_topic)
        await mqtt.async_subscribe( self.hass, self.attribute_topic, attribute_message_received, self.qos )

        _LOGGER.info("Subscribe to the topic %s", self.channel_topic)
        await mqtt.async_subscribe( self.hass, self.channel_topic, message_received, self.qos )

        _LOGGER.info("Subscribe to the topic %s", self.ota_reply_topic)
        await mqtt.async_subscribe( self.hass, self.ota_reply_topic, ota_message_received, self.qos )

        _LOGGER.info("Request the current state over the topic %s", self.request_topic)
        await mqtt.async_publish( self.hass, self.request_topic, "1", self.qos, False )

        _LOGGER.info("Request the attributes over the topic %s", self.attribute_request_topic)
        await mqtt.async_publish( self.hass, self.attribute_request_topic, "1", self.qos, False )

    async def publish_command(self, message, qos, retain):
        _LOGGER.info("Publish a command %s to the topic %s", message, self.command_topic)
        await mqtt.async_publish( self.hass, self.command_topic, message, qos, retain )

    async def ota_check(self):
        _LOGGER.info("Check OTA availability: publish a request to the topic %s", self.ota_check_topic)
        await mqtt.async_publish( self.hass, self.ota_check_topic, "1", 0, False )
    
    async def ota_perform(self):
        _LOGGER.info("Perform OTA update: publish a request to the topic %s", self.ota_perform_topic)
        await mqtt.async_publish( self.hass, self.ota_perform_topic, "1", 0, False )

    def device_id(self):
        return self._device_id

    def channel(self):
        return self._channel

    def available(self):
        return self._available

    def picture(self):
        return self._picture

    def effect(self):
        return self._effect

    def board_temperature(self):
        return self._board_temperature

    def uptime(self):
        return self._uptime

    def state(self):
        return self._state

    def brightness(self):
        return self._brightness

    def color_mode(self):
        return self._color_mode

    def white_value(self):
        return self._white_value

    def parameter1(self):
        return self._parameter1

    def parameter2(self):
        return self._parameter2

    def rgb(self):
        return self._rgb

    def firmware_version(self):
        return self._firmware_version

    def ip_addr(self):
        return self._ip_addr

    def mac(self):
        return self._mac

    def url(self):
        return self._url

    def available_version(self):
        return self._available_version

    def available_version_int(self):
        return self._available_version_int

    def firmware_version_int(self):
        return self._firmware_version_int

    def ota_in_progress(self):
        return self._ota_in_progress
