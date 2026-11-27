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


def test_tasks_default_to_due_date_sort_with_unset_dates_last(client):
    """
    デフォルトのソート方法（"due_date"）では期限日の昇順に並び、
    期限未設定のタスクは日付の有無にかかわらず常に最後に表示されることを確認する。
    """
    _register_and_login(client)

    client.post("/api/tasks", json={"title": "期限なしタスク"})
    client.post("/api/tasks", json={"title": "遅い期限", "due_date": "2026-12-31"})
    client.post("/api/tasks", json={"title": "早い期限", "due_date": "2026-12-01"})

    tasks = client.get("/api/tasks").json()
    titles = [task["title"] for task in tasks]

    assert titles == ["早い期限", "遅い期限", "期限なしタスク"]


def test_sort_preference_title_orders_by_title(client):
    """ソート方法を "title" に変更すると、タスク名の昇順で一覧が返ることを確認する。"""
    _register_and_login(client)

    client.post("/api/tasks", json={"title": "ぶどう"})
    client.post("/api/tasks", json={"title": "あんず"})
    client.post("/api/tasks", json={"title": "いちご"})

    update_response = client.patch("/api/auth/me/sort-preference", json={"sort_preference": "title"})
    assert update_response.status_code == 200
    assert update_response.json()["sort_preference"] == "title"

    tasks = client.get("/api/tasks").json()
    titles = [task["title"] for task in tasks]

    assert titles == ["あんず", "いちご", "ぶどう"]


def test_sort_preference_is_persisted_and_returned_by_me(client):
    """
    設定したソート方法がDBに保存され、GET /api/auth/me で返るユーザー情報にも
    反映されることを確認する（別端末からログインしても同じ設定が復元されることの裏付け）。
    """
    _register_and_login(client)

    client.patch("/api/auth/me/sort-preference", json={"sort_preference": "manual"})

    me_response = client.get("/api/auth/me")
    assert me_response.json()["sort_preference"] == "manual"


def test_new_task_is_appended_to_end_of_manual_order(client):
    """
    手動並び替え（"manual"）のソート方法のとき、新規作成したタスクは
    常に一覧の最後尾に追加されることを確認する。
    """
    _register_and_login(client)
    client.patch("/api/auth/me/sort-preference", json={"sort_preference": "manual"})

    client.post("/api/tasks", json={"title": "1番目"})
    client.post("/api/tasks", json={"title": "2番目"})
    client.post("/api/tasks", json={"title": "3番目"})

    tasks = client.get("/api/tasks").json()
    titles = [task["title"] for task in tasks]

    assert titles == ["1番目", "2番目", "3番目"]


def test_reorder_tasks_updates_manual_order(client):
    """
    ドラッグ&ドロップ後に呼ばれる並び替えAPI（PATCH /api/tasks/reorder）で
    新しい順序を渡すと、手動並び替え（"manual"）での一覧順がその通りになることを確認する。
    """
    _register_and_login(client)
    client.patch("/api/auth/me/sort-preference", json={"sort_preference": "manual"})

    first = client.post("/api/tasks", json={"title": "1番目"}).json()
    second = client.post("/api/tasks", json={"title": "2番目"}).json()
    third = client.post("/api/tasks", json={"title": "3番目"}).json()

    # 元の順序は [1番目, 2番目, 3番目] だが、[3番目, 1番目, 2番目] に並び替える。
    reorder_response = client.patch(
        "/api/tasks/reorder", json={"task_ids": [third["id"], first["id"], second["id"]]}
    )
    assert reorder_response.status_code == 200

    tasks = client.get("/api/tasks").json()
    titles = [task["title"] for task in tasks]

    assert titles == ["3番目", "1番目", "2番目"]


def test_reorder_tasks_rejects_other_users_task_id(client):
    """
    並び替えAPIに他ユーザーのタスクIDが混ざっている（＝自分の全タスクIDの集合と一致しない）
    場合は404エラーになり、不正な並び替えが行われないことを確認する。
    """
    _register_and_login(client, username="owner", password="password123")
    own_task = client.post("/api/tasks", json={"title": "ownerのタスク"}).json()

    client.post("/api/auth/logout")
    _register_and_login(client, username="intruder", password="password123")
    other_task = client.post("/api/tasks", json={"title": "intruderのタスク"}).json()

    # intruderとしてログイン中、ownerのタスクIDを混ぜて並び替えを試みる。
    reorder_response = client.patch(
        "/api/tasks/reorder", json={"task_ids": [own_task["id"], other_task["id"]]}
    )
    assert reorder_response.status_code == 404
