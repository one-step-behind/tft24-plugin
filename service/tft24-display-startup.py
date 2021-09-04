#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Python Version 2.7
# tft24-display-startup.py

PLUGIN_NAME = "tft24-display"

from PIL import ImageFont
from os import path
from spidev import SpiDev
from lib_tft24T import TFT24T
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
textSizeHuge = 50

configFile = '/data/configuration/miscellanea/' + PLUGIN_NAME + '/config.json'
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
        displayLandscape = bool(config['display_landscape']['value'])
        color = tuple(map(int, str(config['color_artist']['value']).split(', ')))
except Exception as e:
    pass


### Create TFT LCD/TOUCH object:
# If displayLandscape=False or omitted, display defaults to portrait mode
TFT = TFT24T(SpiDev(), GPIO, landscape=displayLandscape)

# Initialize display.
TFT.initLCD(GPIO_DC, GPIO_RST, GPIO_LED)

# Get the PIL Draw object to start drawing on the display buffer.
draw = TFT.draw()

currentDir = path.dirname(path.abspath(__file__))
fontFamily = currentDir + '/fonts/' + str(config['display_fontface']['value'])
fontHuge = ImageFont.truetype(fontFamily, textSizeHuge)

def drawStartupView():
    TFT.display()
    startupText = "musicbox"
    startupTextDimensions = fontHuge.getsize(startupText)
    centerTextPositionX = (TFT.width / 2) - (startupTextDimensions[0] / 2) # calculate centerX pos based on text width
    centerTextPositionY = (TFT.height / 2) - (startupTextDimensions[1] / 2) # calculate centerY pos based on text height
    TFT.textdirect((centerTextPositionX, centerTextPositionY), startupText, fontHuge, color)

if __name__ == "__main__":
    drawStartupView()
