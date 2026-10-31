# Vetting skills before you install them

Skills, plugins and "the one CLAUDE.md that changes everything" arrive every day from videos and threads. Your
assistant runs with access to your email, calendar and files, so anything you install becomes part of it: its
instructions are followed, its scripts are run, its hooks fire on every tool call. Check before installing.

## The tool: SkillSpector

[NVIDIA SkillSpector](https://github.com/NVIDIA/SkillSpector) (Apache-2.0) scans a skill for prompt injection,
data exfiltration, credential access, risky code, hidden instructions, unpinned dependencies and more, and gives a
0–100 risk score with a recommendation (SAFE / CAUTION / DO NOT INSTALL).

- **Static mode (`--no-llm`) costs nothing**: pattern rules, AST and taint analysis, YARA signatures. It is what we
  use.
- An optional second stage asks an LLM to judge each finding in context; it needs an API key (several providers are
  supported) and costs money per scan.
- It never runs the code it scans. It is a filter, not a sandbox.

Install it in a **disposable VM or container**, not on the assistant's machine: you are about to download code you
do not trust yet.

```bash
pipx install 'git+https://github.com/NVIDIA/SkillSpector.git@<commit>'   # pin the version you use
skillspector scan <folder|git-url> --no-llm --format markdown --output report.md
```

## Scan the skill, not the repo

What gets installed is the folder with the `SKILL.md` (and the scripts it calls). A whole repository also has docs,
tests, CI, benchmarks and examples, and those trip almost every rule: a README that mentions `~/.claude/`, a test that
fakes a malicious prompt, a CI step with `sudo`.

What we measured: a well-known MIT-licensed skill repo scored **100/100 "DO NOT INSTALL"** scanned as a whole, and
**0/100 "SAFE"** for the actual skill folder. This repository, which is mostly documentation and shell scripts,
also scores high as a whole. So the whole-repo score tells you **where to look**, never what to decide.

[`templates/tools/vet-skill.sh`](../templates/tools/vet-skill.sh) does it for you:

```bash
templates/tools/vet-skill.sh https://github.com/<owner>/<repo>            # latest commit
templates/tools/vet-skill.sh https://github.com/<owner>/<repo> <commit>   # the exact commit you will install
```

It scans every folder that has a `SKILL.md` on its own, then the whole repo for reference, and saves a Markdown
report per skill plus the commit it looked at.

## Then read it yourself

The score is a triage. For anything you are going to install:

1. Read every finding in the skill's report and the lines it points to. Most CAUTION results are instructions
   that are fine in context ("edit files", "run the tests"); some are not.
2. Read the `SKILL.md` and every script it runs, in full. If it is too long to read, it is too long to trust.
3. Look for hooks (`hooks.json`, settings snippets) and anything that runs on every tool call or at session start.
4. **Pin the commit you reviewed** and install that commit, not "latest". An update is a new review.
5. Ask Claude to review it with you: paste the report and the files, ask what each instruction would make the
   assistant do with your email and files.

## Often you do not need to install anything

Big collections (hundreds of skills, agents, commands, hooks) cost context in every conversation and add hooks that
run constantly. For an assistant, the useful part of most of them is one idea. Copy that idea, in your own words, into
your `CLAUDE.md` or a small skill of your own, and you get the benefit without the code, the hooks or the updates.

Searching skill directories is fine; installing whatever they suggest without this review is exactly the risk this
page is about.
