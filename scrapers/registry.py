# scrapers/registry.py
from importlib import import_module
from pathlib import Path
from typing import Dict, Type
from inspect import isclass

from scrapers.base import BaseScraper

REGISTRY: Dict[str, Type[BaseScraper]] = {}

root = Path(__file__).parent

for py in root.rglob("*.py"):
    if py.name.startswith("_"):            # skip private helpers
        continue
    if py.stem in {"__init__", "base", "base_lazy", "models", "registry", "selectors"}:
        continue

    #       path  scrapers/linkedin/scraper.py  -> scrapers.linkedin.scraper
    mod_name = ".".join(py.relative_to(root).with_suffix("").parts)
    mod = import_module(f"scrapers.{mod_name}")

    for obj in mod.__dict__.values():
        if isclass(obj) and issubclass(obj, BaseScraper) and obj is not BaseScraper:
            REGISTRY[obj.platform.lower()] = obj

