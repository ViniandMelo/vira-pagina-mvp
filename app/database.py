from pathlib import Path

from sqlalchemy import inspect, text
from sqlmodel import SQLModel, Session, create_engine


DATABASE_URL = f"sqlite:///{Path(__file__).resolve().parent.parent / 'vira_pagina.db'}"
engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False},
)


def create_db_and_tables() -> None:
    SQLModel.metadata.create_all(engine)
    columns = {column["name"] for column in inspect(engine).get_columns("sugestaolivro")}
    if "status_sugestao" not in columns:
        with engine.begin() as connection:
            connection.execute(
                text(
                    "ALTER TABLE sugestaolivro "
                    "ADD COLUMN status_sugestao VARCHAR NOT NULL DEFAULT 'Pendente'"
                )
            )


def get_session():
    with Session(engine) as session:
        yield session
