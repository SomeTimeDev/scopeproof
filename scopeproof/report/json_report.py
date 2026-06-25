from __future__ import annotations

import json
from dataclasses import asdict

from scopeproof.models import FullReport


def render_json(report: FullReport) -> str:
    payload = asdict(report)
    payload["overall_status"] = report.overall_status
    return json.dumps(payload, indent=2, sort_keys=True)

