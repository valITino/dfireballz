# Models — Directory Rules

## ForensicPayload Contract

The `ForensicPayload` in `forensic_payload.py` is the central data model. All investigation results flow through it.

- Do NOT remove or rename existing fields — downstream report generators depend on them
- All new fields MUST have default values (backward compatibility)
- All fields MUST be type-annotated
- Use `list[X] = Field(default_factory=list)` for collection fields
- Validate with Pydantic — no raw dicts

## ForensicSession

`base.py` defines the session model. It tracks case metadata and session state.

- Session IDs are UUIDs — never use sequential integers
- Timestamps use UTC ISO 8601 format
