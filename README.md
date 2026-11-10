# vira-pagina-mvp
MVP do sistema de gestão de acervo e localização física para o Sebo Vira Página.


# 📚 Sebo Vira Página — MVP de Gestão de Acervo

Sistema de gestão e localização física de livros desenvolvido para otimizar o atendimento de balcão do sebo comunitário "Vira Página".

## 🛠️ Tecnologias Utilizadas
- **Linguagem:** Python 3.12
- **Framework Web / API:** FastAPI
- **Validação de Dados:** Pydantic
- **Banco de Dados:** SQLite (Embarcado/Local)
- **Autenticação e Segurança:** Hash Argon2 / Passlib (diretrizes OWASP Top 10)
- **Acessibilidade:** WCAG 2.1 AA (contraste 4.5:1, áreas de toque >= 44px)

## 📌 Requisitos Principais Atendidos
- **RF01:** Cadastro de novos livros e localização física (Corredor/Prateleira).
- **RF02:** Consulta rápida por título ou autor com resposta sob pressão de tempo.
- **RF03:** Atualização do status do exemplar para "Vendido".
- **RNF01:** Autenticação segura de operador sem senhas em texto limpo.
- **RNF03:** Desempenho de carregamento e busca em menos de 2,5s.

## 🚀 Como Executar o Projeto
```bash
# Clonar o repositório
git clone [https://github.com/SEU_USUARIO/vira-pagina-mvp.git](https://github.com/SEU_USUARIO/vira-pagina-mvp.git)

# Entrar no diretório
cd vira-pagina-mvp

# Criar e ativar ambiente virtual
python -m venv .venv
source .venv/bin/activate  # No Windows: .venv\Scripts\activate

# Instalar dependências
pip install -r requirements.txt

# Executar o servidor FastAPI
uvicorn app.main:app --reload
