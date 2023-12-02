# Supertask

## About

Just playing around a bit with Python and `APScheduler` to implement
`cron`-like behaviour.

At the moment, a few _jobs_ are seeded from the JSON File `config.json`.
A `Watcher/Observer` keeps the crontabs up-to-date, as you change the
file.

There is also an HTTP API to manipulate the data model, provided by
Pydantic and FastAPI.

## Status

It is a work in progress, and to be considered alpha-quality software.
Contributions are much welcome.


## Setup

```shell
pip install -r requirements.txt -r requirements-dev.txt
```


## Usage

Run scheduler daemon, with pre-seeded example jobs.
```shell
python main.py
```


## Development

Run software tests.
```shell
poe test
```

Run linters.
```shell
poe lint
```

Format code.
```shell
poe format
```
