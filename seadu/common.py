from dataclasses import dataclass
from datetime import datetime
from pathlib import Path


@dataclass
class Settings:
    token: str
    server_url: str


@dataclass
class Item:
    path: Path
    size: int
    mtime: datetime
