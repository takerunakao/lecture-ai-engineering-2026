#!/usr/bin/env python3
"""Day2 発展: 用語集で LoRA 学習し、同一設問の学習前後と検索を比較する。

Colab T4 用。依存ライブラリは notebooks/day2_advanced_glossary.ipynb で導入。
  python scripts/prepare_day2_data.py
  python scripts/run_day2_training.py --dry-run
  python scripts/run_day2_training.py

dry-run はデータ・条件の確認だけで、GPU、torch、モデル取得、結果作成は不要。
実際に学習できなかった場合は完了結果を作らない。
"""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import importlib.metadata
import json
import math
from pathlib import Path
import platform
import subprocess
import sys
import time
import traceback
from typing import Any
import uuid

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

PINS = {"transformers": "5.18.0", "peft": "0.21.1", "trl": "1.14.2",
        "accelerate": "1.15.0", "datasets": "5.1.0"}
CONFIG = {
    "base_model": "Qwen/Qwen3.5-0.8B",
    "revision": "2fc06364715b967f1860aea9cf38778875588b17",
    "dtype": "float32", "quantization": None,
    "seed": 42, "num_train_epochs": 3, "warmup_steps": 6,
    "lr": 2e-4, "lora_r": 16, "lora_alpha": 32, "lora_dropout": 0.05,
    "target_modules": ["q_proj", "k_proj", "v_proj", "o_proj", "gate_proj", "up_proj", "down_proj"],
    "per_device_train_batch_size": 4, "gradient_accumulation_steps": 2,
    "max_seq_len": 512, "max_new_tokens": 256,
    "gen": {"do_sample": False}, "enable_thinking": False,
    "eos_policy": "tokenizer.eos_token_id_explicit_in_both_evaluations",
    "fp16": False, "bf16": False, "packing": False,
    "loss_scope": "full_sequence", "completion_only_loss": False, "assistant_only_loss": False,
    "lr_scheduler_type": "cosine", "logging_steps": 10,
    "save_steps": 10, "save_total_limit": 2,
    "evaluation_context": "system_and_question_only_no_glossary",
}


class ExperimentError(RuntimeError):
    """利用者が直せる、秘密情報を含まない事前確認エラー。"""


def now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def clean_json(value: Any) -> Any:
    """JSONにNaN/Infinityを残さず、未知の実行時オブジェクトも保存しない。"""
    if value is None or isinstance(value, (str, bool, int)):
        return value
    if isinstance(value, float):
        return value if math.isfinite(value) else None
    if isinstance(value, dict):
        return {str(k): clean_json(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [clean_json(v) for v in value]
    return None


def save_json(path: Path, value: Any) -> None:
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(json.dumps(clean_json(value), ensure_ascii=False, indent=2,
                                    allow_nan=False) + "\n", encoding="utf-8")
    temporary.replace(path)


def git_commit() -> str | None:
    try:
        result = subprocess.run(["git", "rev-parse", "HEAD"], cwd=ROOT,
                                capture_output=True, text=True, timeout=5, check=False)
        return result.stdout.strip() if result.returncode == 0 else None
    except (OSError, subprocess.TimeoutExpired):
        return None


def read_inputs() -> tuple[list, list, list, dict, dict]:
    from app.day2_eval import SYSTEM, load_cases, load_jsonl

    data_dir = ROOT / "lectures/02/data"
    paths = {"train": data_dir / "glossary_sft.jsonl", "raw": data_dir / "glossary_sft_raw.jsonl",
             "cases": data_dir / "eval_cases.json", "manifest": data_dir / "manifest.json",
             "glossary": ROOT / "data/glossary.json"}
    missing = [str(p.relative_to(ROOT)) for p in paths.values() if not p.is_file()]
    if missing:
        raise ExperimentError("データがありません。先に scripts/prepare_day2_data.py を実行してください：" + ", ".join(missing))
    train = load_jsonl(paths["train"])
    cases = load_cases(paths["cases"])
    terms = json.loads(paths["glossary"].read_text(encoding="utf-8"))["terms"]
    manifest = json.loads(paths["manifest"].read_text(encoding="utf-8"))
    if not train or not cases:
        raise ExperimentError("学習データと評価設問は1件以上必要です。")
    positives = negatives = 0
    for index, row in enumerate(train, 1):
        messages = row.get("messages", [])
        if ([m.get("role") for m in messages] != ["system", "user", "assistant"] or
                any(not isinstance(m.get("content"), str) for m in messages) or
                messages[0]["content"] != SYSTEM):
            raise ExperimentError(f"学習データ {index} 行目のchat形式またはsystem文が一致しません。")
        try:
            target = json.loads(messages[-1]["content"])
        except (json.JSONDecodeError, TypeError) as exc:
            raise ExperimentError(f"学習データ {index} 行目の教師JSONが不正です。") from exc
        if (not isinstance(target, dict) or set(target) != {"answer", "needs_review"} or
                not isinstance(target["answer"], str) or not isinstance(target["needs_review"], bool)):
            raise ExperimentError(f"学習データ {index} 行目の教師JSONのキーまたは型が不正です。")
        negatives += int(target["needs_review"])
        positives += int(not target["needs_review"])
    metadata = {"dataset_sha256": sha256(paths["train"]), "raw_dataset_sha256": sha256(paths["raw"]),
                "eval_cases_sha256": sha256(paths["cases"]), "glossary_sha256": sha256(paths["glossary"]),
                "manifest_sha256": sha256(paths["manifest"]), "training_examples": len(train),
                "positive_examples": positives, "negative_examples": negatives, "eval_examples": len(cases)}
    return train, cases, terms, manifest, metadata


def build_messages(question: str) -> list[dict]:
    from app.day2_eval import SYSTEM
    # 正解・用語集本文・検索結果は生成モデルへ渡さない。
    return [{"role": "system", "content": SYSTEM}, {"role": "user", "content": question}]


def tokenize_ids(tokenizer: Any, messages: list[dict], *, add_generation_prompt: bool) -> list[int]:
    # transformers 5.18 defaults to BatchEncoding. len(mapping) counts fields,
    # so explicitly request a flat list and validate it before any GPU work.
    ids = tokenizer.apply_chat_template(
        messages, tokenize=True, return_dict=False, return_tensors=None,
        add_generation_prompt=add_generation_prompt, enable_thinking=False,
    )
    if (not isinstance(ids, list) or not ids
            or any(type(token) is not int or token < 0 for token in ids)):
        raise ExperimentError(
            "tokenizerが一次元の整数token ID列を返していません。"
            "return_dict=Falseとreturn_tensors=None、およびtokenizerの版を確認してください。"
        )
    return ids


def tokenize_all(tokenizer: Any, train: list, cases: list) -> tuple[list, list, dict]:
    """学習と生成で実際に使うtoken列を作り、切り捨て前に全件を検査する。"""
    training = []
    evaluation = []
    lengths = {"max_seq_len": CONFIG["max_seq_len"], "training": [], "evaluation": []}
    for index, row in enumerate(train, 1):
        ids = tokenize_ids(tokenizer, row["messages"], add_generation_prompt=False)
        training.append({"input_ids": ids, "attention_mask": [1] * len(ids)})
        lengths["training"].append({"row": index, "tokens": len(ids)})
    for case in cases:
        ids = tokenize_ids(tokenizer, build_messages(case["question"]), add_generation_prompt=True)
        evaluation.append(ids)
        lengths["evaluation"].append({"id": case["id"], "input_tokens": len(ids)})
    too_long = ([f"train行{x['row']}={x['tokens']}" for x in lengths["training"]
                 if x["tokens"] > CONFIG["max_seq_len"]] +
                [f"eval {x['id']}={x['input_tokens']}" for x in lengths["evaluation"]
                 if x["input_tokens"] > CONFIG["max_seq_len"]])
    lengths["all_fit"] = not too_long
    lengths["exceeds_limit"] = too_long
    return training, evaluation, lengths


def evaluate(model: Any, tokenizer: Any, torch: Any, cases: list, tokenized_cases: list,
             label: str, run_dir: Path) -> dict:
    from app.day2_eval import score_answer, summarize

    model.eval()
    model.config.use_cache = True
    rows: list[dict] = []
    started = time.perf_counter()
    payload = {"status": "running", "completed": False, "planned_n": len(cases),
               "summary": None, "rows": rows}

    def persist() -> None:
        payload["summary"] = summarize(rows, label)
        payload["summary"]["seconds"] = time.perf_counter() - started
        payload["summary"]["generation_seconds"] = sum(r["elapsed_seconds"] for r in rows)
        payload["summary"]["truncated_n"] = sum(r["truncated"] for r in rows)
        save_json(run_dir / f"eval_{label}.json", payload)

    # Trainer can synchronize generation_config with the tokenizer. Pass EOS
    # explicitly both before and after so that synchronization is not a confound.
    eos_ids = tokenizer.eos_token_id
    eos_ids = set(eos_ids if isinstance(eos_ids, (list, tuple)) else [eos_ids])
    try:
        persist()
        for case, ids in zip(cases, tokenized_cases, strict=True):
            inputs = {"input_ids": torch.tensor([ids], dtype=torch.long, device=model.device),
                      "attention_mask": torch.ones((1, len(ids)), dtype=torch.long, device=model.device)}
            torch.cuda.synchronize()
            begin = time.perf_counter()
            with torch.inference_mode():
                output = model.generate(**inputs, max_new_tokens=CONFIG["max_new_tokens"],
                                        pad_token_id=tokenizer.pad_token_id,
                                        eos_token_id=tokenizer.eos_token_id, **CONFIG["gen"])
            torch.cuda.synchronize()
            elapsed = time.perf_counter() - begin
            generated = output[0][len(ids):].tolist()
            raw = tokenizer.decode(generated, skip_special_tokens=True).strip()
            eos_terminated = bool(generated) and generated[-1] in eos_ids
            hit_cap = len(generated) >= CONFIG["max_new_tokens"]
            row = {"id": case["id"], "category": case["category"], "question": case["question"],
                   "term_id": case.get("term_id"), "raw": raw, "input_tokens": len(ids),
                   "generated_tokens": len(generated), "max_new_tokens": CONFIG["max_new_tokens"],
                   "hit_max_new_tokens": hit_cap, "eos_terminated": eos_terminated,
                   "truncated": hit_cap and not eos_terminated, "elapsed_seconds": elapsed,
                   **score_answer(raw, case)}
            rows.append(row)
            persist()
            print(f"[{label}] {len(rows)}/{len(cases)} {case['id']} "
                  f"形式={row['format_ok']} 内容={row['content_ok']} {elapsed:.2f}秒", flush=True)
        payload.update(status="completed", completed=True)
        persist()
        return payload
    except BaseException as exc:
        payload.update(status="interrupted" if isinstance(exc, KeyboardInterrupt) else "failed",
                       error_type=type(exc).__name__, error_detail=str(exc))
        persist()
        raise


def run(run_dir: Path, train: list, cases: list, terms: list, manifest: dict, data: dict) -> int:
    # ここからのみGPU・機械学習ライブラリを使う。dry-runではimportしない。
    import torch
    from datasets import Dataset
    from peft import LoraConfig
    from transformers import AutoModelForCausalLM, AutoTokenizer, TrainerCallback, set_seed
    from trl import SFTConfig, SFTTrainer
    from app.day2_eval import evaluate_search

    versions = {name: importlib.metadata.version(name) for name in PINS}
    versions.update(torch=torch.__version__, python=platform.python_version())
    mismatched = [f"{name}: {versions[name]}（指定 {required}）" for name, required in PINS.items()
                  if versions[name] != required]
    if mismatched:
        raise ExperimentError("固定ライブラリ版と一致しません。Colabの導入セルを実行してください：" + ", ".join(mismatched))
    if not torch.cuda.is_available():
        raise ExperimentError("CUDA GPUがありません。ColabのランタイムをT4 GPUに変更してください。学習は未実行です。")
    if run_dir.exists():
        raise ExperimentError("結果フォルダが既にあります。新しい --run-dir を指定してください。")
    run_dir.mkdir(parents=True, exist_ok=False)
    expected_steps = math.ceil(math.ceil(len(train) / CONFIG["per_device_train_batch_size"]) /
                               CONFIG["gradient_accumulation_steps"]) * CONFIG["num_train_epochs"]
    result = {"status": "running", "completed": False, "executed_training_myself": False,
              "started_at": now(), "finished_at": None, "stage": "preflight",
              "method": "LoRA（量子化なし・float32）", "config": CONFIG, "versions": versions,
              "model_revision": CONFIG["revision"], "git_commit": git_commit(),
              "runner_sha256": sha256(Path(__file__)), "gpu": torch.cuda.get_device_name(0),
              "gpu_total_memory_bytes": torch.cuda.get_device_properties(0).total_memory,
              **data, "manifest": manifest, "before": None, "after": None, "search": None,
              "train": {"status": "not_started", "completed": False, "planned_optimizer_steps": expected_steps,
                        "global_step": None, "epoch": None, "seconds": None,
                        "final_logged_loss": None, "final_logged_loss_step": None, "train_loss": None},
              "regressed_ids": []}
    trainer = None
    training_started = None
    wall_start = time.perf_counter()
    train_log = {"status": "not_started", "logs": [], "log_history": []}

    def persist() -> None:
        save_json(run_dir / "result.json", result)
        save_json(run_dir / "train_log.json", train_log)

    class SaveTrainingLog(TrainerCallback):
        def on_log(self, args, state, control, logs=None, **kwargs):
            entry = {"at": now(), "step": state.global_step, "epoch": state.epoch,
                     **clean_json(logs or {})}
            train_log["logs"].append(entry)
            train_log["log_history"] = clean_json(state.log_history)
            result["train"].update(global_step=state.global_step, epoch=state.epoch)
            if logs and "loss" in logs:
                result["train"].update(final_logged_loss=entry.get("loss"),
                                       final_logged_loss_step=state.global_step)
            persist()
            if logs and isinstance(logs.get("loss"), (float, int)) and not math.isfinite(logs["loss"]):
                raise ExperimentError("学習lossがNaNまたはInfinityになったため停止しました。")

    try:
        persist()
        # 途中までしか実行できなくても、空の評価を完了と混同しない。
        for label in ("before", "after"):
            save_json(run_dir / f"eval_{label}.json", {"status": "not_started", "completed": False,
                                                       "planned_n": len(cases), "summary": None, "rows": []})
        save_json(run_dir / "eval_search.json", {"status": "not_started", "completed": False,
                                                  "summary": None, "rows": []})
        set_seed(CONFIG["seed"])
        baseline = evaluate_search(cases, terms)
        baseline.update(status="completed", completed=True)
        result["search"] = baseline["summary"]
        save_json(run_dir / "eval_search.json", baseline)
        result["stage"] = "tokenize"
        persist()
        tokenizer = AutoTokenizer.from_pretrained(CONFIG["base_model"], revision=CONFIG["revision"])
        if tokenizer.pad_token is None:
            tokenizer.pad_token = tokenizer.eos_token
        result["tokenizer_special_tokens"] = {
            "eos_token_id": tokenizer.eos_token_id,
            "pad_token_id": tokenizer.pad_token_id,
        }
        tokenized_train, tokenized_cases, lengths = tokenize_all(tokenizer, train, cases)
        save_json(run_dir / "token_lengths.json", lengths)
        result["token_lengths"] = {"all_fit": lengths["all_fit"],
                                  "train_max": max(x["tokens"] for x in lengths["training"]),
                                  "eval_input_max": max(x["input_tokens"] for x in lengths["evaluation"])}
        if not lengths["all_fit"]:
            raise ExperimentError("512トークンを超える例があります。黙って切り捨てません。token_lengths.jsonを確認し、データを見直してください。")
        result["stage"] = "load_model"
        persist()
        model = AutoModelForCausalLM.from_pretrained(CONFIG["base_model"], revision=CONFIG["revision"],
                                                    dtype=torch.float32).to("cuda")
        model.config.use_cache = True
        model.eval()  # adapterを装着する前に必ずevalモードで測定する。
        result["base_memory_bytes"] = model.get_memory_footprint()
        result["stage"] = "evaluate_before"
        persist()
        before = evaluate(model, tokenizer, torch, cases, tokenized_cases, "before", run_dir)
        result["before"] = before["summary"]
        result["stage"] = "prepare_training"
        persist()
        model.config.use_cache = False
        lora = LoraConfig(r=CONFIG["lora_r"], lora_alpha=CONFIG["lora_alpha"],
                          lora_dropout=CONFIG["lora_dropout"], bias="none", task_type="CAUSAL_LM",
                          target_modules=CONFIG["target_modules"])
        settings = SFTConfig(
            output_dir=str(run_dir / "checkpoints"), num_train_epochs=CONFIG["num_train_epochs"],
            per_device_train_batch_size=CONFIG["per_device_train_batch_size"],
            gradient_accumulation_steps=CONFIG["gradient_accumulation_steps"],
            learning_rate=CONFIG["lr"], lr_scheduler_type=CONFIG["lr_scheduler_type"],
            warmup_steps=CONFIG["warmup_steps"], logging_steps=CONFIG["logging_steps"],
            save_steps=CONFIG["save_steps"], save_total_limit=CONFIG["save_total_limit"],
            fp16=False, bf16=False, max_length=CONFIG["max_seq_len"], packing=False,
            completion_only_loss=False, assistant_only_loss=False, report_to="none", seed=CONFIG["seed"])
        # 全会話のlossを使う設定は配布ノートと同じ。評価ラベルはTrainerへ渡さない。
        trainer = SFTTrainer(model=model, args=settings, train_dataset=Dataset.from_list(tokenized_train),
                             peft_config=lora, processing_class=tokenizer, callbacks=[SaveTrainingLog()])
        if len(trainer.train_dataset) != len(tokenized_train):
            raise ExperimentError("Trainerの前処理でデータ件数が変化しました。学習を開始せず停止します。")
        for source, prepared in zip(tokenized_train, trainer.train_dataset, strict=True):
            if list(prepared["input_ids"]) != source["input_ids"]:
                raise ExperimentError("Trainerの前処理でtoken列が変化しました。切り捨て・テンプレート差を確認してください。")
        trainable, total = trainer.model.get_nb_trainable_parameters()
        result["train"].update(trainable_parameters=trainable, total_parameters=total,
                               trainable_fraction=trainable / total, status="running")
        result["stage"] = "training"
        train_log["status"] = "running"
        persist()
        torch.cuda.synchronize()
        training_started = time.perf_counter()
        train_output = trainer.train()
        torch.cuda.synchronize()
        result["train"]["seconds"] = time.perf_counter() - training_started
        training_started = None
        mean_loss = float(train_output.training_loss)
        if not math.isfinite(mean_loss):
            raise ExperimentError("学習全体の平均train_lossが非有限のため、完了として保存しません。")
        logged_losses = [entry for entry in trainer.state.log_history if "loss" in entry]
        if logged_losses:
            final_loss = float(logged_losses[-1]["loss"])
            if not math.isfinite(final_loss):
                raise ExperimentError("最後に記録された区間lossが非有限のため、完了として保存しません。")
            result["train"].update(final_logged_loss=final_loss,
                                   final_logged_loss_step=logged_losses[-1].get("step"))
        if (trainer.state.global_step != expected_steps or trainer.state.epoch is None or
                trainer.state.epoch + 1e-6 < CONFIG["num_train_epochs"]):
            raise ExperimentError("予定のステップ数・エポック数に達していません。部分学習として保存します。")
        result["train"].update(status="completed", completed=True, global_step=trainer.state.global_step,
                               epoch=trainer.state.epoch, train_loss=mean_loss, metrics=clean_json(train_output.metrics))
        train_log.update(status="completed", log_history=clean_json(trainer.state.log_history))
        result["stage"] = "save_adapter"
        persist()
        trainer.model.save_pretrained(run_dir / "adapter")
        tokenizer.save_pretrained(run_dir / "adapter")
        tuned = trainer.model
        tuned.config.use_cache = True
        tuned.eval()
        result["stage"] = "evaluate_after"
        persist()
        after = evaluate(tuned, tokenizer, torch, cases, tokenized_cases, "after", run_dir)
        result["after"] = after["summary"]
        result["regressed_ids"] = [b["id"] for b, a in zip(before["rows"], after["rows"], strict=True)
                                   if b["both_ok"] and not a["both_ok"]]
        result.update(status="completed", completed=True, executed_training_myself=True, stage="completed")
        print("学習と前後評価が完了しました。結果を確認し、自分の考察を追記してください。", flush=True)
        return 0
    except BaseException as exc:
        interrupted = isinstance(exc, KeyboardInterrupt)
        result.update(status="interrupted" if interrupted else "failed", completed=False,
                      executed_training_myself=False, error_type=type(exc).__name__,
                      error_detail=str(exc), traceback_file="traceback.txt")
        (run_dir / "traceback.txt").write_text(traceback.format_exc(), encoding="utf-8")
        if training_started is not None:
            result["train"]["seconds"] = time.perf_counter() - training_started
        if result["train"]["status"] == "running":
            result["train"].update(status=result["status"], completed=False)
            train_log["status"] = result["status"]
        print(f"未完了として保存します：{type(exc).__name__}／段階 {result['stage']}。", file=sys.stderr)
        traceback.print_exc(file=sys.stderr)
        print(f"部分結果：{run_dir}", file=sys.stderr)
        return 130 if interrupted else 1
    finally:
        if trainer is not None:
            result["train"].update(global_step=trainer.state.global_step, epoch=trainer.state.epoch)
            train_log["log_history"] = clean_json(trainer.state.log_history)
        result["finished_at"] = now()
        result["wall_seconds"] = time.perf_counter() - wall_start
        persist()


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--dry-run", action="store_true", help="入力と実験計画を確認。モデル取得・学習・結果作成なし")
    parser.add_argument("--run-dir", type=Path, help="新規の結果フォルダ。既存フォルダは上書きしない")
    args = parser.parse_args(argv)
    try:
        train, cases, terms, manifest, data = read_inputs()
        print(json.dumps({"config": CONFIG, "data": data, "required_versions": PINS}, ensure_ascii=False, indent=2))
        if args.dry_run:
            print("DRY RUN：学習・生成・モデル取得・実測result.json作成は行っていません。")
            print("全token長の検査は実行時に固定revisionのtokenizerで行います（このdry-runでは未実施）。")
            return 0
        run_id = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ") + "_" + uuid.uuid4().hex[:8]
        run_dir = args.run_dir or ROOT / "lectures/02/results" / run_id
        return run(run_dir.resolve(), train, cases, terms, manifest, data)
    except ExperimentError as exc:
        print(str(exc), file=sys.stderr)
        return 2
    except (ImportError, importlib.metadata.PackageNotFoundError) as exc:
        print(f"ライブラリ未導入です（{type(exc).__name__}）。Colabノートブックの導入セルから実行してください。学習は未実行です。", file=sys.stderr)
        traceback.print_exc(file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
