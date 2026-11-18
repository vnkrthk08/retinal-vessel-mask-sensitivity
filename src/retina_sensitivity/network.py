from __future__ import annotations

import os
import ssl
from urllib.error import URLError
from urllib.request import Request, urlopen

import truststore


def open_verified_url(request: Request, timeout: int = 90):
    context = truststore.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
    custom_ca = os.environ.get("SSL_CERT_FILE")
    if custom_ca:
        context.load_verify_locations(cafile=custom_ca)
    try:
        return urlopen(request, timeout=timeout, context=context)
    except URLError as exc:
        if isinstance(exc.reason, ssl.SSLCertVerificationError):
            raise RuntimeError(
                "HTTPS certificate verification failed. Update the system root certificates, "
                "or set SSL_CERT_FILE to a PEM CA bundle trusted by your organization. "
                "Certificate verification remains enabled."
            ) from exc
        raise
