"""Support for LED selects."""
import logging

import json
import voluptuous as vol

from homeassistant.const import CONF_ICON, CONF_NAME
from homeassistant.components.select import SelectEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.components import mqtt

from .const import (
    DOMAIN,
    CONF_DEVICE_ID,
    CONF_CHANNEL,
    PIXIE_ATTR_PICTURE,
    PIXIE_PICTURE_LIST,
)

_LOGGER = logging.getLogger(__name__)

async def async_setup_entry(hass, config_entry, async_add_entities):
    select_picture = PixiePictureSelect(hass, config_entry)
    
    # Add devices
    async_add_entities([select_picture], True)

class PixiePictureSelect(SelectEntity):
    """Define a Pixie picture select"""
    _attr_icon = "mdi:playlist-play"

    def __init__(self, hass, config_entry):

        self.hass = hass
        create_name = False
        if CONF_NAME in config_entry.data:
            if config_entry.data[CONF_NAME] == "":
                create_name = True
            else:
                self._name = config_entry.data[CONF_NAME]
        else:
            create_name = True

        if create_name:
            self._name = "pixie_" + config_entry.data[CONF_DEVICE_ID] + "_" + str(config_entry.data[CONF_CHANNEL])
        self._picture = ""
        self._available = False
        self._device_id = config_entry.data[CONF_DEVICE_ID]
        self._channel = config_entry.data[CONF_CHANNEL]
        self._unique_id = config_entry.entry_id

        self.qos = 0
        self.retain = False
        self.availability_topic = "pixie_" + self._device_id + "/status"
        self.channel_topic = "pixie_" + self._device_id + "/channel" + str(self._channel)
        self.command_topic = "pixie_" + self._device_id + "/channel" + str(self._channel) + "/set"

    async def async_added_to_hass(self):
        """Subscribe to MQTT events."""
        @callback
        async def availability_received(msg):
            if msg.payload == "online":
                self._available = True
            else:
                self._available = False

        @callback
        async def message_received(msg):
            """Run when new MQTT message has been received."""

            _LOGGER.debug("MQTT message received: %s", msg.payload)
            try:
                data = json.loads(msg.payload)
            except vol.MultipleInvalid as error:
                _LOGGER.debug("Skipping update because of malformatted data: %s", error)
                return

            if "picture" in data:
                self._picture = data["picture"]

            self.async_write_ha_state()

        _LOGGER.info("Subscribe to the topic %s", self.availability_topic)
        await mqtt.async_subscribe( self.hass, self.availability_topic, availability_received, self.qos )

        _LOGGER.info("Subscribe to the topic %s", self.channel_topic)
        return await mqtt.async_subscribe( self.hass, self.channel_topic, message_received, self.qos )

    @property
    def available(self):
        """Return the availability of the light."""
        return self._available

    @property
    def unique_id(self):
        """Return the entity unique ID."""
        return self._unique_id

    @property
    def name(self):
        """Return the display name of this light."""
        return self._name

    @property
    def current_option(self):
        """Return the current selected picture."""
        return self._picture

    @property
    def options(self):
        """Return a list of available pictures as strings."""
        return PIXIE_PICTURE_LIST

    async def async_select_option(self, option: str):
        """Change the selected option."""
        _LOGGER.warning("Pixie Select Picture does not support a select option.")
        return



