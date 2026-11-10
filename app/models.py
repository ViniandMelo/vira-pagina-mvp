from typing import Literal

from pydantic import field_validator
from sqlmodel import Field, SQLModel


class LivroBase(SQLModel):
    titulo: str = Field(index=True, min_length=1)
    autor: str = Field(index=True, min_length=1)
    preco: float = Field(ge=0)
    status_disponibilidade: str = Field(default="Disponível", index=True)
    corredor: str = Field(min_length=1)
    prateleira: str = Field(min_length=1)

    @field_validator("titulo", "autor", "corredor", "prateleira")
    @classmethod
    def validar_texto_obrigatorio(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("Este campo não pode ficar vazio.")
        return value


class Livro(LivroBase, table=True):
    id: int | None = Field(default=None, primary_key=True)


class LivroCreate(LivroBase):
    pass


class LivroUpdate(LivroBase):
    pass


class SugestaoLivroBase(SQLModel):
    titulo_sugerido: str = Field(min_length=1, max_length=200)
    autor_sugerido: str = Field(min_length=1, max_length=200)
    observacao: str | None = Field(default=None, max_length=2000)

    @field_validator("titulo_sugerido", "autor_sugerido")
    @classmethod
    def validar_texto_obrigatorio(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("Este campo não pode ficar vazio.")
        return value

    @field_validator("observacao")
    @classmethod
    def normalizar_observacao(cls, value: str | None) -> str | None:
        if value is None:
            return None
        return value.strip() or None


class SugestaoLivro(SugestaoLivroBase, table=True):
    id: int | None = Field(default=None, primary_key=True)
    status_sugestao: str = Field(default="Pendente", index=True)


class SugestaoLivroCreate(SugestaoLivroBase):
    pass


class SugestaoStatusUpdate(SQLModel):
    status_sugestao: Literal["Pendente", "Mantido na Lista"]


class SugestaoCatalogo(SQLModel):
    preco: float = Field(ge=0)
    corredor: str = Field(min_length=1, max_length=50)
    prateleira: str = Field(min_length=1, max_length=50)

    @field_validator("corredor", "prateleira")
    @classmethod
    def validar_localizacao(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("Este campo não pode ficar vazio.")
        return value
