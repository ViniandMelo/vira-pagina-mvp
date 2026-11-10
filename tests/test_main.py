import pytest
from fastapi.testclient import TestClient
from sqlalchemy.pool import StaticPool
from sqlmodel import Session, SQLModel, create_engine

from app.database import get_session
from app.main import app


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
    assert "422" not in paths["/api/livros/busca"]["get"]["responses"]
    bad_request = paths["/api/livros/busca"]["get"]["responses"]["400"]
    assert "dados_invalidos" in bad_request["content"]["application/json"]["examples"]
    not_found = paths["/livros/{livro_id}"]["get"]["responses"]["404"]
    assert not_found["content"]["application/json"]["example"]["detail"] == "Livro não encontrado."
