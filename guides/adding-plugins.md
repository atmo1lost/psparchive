> reminder to find some [plugins](/plugins.html)

# installing plugins on psp

plugins add extra features to your cfw, like screenshots, overclocking, or cheats. this only works if you already have cfw installed.

## 1. find the plugin folder

on your memory stick, go to:

seplugins/

if it doesn't exist, create it.

## 2. copy the plugin files

drop the plugin's .prx file into the seplugins folder.

## 3. enable it

open seplugins/game.txt and seplugins/vsh.txt in a text editor.

add a line pointing to the plugin, like:

ms0:/seplugins/pluginname.prx 1

the 1 at the end turns it on, 0 turns it off.

- game.txt = loads in games
- vsh.txt = loads in the xmb menu

## 4. reboot

restart your psp. the plugin should now be active.

## troubleshooting

- freeze on boot: turn the plugin off in vsh.txt/game.txt, then check you copied the right prx for your cfw version
- plugin not doing anything: check the path in the txt file matches exactly where you put the prx