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
    PIXIE_ATTR_EFFECT,
    PIXIE_PICTURE_LIST,
    PIXIE_EFFECT_LIST,
)

_LOGGER = logging.getLogger(__name__)

async def async_setup_entry(hass, config_entry, async_add_entities):
    coordinator = PixieSelectCoordinator(hass, config_entry)

    select_picture = PixiePictureSelect(coordinator)
    select_effect = PixieEffectSelect(coordinator)

    # Add devices
    async_add_entities([select_picture, select_effect], True)


class PixieSelectCoordinator:
    def __init__(self, hass, config_entry):
        self.hass = hass
        self._picture = None
        self._effect = None
        self._available = False
        self._device_id = config_entry.data[CONF_DEVICE_ID]
        self._channel = config_entry.data[CONF_CHANNEL]

        self.qos = 0
        self.retain = False
        self.availability_topic = f"pixie_{self._device_id}/status"
        self.channel_topic = f"pixie_{self._device_id}/channel{self._channel}"
        self.command_topic = f"pixie_{self._device_id}/channel{self._channel}/set"

        self._state_update_callback = None

    def set_state_update_callback(self, callback=None):
        self._state_update_callback = callback

    async def async_mqtt_handler(self):
        """Subscribe to MQTT events."""
        @callback
        async def availability_received(msg):
            if msg.payload == "online":
                self._available = True
            else:
                self._available = False
            
            if self._state_update_callback != None:
                self._state_update_callback()


        @callback
        async def message_received(msg):
            """Run when new MQTT message has been received."""

            _LOGGER.debug("MQTT message received: %s", msg.payload)
            try:
                data = json.loads(msg.payload)
            except vol.MultipleInvalid as error:
                _LOGGER.debug("Skipping update because of malformatted data: %s", error)
                return

            if PIXIE_ATTR_PICTURE in data:
                self._picture = data[PIXIE_ATTR_PICTURE]
            else:
                self._picture = None

            if PIXIE_ATTR_EFFECT in data:
                self._effect = data[PIXIE_ATTR_EFFECT]
            else:
                self._effect = None

            if self._state_update_callback != None:
                self._state_update_callback()

        _LOGGER.info("Subscribe to the topic %s", self.availability_topic)
        await mqtt.async_subscribe( self.hass, self.availability_topic, availability_received, self.qos )

        _LOGGER.info("Subscribe to the topic %s", self.channel_topic)
        return await mqtt.async_subscribe( self.hass, self.channel_topic, message_received, self.qos )

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


class PixiePictureSelect(SelectEntity):
    """Define a Pixie picture select"""
    _attr_icon = "mdi:playlist-play"
    _attr_entity_registry_enabled_default = False

    def __init__(self, coordinator):
        self._coordinator = coordinator
        self._device_id = coordinator.device_id()
        self._channel = coordinator.channel()
        self._attr_unique_id = f"pixie_{self._device_id}_{self._channel}_picture"
        self._attr_name = f"Pixie {self._device_id} {self._channel} Picture"

    def state_update_callback(self):
        self.async_write_ha_state()

    async def async_added_to_hass(self):
        """Subscribe to MQTT events."""
        self._coordinator.set_state_update_callback(self.state_update_callback)
        await self._coordinator.async_mqtt_handler()

    @property
    def available(self):
        """Return the availability of the light."""
        return self._coordinator.available()

    @property
    def current_option(self):
        """Return the current selected picture."""
        return self._coordinator.picture()

    @property
    def options(self):
        """Return a list of available pictures as strings."""
        return PIXIE_PICTURE_LIST

    async def async_select_option(self, option: str):
        """Change the selected option."""
        _LOGGER.warning("Pixie Select Picture does not currently support a select option.")
        return



class PixieEffectSelect(SelectEntity):
    """Define a Pixie effect select"""
    _attr_icon = "mdi:playlist-play"
    _attr_entity_registry_enabled_default = False

    def __init__(self, coordinator):
        self._coordinator = coordinator
        self._device_id = coordinator.device_id()
        self._channel = coordinator.channel()
        self._attr_unique_id = f"pixie_{self._device_id}_{self._channel}_effect"
        self._attr_name = f"Pixie {self._device_id} {self._channel} Effect"

    def state_update_callback(self):
        self.async_write_ha_state()

    async def async_added_to_hass(self):
        """Subscribe to MQTT events."""
        self._coordinator.set_state_update_callback(self.state_update_callback)
        await self._coordinator.async_mqtt_handler()

    @property
    def available(self):
        """Return the availability of the light."""
        return self._coordinator.available()

    @property
    def current_option(self):
        """Return the current selected effect."""
        return self._coordinator.effect()

    @property
    def options(self):
        """Return a list of available effects as strings."""
        return PIXIE_EFFECT_LIST

    async def async_select_option(self, option: str):
        """Change the selected option."""
        _LOGGER.warning("Pixie Select Effect does not currently support a select option.")
        return


