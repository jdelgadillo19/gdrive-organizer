"""Human-readable canonization reports."""

from __future__ import annotations

from kip_core.canon.models import CanonizationResult


def format_canonization_markdown(result: CanonizationResult) -> str:
    lines: list[str] = [
        "# Libby Canonization Report",
        "",
        f"- **Corpus:** `{result.corpus_root}`",
        f"- **Canon folder (recommended):** `{result.canon_folder_relative}/`",
        f"- **Analyzed at:** {result.analyzed_at.isoformat()}",
        f"- **Extraction coverage:** {result.extraction_coverage_ratio * 100:.1f}%",
        "",
        "## Canon topics",
        "",
    ]

    for topic in result.topics:
        lines.append(f"### {topic.title} (`{topic.topic_id.value}`)")
        lines.append("")
        lines.append(topic.description)
        lines.append("")
        if topic.gap:
            lines.append(f"**GAP:** {topic.gap_message}")
            lines.append("")
            continue
        if topic.recommended_file_id:
            lines.append(f"**Recommended canon:** `{topic.recommended_file_id}`")
            lines.append("")
        if topic.candidates:
            lines.append("| Score | Canon? | Path |")
            lines.append("|------:|:------:|------|")
            for cand in topic.candidates:
                flag = "yes" if cand.recommended_canon else ""
                lines.append(f"| {cand.match_score} | {flag} | `{cand.relative_path}` |")
            lines.append("")

    if result.cross_reference_issues:
        lines.extend(["## Cross-reference and conflicts", ""])
        for issue in result.cross_reference_issues:
            lines.append(f"- **[{issue.severity.value}]** {issue.summary}")
            lines.append(f"  - A: `{issue.file_a}`")
            lines.append(f"  - B: `{issue.file_b}`")
            if issue.contradiction_signals:
                lines.append(f"  - Signals: {', '.join(issue.contradiction_signals)}")
        lines.append("")

    if result.near_duplicate_groups:
        lines.extend(["## Near-duplicate groups", ""])
        for group in result.near_duplicate_groups:
            lines.append("- " + ", ".join(f"`{g}`" for g in group))
        lines.append("")

    if result.unassigned_documents:
        lines.extend(["## Unassigned documents", ""])
        for path in result.unassigned_documents:
            lines.append(f"- `{path}`")
        lines.append("")

    lines.extend(
        [
            "## Next steps",
            "",
            "1. Create or designate `Canon/` under the corpus root (read-wide, write restricted).",
            "2. Promote recommended files per topic; resolve cross-reference issues.",
            "3. Re-run canonization after moves to verify canon coverage.",
            "",
        ]
    )
    return "\n".join(lines)
