"""Valide les fichiers JSON du projet Power BI contre les schémas officiels de Microsoft.

    python powerbi/validate_pbip.py [dossier_local_des_schemas]

Sans dossier local, les schémas sont téléchargés depuis developer.microsoft.com.
"""
from __future__ import annotations

import json
import sys
import urllib.request
from functools import lru_cache
from pathlib import Path

from jsonschema import Draft7Validator, Draft202012Validator
from referencing import Registry, Resource

HERE = Path(__file__).resolve().parent
PREFIX = "https://developer.microsoft.com/json-schemas/fabric/"
LOCAL = Path(sys.argv[1]) if len(sys.argv) > 1 else None


@lru_cache(maxsize=None)
def fetch(uri: str) -> dict:
    if LOCAL and uri.startswith(PREFIX):
        return json.loads((LOCAL / uri[len(PREFIX):]).read_text(encoding="utf-8"))
    with urllib.request.urlopen(uri, timeout=30) as r:
        return json.loads(r.read().decode("utf-8"))


def retrieve(uri: str) -> Resource:
    return Resource.from_contents(fetch(uri.split("#")[0]))


def main() -> int:
    files = sorted(p for p in HERE.glob("Tourisme-Suisse.*/**/*.json") if "StaticResources" not in p.parts)
    files += [HERE / "Tourisme-Suisse.pbip", *HERE.glob("Tourisme-Suisse.*/definition.pbi*"), *HERE.glob("Tourisme-Suisse.*/.platform")]
    registry = Registry(retrieve=retrieve)
    errors = checked = 0
    for f in files:
        doc = json.loads(f.read_text(encoding="utf-8"))
        uri = doc.get("$schema")
        if not uri:
            continue
        try:
            schema = fetch(uri)
        except FileNotFoundError:
            print(f"(schéma absent du dossier local, ignoré : {uri})")
            continue
        cls = Draft202012Validator if "2020-12" in schema.get("$schema", "") else Draft7Validator
        v = cls({**schema, "$id": schema.get("$id", uri)}, registry=registry)
        checked += 1
        for e in v.iter_errors(doc):
            errors += 1
            print(f"ERREUR {f.relative_to(HERE)} : {'/'.join(map(str, e.absolute_path))} : {e.message[:300]}")
    print(f"{checked} fichiers vérifiés, {errors} erreur(s)")
    return 1 if errors or checked == 0 else 0


if __name__ == "__main__":
    sys.exit(main())
