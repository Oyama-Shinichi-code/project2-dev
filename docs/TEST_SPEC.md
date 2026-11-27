# テスト仕様一覧

このドキュメントは、`tests/` に書かれている自動テストの内容を、プログラムを読まなくても
把握できるように一覧化したものです。「このアプリは何ができて、何をエラーにするのか」という
仕様書としての役割を持ちます。

**運用ルール**: 新しい機能を追加してテストを書いたら、必ずこのファイルにも対応する項目を追記する。
テストの内容を変更した場合は、このファイルの該当箇所も合わせて更新する。

テストを実行するには以下を実行する。

```
.venv/Scripts/python.exe -m pytest -v
```

---

## 認証機能（`tests/test_auth.py`）

ベースURL: `/api/auth`

| テスト名 | 確認している仕様 |
|---|---|
| `test_register_new_user_succeeds` | 新規ユーザー登録（`POST /api/auth/register`）が成功すると、201とユーザー情報（id・username）が返る。レスポンスに平文パスワード・ハッシュ化パスワードのどちらも含まれない。 |
| `test_register_duplicate_username_fails` | 既に存在するユーザー名で登録しようとすると400エラーになる（ユーザー名は一意）。 |
| `test_login_with_correct_credentials_succeeds` | 登録済みのユーザー名・パスワードでログイン（`POST /api/auth/login`）すると200とユーザー情報が返る。 |
| `test_login_with_wrong_password_fails` | パスワードが間違っている場合は401エラーになる。 |
| `test_me_without_login_returns_401` | ログインしていない状態で現在のユーザー情報取得（`GET /api/auth/me`）を呼ぶと401エラーになる。 |
| `test_me_after_login_returns_current_user` | ログイン後に `GET /api/auth/me` を呼ぶと、ログイン中の自分自身のユーザー情報が返る。 |
| `test_logout_then_me_returns_401` | ログアウト（`POST /api/auth/logout`）後は、再び `GET /api/auth/me` が401エラーになる（セッションが無効化される）。 |
| `test_delete_account_requires_login` | 未ログイン状態でアカウント削除（`DELETE /api/auth/me`）を呼ぶと401エラーになる。 |
| `test_delete_account_with_wrong_password_fails` | 本人確認用パスワードが間違っている場合は403エラーになり、アカウントは削除されない（削除後も `GET /api/auth/me` が成功することで確認）。 |
| `test_delete_account_with_correct_password_succeeds` | 正しいパスワードでアカウント削除すると204が返り、以降 `GET /api/auth/me` は401になる（セッションも無効化される）。削除後は同じユーザー名で再登録できる（完全に削除されたことの確認）。 |
| `test_delete_account_also_deletes_own_tasks` | アカウント削除時に、そのユーザーが作成したタスクも一緒に削除される（同名での再登録後、タスク一覧が空であることで確認）。 |

### このコードから分かる仕様（補足）
- ログイン状態はセッションCookieで管理する。ログインするとCookieが発行され、以降のリクエストはそのCookieで本人確認される。
- ユーザー名・パスワードが違う場合と、ユーザー名自体が存在しない場合は、同じ401エラーメッセージを返す（ユーザー名の存在を外部に推測されないようにするため）。
- アカウント削除は誤操作・第三者による削除を防ぐため、本人確認としてパスワードの再入力を必須とする（画面上は確認モーダルでパスワード入力を求める）。

---

## タスク管理機能（`tests/test_tasks.py`）

ベースURL: `/api/tasks`

| テスト名 | 確認している仕様 |
|---|---|
| `test_create_task_requires_login` | 未ログイン状態でタスクを作成（`POST /api/tasks`）しようとすると401エラーになる。 |
| `test_create_and_list_task` | タスクを作成すると、タイトル・詳細が保存され、`is_done` は初期値 `false` になる。作成したタスクは一覧取得（`GET /api/tasks`）に反映される。 |
| `test_update_task_marks_as_done` | タスクの完了フラグ（`is_done`）を部分更新（`PATCH /api/tasks/{id}`）できる。更新リクエストに含めなかった項目（タイトル等）は変化しない。 |
| `test_delete_task` | タスクを削除（`DELETE /api/tasks/{id}`）すると、一覧から消える。 |
| `test_user_cannot_access_other_users_task` | 他ユーザーが作成したタスクは、一覧に出てこない。IDを直接指定して更新・削除しようとしても404エラーになる（存在自体を教えない）。**アクセス制御の中核となる最重要テスト。** |

### このコードから分かる仕様（補足）
- タスク一覧は常にログイン中ユーザー自身のものだけが返る（他ユーザーのタスクは混在しない）。
- タスクのタイトルは必須、詳細（description）と期限（due_date）は任意。
- 更新APIは「指定したフィールドだけ」を変更する部分更新方式（PATCH）。

---

## 未カバーの観点（今後追加検討）
- タスクのタイトルが空文字・201文字以上の場合の挙動（バリデーションエラーになるはずだが、現時点でテスト未作成）。
- パスワードが8文字未満での新規登録時の挙動確認。
- 同時に複数のタスクを作成した際の並び順（作成日時の降順）の確認。

