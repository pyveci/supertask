# Development Sandbox

## Introduction

Acquire sources.
```shell
git clone https://github.com/pyveci/supertask
cd supertask
```

It is recommended to use a Python virtualenv for the subsequent operations.
If you something gets messed up during development, it is easy to nuke the
installation, and start from scratch.
```shell
python3 -m venv .venv
source .venv/bin/activate
```

Install project in sandbox mode.
```shell
pip install --editable=.
```

Start service containers needed for running the test suite completely.
```shell
docker run --rm -it --name=cratedb \
  --publish=4200:4200 --publish=5432:5432 \
  --env=CRATE_HEAP_SIZE=2g \
  crate/crate:nightly \
  -Cdiscovery.type=single-node
```
```shell
docker run --rm -it --name=postgresql \
  --publish=5433:5432 \
  --env "POSTGRES_HOST_AUTH_METHOD=trust" \
  postgres:17 postgres -c log_statement=all
```

Run linters and software tests.
```shell
poe check
```

Format code.
```shell
poe format
```
