import pytest

from supertask.model import ScheduleItem


def test_cronjob_fail_4():
    """
    Validate decoding fails because crontab syntax includes too few fields.
    """
    schedule = ScheduleItem(cron="1 2 3 4")
    with pytest.raises(ValueError) as ex:
        schedule.crontab()
    assert ex.match("Invalid crontab syntax: 1 2 3 4")


def test_cronjob_fail_8():
    """
    Validate decoding fails because crontab syntax includes too many fields.
    """
    schedule = ScheduleItem(cron="1 2 3 4 5 6 7 8")
    with pytest.raises(ValueError) as ex:
        schedule.crontab()
    assert ex.match("Invalid crontab syntax: 1 2 3 4 5 6 7 8")


def test_cronjob_success_5():
    """
    Validate decoding succeeds with 5 fields worth of crontab syntax.
    """
    schedule = ScheduleItem(cron="* * * * *")
    crontab = schedule.crontab()
    assert crontab["second"] is None
    assert crontab["minute"] == "*"
    assert crontab["year"] is None


def test_cronjob_success_6():
    """
    Validate decoding of a 6-field crontab string with seconds.
    
    This test verifies that ScheduleItem.crontab correctly extracts the seconds
    and minute values from a crontab string that includes seconds, while ensuring
    that the year field remains unset.
    """
    schedule = ScheduleItem(cron="*/10 * * * * *")
    crontab = schedule.crontab()
    assert crontab["second"] == "*/10"
    assert crontab["minute"] == "*"
    assert crontab["year"] is None


def test_cronjob_success_7():
    """
    Test decoding of crontab syntax with seconds and year.
    
    This test ensures that the ScheduleItem.crontab() method correctly parses a cron
    expression that includes an explicit seconds field and a year specification. It
    verifies that the returned dictionary contains 'second' as "*/10", 'minute' as "*",
    and 'year' as "2026".
    """
    schedule = ScheduleItem(cron="*/10 * * * * * 2026")
    crontab = schedule.crontab()
    assert crontab["second"] == "*/10"
    assert crontab["minute"] == "*"
    assert crontab["year"] == "2026"
