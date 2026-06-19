SNAPSHOT_SCHEMA_VERSION = "cell-engine.snapshot.v1"

SNAPSHOT_SCHEMA = {
    "$schema": "https://json-schema.org/draft/2020-12/schema",
    "title": "Cell engine snapshot",
    "type": "object",
    "required": ["schema_version", "definition", "state", "metadata"],
    "properties": {
        "schema_version": {"const": SNAPSHOT_SCHEMA_VERSION},
        "definition": {"type": "object"},
        "state": {"type": "object"},
        "metadata": {
            "type": "object",
            "required": ["engine", "created_at_utc"],
            "properties": {
                "engine": {"type": "string"},
                "created_at_utc": {"type": "string"},
            },
        },
    },
}

