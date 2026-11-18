"""Local files, pinned course materials and reproducibility records."""

from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import subprocess
import tempfile
import urllib.request


def canonical_json(value) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def digest(value) -> str:
    return sha256_bytes(canonical_json(value).encode("utf-8"))


def safe_path(path: Path, root: Path) -> Path:
    """Reject links and escapes before touching a controlled output path."""
    path = Path(path)
    root = root.resolve()
    if not path.is_absolute():
        path = root / path
    try:
        relative = path.relative_to(root)
    except ValueError as exc:
        raise ValueError("作業先がリポジトリの外にあります。") from exc
    current = root
    for component in relative.parts:
        if component in ("..", "."):
            raise ValueError("相対パスに不正な要素があります。")
        current = current / component
        if current.is_symlink():
            raise ValueError("出力先にシンボリックリンクがあります。")
    if not path.resolve().is_relative_to(root):
        raise ValueError("作業先がリポジトリの外にあります。")
    return path


def atomic_write(path: Path, text: str) -> None:
    path = Path(path)
    if path.is_symlink():
        raise ValueError("シンボリックリンクには保存しません。")
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, name = tempfile.mkstemp(prefix=".day5-", dir=path.parent)
    temporary = Path(name)
    try:
        with os.fdopen(fd, "w", encoding="utf-8", newline="\n") as stream:
            stream.write(text)
            stream.flush()
            os.fsync(stream.fileno())
        temporary.replace(path)
    finally:
        temporary.unlink(missing_ok=True)


def write_json(path: Path, value) -> None:
    atomic_write(path, json.dumps(value, ensure_ascii=False, indent=2) + "\n")


def read_json(path: Path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def read_records(path: Path) -> list[dict]:
    if not path.exists():
        return []
    records = []
    for line_number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        if line.strip():
            try:
                records.append(json.loads(line))
            except json.JSONDecodeError as exc:
                raise ValueError(f"実行記録の{line_number}行目が途中で切れています。ZIPを共有してください。") from exc
    return records


def append_record(path: Path, value: dict) -> None:
    if path.is_symlink():
        raise ValueError("実行記録の保存先がシンボリックリンクです。")
    with path.open("a", encoding="utf-8", newline="\n") as stream:
        stream.write(canonical_json(value) + "\n")
        stream.flush()
        os.fsync(stream.fileno())


def git_head(root: Path) -> str | None:
    result = subprocess.run(["git", "rev-parse", "HEAD"], cwd=root, text=True,
                            capture_output=True, check=False)
    return result.stdout.strip() if result.returncode == 0 else None


def source_fingerprints(root: Path) -> dict[str, str]:
    paths = sorted((root / "day5_lab").glob("*.py"))
    paths += [root / "scripts/run_day5_comparison.py", root / "scripts/prepare_day5_answer.py",
              root / "lectures/05/questions.json", root / "lectures/05/source_manifest.json"]
    return {str(path.relative_to(root)): sha256_bytes(path.read_bytes()) for path in paths}


def data_dir(root: Path) -> Path:
    return safe_path(root / "lectures/05/.cache/rag_data", root)


def verify_data(root: Path, *, download: bool = False) -> dict:
    manifest = read_json(root / "lectures/05/source_manifest.json")
    target_dir = data_dir(root)
    details = []
    for spec in manifest["data_files"]:
        name = spec["name"]
        if name not in {"lectures.json", "graph.json", "tree.json", "index.sqlite3"}:
            raise ValueError("教材マニフェストのファイル名が不正です。")
        target = safe_path(target_dir / name, root)
        if target.exists():
            raw = target.read_bytes()
            if sha256_bytes(raw) != spec["sha256"] or len(raw) != spec["size_bytes"]:
                raise ValueError(f"{name}のハッシュが一致しません。既存データは変更していません。")
        elif not download:
            raise FileNotFoundError("教材が未準備です。python scripts/run_day5_comparison.py --setup を実行してください。")
        else:
            candidate = root / "data/rag_data" / name
            raw = candidate.read_bytes() if candidate.is_file() and not candidate.is_symlink() else b""
            if sha256_bytes(raw) != spec["sha256"]:
                expected_url = ("https://raw.githubusercontent.com/matsuolab/lecture-ai-engineering-2026/"
                                + manifest["upstream_commit"] + "/data/rag_data/" + name)
                if spec["url"] != expected_url:
                    raise ValueError("教材の取得URLが確定版と一致しません。")
                print(f"教材を取得中: {name}", flush=True)
                request = urllib.request.Request(expected_url, headers={"User-Agent": "aie2026-day5-study/1.0"})
                with urllib.request.urlopen(request, timeout=60) as response:
                    raw = response.read(spec["size_bytes"] + 1)
            if len(raw) != spec["size_bytes"] or sha256_bytes(raw) != spec["sha256"]:
                raise ValueError(f"取得した{name}のハッシュが一致しません。保存を中止しました。")
            target_dir.mkdir(parents=True, exist_ok=True)
            fd, temporary_name = tempfile.mkstemp(prefix=".download-", dir=target_dir)
            temporary = Path(temporary_name)
            try:
                with os.fdopen(fd, "wb") as stream:
                    stream.write(raw)
                temporary.replace(target)
            finally:
                temporary.unlink(missing_ok=True)
        details.append({"name": name, "sha256": spec["sha256"], "size_bytes": len(raw)})
    return {"upstream_commit": manifest["upstream_commit"], "files": details}


def snapshot_sources(root: Path, run_dir: Path, fingerprints: dict[str, str]) -> None:
    for relative, expected_hash in fingerprints.items():
        original = safe_path(root / relative, root)
        destination = safe_path(run_dir / "source_snapshot" / relative, root)
        raw = original.read_bytes()
        if sha256_bytes(raw) != expected_hash:
            raise ValueError("記録中にコードが変わりました。再実行してください。")
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_bytes(raw)


def copy_review_sources(root: Path, run_dir: Path, corpus, cases: list[dict]) -> None:
    """Reference text is for post-run human review, never sent as generation gold."""
    ids = sorted({page_id for case in cases for group in case["reference_groups"] for page_id in group["page_ids"]})
    write_json(run_dir / "reference_pages.json", {
        "purpose": "人手確認用。検索と回答生成にはこの正解候補を渡していません。",
        "pages": [corpus.pages[page_id] for page_id in ids],
    })
