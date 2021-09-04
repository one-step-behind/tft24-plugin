'use strict';

var config = new(require('v-conf'))();
var exec = require('child_process').exec;
var libQ = require('kew');

var serviceName = 'tft24-display';

// Define the Controller class
module.exports = ControllerVolumioDisplay;

function ControllerVolumioDisplay(context) {
  // This fixed variable will let us refer to 'this' object at deeper scopes
  var self = this;

  this.context = context;
  this.commandRouter = this.context.coreCommand;
  this.logger = this.context.logger;
  this.configManager = this.context.configManager;
};

ControllerVolumioDisplay.prototype.onVolumioStart = function() {
  var self = this;
  self.logger.info("Display initialized");

  this.configFile = this.commandRouter.pluginManager.getConfigurationFile(this.context, 'config.json');
  // self.getConf(this.configFile);

  return libQ.resolve();
};

ControllerVolumioDisplay.prototype.onStart = function() {
  var self = this;
  var defer = libQ.defer();

  self.startService(serviceName, true)
    .then(function() {
      defer.resolve();
    })
    .fail(function(e) {
      self.commandRouter.pushToastMessage('error', "Startup failed", "Could not start the " + serviceName + " service in a fashionable manner. Error: " + e);
      self.logger.info("onStart: Could not start the " + serviceName + " service in a fashionable manner. Error: " + e);
      defer.reject(new error());
    });

  return defer.promise;
};

ControllerVolumioDisplay.prototype.onStop = function() {
  var self = this;
  var defer = libQ.defer();

  self.stopService(serviceName)
    .then(function() {
      defer.resolve();
    })
    .fail(function(e) {
      self.commandRouter.pushToastMessage('error', "Stopping failed", "Could not stop the " + serviceName + " service in a fashionable manner. Error: " + e);
      self.logger.info("onStop: Could not start the " + serviceName + " service in a fashionable manner. Error: " + e);
      defer.reject(new error());
    });

  return defer.promise;
};

// Plugin methods -----------------------------------------------------------------------------

ControllerVolumioDisplay.prototype.getConfigurationFiles = function() {
	return ['config.json'];
}

ControllerVolumioDisplay.prototype.getUIConfig = function() {
  var self = this;
  var defer = libQ.defer();
  var lang_code = this.commandRouter.sharedVars.get('language_code');

  self.getConf(this.configFile);
  self.logger.info("Loaded the previous config.");

  self.commandRouter.i18nJson(
    __dirname + '/i18n/strings_' + lang_code + '.json',
		__dirname+'/i18n/strings_en.json',
    __dirname + '/UIConfig.json'
  )
    .then(function(uiconf) {
      self.logger.info("## populating UI...");

      uiconf.sections[0].content[0].value = self.config.get('gpio_dc');
      uiconf.sections[0].content[1].value = self.config.get('gpio_rst');
      uiconf.sections[0].content[2].value = self.config.get('gpio_led');
      uiconf.sections[0].content[3].value = self.config.get('ups');
      uiconf.sections[0].content[4].value = self.config.get('debugging');

      uiconf.sections[1].content[0].value.value = self.config.get('display_fontface').toString();
      uiconf.sections[1].content[0].value.label = self.config.get('display_fontface').toString();
      uiconf.sections[1].content[1].value = self.config.get('display_landscape');
      uiconf.sections[1].content[2].value = self.config.get('cover_fullscreen');
      uiconf.sections[1].content[3].value = self.config.get('cover_width');
      uiconf.sections[1].content[4].value = self.config.get('cover_transparency');

      uiconf.sections[1].content[5].value = self.config.get('color_timebar');
      uiconf.sections[1].content[6].value = self.config.get('color_time');
      uiconf.sections[1].content[7].value = self.config.get('color_album');
      uiconf.sections[1].content[8].value = self.config.get('color_artist');
      uiconf.sections[1].content[9].value = self.config.get('color_songtitle');
      uiconf.sections[1].content[10].value = self.config.get('color_status');

      self.logger.info("Display settings loaded");

      defer.resolve(uiconf);
    })
    .fail(function() {
      defer.reject(new Error());
    });

  return defer.promise;
};

ControllerVolumioDisplay.prototype.getConf = function(configFile) {
  this.config = config;
  this.config.loadFile(configFile);

  return libQ.resolve().promise;
};


ControllerVolumioDisplay.prototype.tryParse = function(str, defaultValue) {
  var retValue = defaultValue;
  str = str.toString();

  if (str !== null) {
    if (str.length > 0) {
      if (!isNaN(str)) {
        retValue = parseInt(str);
      }
    }
  }

  return retValue;
};

ControllerVolumioDisplay.prototype.startService = function(serviceName) {
  var self = this;
  var defer = libQ.defer();
  var command = "/usr/bin/sudo /bin/systemctl start " + serviceName;

  exec(command, {
    uid: 1000,
    gid: 1000
  }, function(error, stdout, stderr) {
    if (error !== null) {
      self.commandRouter.pushConsoleMessage('The following error occurred while starting ' + serviceName + ' service: ' + error);
      self.commandRouter.pushToastMessage('error', "Starting service failed", "Starting " + serviceName + " service failed with error: " + error);
      defer.reject();
    } else {
      self.commandRouter.pushConsoleMessage(serviceName + ' started');
      self.commandRouter.pushToastMessage('success', "Starting", "Started " + serviceName + " service.");
      defer.resolve();
    }
  });

  return defer.promise;
};

ControllerVolumioDisplay.prototype.reloadService = function () {
	var defer=libQ.defer();
	var command = "/usr/bin/sudo /bin/systemctl daemon-reload";

	exec(command, {uid:1000,gid:1000}, function (error, stdout, stderr) {
		if (error !== null) {
			defer.reject();
		}
		else {
			defer.resolve();
		}
	});

	return defer.promise;
};

ControllerVolumioDisplay.prototype.restartService = function(serviceName, boot) {
  var self = this;
  var defer = libQ.defer();

  var command = "/usr/bin/sudo /bin/systemctl restart " + serviceName;

  exec(command, {
    uid: 1000,
    gid: 1000
  }, function(error, stdout, stderr) {
    if (error !== null) {
      self.commandRouter.pushConsoleMessage('The following error occurred while restarting ' + serviceName + ' service: ' + error);
      self.commandRouter.pushToastMessage('error', "Restart failed", "restartService: Restarting " + serviceName + " service failed with error: " + error);
      defer.reject();
    } else {
      self.commandRouter.pushConsoleMessage(serviceName + ' started');

      if (boot == false)
        self.commandRouter.pushToastMessage('success', "Restarted " + serviceName, "Restarted " + serviceName + " service for the changes to take effect.");

      defer.resolve();
    }
  });

  return defer.promise;
};

ControllerVolumioDisplay.prototype.stopService = function(serviceName) {
  var self = this;
  var defer = libQ.defer();
  var command = "/usr/bin/sudo /bin/systemctl stop " + serviceName;

  self.commandRouter.pushToastMessage('info', "Stopping Display service");

  exec(command, {
    uid: 1000,
    gid: 1000
  }, function(error, stdout, stderr) {
    if (error !== null) {
      self.commandRouter.pushConsoleMessage('The following error occurred while stopping ' + serviceName + ' service: ' + error);
      self.commandRouter.pushToastMessage('error', "Stopping service failed", "Stopping " + serviceName + " service failed with error: " + error);
      defer.reject();
    } else {
      self.commandRouter.pushConsoleMessage(serviceName + ' stopped');
      self.commandRouter.pushToastMessage('success', "Stopping Display service", "Stopped " + serviceName + " service.");
      defer.resolve();
    }
  });

  return defer.promise;
};

// Public Methods ---------------------------------------------------------------------------------------

ControllerVolumioDisplay.prototype.updateConnectionConfig = function(data) {
  var self = this;
  var defer = libQ.defer();

  self.config.set('gpio_dc', self.tryParse(data['gpio_dc'], 0));
  self.config.set('gpio_rst', self.tryParse(data['gpio_rst'], 0));
  self.config.set('gpio_led', self.tryParse(data['gpio_led'], 0));
  self.config.set('ups', data['ups']);
  self.config.set('debugging', data['debugging']);
  self.commandRouter.pushToastMessage('success', "Successfully saved connection settings");

  self.reloadService()
    .then(function(restart) {
      self.restartService(serviceName, false);
      defer.resolve(restart);
    })
    .fail(function(error) {
      self.commandRouter.pushToastMessage('error', "updateConnectionConfig: Restart failed", "Restarting " + serviceName + " failed with error: " + error);
      defer.reject(new Error());
    });

  return defer.promise;
};

ControllerVolumioDisplay.prototype.updateVisualConfig = function(data) {
  var self = this;
  var defer = libQ.defer();

  self.config.set('display_fontface', data['display_fontface']['value']);
  self.config.set('display_landscape', data['display_landscape']);
  self.config.set('cover_fullscreen', data['cover_fullscreen']);
  self.config.set('cover_width', self.tryParse(data['cover_width'], 80));
  self.config.set('cover_transparency', self.tryParse(data['cover_transparency'], 30));

  self.config.set('color_album', data['color_album']);
  self.config.set('color_artist', data['color_artist']);
  self.config.set('color_songtitle', data['color_songtitle']);
  self.config.set('color_status', data['color_status']);
  self.config.set('color_time', data['color_time']);
  self.config.set('color_timebar', data['color_timebar']);

  self.commandRouter.pushToastMessage('success', "Successfully saved visual settings");

  self.reloadService()
    .then(function(restart) {
      self.restartService(serviceName, false);
      defer.resolve(restart);
    })
    .fail(function(error) {
      self.commandRouter.pushToastMessage('error', "updateVisualConfig: Restart failed", "Restarting " + serviceName + " failed with error: " + error);
      defer.reject(new Error());
    });

  return defer.promise;
};

ControllerVolumioDisplay.prototype.serviceRestart = function(data) {
  var self = this;
  var defer = libQ.defer();

  self.commandRouter.pushToastMessage('success', "Restarting Display Service");

  self.restartService(serviceName, false)
    .fail(function(e) {
      self.commandRouter.pushToastMessage('error', "Restart failed", "Restarting " + serviceName + " service failed with error: " + e);
      defer.reject(new Error());
    });

  return defer.promise;
}
