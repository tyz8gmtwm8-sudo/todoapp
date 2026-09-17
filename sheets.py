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

HEADERS = ["id", "title", "content", "due_date"]


def _get_worksheet():
    """認証を行い、スプレッドシートの1枚目のシート(worksheet)を取得する"""
    if not SPREADSHEET_ID:
        raise RuntimeError(
            "環境変数 SPREADSHEET_ID が設定されていません。"
            ".env ファイルを確認してください。"
        )

    credentials = Credentials.from_service_account_file(
        CREDENTIALS_FILE, scopes=SCOPES
    )
    client = gspread.authorize(credentials)
    spreadsheet = client.open_by_key(SPREADSHEET_ID)
    worksheet = spreadsheet.sheet1

    # ヘッダー行が無い(真っ白な)スプレッドシートの場合は、自動で作る
    if worksheet.row_values(1) != HEADERS:
        worksheet.update("A1", [HEADERS])

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
    """新しいやることを1件、スプレッドシートに追加する"""
    worksheet = _get_worksheet()
    new_id = str(uuid.uuid4())  # 他と絶対に被らないID(UUID)を発行する
    worksheet.append_row([new_id, title, content, due_date])
    return new_id


def update_todo(todo_id, title, content, due_date):
    """idを指定して、既存のやることの内容を書き換える"""
    worksheet = _get_worksheet()
    cell = worksheet.find(str(todo_id), in_column=1)
    if cell is None:
        raise ValueError(f"id={todo_id} のデータが見つかりません。")

    row = cell.row
    worksheet.update(f"A{row}:D{row}", [[todo_id, title, content, due_date]])
