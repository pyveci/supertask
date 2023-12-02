# Supertask


## About

Supertask is a convenience job scheduler based on [APScheduler], [FastAPI],
[Pydantic], [SQLAlchemy], and a few other excellent packages.

You can use Supertask to invoke time-driven actions like the venerable [cron]
daemon is doing it. It can be used both as a standalone program, and as a
library.

It aims for [DWIM]-like usefulness and [UX], and provides CLI and HTTP
interfaces, and others.


## Features

- Store jobs in databases supported by SQLAlchemy.
- HTTP API to manipulate the job data model.
- Optionally, jobs can be pre-seeded from a JSON file `config.json`, either
  from the local filesystem, or from a remote URL. When using the filesystem,
  a watchdog monitors the file for changes, in order to keep the crontabs
  up-to-date.
- Minimal web interface (work-in-progress)


## Status

Please note that Supertask is a work in progress, and to be considered
alpha-quality software. Contributions of all kinds are much welcome,
in order to make it more solid, and to add features.

Breaking changes should be expected until a 1.0 release, so version
pinning is strongly recommended, especially when you use it as a library.


## Setup

```shell
pip install -r requirements.txt -r requirements-dev.txt
```


## Configuration

Supertask obtains configuration settings from both command-line arguments,
environment variables, and `.env` files. 

Define job store address.
```shell
export ST_STORE_ADDRESS=memory://
```
```shell
export ST_STORE_ADDRESS=postgresql://postgres@localhost
```
```shell
export ST_STORE_ADDRESS=crate://crate@localhost
```


## Usage

Run scheduler daemon, with pre-seeded example jobs.
```shell
supertask --pre-delete-jobs --pre-seed-jobs=cronjobs.json
```

Run scheduler daemon, and start HTTP API service.
```shell
supertask --http-listen-address=localhost:4243
```

Consume HTTP API.
```shell
http http://localhost:4243/cronjobs/
```

All together now.
```shell
supertask \
  --http-listen-address=localhost:4243 \
  --pre-delete-jobs \
  --pre-seed-jobs=https://github.com/WalBeh/scheduler-playground/raw/master/cronjobs.json
```


## Development

For installing a development sandbox, please refer to the [development sandbox
documentation].


[APScheduler]: https://pypi.org/project/APScheduler/
[cron]: https://en.wikipedia.org/wiki/Cron
[development sandbox documentation]: https://github.com/WalBeh/scheduler-playground/blob/main/docs/sandbox.md
[DWIM]: https://en.wikipedia.org/wiki/DWIM
[FastAPI]: https://pypi.org/project/fastapi/
[Pydantic]: https://pypi.org/project/pydantic/
[SQLAlchemy]: https://pypi.org/project/SQLAlchemy/
[UX]: https://en.wikipedia.org/wiki/User_experience
