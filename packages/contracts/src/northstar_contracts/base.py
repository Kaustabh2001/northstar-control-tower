from datetime import UTC, datetime
from typing import Annotated

from pydantic import BaseModel, ConfigDict, Field

NonEmptyString = Annotated[str, Field(min_length=1)]
Identifier = Annotated[
    str,
    Field(
        min_length=3,
        max_length=120,
        pattern=r"^[a-zA-Z0-9][a-zA-Z0-9._:/-]*$",
    ),
]
SemanticVersion = Annotated[
    str,
    Field(pattern=r"^(0|[1-9]\d*)\.(0|[1-9]\d*)\.(0|[1-9]\d*)(?:[-+][0-9A-Za-z.-]+)?$"),
]


def utc_now() -> datetime:
    return datetime.now(UTC)


class ContractModel(BaseModel):
    """Strict base model used on every service boundary."""

    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)
