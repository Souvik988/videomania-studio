# Voiceover Film — Publish Director

Local delivery packaging only. Run `scripts/deliver.py --project <id>`: copies the final, preview,
thumbnail, captions, stems and editable source into `delivery/`, writes `asset-provenance.json`
and `quality-report.md`, then re-probes every file. `publish_log.entries[0]` =
`{platform: "local", status: "exported"}`. Never upload or post anywhere without a separate,
explicit user approval for that specific action.
