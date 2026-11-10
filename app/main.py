from contextlib import asynccontextmanager
from pathlib import Path
from typing import Annotated, Any

from fastapi import Depends, FastAPI, HTTPException, Query, Request
from fastapi.encoders import jsonable_encoder
from fastapi.exceptions import RequestValidationError
from fastapi.openapi.utils import get_openapi
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel
from sqlalchemy.exc import IntegrityError
from sqlmodel import Session, select

from app.database import create_db_and_tables, get_session
from app.models import (
    Livro,
    LivroCreate,
    LivroUpdate,
    SugestaoLivro,
    SugestaoCatalogo,
    SugestaoLivroCreate,
    SugestaoStatusUpdate,
)


class ErrorResponse(BaseModel):
    detail: str | list[dict[str, Any]]


VALIDATION_ERROR_RESPONSE = {
    "model": ErrorResponse,
    "description": "Dados inválidos ou rejeitados ao processar a requisição.",
    "content": {
        "application/json": {
            "examples": {
                "dados_invalidos": {
                    "summary": "Dados de livro inválidos",
                    "value": {
                        "detail": [
                            {
                                "type": "greater_than_equal",
                                "loc": ["body", "preco"],
                                "msg": "Input should be greater than or equal to 0",
                                "input": -10,
                                "ctx": {"ge": 0},
                            }
                        ]
                    },
                },
            }
        }
    },
}
NOT_FOUND_RESPONSE = {
    "model": ErrorResponse,
    "description": "Livro não encontrado para o ID informado.",
    "content": {
        "application/json": {
            "example": {"detail": "Livro não encontrado."}
        }
    },
}


@asynccontextmanager
async def lifespan(_: FastAPI):
    create_db_and_tables()
    yield


app = FastAPI(title="Vira Página", lifespan=lifespan)
templates = Jinja2Templates(directory=str(Path(__file__).parent / "templates"))
app.mount(
    "/static",
    StaticFiles(directory=str(Path(__file__).parent / "static")),
    name="static",
)
SessionDep = Annotated[Session, Depends(get_session)]


@app.exception_handler(RequestValidationError)
async def tratar_dados_invalidos(_: Request, exc: RequestValidationError):
    return JSONResponse(
        status_code=400,
        content={"detail": jsonable_encoder(exc.errors())},
    )


def openapi_com_erros_documentados() -> dict[str, Any]:
    if app.openapi_schema:
        return app.openapi_schema

    schema = get_openapi(
        title=app.title,
        version=app.version,
        routes=app.routes,
    )
    for path_item in schema["paths"].values():
        for operation in path_item.values():
            if isinstance(operation, dict):
                operation.get("responses", {}).pop("422", None)
    app.openapi_schema = schema
    return app.openapi_schema


app.openapi = openapi_com_erros_documentados


@app.get("/", response_class=HTMLResponse)
def home(request: Request, session: SessionDep):
    livros = session.exec(select(Livro).order_by(Livro.titulo)).all()
    sugestoes = session.exec(
        select(SugestaoLivro).order_by(SugestaoLivro.id.desc())
    ).all()
    return templates.TemplateResponse(
        request=request,
        name="index.html",
        context={"livros": livros, "sugestoes": sugestoes},
    )


@app.get("/livros/", response_model=list[Livro], status_code=200)
def listar_livros(session: SessionDep):
    return session.exec(select(Livro).order_by(Livro.titulo)).all()


@app.post(
    "/livros/",
    response_model=Livro,
    status_code=201,
    responses={400: VALIDATION_ERROR_RESPONSE},
)
def cadastrar_livro(livro: LivroCreate, session: SessionDep):
    novo_livro = Livro.model_validate(livro)
    session.add(novo_livro)
    try:
        session.commit()
    except IntegrityError as exc:
        session.rollback()
        raise HTTPException(
            status_code=400,
            detail="Não foi possível cadastrar o livro com os dados informados.",
        ) from exc
    session.refresh(novo_livro)
    return novo_livro


@app.patch(
    "/livros/{livro_id}/venda",
    response_model=Livro,
    status_code=200,
    summary="Registrar venda de um livro",
    description=(
        "Altera a disponibilidade de um exemplar de 'Disponível' para 'Vendido'. "
        "Um livro já vendido não pode ser vendido novamente."
    ),
    responses={
        400: VALIDATION_ERROR_RESPONSE,
        404: NOT_FOUND_RESPONSE,
        409: {
            "model": ErrorResponse,
            "description": "O livro não está disponível para venda.",
            "content": {
                "application/json": {
                    "example": {
                        "detail": "Somente livros disponíveis podem ser vendidos."
                    }
                }
            },
        },
    },
)
def registrar_venda(livro_id: int, session: SessionDep):
    livro = session.get(Livro, livro_id)
    if livro is None:
        raise HTTPException(status_code=404, detail="Livro não encontrado.")
    if livro.status_disponibilidade != "Disponível":
        raise HTTPException(
            status_code=409,
            detail="Somente livros disponíveis podem ser vendidos.",
        )

    livro.status_disponibilidade = "Vendido"
    session.add(livro)
    session.commit()
    session.refresh(livro)
    return livro


@app.patch(
    "/livros/{livro_id}/toggle-status",
    response_model=Livro,
    status_code=200,
    summary="Alternar disponibilidade do livro",
    description="Alterna o status entre 'Disponível' e 'Vendido'.",
    responses={
        400: VALIDATION_ERROR_RESPONSE,
        404: NOT_FOUND_RESPONSE,
        409: {
            "model": ErrorResponse,
            "description": "O status atual não pode ser alternado.",
        },
    },
)
def alternar_status_livro(livro_id: int, session: SessionDep):
    livro = session.get(Livro, livro_id)
    if livro is None:
        raise HTTPException(status_code=404, detail="Livro não encontrado.")
    if livro.status_disponibilidade not in {"Disponível", "Vendido"}:
        raise HTTPException(
            status_code=409,
            detail="O status atual do livro não pode ser alternado.",
        )

    livro.status_disponibilidade = (
        "Vendido" if livro.status_disponibilidade == "Disponível" else "Disponível"
    )
    session.add(livro)
    session.commit()
    session.refresh(livro)
    return livro


@app.post(
    "/sugestoes/",
    response_model=SugestaoLivro,
    status_code=201,
    summary="Enviar sugestão de livro",
    description="Salva uma sugestão da comunidade para o acervo do sebo.",
    responses={400: VALIDATION_ERROR_RESPONSE},
)
def cadastrar_sugestao(
    sugestao: SugestaoLivroCreate,
    session: SessionDep,
):
    nova_sugestao = SugestaoLivro.model_validate(sugestao)
    session.add(nova_sugestao)
    session.commit()
    session.refresh(nova_sugestao)
    return nova_sugestao


@app.get(
    "/sugestoes/",
    response_model=list[SugestaoLivro],
    status_code=200,
    summary="Listar sugestões da comunidade",
)
def listar_sugestoes(session: SessionDep):
    return session.exec(
        select(SugestaoLivro)
        .order_by(SugestaoLivro.id.desc())
    ).all()


@app.patch(
    "/sugestoes/{sugestao_id}/status",
    response_model=SugestaoLivro,
    status_code=200,
    summary="Manter sugestão na lista de espera",
    responses={
        400: VALIDATION_ERROR_RESPONSE,
        404: {"model": ErrorResponse, "description": "Sugestão não encontrada."},
        409: {
            "model": ErrorResponse,
            "description": "Sugestão já adicionada ao catálogo.",
        },
    },
)
def atualizar_status_sugestao(
    sugestao_id: int,
    dados: SugestaoStatusUpdate,
    session: SessionDep,
):
    sugestao = session.get(SugestaoLivro, sugestao_id)
    if sugestao is None:
        raise HTTPException(status_code=404, detail="Sugestão não encontrada.")
    if sugestao.status_sugestao == "Adicionado ao Catálogo":
        raise HTTPException(
            status_code=409,
            detail="Sugestões já adicionadas ao catálogo não podem ser alteradas.",
        )

    sugestao.status_sugestao = dados.status_sugestao
    session.add(sugestao)
    session.commit()
    session.refresh(sugestao)
    return sugestao


@app.post(
    "/sugestoes/{sugestao_id}/adicionar-ao-catalogo",
    response_model=Livro,
    status_code=201,
    summary="Adicionar sugestão ao catálogo",
    description=(
        "Cria um livro a partir da sugestão. O operador informa preço e localização "
        "do exemplar antes da inclusão."
    ),
    responses={
        400: VALIDATION_ERROR_RESPONSE,
        404: {"model": ErrorResponse, "description": "Sugestão não encontrada."},
        409: {
            "model": ErrorResponse,
            "description": "A sugestão já foi adicionada ao catálogo.",
        },
    },
)
def adicionar_sugestao_ao_catalogo(
    sugestao_id: int,
    dados: SugestaoCatalogo,
    session: SessionDep,
):
    sugestao = session.get(SugestaoLivro, sugestao_id)
    if sugestao is None:
        raise HTTPException(status_code=404, detail="Sugestão não encontrada.")
    if sugestao.status_sugestao == "Adicionado ao Catálogo":
        raise HTTPException(
            status_code=409,
            detail="Esta sugestão já foi adicionada ao catálogo.",
        )

    livro = Livro(
        titulo=sugestao.titulo_sugerido,
        autor=sugestao.autor_sugerido,
        preco=dados.preco,
        corredor=dados.corredor,
        prateleira=dados.prateleira,
        status_disponibilidade="Disponível",
    )
    sugestao.status_sugestao = "Adicionado ao Catálogo"
    session.add(livro)
    session.add(sugestao)
    try:
        session.commit()
    except IntegrityError as exc:
        session.rollback()
        raise HTTPException(
            status_code=400,
            detail="Não foi possível adicionar a sugestão ao catálogo.",
        ) from exc
    session.refresh(livro)
    return livro


@app.get(
    "/livros/{livro_id}",
    response_model=Livro,
    status_code=200,
    responses={
        400: VALIDATION_ERROR_RESPONSE,
        404: NOT_FOUND_RESPONSE,
    },
)
def obter_livro(livro_id: int, session: SessionDep):
    livro = session.get(Livro, livro_id)
    if livro is None:
        raise HTTPException(status_code=404, detail="Livro não encontrado.")
    return livro


@app.put(
    "/livros/{livro_id}",
    response_model=Livro,
    status_code=200,
    responses={
        400: VALIDATION_ERROR_RESPONSE,
        404: NOT_FOUND_RESPONSE,
    },
)
def atualizar_livro(livro_id: int, dados: LivroUpdate, session: SessionDep):
    livro = session.get(Livro, livro_id)
    if livro is None:
        raise HTTPException(status_code=404, detail="Livro não encontrado.")

    livro.sqlmodel_update(dados.model_dump())
    try:
        session.commit()
    except IntegrityError as exc:
        session.rollback()
        raise HTTPException(
            status_code=400,
            detail="Não foi possível atualizar o livro com os dados informados.",
        ) from exc
    session.refresh(livro)
    return livro


@app.get(
    "/api/livros/busca",
    response_model=list[Livro],
    status_code=200,
    responses={400: VALIDATION_ERROR_RESPONSE},
)
def buscar_livros(
    session: SessionDep,
    q: Annotated[str, Query(min_length=1, description="Título ou autor")],
):
    busca = q.strip()
    if not busca:
        raise HTTPException(status_code=400, detail="Informe um título ou autor para buscar.")
    termo = f"%{busca}%"
    consulta = (
        select(Livro)
        .where(Livro.titulo.ilike(termo) | Livro.autor.ilike(termo))
        .order_by(Livro.titulo)
    )
    return session.exec(consulta).all()
