#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Python Version 2.7
# tft24-display-startup.py

from __future__ import print_function

PLUGIN_NAME = "tft24-display"
from PIL import ImageFont
from os import path
from spidev import SpiDev
from lib_tft24T import TFT24T
from json import loads as JsonLoad
import RPi.GPIO as GPIO

GPIO.setmode(GPIO.BCM)
GPIO.setwarnings(False)

# =============================================================================
# CONFIGURATION
# =============================================================================
# LCD TFT SCREEN
GPIO_DC = 24
GPIO_RST = 25 # None
GPIO_LED = 12 # None

# Display
displayLandscape = False # True | False

# Colors
color = (200, 70, 0)

# Text configuration
fontFace = None
textSizeHuge = 50

configFile = '/data/configuration/user_interface/' + PLUGIN_NAME + '/config.json'
# =============================================================================
# // END CONFIGURATION
# =============================================================================

### read config
try:
    with open(configFile, 'r') as configFileContent:
        data = configFileContent.read()
        config = JsonLoad(data)

        GPIO_DC = int(config['gpio_dc']['value'])
        GPIO_RST = int(config['gpio_rst']['value'])
        GPIO_LED = int(config['gpio_led']['value'])
        fontFace = str(config['display_fontface']['value'])
        color = tuple(map(int, str(config['color_album']['value']).split(',')))
        debugOutput = bool(config['debugging']['value'])

except Exception as e:
    print("Something went wrong while getting config: " + str(e))
    pass


### Create TFT LCD/TOUCH object, initialize and clear
# If displayLandscape=False or omitted, display defaults to portrait mode
TFT = TFT24T(SpiDev(), GPIO, landscape=displayLandscape)
TFT.initLCD(GPIO_DC, GPIO_RST, GPIO_LED)
TFT.clear()

# config
fontFamily = path.dirname(path.abspath(__file__)) + '/fonts/' + fontFace
fontHuge = ImageFont.truetype(fontFamily, textSizeHuge)

displayWidth = TFT.width
displayHeight = TFT.height

def drawStartupView():
    startupText = "musicbox"
    startupTextDimensions = fontHuge.getsize(startupText)
    centerTextPositionX = (displayWidth / 2) - (startupTextDimensions[0] / 2) # calculate centerX pos based on text width
    centerTextPositionY = (displayHeight / 2) - (startupTextDimensions[1] / 2) - 10 # calculate centerY pos based on text height

    if debugOutput:
        print("disp DIM: " + str(displayWidth) + " - " + str(displayHeight))
        print("text DIM: " + str(startupTextDimensions[0]) + " - " + str(startupTextDimensions[1]))
        print("posi DIM: " + str(centerTextPositionX) + " - " + str(centerTextPositionY))

    # textdirect doesn't work with landscape orientation
    TFT.textdirect((centerTextPositionX, centerTextPositionY), startupText, fontHuge, color)

if __name__ == "__main__":
    drawStartupView()
