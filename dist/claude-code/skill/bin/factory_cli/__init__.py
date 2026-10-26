"""factory_cli: the factory's state CLI logic.

The single read/validate/write path for run state (FR-001..FR-004, FR-022).
`bin/factory` is the thin entry script over `factory_cli.cli`; every state
mutation goes through `state.write_state`, never by hand.
"""
