from __future__ import annotations

import textwrap
from pathlib import Path


path = Path("tools/ace/character_retrieval.py")
text = path.read_text(encoding="utf-8")
start = text.index("def build_character_index(root: Path = ROOT)")
end = text.index("\ndef _norm_text", start)
replacement = textwrap.dedent(r'''
def _capsule_for_entity(entity: dict[str, object], canon_root: Path) -> Path | None:
    capsule_ref = entity.get("capsule_ref")
    if isinstance(capsule_ref, str) and capsule_ref.strip():
        candidate = (canon_root / capsule_ref.strip() / "identity.json").resolve()
        if candidate.is_file() and canon_root in candidate.parents:
            return candidate
    for key in ("capsule_id", "entity_id"):
        value = entity.get(key)
        if isinstance(value, str) and value.strip():
            candidate = canon_root / "canon/L2/entities" / value.strip() / "capsule/identity.json"
            if candidate.is_file():
                return candidate
    return None


def _capsule_value(payload: dict[str, object], *keys: str) -> str | None:
    for key in keys:
        value = payload.get(key)
        if isinstance(value, str) and value.strip():
            return value.strip()
    return None


def _record_from_flat_entity(entity_path: Path, canon_root: Path) -> tuple[CharacterRecord | None, str | None]:
    payload = _load_json(entity_path)
    if not isinstance(payload, dict) or payload.get("entity_kind") != "character":
        return None, None
    canonical_id = _safe_string(payload.get("entity_id"))
    entity_name = _safe_string(payload.get("name"))
    certainty = _safe_string(payload.get("certainty"))
    if not canonical_id or not entity_name or certainty not in ACCEPTED_CERTAINTIES:
        return None, None

    capsule_path = _capsule_for_entity(payload, canon_root)
    capsule_payload: dict[str, object] = {}
    if capsule_path is not None:
        loaded = _load_json(capsule_path)
        if isinstance(loaded, dict) and _safe_string(loaded.get("certainty")) in ACCEPTED_CERTAINTIES:
            capsule_payload = loaded

    aliases: list[str] = []
    for source in (payload.get("aliases"), capsule_payload.get("aliases")):
        if isinstance(source, list):
            for item in source:
                if isinstance(item, str) and item.strip() and item.strip() not in aliases:
                    aliases.append(item.strip())

    factions = payload.get("faction_bindings", [])
    faction_id = _capsule_value(capsule_payload, "faction_id")
    if not faction_id and isinstance(factions, list):
        faction_id = next((item.strip() for item in factions if isinstance(item, str) and item.strip()), None)

    binding = capsule_payload.get("location_binding", {})
    if not isinstance(binding, dict):
        binding = {}
    location_type = _safe_string(binding.get("type")) or _safe_string(payload.get("location_type"))
    location_ref = (
        _safe_string(binding.get("target_id"))
        or _safe_string(payload.get("region_id"))
        or _safe_string(payload.get("parent_org_id"))
    )
    location_basis = _safe_string(binding.get("basis"))

    capsule_dir = capsule_path.parent if capsule_path is not None else None
    traits = capsule_dir / "traits.json" if capsule_dir is not None else None
    knowledge = capsule_dir / "knowledge.jsonl" if capsule_dir is not None else None
    entity_ref = _relative_to_canonrec(entity_path, canon_root)
    return (
        CharacterRecord(
            canonical_id=canonical_id,
            name=_capsule_value(capsule_payload, "name", "character_name") or entity_name,
            aliases=tuple(aliases),
            role=_capsule_value(capsule_payload, "role", "character_role") or _safe_string(payload.get("role")),
            faction_id=faction_id,
            status=_safe_string(payload.get("status")) or _safe_string(capsule_payload.get("status")),
            certainty=certainty,
            location_type=location_type,
            location_ref=location_ref,
            location_basis=location_basis,
            identity_ref=entity_ref,
            identity_sha256=file_sha256(entity_path),
            traits_ref=_relative_to_canonrec(traits, canon_root) if traits is not None and traits.is_file() else None,
            traits_sha256=file_sha256(traits) if traits is not None and traits.is_file() else None,
            knowledge_ref=_relative_to_canonrec(knowledge, canon_root) if knowledge is not None and knowledge.is_file() else None,
            knowledge_sha256=file_sha256(knowledge) if knowledge is not None and knowledge.is_file() else None,
        ),
        _relative_to_canonrec(capsule_path, canon_root) if capsule_path is not None else None,
    )


def _record_from_capsule(identity_path: Path, canon_root: Path) -> CharacterRecord | None:
    payload = _load_json(identity_path)
    if not isinstance(payload, dict):
        return None
    certainty = _safe_string(payload.get("certainty"))
    canonical_id = _capsule_value(payload, "canonical_id", "capsule_id")
    name = _capsule_value(payload, "name", "character_name")
    if certainty not in ACCEPTED_CERTAINTIES or not canonical_id or not name:
        return None
    binding = payload.get("location_binding", {})
    if not isinstance(binding, dict):
        binding = {}
    aliases = payload.get("aliases", [])
    if not isinstance(aliases, list):
        aliases = []
    capsule_dir = identity_path.parent
    traits = capsule_dir / "traits.json"
    knowledge = capsule_dir / "knowledge.jsonl"
    return CharacterRecord(
        canonical_id=canonical_id,
        name=name,
        aliases=tuple(item.strip() for item in aliases if isinstance(item, str) and item.strip()),
        role=_capsule_value(payload, "role", "character_role"),
        faction_id=_capsule_value(payload, "faction_id"),
        status=_safe_string(payload.get("status")),
        certainty=certainty,
        location_type=_safe_string(binding.get("type")),
        location_ref=_safe_string(binding.get("target_id")),
        location_basis=_safe_string(binding.get("basis")),
        identity_ref=_relative_to_canonrec(identity_path, canon_root),
        identity_sha256=file_sha256(identity_path),
        traits_ref=_relative_to_canonrec(traits, canon_root) if traits.is_file() else None,
        traits_sha256=file_sha256(traits) if traits.is_file() else None,
        knowledge_ref=_relative_to_canonrec(knowledge, canon_root) if knowledge.is_file() else None,
        knowledge_sha256=file_sha256(knowledge) if knowledge.is_file() else None,
    )


def _records(root: Path) -> list[CharacterRecord]:
    canon_root = (root / CANONREC_REL).resolve()
    entities_root = canon_root / "canon/L2/entities"
    registry_root = entities_root / "characters"
    records: list[CharacterRecord] = []
    seen_ids: set[str] = set()
    consumed_capsules: set[str] = set()

    if registry_root.is_dir():
        for entity_path in sorted(registry_root.glob("*.json")):
            record, capsule_ref = _record_from_flat_entity(entity_path, canon_root)
            if record is None:
                continue
            if record.canonical_id in seen_ids:
                raise ACEError(
                    f"duplicate canonical character entity id in registry: {record.canonical_id}",
                    code="projection_invalid",
                )
            records.append(record)
            seen_ids.add(record.canonical_id)
            if capsule_ref:
                consumed_capsules.add(capsule_ref)

    # Compatibility fallback for canonical capsules that have not yet been
    # bridged into the flat entity registry.
    if entities_root.is_dir():
        for identity_path in sorted(entities_root.glob("*/capsule/identity.json")):
            rel = _relative_to_canonrec(identity_path, canon_root)
            if rel in consumed_capsules:
                continue
            record = _record_from_capsule(identity_path, canon_root)
            if record is None or record.canonical_id in seen_ids:
                continue
            records.append(record)
            seen_ids.add(record.canonical_id)

    return sorted(records, key=lambda item: (item.canonical_id.casefold(), item.name.casefold()))


def build_character_index(root: Path = ROOT) -> dict[str, Any]:
    """Build the deterministic registry-complete CanonRec character index."""

    public = [item.public_identity() for item in _records(root)]
    return {
        "schema_version": SCHEMA_VERSION,
        "record_type": "ace_character_identity_index",
        "index_version": CHARACTER_RETRIEVAL_VERSION,
        "record_count": len(public),
        "records": public,
        "index_sha256": semantic_sha256(public),
        "discovery_surfaces": [
            "canon/L2/entities/characters/*.json",
            "canon/L2/entities/*/capsule/identity.json",
        ],
    }

''')
path.write_text(text[:start] + replacement + text[end:], encoding="utf-8")

# Add the flat-only registry regression fixture and test.
test_path = Path("tests/test_aurora_ace_character_retrieval.py")
body = test_path.read_text(encoding="utf-8")
helper = textwrap.dedent(r'''

def _write_flat_character(
    root: Path,
    canonical_id: str,
    name: str,
    *,
    role: str = "Fighter Commander",
    faction_id: str = "galactic_union",
) -> None:
    path = root / core.CANONREC_REL / "canon/L2/entities/characters" / f"{canonical_id}.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(
            {
                "entity_kind": "character",
                "entity_id": canonical_id,
                "name": name,
                "aliases": [],
                "certainty": "CANON",
                "status": "active",
                "faction_bindings": [faction_id],
                "role": role,
                "location_type": None,
                "region_id": None,
                "parent_org_id": None,
            },
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
''')
marker = "\n\ndef _capability_index()"
if "def _write_flat_character(" not in body:
    if marker not in body:
        raise SystemExit("flat test helper insertion marker missing")
    body = body.replace(marker, helper + marker)

test = textwrap.dedent(r'''

def test_flat_entity_registry_character_is_retrieved_without_capsule(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    _write_flat_character(tmp_path, "char_aria_lenix", "Aria Lenix")
    _patch(monkeypatch)
    index = character_retrieval.build_character_index(tmp_path)
    assert [item["canonical_id"] for item in index["records"]] == ["char_aria_lenix"]
    query = character_retrieval.compile_existing_character_query_if_applicable(
        "Who is Aria Lenix?",
        {"name": "Aria Lenix", "existence_status": "known"},
        seed=808,
        mode="commit_ready",
        requester_kind="user",
        requester_id="pilot",
        session_ref=None,
        root=tmp_path,
    )
    assert query is not None
    receipt = character_retrieval.resolve_existing_character_query(
        query, tmp_path / "packet", root=tmp_path
    )
    assert receipt["status"] == "RETRIEVED_CANON"
    identity = receipt["answer"]["fields"][0]["value"]
    assert identity["canonical_id"] == "char_aria_lenix"
    assert identity["source_ref"].endswith("characters/char_aria_lenix.json")
''')
if "test_flat_entity_registry_character_is_retrieved_without_capsule" not in body:
    body += test + "\n"
test_path.write_text(body, encoding="utf-8")

# Correct the normative discovery surface.
doc = Path("docs/AURORA_ACE__ADDENDUM__CHARACTER_RETRIEVAL__v0.4__2026-08-11.md")
d = doc.read_text(encoding="utf-8")
old = """The initial deterministic index reads committed character capsule identities under:\n\n`canon/L2/entities/*/capsule/identity.json`\n\nAn eligible identity record contributes, when present:\n"""
new = """The initial deterministic index uses the flat CanonRec character entity registry as its primary discovery surface:\n\n`canon/L2/entities/characters/*.json`\n\nWhen an entity record carries a `capsule_ref` / `capsule_id`, ACE follows that explicit bridge into `canon/L2/entities/*/capsule/identity.json` and uses the capsule as richer identity evidence. Capsule-only canonical characters remain a compatibility fallback so older recovered canon is not omitted while the entity registry is normalized.\n\nAn eligible character record contributes, when present:\n"""
if d.count(old) != 1:
    raise SystemExit("normative discovery paragraph missing")
doc.write_text(d.replace(old, new), encoding="utf-8")
