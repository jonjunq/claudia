# Recipe: your computer and your game servers

> *"Turn on the computer in the study."* *"Turn it off, I forgot."* *"Map the shared folder as drive Z: on my PC."*
> *"Open this page on my computer's screen."* *"Turn on the Minecraft server."*

**Ours does this**: Wake-on-LAN to turn the desktop on, a shutdown over SSH, mapping and removing a network drive,
pairing a game-streaming client, and starting or stopping the game servers.
**Possible, with care**: installing programs, preparing a second operating system (dual boot).

## Turning it on: Wake-on-LAN

- In the BIOS/UEFI: "Wake on LAN" or "Resume by PCI-E" on. In Windows, the network card's *Wake on Magic Packet*;
  turning off *Fast startup* helps.
- The computer's MAC address and the assistant's machine on the same network (magic packets do not cross routers).
- `wakeonlan <MAC>` on the assistant's machine. Allowing it outright is safe: it only sends a wake-up packet
  (`"Bash(wakeonlan *)"`).

## Everything else: SSH with a narrow permission

The assistant needs an SSH key it can use on your computer (Windows has an OpenSSH server built in; Linux and macOS
too). Give it **its own key** and decide how far it reaches:

- **Narrowest (Linux/macOS)**: a forced command in `authorized_keys`, so that key can only run one script that
  accepts a few words (`shutdown`, `sleep`, `map-drive`):
  `command="/usr/local/bin/assistant-pc",restrict ssh-ed25519 AAAA… assistant`
- **What we did (Windows)**: an ordinary key, plus an `allow` sentence for exactly two actions; anything else still
  goes past the classifier, which asks you or blocks:

```json
"The owner authorises the assistant, when the owner asks on Telegram, to do exactly this on the owner's PC (ssh pc): shut it down with `ssh pc 'shutdown /s /t 5'`, and change or remove its network drive Z: (net use Z: …, net use Z: /delete). Any other change on that PC still needs asking."
```

Be honest with yourself about the second option: the key can do anything your user can; the sentence and the
classifier are what hold it back. Do not put `Bash(ssh pc *)` in `permissions.allow`: that would skip the classifier
for every command.

## Ask your assistant to set it up

> "My desktop is [Windows/Linux] at [address], MAC [..]. I want to ask you to turn it on, turn it off and map the
> shared folder. Set up the SSH access with your own key and the narrowest permission you can, and tell me what I
> have to do on the PC."

## More you can ask (possible, some tried)

- **Open a page on its screen** ("put the recipe on my monitor"): a scheduled task in the logged-in session on
  Windows, `DISPLAY=:0 xdg-open` on Linux.
- **Game streaming** (Sunshine on the PC, Moonlight on the TV or laptop): when Moonlight shows a PIN, send it to the
  assistant and it pairs through Sunshine's web API.
- **Game servers** (Minecraft, Valheim…, on a panel such as Pelican or Pterodactyl): a sub-user API key limited to
  power on/off and the console of those servers, and "turn on the server for tonight" works from the phone. Read
  access to your server for the rest: [homelab-read-access.md](../homelab-read-access.md).
- **Installing programs** or **preparing a dual boot**: possible over SSH, and ours helped with both, but these are
  the changes that can cost you data. Ask for the plan first, make a backup, and approve each step.

## Risks

- ⚠️ An SSH key to your computer is the biggest reach you can give it after your email: whoever fools the assistant
  (a malicious email, a web page) gets that reach too. Prefer the forced command; at least keep it out of
  `permissions.allow`.
- Shutting down loses unsaved work: ours waits 5 seconds and only on your request; for a shared computer, ask
  first who is using it.
- Launching games or launchers (Steam) over SSH can run them outside your desktop session and break them: let it
  wake the computer and prepare things, and start the game yourself.
