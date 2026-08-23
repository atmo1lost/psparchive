# psp save modding, explained simply

a "save" is the file that remembers your progress in a game. on the psp these files are locked with a secret code (encryption) so nothing outside the game can read or change them. to edit a save (like giving yourself more money or unlocking a level) you first have to unlock it, change it, then lock it back up so the game accepts it again.

## the tool you need

**apollo save tool (psp)** does the unlock/change/lock steps for you, right on the psp, no computer needed.

- download: https://github.com/bucanero/apollo-psp/releases/tag/latest
- source code: https://github.com/bucanero/apollo-psp
- info page: https://bucanero.github.io/apollo-psp/
- gamebrew writeup (screenshots, feature list): https://www.gamebrew.org/wiki/Apollo_Save_Tool_PSP

## how it works, step by step

1. install apollo save tool on your psp like any other homebrew (needs cfw already installed, see the cfw guide)
2. open the game you want to mod, play until it saves once (load or save a level). this lets apollo grab the game's secret unlock code
3. open apollo save tool, find your save in the list
4. pick a ready-made patch/cheat if one exists (apollo has an online list of cheats for lots of games) and apply it
5. if you're doing your own edit instead of a cheat code: export/decrypt the save, this gives you a plain file you can open
6. edit the plain file with a hex editor (a tool that lets you view/change raw numbers in a file) — this part takes some care, wrong edits can corrupt the save
7. import/encrypt the save again so the game will accept it
8. load the game and check your save works

## if you don't have a modded psp (using ppsspp emulator instead)

ppsspp keeps saves encrypted by default, but you can turn that off:
- open ppsspp, go to file > open memory stick, then psp/system
- open the file `ppsspp.ini`
- find the line `EncryptSave = True` and change it to `EncryptSave = False`
- save the file and restart ppsspp
- source: https://kingdomsaveeditor.xee.dev/docs/decryption.html

with encryption off your saves are just plain files you can edit directly, no unlock step needed.

## other tools worth knowing

- **save-editor.com psp save editor/decrypter** — a website version, upload your save + PARAM.SFO (a small info file every save has) and it decrypts/encrypts for you: https://www.save-editor.com/tools/wse_psp_save_editor.html and https://www.save-editor.com/tools/wse_psp_save_encrypter_decrypter.html
- **psp-save (command line tool)** — for people comfortable with a terminal, does the same decrypt/encrypt job: https://github.com/vita8328/psp-save

## simple safety rule

always copy your save somewhere safe before touching it. if the edit goes wrong you can put the backup back and lose nothing.