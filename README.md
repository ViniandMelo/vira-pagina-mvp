# Sebo Vira Página — MVP de Gestão de Acervo

Sistema de gestão e localização física de livros do sebo comunitário Vira Página, desenvolvido em Python com FastAPI, SQLModel, SQLite e Jinja2.

## Requisitos no computador

- Python 3.12 ou superior instalado e disponível no terminal (`py --version` no Windows).
- Git, se ainda for clonar o repositório.
- PowerShell ou Git Bash no Windows.

## Preparar o projeto

### Primeira vez: clonar o repositório

No terminal, execute:

```bash
git clone https://github.com/ViniandMelo/vira-pagina-mvp.git
cd vira-pagina-mvp
```

### Projeto já clonado

Abra o terminal na pasta do projeto. Se o clone já existe, não é necessário cloná-lo novamente.

Crie o ambiente virtual apenas se a pasta `.venv` ainda não existir. No PowerShell e no Git Bash:

```bash
py -m venv .venv
```

Ative o ambiente e instale as dependências conforme o terminal utilizado.

#### PowerShell

```powershell
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
```

Se a ativação for bloqueada, use diretamente o Python do ambiente:

```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
```

#### Git Bash

```bash
source .venv/Scripts/activate
python -m pip install -r requirements.txt
```

## Iniciar e abrir o sistema

Com o ambiente virtual ativo, inicie o servidor:

```bash
python -m uvicorn app.main:app --reload
```

Mantenha o terminal aberto. A aplicação cria o banco SQLite local `vira_pagina.db` na primeira inicialização. Abra:

- Interface do acervo: http://127.0.0.1:8000/
- Swagger para testar a API: http://127.0.0.1:8000/docs
- Especificação OpenAPI em JSON: http://127.0.0.1:8000/openapi.json

No Swagger, expanda uma rota e clique em **Try it out**. O bloco **Responses** mostra os códigos esperados, os erros possíveis e exemplos dos corpos de erro. Clique em **Execute** para fazer a chamada real. Para conferir um erro, por exemplo, use ID `999999` em `GET /livros/{livro_id}` (se esse ID não existir).

## Rotas da API e respostas

| Método | Caminho | Sucesso | Erros documentados |
|---|---|---|---|
| GET | `/livros/` | `200 OK`, lista livros | — |
| POST | `/livros/` | `201 Created`, retorna o livro cadastrado | `400 Bad Request` para dados inválidos |
| GET | `/livros/{livro_id}` | `200 OK`, retorna um livro | `400` para ID inválido; `404 Not Found` se não existir |
| PUT | `/livros/{livro_id}` | `200 OK`, retorna o livro atualizado | `400` para dados/ID inválidos; `404` se não existir |
| GET | `/api/livros/busca?q={termo}` | `200 OK`, lista resultados por título ou autor | `400 Bad Request` se o termo estiver ausente ou vazio |

Uma URL que não corresponda a nenhuma rota retorna `404 Not Found`. Essa resposta geral de rota inexistente não é uma operação cadastrada no Swagger; ela pode ser verificada com o comando curl abaixo.

## Exemplos para testar a API no Git Bash

Deixe o servidor ativo em um terminal e execute os comandos a seguir em outro. `-i` exibe o status HTTP e os cabeçalhos junto ao corpo.

### Cadastrar um livro — esperado `201`

```bash
curl -i -X POST http://127.0.0.1:8000/livros/ \
  -H "Content-Type: application/json" \
  -d '{"titulo":"O Pequeno Príncipe","autor":"Antoine de Saint-Exupéry","preco":25.9,"status_disponibilidade":"Disponível","corredor":"A","prateleira":"2"}'
```

A resposta contém o livro e o `id` criado. Use esse ID nos próximos testes.

### Buscar por título ou autor — esperado `200`

```bash
curl -i "http://127.0.0.1:8000/api/livros/busca?q=Pequeno"
```

A resposta deve conter o livro e sua localização (`corredor` e `prateleira`).

### Consultar um ID inexistente — esperado `404`

```bash
curl -i http://127.0.0.1:8000/livros/999999
```

### Atualizar um ID inexistente — esperado `404`

```bash
curl -i -X PUT http://127.0.0.1:8000/livros/999999 \
  -H "Content-Type: application/json" \
  -d '{"titulo":"Livro","autor":"Autor","preco":20,"status_disponibilidade":"Disponível","corredor":"A","prateleira":"1"}'
```

### Enviar dados inválidos — esperado `400`

O preço negativo e o título vazio não passam pela validação:

```bash
curl -i -X POST http://127.0.0.1:8000/livros/ \
  -H "Content-Type: application/json" \
  -d '{"titulo":"","autor":"Autor","preco":-10,"corredor":"A","prateleira":"1"}'
```

### Buscar sem termo — esperado `400`

```bash
curl -i "http://127.0.0.1:8000/api/livros/busca?q="
```

### Acessar uma rota inexistente — esperado `404`

```bash
curl -i http://127.0.0.1:8000/rota-inexistente
```

## Executar os testes automatizados

Os testes usam um banco SQLite temporário isolado e **não precisam do servidor Uvicorn rodando**. Com o ambiente virtual ativo, instale as dependências de teste:

```bash
python -m pip install -r requirements-test.txt
```

Execute todos os testes com detalhes:

```bash
python -m pytest -v
```

Execute um único teste:

```bash
python -m pytest tests/test_main.py::test_missing_book_returns_not_found -v
```

Gere também o relatório de cobertura:

```bash
python -m pytest --cov=app --cov-report=term-missing
```
