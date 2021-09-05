#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Python Version 2.7
# tft24-display.py
# This is a ILI9341 driven LCD display.

PLUGIN_NAME = "tft24-display"

from PIL import Image, ImageDraw, ImageFont
from StringIO import StringIO
from os import system, path
from time import sleep
from math import ceil
from gpiozero import CPUTemperature
from lib_tft24T import TFT24T
from sys import argv, exit
from subprocess import check_output
from requests import get as RequestGet
from json import loads as JsonLoad
from signal import signal, SIGTERM
from threading import Thread as ThreadThread, Event as ThreadEvent
from struct import pack, unpack
from smbus import SMBus
from netifaces import gateways, AF_INET, ifaddresses
from spidev import SpiDev
import RPi.GPIO as GPIO

GPIO.setmode(GPIO.BCM)
GPIO.setwarnings(False)

# =============================================================================
# CONFIGURATION
# =============================================================================

# Display
displayMargin = 5 # px

# Text configuration
textSizeSmall = 11
lineHeightSmall = 12
textSizeNormal = 14
lineHeightNormal = 15
textSizeBig = 18
lineHeightBig = 20
textSizeHuge = 40
lineGap = 8

# anything else
sleepDelayPlay = 2 # in seconds
sleepDelayInitial = 5 # in seconds
sleepDelayShutdown = 60 # in seconds
seekbarHeight = 5 # should be an odd number
maxWidthSourceIcon = 25
logfile = '/home/volumio/log/' + PLUGIN_NAME + '.log'
configFile = '/data/configuration/user_interface/' + PLUGIN_NAME + '/config.json'

# =============================================================================
# // END CONFIGURATION
# =============================================================================

localhost = 'http://localhost:3000'
currentDir = path.dirname(path.abspath(__file__))

# Define some global variables
status = ''
service = ''
volatile = True
actVolume = 0
volumioStatus = {}
lastVolumioStatus = {}
textTopSongDetails = 100
textVolume = 0
textStatus = ''
textTime = ''
textArtist = ''
textTitle = ''
textAlbum = ''
lastNetwork = ''
iface = None
ipaddress = None
TFT = None
draw = None
fontSmall = None
fontNormal = None
fontBig = None
fontHuge = None

# =============================================================================
# The follwing variables will be overwritten with Volumio Display plugin config
# =============================================================================
# LCD TFT SCREEN: fallback GPIOs and orientation
GPIO_DC = 24
GPIO_RST = 25 # None
GPIO_LED = 12 # None
displayLandscape = False # True | False
debugOutput = False # True | False

# Album image
coverFullscreen = False # True | False
coverSize = 80 # only used if albumImageFull is False
coverTransparency = 0.3 # only used if albumImageFull is True
# Colors
colorAlbum = (180, 110, 6) #(84, 198, 136)
colorArtist = (180, 180, 180)
colorSongtitle = (255, 255, 255) #(220, 160, 25)
colorStatus = (180, 180, 180)
colorTime = (255, 255, 255)
colorTimebar = (180, 110, 6)

# Show UPS info
showUpsInfo = False
# =============================================================================

# UPS Device
ups_device_address = 0x36 # UPS HAT Pro: 0x62; X750: 0x36
ups_i2c_port = 1  # 0 = /dev/i2c-0 (port I2C0), 1 = /dev/i2c-1 (port I2C1)
ups_bus = SMBus(ups_i2c_port)
upsCapacityInt = 0
lastUpsCapacityInt = 0

# Some precalculations
textTopSongDetailsAlbum = textTopSongDetails
textTopSongDetailsArtist = textTopSongDetailsAlbum + (textSizeNormal * 2) + 2
textTopSongDetailsTitle = textTopSongDetailsArtist + (textSizeNormal * 2) + 2

def initDisplay():
    global debugOutput, draw, TFT, GPIO_DC, GPIO_RST, GPIO_LED, showUpsInfo, displayLandscape, coverFullscreen, coverSize
    global coverTransparency, colorAlbum, colorArtist, colorSongtitle, colorStatus, colorTime, colorTimebar

    # read config from within plugins file
    try:
        with open(configFile, 'r') as configFileContent:
            data = configFileContent.read()
            config = JsonLoad(data)

            GPIO_DC = int(config['gpio_dc']['value'])
            GPIO_RST = int(config['gpio_rst']['value'])
            GPIO_LED = int(config['gpio_led']['value'])
            showUpsInfo = bool(config['ups']['value'])
            debugOutput = bool(config['debugging']['value'])

            setFonts(str(config['display_fontface']['value']))
            displayLandscape = bool(config['display_landscape']['value'])
            coverFullscreen = bool(config['cover_fullscreen']['value'])
            coverSize = int(config['cover_width']['value'])
            coverTransparency = float(config['cover_transparency']['value'])/100

            colorAlbum = tuple(map(int, str(config['color_album']['value']).split(',')))
            colorArtist = tuple(map(int, str(config['color_artist']['value']).split(',')))
            colorSongtitle = tuple(map(int, str(config['color_songtitle']['value']).split(',')))
            colorStatus = tuple(map(int, str(config['color_status']['value']).split(',')))
            colorTime = tuple(map(int, str(config['color_time']['value']).split(',')))
            colorTimebar = tuple(map(int, str(config['color_timebar']['value']).split(',')))

        debug("Initialized TFT settings")
        debug("displayLandscape", displayLandscape)
        debug("coverFullscreen", coverFullscreen)
        debug("coverSize", coverSize)
        debug("coverTransparency", coverTransparency)
        debug("colorAlbum", colorAlbum)

    except Exception as e:
        debug("Something went wrong while getting config: " + str(e))
        pass
    
    ### Create TFT LCD/TOUCH object
    # If displayLandscape=False or omitted, display defaults to portrait mode
    TFT = TFT24T(SpiDev(), GPIO, landscape=displayLandscape)

    # Initialize display
    TFT.initLCD(GPIO_DC, GPIO_RST, GPIO_LED)
    TFT.clear()

    # Get the PIL Draw object to start drawing on the display buffer.
    draw = TFT.draw()

    # Load and draw background image
    if TFT.is_landscape:
        TFT.load_wallpaper(currentDir + '/img/volumio_bg_horizontal.png')
    else:
        TFT.load_wallpaper(currentDir + '/img/volumio_bg_portrait.png')

# Clean part of screen
def cleanPart(x1, y1, x2, y2):
    if debugOutput:
        draw.rectangle((x1, y1, x2, y2), outline=255, fill=100) # with debug background
    else:
        draw.rectangle((x1, y1, x2, y2), outline=0, fill=0)

def setFonts(displayFontface):
    global fontSmall, fontNormal, fontBig, fontHuge

    fontFamily = currentDir + '/fonts/' + displayFontface
    fontSmall = ImageFont.truetype(fontFamily, textSizeSmall)
    fontNormal = ImageFont.truetype(fontFamily, textSizeNormal)
    fontBig = ImageFont.truetype(fontFamily, textSizeBig)
    fontHuge = ImageFont.truetype(fontFamily, textSizeHuge)

def getNetworkIp():
    # https://stackoverflow.com/questions/55612912/how-to-find-ip-address-of-current-connection-lan-or-wifi-using-python
    global iface, ipaddress

    networkGateways = gateways()

    if networkGateways and networkGateways['default']:
        iface = networkGateways['default'][AF_INET][1]
        ipaddress = ifaddresses(iface)[AF_INET][0]['addr']
        debug('NET', iface, ipaddress)
    else:
        iface = 'None'
        ipaddress = 'unknown'

class ShutdownView():
    def __init__(self):
        debug('=== SHUTDOWN VIEW')

        TFT.clear()
        cleanPart(0, 0, TFT.height, TFT.width -1)
        shutdownText = "Goodbye!"
        shutdownTextDimensions = fontHuge.getsize(shutdownText)
        centerTextPositionX = (TFT.width / 2) - (shutdownTextDimensions[0] / 2) # calculate centerX pos based on text width
        centerTextPositionY = (TFT.height / 2) - (shutdownTextDimensions[1] / 2) # calculate centerY pos based on text width
        TFT.textdirect((centerTextPositionX, centerTextPositionY), shutdownText, fontHuge, colorArtist)

def prepareAlbumArt():
    """Album cover"""
    albumImageUrl = None
    albumArtResponse = None
    albumIO = None

    debug('=== ALBUM ART')
    
    if volumioStatus.get('albumart') and lastVolumioStatus.get('albumart') != volumioStatus.get('albumart'):
        albumImageUrl = str(volumioStatus.get('albumart'))
        debug('albumImageUrl', albumImageUrl)

        if albumImageUrl:
            if not albumImageUrl.startswith('http'):
                albumImageUrl = localhost + albumImageUrl

            albumArtResponse = RequestGet(albumImageUrl) # , stream=True)

        if albumArtResponse:
            debug('albumArtResponse content', albumArtResponse)
            albumIO = StringIO(albumArtResponse.content)
        else:
            # fallback image
            albumIO = currentDir + '/img/albumart.jpg'
            

        if albumIO:
            debug('reDRAW album image')

            if displayLandscape:
                #cleanPart(0, textPosTop, albumImageWidth, albumImageWidth + textSizeSmall)
                draw.pasteimageresized(albumIO, (TFT.height - coverSize, 0), (coverSize, coverSize))
            else:
                if coverFullscreen:
                    # Big album cover
                    draw.pasteimageresized(albumIO, (0, TFT.height - TFT.width), (TFT.width, TFT.width), coverTransparency)
                else:
                    # Small album cover
                    cleanPart(0, TFT.height - coverSize, coverSize, TFT.height)
                    draw.pasteimageresized(albumIO, (0, TFT.height - coverSize), (coverSize, coverSize))

def prepareTime(barPosition, textPosition):
    """Time elapsed / Time duration & visual bar"""
    # TODO: THIS IS SOMEHOW BULLSHIT and makes no real sense yet, has to be re-thougt

    debug('=== TIME')

    textPosTop = textPosition[1]
    trackLength = 0
    trackPos = 0
    pixelPos = 0
    barWidth = 240 if displayLandscape else 160
    barHalf = barWidth / 2

    # clean timebar for redraw only if track changed ("artist" and "title")
    # OR "seek" is smaller than before / otherwise makes no senese to clean it
    if (
        volumioStatus.get('service') != 'webradio' 
        and (
            volumioStatus.get('artist') != lastVolumioStatus.get('artist') 
            and volumioStatus.get('title') != lastVolumioStatus.get('title')
        ) 
        or (
            volumioStatus.get('seek') 
            and lastVolumioStatus.get('seek') 
            and int(volumioStatus.get('seek')) < int(lastVolumioStatus.get('seek'))
        )
    ):
        cleanPart(0, barPosition - (seekbarHeight / 2), barWidth, barPosition + (seekbarHeight / 2))
    elif volumioStatus.get('service') == 'webradio' and lastVolumioStatus.get('service') != 'webradio':
        # clean time text part...
        cleanPart(0, textPosTop, barWidth, textPosTop + textSizeSmall)
        # ...and draw thick full position line because it's a stream
        draw.line((0, barPosition, pixelPos, barPosition), fill=colorTimebar, width=seekbarHeight)

    # calculate and redraw timebar and time text if not webradio stream
    if volumioStatus.get('service') != 'webradio':
        if volumioStatus.get('duration') and volumioStatus.get('seek'):
            trackLength = int(volumioStatus.get('duration'))
            trackPos = int(volumioStatus.get('seek')) / 1000
            tmpPerc = 100 * trackPos / trackLength # calculate percent of current track position
            pixelPos = ceil(barWidth * tmpPerc / 100) # calculate absolute pixel in conjunction of display width
            debug("bar values:", trackPos, trackLength, tmpPerc, pixelPos)

            # draw timebar
            # x min, y min, x max, y max
            draw.line((0, barPosition, barWidth, barPosition), fill=colorTimebar, width=1) # thin full line
            draw.line((0, barPosition, pixelPos, barPosition), fill=colorTimebar, width=seekbarHeight) # thick current position line

            # seek / current song position
            if volumioStatus.get('seek') != lastVolumioStatus.get('seek'):
                m1, s1 = divmod(trackPos, 60)
                h1, m1 = divmod(m1, 60)

                if trackLength >= 3600:
                    textTime = "%d:%02d:%02d" % (h1, m1, s1)
                else:
                    textTime = "%02d:%02d" % (m1, s1)

                cleanPart(0, textPosTop, barHalf, textPosTop + textSizeSmall)
                draw.textwrapped(textPosition, textTime, 30, lineHeightNormal, fontSmall, colorTime)

            # duration
            if (
                volumioStatus.get('duration') != lastVolumioStatus.get('duration')
                or volumioStatus.get('status') != lastVolumioStatus.get('status')
            ):
                m2, s2 = divmod(trackLength, 60)
                h2, m2 = divmod(m2, 60)

                if trackLength >= 3600:
                    # hours, minutes, seconds
                    textDuration = "%d:%02d:%02d" % (h2, m2, s2)
                else:
                    # minutes, seconds
                    textDuration = "%02d:%02d" % (m2, s2)

                cleanPart(barHalf, textPosTop, barWidth, textPosTop + textSizeSmall)
                rightDurationPosition = barWidth - fontSmall.getsize(textDuration)[0] - displayMargin # calculate right pos based on text width
                draw.textwrapped((rightDurationPosition, textPosTop), textDuration, 30, lineHeightNormal, fontSmall, colorTime)

class PlayStateSymbol():
    """Play status symbol"""
    # global textStatus

    def __init__(self):
        debug('=== PLAY STATE')
        debug(textStatus)

        if textStatus != '' and textStatus != lastVolumioStatus.get('status'):
            self.view()

    def view(self):
        left = 245 if displayLandscape else 168
        top = 210 if displayLandscape else 69

        draw.pasteimage(currentDir + "/img/status-" + textStatus + ".png", (left, top), True)

class VolumeText():
    """Volume text"""
    # global textVolume
    def __init__(self):
        debug('=== VOLUME')

        if textVolume != lastVolumioStatus.get('volume'):
            self.view()

    def view(self):
        if displayLandscape:
            valueTop = 210
            # clean volume text part
            cleanPart(280, valueTop, 300, valueTop + textSizeBig)

            rightVolumePosition = TFT.height - fontBig.getsize(textVolume)[0] - 20 # calculate right pos based on text width
        else:
            valueTop = 68
            # clean volume text part
            cleanPart(196, valueTop, 220, valueTop + textSizeBig)

            rightVolumePosition = TFT.width - fontBig.getsize(textVolume)[0] - 20 # calculate right pos based on text width

        draw.textwrapped((rightVolumePosition, valueTop), textVolume, 30, lineHeightBig, fontBig, "white")

class AlbumName:
    """Album text"""
    def __init__(self):
        self.valueTop = 115 if displayLandscape else textTopSongDetailsAlbum

        debug('=== ALBUM NAME')
    
        if volumioStatus.get('album') != lastVolumioStatus.get('album'):
            self.view()

    def view(self):
        if displayLandscape:
            # clean out album data part
            cleanPart(0, self.valueTop, TFT.height -1, self.valueTop + (lineHeightNormal * 2) -1)
            draw.textwrapped((displayMargin, self.valueTop), textAlbum, 38, lineHeightNormal, fontNormal, colorAlbum)
        else:
            # clean out album data part
            cleanPart(0, self.valueTop, TFT.width -1, self.valueTop + (lineHeightNormal * 2) -1)
            draw.textwrapped((displayMargin, self.valueTop), textAlbum, 34, lineHeightNormal, fontNormal, colorAlbum)

class ArtistName:
    """Artist text"""
    def __init__(self):
        self.valueTop = 85 if displayLandscape else textTopSongDetailsArtist

        debug('=== ARTIST NAME')

        if volumioStatus.get('artist') != lastVolumioStatus.get('artist'):
            self.view()

    def view(self):
        if not textAlbum:
            self.valueTop = textTopSongDetailsAlbum

        if displayLandscape:
            # clean out artist data part
            cleanPart(0, self.valueTop, TFT.height -1, self.valueTop + (lineHeightNormal * 2) -1)
            draw.textwrapped((displayMargin, self.valueTop), textArtist, 34, lineHeightNormal, fontNormal, colorArtist)
        else:
            # clean out artist data part
            cleanPart(0, self.valueTop, TFT.width -1, self.valueTop + (lineHeightNormal * 2) -1)
            draw.textwrapped((displayMargin, self.valueTop), textArtist, 34, lineHeightNormal, fontNormal, colorArtist)

class SongTitle:
    """Song title text"""
    def __init__(self):
        self.valueTop = 145 if displayLandscape else textTopSongDetailsTitle
        self.textTitle = textTitle # set globally
        self.maxTitleLength = 125

        debug('=== SONG TITLE')

        if volumioStatus.get('title') != lastVolumioStatus.get('title'):
            self.view()

    def view(self):
        if not textAlbum:
            self.valueTop = textTopSongDetailsArtist

        # shorten title length to prevent overflow
        if len(self.textTitle) > self.maxTitleLength:
            self.textTitle = self.textTitle[:self.maxTitleLength] + '...'

        if displayLandscape:
            # clean out song title data part
            cleanPart(0, self.valueTop, TFT.height -1, TFT.width - 40 -1)
            draw.textwrapped((displayMargin, self.valueTop), self.textTitle, 38, lineHeightBig, fontBig, colorSongtitle)
        else:
            # clean out song title data part
            cleanPart(0, self.valueTop, TFT.width -1, TFT.height - coverSize -1)
            draw.textwrapped((displayMargin, self.valueTop), self.textTitle, 25, lineHeightBig, fontBig, colorSongtitle)

class FilestreamInfo:
    """File/Stream data (icon, bitrate)"""
    def __init__(self):
        self.fileData = ''
        self.valueLeft = displayMargin + (0 if displayLandscape else coverSize)
        self.valueTop = ((TFT.width if displayLandscape else TFT.height) - (displayMargin * (3 if showUpsInfo else 2)) - (textSizeSmall * (3 if showUpsInfo else 2))) + (6 if showUpsInfo else 3)
        self.width = (237 if displayLandscape else TFT.width) - 1
        self.view()

    def view(self):
        debug('=== FILE STREAM INFO')

        if volumioStatus.get('bitdepth'):
            self.fileData = str(volumioStatus.get('bitdepth'))

        if volumioStatus.get('samplerate'):
            self.fileData = self.fileData + " "+ u'•' + " " + str(volumioStatus.get('samplerate'))

            # some track types (m4a?) doesn't contain kHz string
            if str(volumioStatus.get('samplerate'))[-3:].lower() != 'khz':
                self.fileData = self.fileData + " kHz"

        # Webradio
        if volumioStatus.get('bitdepth') == '' and volumioStatus.get('samplerate') == '' and volumioStatus.get('service') == 'webradio':
            self.fileData = 'Stream: ' + str(volumioStatus.get('bitrate'))

        if (volumioStatus.get('trackType') and volumioStatus.get('trackType') != lastVolumioStatus.get('trackType')) or (volumioStatus.get('stream') and volumioStatus.get('stream') != lastVolumioStatus.get('stream')):
            # clean out file stream icon part
            cleanPart(self.valueLeft, self.valueTop, self.width, self.valueTop + lineHeightSmall)

            if volumioStatus.get('trackType') and volumioStatus.get('trackType') != 'webradio':
                draw.pasteimage(currentDir + "/img/format-icons/" + volumioStatus.get('trackType').lower() + ".png", (self.valueLeft, self.valueTop), True);
            elif volumioStatus.get('stream') and volumioStatus.get('stream') != True:
                draw.pasteimage(currentDir + "/img/format-icons/" + volumioStatus.get('stream').lower() + ".png", (self.valueLeft, self.valueTop), True);
            elif volumioStatus.get('service') and volumioStatus.get('service') == 'webradio':
                draw.pasteimage(currentDir + "/img/format-icons/webradio.png", (self.valueLeft, self.valueTop), True);
        else:
            # clean out file stream text part
            cleanPart(self.valueLeft + maxWidthSourceIcon + displayMargin, self.valueTop, self.width, self.valueTop + lineHeightSmall)

        draw.textwrapped(((self.valueLeft + maxWidthSourceIcon + displayMargin), self.valueTop +1), self.fileData, 30, lineHeightSmall, fontSmall, colorStatus)
        #TFT.textdirect(((self.valueLeft + maxWidthSourceIcon + displayMargin), self.valueTop +1), self.fileData, fontSmall, colorStatus)

class NetworkInfo:
    """Network IP"""
    def __init__(self):
        self.ip = getNetworkIp()
        self.valueLeft = displayMargin + (0 if displayLandscape else coverSize)
        self.valueTop = ((TFT.width if displayLandscape else TFT.height) - (displayMargin * (2 if showUpsInfo else 1)) - (textSizeSmall * (2 if showUpsInfo else 1))) + (3 if showUpsInfo else 0)
        self.width = (237 if displayLandscape else TFT.width) - 1
        self.view()

    def view(self):
        debug('=== NETWORK INFO')

        # clean out network data part
        cleanPart(self.valueLeft, self.valueTop, self.width, self.valueTop + lineHeightSmall)

        if iface and iface != None and ipaddress:
            draw.pasteimage(currentDir + "/img/connection/" + iface + ".png", (self.valueLeft, self.valueTop), True);
            draw.textwrapped(((self.valueLeft + maxWidthSourceIcon + displayMargin), self.valueTop +1), ipaddress + ' (' + iface + ')', 30, lineHeightSmall, fontSmall, colorStatus)
        else:
            draw.textwrapped(((self.valueLeft + maxWidthSourceIcon + displayMargin), self.valueTop +1), 'Keine IP', 30, lineHeightSmall, fontSmall, colorStatus)

class BatteryInfo():
    """UPS capacity icon and text"""
    def __init__(self):
        if showUpsInfo:
            self.getTemperature()
            self.readVoltage()
            self.lastUpsCapacityInt = lastUpsCapacityInt

            self.valueLeft = displayMargin + (0 if displayLandscape else coverSize)
            self.valueTop = ((TFT.width if displayLandscape else TFT.height) - displayMargin - textSizeSmall)
            self.width = (237 if displayLandscape else TFT.width) - 1

            if self.lastUpsCapacityInt != upsCapacityInt:
                self.view()

    def view(self):
        debug('=== BATTERY INFO')

        # clean out battery data part
        cleanPart(self.valueLeft, self.valueTop, self.width, self.valueTop + lineHeightSmall)

        drawCapacitySymbol(upsCapacityInt)
        upsStatusString = '{:.0f}'.format(self.cpuTemperatureInt) + u'°' + 'C '+ u'•' + ' {:.2f}'.format(self.upsVoltageInt) + "V "+ u'•' + " " + str(upsCapacityInt) + "%"
        draw.textwrapped(((self.valueLeft + maxWidthSourceIcon + displayMargin), self.valueTop +1), upsStatusString, 30, lineHeightSmall, fontSmall, colorStatus)

        lastUpsCapacityInt = upsCapacityInt
    
    def getTemperature(self):
        """read temperature"""
        cpu = CPUTemperature()
        self.cpuTemperatureInt = cpu.temperature

    # Read UPS Voltage
    def readVoltage(self):
        """read voltage from UPS"""
        read = ups_bus.read_word_data(ups_device_address, 2)
        swapped = unpack("<H", pack(">H", read))[0]
        voltage = swapped * 1.25 /1000/16
        self.upsVoltageInt = voltage

# Read UPS capacity
def readCapacity():
    read = ups_bus.read_word_data(ups_device_address, 4)
    swapped = unpack("<H", pack(">H", read))[0]
    capacity = (swapped / 256)
    return capacity

# Read UPS status
def readStatus():
    read = ups_bus.read_word_data(ups_device_address, 0x14)
    return unpack("<H", pack(">H", read))[0]

# Draw battery symbol depending on capacity percentage
def drawCapacitySymbol(percent):
    status = readStatus()

    debug('=== BATTERY SYMBOL')

    left = displayMargin + (0 if displayLandscape else coverSize)
    top = (TFT.width if displayLandscape else TFT.height) - 15

    if status < 1024:
        draw.pasteimage(currentDir + "/img/battery-horizontal-charging.png", (left, top), True)
        debug('AC Power Connected 3A Charging')
    else:
        debug('No power connected')
        imagePercent = 100

        if percent >= 0 and percent < 25:
            imagePercent = 25
        elif percent >= 25 and percent < 50:
            imagePercent = 50
        elif percent >= 50 and percent < 75:
            imagePercent = 75
        draw.pasteimage(currentDir + "/img/battery-horizontal-" + str(imagePercent) + ".png", (left, top), True)

# ==========================================

def drawView():
    prepareAlbumArt() # takes 2% of cpu
    PlayStateSymbol()
    VolumeText()
    prepareTime(76 if displayLandscape else 78, (displayMargin, 60 if displayLandscape else 85)) # barPosition, text: (left, top)
    AlbumName()
    ArtistName()
    SongTitle()
    FilestreamInfo()
    NetworkInfo()
    BatteryInfo()

    TFT.display() # takes 8%


def debug(*args):
    """
    Debug: prints the concatenated args
    """
    if (debugOutput):
        lst=[]
        for arg in args:
            lst.append(str(arg))
        print ' '.join(lst)


def log2file(error):
    """Logs a string into a file"""
    with open(logfile, 'a') as file_object:
        file_object.write(error + "\n")


# Display function which runs in a thread
def display(name, delay, run_event):
    global volumioStatus, lastVolumioStatus, textStatus, textArtist, textTitle, textAlbum, textVolume, upsCapacityInt

    #print "im running once"

    while run_event.is_set():
        tmpVolumioStatus = check_output(['volumio', 'status'])

        if tmpVolumioStatus:
            debug("running display thread")

            volumioStatus = JsonLoad(tmpVolumioStatus)

            if showUpsInfo:
                upsCapacityInt = readCapacity()

                if upsCapacityInt > 100:
                    upsCapacityInt = 100

            if volumioStatus != lastVolumioStatus or (showUpsInfo and upsCapacityInt != lastUpsCapacityInt):
                if volumioStatus.get('status'):
                    textStatus = str(volumioStatus['status'])
                    textVolume = str(volumioStatus.get('volume'))

                    # get some global values from volumio status
                    if True: #volumioStatus.get('status') != 'stop':
                        if volumioStatus.get('album'):
                            textAlbum = volumioStatus.get('album').encode('utf-8').decode('utf-8').strip()
                        else:
                            textAlbum = ''

                        if volumioStatus.get('artist'):
                            textArtist = volumioStatus.get('artist').encode('utf-8').decode('utf-8').strip()
                        else:
                            textArtist = ''

                        if volumioStatus.get('title'):
                            textTitle = volumioStatus.get('title').encode('utf-8').decode('utf-8').strip()
                        else:
                            textTitle = ''
                    #"""

                drawView()

                lastVolumioStatus = volumioStatus

            sleep(sleepDelayPlay)

        else:
            sleep(sleepDelayInitial)


def sigterm_handler(_signo, _stack_frame):
    # Raises SystemExit(0):
    log2file("shutting down service")
    exit(0)
    #raise(SystemExit)

if len(argv) > 1 and argv[1] == "handle_signal":
    signal(SIGTERM, sigterm_handler)


def main():
    #global sleepDelayPlay

    drawShutdownView = True

    initDisplay()

    run_event = ThreadEvent()
    run_event.set()
    job = ThreadThread(target = display, args = ("task", sleepDelayPlay, run_event))
    job.start()
    log2file("Started")

    try:
        while 1:
            sleep(.1)
    except (KeyboardInterrupt, SystemExit):
        debug("clear event thread")
        run_event.clear()
        job.join()
        debug("thread successfully closed")
        drawShutdownView = False
        exit(0)
    except BaseException as b:
        log2file(b)
    except IOError:
        log2file("IOError. Couldn't open file: " + logfile)
    except Exception as e:
        log2file(e)
    except:
        log2file("SOMETHING WENT REALLY WRONG !")
    finally:
        if drawShutdownView:
            try:
                TFT.clear()
                debug("display shutdown view")
                ShutdownView()
                sleep(10)
                #TFT.clear()
                #GPIO.cleanup()
            except:
                pass

        log2file("Stopped")
        TFT.clear()
        GPIO.cleanup()
        run_event.clear()
        job.join()
        debug("cleaned up GPIOs")

if __name__ == "__main__":
    main()
