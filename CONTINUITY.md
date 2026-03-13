Goal (incl. success criteria):
- Configure command output routing so selected plugin commands can go to alternate Slack channels.
- Keep `transports.slack.channel_id` as the default destination.
- Support generic plugin mappings, including subcommand-style rules (example: `cron summary`).

Constraints/Assumptions:
- Changes should stay in existing `plugin_channels` config shape when possible.
- Routing applies to inline slash/action/shortcut command flows.
- Source channel/thread context remains separate from output channel for cross-channel sends.

Key decisions:
- Normalize plugin route keys with whitespace folding and optional `takopi-` prefix stripping.
- Resolve output channel by checking `"<command> <first_arg>"` before plain `<command>`.
- Keep `channel_id` as fallback when no plugin route is configured.

State:
- DONE

Done:
- Extended `SlackTransportSettings` parser to normalize spaced route keys.
- Updated bridge `_resolve_command_channel` to support command + first-arg matching for routing.
- Wired `args_text` into all command dispatch call sites.
- Added config and helper tests for subcommand routing and whitespace normalization.
- Updated README with subcommand-style example for `plugin_channels`.

Now:
- Awaiting user confirmation, then we can tailor exact config snippets for your existing plugin set.

Next:
- Apply any requested naming/shape preference if you want a different route-key convention.

Open questions (UNCONFIRMED if needed):
- UNCONFIRMED: Whether you want a separate per-plugin default key and per-command override hierarchy (currently using command-firstarg and command fallback only).

Working set (files/ids/commands):
- CONTINUITY.md
- README.md
- src/takopi_slack_plugin/config.py
- src/takopi_slack_plugin/bridge.py
- tests/test_slack_config.py
- tests/test_slack_helpers.py
