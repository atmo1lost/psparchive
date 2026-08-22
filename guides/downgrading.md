# downgrading PSP firmware

some CFW requires a specific firmware version below your current one.

## 1. confirm you actually need to downgrade

most modern CFW supports installing directly on the latest official firmware. only downgrade if your target CFW explicitly requires it.

## 2. backup first

back up your memory stick contents before doing anything else.

## 3. run the downgrader

```
1. Place the downgrader in /PSP/GAME/
2. Launch from XMB
3. Do not interrupt power during the process
```

## 4. confirm result

check firmware version in system info to confirm the downgrade landed.

## sources

- **chronoswitch (downgrader)** — actively maintained fork: [github.com/PSP-Archive/Chronoswitch](https://github.com/PSP-Archive/Chronoswitch)
- **official firmware EBOOTs (6.60/6.61)** — [pspunk.com/psp-update](https://www.pspunk.com/psp-update/)
- **older firmware versions** — [darthsternie.net/psp-firmwares](https://darthsternie.net/psp-firmwares/)

## MODEL WARNINGS!!

- 09g PSP-3000 units **cannot** go below firmware 6.30. attempting it can brick the device.
- always confirm your motherboard/model before downgrading, chronoswitch detects this but check its current changelog for your specific model support.
