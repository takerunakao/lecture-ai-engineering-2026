"""Bounded, resumable, explicitly requested live comparisons for Day5."""

from __future__ import annotations

import argparse
from datetime import datetime, timedelta, timezone
import json
import os
from pathlib import Path
import platform
import sys
import time
import uuid
import zipfile

from .gemini import GeminiClient, _model_name
from .io_utils import (append_record, atomic_write, copy_review_sources, data_dir, digest,
                       git_head, read_json, read_records, safe_path, snapshot_sources,
                       source_fingerprints, verify_data, write_json)
from .reporting import (automated_metrics, latest_successes, make_review_template,
                        render_answer, render_report, quri_text, validate_review)
from .retrieval import Corpus

DEFAULT_MODEL = "gemini-3.5-flash-lite"
JST = timezone(timedelta(hours=9))


def now_utc() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def build_task_plan(cases: list[dict], repeats: int) -> list[dict]:
    plan = []
    for repeat in range(1, repeats + 1):
        for index, case in enumerate(cases):
            methods = ("baseline", "graph") if (repeat - 1 + index) % 2 == 0 else ("graph", "baseline")
            for method in methods:
                plan.append({"task_id": f"r{repeat}_{case['id']}_{method}", "repeat": repeat,
                             "case_id": case["id"], "method": method})
    return plan


def load_cases(root: Path, corpus: Corpus) -> list[dict]:
    document = read_json(root / "lectures/05/questions.json")
    cases = document["cases"]
    if document.get("schema_version") != 1 or not document.get("preregistered"):
        raise ValueError("質問セットの事前定義が確認できません。")
    if len(cases) != 4 or len({case['id'] for case in cases}) != 4:
        raise ValueError("比較には重複しない4問が必要です。")
    for case in cases:
        if not isinstance(case["question"], str) or not 1 <= len(case["question"].strip()) <= 1000:
            raise ValueError("質問が空か長すぎます。")
        for group in case["reference_groups"]:
            if not group["page_ids"] or not set(group["page_ids"]) <= set(corpus.pages):
                raise ValueError(f"{case['id']}の根拠ページが対象資料にありません。")
    return cases


def preflight(root: Path, *, download: bool, model: str, repeats: int,
              remaining_trials: int | None = None) -> tuple[Corpus, list[dict], dict]:
    if sys.version_info < (3, 10):
        raise ValueError("Python 3.10以上を使用してください。")
    _model_name(model)
    data = verify_data(root, download=download)
    corpus = Corpus(data_dir(root))
    cases = load_cases(root, corpus)
    if len(corpus.pages) != 214:
        raise ValueError("対象ページ数が214ではありません。")
    # A vector already in the index checks file integrity and the selection code;
    # it is not a query embedding and is never reported as an experiment result.
    print(f"教材・構成確認OK / 資料={len(corpus.pages)}ページ / モデル={model}")
    print(f"実行予定: 4問 × 2方式 × {repeats}回 = {8 * repeats}回答")
    request_count = 8 * repeats if remaining_trials is None else remaining_trials
    print(f"今回のAPI予定回数: 回答生成 {request_count}回 + 質問の埋め込み {request_count}回")
    print("GEMINI_API_KEY: " + ("設定あり（値は表示しません）" if os.getenv("GEMINI_API_KEY") else "未設定"))
    print("この構成確認ではモデルAPIを呼び出していません。")
    return corpus, cases, data


def resolve_run(root: Path, value: str) -> Path:
    results = safe_path(root / "lectures/05/results", root)
    if value == "latest":
        latest = read_json(results / "latest.json")
        value = str(results / latest["run_id"])
    path = Path(value)
    if not path.is_absolute():
        path = root / path
    path = safe_path(path, root)
    if not path.resolve().is_relative_to(results.resolve()) or not (path / "config.json").is_file():
        raise ValueError("Day5の実行結果フォルダを指定してください。")
    return path


def create_run(root: Path, cases: list[dict], data: dict, args) -> tuple[Path, dict]:
    instant = datetime.now(timezone.utc)
    run_id = instant.strftime("%Y%m%dT%H%M%SZ_") + uuid.uuid4().hex[:8]
    directory = safe_path(root / "lectures/05/results" / run_id, root)
    directory.mkdir(parents=True, exist_ok=False)
    fingerprints = source_fingerprints(root)
    config = {
        "schema_version": 1, "run_id": run_id,
        "started_at_utc": instant.isoformat(timespec="seconds"),
        "started_at_jst": instant.astimezone(JST).isoformat(timespec="seconds"),
        "model": args.model, "embedding_model": "gemini-embedding-001",
        "embedding_dimensions": 768, "repeats": args.repeats, "top_k": 5,
        "temperature": 0, "max_output_tokens": args.max_output_tokens,
        "pause_seconds": args.pause_seconds, "timeout_seconds": args.timeout_seconds,
        "corpus_document_ids": ["lec01-main", "lec02-main", "lec03-main"], "corpus_pages": 214,
        "upstream_commit": data["upstream_commit"], "source_data": data,
        "code_fingerprints": fingerprints, "git_head_before_run": git_head(root),
        "python": platform.python_version(), "implementation_version": "1.0.0",
        "generation_protocol": "One deterministic retrieval followed by one generation request per trial. No model-directed query rewriting or agent tool loop.",
        "timing_protocol": "Each trial independently embeds the same raw question; total includes embedding, retrieval and generation; excludes setup and inter-trial pause.",
        "execution_order": "For each question the method order alternates; repetition 2 reverses repetition 1.",
        "cost_scope": "Paid Standard generation list-price estimate; excludes query embedding and index construction; actual invoices/free tier may differ.",
        "cases": cases, "task_plan": build_task_plan(cases, args.repeats),
    }
    config["configuration_sha256"] = digest(config)
    write_json(directory / "config.json", config)
    snapshot_sources(root, directory, fingerprints)
    write_json(root / "lectures/05/results/latest.json", {"run_id": run_id})
    write_json(directory / "human_review.json", make_review_template(config))
    return directory, config


def validate_resume(root: Path, directory: Path, data: dict) -> dict:
    config = read_json(directory / "config.json")
    expected_digest = config.get("configuration_sha256")
    unsigned = {k: v for k, v in config.items() if k != "configuration_sha256"}
    if not expected_digest or digest(unsigned) != expected_digest:
        raise ValueError("実行条件の記録が変更されています。再開せず、新しい実行にしてください。")
    if source_fingerprints(root) != config["code_fingerprints"] or data != config["source_data"]:
        raise ValueError("前回からコード・質問・教材が変更されています。同じ実験として再開できません。")
    return config


def export_result(root: Path, directory: Path, config: dict, status: str, error: dict | None = None) -> dict:
    records = read_records(directory / "records.jsonl")
    successful = latest_successes(records)
    planned = {task["task_id"] for task in config["task_plan"]}
    completed = planned == set(successful)
    if completed:
        status = "completed"
    review_path = directory / "human_review.json"
    review = read_json(review_path) if review_path.exists() else make_review_template(config)
    review_errors = validate_review(config, review)
    result = {
        "schema_version": 1, "run_id": config["run_id"], "status": status,
        "completed": completed, "model_api_executed": bool(records),
        "planned_trials": len(planned), "completed_trials": len(successful),
        "recorded_attempts": len(records), "updated_at_utc": now_utc(),
        "model": config["model"], "upstream_commit": config["upstream_commit"],
        "configuration_sha256": config["configuration_sha256"],
        "human_review_status": "reviewed" if not review_errors else "pending",
        "ready_for_submission": completed and not review_errors,
        "error": error,
        "cost_note": "Failed/aborted requests can still be billed; missing usage is not zero. See all attempts in records.jsonl.",
    }
    write_json(directory / "result.json", result)
    atomic_write(directory / "report.md", render_report(config, records, status, review))
    archive = safe_path(root / "lectures/05" / f"day5_results_{config['run_id']}.zip", root)
    temporary = archive.with_suffix(".zip.tmp")
    try:
        with zipfile.ZipFile(temporary, "w", compression=zipfile.ZIP_DEFLATED) as bundle:
            # The allowlist deliberately excludes the API key, environment,
            # full data cache, other homework, and unrelated local files.
            for name in ("config.json", "result.json", "records.jsonl", "report.md", "human_review.json",
                         "reference_pages.json", "progress.json"):
                path = safe_path(directory / name, root)
                if path.is_file():
                    bundle.write(path, arcname=f"{config['run_id']}/{name}")
            snapshot = directory / "source_snapshot"
            if snapshot.is_dir():
                for path in sorted(snapshot.rglob("*")):
                    if path.is_file():
                        safe_path(path, root)
                        bundle.write(path, arcname=f"{config['run_id']}/source_snapshot/{path.relative_to(snapshot)}")
        temporary.replace(archive)
    finally:
        temporary.unlink(missing_ok=True)
    result["archive_path"] = str(archive.relative_to(root))
    return result


def run_trials(root: Path, directory: Path, config: dict, corpus: Corpus,
               client: GeminiClient, *, sleep=time.sleep, timer=time.perf_counter) -> dict:
    """Injectable client/time functions support genuine offline failure tests."""
    records_path = directory / "records.jsonl"
    records = read_records(records_path)
    done = latest_successes(records)
    cases = {case["id"]: case for case in config["cases"]}
    copy_review_sources(root, directory, corpus, config["cases"])
    status, final_error = "running", None
    remaining = [task for task in config["task_plan"] if task["task_id"] not in done]
    try:
        for task in remaining:
            previous_attempts = sum(row["task_id"] == task["task_id"] for row in records)
            record = {**task, "attempt": previous_attempts + 1, "status": "running", "stage": "embed",
                      "started_at_utc": now_utc()}
            case = cases[task["case_id"]]
            started = timer()
            ordinal = len(done) + 1
            print(f"[{ordinal}/{len(config['task_plan'])}] {task['case_id']} / {task['method']} / 反復{task['repeat']}", flush=True)
            try:
                write_json(directory / "progress.json", {**record, "question": case["question"]})
                embedded = client.embed(case["question"])
                vector = embedded["vector"]
                record["embedding"] = {key: value for key, value in embedded.items() if key != "vector"}
                record["embedding"]["vector_sha256"] = digest(vector)
                record["stage"] = "retrieve"
                write_json(directory / "progress.json", {**task, "stage": "retrieve", "attempt": record["attempt"]})
                retrieval_started = timer()
                retrieved = corpus.retrieve(case["question"], vector, task["method"], top_k=config["top_k"])
                retrieved["elapsed_seconds"] = timer() - retrieval_started
                record["retrieval"] = retrieved
                if len(retrieved["pages"]) != 5 or len({page["page_id"] for page in retrieved["pages"]}) != 5:
                    raise ValueError("取得件数が5件でないか重複しています。API生成前に停止しました。")
                ids = [page["page_id"] for page in retrieved["pages"]]
                print("  [retrieval] " + ", ".join(ids), flush=True)
                record["stage"] = "generate"
                write_json(directory / "progress.json", {**task, "stage": "generate", "page_ids": ids,
                                                            "attempt": record["attempt"]})
                # Only the raw question and retrieved pages cross this boundary.
                # Reference groups, expected answers and human rubrics are not sent.
                generated = client.generate(case["question"], retrieved["pages"], config["model"],
                                            max_output_tokens=config["max_output_tokens"],
                                            temperature=config["temperature"])
                record["generation"] = generated
                record["elapsed_seconds"] = timer() - started
                record["metrics"] = automated_metrics(case, retrieved["pages"], generated["answer"])
                record["status"], record["stage"] = "completed", "completed"
                record["finished_at_utc"] = now_utc()
                append_record(records_path, record)
                records.append(record)
                done[task["task_id"]] = record
                cost = generated.get("cost_estimate", {}).get("usd")
                rendered_cost = "算定不可" if cost is None else f"${cost:.6f}"
                print(f"  → completed / {record['elapsed_seconds']:.2f}秒 / 生成API推定 {rendered_cost}", flush=True)
                write_json(directory / "progress.json", {"status": "running", "completed_trials": len(done),
                                                           "planned_trials": len(config["task_plan"])})
            except (Exception, KeyboardInterrupt) as exc:
                record["status"] = "interrupted" if isinstance(exc, KeyboardInterrupt) else "failed"
                record["elapsed_seconds"] = timer() - started
                # Provider errors have already had secrets removed. Other failures
                # are local validation errors; redact the key defensively as well.
                detail = str(exc) or type(exc).__name__
                key = os.getenv("GEMINI_API_KEY", "")
                if key:
                    detail = detail.replace(key, "[REDACTED]")
                record["error"] = {"type": type(exc).__name__, "message": detail[:1200],
                                   "http_status": getattr(exc, "status_code", None)}
                partial = getattr(exc, "partial_result", None)
                if partial:
                    record["generation_partial"] = partial
                record["finished_at_utc"] = now_utc()
                append_record(records_path, record)
                records.append(record)
                status, final_error = record["status"], record["error"]
                print(f"  → {status}: {record['error']['message']}", flush=True)
                break
            if len(done) < len(config["task_plan"]) and config["pause_seconds"]:
                sleep(config["pause_seconds"])
        else:
            status = "completed"
    except KeyboardInterrupt:
        status = "interrupted"
        final_error = {"type": "KeyboardInterrupt", "message": "待機中に中断しました。完了分は保存済みです。"}
    finally:
        outcome = export_result(root, directory, config, status, final_error)
    return outcome


def print_outcome(root: Path, directory: Path, outcome: dict) -> None:
    print(f"\n記録: {directory.relative_to(root)}/report.md")
    print(f"ダウンロードするZIP: {outcome['archive_path']}")
    print(f"完了した比較: {outcome['completed_trials']}/{outcome['planned_trials']}")
    if outcome["completed"]:
        print("API比較は完了しました。回答と引用根拠の人手確認はまだ別に必要です。")
        print("ZIPを共有してください。実際の結果から考察・提出レポート・300文字以内のQ3を確定します。")
    else:
        print("比較は未完了です。自動の再試行はしていません。部分結果もZIPに保存しました。")
        print("エラーを確認するため、このZIPを共有してください。")
        print("同じ条件で明示的に再開する場合: python scripts/run_day5_comparison.py --resume latest")


def main(root: Path | None = None) -> int:
    root = (root or Path(__file__).resolve().parents[1]).resolve()
    parser = argparse.ArgumentParser(description="Day5: 基本RAGと改良Graphを同条件で比較する（--run／--resume時にモデルAPIを使用）")
    actions = parser.add_mutually_exclusive_group()
    actions.add_argument("--check", action="store_true", help="保存済み教材と構成を確認。APIを呼ばない")
    actions.add_argument("--setup", action="store_true", help="確定版教材を取得し構成を確認。モデルAPIを呼ばない")
    actions.add_argument("--run", action="store_true", help="実際にモデルAPIを呼び出して比較する")
    actions.add_argument("--resume", metavar="RUN_DIR", help="同じ条件の未完了実行を明示的に再開。latest可")
    actions.add_argument("--summarize", metavar="RUN_DIR", help="結果・ZIPを再集計。APIを呼ばない。latest可")
    parser.add_argument("--model", default=os.getenv("AIE_MODEL", DEFAULT_MODEL))
    parser.add_argument("--repeats", type=int, choices=(1, 2, 3), default=2)
    parser.add_argument("--max-output-tokens", type=int, default=4096)
    parser.add_argument("--pause-seconds", type=float, default=10)
    parser.add_argument("--timeout-seconds", type=float, default=120)
    args = parser.parse_args()
    if not 512 <= args.max_output_tokens <= 8192 or not 0 <= args.pause_seconds <= 60 or not 10 <= args.timeout_seconds <= 300:
        parser.error("出力上限512〜8192、待機0〜60秒、タイムアウト10〜300秒で指定してください。")
    try:
        if args.summarize:
            directory = resolve_run(root, args.summarize)
            config = read_json(directory / "config.json")
            previous = read_json(directory / "result.json")
            outcome = export_result(root, directory, config, previous["status"], previous.get("error"))
            print_outcome(root, directory, outcome)
            return 0
        resume_directory = None
        preview = None
        if args.resume:
            resume_directory = resolve_run(root, args.resume)
            preview = read_json(resume_directory / "config.json")
            done = latest_successes(read_records(resume_directory / "records.jsonl"))
            remaining = sum(task["task_id"] not in done for task in preview["task_plan"])
        else:
            remaining = None
        corpus, cases, data = preflight(
            root, download=args.setup,
            model=preview["model"] if preview else args.model,
            repeats=preview["repeats"] if preview else args.repeats,
            remaining_trials=remaining)
        if not args.run and not args.resume:
            print("比較を開始するコマンド: python scripts/run_day5_comparison.py --run")
            return 0
        key = os.getenv("GEMINI_API_KEY")
        if not key:
            raise ValueError("GEMINI_API_KEYがありません。CodespacesのSecretsを確認し、Codespaceを再起動してください。")
        if args.resume:
            directory = resume_directory
            config = validate_resume(root, directory, data)
            print("再開は保存済み条件を使います（今回の--model等の指定は使いません）。")
        else:
            directory, config = create_run(root, cases, data, args)
        print(f"結果の保存先: {directory.relative_to(root)}")
        print("ここから実際のモデルAPIを呼び出します。料金は契約・利用枠に依存します。")
        client = GeminiClient(api_key=key, timeout_seconds=config["timeout_seconds"])
        outcome = run_trials(root, directory, config, corpus, client)
        print_outcome(root, directory, outcome)
        return 0 if outcome["completed"] else 1
    except (OSError, ValueError, KeyError, json.JSONDecodeError) as exc:
        message = str(exc)
        key = os.getenv("GEMINI_API_KEY", "")
        if key:
            message = message.replace(key, "[REDACTED]")
        print(f"確認で停止しました: {message}", file=sys.stderr)
        return 2


def prepare_main(root: Path | None = None) -> int:
    root = (root or Path(__file__).resolve().parents[1]).resolve()
    parser = argparse.ArgumentParser(description="実測と確認済みの観察をDay5の提出ファイルへ取り込む。APIを呼ばない")
    parser.add_argument("--run", default="latest", help="結果フォルダ。既定latest")
    args = parser.parse_args()
    try:
        directory = resolve_run(root, args.run)
        config = read_json(directory / "config.json")
        result = read_json(directory / "result.json")
        records = read_records(directory / "records.jsonl")
        if not result.get("completed") or len(latest_successes(records)) != len(config["task_plan"]):
            raise ValueError("比較が未完了です。成功した実測だけで提出完了とは扱えません。")
        review = read_json(directory / "human_review.json")
        errors = validate_review(config, review)
        if errors:
            raise ValueError("人手確認が未完了です。ZIPを共有して回答と根拠を確認してください。\n" + "\n".join(errors[:5]))
        answer_path = safe_path(root / "lectures/05/answer.md", root)
        original = answer_path.read_text(encoding="utf-8")
        if original.count("\n## 宿題\n") != 1:
            raise ValueError("answer.mdの宿題見出しを一意に確認できません。上書きしていません。")
        prefix, old_homework = original.split("\n## 宿題\n", 1)
        if "<!-- DAY5_GENERATED_HOMEWORK -->" not in old_homework:
            raise ValueError("answer.mdの宿題欄に独自の記述があります。上書きしていません。")
        relative = str(directory.relative_to(root / "lectures/05"))
        homework = render_answer(config, records, review, relative)
        if not homework.startswith("## 宿題"):
            raise ValueError("生成した宿題本文の見出しが不正です。")
        homework = homework.replace("## 宿題", "## 宿題\n\n<!-- DAY5_GENERATED_HOMEWORK -->", 1)
        # Keep a local backup even for a previous generated report.
        backup_dir = safe_path(root / "lectures/05/.cache/answer_backups", root)
        backup_dir.mkdir(parents=True, exist_ok=True)
        backup = backup_dir / (datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ_") + uuid.uuid4().hex[:6] + ".md")
        backup.write_text(original, encoding="utf-8")
        quri = quri_text(review)
        atomic_write(answer_path, prefix.rstrip() + "\n\n" + homework.rstrip() + "\n")
        atomic_write(root / "lectures/05/quri_answers.md", quri)
        pr_body = ("## 目的\n\nDay5の発展課題として、講義資料の基本RAGと質問に応じて候補を選ぶGraphを比較します。\n\n"
                   "## 変更内容\n\n- 独立したDay5用コードで、質問・モデル・214ページ・取得5ページを揃えました。\n"
                   f"- 4問を各方式{config['repeats']}回実行し、検索経路・回答・引用・時間・トークン・生成API推定費用を記録しました。\n"
                   "- 根拠の取得と、回答の正しさ・引用の妥当性を分けて確認しました。\n"
                   "- 実行前の質問と参照ページ、コード・教材の版を保存しました。\n\n"
                   "## 観察と採否\n\n" + review["observations"]["comparison_summary"] + "\n\n"
                   + review["observations"]["adoption_decision"] + "：" + review["observations"]["adoption_reason"]
                   + "\n\n## 記録\n\n提出レポート：`lectures/05/answer.md`\n"
                   + f"実測：`lectures/05/{relative}/report.md`\n\nAI支援を用いて実装・記録・分析を整理しました。\n")
        atomic_write(root / "lectures/05/PR_BODY.md", pr_body)
        export_result(root, directory, config, "completed")
        print("answer.md・PR_BODY.md・quri_answers.mdへ確認済みの結果を取り込みました。")
        print(f"Q3文字数: {len(review['observations']['q3'])}/300")
        return 0
    except (OSError, ValueError, KeyError, json.JSONDecodeError) as exc:
        print(f"提出ファイルの生成を停止しました: {exc}", file=sys.stderr)
        return 2
