// タスク一覧画面（tasks.html）専用のロジック。

const currentUsernameEl = document.getElementById("current-username");
const errorMessageEl = document.getElementById("error-message");
const logoutButton = document.getElementById("logout-button");
const taskCreateForm = document.getElementById("task-create-form");
const taskListEl = document.getElementById("task-list");
const taskItemTemplate = document.getElementById("task-item-template");
const sortPreferenceSelect = document.getElementById("sort-preference-select");

// 現在のソート方法。ページ読み込み時にサーバー（ユーザー設定）から取得して反映する。
let currentSortPreference = "due_date";

// アカウント削除まわりの要素。
const deleteAccountButton = document.getElementById("delete-account-button");
const deleteAccountModal = document.getElementById("delete-account-modal");
const deleteAccountForm = document.getElementById("delete-account-form");
const deleteAccountPasswordInput = document.getElementById("delete-account-password");
const deleteAccountCancelButton = document.getElementById("delete-account-cancel-button");
const deleteAccountErrorEl = document.getElementById("delete-account-error");

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

    // ドラッグ&ドロップでの並び替え処理。
    // 手動順（"manual"）のときだけ draggable を有効にし、ドラッグハンドル部分から掴めるようにする。
    const dragHandle = li.querySelector(".task-drag-handle");

    dragHandle.addEventListener("mousedown", () => {
        li.draggable = true;
    });

    li.addEventListener("dragstart", (event) => {
        // 他のli要素にドロップされたときに「どのタスクが掴まれたか」を伝えるため、
        // タスクIDをdataTransferに積んでおく。
        event.dataTransfer.setData("text/plain", String(task.id));
        li.classList.add("is-dragging");
    });

    li.addEventListener("dragend", () => {
        li.classList.remove("is-dragging");
        li.draggable = false;
    });

    // ドロップ先候補になったときに見た目で分かるように枠線を出す。
    li.addEventListener("dragover", (event) => {
        // dragoverでpreventDefaultしないとdropイベントが発生しないブラウザの仕様に対応。
        event.preventDefault();
        li.classList.add("drag-over-top");
    });

    li.addEventListener("dragleave", () => {
        li.classList.remove("drag-over-top");
    });

    // ドロップされたら、掴まれていたタスクを移動し、新しい並び順をサーバーに保存する。
    // 「常にこの行の直前に入る」実装だと、最後の行にドロップしても最後尾に行けず
    // 必ず最後から2番目で止まってしまうため、ドロップ位置がこの行の上半分か下半分かで
    // 「直前に挿入」か「直後に挿入」かを切り替える。
    li.addEventListener("drop", async (event) => {
        event.preventDefault();
        li.classList.remove("drag-over-top");

        const draggedTaskId = event.dataTransfer.getData("text/plain");
        const draggedEl = taskListEl.querySelector(`[data-task-id="${draggedTaskId}"]`);
        if (!draggedEl || draggedEl === li) {
            return;
        }

        const rect = li.getBoundingClientRect();
        const isDroppedOnBottomHalf = event.clientY > rect.top + rect.height / 2;

        if (isDroppedOnBottomHalf) {
            // この行の直後（＝次の要素の直前。liが最後尾ならリストの最後尾）に挿入する。
            taskListEl.insertBefore(draggedEl, li.nextSibling);
        } else {
            taskListEl.insertBefore(draggedEl, li);
        }

        await saveManualOrder();
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

    // 手動順（"manual"）のときだけドラッグハンドルを表示する。
    taskListEl.classList.toggle("is-manual-sort", currentSortPreference === "manual");
}

/**
 * 現在画面に表示されている順番（data-task-id属性の並び）を、
 * 新しい手動並び順としてサーバーに保存する。
 * ドラッグ&ドロップで並び替えた直後に呼び出す。
 */
async function saveManualOrder() {
    const taskIds = [...taskListEl.querySelectorAll(".task-item")].map((li) =>
        Number(li.dataset.taskId)
    );

    const result = await api.reorderTasks(taskIds);
    if (!result.ok) {
        showError("並び替えの保存に失敗しました");
        // 保存に失敗した場合は、サーバー上の正しい順序で再描画して表示を戻す。
        await loadTasks();
    }
}

// タスク一覧の末尾（最後のタスク行より下の空白部分）にドロップされた場合に、
// 掴んでいたタスクを一覧の最後尾に移動させるための処理。
taskListEl.addEventListener("dragover", (event) => {
    event.preventDefault();
});

taskListEl.addEventListener("drop", async (event) => {
    // ドロップ先がli要素自体（個々のタスク行）の場合は、そちら側のdropハンドラに任せる。
    if (event.target.closest(".task-item")) {
        return;
    }
    event.preventDefault();

    const draggedTaskId = event.dataTransfer.getData("text/plain");
    const draggedEl = taskListEl.querySelector(`[data-task-id="${draggedTaskId}"]`);
    if (!draggedEl) {
        return;
    }

    taskListEl.appendChild(draggedEl);
    await saveManualOrder();
});

// 並び順プルダウンが変更されたら、サーバーに保存してから一覧を再読み込みする。
sortPreferenceSelect.addEventListener("change", async () => {
    currentSortPreference = sortPreferenceSelect.value;

    const result = await api.updateSortPreference(currentSortPreference);
    if (!result.ok) {
        showError("並び順の保存に失敗しました");
        return;
    }

    await loadTasks();
});

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

    // ユーザーに紐づけて保存されているソート方法を復元し、プルダウンに反映する。
    currentSortPreference = result.data.sort_preference;
    sortPreferenceSelect.value = currentSortPreference;
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

// 「アカウント削除」ボタンを押したら確認モーダルを表示する。
deleteAccountButton.addEventListener("click", () => {
    deleteAccountPasswordInput.value = "";
    deleteAccountErrorEl.hidden = true;
    deleteAccountModal.hidden = false;
});

// モーダルの「キャンセル」ボタンでモーダルを閉じる。
deleteAccountCancelButton.addEventListener("click", () => {
    deleteAccountModal.hidden = true;
});

// モーダルの確認フォーム（パスワード入力→削除する）の送信処理。
deleteAccountForm.addEventListener("submit", async (event) => {
    event.preventDefault();

    const result = await api.deleteAccount(deleteAccountPasswordInput.value);

    if (result.ok) {
        // アカウント削除が成功したら、ログイン画面に戻す。
        window.location.href = "/login";
    } else {
        // パスワードが違う場合（403）など、モーダル内にエラーを表示する
        // （画面全体のエラー欄ではなく、モーダル内の専用エラー欄を使う）。
        const detail = result.data && result.data.detail ? result.data.detail : "アカウントの削除に失敗しました";
        deleteAccountErrorEl.textContent = detail;
        deleteAccountErrorEl.hidden = false;
    }
});

// ページが読み込まれたタイミングで、ユーザー情報とタスク一覧を取得する。
// loadCurrentUser() でソート方法（currentSortPreference）を確定させた後に
// loadTasks() を呼ぶことで、ドラッグハンドル表示の初回描画がずれないようにする。
(async () => {
    await loadCurrentUser();
    await loadTasks();
})();
