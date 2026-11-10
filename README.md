# Sebo Vira Página — MVP de Gestão de Acervo

Sistema de gestão e localização física de livros do sebo comunitário Vira Página, desenvolvido em Python com FastAPI, SQLModel, SQLite e Jinja2.

## Requisitos

- Python 3.12 ou superior
- Terminal (PowerShell ou Git Bash)

## Instalação e execução no Windows

Abra um terminal na pasta do projeto. Se ainda não clonou o repositório:

```bash
git clone https://github.com/ViniandMelo/vira-pagina-mvp.git
cd vira-pagina-mvp
```

Crie o ambiente virtual e instale as dependências. Use os comandos correspondentes ao terminal aberto.

### PowerShell

```powershell
py -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
```

Se o PowerShell bloquear a ativação do ambiente, execute `python -m pip install -r requirements.txt` usando diretamente o Python do ambiente:

```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
```

### Git Bash

```bash
py -m venv .venv
source .venv/Scripts/activate
python -m pip install -r requirements.txt
```

Inicie o servidor (funciona nos dois terminais):

```bash
python -m uvicorn app.main:app --reload
```

Mantenha esse terminal aberto enquanto testa o sistema. Na inicialização, o SQLite cria automaticamente o arquivo `vira_pagina.db` na pasta do projeto.

## Testar no navegador

- Interface do acervo: http://127.0.0.1:8000/
- Documentação interativa Swagger: http://127.0.0.1:8000/docs

No Swagger, abra `POST /livros/`, clique em **Try it out**, envie o JSON de exemplo abaixo e clique em **Execute**. Uma resposta `201` indica que o livro foi cadastrado.

```json
{
  "titulo": "O Pequeno Príncipe",
  "autor": "Antoine de Saint-Exupéry",
  "preco": 25.9,
  "status_disponibilidade": "Disponível",
  "corredor": "A",
  "prateleira": "2"
}
```

Em seguida, abra `GET /api/livros/busca`, informe `q=Pequeno` e clique em **Execute** para conferir o resultado da busca.

## Testar o cadastro no Postman

Você pode importar o cURL abaixo no Postman:

1. Abra **Import**.
2. Selecione **Raw text**.
3. Cole o comando e clique em **Continue** e **Import**.
4. Abra a requisição importada e clique em **Send**.

```bash
curl --location --request POST 'http://127.0.0.1:8000/livros/' \
  --header 'Content-Type: application/json' \
  --data-raw '{
    "titulo": "O Pequeno Príncipe",
    "autor": "Antoine de Saint-Exupéry",
    "preco": 25.9,
    "status_disponibilidade": "Disponível",
    "corredor": "A",
    "prateleira": "2"
  }'
```

O esperado é receber `201 Created` e um JSON contendo também o `id` gerado. Para buscar o livro no Postman, crie uma requisição **GET** para:

```text
http://127.0.0.1:8000/api/livros/busca?q=Pequeno
```

## Rotas disponíveis

| Método | Caminho | Descrição |
|---|---|---|
| GET | `/` | Interface web e listagem do acervo |
| POST | `/livros/` | Cadastra um livro |
| GET | `/api/livros/busca?q={termo}` | Busca por título ou autor |
