from sqlmodel import Field, SQLModel


class Livro(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    titulo: str = Field(index=True, min_length=1)
    autor: str = Field(index=True, min_length=1)
    preco: float = Field(ge=0)
    status_disponibilidade: str = Field(default="Disponível", index=True)
    corredor: str
    prateleira: str
