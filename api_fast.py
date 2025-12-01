from fastapi import FastAPI, HTTPException, status, Depends, Header, Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field, constr, validator
import sqlite3
import os
import math
import logging

# config / logging
DB_PATH = os.environ.get("BIB_DB", "biblioteca.db")
API_KEY = os.environ.get("API_KEY")  # if set, write endpoints require this header x-api-key

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger("biblioteca_api")

app = FastAPI(title="API Biblioteca (av2)", version="1.1")

# Allow CORS for local dev (adjust origins in production)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)

# DB helper
def get_db_connection():
    conn = sqlite3.connect(DB_PATH, timeout=10)
    conn.row_factory = sqlite3.Row
    return conn

# Auth dependency (optional)
def require_api_key(x_api_key: str = Header(None)):
    if API_KEY is None:
        #sem chave api necessária se a var de ambiente não estiver definida
        return
    if x_api_key != API_KEY:
        logger.warning("Unauthorized attempt with x-api-key=%s", x_api_key)
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid or missing API key")

# modelo pydantic
class BookBase(BaseModel):
    titulo: constr(strip_whitespace=True, min_length=1)
    autor: constr(strip_whitespace=True, min_length=1)
    ano_publicacao: int = Field(..., ge=0, le=9999)
    disponivel: bool = True

    @validator("titulo", "autor")
    def not_empty(cls, v):
        if not v or not v.strip():
            raise ValueError("Campo obrigatório")
        return v.strip()

class BookCreate(BookBase):
    pass

class BookUpdate(BaseModel):
    titulo: constr(strip_whitespace=True, min_length=1) | None = None
    autor: constr(strip_whitespace=True, min_length=1) | None = None
    ano_publicacao: int | None = Field(None, ge=0, le=9999)
    disponivel: bool | None = None

class BookOut(BookBase):
    id: int

class Meta(BaseModel):
    total: int
    page: int
    per_page: int
    total_pages: int

class ListResponse(BaseModel):
    items: list[BookOut]
    meta: Meta

class StatsOut(BaseModel):
    total: int
    disponiveis: int
    indisponiveis: int
    ano_min: int | None
    ano_max: int | None

# exception handlers
@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    logger.info("HTTPException %s %s -> %s", request.method, request.url, exc.detail)
    return JSONResponse(status_code=exc.status_code, content={"detail": exc.detail})

@app.on_event("startup")
def startup_event():
    logger.info("Starting Biblioteca API (DB=%s). API_KEY set=%s", DB_PATH, bool(API_KEY))

# funções uteis
def row_to_book(r):
    return BookOut(
        id=r["id"],
        titulo=r["titulo"],
        autor=r["autor"],
        ano_publicacao=r["ano_publicacao"],
        disponivel=bool(r["disponivel"])
    )

# endpoints
@app.get("/livros", response_model=ListResponse)
def list_books(q: str | None = None, page: int = 1, per_page: int = 10,
               sort_by: str = "id", sort_dir: str = "desc"):
    """
    Lista livros com paginação, busca por título/autor, e ordenação.
    Ex: /livros?q=algoritmos&page=1&per_page=5&sort_by=ano_publicacao&sort_dir=asc
    """
    # sanitize params
    page = max(1, page)
    per_page = min(max(1, per_page), 100)
    allowed_sort = {"id", "titulo", "autor", "ano_publicacao", "disponivel"}
    if sort_by not in allowed_sort:
        sort_by = "id"
    sort_dir = "asc" if sort_dir.lower() == "asc" else "desc"

    conn = get_db_connection()
    cur = conn.cursor()

    params = []
    where = ""
    if q:
        term = f"%{q}%"
        where = "WHERE titulo LIKE ? OR autor LIKE ?"
        params.extend([term, term])

    # total count
    count_sql = f"SELECT COUNT(*) as cnt FROM livros {where}"
    total = cur.execute(count_sql, params).fetchone()["cnt"]

    offset = (page - 1) * per_page
    sql = f"SELECT * FROM livros {where} ORDER BY {sort_by} {sort_dir} LIMIT ? OFFSET ?"
    params.extend([per_page, offset])
    rows = cur.execute(sql, params).fetchall()
    conn.close()

    items = [row_to_book(r) for r in rows]
    total_pages = math.ceil(total / per_page) if per_page else 1
    meta = Meta(total=total, page=page, per_page=per_page, total_pages=total_pages)
    return ListResponse(items=items, meta=meta)

@app.get("/livros/{book_id}", response_model=BookOut)
def get_book(book_id: int):
    conn = get_db_connection()
    row = conn.execute("SELECT * FROM livros WHERE id = ?", (book_id,)).fetchone()
    conn.close()
    if row is None:
        raise HTTPException(status_code=404, detail="Livro não encontrado")
    return row_to_book(row)

@app.post("/livros", response_model=BookOut, status_code=status.HTTP_201_CREATED, dependencies=[Depends(require_api_key)])
def create_book(book: BookCreate):
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute(
        "INSERT INTO livros (titulo, autor, ano_publicacao, disponivel) VALUES (?, ?, ?, ?)",
        (book.titulo, book.autor, book.ano_publicacao, int(book.disponivel))
    )
    conn.commit()
    new_id = cur.lastrowid
    conn.close()
    logger.info("Livro criado id=%s titulo=%s", new_id, book.titulo)
    return BookOut(id=new_id, **book.dict())

@app.put("/livros/{book_id}", response_model=BookOut, dependencies=[Depends(require_api_key)])
def update_book(book_id: int, book: BookUpdate):
    conn = get_db_connection()
    cur = conn.cursor()
    existing = cur.execute("SELECT * FROM livros WHERE id = ?", (book_id,)).fetchone()
    if existing is None:
        conn.close()
        raise HTTPException(status_code=404, detail="Livro não encontrado")
    titulo = book.titulo if book.titulo is not None else existing["titulo"]
    autor = book.autor if book.autor is not None else existing["autor"]
    ano = book.ano_publicacao if book.ano_publicacao is not None else existing["ano_publicacao"]
    disponivel = int(book.disponivel) if book.disponivel is not None else existing["disponivel"]
    cur.execute(
        "UPDATE livros SET titulo = ?, autor = ?, ano_publicacao = ?, disponivel = ? WHERE id = ?",
        (titulo, autor, ano, disponivel, book_id)
    )
    conn.commit()
    conn.close()
    logger.info("Livro atualizado id=%s", book_id)
    return BookOut(id=book_id, titulo=titulo, autor=autor, ano_publicacao=ano, disponivel=bool(disponivel))

@app.delete("/livros/{book_id}", dependencies=[Depends(require_api_key)])
def delete_book(book_id: int):
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT 1 FROM livros WHERE id = ?", (book_id,))
    if cur.fetchone() is None:
        conn.close()
        raise HTTPException(status_code=404, detail="Livro não encontrado")
    cur.execute("DELETE FROM livros WHERE id = ?", (book_id,))
    conn.commit()
    conn.close()
    logger.info("Livro removido id=%s", book_id)
    return {"detail": "Livro removido"}

@app.get("/stats", response_model=StatsOut)
def stats():
    conn = get_db_connection()
    cur = conn.cursor()
    r_total = cur.execute("SELECT COUNT(*) as cnt FROM livros").fetchone()["cnt"]
    r_disp = cur.execute("SELECT COUNT(*) as cnt FROM livros WHERE disponivel = 1").fetchone()["cnt"]
    r_ind = r_total - r_disp
    r_min = cur.execute("SELECT MIN(ano_publicacao) as v FROM livros").fetchone()["v"]
    r_max = cur.execute("SELECT MAX(ano_publicacao) as v FROM livros").fetchone()["v"]
    conn.close()
    return StatsOut(total=r_total, disponiveis=r_disp, indisponiveis=r_ind, ano_min=r_min, ano_max=r_max)