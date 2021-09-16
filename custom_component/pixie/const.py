""" Pixie constants """

DOMAIN = "pixie"

CONF_CHANNEL = "channel"
        
PIXIE_ATTR_STATE = "state"
PIXIE_ATTR_PICTURE = "picture"
PIXIE_ATTR_TRANSITION_NAME = "transition_name"
PIXIE_ATTR_TRANSITION = "transition"
PIXIE_ATTR_EFFECT = "effect"
PIXIE_ATTR_PARAMETER1 = "parameter1"
PIXIE_ATTR_PARAMETER2 = "parameter2"
PIXIE_ATTR_BRIGHTNESS = "brightness"

# Services
SERVICE_SET_EFFECT = "set_effect"
SERVICE_SET_PICTURE = "set_picture"
SERVICE_TURN_ON_TRANSITION = "turn_on_transition"
SERVICE_TURN_OFF_TRANSITION = "turn_off_transition"


PIXIE_EFFECT_LIST = [
    "ColorLoop",
    "Rainbow",
    "DoubleRainbow",
    "RainbowChase",
    "RunningLights",
    "TwoColors",
    "ThreeColors",
    "ColorPeaks",
    "Sparks",
    "Comet",
    "CometWithParticles",
    "RandomComets",
    "ColorFadings",
    "Sparkles",
    "SparklesOnColor",
    "SparklesOnColorLoop",
    "RainbowWipesUp",
    "RainbowWipesDown",
    "ColorWipes",
    "Chain",
    "BrokenLamp",
    "FastPixels",
    "BrightStripes",
    "DarkStripes",
    "MulticolorBurst",
    "OneColorBurst",
    "RandomColorBurst",
    "ColorPendulum",
    "RainbowScan",
    "DoubleRainbowScan",
    "RandomColor",
    "ChaseDown",
    "ChaseUp",
    "Chase2Down",
    "Chase2Up",
    "SporadicMeteors",
    "Dots",
    "RGBScanner",
    "Twinkles",
    "PixelQueue",
    "PeriodicMeteorsUp",
    "PeriodicMeteorsDown",
    "Flicker",
    "MultiplePixelQueues",
    "MultipleColorPixelQueues",
    "Fireworks",
    "Strobe",
    "BigSparks",
    "RunAndLightUp",
    "Moths",
    "Breathe",
    "Pixie",
    "Neutrinos",
    "Emitter",
    "BlackHole",
    "ColorRunsUp",
    "ColorRunsDown",
    "LightBars",
    "Fireworks2",
    "Paintbrush",
    "Lightning",
    "DarkSparklesOnColor",
    "Noise",
    "Particles",
    "Curtains",
    "Scanner",
]

PIXIE_PICTURE_LIST = [
    "Rainbow",
    "Rainbow2",
    "Rainbow3",
    "Rainbow4",
    "Dots",
    "Stripes",
    "ProgressBar",
    "Noise",
]

PIXIE_TRANSITION_LIST = [
    "Fade",
    "Unfold",
    "Fold",
    "Unroll",
    "Roll",
    "Dots",
    "FadeOut",
    "SinIn",
    "SinOut",
    "Paintbrush",
    "Curtains",
]

