// タスク一覧画面（tasks.html）専用のロジック。

const currentUsernameEl = document.getElementById("current-username");
const errorMessageEl = document.getElementById("error-message");
const logoutButton = document.getElementById("logout-button");
const taskCreateForm = document.getElementById("task-create-form");
const taskListEl = document.getElementById("task-list");
const taskItemTemplate = document.getElementById("task-item-template");

function showError(message) {
    errorMessageEl.textContent = message;
    errorMessageEl.hidden = false;
}

/**
 * タスク1件分のデータから、画面に表示するli要素を組み立てる。
 * HTML側の <template id="task-item-template"> をコピーして中身を埋める方式にしている。
 */
function buildTaskElement(task) {
    // templateの中身（content）をディープコピーして、元のtemplateを汚さないようにする。
    const fragment = taskItemTemplate.content.cloneNode(true);
    const li = fragment.querySelector(".task-item");

    // data-task-id属性に紐づけておくことで、後から「どのタスクの行か」を特定できるようにする。
    li.dataset.taskId = task.id;
    if (task.is_done) {
        li.classList.add("is-done");
    }

    const checkbox = li.querySelector(".task-done-checkbox");
    checkbox.checked = task.is_done;

    // 表示モード側の要素（通常時に見えている部分）。
    const viewEl = li.querySelector(".task-view");
    const titleEl = li.querySelector(".task-title");
    const descriptionEl = li.querySelector(".task-description");
    const dueDateEl = li.querySelector(".task-due-date");

    // 編集モード側の要素（編集ボタンを押したときだけ見える部分）。
    const editForm = li.querySelector(".task-edit-form");
    const editTitleInput = li.querySelector(".task-edit-title");
    const editDescriptionInput = li.querySelector(".task-edit-description");
    const editDueDateInput = li.querySelector(".task-edit-due-date");
    const editButton = li.querySelector(".task-edit-button");
    const cancelButton = li.querySelector(".task-edit-cancel-button");

    /**
     * 画面表示用の文字列を、現在のtaskオブジェクトの内容で更新する。
     * 作成時・編集保存時の両方から呼び出す共通処理。
     */
    function renderView(currentTask) {
        titleEl.textContent = currentTask.title;
        descriptionEl.textContent = currentTask.description || "";
        dueDateEl.textContent = currentTask.due_date ? `期限: ${currentTask.due_date}` : "";
    }

    renderView(task);

    // 完了/未完了チェックボックスが変更されたら、APIに更新を送る。
    checkbox.addEventListener("change", async () => {
        const result = await api.updateTask(task.id, { is_done: checkbox.checked });
        if (result.ok) {
            li.classList.toggle("is-done", checkbox.checked);
        } else {
            // 失敗した場合はチェック状態を元に戻し、ユーザーに分かるようにする。
            checkbox.checked = !checkbox.checked;
            showError("タスクの更新に失敗しました");
        }
    });

    // 削除ボタンが押されたら、APIで削除してから画面上の要素も取り除く。
    const deleteButton = li.querySelector(".task-delete-button");
    deleteButton.addEventListener("click", async () => {
        const result = await api.deleteTask(task.id);
        if (result.ok) {
            li.remove();
        } else {
            showError("タスクの削除に失敗しました");
        }
    });

    // 編集ボタンが押されたら、表示モードを隠して編集モード（フォーム）を表示する。
    // その際、現在の値をフォームの入力欄に流し込んでおく（何もしていない状態からの編集を防ぐ）。
    editButton.addEventListener("click", () => {
        editTitleInput.value = task.title;
        editDescriptionInput.value = task.description || "";
        editDueDateInput.value = task.due_date || "";

        viewEl.hidden = true;
        editForm.hidden = false;
    });

    // キャンセルボタンが押されたら、入力内容を保存せずに表示モードへ戻す。
    cancelButton.addEventListener("click", () => {
        editForm.hidden = true;
        viewEl.hidden = false;
    });

    // 編集フォームの送信（保存ボタン）処理。
    editForm.addEventListener("submit", async (event) => {
        event.preventDefault();

        const result = await api.updateTask(task.id, {
            title: editTitleInput.value,
            description: editDescriptionInput.value || null,
            due_date: editDueDateInput.value || null,
        });

        if (result.ok) {
            // サーバーから返ってきた最新の内容でtaskオブジェクト自体も更新しておく
            // （再度編集ボタンを押したときに古い値が出ないようにするため）。
            task.title = result.data.title;
            task.description = result.data.description;
            task.due_date = result.data.due_date;

            renderView(task);
            editForm.hidden = true;
            viewEl.hidden = false;
        } else {
            showError("タスクの編集に失敗しました");
        }
    });

    return li;
}

/**
 * サーバーから最新のタスク一覧を取得し、画面に描画し直す。
 */
async function loadTasks() {
    const result = await api.listTasks();

    if (!result.ok) {
        showError("タスク一覧の取得に失敗しました");
        return;
    }

    // 一覧を描画し直す前に、既存の表示内容をすべて空にする。
    taskListEl.innerHTML = "";

    for (const task of result.data) {
        taskListEl.appendChild(buildTaskElement(task));
    }
}

/**
 * ログイン状態を確認し、ユーザー名を画面に表示する。
 * 未ログインの場合はログイン画面にリダイレクトする
 * （このページは本来ログイン必須だが、直接URLを叩かれた場合の保険として行う）。
 */
async function loadCurrentUser() {
    const result = await api.me();

    if (!result.ok) {
        window.location.href = "/login";
        return;
    }

    currentUsernameEl.textContent = result.data.username;
}

// タスク新規作成フォームの送信処理。
taskCreateForm.addEventListener("submit", async (event) => {
    event.preventDefault();

    const titleInput = document.getElementById("task-title");
    const descriptionInput = document.getElementById("task-description");
    const dueDateInput = document.getElementById("task-due-date");

    const result = await api.createTask(
        titleInput.value,
        descriptionInput.value,
        dueDateInput.value
    );

    if (result.ok) {
        // 作成に成功したらフォームを空にして、一覧を再読み込みする。
        taskCreateForm.reset();
        await loadTasks();
    } else {
        showError("タスクの作成に失敗しました");
    }
});

// ログアウトボタンの処理。
logoutButton.addEventListener("click", async () => {
    await api.logout();
    window.location.href = "/login";
});

// ページが読み込まれたタイミングで、ユーザー情報とタスク一覧を取得する。
loadCurrentUser();
loadTasks();
