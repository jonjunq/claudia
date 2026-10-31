# Daily cycle, routines and commands

## The nightly end of day

`/usr/local/sbin/assistant-daily-restart`, run by cron as root (05:45 by default, in `/etc/cron.d/assistant`):

1. Types `END OF DAY (automatic, do not message the owner)…` into the session.
2. The assistant follows the "End of day" section of `CLAUDE.md`: saves lasting facts to memory, cleans up
   `notes/todo.md`, writes `notes/diary/<date>.md` and, last, overwrites `notes/yesterday.md`.
3. The script waits until `yesterday.md` changes (up to 12 minutes) plus 45 seconds, and logs whether it did.
4. It creates `~/assistant/.new-session`, runs `claude update` as the user, and restarts the service.
5. `start.sh` sees `.new-session` and starts a fresh conversation with a first prompt that tells it to schedule
   today's routines and wait quietly.

It runs as root on purpose: the assistant cannot change or skip it. Everything is logged to
`~/assistant/restarts.log`; in three weeks of daily use ours logged one "summary NOT updated" (the very first
night) and every other night OK.

Why restart at all? A conversation that runs for days fills its context window, gets slower, and each reply costs
more of your limits. A clean start with a 40-line summary is cheaper and, in practice, nobody notices.

## Routines

Scheduled tasks created inside a Claude Code session (`CronCreate`) live only as long as the session, and recurring
ones expire after seven days ([scheduled tasks](https://code.claude.com/docs/en/scheduled-tasks)). So routines are
written down instead, in `notes/routines.md`:

```
- 08:00 (every day) — Morning summary: today's calendar, items due today, new email since yesterday.
- 18:00 (Mon-Fri) — If there is a delivery being tracked, check it and say only if something changed.
```

and at the start of every conversation the assistant schedules **one-shot** tasks for the ones due today. When you
ask for a new routine ("every Monday at 9 remind me to…") it edits `routines.md` itself. One-off reminders go to
`notes/todo.md` with date and time and are rescheduled each morning while still due.

Tips from the morning summary we use:

- Order it the way you read: calendar, what is due, email.
- Say "these are the new emails since the last summary", or it reads as if your inbox only had three.
- Keep it to a screen. Offer drafts instead of writing them unasked.

## `/usage`

The assistant cannot see its own terminal, where Claude Code shows context and plan usage. `bin/statusline.sh` is
configured as the status line: Claude Code feeds it a JSON with the model, the context window and, on subscription
plans, the 5-hour and weekly `rate_limits`; the script saves them to `~/assistant/state.json`. `/usage` from Telegram
makes the assistant read that file and answer in two lines, with reset times in your time zone. It also warns you on
its own past 70 % of the weekly limit or 80 % of the 5-hour one. The data is as of its last reply.

## `/clear`

To start fresh mid-day without waiting for the night: send `/clear`. The assistant replies, saves what is in progress
to `notes/todo.md` and lasting facts to memory, and as its last step runs `bin/clear-context.sh`. That script detaches
a small background job which waits until the current turn ends, types `/clear` into the tmux session and sends the
first message of the new conversation (reschedule the missing routines, then confirm on Telegram). The service is not
restarted.

## Keeping Claude Code up to date

The daily restart runs `claude update` and logs the version before and after. The native installer also enables
auto-updates; the restart makes sure the new version is actually the one running.
