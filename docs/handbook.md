# Handbook

## Configuration

Supertask obtains configuration settings from both command-line arguments,
environment variables, and `.env` files. 

It is required to define the job store address. For that, use either the
`--store-address` command line option, or the `ST_STORE_ADDRESS` environment
variable. The value is an SQLAlchemy-compatible connection URL.

```shell
export ST_STORE_ADDRESS=memory://
```
```shell
export ST_STORE_ADDRESS=postgresql://postgres@localhost
```
```shell
export ST_STORE_ADDRESS=crate://crate@localhost
```

The default full qualified table name is `"supertask"."jobs"`. It can be defined
by using the `--store-schema-name` and `--store-table-name` command-line
options, or by adjusting the `ST_STORE_SCHEMA_NAME` and `ST_STORE_TABLE_NAME`
environment variables.

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
  --pre-seed-jobs=https://github.com/pyveci/supertask/raw/main/cronjobs.json
```

When jobs have been scheduled, and you don't want to invoke the HTTP API, it
is sufficient to invoke `supertask` without any parameters.

## Appendix

### Extended crontab syntax

Traditional Unix Cron uses just 5 components to define schedules, like
`minute, hour, day (month), month, day (week)`.
```
# Every minute.
* * * * *

# Every 10 minutes.
*/10 * * * *
```
-- https://crontab.guru/every-minute
-- https://crontab.guru/every-ten-minutes

APScheduler provides an extended 6- or 7-tuple syntax, adding an optional scheduling
unit for **seconds** on the left hand side, and another one for scheduling **years**
on the right hand side, like `second (0-59), minute (0-59), hour (0-23), day of month
(1-31), month (1-12), day of week (0-6)`.
```
# Every 10 seconds, starting 2026.
*/10 * * * * * 2026
```
-- https://crontabkit.com/crontab-every-10-seconds
