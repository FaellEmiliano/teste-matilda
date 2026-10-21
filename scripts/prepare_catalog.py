"""Refresh real OpenAlex records; never synthesize bibliographic metadata."""
import json
from pathlib import Path
from datetime import datetime, timezone
import httpx

ROOT = Path(__file__).resolve().parents[1]
DOIS = [
 '10.1126/science.1225829', '10.1038/nature09886',
 '10.1126/science.1192272', '10.1126/science.1258096',
 '10.1016/j.immuni.2005.06.008', '10.1038/mt.2008.200',
 '10.1056/NEJMoa2034577', '10.1056/NEJMoa2035389',
 '10.1126/science.1231143', '10.1038/171737a0',
]
if __name__ == '__main__':
    out = ROOT / 'data' / 'openalex_snapshots'
    out.mkdir(parents=True, exist_ok=True)
    with httpx.Client(timeout=25, follow_redirects=True) as client:
        for doi in DOIS:
            try:
                r = client.get('https://api.openalex.org/works/https://doi.org/' + doi)
                r.raise_for_status()
                record = r.json()
                path = out / (doi.lower().replace('/', '_') + '.json')
                path.write_text(json.dumps({'retrieved_at': datetime.now(timezone.utc).isoformat(), 'request_url': str(r.url), 'data': record}, ensure_ascii=False, indent=2))
                print(doi, record['title'], len(record.get('referenced_works', [])), 'references')
            except httpx.HTTPError as exc:
                print(doi, type(exc).__name__)
