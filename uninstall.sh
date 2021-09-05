#!/bin/bash
## ILI9341 TFT Display plugin uninstallation script
echo "=== Uninstalling Volumio ILI9341 TFT Display plugin and it's dependencies..."
PLUGIN_TYPE="user_interface"
PLUGIN_NAME="tft24-display"
INSTALLING="./${PLUGIN_NAME}-plugin.installing"
UNINSTALLING="./${PLUGIN_NAME}-plugin.uninstalling"
PLUGIN_DATA_PATH=/data/plugins/${PLUGIN_TYPE}/${PLUGIN_NAME}

if [ -f $UNINSTALLING ]; then
	echo "Plugin is already uninstalling! ABORT uninstall. ==="
elif [ -f $INSTALLING ]; then
	echo "Plugin is still installing! ABORT uninstall. ==="
else
	touch $UNINSTALLING

	# Stop and unsoftlink the display startup service
	sudo systemctl stop ${PLUGIN_NAME}-startup
	rm /etc/systemd/system/${PLUGIN_NAME}-startup.service

	# Stop and unsoftlink the Volumio display service
	sudo systemctl stop ${PLUGIN_NAME}
	rm /etc/systemd/system/${PLUGIN_NAME}.service

	# Remove plugin folder
	rm -rf ${PLUGIN_DATA_PATH}

	# Remove plugin configuration
	rm -rf /data/configuration/${PLUGIN_TYPE}/${PLUGIN_NAME}

	rm $UNINSTALLING

	echo "Plugin successfully uninstalled. ==="
fi