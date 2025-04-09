# Research

A mix of prior art enumeration and other relevant notes, comparing
Supertask to other systems, and enumerating where it draws inspiration
from.

## Aika
[Aika] provides date- and time-range parsing utilities for multiple
languages.

## Go cron
[cron][cron-go] is a cron library for Go.

## later
[later] is a JavaScript library for defining recurring schedules and
calculating future (or past) occurrences for them. Includes support
for using English phrases and Cron schedules. Works in Node and in
the browser. Used by Algolia. Thanks for sharing, @msbt.

## Nextdoor Scheduler
To replace Cron by the [Nextdoor Scheduler], we used the excellent Python
module APScheduler to schedule jobs. It enabled us to manage jobs
programmatically — we built REST APIs, command line tools, and human-friendly
web UI, see also [We Don't Run Cron Jobs at Nextdoor].

## pg_timetable
[pg_timetable] is an advanced job scheduler for PostgreSQL, offering many
advantages over traditional schedulers such as cron and others. It is
completely database-driven and provides a couple of advanced concepts.

## Quartz Job Scheduler
[Quartz] is a richly featured, open-source job scheduling library that can be
integrated within virtually any Java application—from the smallest stand-alone
application to the largest e-commerce system.

## Timeloop
[timeloop] is an elegant periodic task executor.

## tractor
[tractor] is a distributed, structured concurrency runtime for Python
and friends, built on trio.

## VictoriaMetrics
> vmalert: Add `eval_offset` attribute for Groups. If specified, Group will
> be evaluated at the exact time offset in the range of `[0…evaluationInterval]`.
> The setting might be useful for cron-like rules which must be evaluated at
> specific moments of time. See the issue for details.
>
> - [Groups documentation](https://docs.victoriametrics.com/vmalert/#groups)
> - [Issue #3409](https://github.com/VictoriaMetrics/VictoriaMetrics/issues/3409)

## Windows PowerShell API
See [Scheduling Jobs with the Windows PowerShell API].

## Backlog
- Bash, Python, Java
- at, cron, systemd timers, Jenkins
- Grafana, Prometheus, VictoriaMetrics


[Aika]: https://pypi.org/project/aika/
[cron-go]: https://github.com/robfig/cron
[later]: https://github.com/bunkat/later
[Nextdoor Scheduler]: https://github.com/Nextdoor/ndscheduler
[pg_timetable]: https://github.com/cybertec-postgresql/pg_timetable
[Quartz]: https://github.com/quartz-scheduler/quartz
[Scheduling Jobs with the Windows PowerShell API]: https://learn.microsoft.com/en-us/powershell/scripting/developer/scheduling-jobs-with-the-windows-powershell-api?view=powershell-7.5
[timeloop]: https://github.com/sankalpjonn/timeloop
[tractor]: https://github.com/goodboy/tractor
[We Don't Run Cron Jobs at Nextdoor]: https://engblog.nextdoor.com/we-don-t-run-cron-jobs-at-nextdoor-6f7f9cc62040
