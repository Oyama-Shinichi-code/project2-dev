# タスク管理（作成・一覧・更新・削除）のAPIエンドポイントを定義するルーター。
# すべてのエンドポイントで get_current_user を使い、ログイン済みユーザーのみが
# 自分自身のタスクにアクセスできるようにしている。
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.auth.dependencies import get_current_user
from app.auth.models import User
from app.database import get_db
from app.tasks.models import Task
from app.tasks.schemas import TaskCreate, TaskOut, TaskReorderRequest, TaskUpdate

# "/api" プレフィックスにより、画面用の /tasks（app/views.py）と衝突しないようにしている。
router = APIRouter(prefix="/api/tasks", tags=["tasks"])


def _get_owned_task_or_404(task_id: int, current_user: User, db: Session) -> Task:
    """
    指定したIDのタスクを取得し、かつそれがログイン中ユーザー自身のものであることを確認する。
    他人のタスクへのアクセスを防ぐための共通チェック処理（更新・削除で共用する）。
    見つからない・他人のタスクの場合は、存在を教えないために同じ404を返す。
    """
    task = db.get(Task, task_id)
    if task is None or task.user_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Task not found")
    return task


@router.post("", response_model=TaskOut, status_code=status.HTTP_201_CREATED)
def create_task(
    task_in: TaskCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """新しいタスクを作成する。作成者は常にログイン中のユーザー自身になる。"""
    # 手動並び替え（sort_order）では、新規タスクは常に一覧の最後尾に追加されるようにする。
    # 既存タスクの最大値+1を割り当てることで、過去のタスクより後ろに来るようにする。
    max_sort_order = (
        db.query(Task.sort_order)
        .filter(Task.user_id == current_user.id)
        .order_by(Task.sort_order.desc())
        .first()
    )
    next_sort_order = (max_sort_order[0] + 1) if max_sort_order else 0

    new_task = Task(
        user_id=current_user.id,
        title=task_in.title,
        description=task_in.description,
        due_date=task_in.due_date,
        sort_order=next_sort_order,
    )
    db.add(new_task)
    db.commit()
    db.refresh(new_task)
    return new_task


@router.get("", response_model=list[TaskOut])
def list_tasks(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    ログイン中ユーザー自身のタスクのみを一覧取得する（他ユーザーのタスクは絶対に含めない）。
    並び順はユーザーの sort_preference 設定（日付順・タスク名順・手動順）に従う。
    """
    query = db.query(Task).filter(Task.user_id == current_user.id)

    if current_user.sort_preference == "title":
        # タスク名の昇順（あいうえお順・アルファベット順）。
        query = query.order_by(Task.title.asc())
    elif current_user.sort_preference == "manual":
        # ユーザーがドラッグ&ドロップで並び替えた順（sort_orderの昇順）。
        query = query.order_by(Task.sort_order.asc())
    else:
        # デフォルト（"due_date"）: 期限日の昇順。
        # 期限未設定（NULL）のタスクは常に最後に表示したいが、SQLiteのデフォルトでは
        # NULLは昇順で最初に来てしまうため、「期限未設定かどうか」を先にソートキーにして回避する。
        query = query.order_by(Task.due_date.is_(None).asc(), Task.due_date.asc())

    tasks = query.all()
    return tasks


@router.patch("/reorder", response_model=list[TaskOut])
def reorder_tasks(
    body: TaskReorderRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    ドラッグ&ドロップで並び替えた結果（新しい順序のタスクID配列）を受け取り、
    各タスクの sort_order を更新する。手動並び替え（"manual"）の記憶に使う。
    他ユーザーのタスクIDが混ざっていないかも確認し、不正な場合は404を返す。
    """
    tasks_by_id = {
        task.id: task
        for task in db.query(Task).filter(Task.user_id == current_user.id).all()
    }

    # リクエストに含まれる全IDが、本当にログイン中ユーザー自身のタスクかを確認する。
    if set(body.task_ids) != set(tasks_by_id.keys()):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Task not found")

    for index, task_id in enumerate(body.task_ids):
        tasks_by_id[task_id].sort_order = index

    db.commit()

    return (
        db.query(Task)
        .filter(Task.user_id == current_user.id)
        .order_by(Task.sort_order.asc())
        .all()
    )


@router.patch("/{task_id}", response_model=TaskOut)
def update_task(
    task_id: int,
    task_in: TaskUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    タスクを部分更新する（完了/未完了の切り替えもこのエンドポイントで行う）。
    リクエストで指定されたフィールドのみを更新し、指定されなかったフィールドは変更しない。
    """
    task = _get_owned_task_or_404(task_id, current_user, db)

    # model_dump(exclude_unset=True) で「リクエストに実際に含まれていたフィールド」だけを取り出す。
    # これにより、「is_doneだけ送った場合にtitleがNoneで上書きされてしまう」事故を防ぐ。
    update_data = task_in.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(task, field, value)

    db.commit()
    db.refresh(task)
    return task


@router.delete("/{task_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_task(
    task_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """タスクを削除する。"""
    task = _get_owned_task_or_404(task_id, current_user, db)
    db.delete(task)
    db.commit()
    return None
