import pytest
from fastapi.testclient import TestClient
from backend.app.main import app
from backend.app.database import get_db
from backend.app.services.auth_service import create_access_token
import os

@pytest.fixture
def client():
    return TestClient(app)

@pytest.fixture
def prod_origin():
    return "https://gym-nine-xi-65.vercel.app"

def test_preflight_options_for_production_origin(client, prod_origin):
    """
    Test preflight OPTIONS request from the exact production frontend origin
    https://gym-nine-xi-65.vercel.app with POST, Authorization, and Content-Type.
    """
    resp = client.options(
        "/api/v1/chat/message",
        headers={
            "Origin": prod_origin,
            "Access-Control-Request-Method": "POST",
            "Access-Control-Request-Headers": "authorization, content-type",
        },
    )
    assert resp.status_code == 200
    assert resp.headers.get("access-control-allow-origin") == prod_origin
    assert resp.headers.get("access-control-allow-credentials") == "true"
    
    allow_methods = resp.headers.get("access-control-allow-methods", "")
    assert "POST" in allow_methods
    assert "OPTIONS" in allow_methods
    
    allow_headers = resp.headers.get("access-control-allow-headers", "").lower()
    assert "authorization" in allow_headers
    assert "content-type" in allow_headers

def test_post_chat_message_cors_headers_unauthorized(client, prod_origin):
    """
    Ensure unauthorized POST request still returns CORS headers so browser
    reads 401 instead of opaque CORS error.
    """
    resp = client.post(
        "/api/v1/chat/message",
        headers={"Origin": prod_origin},
        json={"message": "hello"},
    )
    assert resp.status_code == 401
    assert resp.headers.get("access-control-allow-origin") == prod_origin
    assert resp.headers.get("access-control-allow-credentials") == "true"
    body = resp.json()
    assert body.get("success") is False
    assert "Authorization" in body.get("message", "")

@pytest.mark.asyncio
async def test_post_chat_message_cors_headers_authorized(client, prod_origin):
    """
    Ensure authenticated POST request returns 200, valid assistant response,
    and correct CORS headers.
    """
    db = get_db()
    test_user_id = "test_cors_verified_user"
    await db.users.insert_one({
        "id": test_user_id,
        "email": "cors_test@fit.com",
        "name": "CORS Tester",
        "role": "USER",
    })

    token = create_access_token({"sub": test_user_id, "role": "USER"})
    resp = client.post(
        "/api/v1/chat/message",
        headers={
            "Origin": prod_origin,
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
        },
        json={"message": "Suggest a healthy breakfast"},
    )
    assert resp.status_code == 200
    assert resp.headers.get("access-control-allow-origin") == prod_origin
    assert resp.headers.get("access-control-allow-credentials") == "true"
    
    body = resp.json()
    assert body.get("success") is True
    assert "data" in body
    assert "message" in body["data"]

def test_preflight_options_for_local_origins(client):
    """
    Ensure local development origins continue to work seamlessly.
    """
    for local_origin in ["http://localhost:5173", "http://127.0.0.1:5173", "http://localhost:3000"]:
        resp = client.options(
            "/api/v1/chat/message",
            headers={
                "Origin": local_origin,
                "Access-Control-Request-Method": "POST",
                "Access-Control-Request-Headers": "authorization, content-type",
            },
        )
        assert resp.status_code == 200
        assert resp.headers.get("access-control-allow-origin") == local_origin
        assert resp.headers.get("access-control-allow-credentials") == "true"

def test_preflight_options_for_preview_vercel_origin(client):
    """
    Ensure wildcard/regex Vercel preview deploys also receive proper CORS response.
    """
    preview_origin = "https://gym-preview-branch-test.vercel.app"
    resp = client.options(
        "/api/v1/chat/message",
        headers={
            "Origin": preview_origin,
            "Access-Control-Request-Method": "POST",
            "Access-Control-Request-Headers": "authorization, content-type",
        },
    )
    assert resp.status_code == 200
    assert resp.headers.get("access-control-allow-origin") == preview_origin

def test_disallowed_origin_rejected(client):
    """
    Ensure untrusted / foreign origins are NOT given Access-Control-Allow-Origin.
    """
    resp = client.options(
        "/api/v1/chat/message",
        headers={
            "Origin": "https://malicious-site.com",
            "Access-Control-Request-Method": "POST",
            "Access-Control-Request-Headers": "authorization",
        },
    )
    # Starlette returns 400 Disallowed CORS origin for disallowed preflight origins
    assert resp.headers.get("access-control-allow-origin") is None

def test_frontend_api_base_url_configuration():
    """
    Verify frontend configuration files point to the production backend on Render.
    """
    prod_env_path = os.path.join(os.path.dirname(__file__), "..", "frontend", ".env.production")
    with open(prod_env_path, "r", encoding="utf-8") as f:
        content = f.read()
    assert "https://gym-ikjt.onrender.com" in content

@pytest.mark.asyncio
async def test_offset_naive_datetime_subtraction_regression(client, prod_origin):
    """
    Regression test: PyMongo returns offset-naive datetimes in conversation_messages.
    Ensure ChatService.handle_user_message does not crash with
    'TypeError: can't subtract offset-naive and offset-aware datetimes'.
    """
    from datetime import datetime
    import uuid

    db = get_db()
    user_id = f"user_naive_{uuid.uuid4().hex[:8]}"
    await db.users.insert_one({"id": user_id, "email": f"{user_id}@test.com", "role": "USER"})

    session_id = f"session_naive_{uuid.uuid4().hex[:8]}"
    await db.chat_sessions.insert_one({
        "id": session_id,
        "user_id": user_id,
        "title": "Naive DT Test",
        "created_at": datetime.now(),  # naive datetime as returned by PyMongo
    })

    # Insert a prior user message with a naive datetime
    await db.conversation_messages.insert_one({
        "id": f"msg_naive_{uuid.uuid4().hex[:8]}",
        "session_id": session_id,
        "sender": "USER",
        "message": "1 bowl dal khadhi",
        "created_at": datetime.now(),  # naive datetime
    })

    token = create_access_token({"sub": user_id, "role": "USER"})
    # Send another message to trigger the duplicate check that compares now (aware) with past (naive)
    resp = client.post(
        "/api/v1/chat/message",
        headers={
            "Origin": prod_origin,
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
        },
        json={
            "message": "1 bowl dal khadhi",
            "sessionId": session_id,
        },
    )
    assert resp.status_code == 200, f"Expected 200 but got {resp.status_code}: {resp.text}"
    body = resp.json()
    assert body.get("success") is True

