from supertask.vendor.jobs import example_waiter


def test_my_job(mocker, capsys):
    mocker.patch("random.randint")
    mocker.patch("time.sleep")
    example_waiter("foo")
    out, err = capsys.readouterr()
    assert "JOB-START" in err
    assert "JOB-FINISH" in err
