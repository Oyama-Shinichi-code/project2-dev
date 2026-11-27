// 新規登録画面（register.html）専用のロジック。

const registerForm = document.getElementById("register-form");
const errorMessageEl = document.getElementById("error-message");

function showError(message) {
    errorMessageEl.textContent = message;
    errorMessageEl.hidden = false;
}

registerForm.addEventListener("submit", async (event) => {
    event.preventDefault();

    const username = document.getElementById("username").value;
    const password = document.getElementById("password").value;

    const registerResult = await api.register(username, password);

    if (!registerResult.ok) {
        const detail = registerResult.data && registerResult.data.detail
            ? registerResult.data.detail
            : "登録に失敗しました";
        showError(detail);
        return;
    }

    // 登録が成功したら、そのままログインまで行ってタスク一覧へ遷移する
    // （ユーザーに「登録してからもう一度ログインし直す」という二度手間をさせない）。
    const loginResult = await api.login(username, password);

    if (loginResult.ok) {
        window.location.href = "/tasks";
    } else {
        // ここに到達するのは通常ありえないが、念のためログイン画面へ誘導する。
        window.location.href = "/login";
    }
});
