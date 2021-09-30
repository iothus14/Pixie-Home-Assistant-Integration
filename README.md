# Home Assistant Integration for a Pixie LED Controller

This is a custom component to support a Pixie LED controller in Home Assistant.


### Installation

Requires Home Assistant 2021.4.0 or newer.

#### Installation through HACS
Find the Pixie integration in HACS and install it. If you haven't installed HACS, please, go get it at https://hacs.xyz/ and go through the installation and configuration. Restart Home Assistant and install the new integration through Configuration -> Integrations in HA (see the details below).

#### Manual installation
Copy the sub-path `/custom_components/pixie` of this repo into the path /config/custom_components/pixie of your HA installation.


### Configuration
 Every pixie device has its own unique ID which will be used to configure the device in Home Assistant. A Pixie controller has 4 independent hardware channels 
to controll addressable LED strips. Every channel can be configured separately with this integration.
 1. Open "Configuration" -> "Integration" in your Home Assistant instance.
 2. Click the button "+ADD INTEGRATION".
 3. In the window "Set up a new integration" type ***Pixie*** and run the configuration process by clicking on the found item of the list "Pixie LED Controller".
 4. Type the pixie unique ID and select a channel of the device to configure.
 5. Press "Ok". If the input data is correct the integration will create a light entity with a default name `light.pixie_abcdef_0` where `abcdef` is the unique id of the controller. The number at the endd is the channel number.

### Services
 The integration brings a several services which can be also found in "Developer Tools" -> "Services":
 - pixie.set_effect - run an animation effect with parameters.
 - pixie.set_picture - run a static effect with parameters.
 - pixie.turn_on_transition - turn on the LED strip with any supported transition
 - pixie.turn_off_transition - turn off the LED strip with any supported transition

#### pixie.set_effect

 The service `set_effect` can be used in any automation
```
```
