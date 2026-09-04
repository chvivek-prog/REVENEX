
from pathlib import Path
from revenex.api import webauthn_auth


def test_webauthn_module_contract():
    assert callable(webauthn_auth.registration_options)
    assert callable(webauthn_auth.registration_verify)
    assert callable(webauthn_auth.authentication_options)
    assert callable(webauthn_auth.authentication_verify)
    assert callable(webauthn_auth.has_credentials)


def test_dashboard_has_real_passkey_ui():
    html = Path(
        "frontend/revenue_command_center.html"
    ).read_text()

    assert "REVENEX_REAL_PASSKEY_UI_V1" in html
    assert "navigator.credentials.create" in html
    assert "navigator.credentials.get" in html
