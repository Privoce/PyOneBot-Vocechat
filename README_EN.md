<!-- markdownlint-disable MD033 MD041 -->
<p align="center">
  <a href="https://github.com/Privoce/PyOneBot-Vocechat"><img src="./PyOneBot-Vocechat.png" width="200" height="200" alt="PyOneBot-Vocechat"></a>
</p>

<div align="center">

# PyOneBot-Vocechat

<!-- prettier-ignore-start -->
<!-- markdownlint-disable-next-line MD036 -->
_✨ OneBot v12 implementation for Vocechat platform ✨_
<!-- prettier-ignore-end -->

</div>

<p align="center">
  <a href="https://raw.githubusercontent.com/Privoce/PyOneBot-Vocechat/main/LICENSE">
    <img src="https://img.shields.io/github/license/Privoce/PyOneBot-Vocechat" alt="license">
  </a>
  <img src="https://img.shields.io/badge/OneBot-12-black?logo=data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAHAAAABwCAMAAADxPgR5AAAAGXRFWHRTb2Z0d2FyZQBBZG9iZSBJbWFnZVJlYWR5ccllPAAAAAxQTFRF////29vbr6+vAAAAk1hCcwAAAAR0Uk5T////AEAqqfQAAAKcSURBVHja7NrbctswDATQXfD//zlpO7FlmwAWIOnOtNaTM5JwDMa8E+PNFz7g3waJ24fviyDPgfhz8fHP39cBcBL9KoJbQUxjA2iYqHL3FAnvzhL4GtVNUcoSZe6eSHizBcK5LL7dBr2AUZlev1ARRHCljzRALIEog6H3U6bCIyqIZdAT0eBuJYaGiJaHSjmkYIZd+qSGWAQnIaz2OArVnX6vrItQvbhZJtVGB5qX9wKqCMkb9W7aexfCO/rwQRBzsDIsYx4AOz0nhAtWu7bqkEQBO0Pr+Ftjt5fFCUEbm0Sbgdu8WSgJ5NgH2iu46R/o1UcBXJsFusWF/QUaz3RwJMEgngfaGGdSxJkE/Yg4lOBryBiMwvAhZrVMUUvwqU7F05b5WLaUIN4M4hRocQQRnEedgsn7TZB3UCpRrIJwQfqvGwsg18EnI2uSVNC8t+0QmMXogvbPg/xk+Mnw/6kW/rraUlvqgmFreAA09xW5t0AFlHrQZ3CsgvZm0FbHNKyBmheBKIF2cCA8A600aHPmFtRB1XvMsJAiza7LpPog0UJwccKdzw8rdf8MyN2ePYF896LC5hTzdZqxb6VNXInaupARLDNBWgI8spq4T0Qb5H4vWfPmHo8OyB1ito+AysNNz0oglj1U955sjUN9d41LnrX2D/u7eRwxyOaOpfyevCWbTgDEoilsOnu7zsKhjRCsnD/QzhdkYLBLXjiK4f3UWmcx2M7PO21CKVTH84638NTplt6JIQH0ZwCNuiWAfvuLhdrcOYPVO9eW3A67l7hZtgaY9GZo9AFc6cryjoeFBIWeU+npnk/nLE0OxCHL1eQsc1IciehjpJv5mqCsjeopaH6r15/MrxNnVhu7tmcslay2gO2Z1QfcfX0JMACG41/u0RrI9QAAAABJRU5ErkJggg==" alt="OneBot 12">
  <img src="https://img.shields.io/badge/vocechat-Bot-lightgrey?style=social&logo=data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAABAAAAAQCAMAAAAoLQ9TAAAA7VBMVEUAAABgvvE6fPc7e/o3ePd00eyG6upvye5rxO1kuvFBiPQ3ePhXqPI3d/dd0f9KkvRChvVervB51+s2dfc+gfVVo/I3dfeA4utGjfWB4upXpPF00uxtxeyI7uk5fPZPmPOH7OhVpPFqxO42dvdkue9LlPSD5uphtvBKj/Nwyu1ht+9mve5SofJ00O1Pm/OH7Ok1cvdNmfJsx+6I7e2E7eiH8PCI7u5RnvNlu+9pwO5wy+1txu152Ox00ux93utFjPVBhvVer/E+gPZKk/RVo/JhtfBOmPNaqfGA4uo5e/aE6OlOmfNZqPFhtvBxzOyvuGCTAAAAN3RSTlMACGwe+sWnnYFSUUwmDgX99fXz8uvl5OPc29rZ19C/v7GoqKShoJyZgHRuaWRhVERDPDs6OBEP4XoFngAAAJlJREFUGNNVx1UCglAABdELGLTd3d0BFmA3+1+OxLPmaw7sBr6EFva2KLjNireLtt4s/bLrec51VgblTTOAz/WKBSamQmNKvOig1y0XGNSJ1QbYJqxSxMeQCKe3t49Yn6J4Hh8flFNAN2hkTMdny3vd2Anw/9kjYfzrawXg1OfXEQaoOr479ggA2pxYIo4PQRrVksFonpbsfwHbOylLMGOdagAAAABJRU5ErkJggg==" alt="Vocechat Bot">
</p>

<p align="center">
  <a href="">Documentation (WIP)</a>
  ·
  <a href="#quick-start">Quick Start</a>
</p>

[中文](README.md) | English

> [!NOTE]
> This project is currently in early development stage. If you encounter any issues, please submit an issue.


## Introduction

OneBot v12 implementation for Vocechat platform based on [pylibob](https://github.com/Herta-villa/pylibob).

## Features

- Supports OneBot v12 standard
- Supports multiple communication methods (HTTP, WebSocket, WebSocket Reverse)
- Supports Vocechat message receiving and parsing
- Provides simple and easy-to-use configuration interface
- Supports custom message and event handling
- Built-in logging and error handling mechanism

> [!IMPORTANT]
> Current version has only been tested with Vocechat server version 0.4.2.

## Project Structure

- `core/`: Contains core logic for Vocechat Webhook processing and bot actions
  - `bot_actions.py`: Implements mapping from OneBot actions to Vocechat API
  - `webhook.py`: Handles Webhook messages from Vocechat
  - `logger.py`: Logging module
- `main.py`: Project entry file, responsible for initializing OneBot implementation and running
- `config.py`: Configuration file for setting OneBot connection methods, Webhook server address and port, and Vocechat bot information
- `pylibob/`: Modified Libonebot providing OneBot v12 standard implementation
- `requirements.txt`: Python dependencies list

## Quick Start

### Installation

This repository has modified pylibob, please don't install pylibob directly via pip

1. Clone this repository:
```bash
git clone https://github.com/Privoce/PyOneBot-Vocechat.git
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

### Configuration

Configure via `.env` file (will be automatically generated on first run):
1. Modify the generated `.env` file according to the prompts
2. Restart the application after configuration changes

### Run

```bash
python main.py
```

## Development Guide

### Custom Message Handling

In `core/bot_actions.py`, you can customize how to handle received messages and events:

```python
# Example: Handling text messages
async def handle_message(message):
    if message.type == "text":
        # Handle text message
        pass
```

### Error Handling

The system has built-in error handling mechanism, main error types include:
- Configuration errors
- Network connection errors
- API call errors
- Message processing errors

Error logs will be recorded to console and log files.

## Troubleshooting

1. Webhook not receiving messages
   - Verify webhook configuration in Vocechat admin console
   - Check firewall settings for specified port
   - Ensure network connectivity is working properly

2. Bot not responding
   - Confirm API Key configuration is correct
   - Check error messages in log files
   - Verify Vocechat server status

## License

[GPL v3](https://github.com/Privoce/vocechat-web/blob/main/LICENSE)

## Special Thanks

[Herta-villa/pylibob](https://github.com/Herta-villa/pylibob)

## Contributors

<a href="https://github.com/Privoce/PyOneBot-Vocechat/graphs/contributors">
  <img src="https://contrib.rocks/image?repo=Privoce/PyOneBot-Vocechat" />
</a>
