"""Pixie LED Controller integration."""

import logging

from homeassistant.components.light import DOMAIN as LIGHT_DOMAIN
from homeassistant.components.select import DOMAIN as SELECT_DOMAIN
from homeassistant.components.sensor import DOMAIN as SENSOR_DOMAIN

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.entity_registry import async_migrate_entries
from homeassistant.components import mqtt

from .coordinator import PixieCoordinator
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
    SERVICE_TURN_ON_TRANSITION,
    SERVICE_TURN_OFF_TRANSITION,
    PIXIE_EFFECT_LIST,
    PIXIE_PICTURE_LIST,
    PIXIE_TRANSITION_LIST,
)

PLATFORMS = (LIGHT_DOMAIN, SELECT_DOMAIN, SENSOR_DOMAIN)

_LOGGER = logging.getLogger(__name__)

async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up a pixie light from a config entry."""
    hass.config_entries.async_setup_platforms(entry, PLATFORMS)

    _LOGGER.info("Set up entry: entry_id: %s;", entry.entry_id)

    hass.data.setdefault(DOMAIN, {})
    hass.data[DOMAIN][entry.entry_id] = entry.data

    coordinator = PixieCoordinator(hass, entry)
    c_key = f"coordinator_{entry.entry_id}"
    hass.data[DOMAIN][c_key] = coordinator

    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry):
    """Unload a config entry."""
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unload_ok:
        hass.data[DOMAIN].pop(entry.entry_id)
        c_key = f"coordinator_{entry.entry_id}"
        hass.data[DOMAIN].pop(c_key)

        if not hass.data[DOMAIN]:
            hass.services.async_remove(domain=DOMAIN, service=SERVICE_SET_EFFECT)
            hass.services.async_remove(domain=DOMAIN, service=SERVICE_SET_PICTURE)
            hass.services.async_remove(domain=DOMAIN, service=SERVICE_TURN_ON_TRANSITION)
            hass.services.async_remove(domain=DOMAIN, service=SERVICE_TURN_OFF_TRANSITION)

    return unload_ok

