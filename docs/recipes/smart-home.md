# Recipe: lights, plugs and the heating (Home Assistant)

> *"Turn off the living-room lights."* *"Is the heater on?"* *"Switch the plug of the router off and on again."*

**Possible, not tried by us.** Everything it needs exists; we do not run Home Assistant.

## What it needs

- [Home Assistant](https://www.home-assistant.io) running at home with your devices in it.
- Home Assistant's own **Model Context Protocol Server** integration, which lets an MCP client such as Claude Code
  control the entities **you expose to Assist** (Settings → Voice assistants → Expose), and nothing else. That is
  the limit you want: a long-lived access token on its own gives the same reach as the user who created it, and
  Home Assistant cannot restrict a token to some devices.
- The assistant's machine able to reach Home Assistant on your network.

Check the integration's current page in the Home Assistant docs before you start: names and steps change between
releases.

## Ask your assistant to set it up

> "I use Home Assistant at [address]. Help me connect you through its MCP Server integration, exposing only the
> living-room lights, the heater and the router plug. Tell me what I have to click in Home Assistant, and add the
> MCP server to your settings."

It will add the server with `claude mcp add` and test it by reading a state ("is the heater on?") before switching
anything.

## Permissions

Reading states can run alone. For switching, either let each action ask you (the default), or tell the classifier
which devices are yours:

```json
"The owner's Home Assistant (192.0.2.30) and the devices exposed to it are the owner's. Switching the exposed lights, plugs and heating on or off is authorised when the owner asks on Telegram."
```

## Risks

- ⚠️ Expose only what is harmless to switch by mistake. Leave out locks, alarms, garage doors, ovens and anything
  that could hurt someone or let someone in.
- A message in an email or a web page could ask it to switch something: the sentence above ties switching to your
  request, and the assistant treats what it reads as data.
- If Home Assistant is reachable from the internet, that is a separate risk; the assistant does not need it to be.
