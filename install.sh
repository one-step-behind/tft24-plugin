#!/bin/bash
## ILI9341 TFT Display plugin installation script
echo "=== Installing ILI9341 TFT Display plugin and it's dependencies..."
PLUGIN_TYPE="user_interface"
PLUGIN_NAME="tft24-display"
INSTALLING="./${PLUGIN_NAME}-plugin.installing"
PLUGIN_DATA_PATH=/data/plugins/${PLUGIN_TYPE}/${PLUGIN_NAME}

if [ -f $INSTALLING ]; then
	echo "Plugin is already installing! Abort this installation attempt. ==="
else
	touch $INSTALLING

	# Copy and reload the display startup service
	sudo systemctl stop ${PLUGIN_NAME}-startup
	mv -f ${PLUGIN_DATA_PATH}/service/${PLUGIN_NAME}-startup.service /etc/systemd/system/${PLUGIN_NAME}-startup.service
	sudo chmod 644 /etc/systemd/system/${PLUGIN_NAME}-startup.service
	sudo systemctl enable ${PLUGIN_NAME}-startup

	# Softlink and reload the Volumio display service
	sudo systemctl stop ${PLUGIN_NAME}
	mv -f ${PLUGIN_DATA_PATH}/service/${PLUGIN_NAME}.service /etc/systemd/system/${PLUGIN_NAME}.service
	sudo chmod 644 /etc/systemd/system/${PLUGIN_NAME}.service

	#sudo systemctl daemon-reload

	rm $INSTALLING

	echo "Plugin successfully installed. ==="
fi