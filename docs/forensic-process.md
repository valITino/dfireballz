# DFIReballz Forensic Process Model

This document defines the canonical six-phase forensic process every DFIReballz
investigation follows. It is the platform's procedural backbone: the order in
which work happens, the criteria for moving between phases, the on-disk layout
that mirrors those phases, and the DFIReballz tooling that belongs in each.

The model is written from publicly available standards. **No draft or
copyrighted standard text is reproduced.** ASTM WK96121 (AI governance for
forensic science, subcommittee E30.16) is being watched but is not used as a
basis here — it is an unballoted draft and ASTM's IP policy prohibits AI
processing of its text. We will revisit on publication.

## Why a phase model

Without explicit phases, an investigation is just a sequence of tool calls.
That is hard to defend, hard to audit, and hard for an AI agent to drive
correctly. Phases give every action a known place in the lifecycle, make
entry/exit criteria checkable, and produce work product whose structure is
recognizable to reviewers and to courts.

Phases are **soft gates** by default in this rollout: the platform documents
and recommends order but does not refuse out-of-order actions. Strict gating
in the orchestrator is a planned follow-up slice. Loopback (returning to an
earlier phase) is allowed at any time but must be logged — see "Loopback
policy" below.

## Standards basis

The phase model is consolidated from:

| Standard | Scope |
|---|---|
| ISO/IEC 27037:2012 | Identification, collection, acquisition, preservation of digital evidence |
| ISO/IEC 27041:2015 | Assurance of investigation methods |
| ISO/IEC 27042:2015 | Analysis and interpretation of digital evidence |
| ISO/IEC 27043:2015 | Incident investigation principles and processes |
| NIST SP 800-86 | Guide to Integrating Forensic Techniques into Incident Response (4-phase model) |
| SWGDE Best Practices | Computer forensic acquisitions and examinations |
| ACPO Good Practice Guide | Four principles of digital evidence handling |
| RFC 3227 | Guidelines for evidence collection and archiving (order of volatility) |

Watched (not used as basis):

- **ASTM WK96121** — early-stage draft, E30.16, initiated 2025-08-20. Topic
  (AI governance in forensic science) is genuinely relevant to this platform.
  Revisit on ballot/publication; do not feed the draft text into AI tooling.

## The six phases

```
1. Readiness  →  2. Identification  →  3. Acquisition  →
   4. Examination  →  5. Analysis  →  6. Reporting / Closure
```

Each phase has a fixed contract: **entry criteria** that must be true to
begin, **activities** carried out within it, **exit criteria** that must be
true to leave, and a **canonical output location** under the case directory.

### Phase 1 — Readiness

**Purpose.** Prove the platform, the analyst, and the case are ready to
handle evidence with integrity *before* any evidence is touched.

**Entry criteria.**

- An investigation has been authorized (case opened via the orchestrator).
- The legal/organizational authority for the investigation is recorded on
  the case.

**Activities.**

- Case created with `case_number`, classification, investigator, and the
  documented authority.
- MCP server health-check passes for every server the playbook needs.
- Tool versions captured and pinned to the case (e.g. `dc3dd --version`,
  `volatility3 --version`, `tshark -v`).
- Required API keys for the planned playbook validated (no placeholder
  secrets, no expired keys).
- Time source attested (NTP sync confirmed; UTC).
- Working directory `cases/<case-id>/01-readiness/` created.
- Chain-of-custody log initialized for the case.

**Exit criteria.**

- `01-readiness/case-precondition.json` exists and records: case_id,
  investigator, authority reference, MCP health snapshot, pinned tool
  versions, API key presence (presence only — never values), time source,
  UTC offset of the host clock.
- A chain-of-custody entry of action `case_opened` exists.

**Output location.** `cases/<case-id>/01-readiness/`

**Typical DFIReballz tooling.** Orchestrator API (`/cases`, `/health`),
`make health`, MCP server `health` tools.

### Phase 2 — Identification

**Purpose.** Identify the digital evidence that is potentially relevant,
classify it, and assign stable IDs before anything is acquired.

**Entry criteria.**

- Readiness exit criteria met.

**Activities.**

- Enumerate evidence sources: physical drives, memory, network captures,
  cloud accounts, mobile devices, log archives.
- Document make, model, serial number, condition, and location for each
  physical item; photograph in situ before handling.
- Classify each source by volatility (RFC 3227 order: CPU/registers →
  routing tables / ARP / process tables → memory → temporary files → disk
  → remote logs → physical configuration). Volatile sources move first.
- Assign evidence identifiers using the case-scoped scheme
  `<case-number>-E<NNN>` (e.g. `DFIR-2026-001-E001`).
- Document the legal authority and scope limit for collecting each item.
- Record everything in the chain-of-custody log via the
  `evidence_identification` step in the chain-of-custody playbook.

**Exit criteria.**

- Every in-scope evidence item has an evidence record with: assigned ID,
  type, source description, acquisition order, authority reference,
  identifying photographs (where applicable).
- A chain-of-custody entry of action `identified` exists for each item.

**Output location.** `cases/<case-id>/02-identification/`

**Typical DFIReballz tooling.** Orchestrator evidence API, the
`chain-of-custody.md` playbook (`evidence_identification` step),
photographs ingested as evidence themselves.

### Phase 3 — Acquisition

**Purpose.** Collect identified evidence in a forensically sound manner that
preserves integrity and is reproducibly verifiable.

**Entry criteria.**

- Identification exit criteria met.
- Write-blocker (hardware or validated software) available where the
  evidence type requires one.

**Activities.**

- Engage write-blocker. Document make/model/firmware.
- Create a forensic image with simultaneous hashing — `dc3dd` is the
  primary tool. Use at least two algorithms (SHA-256 mandatory; MD5 or
  SHA-1 as the second to detect collision-class attacks against a single
  algorithm).
- Memory: capture before disk where the system is live (volatility order).
- Network: capture in PCAP-NG with full packet bytes where authorized.
- Store the image under `cases/<case-id>/03-acquisition/<evidence-id>/`.
- Record acquisition method, tool, tool version, write-blocker, examiner,
  start/end timestamps.
- Independently verify image hashes with a separate tool (`hashdeep`) and
  compare against acquisition hashes.
- Append chain-of-custody entries: `acquired`, `verified`.

**Exit criteria.**

- Every in-scope evidence item has an image (or equivalent acquisition
  artifact) plus a verified hash from an independent tool.
- `03-acquisition/acquisition-manifest.json` lists every artifact with:
  evidence ID, source description, image path, all hashes, tool/version,
  examiner, timestamps.
- A chain-of-custody entry of action `verified` exists for each item.
- No hash mismatch is unresolved. Any mismatch must be documented and the
  case status set to `integrity-issue` until resolved.

**Output location.** `cases/<case-id>/03-acquisition/`

**Typical DFIReballz tooling.** `kali-forensics/dc3dd`,
`kali-forensics/hashdeep`, `documentation/coc_generator`, the
`chain-of-custody.md` playbook (`acquisition_imaging`, `hash_verification`).

### Phase 4 — Examination

**Purpose.** Render acquired data into a form suitable for analysis and
extract items of potential relevance — *without altering the originals*.

**Entry criteria.**

- Acquisition exit criteria met (verified images exist, manifest written).

**Activities.**

- All work happens on copies (working images), never originals.
- Re-verify the source image hash before launching each major examination
  tool. Mismatch is a stop-the-world event.
- Parse, decode, decompress, decrypt where authorized.
- Extract artifacts: files, headers, metadata, registry hives, EVTX,
  MFT, prefetch, USN journal, browser history, memory processes, network
  flows, etc.
- Label each extracted artifact with the source-image SHA-256 and a
  reference to the acquisition manifest entry.
- Build search indexes where appropriate.

**Exit criteria.**

- `04-examination/extraction-manifest.json` lists every extracted
  artifact, tied back by hash to its source image.
- Pre- and post-examination hashes of every source image match (no
  mutation occurred).

**Output location.** `cases/<case-id>/04-examination/`

**Typical DFIReballz tooling.**

- `kali-forensics`: volatility3, sleuthkit, foremost, bulk_extractor,
  exiftool, yara
- `winforensics`: mft_parser, evtx_parser, registry_parser,
  prefetch_parser, shellbags_parser, amcache_parser, usn_journal_parser
- `binary-analysis`: radare2, ghidra (headless), capa, binwalk
- `network-forensics`: tshark (for PCAP examination)
- `filesystem`: scoped to `/cases`, `/evidence` (read-only), `/reports`,
  `/output`

### Phase 5 — Analysis

**Purpose.** Interpret examined artifacts to answer the investigative
questions; build timelines; correlate; draw evidence-supported conclusions
that distinguish fact from interpretation.

**Entry criteria.**

- Examination exit criteria met.

**Activities.**

- Timeline correlation across artifacts (filesystem, EVTX, network,
  memory, browser).
- IOC enrichment via `threat-intel` (VirusTotal, Shodan, AbuseIPDB,
  MalwareBazaar, ThreatFox, URLScan).
- OSINT pivots via `osint` (maigret, sherlock, holehe, theHarvester,
  dnstwist, subfinder).
- Hypothesis testing: each hypothesis paired with the artifacts that
  support or refute it.
- Cross-evidence correlation: when two artifacts from different sources
  agree, that's stronger than either alone — record the correlation.
- Every finding cites: evidence ID(s), examination artifact ID(s) with
  hashes, and tool-invocation audit IDs (the AI invocation log written
  by `dfireballz/audit/emitter.py`).

**Exit criteria.**

- `05-analysis/findings.json` lists every finding with: claim, supporting
  artifact references (with hashes), tool-invocation audit IDs, confidence
  qualifier, and `fact | interpretation` flag.
- Every active hypothesis is either supported or refuted with rationale.

**Output location.** `cases/<case-id>/05-analysis/`

**Typical DFIReballz tooling.** `threat-intel/*`, `osint/*`,
`network-forensics/tshark`, all examination tools used iteratively.

### Phase 6 — Reporting / Closure

**Purpose.** Produce the formal report, attach the supporting evidence,
finalize chain of custody, archive the case.

**Entry criteria.**

- Analysis exit criteria met.

**Activities.**

- Generate the formal report (Markdown, HTML, PDF) via the
  `dfireballz/reporting` pipeline. The report MUST include: executive
  summary, methodology, evidence list, findings with citations, IoC
  table, full chain-of-custody log, audit-log digest, timeline.
- Re-verify every source-image hash one last time and attach the result.
- Sign or seal the audit log: capture the SHA-256 of the JSONL audit
  trail and pin it into the report and into the chain-of-custody log.
- Append a chain-of-custody entry of action `case_closed`.
- Mark the case status closed in the orchestrator.

**Exit criteria.**

- Final report exists in `reports/<case-id>/` (per the existing reporting
  pipeline; see `dfireballz/reporting/CLAUDE.md`).
- `06-reporting/closure-manifest.json` records: report paths and hashes,
  audit-log SHA-256, final source-image hash verification result, case
  status, closing examiner, closing timestamp.
- All source-image hashes match the originals from acquisition.

**Output location.**

- `reports/<case-id>/` (formal deliverables — existing reporting layout)
- `cases/<case-id>/06-reporting/` (closure manifest and intermediate
  reporting artifacts)

**Typical DFIReballz tooling.** `dfireballz.reporting.md_generator`,
`html_generator`, `pdf_generator`, all consuming a `ForensicPayload`.

## Loopback policy

Real investigations sometimes require returning to an earlier phase
(analysis reveals a missed evidence source; examination uncovers a need
for re-acquisition; reporting catches a gap). Loopback is allowed and
expected — but it must be documented so the audit trail shows what
happened in what order.

Rules:

1. The decision to loop back is recorded as a chain-of-custody entry
   describing the source phase, the target phase, the reason, and the
   examiner approving it.
2. The new pass through the earlier phase writes into a revisioned
   subdirectory: `cases/<case-id>/0N-<phase>-rev2/`, then `-rev3/`, etc.
   The original `0N-<phase>/` is never overwritten.
3. After the loopback completes, every phase from the loopback target
   forward is re-evaluated. If only the analysis is updated, the loopback
   is logged but downstream phases need not re-run; if examination
   changes, downstream analysis must be re-derived from the new
   examination output.
4. The final report's methodology section enumerates every loopback.

Strict mode — the orchestrator refusing out-of-order or undocumented
loopbacks — is a planned follow-up slice. Until then this policy is
enforced by review of the chain-of-custody log against the on-disk phase
directories.

## Case directory layout (canonical)

```
cases/
└── <case-number>/
    ├── 01-readiness/
    │   └── case-precondition.json
    ├── 02-identification/
    │   └── evidence-records/
    ├── 03-acquisition/
    │   ├── acquisition-manifest.json
    │   └── <evidence-id>/
    │       ├── <evidence-id>.dd
    │       ├── <evidence-id>_acquisition.log
    │       └── <evidence-id>_verification.log
    ├── 04-examination/
    │   ├── extraction-manifest.json
    │   └── <evidence-id>/
    ├── 05-analysis/
    │   ├── findings.json
    │   └── timelines/
    └── 06-reporting/
        └── closure-manifest.json
```

The existing `notes/`, `artifacts/`, `timelines/` subdirectories that
appear in older prompt templates remain valid for ad-hoc working files,
but new work should follow the phase layout above. See
[`cases/README.md`](../cases/README.md) for the layout contract.

## How playbooks express phase

Playbook YAML front matter accepts an optional `phase` field per step,
naming the phase that step belongs to. Values:
`readiness | identification | acquisition | examination | analysis | reporting`.

Playbooks SHOULD organize their steps in phase order. Playbooks MAY span
multiple phases (most do). The runner currently does not enforce phase
ordering — see `orchestrator/playbook_runner.py` — but the phase tag is
preserved through the chain-of-custody log so every action can be traced
back to its phase.

See [`playbooks/phishing-investigation.md`](../playbooks/phishing-investigation.md)
for the worked reference playbook organized by phase.

## What this document is *not*

- It is not a copy of any ISO/IEC, NIST, ASTM, SWGDE, or ACPO text.
- It is not a substitute for reading those standards. Practitioners on a
  legally significant matter should consult the source documents directly.
- It is not a compliance certificate. Following the phase model improves
  defensibility but does not by itself certify compliance with any
  particular standard.
- It is not a final design. Strict phase gating, the AI-governance layer
  (eventual ASTM WK96121 mapping), and per-playbook phase enforcement are
  follow-up slices, called out in the rollout plan.

## Rollout plan

This document and the phase-tagged phishing playbook are slice 1.

Planned follow-ups (not in this slice):

- Slice 2 — phase-tag the remaining playbooks and prompt templates.
- Slice 3 — strict phase gating in the orchestrator's `playbook_runner`,
  including loopback enforcement and revisioned subdirectories.
- Slice 4 — automatic pre-flight (Readiness) and post-flight (Closure)
  steps emitted by the orchestrator on case open / case close.
- Slice 5 — AI governance layer: model/prompt provenance pinned to each
  case, mapped onto ASTM WK96121's published categories once it ballots.
