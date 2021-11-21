# ILI9341 TFT display plugin for Volumio 2.x

You built a battery powered Musicbox with an SPI TFT and want to display some informations about the actual song which is playing? Here it is. The ILI9341 display plugin for Volumio 2.x.

## Constraints

I ordered a display without touch. So touch is not handled by this script, yet. There is also no need for that because there's no menu or similar navigation. It just _displays_ information without any interaction.

The Python script to get all the informations and to show them on the display is _not_ optimized in regards of resources and speed but it's roughly functional.

![TFT display plugin sample](/resources/display-sample.jpg?raw=true "TFT display plugin sample")

## Installation

You can download the ZIP or clone the repository.

1. SSH into your Volumio
2. Download ZIP or clone repository
   * **Download:** `wget -O tft24-plugin.zip https://github.com/one-step-behind/tft24-plugin/archive/refs/heads/main.zip` and unpack
   * **Clone:** `git clone https://github.com/one-step-behind/tft24-plugin.git`
3. Change into `tft24-plugin` directory
4. Run the command: `volumio plugin install` to freshly _install_ or `volumio plugin update` to _update_ the plugin
5. Wait a few seconds for a message saying install was successful. You can press CTRL+C if it says *Progress: 100* and *Plugin successfully installed.*
6. Login to Volumio IU and go to *Plugins*
7. Configure the plugin to your needs
8. Enjoy watching at your display :-)
