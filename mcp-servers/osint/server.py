"""OSINT MCP Server — Aggregates Maigret, Sherlock, Holehe, theHarvester, and more."""

import subprocess

from fastmcp import FastMCP

mcp = FastMCP(
    "osint",
    description=(
        "OSINT: Maigret, Sherlock, Holehe, SpiderFoot, "
        "theHarvester, DNSTwist, h8mail, subfinder"
    ),
)


def _run(args: list[str], timeout: int = 300) -> dict:
    """Run a subprocess safely."""
    try:
        result = subprocess.run(
            args, capture_output=True, text=True, timeout=timeout, shell=False
        )
        return {
            "stdout": result.stdout,
            "stderr": result.stderr,
            "returncode": result.returncode,
        }
    except subprocess.TimeoutExpired:
        return {"error": f"Command timed out after {timeout}s", "returncode": -1}
    except FileNotFoundError:
        return {"error": f"Command not found: {args[0]}", "returncode": -1}


@mcp.tool()
def username_search(
    username: str,
    platforms: str | None = None,
    output_format: str = "text",
) -> dict:
    """Search for a username across 500+ platforms using Maigret and Sherlock.

    Args:
        username: Username to search for
        platforms: Comma-separated platform list (optional, default: all)
        output_format: Output format (text, json)
    """
    results = {}

    # Maigret search
    maigret_cmd = ["maigret", username, "--timeout", "15"]
    if output_format == "json":
        maigret_cmd.append("--json")
    results["maigret"] = _run(maigret_cmd, timeout=120)

    # Sherlock search
    sherlock_cmd = ["sherlock", username, "--timeout", "15"]
    results["sherlock"] = _run(sherlock_cmd, timeout=120)

    return results


@mcp.tool()
def email_check(email: str) -> dict:
    """Check email registration across platforms (Holehe) and breach databases (h8mail).

    Args:
        email: Email address to check
    """
    results = {}

    # Holehe check
    results["holehe"] = _run(["holehe", email], timeout=60)

    # h8mail breach check
    results["h8mail"] = _run(["h8mail", "-t", email], timeout=60)

    return results


@mcp.tool()
def harvester_scan(domain: str, sources: str = "all", limit: int = 500) -> dict:
    """Run theHarvester to find emails, subdomains, hosts, and employee names.

    Args:
        domain: Target domain
        sources: Data sources (all, google, bing, linkedin, etc.)
        limit: Maximum results to return
    """
    cmd = ["theHarvester", "-d", domain, "-b", sources, "-l", str(limit)]
    return _run(cmd, timeout=300)


@mcp.tool()
def subdomain_enum(domain: str) -> dict:
    """Enumerate subdomains using subfinder and amass.

    Args:
        domain: Target domain
    """
    results = {}

    # subfinder
    results["subfinder"] = _run(["subfinder", "-d", domain, "-silent"], timeout=120)

    # amass passive
    results["amass"] = _run(
        ["amass", "enum", "-passive", "-d", domain], timeout=300
    )

    return results


@mcp.tool()
def dns_twist(domain: str) -> dict:
    """Detect typosquatting and phishing domains using dnstwist.

    Args:
        domain: Target domain to check for lookalikes
    """
    return _run(["dnstwist", "--format", "json", domain], timeout=120)


@mcp.tool()
def whois_lookup(target: str) -> dict:
    """Perform WHOIS lookup on a domain or IP.

    Args:
        target: Domain name or IP address
    """
    return _run(["whois", target], timeout=30)


@mcp.tool()
def web_fingerprint(url: str) -> dict:
    """Fingerprint web technologies using whatweb.

    Args:
        url: Target URL
    """
    return _run(["whatweb", "--color=never", url], timeout=60)


@mcp.tool()
def passive_dns(ip_or_domain: str) -> dict:
    """Query passive DNS records for an IP or domain.

    Args:
        ip_or_domain: IP address or domain name
    """
    results = {}
    # DNS lookups
    results["dig"] = _run(["dig", "+short", ip_or_domain], timeout=15)
    results["dig_any"] = _run(["dig", "ANY", "+short", ip_or_domain], timeout=15)
    # Reverse DNS if IP address
    parts = ip_or_domain.split(".")
    if len(parts) == 4 and all(p.isdigit() and 0 <= int(p) <= 255 for p in parts):
        results["reverse"] = _run(["dig", "+short", "-x", ip_or_domain], timeout=15)
    return results


if __name__ == "__main__":
    mcp.run(transport="stdio")
