# タスク管理機能（作成・一覧・更新・削除）のテスト。
# 「他人のタスクにはアクセスできない」というアクセス制御の確認も含む。


def _register_and_login(client, username="taskuser", password="password123"):
    """テスト用のヘルパー関数。ユーザー登録とログインをまとめて行う。"""
    client.post("/api/auth/register", json={"username": username, "password": password})
    client.post("/api/auth/login", json={"username": username, "password": password})


def test_create_task_requires_login(client):
    """未ログイン状態でタスクを作成しようとすると401になることを確認する。"""
    response = client.post("/api/tasks", json={"title": "ログイン前のタスク"})

    assert response.status_code == 401


def test_create_and_list_task(client):
    """タスクを作成し、一覧に反映されることを確認する。"""
    _register_and_login(client)

    create_response = client.post(
        "/api/tasks", json={"title": "買い物に行く", "description": "牛乳を買う"}
    )
    assert create_response.status_code == 201
    created = create_response.json()
    assert created["title"] == "買い物に行く"
    assert created["is_done"] is False

    list_response = client.get("/api/tasks")
    assert list_response.status_code == 200
    tasks = list_response.json()
    assert len(tasks) == 1
    assert tasks[0]["title"] == "買い物に行く"


def test_update_task_marks_as_done(client):
    """タスクの完了フラグを更新でき、タイトル等の他の項目は変わらないことを確認する。"""
    _register_and_login(client)
    created = client.post("/api/tasks", json={"title": "完了予定のタスク"}).json()

    update_response = client.patch(f"/api/tasks/{created['id']}", json={"is_done": True})

    assert update_response.status_code == 200
    updated = update_response.json()
    assert updated["is_done"] is True
    # タイトルは更新対象に含めていないので変化しないはず。
    assert updated["title"] == "完了予定のタスク"


def test_delete_task(client):
    """タスクを削除すると一覧から消えることを確認する。"""
    _register_and_login(client)
    created = client.post("/api/tasks", json={"title": "削除予定のタスク"}).json()

    delete_response = client.delete(f"/api/tasks/{created['id']}")
    assert delete_response.status_code == 204

    list_response = client.get("/api/tasks")
    assert list_response.json() == []


def test_user_cannot_access_other_users_task(client):
    """
    別ユーザーが作成したタスクには、IDを指定してもアクセス（更新・削除）できないことを確認する。
    要件定義書の「他ユーザーのタスクは参照・操作できない」を担保する最重要テスト。
    """
    # ユーザー1がタスクを作成する。
    _register_and_login(client, username="owner", password="password123")
    task = client.post("/api/tasks", json={"title": "ownerのタスク"}).json()

    # ユーザー2としてログインし直す（ログアウトしてから別ユーザーでログイン）。
    client.post("/api/auth/logout")
    _register_and_login(client, username="intruder", password="password123")

    # ユーザー2から見ると、ユーザー1のタスク一覧には何も見えないはず。
    list_response = client.get("/api/tasks")
    assert list_response.json() == []

    # ユーザー2がユーザー1のタスクを更新・削除しようとしても404になるべき（存在を教えない）。
    update_response = client.patch(f"/api/tasks/{task['id']}", json={"is_done": True})
    assert update_response.status_code == 404

    delete_response = client.delete(f"/api/tasks/{task['id']}")
    assert delete_response.status_code == 404
