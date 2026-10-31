# Changelog

## 1.1.0 — 2026-10-31

- `docs/homelab-read-access.md`: giving the assistant read-only visibility of Proxmox VE (`PVEAuditor` token),
  Proxmox Backup Server (`DatastoreAudit`) and dashboards, with a per-service firewall hole, credentials and
  certificate handling, a skill template and a test checklist, plus the threat model behind it.
- `docs/vetting-skills.md` and `templates/tools/vet-skill.sh`: scanning third-party skills with NVIDIA SkillSpector
  before installing them, skill folder by skill folder (whole-repo scores are dominated by false positives), pinned
  to the reviewed commit.

## 1.0.0 — 2026-10-31

First public version, distilled from an assistant in daily use since October 2026.

- `install.sh`: workspace, settings, systemd units and nightly cron for one user, without overwriting existing files.
- Workspace templates: `CLAUDE.md`, notes (`todo`, `yesterday`, `routines`, `diary/`), `assistant.env`.
- Scripts: restart loop with `--continue` and fallback, daily end of day + update + fresh conversation, status line
  for `/usage`, `/clear`, permission-prompt watcher, development-channel dialog acceptor, voice in (Groq / local
  faster-whisper) and out (ElevenLabs).
- Docs: setup, personality and memory, permissions, daily cycle, voice (with an experimental Discord call design),
  isolation, troubleshooting, comparison with Hermes Agent and a claude.ai Project.
