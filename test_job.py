from scheduler import my_job


def test_my_job(mocker, capsys):
    mocker.patch("random.randint")
    mocker.patch("time.sleep")
    my_job("foo")
    out, err = capsys.readouterr()
    assert "DONE" in err
