# ブラウザに表示するHTMLページ（画面）を返すルーター。
# app/auth/router.py や app/tasks/router.py はJSONを返す「APIエンドポイント」だが、
# ここで定義するのはJinja2テンプレートを使ってHTMLを返す「画面用エンドポイント」。
from fastapi import APIRouter, Request
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates

router = APIRouter()

# app/templates/ 以下のHTMLファイルをテンプレートとして読み込む設定。
templates = Jinja2Templates(directory="app/templates")


@router.get("/")
def index():
    """
    トップページへのアクセスは、常にタスク一覧ページへリダイレクトする。
    ログインしていない場合は、tasks.js側のチェックでログイン画面に飛ばされる。
    """
    return RedirectResponse(url="/tasks")


@router.get("/login")
def login_page(request: Request):
    """ログイン画面を表示する。"""
    return templates.TemplateResponse(request, "login.html")


@router.get("/register")
def register_page(request: Request):
    """新規登録画面を表示する。"""
    return templates.TemplateResponse(request, "register.html")


@router.get("/tasks")
def tasks_page(request: Request):
    """
    タスク一覧画面を表示する。
    実際のログインチェックやデータ取得はこの画面から読み込まれるJS（tasks.js）が
    APIを呼んで行うため、このルート自体は常にHTMLを返すだけで良い。
    """
    return templates.TemplateResponse(request, "tasks.html")
