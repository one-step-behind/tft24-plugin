#!/bin/bash
## Display uninstallation script
echo "=== Uninstalling Volumio ILI9341 TFT Display plugin and it's dependencies..."
PLUGIN_NAME="tft24-display"
PLUGIN_TYPE="miscellanea"
INSTALLING="./${PLUGIN_NAME}-plugin.installing"
UNINSTALLING="./${PLUGIN_NAME}-plugin.uninstalling"

if [ ! -f $INSTALLING ]; then

	touch $UNINSTALLING

	PLUGINPATH=/data/plugins/${PLUGIN_TYPE}/${PLUGIN_NAME}
	HOMEPATH=/home/volumio/${PLUGIN_NAME}

	# Stop and unsoftlink Display Plugin services
	sudo systemctl stop ${PLUGIN_NAME}-startup
	sudo systemctl stop ${PLUGIN_NAME}
	#sudo rm /lib/systemd/system/${PLUGIN_NAME}-startup.service
	rm /etc/systemd/system/${PLUGIN_NAME}-startup.service
	rm /etc/systemd/system/${PLUGIN_NAME}.service

	# Remove plugin
	rm -rf ${PLUGINPATH}

	# Remove Plugin resources
	rm -rf ${HOMEPATH}
	rm -rf /data/configuration/${PLUGIN_TYPE}/${PLUGIN_NAME}

	rm $UNINSTALLING

	#required to end the plugin uninstall
	echo "Plugin successfully uninstalled. ==="
elif [ ! -f $UNINSTALLING ]; then
	echo "Plugin is already uninstalling! ABORT uninstall. ==="
else
	echo "Plugin is still installing! ABORT uninstall. ==="
fi