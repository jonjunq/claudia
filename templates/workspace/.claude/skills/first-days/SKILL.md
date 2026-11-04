---
name: first-days
description: Your first weeks with __OWNER__ - offering, one at a time, the things you can do or set up for them, and remembering what they said. Load it at the start of each conversation while notes/first-days.md says "phase: active", and whenever __OWNER__ asks what you can do.
---

# First weeks: show __OWNER__ what you can do

__OWNER__ may not know what you can do, or that most of it is a message away: they should not have to read any
docs. For the first weeks, offer the things below yourself, **one at a time, at a natural moment**, and keep track
in `notes/first-days.md` so you never insist on something they declined.

## How to offer
- **One offer a day at most**, and only at a natural moment: right after you helped with something related, or in
  a calm moment of the day (after the morning summary). Never in the middle of something urgent or serious, never
  several in one message, never as the first line of an answer to something else.
- **Plain words, for someone who is not technical.** No jargon ("n8n" is "a small free automation tool I install
  here"). Say what they gain, what it costs (money, time, a step only they can do) and the risk if there is one.
  End with a yes/no or numbered options, and an example of how to ask for it later.
- Like this: "💡 Did you know I can … ? It would mean … . It costs … . Shall I set it up? 1 yes · 2 later · 3 no".
- **Check before offering**: if it is already set up, mark it `already` and offer nothing; if it would be useful to
  know, mention it in one line the next time it fits ("by the way, you can send me voice notes").
- They say yes: do it now (or schedule it), following the item's guide; things only they can do, explain step by
  step. They say no: mark `no` and never offer it again unless they bring it up. "Later": mark `later` with the date;
  you may ask once more after a week or more, then it is `no`.
- Things that need something they may not have (a TV, a server, a shop) are offered only when it comes up: if they
  mention it, or you see it in their email or calendar. Do not ask "do you have a smart TV?".
- If they ask "what can you do?", answer with a short grouped list from the catalog (that is the one time a list is
  right), then continue one at a time.

## The state file: `notes/first-days.md`
Read it at the start of each conversation; update it after each offer. One line per item:
`- <id>: <already | offered YYYY-MM-DD | yes YYYY-MM-DD | no YYYY-MM-DD | later YYYY-MM-DD> — a few words`.
- The first time (`started:` is empty): write today's date, check what is already set up and mark it `already`.
  Introduce yourself in 3-4 lines (who you are, that they can write or talk to you any time, one example), with no
  offer in that message. If `notes/diary/` has more than two weeks of pages, they know you: skip the introduction.
- **The phase ends** when every item has an answer, or 4 weeks after `started` (2 if they already knew you): write
  `phase: done`, and send one short message: they can always ask "what can you do?", and you will only suggest
  things when they fit. From then on, offer something only when it fits a real need of theirs, or when an update
  brings something new (once).

## Catalog
Suggested order for the common ones; the "when it comes up" ones, whenever they do. Guides in
`/usr/local/share/assistant/docs/`.

**Everyday (offer early)**
- `connectors` — email, calendar and Drive. Check: do you have the Gmail / Google Calendar tools? Missing: only
  __OWNER__ can connect them, in claude.ai → Settings → Connectors; guide them. Gain: summaries, drafts, agenda.
- `morning` — the morning summary (agenda, what is due, emails that matter) is in `notes/routines.md`: ask what time
  suits them and what they want in it. "Every morning at 8 I can send you your day. Is 8 good?"
- `reminders` — "remind me…" and recurring routines ("every Monday, remind me of the bins"). Nothing to set up:
  tell them the first time they mention a date or a chore.
- `voice` — voice notes: "you can talk to me instead of typing: send a voice note, I understand it in a second".
  Check: a key in `~/.config/assistant/keys.env` (`GROQ_API_KEY` uncommented) or a local engine (voice.md). Cost:
  a free Groq account, or a local engine that is slower. Risk: the audio goes to that service. Replies with my own
  voice (`speak.sh`, ElevenLabs, paid beyond a small free tier): only if they liked voice notes.
- `recall` — "ask me about anything we talked about weeks ago, I can look it up". Nothing to set up: say it once.

**Automations that cost nothing while idle (n8n)**
- `email-watch` — instead of you checking the inbox every so often (each check is a turn of their subscription,
  usually for nothing), a free automation tool watches it 24/7 and wakes you only when an email arrives; you tell
  them right away only if it matters. "I'd hear about an important email within seconds, day and night, and it
  costs you nothing while nothing arrives." Cost: installing n8n (you, if you have root; otherwise one command
  for them) and a Gmail app password (needs 2-step verification; revocable any time). Risk: n8n holds a password
  that can read their email: it stays on this machine. Guides: n8n.md, wakeup.md. Check: is n8n running, do you get
  email notices?
- `updates` — "so I keep improving: once a day it checks whether there is a new version of me, and I tell you what
  it brings. I never update without your yes." Offer after the first week, or right after n8n is set up. Skill
  `updating`.
- `page-watch` — when they mention a parcel, an order, a price or something out of stock: "I can watch that page
  and tell you when it changes, and the watch switches itself off when it is delivered". n8n.md.

**When it comes up**
- `browser` — websites with no app: forms, bookings, government e-services, downloading a document. "I can fill
  that in on the website for you; if a captcha or a sign-in shows up, I send you a link and you solve it from your
  phone." browser.md (remote window: optional, ask the admin if it is not there).
- `errands` — claims and paperwork: "I can claim that refund for you: I find the form, fill it in, keep the
  reference, watch for their reply in your email and remind you if they do not answer." Their details and their
  yes before sending anything.
- `tv-media` — if they have a smart TV, a projector or a media server: "tell me 'put YouTube on the TV' and I do
  it", "ask me for a film and I'll have it ready on your media server". Needs the device's developer mode or the
  server's API, and an `autoMode` sentence (permissions.md).
- `home` — if they use Home Assistant: "I could switch lights and plugs or tell you if the heater is on". Not
  something this kit ships: a Home Assistant token limited to those devices and a short skill. Say it is possible,
  not tested.
- `home-server` — if they have a home server: "I can keep an eye on it and tell you if a backup failed or a disk
  is filling up, without being able to change anything". homelab-read-access.md.
- `pc-power` — turning a computer on or off at their request (wake-on-LAN, or one narrow permission on that one
  machine). Only if they ask for something like it.
- `trips-payments` — when they plan a trip or a purchase: "tell me 'we want to go to the coast that weekend': I find
  options, show you two or three with prices, and once you say yes I can pay with a virtual card that has its own
  small limit". Off by default; the card is theirs to create and its limit is the risk (permissions.md, "paying with
  a limited card"). New: say so honestly.
- `own-accounts` — accounts of your own (an email alias, social media): "I could have my own account and post or
  answer for you, always showing you the post before it goes out". Needs an `allow` sentence (permissions.md);
  publishing is public, so their yes for each post.
- `whatsapp` — a number of your own on WhatsApp, or for a business an agent that answers their customers (opening
  hours, stock, orders, appointments) and passes to them what it does not know. Two things to say plainly: only
  through the official WhatsApp Business Platform (automating a normal WhatsApp breaks its rules and the number can
  be banned); and the agent that talks to strangers must be a separate, limited one (no access to their email,
  card or home), because anyone can write to it with trick instructions. Possible, not part of this kit.
- `team` — if they manage people: "instead of calling 30 people, ask me 'what is everyone doing?': I message each
  one, ask a follow-up if an answer is vague, and give you one summary (who is on what, what is late, what is
  blocked)". Say plainly: the team must know they are talking to an assistant and what their answers are used for;
  only within working hours; and, as with customers, a separate agent with access to work matters only. Possible,
  not part of this kit.
- `remote-device` — a device away from home (a car radio, an old phone): remote-devices.md.
- `skills` — before installing a skill someone shares with them: check it first (vetting-skills.md).
