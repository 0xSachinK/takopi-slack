# `takopi.toml` Configuration

This plugin uses a hard cutover config model. Removed keys are rejected instead
of being silently translated.

## Minimal Setup

```toml
transport = "slack"

[transports.slack]
bot_token = "xoxb-..."
app_token = "xapp-..."
channel_id = "C12345678"
```

This is the smallest valid config. The bot listens in the configured home
channel and in DMs/MPDMs it is part of.

## Lock To Your Slack User

```toml
transport = "slack"

[transports.slack]
bot_token = "xoxb-..."
app_token = "xapp-..."
channel_id = "C12345678"
allowed_user_ids = ["U12345678"]
```

Set `allowed_user_ids` when only specific Slack users should be able to invoke
Takopi. Leave it empty to allow any user in an allowed channel.

## Allow Any Joined Channel

```toml
transport = "slack"

[transports.slack]
bot_token = "xoxb-..."
app_token = "xapp-..."
channel_id = "C12345678"
allowed_user_ids = ["U12345678"]
allowed_channel_ids = ["*"]
reply_mode = "channel"
```

`allowed_channel_ids = ["*"]` or `["all"]` means the bot can respond in any
channel it has joined.

Behavior in channels:

- Top-level messages must mention the bot.
- Thread replies can continue an existing Takopi session without another
  mention.
- `reply_mode = "channel"` posts responses as top-level channel messages.
- `reply_mode = "thread"` keeps responses inside the Slack thread.

## Route Plugin Output To Other Channels

```toml
transport = "slack"

[transports.slack]
bot_token = "xoxb-..."
app_token = "xapp-..."
channel_id = "C12345678"
allowed_user_ids = ["U12345678"]
allowed_channel_ids = ["*"]

[transports.slack.plugin_channels]
cron = "C22222222"
"cron summary" = "C33333333"
```

`plugin_channels` reroutes command output by command key:

- `cron = "C22222222"` routes `/cron ...` output to that channel
- `"cron summary" = "C33333333"` routes the `summary` subcommand separately

If there is no match, output stays in the invoking channel.

## Full Example

```toml
transport = "slack"

[plugins]
enabled = ["takopi-slack-plugin"]

[transports.slack]
bot_token = "xoxb-..."
app_token = "xapp-..."
channel_id = "C12345678"
allowed_user_ids = ["U12345678"]
allowed_channel_ids = ["*"]
reply_mode = "channel"
message_overflow = "split"
stale_worktree_reminder = true
stale_worktree_hours = 24
stale_worktree_check_interval_s = 600
action_handlers = [
  { id = "preview", command = "preview", args = "start" },
]

[transports.slack.plugin_channels]
cron = "C22222222"
"cron summary" = "C33333333"

[transports.slack.files]
enabled = false
auto_put = true
auto_put_mode = "upload"
uploads_dir = "incoming"
```

## Removed Keys

These old keys are rejected:

- `action_buttons`
- `show_running`

Use `action_handlers` and `action_blocks` instead.

## Slack App Requirements

Required bot scopes:

- `chat:write`
- `commands`
- `app_mentions:read`
- `channels:history`, `groups:history`, `im:history`, `mpim:history` as needed

Required app token scope:

- `connections:write`

Required Slack setup:

1. Enable Socket Mode.
2. Subscribe to `app_mention` and the matching `message.*` event types.
3. Enable Interactivity & Shortcuts.
4. Invite the bot to every channel you expect it to use.
