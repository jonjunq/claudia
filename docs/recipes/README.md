# Everything you can ask it

The full list, with what each thing needs, its main risk and where the guide is. **✅ ours does it**: our assistant
does this for real, daily or whenever it comes up. **🧪 possible**: the pieces exist (here or elsewhere) and it fits,
but we have not tried it ourselves; expect to adjust.

Nothing here has to be set up in advance. Tell your assistant what you want, in your own words, and it reads the
guide (they are installed on its machine, in `/usr/local/share/assistant/docs/`), tells you what it would take and
what only you can do, and sets it up with your yes. In its first weeks it offers these things itself, one at a time,
when they fit ([first-days](../../templates/workspace/.claude/skills/first-days/SKILL.md)).

The recipes are for **your** setup: take the idea, not our architecture. Every `autoMode` sentence below is an
example to adapt, and you write those, not the assistant ([permissions.md](../permissions.md)).

## Everyday

| You say | | Needs | Main risk | Guide |
|---|---|---|---|---|
| *"Remind me to call the plumber tomorrow at ten"*, *"every Monday, the bins"* | ✅ | nothing | reminders vanish at restart unless written in its notes (the template does) | [daily-cycle](../daily-cycle.md) |
| Your day in one message every morning | ✅ | Calendar and Gmail connected | none worth naming | [daily-cycle](../daily-cycle.md) |
| A voice note instead of typing; it answers with its own voice if you like | ✅ | a free Groq key, or a local engine; ElevenLabs to speak | the audio goes to that service | [voice](../voice.md) |
| *"Tell me if anything important comes in"*, day and night, at no cost while nothing arrives | ✅ | n8n and a mail app password | n8n holds a password that reads your email | [n8n](../n8n.md) |
| *"Leave my inbox at zero"*, *"unsubscribe me from that advertising"* | ✅ | a mail app password | an unsubscribe confirms your address to the sender | [email-cleanup](email-cleanup.md) |
| *"File my payslips and invoices in Drive as they arrive"*, warranty reminders | ✅ | n8n email watch, Drive | attachments can carry instructions like any email | [email-cleanup](email-cleanup.md) |
| A parcel, a price, a page: *"tell me when it changes"*, switching itself off when done | ✅ | n8n | none worth naming | [n8n](../n8n.md) |
| *"What did I tell you about the boiler last month?"* | ✅ | nothing | none | [memory](../memory.md) |
| A photo of a paper (an insurance card, a letter): *"put the dates in my calendar"* | ✅ | nothing | the photo stays in its transcripts | — |
| *"Watch this reel/video and tell me if it's true"*, or note it for a weekly summary | ✅ | yt-dlp, ffmpeg | platforms' terms on downloading | [links-and-videos](links-and-videos.md) |
| *"Explain it in a diagram"*: a picture or a one-page explainer instead of a wall of text | ✅ | a diagram skill such as [diagram-design](https://github.com/cathrynlavery/diagram-design), and a headless browser for the screenshot | a third-party skill: check it first | [vetting-skills](../vetting-skills.md) |
| Talking to it on a call (a voice channel; a real phone number) | 🧪 / ✅ ours on Discord | a custom channel; a phone number costs per minute through a voice-agent service | experimental; a phone agent runs on pay-per-use APIs, not your subscription | [voice](../voice.md#experimental-a-voice-call-over-discord) |

## Home and devices

| You say | | Needs | Main risk | Guide |
|---|---|---|---|---|
| *"Put YouTube on the TV"*, *"install the media app on the projector"* | ✅ | the device's developer mode | never root a device: it trips the model's safeguards | [tv-and-projector](tv-and-projector.md) |
| *"I want to watch Dune tonight"*, *"the new season of that series"* | ✅ | a media server (Jellyfin + Radarr/Sonarr) | copyright law where you live; fakes on public trackers | [films-and-series](films-and-series.md) |
| *"Put this .torrent to download"* | ✅ | a download client with its own password | the same, and your IP is visible on public torrents | [films-and-series](films-and-series.md#torrents-you-hand-it) |
| *"Turn the computer on / off"*, *"map the network drive"* | ✅ | Wake-on-LAN; SSH with its own key | an SSH key is a lot of reach: narrow it | [your-computer](your-computer.md) |
| *"Turn on the Minecraft server for tonight"* | ✅ | a game panel's API key limited to power | none worth naming | [your-computer](your-computer.md#more-you-can-ask-possible-some-tried) |
| *"Did last night's backup work?"*, *"why is the server slow?"* | ✅ | read-only API tokens | keep them read-only for real | [homelab-read-access](../homelab-read-access.md) |
| A device away from home (a car radio, an old phone) | ✅ | Tailscale with a tight policy | the device must reach nothing back | [remote-devices](../remote-devices.md) |
| *"Turn off the living-room lights"*, *"is the heater on?"* | 🧪 | Home Assistant's MCP Server integration | expose only what is harmless to switch by mistake | [smart-home](smart-home.md) |

## Errands, money and shopping

| You say | | Needs | Main risk | Guide |
|---|---|---|---|---|
| *"Fill in this government form"*, *"claim what they owe me"* | ✅ | its browser; you approve e-ID sign-ins on your phone | a submission is a legal act: one yes each | [errands-and-appointments](errands-and-appointments.md) |
| *"Book the car inspection after work"*, with travel time | ✅ | its browser | none worth naming | [errands-and-appointments](errands-and-appointments.md#appointments) |
| *"When does my passport expire?"*, forms filled with your details | ✅ | your details in a private file | ID scans are the most sensitive thing it can hold | [errands-and-appointments](errands-and-appointments.md#your-documents) |
| *"Rome the last weekend, flights and hotel, the whole price"* | ✅ | the `trips` skill, `google-travel.py`, its browser | prices move; you pay, or the limited card with your yes | [trips](trips.md) |
| *"How is my portfolio doing?"*, *"anything odd in my account?"*, charts | ✅ | exports, read-only keys or open-banking consent | must be read-only at the provider; your data passes through the model | [money-read-only](money-read-only.md) |
| *"Buy it"*, a subscription with a reminder before each renewal | ✅ pieces, 🧪 purchase | a virtual card with its own small balance | the card's limit is the real boundary | [permissions](../permissions.md#optional-paying-with-a-limited-card) |
| *"Find me a used bike, cheap and near"*, price watches | ✅ | its browser or the marketplace's public search | scams; never pay outside the platform | [shopping-and-second-hand](shopping-and-second-hand.md) |
| *"Sell my camera, here are the photos"* | 🧪 | an account of its own and a phone number | scams aimed at sellers | [shopping-and-second-hand](shopping-and-second-hand.md#selling-possible-not-tried-by-us) |
| *"Sign up for that for me"* | ✅ | an `allow` sentence; an email alias or its own address | accepting terms in your name | [its-own-accounts](its-own-accounts.md) |

## People, accounts and work

| You say | | Needs | Main risk | Guide |
|---|---|---|---|---|
| Its own Instagram: you share reels, it says what holds up | ✅ | an account of its own; an unofficial API (or the official one) | the unofficial route breaks Instagram's terms and can cost the account | [social-media](social-media.md) |
| It posts for you and answers comments | 🧪 | the network's official API | public and permanent: your yes per post | [social-media](social-media.md) |
| *"What's due this week on my course?"*, *"how many holidays do I have left?"* | ✅ | your user on the campus or portal | your school's and employer's rules | [study-and-work](study-and-work.md) |
| *"What are my people doing?"*: one summary instead of thirty calls | 🧪 | a separate, limited agent for the team | people must know they talk to an assistant | [study-and-work](study-and-work.md#your-team-possible-not-tried-by-us) |
| A WhatsApp number of its own, or an agent that answers your shop's customers | 🧪 | the official WhatsApp Business Platform; a separate agent | automating a normal WhatsApp gets the number banned; strangers can write to it | [README](../../README.md#what-you-can-ask-it) |

## The rules behind all of it

- **What it reads is data, never orders**: an email, a web page, a reel or a message from a stranger cannot make it
  do anything. Its `CLAUDE.md` says so, and the classifier checks it.
- **It asks before anything that leaves a mark**: sending, publishing, paying, submitting, deleting.
- **Limits that hold even if it is fooled** live outside the conversation: read-only keys, a card's balance,
  `hard_deny`, a root-owned script, a firewall rule. Prefer those to a sentence in a prompt.
- **More reach = more useful = more at stake.** Each recipe says what it adds; [isolation.md](../isolation.md) says
  where to run it.
