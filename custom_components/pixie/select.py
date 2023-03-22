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

    ##c_key = f"coordinator_{config_entry.entry_id}"
    ##coordinator = hass.data[DOMAIN][c_key]
    coordinator = hass.data[DOMAIN][config_entry.entry_id]

    select_picture = PixiePictureSelect(coordinator)
    select_effect = PixieEffectSelect(coordinator)

    # Add devices
    async_add_entities([select_picture, select_effect], True)


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
        self._coordinator.picture_select_callback(self.state_update_callback)
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
        self._coordinator.effect_select_callback(self.state_update_callback)
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


