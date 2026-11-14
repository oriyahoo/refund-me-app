#!/usr/bin/env python3
"""
Turns OSV-Scanner JSON reports into one Markdown summary: known vulnerabilities (CVE / GHSA /
Debian advisories) in what the app is built from, what fixes each one, and whether it ships.

Used by .github/workflows/image-scan.yml (the run's summary page).

    osv-summary.py "Section title=report.json" ["Another section=other.json" ...]

A section whose file is missing or empty says its scan didn't run, so a broken scan never reads
as "no vulnerabilities". The exit code is always 0: this is a report, not a gate.
"""
import json
import sys
from pathlib import Path

RANK = {"critical": 0, "high": 1, "medium": 2, "moderate": 2, "low": 3, "": 4}


def level(score: str) -> str:
    """OSV gives a CVSS base score (e.g. "7.5"), sometimes nothing: named the way advisories are."""
    try:
        s = float(score)
    except (TypeError, ValueError):
        return ""
    return "critical" if s >= 9 else "high" if s >= 7 else "medium" if s >= 4 else "low" if s > 0 else ""


def fixed_versions(vuln: dict, name: str, ecosystem: str) -> list[str]:
    out: set[str] = set()
    for affected in vuln.get("affected", []):
        pkg = affected.get("package", {})
        if pkg.get("name") != name or not str(pkg.get("ecosystem", "")).split(":")[0] == ecosystem.split(":")[0]:
            continue
        for rng in affected.get("ranges", []):
            for event in rng.get("events", []):
                if "fixed" in event:
                    out.add(event["fixed"])
    return sorted(out)


def rows_of(report: dict) -> list[dict]:
    rows = []
    for result in report.get("results", []):
        for entry in result.get("packages", []):
            pkg = entry.get("package", {})
            name, version, eco = pkg.get("name", "?"), pkg.get("version", "?"), pkg.get("ecosystem", "")
            groups = entry.get("groups", [])
            dev = "dev" in (entry.get("dependency_groups") or [])
            by_id = {v["id"]: v for v in entry.get("vulnerabilities", [])}
            for group in groups or [{"ids": [i]} for i in by_id]:
                ids = group.get("ids", [])
                main = next((by_id[i] for i in ids if i in by_id), None)
                if not main:
                    continue
                aliases = sorted({a for i in ids for a in [i, *by_id.get(i, {}).get("aliases", [])]})
                cves = [a for a in aliases if a.startswith("CVE-")]
                fixes = sorted({f for i in ids if i in by_id for f in fixed_versions(by_id[i], name, eco)})
                rows.append({
                    "package": name,
                    "version": version,
                    "ecosystem": eco,
                    "dev": dev,
                    "level": level(group.get("max_severity", "")),
                    "score": group.get("max_severity", ""),
                    "ids": cves or [main["id"]],
                    "summary": (main.get("summary") or main.get("details", "").split("\n")[0])[:120],
                    "fixed": fixes,
                })
    rows.sort(key=lambda r: (r["dev"], RANK.get(r["level"], 4), r["package"]))
    return rows


def cell(text: str) -> str:
    return str(text).replace("|", "\\|").replace("\n", " ")


def section(title: str, path: Path) -> tuple[str, int, int]:
    lines = [f"### {title}", ""]
    if not path.is_file() or path.stat().st_size == 0:
        err = path.with_suffix(".error")
        why = err.read_text().strip() if err.is_file() else "no report was produced"
        lines += [f"**Not scanned:** {cell(why)}. See this step's log.", ""]
        return "\n".join(lines), 0, 0
    rows = rows_of(json.loads(path.read_text()))
    shipped = [r for r in rows if not r["dev"]]
    if not rows:
        lines += ["No known vulnerabilities.", ""]
        return "\n".join(lines), 0, 0
    lines += [
        f"{len(rows)} known ({len(shipped)} in what ships, {len(rows) - len(shipped)} in development tools only).",
        "",
        "| Severity | Package | Version | Ships? | Advisory | Fixed in | What it is |",
        "|---|---|---|---|---|---|---|",
    ]
    for r in rows:
        score = " (%s)" % r["score"] if r["score"] else ""
        lines.append(
            f"| {r['level'] or 'unrated'}{score} | {cell(r['package'])} | {cell(r['version'])} "
            f"| {'no (dev)' if r['dev'] else 'yes'} | {cell(', '.join(r['ids'][:3]))} "
            f"| {cell(', '.join(r['fixed'][:3]) or 'no fix yet')} | {cell(r['summary'])} |"
        )
    lines.append("")
    serious = sum(1 for r in shipped if r["level"] in ("critical", "high"))
    return "\n".join(lines), len(shipped), serious


def main(args: list[str]) -> None:
    parts, shipped, serious = [], 0, 0
    for arg in args:
        title, _, file = arg.partition("=")
        text, n, s = section(title, Path(file))
        parts.append(text)
        shipped += n
        serious += s
    head = (
        f"**{shipped} known vulnerabilities in what ships, {serious} of them high or critical.**"
        if shipped
        else "**No known vulnerabilities in what ships.**"
    )
    print("\n".join([head, "", *parts]))


if __name__ == "__main__":
    if len(sys.argv) < 2:
        sys.exit(__doc__)
    main(sys.argv[1:])
