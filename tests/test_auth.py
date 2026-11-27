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


def test_delete_account_requires_login(client):
    """未ログイン状態でアカウント削除（DELETE /api/auth/me）を呼ぶと401になることを確認する。"""
    response = client.request(
        "DELETE", "/api/auth/me", json={"password": "password123"}
    )

    assert response.status_code == 401


def test_delete_account_with_wrong_password_fails(client):
    """
    パスワードが間違っている場合は403エラーになり、アカウントが削除されない
    （本人確認を突破できないことを保証する）。
    """
    client.post("/api/auth/register", json={"username": "grace", "password": "password123"})
    client.post("/api/auth/login", json={"username": "grace", "password": "password123"})

    response = client.request(
        "DELETE", "/api/auth/me", json={"password": "wrongpassword"}
    )
    assert response.status_code == 403

    # 削除されていないので、引き続き自分の情報が取得できるはず。
    me_response = client.get("/api/auth/me")
    assert me_response.status_code == 200


def test_delete_account_with_correct_password_succeeds(client):
    """
    正しいパスワードを入力するとアカウントが削除され、
    以降はセッションも無効化されて /auth/me にアクセスできなくなることを確認する。
    """
    client.post("/api/auth/register", json={"username": "henry", "password": "password123"})
    client.post("/api/auth/login", json={"username": "henry", "password": "password123"})

    response = client.request(
        "DELETE", "/api/auth/me", json={"password": "password123"}
    )
    assert response.status_code == 204

    me_response = client.get("/api/auth/me")
    assert me_response.status_code == 401

    # 同じユーザー名で再度登録できる（完全に削除されたことの確認）。
    register_response = client.post(
        "/api/auth/register", json={"username": "henry", "password": "newpassword123"}
    )
    assert register_response.status_code == 201


def test_delete_account_also_deletes_own_tasks(client):
    """アカウントを削除すると、そのユーザーが作成したタスクも一緒に削除されることを確認する。"""
    client.post("/api/auth/register", json={"username": "iris", "password": "password123"})
    client.post("/api/auth/login", json={"username": "iris", "password": "password123"})
    client.post("/api/tasks", json={"title": "irisのタスク"})

    client.request("DELETE", "/api/auth/me", json={"password": "password123"})

    # 同じユーザー名で登録し直しても、削除されたはずの古いタスクは見えない
    # （タスクがDBに残っていればここでバグが露呈する）。
    client.post("/api/auth/register", json={"username": "iris", "password": "newpassword123"})
    client.post("/api/auth/login", json={"username": "iris", "password": "newpassword123"})

    list_response = client.get("/api/tasks")
    assert list_response.json() == []
