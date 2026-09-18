"""
Googleスプレッドシートを「データベース代わり」に使うためのモジュール。

- gspread というライブラリを使って、Pythonからスプレッドシートを
  読み書きします。
- スプレッドシートの1行目（ヘッダー行）は id / title / content / due_date
  という列名にしておく前提です。
"""

import os
import uuid

import gspread
from google.oauth2.service_account import Credentials

# スプレッドシートを読み書きするために必要な権限（スコープ）
SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
]

# 環境変数から設定を読み込む
#   GOOGLE_CREDENTIALS_FILE : サービスアカウントの認証情報(JSON)ファイルのパス
#   SPREADSHEET_ID          : 対象のスプレッドシートのID
CREDENTIALS_FILE = os.environ.get("GOOGLE_CREDENTIALS_FILE", "credentials.json")
SPREADSHEET_ID = os.environ.get("SPREADSHEET_ID")

HEADERS = ["id", "title", "content", "due_date", "done"]

# 目標(今月の目標・来年の目標)を保存するシートのヘッダー
# category列には "month"(今月の目標) か "year"(来年の目標) が入る
GOAL_HEADERS = ["id", "category", "title", "why", "how"]


def _get_spreadsheet():
    """認証を行い、スプレッドシート全体(ブック)を取得する"""
    if not SPREADSHEET_ID:
        raise RuntimeError(
            "環境変数 SPREADSHEET_ID が設定されていません。"
            ".env ファイルを確認してください。"
        )

    credentials = Credentials.from_service_account_file(
        CREDENTIALS_FILE, scopes=SCOPES
    )
    client = gspread.authorize(credentials)
    return client.open_by_key(SPREADSHEET_ID)


def _get_worksheet():
    """やること一覧を保存している、1枚目のシート(worksheet)を取得する"""
    worksheet = _get_spreadsheet().sheet1

    # ヘッダー行が無い(真っ白な)スプレッドシートの場合は、自動で作る
    if worksheet.row_values(1) != HEADERS:
        worksheet.update("A1", [HEADERS])

    return worksheet


def _get_goals_worksheet():
    """目標を保存している「goals」シートを取得する(無ければ自動で作成する)"""
    spreadsheet = _get_spreadsheet()
    try:
        worksheet = spreadsheet.worksheet("goals")
    except gspread.exceptions.WorksheetNotFound:
        worksheet = spreadsheet.add_worksheet(
            title="goals", rows=200, cols=len(GOAL_HEADERS)
        )

    if worksheet.row_values(1) != GOAL_HEADERS:
        worksheet.update("A1", [GOAL_HEADERS])

    return worksheet


def get_all_todos():
    """登録されているやること一覧を、すべて取得する"""
    worksheet = _get_worksheet()
    records = worksheet.get_all_records()  # ヘッダー行を元に辞書のリストで取得
    return records


def get_todo(todo_id):
    """idを指定して、1件だけやることを取得する（見つからなければNone）"""
    for todo in get_all_todos():
        if str(todo["id"]) == str(todo_id):
            return todo
    return None


def add_todo(title, content, due_date):
    """新しいやることを1件、スプレッドシートに追加する(登録直後は「未完了」)"""
    worksheet = _get_worksheet()
    new_id = str(uuid.uuid4())  # 他と絶対に被らないID(UUID)を発行する
    worksheet.append_row([new_id, title, content, due_date, "FALSE"])
    return new_id


def update_todo(todo_id, title, content, due_date):
    """idを指定して、既存のやることの内容を書き換える"""
    worksheet = _get_worksheet()
    cell = worksheet.find(str(todo_id), in_column=1)
    if cell is None:
        raise ValueError(f"id={todo_id} のデータが見つかりません。")

    row = cell.row
    worksheet.update(f"A{row}:D{row}", [[todo_id, title, content, due_date]])


def delete_todo(todo_id):
    """idを指定して、やることを1件削除する"""
    worksheet = _get_worksheet()
    cell = worksheet.find(str(todo_id), in_column=1)
    if cell is None:
        raise ValueError(f"id={todo_id} のデータが見つかりません。")
    worksheet.delete_rows(cell.row)


def toggle_done(todo_id):
    """idを指定して、完了/未完了の状態を反転させる(チェックリストのチェック操作)"""
    worksheet = _get_worksheet()
    cell = worksheet.find(str(todo_id), in_column=1)
    if cell is None:
        raise ValueError(f"id={todo_id} のデータが見つかりません。")

    done_column = HEADERS.index("done") + 1  # gspreadの列番号は1始まり
    current = worksheet.cell(cell.row, done_column).value
    new_value = "FALSE" if current == "TRUE" else "TRUE"
    worksheet.update_cell(cell.row, done_column, new_value)


def get_goals(category):
    """指定したcategory("month"または"year")の目標一覧を取得する"""
    worksheet = _get_goals_worksheet()
    records = worksheet.get_all_records()
    return [goal for goal in records if goal["category"] == category]


def add_goal(category, title, why, how):
    """新しい目標を1件、goalsシートに追加する"""
    worksheet = _get_goals_worksheet()
    new_id = str(uuid.uuid4())
    worksheet.append_row([new_id, category, title, why, how])
    return new_id


def delete_goal(goal_id):
    """idを指定して、目標を1件削除する"""
    worksheet = _get_goals_worksheet()
    cell = worksheet.find(str(goal_id), in_column=1)
    if cell is None:
        raise ValueError(f"id={goal_id} の目標が見つかりません。")
    worksheet.delete_rows(cell.row)
