# Phishing Investigation

Analyze a phishing incident targeting [TARGET].

## Phase 1: Email Analysis
1. Log chain of custody for the phishing email
2. Parse email headers (SPF, DKIM, DMARC results)
3. Identify true sender (X-Originating-IP, Received headers)
4. Extract URLs, attachments, and embedded content

## Phase 2: URL/Domain Investigation
1. Check suspicious URLs on URLScan
2. DNSTwist for typosquatting detection
3. theHarvester for related infrastructure
4. WHOIS lookup on sender and phishing domains
5. Shodan for hosting infrastructure analysis

## Phase 3: Attachment Analysis
1. Hash all attachments (SHA256, MD5)
2. VirusTotal lookup for known malware
3. ExifTool for document metadata
4. YARA scan for malicious macros/scripts
5. If executable: Capa + Radare2 analysis

## Phase 4: Credential Harvesting Check
1. Screenshot the phishing page for evidence
2. Identify credential harvesting form fields
3. Check if credentials were submitted (browser artifacts)
4. Determine scope of compromised accounts

## Phase 5: Threat Intelligence
1. Cross-reference IoCs with ThreatFox
2. Check sender IP on AbuseIPDB
3. MalwareBazaar for attachment hashes
4. Identify related phishing campaigns

## Phase 6: Reporting
1. Include email artifacts with header analysis
2. Document attack chain from delivery to potential impact
3. Provide user awareness recommendations
4. Generate report

## MCP Containers to Use
- osint (theHarvester, DNSTwist, subfinder)
- threat-intel (VirusTotal, URLScan, AbuseIPDB, ThreatFox)
- kali-forensics (ExifTool, YARA)
- binary-analysis (Capa, Radare2 — for attachments)
