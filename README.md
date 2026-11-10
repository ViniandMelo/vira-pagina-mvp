# Sebo Vira Página — MVP de Gestão de Acervo

Aplicação web para cadastrar e localizar livros de um sebo comunitário, acompanhar vendas e organizar sugestões da comunidade. O MVP foi desenvolvido com Python, FastAPI, SQLModel, SQLite e Jinja2.

<p align="center">
  <img src="app/static/image.png" alt="Interior de um sebo com estantes de livros" width="640">
</p>

<p align="center">
  <em>Um espaço para encontrar e compartilhar novas histórias.</em>
</p>

<p align="center">
  <img src="app/static/image%20copy.png" alt="Estantes de livros organizadas no sebo" width="420">
</p>

> **Status da entrega:** MVP funcional para o escopo atual. Inclui cadastro e busca de livros, alternância de disponibilidade, gestão de sugestões, interface responsiva com recursos de acessibilidade e testes automatizados. A integração contínua executa os testes com Python 3.12 em pushes e pull requests para `main` e `master`.

## Requisitos no computador

- Python 3.12 instalado e disponível no terminal (`py --version` no Windows). A CI do projeto também usa Python 3.12.
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

Crie o ambiente virtual apenas se a pasta `.venv` ainda não existir:

```bash
py -m venv .venv
```

Ative o ambiente e instale as dependências da aplicação e de teste conforme o terminal utilizado. Se for executar apenas a aplicação, pode instalar somente `requirements.txt`; para rodar os testes, instale também `requirements-test.txt`.

#### PowerShell

```powershell
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt -r requirements-test.txt
```

Se a ativação for bloqueada, use diretamente o Python do ambiente:

```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements.txt -r requirements-test.txt
```

#### Git Bash

```bash
source .venv/Scripts/activate
python -m pip install -r requirements.txt -r requirements-test.txt
```

Se já possui o clone e o ambiente virtual, entre na pasta do projeto, ative `.venv` e atualize as dependências com o mesmo comando de instalação acima. Não é necessário clonar novamente.

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

Na página inicial, a equipe cadastra exemplares e usa os botões nos cartões para alternar entre **Marcar como Vendido** e **Voltar ao Estoque**. A comunidade envia sugestões; o operador pode mantê-las na lista de espera ou adicioná-las ao catálogo informando preço e localização. Os formulários têm rótulos explícitos, feedback acessível e controles dimensionados para uso por teclado e toque.

## Rotas da API e respostas

| Método | Caminho | Sucesso | Erros documentados |
|---|---|---|---|
| GET | `/livros/` | `200 OK`, lista livros | — |
| POST | `/livros/` | `201 Created`, retorna o livro cadastrado | `400 Bad Request` para dados inválidos |
| GET | `/livros/{livro_id}` | `200 OK`, retorna um livro | `400` para ID inválido; `404 Not Found` se não existir |
| PUT | `/livros/{livro_id}` | `200 OK`, retorna o livro atualizado | `400` para dados/ID inválidos; `404` se não existir |
| PATCH | `/livros/{livro_id}/venda` | `200 OK`, registra a venda e marca como `Vendido` | `404` se não existir; `409 Conflict` se já não estiver disponível |
| PATCH | `/livros/{livro_id}/toggle-status` | `200 OK`, alterna entre `Disponível` e `Vendido` | `400` para ID inválido; `404` se não existir; `409` para status incompatível |
| GET | `/api/livros/busca?q={termo}` | `200 OK`, lista resultados por título ou autor | `400 Bad Request` se o termo estiver ausente ou vazio |
| POST | `/sugestoes/` | `201 Created`, salva sugestão com status `Pendente` | `400 Bad Request` para dados inválidos |
| GET | `/sugestoes/` | `200 OK`, lista sugestões, da mais recente à mais antiga | — |
| PATCH | `/sugestoes/{sugestao_id}/status` | `200 OK`, define `Pendente` ou `Mantido na Lista` | `400` para dados/ID inválidos; `404` se não existir; `409` se já adicionada ao catálogo |
| POST | `/sugestoes/{sugestao_id}/adicionar-ao-catalogo` | `201 Created`, cria livro e marca a sugestão como `Adicionado ao Catálogo` | `400` para dados inválidos; `404` se não existir; `409` se já adicionada |

Na interface inicial, a equipe pode cadastrar exemplares e alternar o status nos cartões entre **Marcar como Vendido** e **Voltar ao Estoque**. A comunidade pode enviar sugestões; a equipe pode mantê-las na lista de espera ou adicioná-las ao catálogo. Ao adicionar uma sugestão, informe preço e localização física; o livro e o novo status da sugestão são gravados juntos.

Na primeira inicialização após esta atualização, a aplicação adiciona a coluna `status_sugestao` à tabela SQLite existente, preenchendo sugestões anteriores como `Pendente`. Essa migração é aditiva e preserva os registros existentes.

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

### Registrar venda de um livro disponível — esperado `200`

Use o ID retornado no cadastro; substitua `1` pelo ID real:

```bash
curl -i -X PATCH http://127.0.0.1:8000/livros/1/toggle-status
```

Na primeira chamada, o livro passa para `Vendido`; chame novamente para voltar a `Disponível`. Um ID que não existe retorna `404`.

O endpoint `/livros/{livro_id}/venda` continua disponível para registrar uma venda apenas uma vez. Ele retorna `409 Conflict` se o livro já estiver vendido.

### Enviar sugestão de título — esperado `201`

```bash
curl -i -X POST http://127.0.0.1:8000/sugestoes/ \
  -H "Content-Type: application/json" \
  -d '{"titulo_sugerido":"A Ilha do Tesouro","autor_sugerido":"Robert Louis Stevenson","observacao":"Gostaria de encontrar uma edição em bom estado."}'
```

O campo `observacao` é opcional.

### Listar sugestões — esperado `200`

```bash
curl -i http://127.0.0.1:8000/sugestoes/
```

Guarde o `id` da sugestão para usar nos comandos de gestão abaixo.

### Manter uma sugestão na lista de espera — esperado `200`

```bash
curl -i -X PATCH http://127.0.0.1:8000/sugestoes/1/status \
  -H "Content-Type: application/json" \
  -d '{"status_sugestao":"Mantido na Lista"}'
```

O status também pode ser redefinido para `Pendente`. Sugestões já adicionadas ao catálogo não podem ser alteradas.

### Adicionar uma sugestão ao catálogo — esperado `201`

Informe preço e localização do exemplar; o título e o autor vêm da sugestão:

```bash
curl -i -X POST http://127.0.0.1:8000/sugestoes/1/adicionar-ao-catalogo \
  -H "Content-Type: application/json" \
  -d '{"preco":32.50,"corredor":"C","prateleira":"9"}'
```

Uma inclusão repetida retorna `409 Conflict`. Se o ID não existir, a API retorna `404`.

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

Os testes usam um banco SQLite temporário isolado e **não precisam do servidor Uvicorn rodando**. Com o ambiente virtual ativo, instale as dependências de teste (caso ainda não tenha instalado):

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

O workflow do GitHub Actions repete a execução de `python -m pytest -v` automaticamente em pushes e pull requests para `main` e `master`.
