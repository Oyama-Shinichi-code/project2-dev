// バックエンドAPI（FastAPI）とのやり取りをまとめた共通モジュール。
// 各画面のJS（login.js, register.js, tasks.js）はこのファイルの関数を呼び出して使う。

/**
 * APIにリクエストを送る共通関数。
 * fetch()をそのまま使うと毎回ヘッダーやエラー処理を書く必要があるため、ここで一元化する。
 *
 * @param {string} path - APIのパス（例: "/auth/login"）
 * @param {string} method - HTTPメソッド（"GET", "POST", "PATCH", "DELETE" など）
 * @param {object|null} body - リクエストボディ（JSONとして送る値。無ければnull）
 * @returns {Promise<{ok: boolean, status: number, data: any}>}
 *          ok: リクエストが成功したか（2xx系か）、status: HTTPステータスコード、data: レスポンスのJSON
 */
async function apiRequest(path, method, body = null) {
    const options = {
        method: method,
        headers: {
            "Content-Type": "application/json",
        },
        // credentials: "same-origin" を指定することで、セッションCookieが
        // リクエストに含まれるようにする（ログイン状態を維持するために必須）。
        credentials: "same-origin",
    };

    if (body !== null) {
        options.body = JSON.stringify(body);
    }

    const response = await fetch(path, options);

    // レスポンスボディが無い場合（204 No Contentなど）はJSONパースをスキップする。
    let data = null;
    const text = await response.text();
    if (text) {
        data = JSON.parse(text);
    }

    return { ok: response.ok, status: response.status, data: data };
}

// 各APIエンドポイントに対応する、呼び出しやすい形の関数をまとめて用意する。
const api = {
    register: (username, password) =>
        apiRequest("/api/auth/register", "POST", { username, password }),

    login: (username, password) =>
        apiRequest("/api/auth/login", "POST", { username, password }),

    logout: () => apiRequest("/api/auth/logout", "POST"),

    me: () => apiRequest("/api/auth/me", "GET"),

    deleteAccount: (password) => apiRequest("/api/auth/me", "DELETE", { password }),

    updateSortPreference: (sortPreference) =>
        apiRequest("/api/auth/me/sort-preference", "PATCH", { sort_preference: sortPreference }),

    listTasks: () => apiRequest("/api/tasks", "GET"),

    reorderTasks: (taskIds) => apiRequest("/api/tasks/reorder", "PATCH", { task_ids: taskIds }),

    createTask: (title, description, dueDate) =>
        apiRequest("/api/tasks", "POST", {
            title: title,
            description: description || null,
            due_date: dueDate || null,
        }),

    updateTask: (taskId, fields) => apiRequest(`/api/tasks/${taskId}`, "PATCH", fields),

    deleteTask: (taskId) => apiRequest(`/api/tasks/${taskId}`, "DELETE"),
};
