# Supertask

Supertask is a convenience task runner for programming recurrent or otherwise
scheduled jobs, based on the excellent [APScheduler], [FastAPI], [Pydantic],
[SQLAlchemy], and [uv] packages, amongst others.

You can use Supertask to invoke time-driven actions like the venerable [cron]
daemon and the contemporary [systemd timers] are doing it. It can be used both
as a standalone program/service, and as a library.

[![CI][badge-ci]][project-ci]
[![Coverage][badge-coverage]][project-coverage]
[![Downloads per month][badge-downloads-per-month]][project-downloads]
[![License][badge-license]][project-license]
[![Release Notes][badge-release-notes]][project-release-notes]

» [Documentation]
| [Changelog]
| [PyPI]
| [Issues]
| [Source code]
| [License]
| [Community Forum]

## Features

- Store jobs in databases supported by SQLAlchemy.
- Supertask aims for [DWIM]-like usefulness and [UX], and provides CLI-,
  HTTP-, and other interfaces.
- Optionally, jobs can be pre-seeded from a JSON file `config.json`, either
  from the local filesystem, or from a wide range of remote locations.
  When using the filesystem, a watchdog monitors the file for changes, in
  order to keep the schedules up to date.

## Status

Please note that Supertask is a work in progress, and to be considered
alpha-quality software. Contributions of all kinds are much welcome,
in order to make it more solid, and to add features.

Breaking changes should be expected until a 1.0 release, so applying
version pinning is strongly recommended when consuming the packages.

[![Status][badge-status]][project-pypi]
[![Package version][badge-package-version]][project-pypi]
[![Supported Python versions][badge-python-versions]][project-pypi]

## Installation

See [Supertask Installation].

## Usage

See [Supertask Handbook].

## Contribute

See [Supertask Sandbox].

## Supported by

[![JetBrains logo.](https://resources.jetbrains.com/storage/products/company/brand/logos/jetbrains.svg)](https://jb.gg/OpenSourceSupport)

Special thanks to the people at JetBrains s.r.o. for supporting us with
excellent development tooling.


[APScheduler]: https://pypi.org/project/APScheduler/
[cron]: https://en.wikipedia.org/wiki/Cron
[DWIM]: https://en.wikipedia.org/wiki/DWIM
[FastAPI]: https://pypi.org/project/fastapi/
[Pydantic]: https://pypi.org/project/pydantic/
[SQLAlchemy]: https://pypi.org/project/SQLAlchemy/
[systemd timers]: https://opensource.com/article/20/7/systemd-timers
[UX]: https://en.wikipedia.org/wiki/User_experience

[Changelog]: https://github.com/pyveci/supertask/blob/main/CHANGES.md
[Community Forum]: https://community.panodata.org/
[Documentation]: https://supertask.readthedocs.io/
[Issues]: https://github.com/pyveci/supertask/issues
[License]: https://github.com/pyveci/supertask/blob/main/LICENSE
[PyPI]: https://pypi.org/project/supertask/
[Supertask Handbook]: https://supertask.readthedocs.io/handbook.html
[Supertask Installation]: https://supertask.readthedocs.io/install.html
[Supertask Sandbox]: https://supertask.readthedocs.io/sandbox.html
[Source code]: https://github.com/pyveci/supertask
[uv]: https://docs.astral.sh/uv/

[badge-ci]: https://github.com/pyveci/supertask/actions/workflows/main.yml/badge.svg
[badge-coverage]: https://codecov.io/gh/pyveci/supertask/branch/main/graph/badge.svg
[badge-downloads-per-month]: https://pepy.tech/badge/supertask/month
[badge-license]: https://img.shields.io/github/license/pyveci/supertask.svg
[badge-package-version]: https://img.shields.io/pypi/v/supertask.svg
[badge-python-versions]: https://img.shields.io/pypi/pyversions/supertask.svg
[badge-release-notes]: https://img.shields.io/github/release/pyveci/supertask?label=Release+Notes
[badge-status]: https://img.shields.io/pypi/status/supertask.svg
[project-ci]: https://github.com/pyveci/supertask/actions/workflows/main.yml
[project-coverage]: https://app.codecov.io/gh/pyveci/supertask
[project-downloads]: https://pepy.tech/project/supertask/
[project-license]: https://github.com/pyveci/supertask/blob/main/LICENSE
[project-pypi]: https://pypi.org/project/supertask
[project-release-notes]: https://github.com/pyveci/supertask/releases
