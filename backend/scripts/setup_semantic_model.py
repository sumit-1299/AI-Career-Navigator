"""Download and verify the pinned public MiniLM model, then check CPU inference."""

from pathlib import Path
import sys
import urllib.request

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from services.semantic_encoder import FILES, MODEL_ID, MODEL_REVISION, file_digest, get_encoder, model_directory


def main():
    directory = model_directory()
    directory.mkdir(parents=True, exist_ok=True)
    print(f"Preparing {MODEL_ID} at revision {MODEL_REVISION}", flush=True)
    for name, expected in FILES.items():
        target = directory / name
        if target.is_file() and file_digest(target) == expected["sha256"]:
            print(f"Already verified: {name}", flush=True)
            continue
        temporary = target.with_suffix(target.suffix + ".part")
        url = f"https://huggingface.co/{MODEL_ID}/resolve/{MODEL_REVISION}/{expected['remote']}"
        print(f"Downloading {name} ({expected['bytes'] / 1_000_000:.1f} MB)...", flush=True)
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "CareerNavigatorResearchPrototype/1.0"})
            received = 0
            with urllib.request.urlopen(req, timeout=60) as response, temporary.open("wb") as destination:
                while chunk := response.read(1024 * 1024):
                    received += len(chunk)
                    if received > expected["bytes"]:
                        raise RuntimeError(f"Unexpected size for {name}.")
                    destination.write(chunk)
            if received != expected["bytes"] or file_digest(temporary) != expected["sha256"]:
                raise RuntimeError(f"Verification failed for {name}; no model file was installed.")
            temporary.replace(target)
        finally:
            temporary.unlink(missing_ok=True)
    vectors = get_encoder().encode(["Write SQL queries joining database tables.", "Retrieve records from relational tables."])
    similarity = sum(a * b for a, b in zip(*vectors))
    if len(vectors[0]) != 384 or not -1 <= similarity <= 1.00001:
        raise RuntimeError("Unexpected encoder output.")
    print("Model ready: CPU inference returned normalized 384-dimensional embeddings.")
    print("This uses a pretrained model; it does not train on candidate data.")


if __name__ == "__main__":
    try:
        main()
    except Exception as exception:
        print(f"Setup failed: {exception}", file=sys.stderr)
        print("Check the semantic dependencies and internet connection, then rerun this script.", file=sys.stderr)
        sys.exit(1)
