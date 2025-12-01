# Sistema Biblioteca (Flask + FastAPI)

Projeto criado para a atividade AV2 - Backend Frameworks.
Contém uma aplicação Flask (interface web) e uma API FastAPI (endpoints REST), compartilhando o mesmo banco SQLite `biblioteca.db`.

## Estrutura
- `app_flask.py` - Aplicação Flask (porta 5000) que exibe lista de livros e formulário para adicionar/editar/remover.
- `api_fast.py` - API FastAPI (porta 8000) com endpoints CRUD e validação via Pydantic.
- `create_db.py` - Script para criar/atualizar o banco `biblioteca.db` e inserir exemplos.
- `biblioteca.db` - Banco SQLite (opcional, pode ser criado pelo script).
- `templates/` - Templates Jinja2 para a interface Flask.
- `requirements.txt` - Dependências Python.

## Como executar (linha de comando)

1. Crie um ambiente virtual (recomendado) e instale dependências:
```bash
python -m venv venv
source venv/bin/activate        # Linux/macOS
venv\\Scripts\\activate         # Windows (PowerShell)
pip install -r requirements.txt
```

2. Inicialize o banco de dados (gera `biblioteca.db` com amostras):
```bash
python create_db.py
```

3. Rode a API FastAPI (porta 8000):
```bash
uvicorn api_fast:app --host 0.0.0.0 --port 8000 --reload
```

Abra `http://127.0.0.1:8000/docs` para testar via Swagger (requisito do trabalho).

4. Em outro terminal, execute a aplicação Flask (porta 5000):
```bash
python app_flask.py
```

Abra `http://127.0.0.1:5000` para ver a lista de livros e o formulário de cadastro.

## Observações técnicas / Comentários
- A API retorna códigos de status apropriados: 201 (criação), 200 (ok), 404 (não encontrado).
- A validação de entrada na API é feita com Pydantic (tipos, tamanhos e ranges).
- O Flask grava/consulta diretamente o mesmo arquivo SQLite para simplicidade; em ambientes reais, uma camada única de dados (por exemplo, via ORM) seria ideal para evitar duplicação de lógica.
- Se quiser que o Flask chame a API FastAPI em vez de acessar o DB diretamente, configure `BIB_DB` para apontar para um serviço remoto ou modifique o código para usar `requests` para consumir os endpoints.

## Testes rápidos (curl)
- Listar livros via API:
```bash
curl http://127.0.0.1:8000/livros
```
- Criar livro via API:
```bash
curl -X POST http://127.0.0.1:8000/livros -H "Content-Type: application/json" -d '{"titulo":"X","autor":"Y","ano_publicacao":2020,"disponivel":true}'
```
- Atualizar:
```bash
curl -X PUT http://127.0.0.1:8000/livros/1 -H "Content-Type: application/json" -d '{"titulo":"Novo","autor":"Autor","ano_publicacao":2000}'
```
- Deletar:
```bash
curl -X DELETE http://127.0.0.1:8000/livros/1
```