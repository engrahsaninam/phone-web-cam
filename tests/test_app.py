from fastapi.testclient import TestClient

from phonecam.app import create_app
from phonecam.pairing import PairingToken
from phonecam.runtime import RuntimeStatus


class FakePeerManager:
    def __init__(self):
        self.received = []

    async def handle_offer(self, sdp: str, offer_type: str):
        self.received.append((sdp, offer_type))
        return {'sdp': 'answer-sdp', 'type': 'answer'}

    async def close(self):
        return None


def make_client():
    token = PairingToken('secret-token')
    manager = FakePeerManager()
    status = RuntimeStatus()
    app = create_app(token=token, peer_manager=manager, runtime_status=status)
    return TestClient(app), manager


def test_offer_rejects_wrong_pairing_token():
    client, manager = make_client()
    response = client.post('/api/offer?token=wrong', json={'sdp': 'offer', 'type': 'offer'})
    assert response.status_code == 403
    assert manager.received == []


def test_offer_accepts_correct_pairing_token():
    client, manager = make_client()
    response = client.post('/api/offer?token=secret-token', json={'sdp': 'offer-sdp', 'type': 'offer'})
    assert response.status_code == 200
    assert response.json() == {'sdp': 'answer-sdp', 'type': 'answer'}
    assert manager.received == [('offer-sdp', 'offer')]


def test_status_is_pairing_token_protected():
    client, _ = make_client()
    assert client.get('/api/status?token=wrong').status_code == 403
    assert client.get('/api/status?token=secret-token').status_code == 200
