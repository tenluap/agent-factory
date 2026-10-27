# Fixture data model

There are no production model changes.

Each affected test owns one TemporaryDirectory. Its HOME contains an existing `.factory` directory; XDG_CONFIG_HOME points to `.config`. The success case owns generated per-user distribution and harness symlinks. The conflict case starts with a skill destination containing `user file` and retains those exact contents after rejection. TemporaryDirectory cleanup removes sandbox contents when each test finishes.

Expected roles are filenames independently derived from the source role inventory and the existing OpenCode naming convention. The inventory must be nonempty and exactly match the installed factory agent names.
