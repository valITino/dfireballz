---
name: Chain of Custody Documentation
id: pb-chain-of-custody
description: >
  Chain of custody documentation template and protocol playbook for
  digital forensics evidence handling. Covers evidence identification,
  acquisition methods, cryptographic hash verification, labeling
  standards, transfer documentation, and storage requirements.
  Ensures evidentiary integrity and legal admissibility.
case_types:
  - all
  - digital-forensics
  - incident-response
  - legal-hold
tools_required:
  - kali-forensics/dc3dd
  - kali-forensics/hashdeep
  - documentation/coc_generator
estimated_duration: 15-30 minutes per evidence item
tags:
  - chain-of-custody
  - evidence-handling
  - legal
  - documentation
  - hash-verification
  - acquisition
steps:
  - id: evidence_identification
    name: Evidence Identification and Logging
    tool: documentation/coc_generator
    action: create_evidence_record
    description: >
      Create a formal evidence record for each item being collected.
      Document the evidence type, physical description, serial numbers,
      make/model, condition, location found, and circumstances of
      collection. Assign a unique evidence identifier following the
      organizational naming convention. Photograph the item in situ
      before handling.
    inputs:
      case_id: "{{case.id}}"
      evidence_fields:
        evidence_id: "{{evidence.assigned_id}}"
        type: "{{evidence.type}}"
        description: "{{evidence.description}}"
        make: "{{evidence.make}}"
        model: "{{evidence.model}}"
        serial_number: "{{evidence.serial_number}}"
        capacity: "{{evidence.capacity}}"
        condition: "{{evidence.condition}}"
        location_found: "{{evidence.location_found}}"
        collected_by: "{{analyst.name}}"
        collection_datetime: "{{timestamp.now}}"
        witness: "{{evidence.witness_name}}"
        photographs: "{{evidence.photo_paths}}"
        notes: "{{evidence.collection_notes}}"
      output_format: json

  - id: acquisition_imaging
    name: Forensic Acquisition
    tool: kali-forensics/dc3dd_hash
    action: forensic_image
    description: >
      Perform a forensic acquisition of the evidence using a validated
      write-blocked connection. Create a bit-for-bit image using dc3dd
      with simultaneous hash computation. Document the acquisition
      method, tool version, write-blocker used, start and end times,
      and any errors encountered. Verify that source and destination
      hashes match.
    inputs:
      source: "{{evidence.device_path}}"
      destination: "{{case.evidence_store}}/{{evidence.assigned_id}}.dd"
      hash_algorithms:
        - md5
        - sha256
      log_file: "{{case.evidence_store}}/{{evidence.assigned_id}}_acquisition.log"
      write_blocker: "{{evidence.write_blocker_id}}"
      split_size: 0
      verify: true
      acquisition_metadata:
        tool: dc3dd
        tool_version: "{{tool.dc3dd.version}}"
        write_blocker_make: "{{evidence.write_blocker_make}}"
        write_blocker_model: "{{evidence.write_blocker_model}}"
        examiner: "{{analyst.name}}"
        start_time: "{{timestamp.now}}"

  - id: hash_verification
    name: Hash Verification
    tool: kali-forensics/hashdeep
    action: verify_hashes
    description: >
      Independently verify the integrity of the forensic image by
      computing hashes with a separate tool (hashdeep) and comparing
      against the acquisition hashes. Document both sets of hashes,
      the verification tool and version, and the verification result.
      Any mismatch must be immediately documented and escalated.
    inputs:
      target: "{{case.evidence_store}}/{{evidence.assigned_id}}.dd"
      algorithms:
        - md5
        - sha256
      expected_hashes:
        md5: "{{steps.acquisition_imaging.outputs.source_md5}}"
        sha256: "{{steps.acquisition_imaging.outputs.source_sha256}}"
      verification_tool: hashdeep
      log_file: "{{case.evidence_store}}/{{evidence.assigned_id}}_verification.log"
      examiner: "{{analyst.name}}"
      verification_time: "{{timestamp.now}}"

  - id: evidence_labeling
    name: Evidence Labeling
    tool: documentation/coc_generator
    action: generate_label
    description: >
      Generate and apply a standardized evidence label containing the
      case number, evidence ID, item description, acquisition date,
      hash values, examiner name, and classification level. Labels
      must be tamper-evident and attached to both the original evidence
      and all forensic copies. Generate a digital label record for the
      case management system.
    inputs:
      case_id: "{{case.id}}"
      evidence_id: "{{evidence.assigned_id}}"
      label_fields:
        case_number: "{{case.number}}"
        evidence_number: "{{evidence.assigned_id}}"
        description: "{{evidence.description}}"
        date_acquired: "{{steps.acquisition_imaging.outputs.start_time}}"
        acquired_by: "{{analyst.name}}"
        md5: "{{steps.hash_verification.outputs.verified_md5}}"
        sha256: "{{steps.hash_verification.outputs.verified_sha256}}"
        classification: "{{case.classification}}"
        handling_instructions: "{{evidence.handling_instructions}}"
      label_format: printable
      copies: 2
      output_dir: "{{case.evidence_store}}/labels"

  - id: transfer_documentation
    name: Transfer Documentation
    tool: documentation/coc_generator
    action: log_transfer
    description: >
      Document every transfer of custody for the evidence item.
      Record the releasing party, receiving party, date and time,
      purpose of transfer, condition at transfer, and both parties'
      signatures. Each transfer creates a new entry in the chain of
      custody log. Verify evidence integrity (hash check) at each
      transfer point.
    inputs:
      case_id: "{{case.id}}"
      evidence_id: "{{evidence.assigned_id}}"
      transfer_record:
        released_by:
          name: "{{transfer.released_by_name}}"
          title: "{{transfer.released_by_title}}"
          organization: "{{transfer.released_by_org}}"
          signature: "{{transfer.released_by_sig}}"
        received_by:
          name: "{{transfer.received_by_name}}"
          title: "{{transfer.received_by_title}}"
          organization: "{{transfer.received_by_org}}"
          signature: "{{transfer.received_by_sig}}"
        datetime: "{{timestamp.now}}"
        purpose: "{{transfer.purpose}}"
        condition: "{{transfer.condition_at_transfer}}"
        integrity_verified: "{{transfer.hash_verified}}"
        location_from: "{{transfer.location_from}}"
        location_to: "{{transfer.location_to}}"
        transport_method: "{{transfer.transport_method}}"
      output_format: json

  - id: storage_documentation
    name: Storage Documentation
    tool: documentation/coc_generator
    action: log_storage
    description: >
      Document the storage location, conditions, and access controls
      for the evidence item. Record the storage facility, room, safe
      or locker identifier, access control mechanism, environmental
      controls, and authorized personnel. Digital evidence storage
      must include encryption status, access logging, and backup
      verification.
    inputs:
      case_id: "{{case.id}}"
      evidence_id: "{{evidence.assigned_id}}"
      storage_record:
        facility: "{{storage.facility_name}}"
        room: "{{storage.room_id}}"
        container: "{{storage.container_id}}"
        access_control: "{{storage.access_method}}"
        environmental_controls:
          temperature: "{{storage.temperature_range}}"
          humidity: "{{storage.humidity_range}}"
          fire_suppression: "{{storage.fire_suppression}}"
        authorized_personnel: "{{storage.authorized_list}}"
        digital_storage:
          encrypted: true
          encryption_method: "{{storage.encryption_method}}"
          access_logged: true
          backup_location: "{{storage.backup_path}}"
          backup_verified: "{{storage.backup_hash_verified}}"
        stored_by: "{{analyst.name}}"
        stored_datetime: "{{timestamp.now}}"
      output_format: json
---

# Chain of Custody Documentation Playbook

## Overview

This playbook establishes the standard protocol for chain of custody documentation in digital forensics investigations. It ensures that all evidence is properly identified, acquired, verified, labeled, and tracked throughout its lifecycle to maintain evidentiary integrity and legal admissibility.

## Prerequisites

- Evidence collection authorization (warrant, consent, or organizational policy)
- Write-blocking hardware or validated software write-blocker
- Forensic acquisition tools (dc3dd, FTK Imager, or equivalent)
- Hash verification tools (hashdeep, md5sum, sha256sum)
- Evidence labels and tamper-evident bags/seals
- Case management system access
- Secure evidence storage facility

## Workflow

1. **Evidence Identification** -- Document and photograph evidence before handling
2. **Forensic Acquisition** -- Create verified forensic image with hash computation
3. **Hash Verification** -- Independently verify image integrity
4. **Evidence Labeling** -- Apply standardized tamper-evident labels
5. **Transfer Documentation** -- Log every custody transfer with signatures
6. **Storage Documentation** -- Record storage location and access controls

## Labeling Standards

Evidence labels must include:
- Case number and evidence item number
- Brief item description
- Date and time of acquisition
- Acquiring examiner name and badge/ID number
- MD5 and SHA256 hash values
- Classification/sensitivity level
- Handling instructions

## Acquisition Methods

| Method | Use Case | Tool |
|--------|----------|------|
| Physical image | Full disk, including unallocated space | dc3dd, FTK Imager |
| Logical image | File-level copy, mounted volumes | robocopy, rsync |
| Memory capture | Volatile data, running processes | WinPmem, LiME |
| Network capture | Traffic analysis | tcpdump, Wireshark |
| Cloud acquisition | Cloud storage, SaaS data | Platform-specific APIs |

## Legal Considerations

- Verify legal authority before collecting any evidence.
- Document the legal basis for collection on the evidence record.
- Maintain continuous chain of custody without gaps.
- Any break in the chain must be documented with explanation.
- Original evidence must remain in a secured, access-controlled location.
- Working copies should be used for all analysis activities.

## Integrity Requirements

- Compute hashes at acquisition, at every transfer, and before analysis.
- Use at least two hash algorithms (MD5 + SHA256 recommended).
- Any hash mismatch is a critical event requiring immediate documentation.
- All hash computations must be logged with tool name, version, and timestamp.

## Output Artifacts

- Evidence identification record with photographs
- Forensic acquisition log with source/destination hashes
- Independent hash verification report
- Printed evidence labels
- Chain of custody transfer log
- Storage location record
