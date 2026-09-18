"""
Todoリストアプリの本体(Flaskアプリ)。

Flaskとは:
    Pythonで簡単にWebアプリを作れるライブラリ(フレームワーク)です。
    「このURLにアクセスされたら、この処理をする」というのを
    関数ごとに書いていきます。

このアプリのページ構成:
    GET  /            … 登録済みのやること一覧を表示するページ
    GET  /new         … 新規登録用のフォームを表示するページ
    POST /new         … フォームの内容をスプレッドシートに登録する処理
    GET  /edit/<id>   … 編集用のフォームを表示するページ
    POST /edit/<id>   … フォームの内容でスプレッドシートを更新する処理
"""

import os

from dotenv import load_dotenv
from flask import Flask, redirect, render_template, request, url_for

# .env ファイルに書いた環境変数(SPREADSHEET_IDなど)を読み込む
load_dotenv()

import sheets

app = Flask(__name__)


@app.route("/")
def index():
    """やること一覧ページ(期日が近い順に並び替えて表示する)"""
    todos = sheets.get_all_todos()
    todos = sorted(todos, key=lambda todo: todo.get("due_date") or "")
    return render_template("index.html", todos=todos)


@app.route("/new", methods=["GET", "POST"])
def new_todo():
    """新規登録ページ"""
    if request.method == "POST":
        title = request.form["title"]
        content = request.form["content"]
        due_date = request.form["due_date"]
        sheets.add_todo(title, content, due_date)
        return redirect(url_for("index"))

    # GETの場合は、空のフォームを表示する
    return render_template("form.html", todo=None, action_url=url_for("new_todo"))


@app.route("/edit/<todo_id>", methods=["GET", "POST"])
def edit_todo(todo_id):
    """編集ページ"""
    if request.method == "POST":
        title = request.form["title"]
        content = request.form["content"]
        due_date = request.form["due_date"]
        sheets.update_todo(todo_id, title, content, due_date)
        return redirect(url_for("index"))

    # GETの場合は、既存の内容が入ったフォームを表示する
    todo = sheets.get_todo(todo_id)
    if todo is None:
        return "指定されたやることが見つかりませんでした。", 404
    return render_template(
        "form.html", todo=todo, action_url=url_for("edit_todo", todo_id=todo_id)
    )


@app.route("/delete/<todo_id>", methods=["POST"])
def delete_todo(todo_id):
    """やることを削除する処理(一覧ページの「削除」ボタンから呼ばれる)"""
    sheets.delete_todo(todo_id)
    return redirect(url_for("index"))


@app.route("/toggle/<todo_id>", methods=["POST"])
def toggle_todo(todo_id):
    """完了/未完了を切り替える処理(一覧ページのチェックボックスから呼ばれる)"""
    sheets.toggle_done(todo_id)
    return redirect(url_for("index"))


if __name__ == "__main__":
    # ローカルで動作確認するときは `python app.py` で起動できます。
    # デバッグモード(コード変更時に自動で再起動する機能)は開発時のみ有効にします。
    port = int(os.environ.get("PORT", 5000))
    debug = os.environ.get("FLASK_DEBUG", "1") == "1"
    app.run(host="0.0.0.0", port=port, debug=debug)
