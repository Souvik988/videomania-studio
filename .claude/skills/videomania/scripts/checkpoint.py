"""Write an OpenMontage checkpoint for a voiceover-film stage.

Usage:
  checkpoint.py --project ID --stage idea --status completed \
      --artifact brief=artifacts/brief.json --artifact decision_log=artifacts/decision_log.json \
      [--approval-ref D001] [--note "..."]
  checkpoint.py --project ID --next          # print next stage to run

Gated stages can be written `completed` only with --approval-ref pointing at an
approval_policy decision in artifacts/decision_log.json (auto mode) or with
--human-approved after the user explicitly approved this gate in chat.
OpenMontage's writer validates artifacts against their schemas and raises on
gate violations — this script never bypasses that.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import vm_env  # noqa: E402


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--project", required=True)
    ap.add_argument("--pipeline", default="voiceover-film")
    ap.add_argument("--stage")
    ap.add_argument("--status", default="completed", choices=["completed", "awaiting_human", "in_progress", "failed"])
    ap.add_argument("--artifact", action="append", default=[], help="name=relative/path.json")
    ap.add_argument("--approval-ref", help="decision_id of an approval_policy decision covering this gate")
    ap.add_argument("--human-approved", action="store_true", help="user approved this gate explicitly in chat")
    ap.add_argument("--note", default=None)
    ap.add_argument("--next", action="store_true")
    args = ap.parse_args()
    vm_env.ensure_openmontage_on_path()
    from lib.checkpoint import get_next_stage, write_checkpoint
    from lib.paths import PROJECTS_DIR

    if args.next:
        print(get_next_stage(Path(PROJECTS_DIR), args.project, args.pipeline))
        return 0

    proj = vm_env.project_dir(args.project)
    artifacts = {}
    for spec in args.artifact:
        name, rel = spec.split("=", 1)
        artifacts[name] = vm_env.read_json(proj / rel)

    approved = args.human_approved
    meta = {}
    if args.approval_ref:
        log = vm_env.read_json(proj / "artifacts" / "decision_log.json")
        match = [d for d in log["decisions"] if d["decision_id"] == args.approval_ref]
        if not match or match[0]["category"] != "approval_policy" or not match[0].get("user_approved"):
            print(f"REFUSED: {args.approval_ref} is not a user-approved approval_policy decision")
            return 2
        approved = True
        meta["approval_ref"] = args.approval_ref
        meta["approval_scope"] = match[0]["selected"]
    if args.note:
        meta["note"] = args.note
    path = write_checkpoint(Path(PROJECTS_DIR), args.project, args.stage, args.status, artifacts,
                            pipeline_type=args.pipeline, human_approved=approved, metadata=meta or None)
    print(f"checkpoint written: {path}")
    print(f"next stage: {get_next_stage(Path(PROJECTS_DIR), args.project, args.pipeline)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
