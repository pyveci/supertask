# Supertask backlog

## Iteration +1
- Use regular logging instead of `icecream`
- Format code
- Are short-interval jobs possible?
- Release 0.1.0

## Iteration +2
- Add `JobExecution` subsystem derived from `django-apscheduler`
- Wrapper around Job execution
- Success / failure notifications
- SDK interface, with examples
- When web server start is request, but it fails, shutdown the application
  ```
  ERROR:    [Errno 8] nodename nor servname provided, or not known
  ```
- Check out FastUI. -- https://github.com/samuelcolvin/FastUI
- Isolate testing from workstation use:
  ```
  Unable to restore job "foo" -- removing it
  ModuleNotFoundError: No module named 'test_core'
  ```


## Done
- Config: Obtain HTTP listen address
- Config: Obtain path/URL to seed file per CLI argument `--seed=cronjobs.json`
- Config: Obtain job store schema- and table names alongside database address
