from fastapi import FastAPI, HTTPException, status
from pydantic import BaseModel, Field, constr
import sqlite3
import os

DB_PATH = os.environ.get("BIB_DB", "biblioteca.db")

app = FastAPI(title="API Biblioteca", version="1.0")

def get_db_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

class BookBase(BaseModel):
    titulo: constr(strip_whitespace=True, min_length=1)
    autor: constr(strip_whitespace=True, min_length=1)
    ano_publicacao: int = Field(..., ge=0, le=9999)
    disponivel: bool = True

class BookCreate(BookBase):
    pass

class BookUpdate(BaseModel):
    titulo: constr(strip_whitespace=True, min_length=1) | None = None
    autor: constr(strip_whitespace=True, min_length=1) | None = None
    ano_publicacao: int | None = None
    disponivel: bool | None = None

class BookOut(BookBase):
    id: int

@app.get("/livros", response_model=list[BookOut])
def list_books():
    conn = get_db_connection()
    rows = conn.execute("SELECT * FROM livros").fetchall()
    conn.close()
    return [BookOut(id=r["id"], titulo=r["titulo"], autor=r["autor"], ano_publicacao=r["ano_publicacao"], disponivel=bool(r["disponivel"])) for r in rows]

@app.get("/livros/{book_id}", response_model=BookOut)
def get_book(book_id: int):
    conn = get_db_connection()
    row = conn.execute("SELECT * FROM livros WHERE id = ?", (book_id,)).fetchone()
    conn.close()
    if row is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Livro não encontrado")
    return BookOut(id=row["id"], titulo=row["titulo"], autor=row["autor"], ano_publicacao=row["ano_publicacao"], disponivel=bool(row["disponivel"]))

@app.post("/livros", response_model=BookOut, status_code=status.HTTP_201_CREATED)
def create_book(book: BookCreate):
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("INSERT INTO livros (titulo, autor, ano_publicacao, disponivel) VALUES (?, ?, ?, ?)",
                (book.titulo, book.autor, book.ano_publicacao, int(book.disponivel)))
    conn.commit()
    new_id = cur.lastrowid
    conn.close()
    return BookOut(id=new_id, **book.dict())

@app.put("/livros/{book_id}", response_model=BookOut)
def update_book(book_id: int, book: BookUpdate):
    conn = get_db_connection()
    cur = conn.cursor()
    existing = cur.execute("SELECT * FROM livros WHERE id = ?", (book_id,)).fetchone()
    if existing is None:
        conn.close()
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Livro não encontrado")
    # Prepare updated values
    titulo = book.titulo if book.titulo is not None else existing["titulo"]
    autor = book.autor if book.autor is not None else existing["autor"]
    ano = book.ano_publicacao if book.ano_publicacao is not None else existing["ano_publicacao"]
    disponivel = int(book.disponivel) if book.disponivel is not None else existing["disponivel"]
    cur.execute("""UPDATE livros SET titulo = ?, autor = ?, ano_publicacao = ?, disponivel = ? WHERE id = ?""",
                (titulo, autor, ano, disponivel, book_id))
    conn.commit()
    conn.close()
    return BookOut(id=book_id, titulo=titulo, autor=autor, ano_publicacao=ano, disponivel=bool(disponivel))

@app.delete("/livros/{book_id}", status_code=status.HTTP_200_OK)
def delete_book(book_id: int):
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT * FROM livros WHERE id = ?", (book_id,))
    if cur.fetchone() is None:
        conn.close()
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Livro não encontrado")
    cur.execute("DELETE FROM livros WHERE id = ?", (book_id,))
    conn.commit()
    conn.close()
    return {"detail": "Livro removido"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("api_fast:app", host="0.0.0.0", port=8000, reload=True)