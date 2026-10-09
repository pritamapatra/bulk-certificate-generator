from typing import Annotated

from pydantic import BaseModel, EmailStr, StringConstraints

RecipientName = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=100)]


class RecipientIn(BaseModel):
    name: RecipientName
    email: EmailStr
