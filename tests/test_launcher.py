from phonecam.launcher import build_pairing_url


def test_build_pairing_url_adds_url_encoded_token():
    assert build_pairing_url('https://example.trycloudflare.com', 'a+b/c') == (
        'https://example.trycloudflare.com/?token=a%2Bb%2Fc'
    )
