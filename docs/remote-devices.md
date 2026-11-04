# Devices away from home, over Tailscale

Optional. For when you want the assistant to reach a device that is not on your home network, for example an
Android car radio or an old phone on mobile data, and nothing else.

The risk is the usual one with a VPN: with [Tailscale](https://tailscale.com)'s default policy every node can reach
every other node, and if one of your machines is a **subnet router** for your LAN, a new node sees your whole home
network the moment it joins. A device that lives in a car, or the assistant itself, should not get that. So the
assistant joins with its own tag, and the policy only lets it open specific ports on that device; the device can
open nothing.

## The assistant's node

- Install Tailscale on the assistant's machine in **userspace mode**, so it creates no network interface and
  nothing else on that machine uses the tailnet: in `/etc/default/tailscaled`,
  `FLAGS="--tun=userspace-networking --socks5-server=localhost:1055"`.
- Join with a tag of its own and without your routes or DNS:
  `tailscale up --advertise-tags=tag:assistant --accept-routes=false --accept-dns=false --operator=<user>`.
  `--operator` lets the assistant's user run `tailscale status` and `tailscale nc` without root. It must not run
  `tailscale up`, `set` or `logout`; say so in its notes.
- In userspace mode outgoing connections go through Tailscale itself, with `tailscale nc` as an SSH `ProxyCommand`:
  `ssh -p 8022 -o ProxyCommand="tailscale nc %h %p" <device-name>`. For ADB, forward it over that SSH
  (`ssh -L 5555:localhost:5555 …`, then `adb connect localhost:5555`) or point adb at the SOCKS5 proxy on port 1055.
- `--advertise-tags` needs an admin (the tag's owner) to log the node in; or use an auth key that carries the tag.

## The policy

In the admin console (Access controls), with [grants](https://tailscale.com/kb/1324/grants) and
[tests](https://tailscale.com/kb/1337/policy-syntax#tests) so a later edit cannot quietly open it up. Ours, with
example tags:

```hujson
{
  "tagOwners": {
    "tag:assistant": ["autogroup:admin"],   // the assistant: reaches only tag:device, on two ports
    "tag:device":    ["autogroup:admin"],   // the remote device: starts nothing towards the tailnet
  },
  "grants": [
    // Your own devices (untagged) keep what they had: everything, including the LAN behind a subnet router.
    {"src": ["autogroup:member"], "dst": ["*"], "ip": ["*"]},
    // Assistant -> device: ADB (5555) and SSH (8022, e.g. Termux's sshd). Nothing else, and nothing back.
    {"src": ["tag:assistant"], "dst": ["tag:device"], "ip": ["tcp:5555", "tcp:8022"]},
  ],
  "tests": [
    {"src": "tag:assistant", "accept": ["tag:device:5555", "tag:device:8022"],
     "deny": ["tag:device:22", "10.0.0.1:80", "<a server of yours>:22"]},
    {"src": "tag:device", "deny": ["tag:assistant:22", "10.0.0.1:80", "<a server of yours>:22"]},
  ],
}
```

Replace `10.0.0.1` with an address on your LAN and add one of your servers, so the tests prove that neither tag
reaches them. Tailscale refuses to save a policy whose tests fail. Tagged nodes do not get the `autogroup:member`
grant, which is what keeps them out. If your first rule is narrower than "everything", keep yours: only the two
tagged lines matter here.

## Adding the device

- Create a **one-off, pre-authorised auth key with `tag:device`** (Settings → Keys) and give it to whoever sets up
  the device; it joins already tagged. A key is a secret: send it on its own, and let it expire.
- Without a key, the device logs in with your account and you tag it right after in the admin console (Machines →
  the device → Edit ACL tags). **Until it is tagged it is one of your devices and sees everything**, so do not wait.
- On Android: the Tailscale app, then turn on "Always-on VPN" if offered and exempt Tailscale from battery
  optimisation, or it drops off after a while. For SSH, [Termux](https://f-droid.org/packages/com.termux/) from
  F-Droid (the Play Store build is abandoned): `pkg install openssh`, `passwd`, `sshd`; then put the assistant's
  public key in Termux's `~/.ssh/authorized_keys`.

## Check it

From the assistant's machine, as its user: `tailscale status` lists the device with its tag;
`tailscale nc <device> 8022` connects; `tailscale nc <one of your servers> 22` and a LAN address do not. From the
device, nothing on the tailnet answers.

What the assistant may do on the device (and what never: the car's own controls, for instance) goes in its notes
and in your `autoMode` sentences ([permissions.md](permissions.md)), as for any other machine of yours.
