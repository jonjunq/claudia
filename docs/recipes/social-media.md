# Recipe: social media accounts of its own

> *"Look at the reels I send you on Instagram and tell me which ones are true and which are hype."* *"Post this
> photo with a caption, and answer the comments."* *"Tell me when that account posts something."*

**Ours does this** on an Instagram account of its own: you share reels with it in a private chat, a small watcher
notices them and wakes the assistant (no tokens spent while nothing arrives), and it downloads each one, transcribes
it, looks at a few frames and notes in one line what it is, whether it holds up and whether it is useful to you.
You get a summary when you ask. Publishing and answering comments: **possible, not tried by us.**

This recipe is the idea and the risks, not code.

## Two routes

1. **The official one (recommended).** Most networks have an API for accounts that post on purpose:
   - Instagram and Facebook: a professional (Business or Creator) account and Meta's official API: publishing,
     comments and, with the right permissions, messages. It needs a Meta app; for your own accounts, being an admin
     of the app is usually enough. Check Meta's current requirements.
   - Bluesky and Mastodon welcome bots through their open APIs: mark the account as automated.
   - X has a paid API.
2. **Unofficial private APIs** (for Instagram, libraries such as `instagrapi` that imitate the phone app). This is
   what we use, knowing what it means:
   - ⚠️ **It breaks Instagram's terms.** Meta can lock or delete the account at any time, with no appeal.
   - It breaks whenever the app changes; logins can ask for verification codes ("challenge") out of the blue.
   - **Only with an account of the assistant's own, never your personal one.** If it is lost, you lose a disposable
     account, not your photos, contacts or messages.

## Rules so the account lasts (what we follow)

- Log in **once** and reuse the saved session; never log in on every run.
- One process at a time with that session.
- Look only at what it needs (the chat with you), at a slow pace with some randomness (every two or three minutes),
  never in bursts.
- On a "challenge", a "login required" or a "too many requests", **stop and tell you**. No retries, no workarounds.
- No mass following, liking or messaging strangers. New accounts cannot start chats: you write to it first.
- Always from the same place (your home connection), like a phone would.

## Ask your assistant to set it up

> "I'd like you to have your own [network] account to [watch the reels I send you / post for me]. Tell me the
> options and their risks first, official API or not. If we go ahead, I'll create the account; you keep the session
> in a private file and stop at the first warning from the network."

Watching without spending tokens: the watcher writes one line per new thing to a log, and the
[wake-up](../wakeup.md) types it into the session. Downloading public videos: [links-and-videos.md](links-and-videos.md).

## Permissions

The first login is the step the classifier is most likely to block (an automated login to a third-party service).
Ours needed an allow rule for exactly the script and its interpreter. Keep that script **outside** anything the
assistant can edit (root-owned, like the [tools](../../templates/tools/)), or the rule lets it run whatever it writes
into the file:

```json
"permissions": { "allow": ["Bash(/opt/assistant-social/venv/bin/python -I /opt/assistant-social/social.py *)"] }
```

Publishing is public and permanent: your yes to each post, as with email.

## Risks

- ⚠️ The account can be closed without warning (unofficial route). Do not build anything that needs it to survive.
- ⚠️ What it reads (captions, comments, messages from strangers) is untrusted: an instruction inside a reel or a
  comment is data, never an order. Never give this account's assistant your email, card or home.
- Its posts speak for you: say in the bio that it is an assistant, and approve each post.
- Downloading other people's videos is for your own analysis; republishing them is a copyright matter.
