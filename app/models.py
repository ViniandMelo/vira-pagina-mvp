from sqlmodel import Field, SQLModel


class LivroBase(SQLModel):
    titulo: str = Field(index=True, min_length=1)
    autor: str = Field(index=True, min_length=1)
    preco: float = Field(ge=0)
    status_disponibilidade: str = Field(default="Disponível", index=True)
    corredor: str = Field(min_length=1)
    prateleira: str = Field(min_length=1)


class Livro(LivroBase, table=True):
    id: int | None = Field(default=None, primary_key=True)


class LivroCreate(LivroBase):
    pass


class LivroUpdate(LivroBase):
    pass
