"""Pixie LED Controller integration."""

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.entity_registry import async_migrate_entries

from .const import DOMAIN
#from .const import DOMAIN, SERVICE_PTZ, SERVICE_PTZ_PRESET

PLATFORMS = ["light"]

async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up foscam from a config entry."""
    hass.config_entries.async_setup_platforms(entry, PLATFORMS)

    hass.data.setdefault(DOMAIN, {})
    hass.data[DOMAIN][entry.entry_id] = entry.data

    return True


#async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry):
#    """Unload a config entry."""
#    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
#    if unload_ok:
#        hass.data[DOMAIN].pop(entry.entry_id)
#
#        if not hass.data[DOMAIN]:
#            hass.services.async_remove(domain=DOMAIN, service=SERVICE_PTZ)
#            hass.services.async_remove(domain=DOMAIN, service=SERVICE_PTZ_PRESET)
#
#    return unload_ok
