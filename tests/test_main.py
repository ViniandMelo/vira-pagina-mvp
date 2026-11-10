import pytest
from fastapi.testclient import TestClient
from sqlalchemy import text
from sqlalchemy.pool import StaticPool
from sqlmodel import Session, SQLModel, create_engine

import app.database as database
from app.database import get_session
from app.main import app
from app.models import SugestaoLivro


@pytest.fixture
def client():
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    SQLModel.metadata.create_all(engine)

    def get_test_session():
        with Session(engine) as session:
            yield session

    previous_overrides = app.dependency_overrides.copy()
    app.dependency_overrides[get_session] = get_test_session
    test_client = TestClient(app)
    try:
        yield test_client
    finally:
        test_client.close()
        app.dependency_overrides.clear()
        app.dependency_overrides.update(previous_overrides)
        engine.dispose()


def test_home_returns_html(client):
    response = client.get("/")

    assert response.status_code == 200
    assert "text/html" in response.headers["content-type"]
    assert "Acervo de livros" in response.text
    assert "Vira Página" in response.text


def test_home_has_accessible_search_and_keyboard_navigation(client):
    response = client.get("/")

    assert '<label class="search-label" for="busca">' in response.text
    assert 'id="busca" class="search-input"' in response.text
    assert 'aria-describedby="busca-ajuda"' in response.text
    assert 'aria-live="polite" aria-atomic="true"' in response.text
    assert '<a class="skip-link" href="#conteudo">' in response.text
    assert 'id="limpar-busca" class="clear-button" type="button"' in response.text
    assert 'id="form-livro"' in response.text
    assert 'id="form-sugestao"' in response.text
    assert 'data-livro-id="1"' not in response.text
    for field_id in (
        "livro-titulo",
        "livro-autor",
        "livro-preco",
        "livro-corredor",
        "livro-prateleira",
        "sugestao-titulo",
        "sugestao-autor",
        "sugestao-observacao",
    ):
        assert f'id="{field_id}"' in response.text
        assert "placeholder=" in response.text.split(f'id="{field_id}"', 1)[1].split(">", 1)[0]


def test_home_references_images_and_suggestion_management(client):
    suggestion = client.post(
        "/sugestoes/",
        json={"titulo_sugerido": "Livro da comunidade", "autor_sugerido": "Autora"},
    ).json()

    response = client.get("/")

    assert response.status_code == 200
    assert 'src="/static/image.png"' in response.text
    assert 'src="/static/image%20copy.png"' in response.text
    for image_path in ("/static/image.png", "/static/image%20copy.png"):
        image_response = client.get(image_path)
        assert image_response.status_code == 200
        assert image_response.headers["content-type"] == "image/png"
    assert suggestion["titulo_sugerido"] in response.text
    assert "Status: Pendente" in response.text
    assert f'aria-controls="dados-catalogo-{suggestion["id"]}"' in response.text


def test_create_book_returns_created_book(client):
    payload = {
        "titulo": "O Pequeno Príncipe",
        "autor": "Antoine de Saint-Exupéry",
        "preco": 25.9,
        "status_disponibilidade": "Disponível",
        "corredor": "A",
        "prateleira": "2",
    }

    response = client.post("/livros/", json=payload)

    assert response.status_code == 201
    assert response.json() == {"id": 1, **payload}


def test_search_returns_matching_book_and_physical_location(client):
    payload = {
        "titulo": "O Pequeno Príncipe",
        "autor": "Antoine de Saint-Exupéry",
        "preco": 25.9,
        "status_disponibilidade": "Disponível",
        "corredor": "A",
        "prateleira": "2",
    }
    client.post("/livros/", json=payload)

    response = client.get("/api/livros/busca", params={"q": "Príncipe"})

    assert response.status_code == 200
    livros = response.json()
    assert len(livros) == 1
    assert livros[0]["titulo"] == payload["titulo"]
    assert livros[0]["corredor"] == "A"
    assert livros[0]["prateleira"] == "2"


def test_register_sale_changes_book_status(client):
    payload = {
        "titulo": "Livro para vender",
        "autor": "Autora",
        "preco": 15,
        "corredor": "B",
        "prateleira": "4",
    }
    livro = client.post("/livros/", json=payload).json()

    response = client.patch(f"/livros/{livro['id']}/venda")

    assert response.status_code == 200
    assert response.json()["status_disponibilidade"] == "Vendido"
    assert client.get(f"/livros/{livro['id']}").json()["status_disponibilidade"] == "Vendido"
    page = client.get("/").text
    assert f'data-livro-id="{livro["id"]}"' in page
    assert f'Voltar ao estoque: {livro["titulo"]}' in page


def test_toggle_book_status_changes_both_directions(client):
    livro = client.post(
        "/livros/",
        json={
            "titulo": "Livro alternável",
            "autor": "Autora",
            "preco": 15,
            "corredor": "B",
            "prateleira": "4",
        },
    ).json()

    vendido = client.patch(f"/livros/{livro['id']}/toggle-status")
    disponivel = client.patch(f"/livros/{livro['id']}/toggle-status")

    assert vendido.status_code == 200
    assert vendido.json()["status_disponibilidade"] == "Vendido"
    assert disponivel.status_code == 200
    assert disponivel.json()["status_disponibilidade"] == "Disponível"


def test_toggle_rejects_unrecognized_book_status(client):
    livro = client.post(
        "/livros/",
        json={
            "titulo": "Livro com status inesperado",
            "autor": "Autora",
            "preco": 15,
            "status_disponibilidade": "Em análise",
            "corredor": "B",
            "prateleira": "4",
        },
    ).json()

    response = client.patch(f"/livros/{livro['id']}/toggle-status")

    assert response.status_code == 409


def test_available_book_card_has_sale_button(client):
    livro = client.post(
        "/livros/",
        json={
            "titulo": "Livro disponível",
            "autor": "Autora",
            "preco": 15,
            "corredor": "B",
            "prateleira": "4",
        },
    ).json()

    response = client.get("/")

    assert f'data-livro-id="{livro["id"]}"' in response.text
    assert f'Marcar como vendido: {livro["titulo"]}' in response.text


def test_cannot_register_sale_for_missing_or_sold_book(client):
    missing_response = client.patch("/livros/999/venda")
    assert missing_response.status_code == 404

    livro = client.post(
        "/livros/",
        json={
            "titulo": "Livro vendido",
            "autor": "Autora",
            "preco": 15,
            "corredor": "B",
            "prateleira": "4",
        },
    ).json()
    client.patch(f"/livros/{livro['id']}/venda")

    repeated_sale = client.patch(f"/livros/{livro['id']}/venda")
    assert repeated_sale.status_code == 409
    assert repeated_sale.json()["detail"] == "Somente livros disponíveis podem ser vendidos."


def test_create_book_suggestion(client):
    response = client.post(
        "/sugestoes/",
        json={
            "titulo_sugerido": "Livro desejado",
            "autor_sugerido": "Autora",
            "observacao": "Gostaria de encontrar este título.",
        },
    )

    assert response.status_code == 201
    assert response.json() == {
        "id": 1,
        "titulo_sugerido": "Livro desejado",
        "autor_sugerido": "Autora",
        "observacao": "Gostaria de encontrar este título.",
        "status_sugestao": "Pendente",
    }


def test_suggestion_observation_is_optional_and_blank_titles_are_invalid(client):
    response = client.post(
        "/sugestoes/",
        json={"titulo_sugerido": "Título", "autor_sugerido": "Autora"},
    )

    assert response.status_code == 201
    assert response.json()["observacao"] is None

    invalid_response = client.post(
        "/sugestoes/",
        json={"titulo_sugerido": "   ", "autor_sugerido": "Autora"},
    )
    assert invalid_response.status_code == 400


def test_suggestion_can_be_kept_or_added_to_catalog(client):
    suggestion = client.post(
        "/sugestoes/",
        json={
            "titulo_sugerido": "Livro da comunidade",
            "autor_sugerido": "Autora",
            "observacao": "Pedido de leitura",
        },
    ).json()

    kept = client.patch(
        f"/sugestoes/{suggestion['id']}/status",
        json={"status_sugestao": "Mantido na Lista"},
    )
    assert kept.status_code == 200
    assert kept.json()["status_sugestao"] == "Mantido na Lista"

    added = client.post(
        f"/sugestoes/{suggestion['id']}/adicionar-ao-catalogo",
        json={"preco": 32.5, "corredor": "C", "prateleira": "9"},
    )
    assert added.status_code == 201
    assert added.json()["titulo"] == suggestion["titulo_sugerido"]
    assert added.json()["autor"] == suggestion["autor_sugerido"]
    assert added.json()["preco"] == 32.5
    assert added.json()["corredor"] == "C"
    assert added.json()["prateleira"] == "9"
    assert client.get("/sugestoes/").json()[0]["status_sugestao"] == "Adicionado ao Catálogo"
    assert any(
        book["titulo"] == suggestion["titulo_sugerido"]
        for book in client.get("/livros/").json()
    )


def test_suggestion_management_rejects_missing_or_completed_suggestions(client):
    missing = client.patch(
        "/sugestoes/999/status",
        json={"status_sugestao": "Mantido na Lista"},
    )
    assert missing.status_code == 404

    suggestion = client.post(
        "/sugestoes/",
        json={"titulo_sugerido": "Outro livro", "autor_sugerido": "Autora"},
    ).json()
    client.post(
        f"/sugestoes/{suggestion['id']}/adicionar-ao-catalogo",
        json={"preco": 10, "corredor": "A", "prateleira": "1"},
    )
    repeated = client.post(
        f"/sugestoes/{suggestion['id']}/adicionar-ao-catalogo",
        json={"preco": 10, "corredor": "A", "prateleira": "1"},
    )
    assert repeated.status_code == 409


def test_suggestion_schema_migration_preserves_existing_rows(monkeypatch, tmp_path):
    engine = create_engine(f"sqlite:///{tmp_path / 'legacy.db'}")
    with engine.begin() as connection:
        connection.execute(
            text(
                "CREATE TABLE sugestaolivro ("
                "id INTEGER PRIMARY KEY, "
                "titulo_sugerido VARCHAR NOT NULL, "
                "autor_sugerido VARCHAR NOT NULL, "
                "observacao VARCHAR)"
            )
        )
        connection.execute(
            text(
                "INSERT INTO sugestaolivro "
                "(titulo_sugerido, autor_sugerido, observacao) "
                "VALUES ('Livro antigo', 'Autora', NULL)"
            )
        )
    monkeypatch.setattr(database, "engine", engine)

    database.create_db_and_tables()

    with Session(engine) as session:
        suggestion = session.get(SugestaoLivro, 1)
        assert suggestion is not None
        assert suggestion.titulo_sugerido == "Livro antigo"
        assert suggestion.status_sugestao == "Pendente"
    engine.dispose()


def test_missing_book_returns_not_found(client):
    response = client.get("/livros/999")

    assert response.status_code == 404
    assert response.json()["detail"] == "Livro não encontrado."


def test_invalid_book_data_returns_bad_request(client):
    response = client.post(
        "/livros/",
        json={
            "titulo": "",
            "autor": "Autor",
            "preco": -1,
            "corredor": "A",
            "prateleira": "1",
        },
    )

    assert response.status_code == 400
    assert "detail" in response.json()


def test_unknown_route_returns_not_found(client):
    response = client.get("/rota-inexistente")

    assert response.status_code == 404


def test_openapi_documents_api_error_scenarios(client):
    schema = client.get("/openapi.json").json()
    paths = schema["paths"]

    assert "400" in paths["/livros/"]["post"]["responses"]
    assert "201" in paths["/livros/"]["post"]["responses"]
    assert "404" in paths["/livros/{livro_id}"]["get"]["responses"]
    assert "404" in paths["/livros/{livro_id}"]["put"]["responses"]
    assert "400" in paths["/api/livros/busca"]["get"]["responses"]
    assert "409" in paths["/livros/{livro_id}/venda"]["patch"]["responses"]
    assert "201" in paths["/sugestoes/"]["post"]["responses"]
    assert "404" in paths["/livros/{livro_id}/venda"]["patch"]["responses"]
    assert "200" in paths["/livros/{livro_id}/toggle-status"]["patch"]["responses"]
    assert "400" in paths["/livros/{livro_id}/toggle-status"]["patch"]["responses"]
    assert "409" in paths["/livros/{livro_id}/toggle-status"]["patch"]["responses"]
    assert "200" in paths["/sugestoes/"]["get"]["responses"]
    assert "400" in paths["/sugestoes/{sugestao_id}/status"]["patch"]["responses"]
    assert "409" in paths["/sugestoes/{sugestao_id}/status"]["patch"]["responses"]
    assert "201" in paths["/sugestoes/{sugestao_id}/adicionar-ao-catalogo"]["post"]["responses"]
    assert "422" not in paths["/api/livros/busca"]["get"]["responses"]
    bad_request = paths["/api/livros/busca"]["get"]["responses"]["400"]
    assert "dados_invalidos" in bad_request["content"]["application/json"]["examples"]
    not_found = paths["/livros/{livro_id}"]["get"]["responses"]["404"]
    assert not_found["content"]["application/json"]["example"]["detail"] == "Livro não encontrado."
