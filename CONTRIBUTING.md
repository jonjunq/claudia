# Contributing

Issues and pull requests are welcome.

- **Every script should earn its place**: say which real failure it prevents (a stalled session, a lost reminder, a
  prompt nobody saw). If a Claude Code release makes a workaround unnecessary, removing it is a welcome contribution.
- **Keep it small and dependency-light**: bash, tmux, jq, curl. No daemons beyond the two services.
- **Never commit personal data**: no tokens, chat ids, emails, names or hostnames in templates, examples or issues.
- **Run the checks**: `tests/run-tests.sh` (shellcheck, JSON validity and an install into a temporary directory).
- Reports of how you use it (what works on your phone, which routines are worth it, what broke after an update) are
  as valuable as code: open an issue.
