"""Install the pinned checker tree; never invoke a model or replace an existing tree."""
import argparse
import io
import json
import os
from pathlib import Path, PurePosixPath
import tarfile
from urllib.request import urlopen

ROOT = Path(__file__).resolve().parent
REVISION = "fdbcb9b93476149cce2d395532bf5164811fe053"
TARGET = ROOT / ".upstream" / "embedeval"
URL = f"https://codeload.github.com/Ecro/embedeval/tar.gz/{REVISION}"

def install(archive=None):
    if TARGET.exists() and any(TARGET.iterdir()):
        raise SystemExit(f"Refusing to overwrite existing checker tree: {TARGET}")
    if archive:
        payload = Path(archive).read_bytes()
    else:
        print(f"Downloading pinned upstream {REVISION}", flush=True)
        with urlopen(URL, timeout=60) as response:
            payload = response.read()
    files = 0
    TARGET.mkdir(parents=True, exist_ok=True)
    with tarfile.open(fileobj=io.BytesIO(payload), mode="r:*") as bundle:
        for member in bundle:
            parts = PurePosixPath(member.name).parts
            if parts and parts[0] == "embedeval-" + REVISION:
                parts = parts[1:]
            if not parts or parts[0] not in {"src", "cases", "LICENSE"}:
                continue
            if member.isdir():
                continue
            if not member.isfile() or any(p in {".", ".."} or ":" in p or "\\" in p for p in parts):
                raise ValueError(f"Unsafe archive member: {member.name}")
            dest = TARGET.joinpath(*parts).resolve()
            if not dest.is_relative_to(TARGET.resolve()):
                raise ValueError("Archive path escapes destination")
            source = bundle.extractfile(member)
            if source is None:
                raise ValueError(f"Unreadable archive member: {member.name}")
            data = source.read()
            # The recorded rule hashes include CRLF from the original Windows checkout.
            if dest.suffix in {".py", ".yaml"}:
                data = data.replace(b"\r\n", b"\n").replace(b"\n", b"\r\n")
            dest.parent.mkdir(parents=True, exist_ok=True)
            dest.write_bytes(data)
            files += 1
    os.environ["EMBEDEVAL_ROOT"] = str(TARGET)
    import bench
    verified = {}
    cases = bench.catalog()["cases"]
    for item in cases:
        case = item["caseDir"]
        if case not in verified:
            verified[case] = bench.rule_hash(TARGET / case)
        if verified[case] != item["rulesHash"]:
            raise ValueError(f"Pinned rules do not match recorded bytes: {case}")
    (TARGET / "installed-revision.json").write_text(json.dumps({"revision":REVISION, "verifiedQuestions":len(cases)}), encoding="utf-8")
    print(f"Installed {files} files; verified {len(cases)} question rule hashes. No model calls.")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--archive", help="Optional local pinned TAR or TAR.GZ")
    install(parser.parse_args().archive)
