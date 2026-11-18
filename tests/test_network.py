import ssl

from retina_sensitivity import network


def test_download_uses_verified_truststore_context(monkeypatch):
    context = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
    calls = {}
    sentinel = object()

    monkeypatch.delenv("SSL_CERT_FILE", raising=False)
    monkeypatch.setattr(network.truststore, "SSLContext", lambda protocol: context)

    def fake_urlopen(request, timeout, context):
        calls.update(request=request, timeout=timeout, context=context)
        return sentinel

    monkeypatch.setattr(network, "urlopen", fake_urlopen)
    result = network.open_verified_url("https://example.org/data.zip", timeout=30)

    assert result is sentinel
    assert calls["timeout"] == 30
    assert calls["context"].verify_mode == ssl.CERT_REQUIRED
    assert calls["context"].check_hostname is True
