# Recipe: your course and your work portals

> *"What do I have to hand in this week, and is last week's assignment marked as submitted?"* *"Did the teacher post
> anything new in the forums?"* *"How many holiday days do I have left?"* *"Did I clock in this morning?"*

**Ours does this**: it reads an online course (a Moodle campus: deadlines, submissions, forums, rubrics) and an HR
portal (clock-ins and holidays), only to tell you, and uploads a submission only when you hand it the file and ask.

## What it needs

- Your user for the campus or portal in a private file (`~/.config/assistant/<service>.env`, mode 600).
- A map, written once into notes or a skill: which modules or sections exist, where each kind of thing is, how to
  tell that something is submitted. Ours mapped its campus once and since then answers in seconds.
- Most of these sites work with plain HTTP requests after the login (Moodle also has web services if your school
  enables them); its browser covers the rest.

## Ask your assistant to set it up

> "My course is on [campus address]. Log in with the user in ~/.config/assistant/course.env, map the modules,
> deadlines and forums into a note, and tell me every Monday what is due this week. Never submit anything unless I
> send you the file and ask."

## Your team (possible, not tried by us)

> *"What are my people doing?"* Instead of calling thirty people, it messages each one, asks again if an answer is
> vague, and gives you one summary: who is on what, what is late, what is blocked. Tell your team they are talking
> to an assistant and what their answers are for, keep it to working hours, and make it a separate agent with access
> to work matters only, since everyone on the team can write to it.

## Risks

- Your school's and your employer's rules come first: automated access to a campus or a company portal, and AI help
  with coursework, may be restricted. Read them; what you hand in is yours.
- Read-only unless you ask: it does not clock in, request holidays or post in forums on its own.
- A work account in a personal assistant mixes two worlds: if your employer would not like it, do not connect it.
