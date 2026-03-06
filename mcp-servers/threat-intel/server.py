"""Threat Intelligence MCP Server — VirusTotal, Shodan, AbuseIPDB, MalwareBazaar, ThreatFox, URLScan."""

import os

import requests
from fastmcp import FastMCP

mcp = FastMCP(
    "threat-intel",
    description="Threat intel: VirusTotal, Shodan, AbuseIPDB, MalwareBazaar, ThreatFox, URLScan",
)


def _get_key(service: str) -> str:
    """Get API key from environment."""
    key = os.environ.get(f"{service.upper()}_API_KEY", "")
    if not key:
        raise ValueError(f"{service} API key not configured. Set {service.upper()}_API_KEY environment variable.")
    return key


@mcp.tool()
def vt_lookup(indicator: str, type: str = "file_hash") -> dict:
    """Look up an indicator on VirusTotal.

    Args:
        indicator: The indicator value (hash, URL, domain, or IP)
        type: Indicator type — file_hash | url | domain | ip
    """
    api_key = _get_key("virustotal")
    base = "https://www.virustotal.com/api/v3"
    headers = {"x-apikey": api_key}

    endpoints = {
        "file_hash": f"{base}/files/{indicator}",
        "url": f"{base}/urls/{indicator}",
        "domain": f"{base}/domains/{indicator}",
        "ip": f"{base}/ip_addresses/{indicator}",
    }

    if type not in endpoints:
        return {"error": f"Invalid type. Must be one of: {list(endpoints.keys())}"}

    try:
        resp = requests.get(endpoints[type], headers=headers, timeout=30)
        return resp.json()
    except requests.RequestException as e:
        return {"error": str(e)}


@mcp.tool()
def shodan_host(ip: str) -> dict:
    """Get Shodan host information for an IP address.

    Args:
        ip: IP address to look up
    """
    api_key = _get_key("shodan")
    try:
        resp = requests.get(
            f"https://api.shodan.io/shodan/host/{ip}",
            params={"key": api_key},
            timeout=30,
        )
        return resp.json()
    except requests.RequestException as e:
        return {"error": str(e)}


@mcp.tool()
def shodan_search(query: str, page: int = 1) -> dict:
    """Search Shodan with a query string.

    Args:
        query: Shodan search query (dork)
        page: Result page number
    """
    api_key = _get_key("shodan")
    try:
        resp = requests.get(
            "https://api.shodan.io/shodan/host/search",
            params={"key": api_key, "query": query, "page": page},
            timeout=30,
        )
        return resp.json()
    except requests.RequestException as e:
        return {"error": str(e)}


@mcp.tool()
def abuse_ip_check(ip: str) -> dict:
    """Check IP reputation on AbuseIPDB.

    Args:
        ip: IP address to check
    """
    api_key = _get_key("abuseipdb")
    try:
        resp = requests.get(
            "https://api.abuseipdb.com/api/v2/check",
            headers={"Key": api_key, "Accept": "application/json"},
            params={"ipAddress": ip, "maxAgeInDays": 90, "verbose": True},
            timeout=30,
        )
        return resp.json()
    except requests.RequestException as e:
        return {"error": str(e)}


@mcp.tool()
def malware_bazaar_lookup(hash_or_tag: str) -> dict:
    """Search MalwareBazaar for a sample by hash or tag.

    Args:
        hash_or_tag: SHA256/MD5/SHA1 hash or malware tag
    """
    try:
        # Try hash lookup first
        resp = requests.post(
            "https://mb-api.abuse.ch/api/v1/",
            data={"query": "get_info", "hash": hash_or_tag},
            timeout=30,
        )
        result = resp.json()
        if result.get("query_status") == "hash_not_found":
            # Try tag search
            resp = requests.post(
                "https://mb-api.abuse.ch/api/v1/",
                data={"query": "get_taginfo", "tag": hash_or_tag, "limit": 25},
                timeout=30,
            )
            result = resp.json()
        return result
    except requests.RequestException as e:
        return {"error": str(e)}


@mcp.tool()
def threatfox_lookup(ioc: str) -> dict:
    """Search ThreatFox IOC database.

    Args:
        ioc: IOC to search (IP, domain, URL, hash)
    """
    try:
        resp = requests.post(
            "https://threatfox-api.abuse.ch/api/v1/",
            json={"query": "search_ioc", "search_term": ioc},
            timeout=30,
        )
        return resp.json()
    except requests.RequestException as e:
        return {"error": str(e)}


@mcp.tool()
def urlscan_lookup(url: str) -> dict:
    """Submit a URL to URLScan.io for analysis.

    Args:
        url: URL to analyze
    """
    api_key = _get_key("urlscan")
    try:
        resp = requests.post(
            "https://urlscan.io/api/v1/scan/",
            headers={"API-Key": api_key, "Content-Type": "application/json"},
            json={"url": url, "visibility": "private"},
            timeout=30,
        )
        return resp.json()
    except requests.RequestException as e:
        return {"error": str(e)}


@mcp.tool()
def cve_lookup(cve_id: str) -> dict:
    """Look up CVE details from NVD.

    Args:
        cve_id: CVE identifier (e.g., CVE-2024-1234)
    """
    try:
        resp = requests.get(
            "https://services.nvd.nist.gov/rest/json/cves/2.0",
            params={"cveId": cve_id},
            timeout=30,
        )
        return resp.json()
    except requests.RequestException as e:
        return {"error": str(e)}


@mcp.tool()
def enrich_ioc(ioc: str, type: str = "auto") -> dict:
    """Enrich an IOC by querying all relevant threat intelligence sources.

    Args:
        ioc: The indicator of compromise value
        type: IOC type — auto | ip | domain | url | file_hash | email
    """
    results = {"ioc": ioc, "type": type, "sources": {}}

    # Auto-detect type
    if type == "auto":
        if ioc.count(".") == 3 and all(p.isdigit() for p in ioc.split(".")):
            type = "ip"
        elif ioc.startswith("http"):
            type = "url"
        elif len(ioc) in (32, 40, 64) and all(c in "0123456789abcdefABCDEF" for c in ioc):
            type = "file_hash"
        elif "@" in ioc:
            type = "email"
        else:
            type = "domain"
        results["type"] = type

    try:
        if type == "ip":
            try:
                results["sources"]["shodan"] = shodan_host(ioc)
            except Exception:
                pass
            try:
                results["sources"]["abuseipdb"] = abuse_ip_check(ioc)
            except Exception:
                pass
            try:
                results["sources"]["virustotal"] = vt_lookup(ioc, "ip")
            except Exception:
                pass
            try:
                results["sources"]["threatfox"] = threatfox_lookup(ioc)
            except Exception:
                pass

        elif type == "domain":
            try:
                results["sources"]["virustotal"] = vt_lookup(ioc, "domain")
            except Exception:
                pass
            try:
                results["sources"]["threatfox"] = threatfox_lookup(ioc)
            except Exception:
                pass

        elif type == "file_hash":
            try:
                results["sources"]["virustotal"] = vt_lookup(ioc, "file_hash")
            except Exception:
                pass
            try:
                results["sources"]["malware_bazaar"] = malware_bazaar_lookup(ioc)
            except Exception:
                pass
            try:
                results["sources"]["threatfox"] = threatfox_lookup(ioc)
            except Exception:
                pass

        elif type == "url":
            try:
                results["sources"]["virustotal"] = vt_lookup(ioc, "url")
            except Exception:
                pass
            try:
                results["sources"]["urlscan"] = urlscan_lookup(ioc)
            except Exception:
                pass

    except Exception as e:
        results["error"] = str(e)

    # Compute confidence score based on number of positive results
    positive_sources = sum(
        1 for v in results["sources"].values()
        if isinstance(v, dict) and "error" not in v
    )
    total_sources = len(results["sources"])
    results["confidence"] = int((positive_sources / max(total_sources, 1)) * 100)

    return results


if __name__ == "__main__":
    mcp.run(transport="stdio")
