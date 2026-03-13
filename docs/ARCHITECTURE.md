# Slack Transport Architecture

## Overview

`takopi-slack-plugin` is a Socket Mode transport for Takopi. The transport is
split into a small set of focused modules:

- `backend.py`: transport bootstrapping and config wiring
- `bridge.py`: Slack event loop, routing, session handling, and interactive actions
- `client.py`: Slack Web API and socket bootstrap helpers
- `engine.py`: adapter from Slack messages into Takopi runner execution
- `thread_sessions.py`: persisted per-thread Slack state
- `commands/`: command dispatch and file-transfer helpers

## Event Flow

1. Socket Mode receives `events_api`, `slash_commands`, or `interactive`.
2. `bridge.py` filters by:
   - allowed channel
   - allowed Slack user
   - valid event shape
3. Channel messages are processed only when:
   - the message is an `app_mention`, or
   - it is a thread reply, or
   - it is a DM / MPDM message
4. The bridge resolves context, thread/session state, and command routing.
5. Execution is delegated to Takopi through `engine.py` or command handlers.

## Session Model

Session state is keyed by `channel_id + thread_id` and stored in
`slack_thread_sessions_state.json`.

Stored state includes:

- resume tokens
- project / branch context
- per-engine model overrides
- per-engine reasoning overrides
- default engine override
- worktree metadata and stale reminder state

Even when `reply_mode = "channel"`, state is still anchored to the initiating
Slack message/thread root so archive, reminders, and thread-local overrides stay
consistent.

## Routing Model

### Channel Access

- `channel_id` is the default home channel.
- `allowed_channel_ids` adds more explicit channels.
- `allowed_channel_ids = ["*"]` or `["all"]` means any channel the bot has
  joined.

### User Access

- `allowed_user_ids` is a transport-level allowlist.
- If empty, any user in an allowed channel may invoke the bot.

### Reply Routing

- `reply_mode = "thread"` replies in-thread.
- `reply_mode = "channel"` posts top-level responses.

### Command Routing

- Command output stays in the invoking channel by default.
- `plugin_channels` can reroute a command, or command + first arg, to a
  different channel.

## Refactor Notes

The bridge intentionally centralizes shared command dispatch through one helper
so inline commands, slash commands, shortcuts, and custom actions use the same
routing and default-context logic.

If the bridge grows further, the next cleanup target should be splitting
interactive/archive handling into a separate module rather than adding more
branching to `bridge.py`.
