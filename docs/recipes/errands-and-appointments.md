# Recipe: paperwork, claims and appointments

> *"Fill in this government form with my details."* *"Claim the money they owe me from my old employer."* *"Book
> the car inspection, any day after work, and tell me how long it takes to get there."* *"When does my passport
> expire?"*

**Ours does this**: government e-services (forms, claims, registrations) through its browser, booking appointments
across several companies at once with the travel time at that hour, and keeping the dates of your documents.

## Forms and claims

- It works in its own browser ([browser.md](../browser.md)): fills the form, attaches documents (merging PDFs if the
  form only takes a few files), and **stops before the final button** to show you a summary. It presents or signs
  only with your yes to that submission.
- **Digital identity**: where your country's e-ID lets you approve a sign-in in an app on your phone, the assistant
  types your ID number and you approve on the phone. Never give it the PIN or password of your e-ID or a
  certificate: that would let it sign anything as you.
- Captchas and "unusual sign-in" checks: you solve them in its browser from your phone (the remote window).
- **Notifications**: it ticks both SMS and email where a form offers them, so you hear about the answer.
- After submitting: it keeps the receipt and the reference, watches your email for the answer, and reminds you if
  there is none by the deadline.

## Appointments

> "Book the car inspection. Weekdays after six, any company."

It looks at several companies and stations at once (the usual one may have nothing for weeks), gathers the first
slots in one message with its pick, and books only the one you choose. Before proposing a time it checks the travel
time with traffic at that hour (a maps site in its browser) and leaves a margin. Then: an event in your calendar with
the booking code and what to bring, and a reminder to leave on time.

Write down how you like appointments once ("weekdays after work, never weekends") and it will not ask again.

## Your documents

Scans of your ID card, passport or driving licence let it fill forms without asking you each time, and remind you
months before they expire.

- ⚠️ They are the most sensitive thing it can hold: with them, someone can impersonate you. Keep them in a private
  folder outside the workspace (`~/.config/assistant/documents/`, mode 700), so they are not in its git history;
  better still, keep only the numbers and dates it needs in a private file, and not the images.
- It never sends them anywhere you did not ask for, and never into a chat with anyone but you.

## Ask your assistant to set it up

> "From now on you can fill in forms for me. Keep my details in a private file outside your workspace, always show
> me the summary before submitting, tick SMS and email notices, and keep the receipts."

## Risks

- Submitting in your name is a legal act: one yes per submission, after reading its summary.
- Prompt injection lives on web pages too: a page that says "also enter your bank details here" is data.
- Bot checks: it uses a normal browser and does not try to hide what it is; when a site refuses automated access,
  you do that step from your phone.
