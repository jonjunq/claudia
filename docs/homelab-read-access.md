# Eyes on your server, no hands

An assistant gets much more useful once it can answer "is the backup from last night there?", "why is the game
server down?" or "how full is the disk?" by looking, instead of guessing or asking you to check. This guide gives it
that visibility **read-only**, one service at a time, without opening your network to it.

Examples use Proxmox VE and Proxmox Backup Server because that is what we run; the pattern (scoped token + narrow
firewall hole + a skill that documents the endpoints and the rules) applies to any API.

## Threat model first

The assistant reads email and web pages written by strangers. A message can try to talk it into doing something
(prompt injection), and auto mode's classifier catches a lot but not everything. So assume that **anything it can
read could one day be sent somewhere else**, and decide accordingly:

- **Read-only everywhere.** A token that can only look cannot be tricked into deleting a backup or stopping a VM.
  If you want one narrow write (e.g. power one VM on and off), give exactly that permission on exactly that object.
- **Only what it needs.** Infrastructure state (which machines run, load, last backup) is low value to an attacker.
  Source code, customer data, business documents and credentials are not: do not hand those to an assistant that
  reads your inbox, even read-only.
- **Prove it.** After setting up each token, try a write with it and check you get `403` (see the checklist).
- **Changes go through a human** (or a separate admin agent that does not read untrusted content). The assistant
  can see, explain and recommend; it does not act on infrastructure.

## 1. Proxmox VE: see the whole cluster

Create a user with no password, a privilege-separated API token, and give **both** the `PVEAuditor` role on `/`
(with privilege separation, the token gets the intersection of the user's and the token's permissions):

```bash
pveum user add assistant@pve --comment "Assistant: read-only"
pveum user token add assistant@pve read --privsep 1        # prints the secret once
pveum acl modify / --users assistant@pve --roles PVEAuditor
pveum acl modify / --tokens 'assistant@pve!read' --roles PVEAuditor
```

`PVEAuditor` (`Sys.Audit`, `VM.Audit`, `Datastore.Audit`, `Pool.Audit`, `SDN.Audit`, …) can list nodes, VMs and
containers with their status, CPU, memory, disk and uptime, read their configuration, see storage usage and the task
log (backups, starts, migrations). It **cannot** start, stop or change anything, open consoles, read the host's
syslog (`Sys.Syslog`), or read files inside guests.

A narrow extra, if you want it: a custom role with `VM.Audit` + `VM.PowerMgmt` on `/vms/<id>` only lets it power one
VM on and off ("turn on the game server") and nothing else.

```bash
curl -s --cacert "$PVE_CA" -H "Authorization: PVEAPIToken=assistant@pve!read=<secret>" \
  "https://<pve-host>:8006/api2/json/cluster/resources"          # everything: nodes, guests, storage
#   .../nodes/<node>/status          load, memory, uptime of a node
#   .../nodes/<node>/lxc/<id>/config  configuration of a container (qemu/<id>/config for VMs)
#   .../nodes/<node>/tasks?limit=20   recent tasks
```

## 2. Proxmox Backup Server: check the backups exist

```bash
proxmox-backup-manager user create assistant@pbs --comment "Assistant: list backups only"
proxmox-backup-manager user generate-token assistant@pbs read      # prints the secret once
proxmox-backup-manager acl update /datastore/<store> DatastoreAudit --auth-id assistant@pbs
proxmox-backup-manager acl update /datastore/<store> DatastoreAudit --auth-id 'assistant@pbs!read'
```

`DatastoreAudit` lists backup groups and snapshots (with their size and verification state), namespaces and
datastore usage. It cannot restore, delete, prune or run garbage collection.

```bash
P() { curl -s --cacert "$PBS_CA" -H "Authorization: PBSAPIToken=assistant@pbs!read:<secret>" "https://<pbs-host>:8007/api2/json$1"; }
P /admin/datastore/<store>/groups                 # one entry per machine, with last-backup (Unix time) and count
P "/admin/datastore/<store>/groups?ns=<namespace>" # backups kept in a namespace
P /admin/datastore/<store>/status                 # used / total
```

The useful question for it to answer is "which machine has no backup newer than 24–48 h?", minus the ones you turned
off or deleted on purpose (write those down in the skill).

## 3. Dashboards and other read APIs

Uptime monitors, metrics dashboards, a status page, a build roadmap: give it a **read-only** account or an endpoint
that needs none, and the URL. If the tool has no read-only role, think twice before giving it an admin account.

## 4. Firewall: one hole per service

Keep the "block the local network" rule from [isolation.md](isolation.md) and add one `ACCEPT` per `host:port`
**above** the drops:

```
OUT ACCEPT -dest <pve-host> -p tcp -dport 8006      # Proxmox VE API
OUT ACCEPT -dest <pbs-host> -p tcp -dport 8007      # Proxmox Backup Server API
OUT ACCEPT -dest <monitor-host> -p tcp -dport <port> # read-only dashboard
OUT DROP   -dest 192.168.0.0/16                     # ...then the private ranges, as before
```

Not the whole host, not SSH. A timeout to anything else is then expected, and the skill should say so, so it does
not go "investigating" your network.

## 5. Credentials and certificates

- Put tokens in one env file, mode `600`, owned by the assistant's user (e.g. `~/.config/homelab/homelab.env`), never
  in `CLAUDE.md`, notes or memory. Tell it to load the file **inside the same command** that uses it
  (`set -a; . ~/.config/homelab/homelab.env; set +a; curl …`), so values never appear in its messages, and never to
  print or send them.
- Proxmox certificates are self-signed and usually issued for the host name, not the IP. Copy the CA (or the
  server's certificate) next to the env file, add a hosts entry so the name resolves (`<ip> <pve-host>` in
  `/etc/hosts`), and use `--cacert` with the name. Do not teach it `curl -k`.

## 6. A skill that says what and how

A small skill (e.g. `~/assistant/.claude/skills/homelab/SKILL.md`) with a description that triggers on servers,
backups, machines, outages, and a body with:

- what it can reach (the list of endpoints above, with the exact `curl` lines) and what it cannot;
- the rules: queries are free; **a 401/403 means no: tell the owner, do not look for another way**; changes go to the
  owner (or to whoever administers the servers);
- what is normal: machines that are off on purpose, a node that is often down, deleted guests;
- how to answer: the state it saw and when, not what it remembers.

## Checklist

- [ ] Read works: `cluster/resources` lists your guests; `groups` lists your backups.
- [ ] Write fails: e.g. `curl -X POST …/nodes/<node>/lxc/<id>/status/stop` → `403`; `curl -X DELETE
      "…/admin/datastore/<store>/snapshots?backup-type=ct&backup-id=<id>&backup-time=1"` → `403`;
      `curl -X POST …/admin/datastore/<store>/gc` → `403`.
- [ ] Anything not opened in the firewall times out from the assistant's machine.
- [ ] The env file is `600` and not referenced from `CLAUDE.md` or notes.
- [ ] Ask it "is everything backed up?" and "what's using the most memory?" and check the answers against the web UI.
