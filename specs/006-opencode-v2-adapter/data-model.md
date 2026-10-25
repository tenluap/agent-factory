# Adapter data model

No new persisted schema, state transition or production model layer.

- Harness adapter: existing format, ordered fields, extra metadata, access policies, models and install-home settings. Only OpenCode access shape changes.
- Role: existing name/description, read-or-write access and model tier. Nine roles determine rendered access and model fields.
- Permission rule: ordered mapping of string action/resource/effect. Resource is wildcard `*`, effect is deny. Read roles deny edit then subagent; write roles deny subagent only.
- Rendered distribution: derived agents plus shared skill/reference tree, generated from maintained source. Other native agents remain byte-identical under canonical inputs.
- Verification evidence: check, environment/version, outcome and limit; static/discovery/dispatch/enforcement categories remain distinct.

Preserve every role's child-agent restriction, read-only edit restriction, permission order, paths and model defaults/overrides. Empty model retains session inheritance. No user configuration migration.
