import re
from typing import Annotated

from pydantic import AfterValidator, Field

_HTML = re.compile(r"<[^>]+>")


def require_plain(value: str) -> str:
    text = value.strip()
    if not text or _HTML.search(text):
        raise ValueError("invalid")
    return text


PlainText = Annotated[str, AfterValidator(require_plain), Field(min_length=1)]
