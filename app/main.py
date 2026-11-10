from contextlib import asynccontextmanager
from pathlib import Path
from typing import Annotated

from fastapi import Depends, FastAPI, HTTPException, Query, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlmodel import Session, select

from app.database import create_db_and_tables, get_session
from app.models import Livro


@asynccontextmanager
async def lifespan(_: FastAPI):
    create_db_and_tables()
    yield


app = FastAPI(title="Vira Página", lifespan=lifespan)
templates = Jinja2Templates(directory=str(Path(__file__).parent / "templates"))
SessionDep = Annotated[Session, Depends(get_session)]


@app.get("/", response_class=HTMLResponse)
def home(request: Request, session: SessionDep):
    livros = session.exec(select(Livro).order_by(Livro.titulo)).all()
    return templates.TemplateResponse(
        request=request,
        name="index.html",
        context={"livros": livros},
    )


@app.post("/livros/", response_model=Livro, status_code=201)
def cadastrar_livro(livro: Livro, session: SessionDep):
    session.add(livro)
    session.commit()
    session.refresh(livro)
    return livro


@app.get("/api/livros/busca", response_model=list[Livro])
def buscar_livros(
    session: SessionDep,
    q: Annotated[str, Query(min_length=1, description="Título ou autor")],
):
    busca = q.strip()
    if not busca:
        raise HTTPException(status_code=422, detail="Informe um título ou autor para buscar.")
    termo = f"%{busca}%"
    consulta = select(Livro).where(
        Livro.titulo.ilike(termo) | Livro.autor.ilike(termo)
    ).order_by(Livro.titulo)
    return session.exec(consulta).all()
