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
    Test decoding of a 6-field crontab string with seconds.
    
    This test verifies that the ScheduleItem.crontab() method correctly decodes a crontab
    string that includes a seconds field. It asserts that the "second" field is interpreted
    as "*/10", the "minute" field as "*", and that the "year" field is None.
    """
    schedule = ScheduleItem(cron="*/10 * * * * *")
    crontab = schedule.crontab()
    assert crontab["second"] == "*/10"
    assert crontab["minute"] == "*"
    assert crontab["year"] is None


def test_cronjob_success_7():
    """
    Validate successful decoding of a crontab string with seconds and year.
    
    This test verifies that a ScheduleItem instantiated with a 7-field crontab
    string extracts the optional 'second' and 'year' values correctly, ensuring
    that the 'second', 'minute', and 'year' fields are parsed as '*/10', '*', and
    '2026', respectively.
    """
    schedule = ScheduleItem(cron="*/10 * * * * * 2026")
    crontab = schedule.crontab()
    assert crontab["second"] == "*/10"
    assert crontab["minute"] == "*"
    assert crontab["year"] == "2026"
