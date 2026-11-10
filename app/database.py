from pathlib import Path

from sqlmodel import SQLModel, Session, create_engine


DATABASE_URL = f"sqlite:///{Path(__file__).resolve().parent.parent / 'vira_pagina.db'}"
engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False},
)


def create_db_and_tables() -> None:
    SQLModel.metadata.create_all(engine)


def get_session():
    with Session(engine) as session:
        yield session
