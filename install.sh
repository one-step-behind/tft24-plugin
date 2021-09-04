#!/bin/bash
## Display installation script
echo "=== Installing ILI9341 TFT Display plugin and it's dependencies..."
PLUGIN_NAME="tft24-display"
PLUGIN_TYPE="miscellanea"
INSTALLING="./${PLUGIN_NAME}-plugin.installing"

if [ ! -f $INSTALLING ]; then

	touch $INSTALLING

	#CONFIGPATH=/data/configuration/${PLUGIN_TYPE}/${PLUGIN_NAME}
	PLUGINPATH=/data/plugins/${PLUGIN_TYPE}/${PLUGIN_NAME}
	HOMEPATH=/home/volumio/${PLUGIN_NAME}

	## Removing previous config
	#if [ ! -f "${CONFIGPATH}/config.json" ];
	#then
	#  echo "Configuration file doesn't exist, nothing to do"
	#else
	#  echo "Configuration File exists removing it"
	#  sudo rm ${CONFIGPATH}/config.json
	#fi

	# Copy custom scripts from the plugin to home directory
	mkdir /home/volumio/${PLUGIN_NAME}

	mv -f ${PLUGINPATH}/service/lib_tft24T.py ${HOMEPATH}/lib_tft24T.py
	mv -f ${PLUGINPATH}/service/${PLUGIN_NAME}.py ${HOMEPATH}/${PLUGIN_NAME}.py
	mv -f ${PLUGINPATH}/service/${PLUGIN_NAME}-startup.py ${HOMEPATH}/${PLUGIN_NAME}-startup.py
	mv -f ${PLUGINPATH}/service/fonts ${HOMEPATH}/fonts
	mv -f ${PLUGINPATH}/service/img ${HOMEPATH}/img
	#mv -f ${PLUGINPATH}/service/* ${HOMEPATH}
	#rm -rf ${PLUGINPATH}/service

	# Delete, softlink and reload the display services
	sudo systemctl stop ${PLUGIN_NAME}-startup
	ln -fs ${PLUGINPATH}/service/${PLUGIN_NAME}-startup.service /etc/systemd/system/${PLUGIN_NAME}-startup.service
	sudo systemctl stop ${PLUGIN_NAME}
	ln -fs ${PLUGINPATH}/service/${PLUGIN_NAME}.service /etc/systemd/system/${PLUGIN_NAME}.service

	#sudo systemctl daemon-reload
	sudo systemctl enable ${PLUGIN_NAME}-startup

	rm $INSTALLING

	#required to end the plugin install
	echo "Plugin successfully installed. ==="
else
	echo "Plugin is already installing! Abort this installation attempt. ==="
fi