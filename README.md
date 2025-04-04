# Webex Alert Bot (Configurable UI)

![Docker Hub Build](https://github.com/mallen012/webex-alert-bot-config/actions/workflows/dockerhub.yml/badge.svg)
![GHCR Build](https://github.com/mallen012/webex-alert-bot-config/actions/workflows/ghcr.yml/badge.svg)
![Docker Pulls](https://img.shields.io/docker/pulls/mallen012/webex-alert-bot-config)
[![Docker Hub](https://img.shields.io/badge/Docker%20Hub-mallen012/webex--alert--bot--config-blue?logo=docker)](https://hub.docker.com/r/mallen012/webex-alert-bot-config)

This version of the Webex Alert Bot includes:

- REST API (`POST /alert`)
- WebSocket support (`alert`)
- Web UI with live alert sending and config editing
- UI form to update `.env` with a new Webex token and room ID
- Automatic app restart when config is updated

## Running

```bash
docker build -t webex-alert-bot .
docker run -d -p 5650:5650 --env-file .env webex-alert-bot
```

## Access the Web UI

Visit `http://<server_ip>:5650` in your browser.

## Environment Variables

| Variable       | Description              |
|----------------|--------------------------|
| WEBEX_TOKEN    | Your Webex bot token     |
| WEBEX_ROOM_ID  | Target room ID for alerts|

## License

MIT
