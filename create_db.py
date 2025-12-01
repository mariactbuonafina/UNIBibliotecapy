import sqlite3
conn = sqlite3.connect("biblioteca.db")
cur = conn.cursor()
cur.execute("""
CREATE TABLE IF NOT EXISTS livros (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    titulo TEXT NOT NULL,
    autor TEXT NOT NULL,
    ano_publicacao INTEGER NOT NULL,
    disponivel INTEGER NOT NULL DEFAULT 1
)
""")
# Insert sample data
cur.execute("INSERT INTO livros (titulo, autor, ano_publicacao, disponivel) VALUES (?, ?, ?, ?)", 
            ("Algoritmos 101", "Maria Silva", 2010, 1))
cur.execute("INSERT INTO livros (titulo, autor, ano_publicacao, disponivel) VALUES (?, ?, ?, ?)", 
            ("Banco de Dados", "João Souza", 2018, 0))
conn.commit()
conn.close()
print('biblioteca.db criado/atualizado com amostras.')