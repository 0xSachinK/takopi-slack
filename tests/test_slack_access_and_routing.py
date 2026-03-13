from __future__ import annotations

import types
from pathlib import Path

import pytest

from takopi.api import ConfigError
from takopi.runner_bridge import ExecBridgeConfig
from takopi_slack_plugin.bridge import (
    _is_allowed_channel,
    _is_allowed_user,
    _resolve_command_channel,
    _should_process_socket_message,
)
from takopi_slack_plugin.client import SlackMessage
from takopi_slack_plugin.commands.reply import make_reply
from takopi_slack_plugin.config import SlackTransportSettings
from tests.slack_fakes import FakeTransport


def test_from_config_parses_access_and_reply_mode() -> None:
    cfg = {
        "bot_token": "xoxb-1",
        "channel_id": "C123",
        "app_token": "xapp-1",
        "allowed_user_ids": ["U123"],
        "allowed_channel_ids": ["C999", "C123"],
        "reply_mode": "channel",
    }
    settings = SlackTransportSettings.from_config(cfg, config_path=Path("/tmp/x"))

    assert settings.allowed_user_ids == ["U123"]
    assert settings.allowed_channel_ids == ["C123", "C999"]
    assert settings.reply_mode == "channel"


def test_from_config_parses_channel_wildcard() -> None:
    cfg = {
        "bot_token": "xoxb-1",
        "channel_id": "C123",
        "app_token": "xapp-1",
        "allowed_channel_ids": ["all"],
    }
    settings = SlackTransportSettings.from_config(cfg, config_path=Path("/tmp/x"))

    assert settings.allowed_channel_ids == ["*"]


def test_from_config_rejects_invalid_reply_mode() -> None:
    cfg = {
        "bot_token": "xoxb-1",
        "channel_id": "C123",
        "app_token": "xapp-1",
        "reply_mode": "sideways",
    }
    with pytest.raises(ConfigError):
        SlackTransportSettings.from_config(cfg, config_path=Path("/tmp/x"))


def test_is_allowed_channel_checks_allowlist() -> None:
    cfg = types.SimpleNamespace(allowed_channel_ids=["C123", "C999"])

    assert _is_allowed_channel(cfg, "C999") is True
    assert _is_allowed_channel(cfg, "C000") is False


def test_is_allowed_channel_accepts_wildcard() -> None:
    cfg = types.SimpleNamespace(allowed_channel_ids=["*"])

    assert _is_allowed_channel(cfg, "C999") is True


def test_is_allowed_user_checks_allowlist() -> None:
    cfg = types.SimpleNamespace(allowed_user_ids=["U123"])

    assert _is_allowed_user(cfg, "U123") is True
    assert _is_allowed_user(cfg, "U999") is False
    assert _is_allowed_user(cfg, None) is False


def test_should_process_socket_message_requires_thread_or_mention_in_channels() -> None:
    top_level = SlackMessage(
        ts="1",
        text="hello",
        user="U1",
        bot_id=None,
        subtype=None,
        thread_ts=None,
        channel_id="C1",
    )
    in_thread = SlackMessage(
        ts="2",
        text="reply",
        user="U1",
        bot_id=None,
        subtype=None,
        thread_ts="1",
        channel_id="C1",
    )

    assert (
        _should_process_socket_message(
            {"type": "message", "channel_type": "channel"},
            top_level,
        )
        is False
    )
    assert (
        _should_process_socket_message(
            {"type": "message", "channel_type": "channel"},
            in_thread,
        )
        is True
    )
    assert (
        _should_process_socket_message(
            {"type": "app_mention", "channel_type": "channel"},
            top_level,
        )
        is True
    )
    assert (
        _should_process_socket_message(
            {"type": "message", "channel_type": "im"},
            top_level,
        )
        is True
    )


def test_resolve_command_channel_falls_back_to_source_channel() -> None:
    cfg = types.SimpleNamespace(
        channel_id="C123",
        plugin_channels={},
    )

    assert (
        _resolve_command_channel(
            cfg,
            command_id="cron",
            args_text="summary",
            source_channel_id="C999",
        )
        == "C999"
    )


@pytest.mark.anyio
async def test_make_reply_uses_top_level_when_reply_mode_is_channel() -> None:
    transport = FakeTransport()
    cfg = types.SimpleNamespace(
        exec_cfg=ExecBridgeConfig(
            transport=transport,
            presenter=object(),
            final_notify=False,
        ),
        reply_mode="channel",
    )

    reply = make_reply(
        cfg,
        channel_id="C1",
        message_ts="1.0",
        thread_ts="1.0",
    )
    await reply(text="hi")

    assert transport.send_calls[0]["options"].thread_id is None


@pytest.mark.anyio
async def test_make_reply_uses_thread_when_reply_mode_is_thread() -> None:
    transport = FakeTransport()
    cfg = types.SimpleNamespace(
        exec_cfg=ExecBridgeConfig(
            transport=transport,
            presenter=object(),
            final_notify=False,
        ),
        reply_mode="thread",
    )

    reply = make_reply(
        cfg,
        channel_id="C1",
        message_ts="1.0",
        thread_ts="1.0",
    )
    await reply(text="hi")

    assert transport.send_calls[0]["options"].thread_id == "1.0"
