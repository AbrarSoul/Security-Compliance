from typing import Protocol

from app.services.outputs.types import OutputFinding


class OutputDetector(Protocol):
    name: str

    def detect(self, text: str) -> list[OutputFinding]: ...
