"""Platform for light integration."""
import logging

import json
import voluptuous as vol
import random

from homeassistant.helpers import config_validation as cv, entity_platform, service
from homeassistant.const import CONF_ICON, CONF_NAME
from homeassistant.core import HomeAssistant, HomeAssistantError, callback
from homeassistant.config_entries import ConfigEntry
from homeassistant.config_entries import SOURCE_IMPORT
from homeassistant.components import mqtt
from homeassistant.const import (
    ATTR_IDENTIFIERS,
    ATTR_MANUFACTURER,
    ATTR_MODEL,
    ATTR_NAME,
    ATTR_SW_VERSION,
)
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
    SERVICE_SET_PICTURE,
    SERVICE_SET_EFFECT,
    SERVICE_SET_RANDOM_EFFECT,
    SERVICE_TURN_ON_TRANSITION,
    SERVICE_TURN_OFF_TRANSITION,
    SERVICE_CHECK_OTA,
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
    """Add a pixie light from a config entry."""

    c_key = f"coordinator_{config_entry.entry_id}"
    coordinator = hass.data[DOMAIN][c_key]
    light = PixieLight(coordinator)

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
        SERVICE_SET_RANDOM_EFFECT,
        {
            vol.Optional(PIXIE_ATTR_PARAMETER1): vol.All( vol.Coerce(int), vol.Range(min=0, max=255) ),
            vol.Optional(PIXIE_ATTR_PARAMETER2): vol.All( vol.Coerce(int), vol.Range(min=0, max=255) ),
            vol.Optional(PIXIE_ATTR_BRIGHTNESS): vol.All( vol.Coerce(int), vol.Range(min=0, max=255) ),
            vol.Exclusive(ATTR_RGB_COLOR, ATTR_RGB_COLOR): vol.All(
                vol.ExactSequence((cv.byte,) * 3), vol.Coerce(tuple)
            ),
        },
        "async_set_random_effect",
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
    
    platform.async_register_entity_service(
        SERVICE_CHECK_OTA,
        { },
        "async_check_ota",
    )
    
    # Add devices
    async_add_entities([light], True)


class PixieLight(LightEntity):
    """Representation of a Pixie Light."""
    _attr_icon = "mdi:led-strip-variant"

    def __init__(self, coordinator):
        """Initialize a PixieLight."""
        self._coordinator = coordinator
        self._device_id = coordinator.device_id()
        self._channel = coordinator.channel()
        self._attr_unique_id = f"pixie_{self._device_id}_{self._channel}"
        self._attr_name = f"Pixie {self._device_id} {self._channel}"

        self.qos = 0
        self.retain = False


    def state_update_callback(self):
        self.async_write_ha_state()

    async def async_added_to_hass(self):
        """Subscribe to MQTT events."""
        self._coordinator.light_state_callback(self.state_update_callback)
        self._coordinator.attr_callback(self.state_update_callback)
        await self._coordinator.async_mqtt_handler()

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
            message["effect"] = kwargs[PIXIE_ATTR_EFFECT].strip('"').strip("'")
        elif "picture" in kwargs:
            message["picture"] = kwargs["picture"].strip('"').strip("'")
        elif "transition" in kwargs:
            message["transition"] = kwargs["transition"]
            if "transition_name" in kwargs:
                message["transition_name"] = kwargs["transition_name"].strip('"').strip("'")

        if ATTR_RGB_COLOR in kwargs:
            rgb = kwargs[ATTR_RGB_COLOR]
            message["color"] = {"r": rgb[0], "g": rgb[1], "b": rgb[2]}

        if ATTR_RGBW_COLOR in kwargs:
            rgb = kwargs[ATTR_RGBW_COLOR]
            message["color"] = {"r": rgb[0], "g": rgb[1], "b": rgb[2], "w": rgb[3]}

        await self._coordinator.publish_command(json.dumps(message), self.qos, self.retain)

    async def async_turn_off(self, **kwargs):
        """Instruct the light to turn off."""
        message = {"state": "OFF"}
        await self._coordinator.publish_command(json.dumps(message), self.qos, self.retain)

    async def async_set_effect(self, **kwargs):
        """Set an effect of a Pixie light."""
        message = {"state": "ON"}
    
        if PIXIE_ATTR_EFFECT not in kwargs:
            _LOGGER.warning("[%s] An effect must be specified to run the service pixie.set_effect", self._device_id )
            return

        message["effect"] = kwargs[PIXIE_ATTR_EFFECT].strip('"').strip("'")

        if message["effect"] not in PIXIE_EFFECT_LIST:
            _LOGGER.warning("[%s] The specified effect %s is not supported. The effect is ignored.", self._device_id,  message["effect"])
            return

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

        await self._coordinator.publish_command(json.dumps(message), self.qos, self.retain)

    async def async_set_random_effect(self, **kwargs):
        """Set a random effect of a Pixie light."""
        message = {"state": "ON"}
    
        i = min( (len(PIXIE_EFFECT_LIST) - 1), round( random.random() * len(PIXIE_EFFECT_LIST) ) )
        message["effect"] = PIXIE_EFFECT_LIST[ i ]

        if PIXIE_ATTR_PARAMETER1 in kwargs:
            message["parameter1"] = min( kwargs[PIXIE_ATTR_PARAMETER1], 255 )
        else:
            message["parameter1"] = round( random.random() * 255 )

        if PIXIE_ATTR_PARAMETER2 in kwargs:
            message["parameter2"] = min( kwargs[PIXIE_ATTR_PARAMETER2], 255 )
        else:
            message["parameter2"] = round( random.random() * 255 )

        if ATTR_RGBW_COLOR in kwargs:
            rgb = kwargs[ATTR_RGBW_COLOR]
            message["color"] = {"r": rgb[0], "g": rgb[1], "b": rgb[2], "w": rgb[3]}
        else:
            message["color"] = { "r":round( random.random() * 255 ), "g":round( random.random() * 255 ), "b":round( random.random() * 255 ), "w":round( random.random() * 255 ) }

        if ATTR_RGB_COLOR in kwargs:
            rgb = kwargs[ATTR_RGB_COLOR]
            message["color"] = {"r": rgb[0], "g": rgb[1], "b": rgb[2]}
        else:
            message["color"] = { "r":round( random.random() * 255 ), "g":round( random.random() * 255 ), "b":round( random.random() * 255 ) }

        if PIXIE_ATTR_BRIGHTNESS in kwargs:
            message["brightness"] = min( max(1, kwargs[PIXIE_ATTR_BRIGHTNESS]), 255 )

        await self._coordinator.publish_command(json.dumps(message), self.qos, self.retain)

    async def async_set_picture(self, **kwargs):
        """Set a picture of a Pixie light."""
        message = {"state": "ON"}

        message["picture"] = kwargs[PIXIE_ATTR_PICTURE].strip('"').strip("'")

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

        await self._coordinator.publish_command(json.dumps(message), self.qos, self.retain)

    async def async_turn_on_transition(self, **kwargs):
        """Turn a Pixie light on with a transition."""

        message = {"state": "ON"}
        message["transition_name"] = kwargs[PIXIE_ATTR_TRANSITION_NAME].strip('"').strip("'")

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

        await self._coordinator.publish_command(json.dumps(message), self.qos, self.retain)


    async def async_turn_off_transition(self, **kwargs):
        """Turn a Pixie light off with a transition."""

        message = {"state": "OFF"}
        message["transition_name"] = kwargs[PIXIE_ATTR_TRANSITION_NAME].strip('"').strip("'")

        message["transition"] = kwargs[PIXIE_ATTR_TRANSITION]

        if PIXIE_ATTR_PARAMETER1 in kwargs:
            message["parameter1"] = min( kwargs[PIXIE_ATTR_PARAMETER1], 255 )

        if PIXIE_ATTR_PARAMETER2 in kwargs:
            message["parameter2"] = min( kwargs[PIXIE_ATTR_PARAMETER2], 255 )

        await self._coordinator.publish_command(json.dumps(message), self.qos, self.retain)


    async def async_check_ota(self, **kwargs):
        """Check available OTA update for a Pixie device."""
        await self._coordinator.ota_check()


    @property
    def brightness(self):
        """Return brightness"""
        return self._coordinator.brightness()

    @property
    def is_on(self):
        """Return true if light is on."""
        return self._coordinator.state()

    @property
    def rgb_color(self):
        """Return the hs color value."""
        return self._coordinator.rgb()

    @property
    def parameter1(self):
        """Return parameter1 which is used to adjust effects/pictures/transitions"""
        return self._coordinator.parameter1()

    @property
    def parameter2(self):
        """Return parameter2 which is used to adjust effects/pictures/transitions"""
        return self._coordinator.parameter2()

    @property
    def white_value(self):
        return self._coordinator.white_value()

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
        return self._coordinator.effect()

    @property
    def picture(self):
        """Return the current effect."""
        return self._coordinator.picture()

    @property
    def supported_features(self):
        return SUPPORT_PIXIE

    @property
    def supported_color_modes(self):
        return { self._coordinator.color_mode() };

    @property
    def color_mode(self):
        """Return the color mode of the light."""
        return self._coordinator.color_mode()

    @property
    def available(self):
        """Return the availability of the light."""
        return self._coordinator.available()

    @property
    def extra_state_attributes(self):
        """Return the device specific state attributes."""
        attributes = {
            "url": self._coordinator.url(),
            "ip_addr": self._coordinator.ip_addr(),
        }

        if self._coordinator.state():
            attributes["parameter1"] = self._coordinator.parameter1()
            attributes["parameter2"] = self._coordinator.parameter2()

        if self._coordinator.state() and self._coordinator.picture() != "" and self._coordinator.picture() != None:
            attributes["picture"] = self._coordinator.picture()

        return attributes

    @property
    def device_info(self):
        return {
            ATTR_IDENTIFIERS: {(DOMAIN, self._device_id)},
            ATTR_NAME: "Pixie",
            ATTR_MANUFACTURER: "iothus14",
            ATTR_MODEL: "Pixie",
            ATTR_SW_VERSION: self._coordinator.firmware_version(),
            "configuration_url": f"http://pixie-{self._coordinator.device_id()}.local"
        }

