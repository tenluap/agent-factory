# Rider MCP tool catalog

This is a routing reference, not a promise that every named tool is enabled in
every IDE, client, Rider version, or project. The installed MCP tool definition
is authoritative for availability, arguments, and permissions.

## Find and invoke a tool

1. In Rider Settings, search for **MCP Server** and confirm the server is
   enabled. In **Exposed Tools**, check that the action is enabled and whether
   it is marked **Router-only**.
2. Prefer a directly exposed action. Router-only actions are hidden from the
   client's ordinary tool list and must be called through the universal
   `execute_tool` action. A router-only action is usable only if the installed
   router definition exposes it.
3. Use the exact name and arguments from the current client/IDE schema. Do not
   infer availability from this document or a web page. The IDE tool list is
   configurable, and plugins and IDE versions may add, remove, or rename tools.
4. For project-aware actions, pass the solution/project root when the schema
   accepts it. Use paths relative to that root where the action requires them.

For the router, pass its `command` string in the syntax documented by the
installed wrapper. For example, when the router accepts command-line-style
arguments: `search_symbol --q OrderService`. Do not pass `tools/list`, `help`,
or a fabricated tool name as a discovery request. If the router syntax or
target schema is unknown, stop and check its installed definition rather than
guessing.

## Core Rider MCP actions

The following is the published Rider/IntelliJ MCP catalog, grouped by task.
Names are exact; descriptions are deliberately brief. See
[Rider MCP Server documentation](https://www.jetbrains.com/help/rider/2026.3/mcp-server.html)
for descriptions, parameters, setup, and version-specific behavior.

### Analysis and code insight

| Action | Use |
|---|---|
| `analyze_calls` | Inspect incoming or outgoing calls using IDE call hierarchy. |
| `build_project` | Build the project or selected files and report build errors. |
| `get_file_problems` | Inspect one file for IDE errors and warnings. |
| `get_project_dependencies` | List project dependencies and versions when known. |
| `get_project_modules` | List project modules and their types. |
| `get_symbol_info` | Get IDE documentation and declaration information at a source position. |
| `lint_files` | Inspect several files for IDE errors and warnings. |

### Database

| Action | Use |
|---|---|
| `cancel_sql_query` | Cancel a running query by session ID. |
| `create_database_connection` | Add a database connection. |
| `edit_database_connection` | Change an existing connection's driver or URL. |
| `execute_sql_query` | Run one SQL statement on a connection. |
| `fetch_query_result` | Page through a prior query result. |
| `get_database_object_description` | Read a database object's structure. |
| `introspect_schema` | Load schema metadata into the IDE model. |
| `list_database_connections` | List configured database connections. |
| `list_database_schemas` | List schemas for a connection. |
| `list_recent_sql_queries` | Inspect recent/running queries where the IDE plan permits it. |
| `list_schema_object_kinds` | List object kinds supported by a database. |
| `list_schema_objects` | List objects in a schema. |
| `preview_table_data` | Preview rows from a table-like object. |
| `test_database_connection` | Test a configured connection and report diagnostics. |

Database actions require a configured connection and, for object/data actions,
the relevant schema to be introspected. Use `list_database_connections` rather
than guessing a connection ID. Read-only connections reject writes. Recent SQL
query inspection may depend on the IDE subscription tier. Treat query execution
and data changes as actions requiring explicit authorization.

### Execution and tests

| Action | Use |
|---|---|
| `execute_run_configuration` | Run a named configuration or an IDE-discovered run point. |
| `get_run_configurations` | List configurations, or discover run points in a file. |
| `test_run_start` | Start a .NET test run and return its session ID. |
| `test_run_state` | Read or wait for the state/results of a test run. |

Discover the configuration or run point first. Preserve its configured launch
values unless an override is necessary and supported. A timed-out start/run
does not imply that the process stopped; inspect its state before retrying.
`test_run_start`/`test_run_state` availability may vary by Rider version.

### Files, edits, and formatting

| Action | Use |
|---|---|
| `apply_patch` | Apply an in-project patch or unified diff. |
| `create_new_file` | Create a project file. |
| `get_all_open_file_paths` | List files open in IDE editors. |
| `list_directory_tree` | Explore a project directory tree. |
| `open_file_in_editor` | Open a project file in the IDE. |
| `read_file` | Read project/dependency sources, including supported archive sources. |
| `reformat_file` | Format files using IDE code style. |
| `rename_refactoring` | Rename a symbol and its resolved references. |

### Search

| Action | Use |
|---|---|
| `search_file` | Find project files by glob. |
| `search_regex` | Find regular-expression matches in project files. |
| `search_symbol` | Find declarations/usages by semantic symbol name. |
| `search_text` | Find literal text in project files. |
| `skill_search` | Search project files using file, text, regex, or symbol mode. |

Prefer semantic symbol/call tools for code relationships; use text or regex
search for literal matches. `skill_search` searches project content, not the
MCP tool catalog.

### Terminal, universal routing, and version control

| Action | Use |
|---|---|
| `execute_terminal_command` | Run a command in the IDE terminal; may require confirmation. |
| `execute_tool` | Invoke an enabled router-only IDE action using the installed router syntax. |
| `get_repositories` | List VCS roots in a project. |
| `git_status` | Inspect repository status, optionally scoped to a repository. |

Terminal commands and run configurations may require user confirmation unless
Rider's Brave Mode is enabled. Do not enable bypass modes just to avoid
approval. Inspect VCS status before grouping or otherwise changing pending work.

## Additional tools that may be exposed by the client or plugins

These are not a guarantee of the base published Rider catalog. The current
client may expose additional IDE operations directly; extensions may also
provide router-only tools. Use them only when their exact installed schema is
available.

### IDE and solution helpers

| Action | Use |
|---|---|
| `build_solution_start`, `build_solution_state` | Start and inspect a solution build. |
| `get_solution_projects` | List projects in a solution. |
| `get_project_problems` | Inspect project-level problems. |
| `post_edit_quality_check` | Run configured post-edit formatting/inspection checks. |

### Refactoring and navigation

| Action | Use |
|---|---|
| `find_implementations` | Find implementations of a type or member. |
| `find_usages` | Find resolved usages of a symbol. |
| `findTests` | Look up tests associated with code, when the test-lookup plugin is available. |
| `change_api_signature` | Change a method/API signature and update callers. |
| `extract_base_class` | Extract a base class. |
| `extract_interface` | Extract an interface. |
| `extract_method` | Extract selected code into a method. |
| `move_type_to_namespace` | Move a type to another namespace. |
| `reorganize_namespaces` | Reorganize namespaces. |
| `safe_delete` | Delete a symbol/file with IDE reference checks. |

### Debugger

These actions require a supported debugger session and may have language/runtime
limitations. Use the exact installed schema, especially for breakpoint and
session IDs.

| Action | Use |
|---|---|
| `xdebug_start_debugger_session`, `xdebug_attach_to_process` | Start or attach a debugger session. |
| `xdebug_get_debugger_status` | Inspect debugger state. |
| `xdebug_control_session` | Control the active debugging session. |
| `xdebug_get_stack`, `xdebug_get_threads` | Inspect stack frames and threads. |
| `xdebug_get_frame_values`, `xdebug_get_value_by_path` | Inspect local/frame values. |
| `xdebug_evaluate_expression` | Evaluate an expression in the debug context. |
| `xdebug_set_variable` | Change a variable in the debug context. |
| `xdebug_get_process_output` | Read process output. |
| `xdebug_set_breakpoints`, `xdebug_list_breakpoints`, `xdebug_remove_breakpoints` | Set, inspect, or remove breakpoints. |
| `xdebug_set_breakpoints_muted` | Mute/unmute breakpoints. |
| `xdebug_run_to_line` | Continue execution to a source line. |
| `xdebug_ignore_exception` | Configure exception handling for the session. |
| `xdebug_get_async_task_stack`, `xdebug_get_async_tasks` | Inspect asynchronous task stacks/tasks where supported. |

### Unreal Engine integration

Unreal actions require the relevant Unreal integration/plugin and a connected
project/editor. Do not assume they are available in a non-Unreal solution.

| Action | Use |
|---|---|
| `ue_status`, `ue_health`, `ue_get_logs` | Inspect integration/editor status and logs. |
| `ue_play`, `simulate_input`, `take_screenshot`, `viewport_camera` | Control or inspect the editor/game viewport. |
| `ue_execute_python` | Run an editor Python operation. |
| `search_assets`, `search_tags` | Search Unreal assets or tags. |
| `get_class_hierarchy`, `get_asset_properties`, `find_default_value_overrides` | Inspect classes/assets and defaults. |
| `spawn_actor` | Add an actor to the Unreal scene. |

`spawn_actor` and editor-control operations change project/editor state; confirm
the requested target and intended effect before use.

### Rider and plugin extensions

| Area | Action | Use |
|---|---|---|
| Air session | `air_set_session_title` | Set the title of the current Air session. |
| CMake | `create_cmake_profile` | Create a CMake profile. |
| CMake | `delete_cmake_profiles` | Delete CMake profiles. |
| CMake | `disable_cmake_profiles` | Disable CMake profiles. |
| CMake | `enable_cmake_profiles` | Enable CMake profiles. |
| CMake | `load_cmake` | Load a CMake project. |
| CMake | `update_cmake_profile` | Update a CMake profile. |
| Data breakpoints | `xdebug_list_data_breakpoints` | List debugger data/watch breakpoints. |
| Data breakpoints | `xdebug_remove_data_breakpoint` | Remove a data breakpoint. |
| Data breakpoints | `xdebug_set_data_breakpoint` | Set a data/watch breakpoint. |
| Low-level debugger | `xdebug_disassemble` | Disassemble instructions at a paused frame/address. |
| Low-level debugger | `xdebug_get_registers` | Read CPU registers from a paused frame. |
| Low-level debugger | `xdebug_read_memory` | Read target-process memory. |
| Database export | `export_query_result` | Export a previous query result with a selected extractor. |
| Database export | `list_data_extractors` | List supported query-result export formats. |
| Database import | `import_data` | Import an inspected source into an existing table. |
| Database import | `inspect_import_file` | Inspect a supported data file before import. |
| Database import | `inspect_import_query` | Inspect a query result before import. |
| Database | `execute_cross_db_query` | Join read-only results from multiple configured connections. |
| dotTrace | `dotTraceAttachReport` | Attach an analysis report to a snapshot. |
| dotTrace | `dotTraceGetCallTree` | Read a snapshot call tree. |
| dotTrace | `dotTraceGetSnapshotFilters` | List filters available for a snapshot. |
| dotTrace | `dotTraceGetSnapshotInfo` | Read snapshot metadata. |
| dotTrace | `dotTraceGetTimeline` | Read timeline aggregates for a snapshot. |
| dotTrace | `dotTraceGetTimelineEvents` | Read individual timeline events. |
| dotTrace | `dotTraceShowAttachedReport` | Display an attached analysis report in Rider. |
| OpenTelemetry | `get_log_records` | Query collected log records. |
| OpenTelemetry | `get_service_map` | Build a service map from tracing data. |
| OpenTelemetry | `get_services` | List discovered services. |
| OpenTelemetry | `get_spans` | Query collected spans. |
| Rider Database | `list_solution_connection_strings` | Find configured connection strings; treat returned values as secrets. |
| Rider Debugger | `xdebug_memory_dump` | Load a memory dump for post-mortem debugging. |
| Rider Debugger | `xdebug_start_mixed_mode_debug` | Attach the debugger to a mixed managed/native process. |
| Unity Profiler | `unity_profiler_analyze` | Find expensive functions across profiler frames. |
| Unity Profiler | `unity_profiler_frame` | Inspect a profiler frame in detail. |
| Unity Profiler | `unity_profiler_overview` | Read session-level profiler timing and allocation data. |
| Unreal | `ue_export_blueprint_nodes` | Export Blueprint graph nodes to Unreal clipboard text. |
| Unreal | `ue_import_blueprint_nodes` | Import Blueprint graph nodes from Unreal clipboard text. |
| Spec | `spec_report_status` | Record an individual specification item's completion or failure. |
| Spec | `spec_specify_finished` | Signal successful completion of a Specify run. |

These are enabled and router-only in the supplied screenshot. Plugin actions
may still require the corresponding plugin, project type, running session, or
service. Confirm the live schema before invoking them.

For older Rider releases, consult the matching version of Rider Help. Do not
assume a published action is enabled locally or infer a tool's removal from an
older list. Re-check the installed **Exposed Tools** inventory and schema when
an action is unavailable or its arguments differ from this reference.
