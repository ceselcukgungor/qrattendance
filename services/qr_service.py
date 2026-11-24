"""QR token issuance, check-in URL construction, and QR image rendering."""
import base64
import io
import secrets
import socket
import time
from urllib.parse import urlencode

import qrcode

from repositories import qr_token_repository
from services import session_service

TOKEN_TTL_SECONDS = 45.0
TOKEN_BYTES = 24
FALLBACK_HOST = "127.0.0.1"
CHECKIN_PATH = "/checkin"


def get_lan_ip():
    """Return the host's LAN IPv4 address, or 127.0.0.1 if none can be determined.

    Connecting a UDP socket sends no packets; it only selects the outbound interface.
    """
    probe = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        probe.connect(("10.255.255.255", 1))
        address = probe.getsockname()[0]
    except OSError:
        return FALLBACK_HOST
    finally:
        probe.close()
    return address if address and not address.startswith("0.") else FALLBACK_HOST


def build_checkin_url(token, port, host=None):
    host = host or get_lan_ip()
    return f"http://{host}:{port}{CHECKIN_PATH}?{urlencode({'token': token})}"


def render_qr_data_uri(data):
    """Render data as a QR code PNG and return it as a base64 data URI."""
    qr = qrcode.QRCode(error_correction=qrcode.constants.ERROR_CORRECT_M, box_size=10, border=2)
    qr.add_data(data)
    qr.make(fit=True)
    buffer = io.BytesIO()
    qr.make_image(fill_color="black", back_color="white").save(buffer, format="PNG")
    encoded = base64.b64encode(buffer.getvalue()).decode("ascii")
    return f"data:image/png;base64,{encoded}"


def generate_token():
    return secrets.token_urlsafe(TOKEN_BYTES)


def issue_token(session_id, port, host=None):
    """Create and persist a new token for an active session and return its QR payload.

    Raises NotFoundError or SessionClosedError if the session is missing or closed.
    """
    session_service.require_active_session(session_id)

    token = generate_token()
    created_at = time.time()
    qr_token_repository.create_token(session_id, token, created_at)

    checkin_url = build_checkin_url(token, port, host)
    return {
        "token": token,
        "created_at": created_at,
        "ttl_seconds": TOKEN_TTL_SECONDS,
        "checkin_url": checkin_url,
        "qr_image": render_qr_data_uri(checkin_url),
    }


def is_token_fresh(created_at, now=None):
    now = time.time() if now is None else now
    return now - created_at <= TOKEN_TTL_SECONDS


def purge_expired_tokens():
    """Delete tokens past their TTL; returns the number of rows removed."""
    return qr_token_repository.delete_tokens_created_before(time.time() - TOKEN_TTL_SECONDS)
