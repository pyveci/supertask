import pytest

from supertask.model import CronJob


def test_cronjob_fail_5():
    """
    Validate decoding fails because crontab syntax includes too few fields.
    """
    job = CronJob(id=42, name="foobar", trigger_cron="1 2 3 4")
    with pytest.raises(ValueError) as ex:
        job.decode_crontab()
    assert ex.match("Invalid crontab syntax: 1 2 3 4")


def test_cronjob_fail_8():
    """
    Validate decoding fails because crontab syntax includes too many fields.
    """
    job = CronJob(id=42, name="foobar", trigger_cron="1 2 3 4 5 6 7 8")
    with pytest.raises(ValueError) as ex:
        job.decode_crontab()
    assert ex.match("Invalid crontab syntax: 1 2 3 4 5 6 7 8")


def test_cronjob_success_5():
    """
    Validate decoding succeeds with 5 fields worth of crontab syntax.
    """
    job = CronJob(id=42, name="foobar", trigger_cron="* * * * *")
    crontab = job.decode_crontab()
    assert crontab["second"] is None
    assert crontab["minute"] == "*"
    assert crontab["year"] is None


def test_cronjob_success_6():
    """
    Validate decoding succeeds with 5 fields worth of crontab syntax, including seconds.
    """
    job = CronJob(id=42, name="foobar", trigger_cron="*/10 * * * * *")
    crontab = job.decode_crontab()
    assert crontab["second"] == "*/10"
    assert crontab["minute"] == "*"
    assert crontab["year"] is None


def test_cronjob_success_7():
    """
    Validate decoding succeeds with 5 fields worth of crontab syntax, including year.
    """
    job = CronJob(id=42, name="foobar", trigger_cron="*/10 * * * * * 2026")
    crontab = job.decode_crontab()
    assert crontab["second"] == "*/10"
    assert crontab["minute"] == "*"
    assert crontab["year"] == "2026"
