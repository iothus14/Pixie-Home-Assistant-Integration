"""Config flow for the Pixie platform."""
import logging

import voluptuous as vol

from homeassistant import config_entries

from .const import (
    DOMAIN,
    CONF_DEVICE_ID,
    CONF_CHANNEL,
    CONF_NAME
    )


class PixieConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow."""

    VERSION = 1

    def __init__(self) -> None:
        """Initialize the config flow."""
        self._errors = {}

    async def async_step_user(self, user_input=None):
        """Step when user initializes a integration."""
        self._errors = {}

        if user_input is not None:
            device_id = user_input[CONF_DEVICE_ID]
            channel = user_input[CONF_CHANNEL]
            name_default = f"pixie_{device_id}_{channel}"
            name = user_input.get(CONF_NAME, name_default)
            await self.async_set_unique_id(f"pixie_{device_id}_{channel}")
            self._abort_if_unique_id_configured()

            valid_chars = ['0', '1', '2', '3', '4', '5', '6', '7', '8', '9', 'A', 'a', 'B', 'b', 'C', 'c', 'D', 'd', 'E', 'e', 'F', 'f']
            matched_list = [characters in valid_chars for characters in device_id]
            all_chars_valid = all(matched_list)

            if len(device_id) == 6 and channel in [0, 1, 2, 3] and all_chars_valid:
                return self.async_create_entry(
                    title=name,
                    data={CONF_DEVICE_ID: device_id, CONF_CHANNEL: channel, CONF_NAME: name},
                )
            elif len(device_id) != 6 or all_chars_valid == False :
                self._errors["base"] = "wrong_device_id"
            elif channel not in [0, 1, 2, 3]:
                self._errors["base"] = "wrong_channel"

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema(
                {
                    vol.Required(CONF_DEVICE_ID): str,
                    vol.Required(CONF_CHANNEL, default=0): vol.All( vol.Coerce(int), vol.In([0, 1, 2, 3] ) ),
                }
            ),
            errors=self._errors,
        )

    async def async_step_import(self, user_input=None):
        """Import a config entry."""
        return await self.async_step_user(user_input)

