from phonecam.runtime import RuntimeStatus


def test_runtime_status_reports_stream_and_virtual_camera_state():
    status = RuntimeStatus()
    status.set_stream(True)
    status.set_virtual_camera(device='OBS Virtual Camera', error=None)

    snapshot = status.snapshot()
    assert snapshot == {
        'stream_connected': True,
        'virtual_camera_active': True,
        'virtual_camera_device': 'OBS Virtual Camera',
        'virtual_camera_error': None,
    }


def test_runtime_status_records_virtual_camera_error():
    status = RuntimeStatus()
    status.set_virtual_camera(device=None, error='OBS Virtual Camera not found')
    assert status.snapshot()['virtual_camera_active'] is False
    assert status.snapshot()['virtual_camera_error'] == 'OBS Virtual Camera not found'
