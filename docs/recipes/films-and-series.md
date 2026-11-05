# Recipe: films, series and downloads

> *"I want to watch Dune tonight."* *"Get me the new season of that series."* *"Here is a .torrent, put it to
> download."* *"Is the film ready?"*

**Ours does this**: it asks your home media server for the film or series, shows you the versions it found (size,
language, quality), downloads the one you pick and tells you when it is in your library. It also queues `.torrent`
files and magnet links you send it.

## What it needs

- A media server at home you already run or are happy to run, typically:
  - **Jellyfin** (or Plex/Emby) for the library and the apps on your TV and phone;
  - **Radarr** (films) and **Sonarr** (series), which search, download and rename;
  - a download client, usually **qBittorrent**, with its web UI behind its own password;
  - optionally Prowlarr (indexers) and Bazarr (subtitles).
  The assistant can install all of these for you with Docker if it has root on a machine with disk space; otherwise
  your admin does it.
- Each app's API key in a private file on the assistant's machine (for example `~/.config/assistant/media.env`, mode
  600), and network access from the assistant's machine to those ports only.

## Ask your assistant to set it up

> "I run Radarr, Sonarr and Jellyfin at [address] (keys in ~/.config/assistant/media.env). When I say 'I want to
> watch X', find it, show me two or three versions with size and language, download the one I choose and tell me
> when it is ready. Never download anything I have not chosen. Write it into a skill."

Or, with nothing installed yet: "I'd like a media server at home for films and series. What would it take on this
machine, and what does it cost?"

The flow it should follow (and write down in its skill):

1. Add the film or series **without** monitoring, so nothing downloads on its own.
2. Ask for the release list (`GET /api/v3/release?movieId=…` in Radarr) and show you the best two or three.
3. On your choice, mark it monitored and grab that release.
4. **Check the runtime** of what arrived against the film's real length before saying "it's ready": fakes with the
   right name and the wrong content exist.

## Torrents you hand it

A `.torrent` sent on Telegram or a magnet link goes to the download client's API (`/api/v2/torrents/add`) in a
category you choose (say `games` → a folder shared to your computer over SMB). It reports progress when you ask and
tells you when it is done.

Download to a local disk and move when complete; writing a torrent straight onto a network share made our NAS lock
half-written files.

## Telling you without spending tokens (possible, not tried by us)

Radarr and Sonarr can call a webhook "on import". Point it at an [n8n](../n8n.md) workflow that sends you a
Telegram message ("🎬 Dune is ready"), or wakes the assistant if it should do something next. No polling, no turns.

## Permissions

```json
"The media server at 192.0.2.20 (Radarr, Sonarr, Jellyfin, qBittorrent) belongs to the owner. Searching for, adding and downloading films and series is authorised when the owner asks and picks the release (or tells the assistant to pick), adding torrents or magnet links the owner sends is authorised, and removing them is authorised when the owner asks."
```

## Risks

- ⚠️ **The law**: downloading copyrighted films and series without a licence is illegal in many countries, and on
  public torrent networks your IP address is visible to rights holders. What you download, and from where, is your
  decision; the assistant should not be the one choosing sources.
- Public trackers carry **fakes and malware** (an `.exe` or `.lnk` in a "film" folder). The runtime check above and
  refusing executables in film downloads cover most of it.
- The API keys of Radarr, Sonarr and qBittorrent are **full admin** of those apps: keep them in a private file, not
  in notes, and do not expose those web UIs to the internet.
- Disk space: large libraries fill disks. Ask it to say how much is left before each download.
- Do not let an email or a web page trigger a download: the `environment` sentence ties it to your request.
