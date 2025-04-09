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
    Test that the crontab method parses a cron string with seconds correctly.
    
    This test creates a ScheduleItem using the cron string "*/10 * * * * *"
    and asserts that the parsed dictionary has "second" set to "*/10", "minute"
    set to "*", and "year" as None, validating support for six-field cron syntax.
    """
    schedule = ScheduleItem(cron="*/10 * * * * *")
    crontab = schedule.crontab()
    assert crontab["second"] == "*/10"
    assert crontab["minute"] == "*"
    assert crontab["year"] is None


def test_cronjob_success_7():
    """
    Test that crontab decodes strings with seconds and year.
    
    This test verifies that a ScheduleItem created with a cron string containing a seconds
    field, minute, and year returns a dictionary mapping: "second" to "*/10", "minute" to "*",
    and "year" to "2026".
    """
    schedule = ScheduleItem(cron="*/10 * * * * * 2026")
    crontab = schedule.crontab()
    assert crontab["second"] == "*/10"
    assert crontab["minute"] == "*"
    assert crontab["year"] == "2026"
