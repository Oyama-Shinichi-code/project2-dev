// ログイン画面（login.html）専用のロジック。

// HTML上の要素を取得しておく。
const loginForm = document.getElementById("login-form");
const errorMessageEl = document.getElementById("error-message");

/**
 * エラーメッセージを画面に表示する。
 * hidden属性を外すことで、普段は非表示になっているエラー欄を見せる。
 */
function showError(message) {
    errorMessageEl.textContent = message;
    errorMessageEl.hidden = false;
}

// フォームが送信されたときの処理。
loginForm.addEventListener("submit", async (event) => {
    // デフォルトの「ページ遷移してサーバーにフォームを送る」動作を止め、
    // 代わりにJavaScriptでAPIを呼ぶ（SPA的な挙動にする）。
    event.preventDefault();

    const username = document.getElementById("username").value;
    const password = document.getElementById("password").value;

    const result = await api.login(username, password);

    if (result.ok) {
        // ログイン成功したらタスク一覧画面へ遷移する。
        window.location.href = "/tasks";
    } else {
        // 401などのエラー時は、サーバーから返ってきたdetailメッセージを表示する。
        const detail = result.data && result.data.detail ? result.data.detail : "ログインに失敗しました";
        showError(detail);
    }
});
