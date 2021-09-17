"""Platform for light integration."""
import logging

import json
import voluptuous as vol

from homeassistant.helpers import config_validation as cv, entity_platform, service
from homeassistant.const import CONF_DEVICE_ID, CONF_ICON, CONF_NAME
from homeassistant.core import HomeAssistant, HomeAssistantError, callback
from homeassistant.config_entries import ConfigEntry
from homeassistant.config_entries import SOURCE_IMPORT
from homeassistant.components import mqtt
from homeassistant.components.light import (
    ATTR_RGB_COLOR,
    ATTR_RGBW_COLOR,
    ATTR_BRIGHTNESS,
    ATTR_EFFECT,
    ATTR_WHITE_VALUE,
    PLATFORM_SCHEMA,
    SUPPORT_BRIGHTNESS,
    SUPPORT_COLOR,
    SUPPORT_EFFECT,
    SUPPORT_WHITE_VALUE,
    SUPPORT_TRANSITION,
    COLOR_MODE_RGB,
    COLOR_MODE_RGBW,
    LightEntity,
)


from .const import (
    DOMAIN,
    CONF_CHANNEL,
    PIXIE_ATTR_STATE,
    PIXIE_ATTR_TRANSITION_NAME,
    PIXIE_ATTR_TRANSITION,
    PIXIE_ATTR_PICTURE,
    PIXIE_ATTR_EFFECT,
    PIXIE_ATTR_PARAMETER1,
    PIXIE_ATTR_PARAMETER2,
    PIXIE_ATTR_BRIGHTNESS,
    SERVICE_SET_PICTURE,
    SERVICE_SET_EFFECT,
    SERVICE_TURN_ON_TRANSITION,
    SERVICE_TURN_OFF_TRANSITION,
    PIXIE_EFFECT_LIST,
    PIXIE_PICTURE_LIST,
    PIXIE_TRANSITION_LIST,
)

_LOGGER = logging.getLogger(__name__)

SUPPORT_PIXIE = SUPPORT_BRIGHTNESS | SUPPORT_EFFECT | SUPPORT_COLOR | SUPPORT_TRANSITION

# Validation of the user's configuration
PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend({
    vol.Required(CONF_DEVICE_ID): cv.string,
    vol.Required(CONF_CHANNEL, default=0): vol.All( vol.Coerce(int), vol.In([0, 1, 2, 3] ) ),
    vol.Optional(CONF_NAME): cv.string,
})


async def async_setup_platform(hass, config, async_add_entities, discovery_info=None):
    """Set up the Pixie Light platform."""

    hass.async_create_task(
        hass.config_entries.flow.async_init(
            DOMAIN, context={"source": SOURCE_IMPORT}, data=dict(config)
        )
    )


async def async_setup_entry(hass, config_entry, async_add_entities):
    """Add a Foscam IP camera from a config entry."""
    #platform = entity_platform.async_get_current_platform()

    light = PixieLight(hass, config_entry)
    
    # Add devices
    async_add_entities([light], True)


class PixieLight(LightEntity):
    """Representation of a Pixie Light."""

    def __init__(self, hass, config_entry):
        """Initialize a PixieLight."""
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
        self._state = False
        self._brightness = 255
        self._color_mode = COLOR_MODE_RGB
        self._effect = ""
        self._white_value = 0
        self._parameter1 = 0
        self._parameter2 = 0
        self._picture = ""
        self._rgb = (255, 255, 255)
        self._available = False
        self._device_id = config_entry.data[CONF_DEVICE_ID]
        self._channel = config_entry.data[CONF_CHANNEL]
        self._unique_id = config_entry.entry_id

        self.qos = 0
        self.retain = False
        self.availability_topic = "pixie_" + self._device_id + "/status"
        self.command_topic = "pixie_" + self._device_id + "/channel" + str(self._channel) + "/set"
        self.channel_topic = "pixie_" + self._device_id + "/channel" + str(self._channel)
        self.all_channels_topic = "pixie_" + self._device_id + "/channel"

        platform = entity_platform.async_get_current_platform()
        platform.async_register_entity_service(
            SERVICE_SET_EFFECT,
            {
                vol.Required(PIXIE_ATTR_EFFECT): cv.string,
                vol.Optional(PIXIE_ATTR_PARAMETER1): vol.All( vol.Coerce(int), vol.Range(min=0, max=255) ),
                vol.Optional(PIXIE_ATTR_PARAMETER2): vol.All( vol.Coerce(int), vol.Range(min=0, max=255) ),
                vol.Optional(PIXIE_ATTR_BRIGHTNESS): vol.All( vol.Coerce(int), vol.Range(min=0, max=255) ),
                vol.Exclusive(ATTR_RGB_COLOR, ATTR_RGB_COLOR): vol.All(
                    vol.ExactSequence((cv.byte,) * 3), vol.Coerce(tuple)
                ),
            },
            "async_set_effect",
        )
        platform.async_register_entity_service(
            SERVICE_SET_PICTURE,
            {
                vol.Required(PIXIE_ATTR_PICTURE): cv.string,
                vol.Optional(PIXIE_ATTR_PARAMETER1): vol.All( vol.Coerce(int), vol.Range(min=0, max=255) ),
                vol.Optional(PIXIE_ATTR_PARAMETER2): vol.All( vol.Coerce(int), vol.Range(min=0, max=255) ),
                vol.Optional(PIXIE_ATTR_BRIGHTNESS): vol.All( vol.Coerce(int), vol.Range(min=0, max=255) ),
                vol.Exclusive(ATTR_RGB_COLOR, ATTR_RGB_COLOR): vol.All(
                    vol.ExactSequence((cv.byte,) * 3), vol.Coerce(tuple)
                ),
            },
            "async_set_picture",
        )
        platform.async_register_entity_service(
            SERVICE_TURN_ON_TRANSITION,
            {
                vol.Required(PIXIE_ATTR_TRANSITION_NAME): cv.string,
                vol.Required(PIXIE_ATTR_TRANSITION): vol.All( vol.Coerce(int), vol.Range(min=0, max=4096) ),
                vol.Optional(PIXIE_ATTR_PARAMETER1): vol.All( vol.Coerce(int), vol.Range(min=0, max=255) ),
                vol.Optional(PIXIE_ATTR_PARAMETER2): vol.All( vol.Coerce(int), vol.Range(min=0, max=255) ),
                vol.Optional(PIXIE_ATTR_BRIGHTNESS): vol.All( vol.Coerce(int), vol.Range(min=0, max=255) ),
                vol.Required(ATTR_RGB_COLOR, ATTR_RGB_COLOR): vol.All(
                    vol.ExactSequence((cv.byte,) * 3), vol.Coerce(tuple)
                ),
            },
            "async_turn_on_transition",
        )
        platform.async_register_entity_service(
            SERVICE_TURN_OFF_TRANSITION,
            {
                vol.Required(PIXIE_ATTR_TRANSITION_NAME): cv.string,
                vol.Required(PIXIE_ATTR_TRANSITION): vol.All( vol.Coerce(int), vol.Range(min=0, max=4096) ),
                vol.Optional(PIXIE_ATTR_PARAMETER1): vol.All( vol.Coerce(int), vol.Range(min=0, max=255) ),
                vol.Optional(PIXIE_ATTR_PARAMETER2): vol.All( vol.Coerce(int), vol.Range(min=0, max=255) ),
            },
            "async_turn_off_transition",
        )

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
        
            self.async_write_ha_state()

        await mqtt.async_subscribe( self.hass, self.availability_topic, availability_received, self.qos )

        _LOGGER.info("Subscribe topic %s", self.channel_topic)
        return await mqtt.async_subscribe( self.hass, self.channel_topic, message_received, self.qos )


    async def async_turn_on(self, **kwargs):
        """Instruct the light to turn on."""

        message = {"state": "ON"}

        if "brightness" in kwargs:
            device_brightness = min( kwargs["brightness"], 255 )
            device_brightness = max(device_brightness, 1) # Make sure the brightness is not rounded down to 0
            message["brightness"] = device_brightness

        if "parameter1" in kwargs:
            message["parameter1"] = min( kwargs["parameter1"], 255 )

        if "parameter2" in kwargs:
            message["parameter2"] = min( kwargs["parameter2"], 255 )

        if "white_value" in kwargs:
            message["white_value"] = min( kwargs["white_value"], 255 )

        if "effect" in kwargs:
            message["effect"] = kwargs["effect"]
        elif "picture" in kwargs:
            message["picture"] = kwargs["picture"]
        elif "transition" in kwargs:
            message["transition"] = kwargs["transition"]
            if "transition_name" in kwargs:
                message["transition_name"] = kwargs["transition_name"]
        
        if ATTR_RGB_COLOR in kwargs:
            rgb = kwargs[ATTR_RGB_COLOR]
            message["color"] = {"r": rgb[0], "g": rgb[1], "b": rgb[2]}

        if ATTR_RGBW_COLOR in kwargs:
            rgb = kwargs[ATTR_RGBW_COLOR]
            message["color"] = {"r": rgb[0], "g": rgb[1], "b": rgb[2], "w": rgb[3]}

        mqtt.async_publish(
            self.hass,
            self.command_topic,
            json.dumps(message),
            self.qos,
            self.retain,
        )

    async def async_turn_off(self, **kwargs):
        """Instruct the light to turn off."""
        message = {"state": "OFF"}
        mqtt.async_publish(
            self.hass,
            self.command_topic,
            json.dumps(message),
            self.qos,
            self.retain,
        )

    async def async_set_effect(self, **kwargs):
        """Set an effect of a Pixie light."""
        message = {"state": "ON"}

        message["effect"] = kwargs[PIXIE_ATTR_EFFECT]

        if PIXIE_ATTR_PARAMETER1 in kwargs:
            message["parameter1"] = min( kwargs[PIXIE_ATTR_PARAMETER1], 255 )

        if PIXIE_ATTR_PARAMETER2 in kwargs:
            message["parameter2"] = min( kwargs[PIXIE_ATTR_PARAMETER2], 255 )

        if ATTR_RGBW_COLOR in kwargs:
            rgb = kwargs[ATTR_RGBW_COLOR]
            message["color"] = {"r": rgb[0], "g": rgb[1], "b": rgb[2], "w": rgb[3]}

        if ATTR_RGB_COLOR in kwargs:
            rgb = kwargs[ATTR_RGB_COLOR]
            message["color"] = {"r": rgb[0], "g": rgb[1], "b": rgb[2]}

        if PIXIE_ATTR_BRIGHTNESS in kwargs:
            message["brightness"] = min( max(1, kwargs[PIXIE_ATTR_BRIGHTNESS]), 255 )

        mqtt.async_publish(
            self.hass,
            self.command_topic,
            json.dumps(message),
            self.qos,
            self.retain,
        )

    async def async_set_picture(self, **kwargs):
        """Set a picture of a Pixie light."""
        message = {"state": "ON"}

        message["picture"] = kwargs[PIXIE_ATTR_PICTURE]

        if PIXIE_ATTR_PARAMETER1 in kwargs:
            message["parameter1"] = min( kwargs[PIXIE_ATTR_PARAMETER1], 255 )

        if PIXIE_ATTR_PARAMETER2 in kwargs:
            message["parameter2"] = min( kwargs[PIXIE_ATTR_PARAMETER2], 255 )

        if ATTR_RGBW_COLOR in kwargs:
            rgb = kwargs[ATTR_RGBW_COLOR]
            message["color"] = {"r": rgb[0], "g": rgb[1], "b": rgb[2], "w": rgb[3]}

        if ATTR_RGB_COLOR in kwargs:
            rgb = kwargs[ATTR_RGB_COLOR]
            message["color"] = {"r": rgb[0], "g": rgb[1], "b": rgb[2]}

        if PIXIE_ATTR_BRIGHTNESS in kwargs:
            message["brightness"] = min( max(1, kwargs[PIXIE_ATTR_BRIGHTNESS]), 255 )

        mqtt.async_publish(
            self.hass,
            self.command_topic,
            json.dumps(message),
            self.qos,
            self.retain,
        )

    async def async_turn_on_transition(self, **kwargs):
        """Turn a Pixie light on with a transition."""

        message = {"state": "ON"}
        message["transition_name"] = kwargs[PIXIE_ATTR_TRANSITION_NAME]
        message["transition"] = kwargs[PIXIE_ATTR_TRANSITION]

        if PIXIE_ATTR_PARAMETER1 in kwargs:
            message["parameter1"] = min( kwargs[PIXIE_ATTR_PARAMETER1], 255 )

        if PIXIE_ATTR_PARAMETER2 in kwargs:
            message["parameter2"] = min( kwargs[PIXIE_ATTR_PARAMETER2], 255 )

        if ATTR_RGBW_COLOR in kwargs:
            rgb = kwargs[ATTR_RGBW_COLOR]
            message["color"] = {"r": rgb[0], "g": rgb[1], "b": rgb[2], "w": rgb[3]}
        
        if ATTR_RGB_COLOR in kwargs:
            rgb = kwargs[ATTR_RGB_COLOR]
            message["color"] = {"r": rgb[0], "g": rgb[1], "b": rgb[2]}

        if PIXIE_ATTR_BRIGHTNESS in kwargs:
            message["brightness"] = min( max(1, kwargs[PIXIE_ATTR_BRIGHTNESS]), 255 )

        mqtt.async_publish(
            self.hass,
            self.command_topic,
            json.dumps(message),
            self.qos,
            self.retain,
        )

    async def async_turn_off_transition(self, **kwargs):
        """Turn a Pixie light off with a transition."""

        message = {"state": "OFF"}
        message["transition_name"] = kwargs[PIXIE_ATTR_TRANSITION_NAME]
        message["transition"] = kwargs[PIXIE_ATTR_TRANSITION]

        if PIXIE_ATTR_PARAMETER1 in kwargs:
            message["parameter1"] = min( kwargs[PIXIE_ATTR_PARAMETER1], 255 )

        if PIXIE_ATTR_PARAMETER2 in kwargs:
            message["parameter2"] = min( kwargs[PIXIE_ATTR_PARAMETER2], 255 )

        mqtt.async_publish(
            self.hass,
            self.command_topic,
            json.dumps(message),
            self.qos,
            self.retain,
        )

    @property
    def unique_id(self):
        """Return the entity unique ID."""
        return self._unique_id

    @property
    def name(self):
        """Return the display name of this light."""
        return self._name

    @property
    def brightness(self):
        """Return brightness"""
        return self._brightness

    @property
    def is_on(self):
        """Return true if light is on."""
        return self._state

    @property
    def rgb_color(self):
        """Return the hs color value."""
        return self._rgb

    @property
    def parameter1(self):
        """Return parameter1 which is used to adjust effects/pictures/transitions"""
        return self._parameter1

    @property
    def parameter2(self):
        """Return parameter2 which is used to adjust effects/pictures/transitions"""
        return self._parameter2

    @property
    def white_value(self):
        return self._white_value

    @property
    def effect_list(self):
        """Return the list of supported effects."""
        return PIXIE_EFFECT_LIST

    @property
    def picture_list(self):
        """Return the list of supported pictures."""
        return PIXIE_PICTURE_LIST

    @property
    def transition_list(self):
        """Return the list of supported pictures."""
        return PIXIE_TRANSITION_LIST

    @property
    def effect(self):
        """Return the current effect."""
        return self._effect

    @property
    def picture(self):
        """Return the current effect."""
        return self._picture

    @property
    def supported_features(self):
        return SUPPORT_PIXIE

    @property
    def supported_color_modes(self):
        return {self._color_mode};

    @property
    def color_mode(self):
        """Return the color mode of the light."""
        return self._color_mode

    @property
    def available(self):
        """Return the availability of the light."""
        return self._available
