# Supertask backlog

## Iteration +1
- Use regular logging instead of `icecream`
- Refactor data model
- Release v0.0.1
- Provide other schedules than `cron`
- Launch command-line targets, using `uv`
- Documentation: `--pre-seed-jobs` can access a wide range of remote resources
- Project scaffolding
- Release v0.0.2

## Iteration +2
- HTTP API: Updating jobs does not work
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
