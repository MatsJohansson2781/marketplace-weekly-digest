import json
from pathlib import Path

from marketplace_digest.digest_builder import build_digest
from marketplace_digest.models import DigestRequest

input_path = Path(__file__).parents[1] / "examples" / "weekly_digest.json"
request = DigestRequest.model_validate(json.loads(input_path.read_text()))

print(build_digest(request).model_dump_json(indent=2))
