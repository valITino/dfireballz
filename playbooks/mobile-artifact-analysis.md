---
name: Mobile Artifact Analysis
id: pb-mobile-artifact-analysis
description: >
  Mobile forensics playbook for extracting and analyzing artifacts from
  mobile device images. Covers SQLite database extraction, location
  history reconstruction, application usage analysis, contacts and
  call log extraction, and timeline correlation. Supports both Android
  and iOS artifact structures.
case_types:
  - mobile-forensics
  - digital-forensics
  - incident-response
  - insider-threat
tools_required:
  - mobile-forensics/sqlite_extractor
  - mobile-forensics/location_analyzer
  - mobile-forensics/app_analyzer
  - mobile-forensics/contact_extractor
  - mobile-forensics/call_log_extractor
estimated_duration: 60-120 minutes
tags:
  - mobile-forensics
  - sqlite
  - location-data
  - app-analysis
  - contacts
  - call-logs
  - android
  - ios
steps:
  - id: sqlite_extraction
    name: SQLite Database Extraction
    tool: mobile-forensics/sqlite_extractor
    action: extract_databases
    description: >
      Locate and extract all SQLite databases from the mobile device
      image. Identify key databases including contacts, call logs,
      SMS/MMS, browser history, application data, and system logs.
      Recover deleted records using WAL and journal file analysis.
      Validate database integrity before proceeding with analysis.
    inputs:
      image_path: "{{evidence.mobile_image_path}}"
      platform: "{{evidence.platform}}"
      extract_paths:
        android:
          - "/data/data/*/databases/*.db"
          - "/data/data/com.android.providers.contacts/databases/contacts2.db"
          - "/data/data/com.android.providers.telephony/databases/mmssms.db"
          - "/data/data/com.android.providers.calendar/databases/calendar.db"
          - "/data/user/0/*/databases/*.db"
        ios:
          - "/private/var/mobile/Library/AddressBook/AddressBook.sqlitedb"
          - "/private/var/mobile/Library/SMS/sms.db"
          - "/private/var/mobile/Library/Calendar/Calendar.sqlitedb"
          - "/private/var/mobile/Library/Safari/History.db"
          - "/private/var/mobile/Containers/Data/Application/*/Documents/*.sqlite"
      recover_deleted: true
      analyze_wal: true
      analyze_journal: true
      output_dir: "{{case.working_dir}}/sqlite_databases"
      output_format: json

  - id: location_history
    name: Location History Reconstruction
    tool: mobile-forensics/location_analyzer
    action: extract_locations
    description: >
      Extract and reconstruct location history from all available
      sources including GPS logs, cell tower records, Wi-Fi connection
      history, and application-specific location data (maps, photos,
      check-ins). Generate a chronological location timeline with
      coordinate plotting and address resolution.
    inputs:
      image_path: "{{evidence.mobile_image_path}}"
      platform: "{{evidence.platform}}"
      sources:
        android:
          - google_location_history
          - cell_tower_logs
          - wifi_connections
          - photo_exif
          - google_maps_history
        ios:
          - significant_locations
          - routined
          - cell_tower_cache
          - wifi_locations
          - photo_exif
          - apple_maps_history
      databases: "{{steps.sqlite_extraction.outputs.location_databases}}"
      time_range:
        start: "{{case.time_range_start}}"
        end: "{{case.time_range_end}}"
      resolve_addresses: true
      generate_kml: true
      generate_timeline: true
      output_dir: "{{case.working_dir}}/location_history"
      output_format: json

  - id: app_usage
    name: Application Usage Analysis
    tool: mobile-forensics/app_analyzer
    action: analyze_apps
    description: >
      Analyze installed application data including usage statistics,
      notification history, cached content, and application-specific
      databases. Focus on messaging apps (WhatsApp, Signal, Telegram),
      social media, email clients, cloud storage, and financial apps.
      Extract messages, media, and metadata from each application.
    inputs:
      image_path: "{{evidence.mobile_image_path}}"
      platform: "{{evidence.platform}}"
      databases: "{{steps.sqlite_extraction.outputs.app_databases}}"
      target_apps:
        messaging:
          - com.whatsapp
          - org.thoughtcrime.securesms
          - org.telegram.messenger
          - com.facebook.orca
          - com.Slack
        social:
          - com.instagram.android
          - com.twitter.android
          - com.facebook.katana
          - com.snapchat.android
        email:
          - com.google.android.gm
          - com.microsoft.office.outlook
        cloud:
          - com.google.android.apps.docs
          - com.dropbox.android
          - com.microsoft.skydrive
        browser:
          - com.android.chrome
          - com.apple.mobilesafari
          - org.mozilla.firefox
      extract:
        - messages
        - media_metadata
        - contacts
        - usage_stats
        - notifications
        - cached_content
      output_dir: "{{case.working_dir}}/app_analysis"
      output_format: json

  - id: contacts_extraction
    name: Contacts Extraction
    tool: mobile-forensics/contact_extractor
    action: extract_contacts
    description: >
      Extract all contacts from the device including phone contacts,
      SIM card contacts, application-specific contacts, and recently
      communicated contacts. Capture full contact records with names,
      phone numbers, email addresses, organizations, and associated
      social media accounts. Identify deleted contacts through
      database recovery.
    inputs:
      image_path: "{{evidence.mobile_image_path}}"
      platform: "{{evidence.platform}}"
      databases: "{{steps.sqlite_extraction.outputs.contact_databases}}"
      sources:
        - device_contacts
        - sim_contacts
        - app_contacts
        - recent_contacts
        - favorites
      include_deleted: true
      extract_fields:
        - display_name
        - phone_numbers
        - email_addresses
        - organization
        - addresses
        - social_profiles
        - notes
        - photo
        - last_contacted
        - contact_frequency
      output_format: json
      output_dir: "{{case.working_dir}}/contacts"

  - id: call_logs
    name: Call Log Extraction
    tool: mobile-forensics/call_log_extractor
    action: extract_call_logs
    description: >
      Extract complete call log records including incoming, outgoing,
      missed, and rejected calls. Capture timestamps, durations,
      contact associations, and geographic metadata. Analyze call
      patterns, frequent contacts, and timeline. Include VoIP calls
      from messaging applications where available.
    inputs:
      image_path: "{{evidence.mobile_image_path}}"
      platform: "{{evidence.platform}}"
      databases: "{{steps.sqlite_extraction.outputs.call_databases}}"
      call_types:
        - incoming
        - outgoing
        - missed
        - rejected
        - blocked
        - voip
      extract_fields:
        - timestamp
        - duration
        - phone_number
        - contact_name
        - call_type
        - carrier
        - location
      time_range:
        start: "{{case.time_range_start}}"
        end: "{{case.time_range_end}}"
      include_deleted: true
      analyze_patterns: true
      output_format: json
      output_dir: "{{case.working_dir}}/call_logs"
---

# Mobile Artifact Analysis Playbook

## Overview

This playbook provides a structured approach to extracting and analyzing forensic artifacts from mobile device images. It covers the key artifact categories relevant to most mobile forensics investigations, supporting both Android and iOS platforms.

## Prerequisites

- Forensic image of the mobile device (physical or logical extraction)
- Platform identification (Android version or iOS version)
- SQLite browser or forensic analysis tool
- Sufficient disk space for extracted databases and media
- GeoIP database for location resolution
- Legal authorization to examine device contents

## Workflow

1. **SQLite Extraction** -- Locate and extract all databases with deleted record recovery
2. **Location History** -- Reconstruct movement timeline from GPS, cell, and Wi-Fi data
3. **Application Usage** -- Analyze messaging, social media, and application data
4. **Contacts Extraction** -- Extract contacts from all sources including deleted entries
5. **Call Log Extraction** -- Recover call records and analyze communication patterns

## Decision Points

- If encryption is encountered on app databases, check for key material in shared preferences or keychain.
- If significant location gaps exist, cross-reference with cell tower and Wi-Fi data.
- If messaging app databases are encrypted (Signal, WhatsApp), attempt key extraction or use specialized decryption tools.
- If deleted records are recovered, document recovery method for evidentiary defensibility.

## Platform-Specific Notes

### Android
- Check `/data/data/` and `/data/user/0/` for application databases.
- Google account synchronization may contain additional data in cloud.
- Samsung, Huawei, and other OEM-specific databases may contain unique artifacts.

### iOS
- Check `/private/var/mobile/` hierarchy for system and app databases.
- KnowledgeC database (`knowledgeC.db`) contains rich usage and context data.
- Health database may contain location and activity data.
- Keychain extraction may be needed for encrypted app databases.

## Output Artifacts

- SQLite database inventory with integrity status
- Location history timeline with KML map export
- Application usage analysis report
- Complete contacts list with metadata
- Call log records with pattern analysis
- Consolidated investigation timeline
