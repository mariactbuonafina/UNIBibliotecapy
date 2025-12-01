from flask import Flask, render_template, request, redirect, url_for, flash
import sqlite3
import os

DB_PATH = os.environ.get("BIB_DB", "biblioteca.db")

app = Flask(__name__)
app.secret_key = "dev-secret"  # for flash messages - replace in production

def get_db_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        titulo = request.form.get("titulo", "").strip()
        autor = request.form.get("autor", "").strip()
        ano = request.form.get("ano_publicacao", "").strip()
        disponivel = 1 if request.form.get("disponivel") == "on" else 0

        if not titulo or not autor or not ano:
            flash("Preencha título, autor e ano de publicação.", "danger")
            return redirect(url_for("index"))

        try:
            ano_int = int(ano)
        except ValueError:
            flash("Ano de publicação inválido.", "danger")
            return redirect(url_for("index"))

        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute(
            "INSERT INTO livros (titulo, autor, ano_publicacao, disponivel) VALUES (?, ?, ?, ?)",
            (titulo, autor, ano_int, disponivel)
        )
        conn.commit()
        conn.close()
        flash("Livro adicionado com sucesso.", "success")
        return redirect(url_for("index"))

    conn = get_db_connection()
    livros = conn.execute("SELECT * FROM livros ORDER BY id DESC").fetchall()
    conn.close()
    return render_template("index.html", livros=livros)

@app.route("/delete/<int:book_id>", methods=["POST"])
def delete(book_id):
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("DELETE FROM livros WHERE id = ?", (book_id,))
    conn.commit()
    conn.close()
    flash("Livro removido.", "info")
    return redirect(url_for("index"))

@app.route("/edit/<int:book_id>", methods=["GET", "POST"])
def edit(book_id):
    conn = get_db_connection()
    cur = conn.cursor()
    if request.method == "POST":
        titulo = request.form.get("titulo", "").strip()
        autor = request.form.get("autor", "").strip()
        ano = request.form.get("ano_publicacao", "").strip()
        disponivel = 1 if request.form.get("disponivel") == "on" else 0

        try:
            ano_int = int(ano)
        except ValueError:
            flash("Ano inválido.", "danger")
            return redirect(url_for("edit", book_id=book_id))

        cur.execute("""
            UPDATE livros SET titulo = ?, autor = ?, ano_publicacao = ?, disponivel = ? WHERE id = ?
        """, (titulo, autor, ano_int, disponivel, book_id))
        conn.commit()
        conn.close()
        flash("Livro atualizado.", "success")
        return redirect(url_for("index"))

    book = conn.execute("SELECT * FROM livros WHERE id = ?", (book_id,)).fetchone()
    conn.close()
    if book is None:
        flash("Livro não encontrado.", "warning")
        return redirect(url_for("index"))
    return render_template("edit.html", book=book)

if __name__ == "__main__":
    # Run on port 5000 as requested
    app.run(host="0.0.0.0", port=5000, debug=True)