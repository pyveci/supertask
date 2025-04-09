# Backlog

## Iteration +1
- Refactor data model: Schedule vs. Payload vs. Metadata
  - Static metadata (optional): Authors, Created/Updated-Timestamps
  - Job: Task + Runtime metadata: Start time, end time, duration, job source, job definition
- Use regular logging instead of `icecream`
- Launch tasks using arbitrary Python files or command-line targets,
  also using `uv` and `docker`.
  Hint: It's not the payload per se, but it's about the dependencies!
- Improve CLI
  By default, pass command to `sh -c` or `--exec` otherwise.
  From there, gradually add more levels of isolation/externalization, to go beyond
  the in-process task scheduling provided by APScheduler Core.
  - `supertask list-namespaces`
  - `supertask list-jobs --ns=e1cd9e64e25c8bdbec85ca242b1fcb32`
  - `supertask run`
  - `supertask run --file timetable.yaml` (make `supertask.yaml` the default)
  - `supertask run --file taskfile.py [--when=]`
  - `supertask run --command echo "hello" [--when=once]`
  - `supertask run --command python:print("hello") [--when=once]`
  - `supertask run [--when=once] -- python:print("hello")`
  - `supertask run [--when=@daily] -- cmd:echo "hello"`
- Micro-bookkeeping about namespaces, including metadata about origin
  (author, source, etc.), to identify individual items amongst an
  enumeration of many.
- Documentation:
  > Jobs can be any Java class that implements the simple Job interface, leaving infinite
  > possibilities for the work your Jobs can perform.
  > -- https://github.com/quartz-scheduler/quartz/blob/main/docs/introduction.adoc
- Release v0.0.1

## Iteration +2
- Kubernetes? -- https://github.com/kubernetes-sigs/kueue
- Provide other schedules than `cron`
- Documentation: `--pre-seed-jobs` can access a wide range of remote resources
- Documentation: Annotations are nice, but are leaning towards library use. On
  the other hand, Supertask focuses on standalone use, so the scheduling engine
  and the job payloads need to be decoupled to a maximum extent.
- Documentation: Schedule periodic tasks in the range of years to milliseconds.
  `await trio.sleep(1/50000/50)  # burn a core @ ~ 50kHz`
- Examples:
  - Emulate `watch`
    ```
    -p, --precise
          Execute command --interval seconds after its previous run started, instead of --interval seconds after its previous run finished. If it's taking
          longer than --interval seconds for command to complete, it is waited for in either case.    
    ```
  - Emit `sin(elapsed)` values to MQTT.
    https://stackoverflow.com/a/7370824
    `supertask run -c python:print(math.sin(time.process_time())) [--when=once]`
    `supertask run -c python:print(math.cos(task.elapsed.total_seconds)) [--when=once]`
  - Download JSON from web, transform, and ingest into database.
  - Submit notifications based on task outcome. Provide per Supertask
    stdlib.
  - Example task defined in JavaScript/TypeScript.
  - Automate tasks in CrateDB Toolkit.
  - Miniature infrastructure or network monitoring.
  - Cleanup jobs, for wiping temporary resources each night.
  - Run a sequence of SQL statements
  - Use trio and tractor
- Project scaffolding?
- Release v0.0.2
- Audit logging
- Fluent API
  - https://www.quartz-scheduler.org/documentation/quartz-2.3.0/tutorials/tutorial-lesson-04.html
  - https://www.quartz-scheduler.org/documentation/quartz-2.3.0/tutorials/tutorial-lesson-05.html
  - https://www.quartz-scheduler.org/documentation/quartz-2.3.0/tutorials/tutorial-lesson-06.html

## Iteration +3
- HTTP API: Updating jobs does not work
  - Use RPyC instead, for providing a CLI
    - https://github.com/agronholm/apscheduler/blob/3.x/examples/rpc/server.py
    - https://github.com/agronholm/apscheduler/blob/3.x/examples/rpc/client.py
  - Use an off-the-shelf web UI
    - https://apscheduler.readthedocs.io/en/3.x/faq.html#is-there-a-graphical-user-interface-for-apscheduler
    - https://github.com/Dragon-GCS/apscheduler-webui, https://docs.pydantic.dev/fastui/
- Check out https://pypi.org/project/fastapi-apscheduler/
- Add `JobExecution` subsystem derived from `django-apscheduler`
- Can Supertask provide its services per MCP server?
- Wrapper around Job execution
- Success / failure notifications
- SDK interface, with examples
- When web server start is request, but it fails, shutdown the application
  ```
  ERROR:    [Errno 8] nodename nor servname provided, or not known
  ```
- Check out FastUI. -- https://github.com/samuelcolvin/FastUI
- APScheduler UIs
  - https://github.com/schmidtfederico/apscheduler-ui
  - https://gitee.com/huge-dream/dvadmin-apscheduler
- Isolate testing from workstation use:
  ```
  Unable to restore job "foo" -- removing it
  ModuleNotFoundError: No module named 'test_core'
  ```

## Done
- Config: Obtain HTTP listen address
- Config: Obtain path/URL to seed file per CLI argument `--seed=cronjobs.json`
- Config: Obtain job store schema- and table names alongside database address
- Format code
- Are short-interval jobs possible? Yes, down to seconds-granularity.
- Data model:
  Introduce `namespace` as multi-tenant identifier entity, and to spawn as many
  ephemeral / ad hoc timetable schedules as there is demand, by making it cheap
  by design, like Kotori is doing it for DAQ channels.
  When no `namespace` is supplied, per task file, `--ns` option, or otherwise,
  generate an ephemeral namespace identifier by using
  `digest(f"{hostname}-{user}-{resource}")`, which qualifies the job's source uniquely
  even when invoked in multiple instances.
