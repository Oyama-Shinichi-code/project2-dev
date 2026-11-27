# タスク管理（作成・一覧・更新・削除）のAPIエンドポイントを定義するルーター。
# すべてのエンドポイントで get_current_user を使い、ログイン済みユーザーのみが
# 自分自身のタスクにアクセスできるようにしている。
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.auth.dependencies import get_current_user
from app.auth.models import User
from app.database import get_db
from app.tasks.models import Task
from app.tasks.schemas import TaskCreate, TaskOut, TaskUpdate

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
    new_task = Task(
        user_id=current_user.id,
        title=task_in.title,
        description=task_in.description,
        due_date=task_in.due_date,
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
    """ログイン中ユーザー自身のタスクのみを一覧取得する（他ユーザーのタスクは絶対に含めない）。"""
    tasks = (
        db.query(Task)
        .filter(Task.user_id == current_user.id)
        .order_by(Task.created_at.desc())
        .all()
    )
    return tasks


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
