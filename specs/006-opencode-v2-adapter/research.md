# OpenCode V2 research

Checked official documentation on 2026-10-25.

- Decision: native adoption with supported V1 compatibility. Rationale: the [migration guide](https://opencode.ai/v2/docs/migrate-v1) says supported agent and skill definitions should continue working. Alternative: calling all V1 definitions broken contradicts that contract. No server/plugin integration changes are needed.
- Decision: ordered native permissions using action/resource/effect and edit/subagent actions. Rationale: [permissions](https://opencode.ai/v2/docs/permissions) documents fields, action names and last-match ordering. Alternative: legacy maps remain translation input but are not the chosen native output.
- Decision: extend existing serializer using JSON flow mappings. Rationale: preserve ordering and wildcard quoting without dependencies. Alternative: a YAML dependency or recursive serialization framework adds scope. The [tools reference](https://opencode.ai/v2/docs/tools) documents shell/subagent capabilities; detail belongs in the adapter.
- Decision: observe real red before production adoption; retain runtime limits. Rationale: existing six-test/v2.1.4 loading evidence is prior context, and discovery cannot prove model-backed dispatch/enforcement. Alternative: claiming a full factory run would exceed evidence. No new model calls are required.

Technical unknowns are resolved. Protected test-seam confirmation remains the plan's user gate.
