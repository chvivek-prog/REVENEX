
from __future__ import annotations

import base64
import hashlib
import json
import secrets
import sqlite3
import time
from pathlib import Path
from typing import Any

from webauthn import (
    generate_authentication_options,
    generate_registration_options,
    options_to_json,
    verify_authentication_response,
    verify_registration_response,
)
from webauthn.helpers.structs import (
    PublicKeyCredentialDescriptor,
    ResidentKeyRequirement,
    UserVerificationRequirement,
)

DB_PATH = Path(__file__).resolve().parents[2] / "revenex_webauthn.sqlite3"

RP_ID = "localhost"
ORIGIN = "http://localhost:8787"
RP_NAME = "REVENEX Intelligence Platform"

CHALLENGE_TTL = 300


def _db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("""
        CREATE TABLE IF NOT EXISTS webauthn_credentials (
            credential_id TEXT PRIMARY KEY,
            user_email TEXT NOT NULL,
            public_key TEXT NOT NULL,
            sign_count INTEGER NOT NULL DEFAULT 0,
            created_at INTEGER NOT NULL
        )
    """)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS webauthn_challenges (
            challenge_id TEXT PRIMARY KEY,
            user_email TEXT NOT NULL,
            challenge TEXT NOT NULL,
            ceremony TEXT NOT NULL,
            expires_at INTEGER NOT NULL
        )
    """)
    conn.commit()
    return conn


def _b64(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).rstrip(b"=").decode()


def _unb64(value: str) -> bytes:
    return base64.urlsafe_b64decode(value + "=" * (-len(value) % 4))


def _challenge(email: str, ceremony: str):
    raw = secrets.token_bytes(32)
    challenge_id = secrets.token_urlsafe(24)

    conn = _db()
    conn.execute(
        "DELETE FROM webauthn_challenges WHERE expires_at < ?",
        (int(time.time()),),
    )
    conn.execute(
        """
        INSERT INTO webauthn_challenges
        (challenge_id,user_email,challenge,ceremony,expires_at)
        VALUES (?,?,?,?,?)
        """,
        (
            challenge_id,
            email,
            _b64(raw),
            ceremony,
            int(time.time()) + CHALLENGE_TTL,
        ),
    )
    conn.commit()
    conn.close()

    return challenge_id, raw


def _consume(challenge_id: str, ceremony: str):
    conn = _db()
    row = conn.execute(
        """
        SELECT * FROM webauthn_challenges
        WHERE challenge_id=? AND ceremony=? AND expires_at>=?
        """,
        (challenge_id, ceremony, int(time.time())),
    ).fetchone()

    if not row:
        conn.close()
        raise ValueError("Invalid or expired WebAuthn challenge")

    conn.execute(
        "DELETE FROM webauthn_challenges WHERE challenge_id=?",
        (challenge_id,),
    )
    conn.commit()
    conn.close()

    return row["user_email"], _unb64(row["challenge"])


def registration_options(email: str):
    email = email.strip().lower()
    if not email:
        raise ValueError("Workspace email is required")

    challenge_id, challenge = _challenge(email, "registration")

    options = generate_registration_options(
        rp_id=RP_ID,
        rp_name=RP_NAME,
        user_name=email,
        user_display_name="REVENEX Workspace",
        user_id=hashlib.sha256(email.encode()).digest(),
        challenge=challenge,
        timeout=120000,
        resident_key=ResidentKeyRequirement.PREFERRED,
        user_verification=UserVerificationRequirement.REQUIRED,
    )

    return {
        "challenge_id": challenge_id,
        "options": json.loads(options_to_json(options)),
    }


def registration_verify(email: str, challenge_id: str, credential: dict[str, Any]):
    stored_email, challenge = _consume(challenge_id, "registration")

    if stored_email != email.strip().lower():
        raise ValueError("Challenge belongs to another workspace")

    verification = verify_registration_response(
        credential=credential,
        expected_challenge=challenge,
        expected_rp_id=RP_ID,
        expected_origin=ORIGIN,
        require_user_verification=True,
    )

    credential_id = _b64(verification.credential_id)
    public_key = _b64(verification.credential_public_key)

    conn = _db()
    conn.execute(
        """
        INSERT OR REPLACE INTO webauthn_credentials
        (credential_id,user_email,public_key,sign_count,created_at)
        VALUES (?,?,?,?,?)
        """,
        (
            credential_id,
            email.strip().lower(),
            public_key,
            verification.sign_count,
            int(time.time()),
        ),
    )
    conn.commit()
    conn.close()

    return {
        "verified": True,
        "credential_id": credential_id,
    }


def authentication_options(email: str):
    email = email.strip().lower()

    conn = _db()
    rows = conn.execute(
        """
        SELECT credential_id
        FROM webauthn_credentials
        WHERE user_email=?
        """,
        (email,),
    ).fetchall()
    conn.close()

    if not rows:
        raise ValueError("No Passkey registered for this workspace")

    descriptors = [
        PublicKeyCredentialDescriptor(id=_unb64(row["credential_id"]))
        for row in rows
    ]

    challenge_id, challenge = _challenge(email, "authentication")

    options = generate_authentication_options(
        rp_id=RP_ID,
        challenge=challenge,
        allow_credentials=descriptors,
        timeout=120000,
        user_verification=UserVerificationRequirement.REQUIRED,
    )

    return {
        "challenge_id": challenge_id,
        "options": json.loads(options_to_json(options)),
    }


def authentication_verify(
    email: str,
    challenge_id: str,
    credential: dict[str, Any],
):
    stored_email, challenge = _consume(challenge_id, "authentication")

    email = email.strip().lower()

    if stored_email != email:
        raise ValueError("Challenge belongs to another workspace")

    credential_id = credential.get("rawId") or credential.get("id")
    if not credential_id:
        raise ValueError("Missing credential ID")

    conn = _db()
    row = conn.execute(
        """
        SELECT * FROM webauthn_credentials
        WHERE credential_id=? AND user_email=?
        """,
        (credential_id, email),
    ).fetchone()

    if not row:
        conn.close()
        raise ValueError("Unknown Passkey")

    verification = verify_authentication_response(
        credential=credential,
        expected_challenge=challenge,
        expected_rp_id=RP_ID,
        expected_origin=ORIGIN,
        credential_public_key=_unb64(row["public_key"]),
        credential_current_sign_count=row["sign_count"],
        require_user_verification=True,
    )

    conn.execute(
        """
        UPDATE webauthn_credentials
        SET sign_count=?
        WHERE credential_id=?
        """,
        (
            verification.new_sign_count,
            row["credential_id"],
        ),
    )
    conn.commit()
    conn.close()

    return {
        "verified": True,
        "email": email,
        "credential_id": row["credential_id"],
        "sign_count": verification.new_sign_count,
    }


def has_credentials(email: str) -> bool:
    conn = _db()
    row = conn.execute(
        """
        SELECT 1 FROM webauthn_credentials
        WHERE user_email=? LIMIT 1
        """,
        (email.strip().lower(),),
    ).fetchone()
    conn.close()
    return row is not None
