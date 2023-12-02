from jobs import my_job


def test_my_job(mocker, capsys):
    mocker.patch("random.randint")
    mocker.patch("time.sleep")
    my_job("foo")
    out, err = capsys.readouterr()
    assert "JOB-START" in err
    assert "JOB-FINISH" in err
