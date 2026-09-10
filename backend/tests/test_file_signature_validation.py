"""P9-9: Magic-byte upload validation — genuine files pass, disguised files fail.

Uses real file signatures only (no network, no secrets).
"""
import io
import uuid

import pytest

from app.core.security import create_access_token
from app.models import User


@pytest.fixture
def auth_headers(test_db):
    user = User(id=uuid.uuid4(), phone="+919876500301", full_name="Sig User", is_active=True)
    test_db.add(user)
    test_db.commit()
    token = create_access_token(data={"sub": str(user.id), "role": "user"})
    return {"Authorization": f"Bearer {token}"}


def _upload(client, headers, filename, content, mime, doc_type="pan"):
    return client.post(
        "/documents/upload",
        data={"doc_type": doc_type},
        files={"file": (filename, io.BytesIO(content), mime)},
        headers=headers,
    )


def test_valid_png_signature_accepted(client, auth_headers):
    res = _upload(client, auth_headers, "a.png", b"\x89PNG\r\n\x1a\n" + b"\x00" * 64, "image/png", "aadhaar")
    assert res.status_code == 200


def test_valid_jpeg_signature_accepted(client, auth_headers):
    res = _upload(client, auth_headers, "p.jpg", b"\xFF\xD8\xFF\xE0" + b"\x00" * 64, "image/jpeg")
    assert res.status_code == 200


def test_valid_pdf_signature_accepted(client, auth_headers):
    res = _upload(client, auth_headers, "d.pdf", b"%PDF-1.4 project report content", "application/pdf", "project_report")
    assert res.status_code == 200


def test_png_bytes_with_pdf_name_rejected(client, auth_headers):
    """PNG content renamed to .pdf with matching PDF MIME must still be rejected."""
    res = _upload(client, auth_headers, "evil.pdf", b"\x89PNG\r\n\x1a\n" + b"\x00" * 64, "application/pdf")
    assert res.status_code == 400
    assert "signature" in res.json()["detail"].lower()


def test_executable_bytes_with_png_name_rejected(client, auth_headers):
    """MZ executable renamed to .png with image MIME must be rejected by signature."""
    res = _upload(client, auth_headers, "evil.png", b"MZ\x90\x00" + b"\x00" * 64, "image/png")
    assert res.status_code == 400
    assert "signature" in res.json()["detail"].lower()


def test_gif_bytes_with_png_name_rejected(client, auth_headers):
    res = _upload(client, auth_headers, "evil.png", b"GIF89a" + b"\x00" * 64, "image/png")
    assert res.status_code == 400


def test_empty_file_still_rejected(client, auth_headers):
    res = _upload(client, auth_headers, "empty.pdf", b"", "application/pdf")
    assert res.status_code == 400


def test_disallowed_extension_still_rejected(client, auth_headers):
    res = _upload(client, auth_headers, "run.exe", b"MZ\x90\x00", "application/x-msdownload")
    assert res.status_code == 400
