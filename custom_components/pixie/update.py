"""Support for Pixie updates."""
from __future__ import annotations

from homeassistant.components.update import (
    UpdateDeviceClass,
    UpdateEntity,
    UpdateEntityFeature,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DOMAIN

import logging

_LOGGER = logging.getLogger(__name__)

async def async_setup_entry( hass: HomeAssistant, config_entry: ConfigEntry, async_add_entities: AddEntitiesCallback ):
    """Set up Pixie sensors"""

    c_key = f"coordinator_{config_entry.entry_id}"
    coordinator = hass.data[DOMAIN][c_key]
    pixie_update_entity = PixieUpdateEntity(coordinator)

    async_add_entities([pixie_update_entity])


class PixieUpdateEntity(UpdateEntity):
    """Defines a Pixie update entity."""

    _attr_device_class = UpdateDeviceClass.FIRMWARE
    _attr_supported_features = (
        UpdateEntityFeature.INSTALL | UpdateEntityFeature.SPECIFIC_VERSION | UpdateEntityFeature.PROGRESS
    )
    _attr_title = "Pixie"

    def __init__(self, coordinator) -> None:
        """Initialize the update entity."""
        self._device_id = coordinator.device_id()
        self._channel = coordinator.channel()
        self._coordinator = coordinator
        self._attr_name = f"Pixie {self._device_id} Firmware Update"
        self._attr_unique_id = f"pixie_{self._device_id}_firmware_update"

    @property
    def installed_version(self) -> str | None:
        """Version currently installed and in use."""
        return self._coordinator.firmware_version()


    @property
    def latest_version(self) -> str | None:
        """Latest version available for install."""
        return self._coordinator.available_version()


    @property
    def release_url(self) -> str | None:
        """URL to the full release notes of the latest version available."""
        return "https://github.com/iothus14/Pixie/releases/"


    async def async_install(self, version: str | None, backup: bool, **kwargs: Any) -> None:
        """Install an update."""
        await self._coordinator.ota_perform()


    async def async_added_to_hass(self):
        """Subscribe to MQTT events."""
        self._coordinator.ota_callback(self.state_update_callback)
        await self._coordinator.async_mqtt_handler()


    def state_update_callback(self):
        self._attr_in_progress = self._coordinator.ota_in_progress()
        self.async_write_ha_state()

