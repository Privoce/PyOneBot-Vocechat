<!-- markdownlint-disable MD033 MD041 -->
<p align="center">
  <a href="https://github.com/Privoce/PyOneBot-Vocechat"><img src="./PyOneBot-Vocechat.png" width="200" height="200" alt="PyOneBot-Vocechat"></a>
</p>

<div align="center">

# PyOneBot-Vocechat

<!-- prettier-ignore-start -->
<!-- markdownlint-disable-next-line MD036 -->
_✨ Vocechat 平台的 OneBot v12 实现 ✨_
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
  <a href="">文档(WIP)</a>
  ·
  <a href="#快速开始">快速上手</a>
</p>

中文 | [English](README_EN.md)

> [!NOTE]
> 该项目目前处于早期开发阶段，如果您遇到任何问题，请提交issue反馈。


## 简介

基于 [pylibob](https://github.com/Herta-villa/pylibob) 的 Vocechat 平台 OneBot v12 实现。

## 功能特性

- 支持 OneBot v12 标准
- 支持多种通信方式（HTTP、WebSocket、WebSocket Reverse）
- 支持 Vocechat 消息的接收和解析
- 提供简单易用的配置接口
- 支持自定义消息处理和事件处理
- 内置日志记录和错误处理机制

> [!IMPORTANT]
> 当前版本仅在Vocechat服务器端0.4.2版本上进行过测试。

## 项目结构

- `core/`: 包含 Vocechat Webhook 处理和机器人动作实现的核心逻辑
  - `bot_actions.py`: 实现 OneBot 动作到 Vocechat API 的映射
  - `webhook.py`: 处理来自 Vocechat 的 Webhook 消息
  - `logger.py`: 日志记录模块
- `main.py`: 项目的入口文件，负责初始化 OneBot 实现和运行
- `config.py`: 配置文件，用于设置 OneBot 连接方式、Webhook 服务器地址和端口，以及 Vocechat 机器人信息
- `pylibob/`: 修改过的 Libonebot，提供 OneBot v12 标准实现
- `requirements.txt`: Python 依赖列表

## 快速开始

### 安装

本仓库对 pylibob 进行了修改，请不要使用 pip 直接安装 pylibob

1. 克隆本仓库：
```bash
git clone https://github.com/Privoce/PyOneBot-Vocechat.git
```

2. 安装依赖：
```bash
pip install -r requirements.txt
```

### 配置

通过修改 `.env` 文件进行配置  
首次启动时会自动生成.env配置文件  
根据提示修改.env文件后重新启动程序即可。

### 运行

```bash
python main.py
```

## 开发指南

### 自定义消息处理

在 `core/bot_actions.py` 中，你可以自定义如何处理接收到的消息和事件：

```python
# 示例：处理文本消息
async def handle_message(message):
    if message.type == "text":
        # 处理文本消息
        pass
```

### 错误处理

系统内置了错误处理机制，主要错误类型包括：
- 配置错误
- 网络连接错误
- API 调用错误
- 消息处理错误

错误日志会被记录到控制台和日志文件中。

## 故障排除

1. Webhook 无法接收消息
   - 检查 Vocechat 后台的 Webhook 配置是否正确
   - 确保服务器防火墙允许指定端口的访问
   - 检查网络连接是否正常

2. 机器人无响应
   - 确认 API Key 配置正确
   - 检查日志文件中的错误信息
   - 验证 Vocechat 服务器状态

## 开源协议

[GPL v3](https://github.com/Privoce/vocechat-web/blob/main/LICENSE)

## 特别鸣谢

[Herta-villa/pylibob](https://github.com/Herta-villa/pylibob)

## 贡献者

<a href="https://github.com/Privoce/PyOneBot-Vocechat/graphs/contributors">
  <img src="https://contrib.rocks/image?repo=Privoce/PyOneBot-Vocechat" />
</a>
