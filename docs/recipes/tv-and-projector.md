# Recipe: the TV and the projector

> *"Put YouTube on the TV."* *"Open the film app on the projector."* *"Install the media server app on the bedroom
> TV."*

**Ours does this**: it installs, opens and removes apps on a smart TV and a projector through the manufacturer's
developer mode, and wakes the TV over the network. It never roots them.

## What it needs

- A TV or projector whose maker offers a **developer mode** with command-line tools, for example:
  - **LG webOS**: the *Developer Mode* app on the TV and LG's `ares-*` CLI (`ares-setup-device`, `ares-install`,
    `ares-launch`). Needs a free LG developer account; the assistant can create it for you if you allow sign-ups
    ([permissions.md](../permissions.md#examples)).
  - **Android TV / Google TV**: *Developer options* → *Network debugging*, and `adb connect <tv>:5555`
    (`adb shell am start …`, `adb install app.apk`).
  - Others (Samsung Tizen, Roku) have their own developer modes: ask your assistant to look up the current one for
    your model before buying anything.
- The device on a fixed address (a DHCP reservation in your router), and the assistant's machine able to reach it.
- For "turn the TV on": Wake-on-LAN enabled in the TV's settings (often called "Turn on via Wi-Fi/LAN") and
  `wakeonlan <MAC>` on the assistant's machine.

## Ask your assistant to set it up

> "I have a [brand, model] TV at [address]. Set up developer mode so you can open and install apps on it when I ask.
> Tell me what I have to do on the remote, step by step."

It will look up the current procedure, install the CLI, walk you through the steps on the TV (enabling developer
mode, a passphrase or a pairing prompt only you can accept) and test it by opening an app.

## Permissions

The classifier does not know the TV is yours. One `environment` sentence in `~/.claude/settings.json` (you write it,
not the assistant: [permissions.md](../permissions.md#teaching-the-auto-mode-classifier-about-your-setup)):

```json
"The owner owns the living-room TV (192.0.2.10) and the projector (192.0.2.11). Installing, launching and uninstalling apps on them through the manufacturer's developer mode and its command-line tools is authorised. Never root them or modify their system software."
```

If you want it faster, allow the CLI outright (`"Bash(ares-launch *)"`, `"Bash(adb -s 192.0.2.10:5555 *)"`,
`"Bash(wakeonlan *)"` in `permissions.allow`); those only talk to the device.

## Risks

- ⚠️ **Never ask it to root or jailbreak a device.** Besides the warranty, the request trips the model's
  safeguards (`[cyber]`), and the words stay in the conversation and keep tripping them every turn until you start
  a fresh one ([troubleshooting](../troubleshooting.md)). Developer mode plus sideloading covers almost everything.
- Sideloaded apps run on a device on your network: only from their official project pages or the store of the
  developer-mode community, never a random download.
- Network debugging on Android (`adb`) gives full control of the TV to anything on your network that can reach port
  5555: turn it on, pair, and keep your home network to devices you trust.
- Developer-mode sessions can expire (LG asks to renew from its app every so often). Ask the assistant to put the
  renewal in your calendar.

## What we learned

- Ours put an ad-free YouTube client, the media server's app and a game-streaming client on two LG devices in one
  evening, through developer mode only.
- The first attempt went through "root the projector" instead: that is what triggered the safeguards and froze the
  session. Rewording the notes it rereads every morning, and a fresh conversation, fixed it.
