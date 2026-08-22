# installing CXMB on psp

CXMB (color xmb) is a plugin that themes the psp xmb menu. requires custom firmware.

## requirements
- psp with cfw installed (6.60 pro-c, me, or similar)
- CXMB plugin files
- a CXMB-compatible theme

## steps

1. [download CXMB](/plugin.html?slug=cxmb)
2. extract the zip, you'll get a `plugins` folder and theme folders
3. copy the CXMB `.prx` file to `ms0:/seplugins/`
4. edit or create `ms0:/seplugins/game.txt` and `vsh.txt`, add:
   ```
   ms0:/seplugins/cxmb.prx 1
   ```
5. copy your chosen theme folder to `ms0:/PSP/THEME/`
6. reboot the psp
7. go to settings > theme, select the CXMB theme

## notes
- if it freezes on boot, remove the plugin line from `vsh.txt` via a pc (mount the memory stick) and check for a bad/corrupt theme file
- some themes require specific CXMB versions, mismatched versions cause crashes on the xmb
- back up `seplugins` before editing, one typo bricks the boot into xmb until fixed