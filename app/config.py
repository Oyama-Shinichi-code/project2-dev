# アプリ全体の設定値（環境変数経由で読み込む値）をまとめるモジュール。
# 秘密鍵などをコード中にハードコードせず、環境変数 (.env) から読み込むことで、
# 誤って秘密情報をGitにコミットしてしまうリスクを減らす。
import os

# セッションCookieの暗号化・署名に使う秘密鍵。
# 本番運用する場合は必ず .env ファイルで独自の値を設定すること（.env は .gitignore で除外済み）。
# 開発用のデフォルト値は、万が一 .env を設定し忘れてもローカルでは動くようにするための仮の値。
SECRET_KEY = os.environ.get("SECRET_KEY", "dev-only-insecure-secret-key-change-me")
