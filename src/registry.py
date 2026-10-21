"""Minimal file-based model registry: registry/models/vN/ + registry/champion.json.
Set MODEL_BUCKET (gs://...) to mirror to GCS (requires google-cloud-storage + ADC)."""
import json
import os
import pathlib

ROOT = pathlib.Path(os.getenv("REGISTRY_DIR", "registry"))


def models_dir():
    d = ROOT / "models"
    d.mkdir(parents=True, exist_ok=True)
    return d


def next_version():
    nums = [int(p.name[1:]) for p in models_dir().glob("v*") if p.name[1:].isdigit()]
    return f"v{max(nums, default=0) + 1}"


def champion():
    f = ROOT / "champion.json"
    return json.loads(f.read_text()) if f.exists() else None


def set_champion(version, metrics):
    (ROOT / "champion.json").write_text(json.dumps({"version": version, "metrics": metrics}, indent=2))


def sync_to_gcs(version):
    bucket = os.getenv("MODEL_BUCKET")
    if not bucket:
        return False
    from google.cloud import storage  # optional dependency
    client = storage.Client()
    b = client.bucket(bucket.removeprefix("gs://"))
    for p in (models_dir() / version).iterdir():
        b.blob(f"models/{version}/{p.name}").upload_from_filename(p)
    b.blob("champion.json").upload_from_filename(ROOT / "champion.json")
    return True
