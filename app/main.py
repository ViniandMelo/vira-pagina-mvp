from contextlib import asynccontextmanager
from pathlib import Path
from typing import Annotated, Any

from fastapi import Depends, FastAPI, HTTPException, Query, Request
from fastapi.encoders import jsonable_encoder
from fastapi.exceptions import RequestValidationError
from fastapi.openapi.utils import get_openapi
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel
from sqlalchemy.exc import IntegrityError
from sqlmodel import Session, select

from app.database import create_db_and_tables, get_session
from app.models import Livro, LivroCreate, LivroUpdate


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
    return templates.TemplateResponse(
        request=request,
        name="index.html",
        context={"livros": livros},
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
