from main import main


def test_main(mocker, caplog):
    mocker.patch("main.Supertask.wait")
    mocker.patch("main.Supertask.start_http_service")
    main()
    assert "Configuring scheduler" in caplog.messages
    assert "Seeding jobs" in caplog.messages
    assert "Adding job tentatively -- it will be properly scheduled when the scheduler starts" in caplog.messages
    assert "Starting scheduler" in caplog.messages
    assert 'Added job "my_job" to job store "default"' in caplog.messages
