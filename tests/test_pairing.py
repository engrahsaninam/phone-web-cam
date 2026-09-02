from phonecam.pairing import PairingToken


def test_pairing_token_is_url_safe_and_long_enough():
    token = PairingToken.create()
    assert len(token.value) >= 32
    assert all(ch.isalnum() or ch in '-_' for ch in token.value)


def test_pairing_token_requires_exact_match():
    token = PairingToken('abc123')
    assert token.matches('abc123') is True
    assert token.matches('ABC123') is False
    assert token.matches('abc123 ') is False
    assert token.matches(None) is False
