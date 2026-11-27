# 認証機能（登録・ログイン・ログアウト）のテスト。
# fixtureの client（tests/conftest.py で定義）を使ってAPIにリクエストを送り、
# レスポンスの内容を検証する。


def test_register_new_user_succeeds(client):
    """新規ユーザー登録が成功し、作成されたユーザー情報が返ることを確認する。"""
    response = client.post(
        "/api/auth/register", json={"username": "alice", "password": "password123"}
    )

    assert response.status_code == 201
    body = response.json()
    assert body["username"] == "alice"
    # レスポンスにパスワード（平文・ハッシュ共に）が含まれていないことも確認する。
    assert "password" not in body
    assert "hashed_password" not in body


def test_register_duplicate_username_fails(client):
    """同じユーザー名で2回登録しようとすると400エラーになることを確認する。"""
    client.post("/api/auth/register", json={"username": "bob", "password": "password123"})
    response = client.post("/api/auth/register", json={"username": "bob", "password": "anotherpass"})

    assert response.status_code == 400


def test_login_with_correct_credentials_succeeds(client):
    """正しいユーザー名・パスワードでログインできることを確認する。"""
    client.post("/api/auth/register", json={"username": "carol", "password": "password123"})

    response = client.post(
        "/api/auth/login", json={"username": "carol", "password": "password123"}
    )

    assert response.status_code == 200
    assert response.json()["username"] == "carol"


def test_login_with_wrong_password_fails(client):
    """パスワードが間違っている場合は401エラーになることを確認する。"""
    client.post("/api/auth/register", json={"username": "dave", "password": "password123"})

    response = client.post(
        "/api/auth/login", json={"username": "dave", "password": "wrongpassword"}
    )

    assert response.status_code == 401


def test_me_without_login_returns_401(client):
    """ログインしていない状態で /auth/me にアクセスすると401になることを確認する。"""
    response = client.get("/api/auth/me")

    assert response.status_code == 401


def test_me_after_login_returns_current_user(client):
    """ログイン後は /auth/me で自分自身の情報が取得できることを確認する。"""
    client.post("/api/auth/register", json={"username": "erin", "password": "password123"})
    client.post("/api/auth/login", json={"username": "erin", "password": "password123"})

    response = client.get("/api/auth/me")

    assert response.status_code == 200
    assert response.json()["username"] == "erin"


def test_logout_then_me_returns_401(client):
    """ログアウト後は /auth/me にアクセスできなくなる（401になる）ことを確認する。"""
    client.post("/api/auth/register", json={"username": "frank", "password": "password123"})
    client.post("/api/auth/login", json={"username": "frank", "password": "password123"})

    logout_response = client.post("/api/auth/logout")
    assert logout_response.status_code == 200

    response = client.get("/api/auth/me")
    assert response.status_code == 401
