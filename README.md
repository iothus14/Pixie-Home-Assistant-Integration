# Home Assistant Integration for a Pixie LED Controller

This is a custom component to support a Pixie LED controller in Home Assistant.


### Installation

Requires Home Assistant 2021.4.0 or newer.

#### Installation through HACS
Find the Pixie integration in HACS and install it. If you haven't installed HACS, please, go get it at https://hacs.xyz/ and go through the installation and configuration. Restart Home Assistant and install the new integration through Configuration -> Integrations in HA (see the details below).

#### Manual installation
Copy the sub-path `/custom_components/pixie` of this repo into the path /config/custom_components/pixie of your HA installation.
The next step is to create a pixie entity in `configuration.yaml`. 

### Configuration

Every pixie device has its own unique ID which will be used to configure the device in Home Assistant. A Pixie controller has 4 independent hardware channels 
to controll addressable LED strips. Every channel can be configured separately.

#### Manual configuration
A pixie configuration can be added manually to the `configuration.yaml` file like this:

```
light:
  - platform: pixie
    name: "My Pixie Light"
    device_id: abcdef
    channel: 0
```
Configuration variables:
| Variable | Type | Optional | Description |
|----------|------|----------|-------------|
| **platform** | *pixie* | No | Always must be pixie |
| **name** | *String* | Yes | A friendly name of the light |
| **device_id** | *String* | No | A unique id of the pixie device |
| **channel** | *Number* | No | A number of channel which this configuration describes. Valid values are 0, 1, 2, 3 |

#### UI configuration

This describes how to configure a pixie device vie Home Assistant Integration:

 1. Open "Configuration" -> "Integration" in your Home Assistant instance.
 2. Click the button "+ADD INTEGRATION".
 3. In the window "Set up a new integration" type ***Pixie*** and run the configuration process by clicking on the found item of the list "Pixie LED Controller".
 4. Type the pixie unique ID and select a channel of the device to configure.
 5. Press "Ok". If the input data is correct the integration will create a light entity with a default name `light.pixie_abcdef_0` where `abcdef` is the unique id of the controller. The number at the endd is the channel number.

### Services
 The integration brings a several services which can be also found in "Developer Tools" -> "Services":
 - `pixie.set_effect` - run an animation effect with parameters.
 - `pixie.set_picture` - run a static effect with parameters.
 - `pixie.turn_on_transition` - turn on the LED strip with any supported transition
 - `pixie.turn_off_transition` - turn off the LED strip with any supported transition

All services can  be used in any automation or script. Please check the service details below.


### Service pixie.set_effect

This service runs an animation effect on the LED strip.

|Service data attribute    | Optional  | Description                        |
|--------------------------|-----------|------------------------------------|
| **entity_id**            | No        | Entity Id of a pixie device.        |
| **effect**               | No        | One of the supported effects. Please check the documentation for the supported effects. |
| **parameter1**           | Yes       | Valid value is in the range 0..255. It usually adjusts the speed of the animation effect. |
| **parameter2**           | Yes       | Valid value is in the range 0..255. It usually adjusts the intensity of the animation effect. |
| **color**                | Yes       | A list containing three integers between 0 and 255 representing the RGB color if the effect supports a color as an input parameter. |
| **brightness**           | Yes       | The brightness value to set (1..255). |

Here is an example to run the "Comet" animation effect.

```
service: pixie.set_effect
data:
  entity_id: light.pixie_abcdef_0
  effect: "Comet"
  parameter1: 128
  parameter2: 200
  color: [255,0,0]
  brightness: 200
```


### Service pixie.set_picture

This service runs a static effect on the LED strip.

|Service data attribute    | Optional  | Description                        |
|--------------------------|-----------|------------------------------------|
| **entity_id**            | No        | Entity Id of a pixie device.        |
| **picture**              | No        | One of the supported static effects. Please check the documentation for the supported effects. |
| **parameter1**           | Yes       | Valid value is in the range 0..255 if parameter1 is applicable to the picture. Otherwise it will be ignored.  |
| **parameter2**           | Yes       | Valid value is in the range 0..255 if parameter2 is applicable to the picture. Otherwise it will be ignored. |
| **color**                | Yes       | A list containing three integers between 0 and 255 representing the RGB color if the effect supports a color as an input parameter. |
| **brightness**           | Yes       | The brightness value to set (1..255). |

This example show how to display a static effect. In this case it runs "Rainbow" on the LED strip.
```
service: pixie.set_pixture
data:
  entity_id: light.pixie_abcdef_0
  picture: "Rainbow"
  parameter1: 200
  parameter2: 120
  brightness: 200
```


### Service pixie.turn_on_transition

This service is very similar to `light.turn_on` which can be also used with a pixie device but `pixie.turn_on_transition` has extra parameters allowing to turn on the LED strip with the supported transitions and parameters to adjust them.

|Service data attribute    | Optional  | Description                        |
|--------------------------|-----------|------------------------------------|
| **entity_id**            | No        | Entity Id of a pixie device.        |
| **transition_name**      | No        | One of the supported transition effects. Please check the documentation for the supported effects. |
| **transition**           | No        | Time is seconds for how long the transition effect will last |
| **parameter1**           | Yes       | Valid value is in the range 0..255 if parameter1 is applicable to the picture. Otherwise it will be ignored.  |
| **parameter2**           | Yes       | Valid value is in the range 0..255 if parameter2 is applicable to the picture. Otherwise it will be ignored. |
| **color**                | No        | A list containing three integers between 0 and 255 representing the RGB color |
| **brightness**           | Yes       | The brightness value to set (1..255). |

Here is an example to turn on the light `light.pixie_abcdef_0` with the RGB color [128, 255, 0] for 30 seconds with a transition effect "SinIn"

```
service: pixie.turn_on_transition
data:
  entity_id: light.pixie_abcdef_0
  transition_name: "SinIn"
  transition: 30
  brightness: 200
  color: [128, 255, 0]
```

### Service pixie.turn_off_transition

This service is very similar to `light.turn_off` which can be also used with a pixie device but `pixie.turn_off_transition` has extra parameters allowing to turn off the LED strip with the supported transitions and parameters to adjust them.

|Service data attribute    | Optional  | Description                        |
|--------------------------|-----------|------------------------------------|
| **entity_id**            | No        | Entity Id of a pixie device.        |
| **transition_name**      | No        | One of the supported transition effects. Please check the documentation for the supported effects. |
| **transition**           | No        | Time is seconds for how long the transition effect will last |
| **parameter1**           | Yes       | Valid value is in the range 0..255 if parameter1 is applicable to the transition effect. Otherwise it will be ignored.  |
| **parameter2**           | Yes       | Valid value is in the range 0..255 if parameter2 is applicable to the transition effect. Otherwise it will be ignored. |


Here is an example to turn off the light `light.pixie_abcdef_0` for 30 seconds with a transition effect "SinOut"

```
service: pixie.turn_off_transition
data:
  entity_id: light.pixie_abcdef_0
  transition_name: "SinOut"
  transition: 5
```

Please check the documentation regarding all supported animations, pictures and transitions.
