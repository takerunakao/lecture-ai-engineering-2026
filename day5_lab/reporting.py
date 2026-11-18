"""Evidence-preserving reports for the Day5 retrieval comparison.

Page-ID matches are provenance checks, never an automatic correctness judge.
All public submission text is assembled only after a complete run and an
explicit human review. Missing usage and costs remain unknown.
"""

from __future__ import annotations

import json
import math
import re
import statistics
import unicodedata


METHODS = {"baseline": "基本RAG", "graph": "改良Graph"}
OBSERVATIONS = (
    "comparison_summary", "improved_example", "remaining_failure_or_limitation",
    "adoption_decision", "adoption_reason", "q3",
)
VERDICTS = {"pass", "fail", "unsure"}
REPOSITORY_URL = "https://github.com/takerunakao/lecture-ai-engineering-2026"


def _page_id(page: dict) -> str | None:
    value = page.get("page_id", page.get("id"))
    return value if isinstance(value, str) else None


def _citations(answer: str) -> list[str]:
    """Extract unique explicit page citations, including compact page lists."""
    text = unicodedata.normalize("NFKC", answer)
    found = []
    pattern = re.compile(
        r"第\s*(\d{1,2})\s*回\s*(?:[・:：/／,、-]\s*)?"
        r"(?:PDF\s*)?(?:pp?\.?\s*|ページ\s*)"
        r"(\d{1,3}(?:\s*(?:[,、]\s*\d{1,3}|[-–〜～]\s*\d{1,3}))*)",
        re.IGNORECASE,
    )
    for match in pattern.finditer(text):
        lecture = int(match.group(1))
        for part in re.split(r"[,、]", match.group(2)):
            interval = re.fullmatch(r"\s*(\d+)\s*[-–〜～]\s*(\d+)\s*", part)
            if interval:
                first, last = map(int, interval.groups())
                # Malformed or very broad ranges are not expanded into fake citations.
                numbers = range(first, last + 1) if 0 < first <= last and last - first <= 100 else []
            else:
                numbers = [int(part.strip())]
            for page in numbers:
                if lecture > 0 and page > 0:
                    found.append(f"lec{lecture:02d}-main-p{page:03d}")
    found.extend(re.findall(r"\blec\d{2}-main-p\d{3}\b", text))
    return list(dict.fromkeys(found))


def automated_metrics(case: dict, pages: list[dict], answer: str) -> dict:
    """Compute limited, reproducible evidence proxies without a model judge."""
    retrieved = {_page_id(page) for page in pages if isinstance(page, dict)} - {None}
    groups = case.get("reference_groups", [])
    hits = [bool(retrieved.intersection(group.get("page_ids", []))) for group in groups]
    citations = _citations(answer)
    in_context = [page_id for page_id in citations if page_id in retrieved]
    return {
        "reference_groups_hit": sum(hits),
        "reference_groups_total": len(groups),
        "reference_groups_coverage": sum(hits) / len(groups) if groups else None,
        "reference_group_hits": hits,
        "citation_page_ids": citations,
        "citation_in_context_hits": len(in_context),
        "citation_in_context_count": len(citations),
        "citation_in_context_rate": len(in_context) / len(citations) if citations else None,
        "citation_out_of_context_page_ids": [page_id for page_id in citations if page_id not in retrieved],
        "evaluation_note": "参照集合は非網羅。取得率・引用ID一致は意味的正しさや引用内容の裏付けを判定しない。引用数は重複を除いたページID数。",
    }


def latest_successes(records: list[dict]) -> dict[str, dict]:
    """Keep the latest successful attempt; later failures do not erase it."""
    result = {}
    ranks = {}
    for index, record in enumerate(records):
        task_id = record.get("task_id")
        if record.get("status") != "completed" or not isinstance(task_id, str):
            continue
        attempt = record.get("attempt", 0)
        rank = (attempt if isinstance(attempt, int) else 0, index)
        if task_id not in ranks or rank >= ranks[task_id]:
            result[task_id], ranks[task_id] = record, rank
    return result


def make_review_template(config: dict) -> dict:
    cases = {case["id"]: case for case in config["cases"]}
    return {
        "schema_version": 1,
        "run_id": config["run_id"],
        "status": "pending",
        "reviewer": "",
        "reviewed_at": "",
        "records": [
            {
                "task_id": task["task_id"],
                "answer_correct": None,
                "citations_supported": None,
                "abstention_ok": None if cases[task["case_id"]]["kind"] == "unanswerable" else "not_applicable",
                "notes": "",
            }
            for task in config["task_plan"]
        ],
        "observations": {name: "" for name in OBSERVATIONS},
    }


def _review_common_errors(review: object) -> list[str]:
    if not isinstance(review, dict):
        return ["人手確認はJSONオブジェクトで記入してください。"]
    errors = []
    if review.get("schema_version") != 1:
        errors.append("人手確認のschema_versionは1である必要があります。")
    if review.get("status") != "reviewed":
        errors.append("人手確認のstatusがreviewedになっていません。")
    for key in ("reviewer", "reviewed_at"):
        if not isinstance(review.get(key), str) or not review[key].strip():
            errors.append(f"人手確認の{key}を記入してください。")
    observations = review.get("observations")
    if not isinstance(observations, dict):
        errors.append("observationsをオブジェクトとして記入してください。")
    else:
        for key in OBSERVATIONS:
            if not isinstance(observations.get(key), str) or not observations[key].strip():
                errors.append(f"observations.{key}を記入してください。")
        q3 = observations.get("q3")
        if isinstance(q3, str) and len(q3) > 300:
            errors.append(f"Q3は300文字以内です（現在{len(q3)}文字）。")
    rows = review.get("records")
    if not isinstance(rows, list) or not rows:
        errors.append("recordsには各実行の人手判定が必要です。")
        return errors
    seen = set()
    for index, row in enumerate(rows):
        if not isinstance(row, dict):
            errors.append(f"records[{index}]はオブジェクトにしてください。")
            continue
        task_id = row.get("task_id")
        if not isinstance(task_id, str) or not task_id:
            errors.append(f"records[{index}]のtask_idがありません。")
        elif task_id in seen:
            errors.append(f"人手判定のtask_idが重複しています: {task_id}")
        else:
            seen.add(task_id)
        for key in ("answer_correct", "citations_supported"):
            if not isinstance(row.get(key), str) or row[key] not in VERDICTS:
                errors.append(f"{task_id}: {key}はpass / fail / unsureから選んでください。")
        if not isinstance(row.get("abstention_ok"), str) or row["abstention_ok"] not in VERDICTS | {"not_applicable"}:
            errors.append(f"{task_id}: abstention_okが未記入または不正です。")
        if not isinstance(row.get("notes"), str) or not row["notes"].strip():
            errors.append(f"{task_id}: 判断の根拠をnotesに記入してください。")
    return errors


def validate_review(config: dict, review: object) -> list[str]:
    """Validate completion of human review, not whether its judgments are true."""
    errors = _review_common_errors(review)
    if not isinstance(review, dict):
        return errors
    if review.get("run_id") != config.get("run_id"):
        errors.append("人手確認のrun_idが今回の実行と一致しません。")
    cases = {case["id"]: case for case in config["cases"]}
    plan = {task["task_id"]: task for task in config["task_plan"]}
    rows = review.get("records")
    if not isinstance(rows, list):
        return errors
    actual = {row.get("task_id") for row in rows if isinstance(row, dict) and isinstance(row.get("task_id"), str)}
    if set(plan) - actual:
        errors.append("人手判定が不足しています: " + ", ".join(sorted(set(plan) - actual)))
    if actual - set(plan):
        errors.append("計画にない人手判定があります: " + ", ".join(sorted(actual - set(plan))))
    for row in rows:
        if not isinstance(row, dict) or not isinstance(row.get("task_id"), str) or row["task_id"] not in plan:
            continue
        task = plan[row["task_id"]]
        unanswerable = cases[task["case_id"]]["kind"] == "unanswerable"
        allowed = VERDICTS if unanswerable else {"not_applicable"}
        if not isinstance(row.get("abstention_ok"), str) or row["abstention_ok"] not in allowed:
            choice = "pass / fail / unsure" if unanswerable else "not_applicable"
            errors.append(f"{task['task_id']}: abstention_okは{choice}にしてください。")
    return errors


def _number(value: object) -> bool:
    return isinstance(value, (int, float)) and not isinstance(value, bool) and math.isfinite(value) and value >= 0


def _fmt(value: object, places: int = 3, missing: str = "未取得") -> str:
    if not _number(value):
        return missing
    return f"{value:.{places}f}" if places else str(int(value))


def _cost(value: object) -> str:
    return "$" + _fmt(value, 6) if _number(value) else "算定不可"


def _cell(value: object) -> str:
    return str(value).replace("|", "\\|").replace("\r", "").replace("\n", " / ")


def _quoted(value: object) -> str:
    return "\n".join("> " + line for line in str(value).splitlines()) or "> （空欄）"


def _mean(values: list[object], places: int = 3) -> str:
    valid = [value for value in values if _number(value)]
    if not valid:
        return f"未取得（0/{len(values)}件）"
    return f"{statistics.fmean(valid):.{places}f}（{len(valid)}/{len(values)}件）"


def _sum(values: list[object], money: bool = False) -> str:
    valid = [value for value in values if _number(value)]
    if not valid:
        return f"{'算定不可' if money else '未取得'}（0/{len(values)}件）"
    label = _cost(sum(valid)) if money else _fmt(sum(valid), 0)
    prefix = "既知分 " if len(valid) != len(values) else ""
    return f"{prefix}{label}（{len(valid)}/{len(values)}件）"


def _successful_planned(config: dict, records: list[dict]) -> list[dict]:
    successes = latest_successes(records)
    return [successes[task["task_id"]] for task in config["task_plan"] if task["task_id"] in successes]


def _aggregate_table(config: dict, records: list[dict]) -> list[str]:
    completed = _successful_planned(config, records)
    lines = [
        "| 方式 | 完了/計画 | 平均総時間 秒（有効件数） | 入力tokens合計 | 出力tokens合計 | 思考tokens合計 | 生成API推定USD合計 |",
        "|---|---:|---:|---:|---:|---:|---:|",
    ]
    for method, title in METHODS.items():
        rows = [row for row in completed if row.get("method") == method]
        planned = sum(task["method"] == method for task in config["task_plan"])
        usage = [row.get("generation", {}).get("usage", {}) for row in rows]
        costs = [row.get("generation", {}).get("cost_estimate", {}).get("usd") for row in rows]
        lines.append("| " + " | ".join([
            title, f"{len(rows)}/{planned}", _mean([row.get("elapsed_seconds") for row in rows]),
            _sum([u.get("input_tokens") for u in usage]), _sum([u.get("output_tokens") for u in usage]),
            _sum([u.get("thinking_tokens") for u in usage]), _sum(costs, money=True),
        ]) + " |")
    lines += [
        "", "集計は各予定タスクの最新の成功試行のみ。括弧内は取得できた値の件数/成功件数で、欠測値は0に置き換えない。未完了なら方式間の集計対象も揃っていない。",
        "生成API推定費用は有料Standardの公表単価による概算で、請求額ではない。クエリ埋め込み・索引構築、失敗・再試行による追加消費、無料枠を含む総費用を表さない。出力と思考トークンは分けて記録し、料金では思考分も考慮する。",
    ]
    return lines


def _trial_table(config: dict, records: list[dict]) -> list[str]:
    successes = latest_successes(records)
    cases = {case["id"]: case for case in config["cases"]}
    lines = [
        "| 実行ID | 状態 | 総時間 秒 | 埋込/検索/生成 秒 | 参照グループ取得 | 引用IDの文脈内一致 | 生成API推定USD |",
        "|---|---|---:|---|---:|---:|---:|",
    ]
    for task in config["task_plan"]:
        row = successes.get(task["task_id"])
        if row is None:
            lines.append(f"| {task['task_id']} | 未完了 | — | — | — | — | — |")
            continue
        generation = row.get("generation", {})
        retrieval = row.get("retrieval", {})
        metrics = automated_metrics(cases[task["case_id"]], retrieval.get("pages", []), generation.get("answer", ""))
        groups = f"{metrics['reference_groups_hit']}/{metrics['reference_groups_total']}" if metrics["reference_groups_total"] else "対象外"
        citations = f"{metrics['citation_in_context_hits']}/{metrics['citation_in_context_count']}" if metrics["citation_in_context_count"] else "引用なし"
        breakdown = "/".join(_fmt(part.get("elapsed_seconds")) for part in [row.get("embedding", {}), retrieval, generation])
        lines.append(f"| {task['task_id']} | 完了・試行{row.get('attempt', '?')} | {_fmt(row.get('elapsed_seconds'))} | {breakdown} | {groups} | {citations} | {_cost(generation.get('cost_estimate', {}).get('usd'))} |")
    return lines


def _review_table(review: dict) -> list[str]:
    lines = [
        "| 実行ID | 回答の正しさ | 引用内容の裏付け | 回答保留 | 判断メモ |",
        "|---|---|---|---|---|",
    ]
    for row in review["records"]:
        lines.append("| " + " | ".join(_cell(row[key]) for key in (
            "task_id", "answer_correct", "citations_supported", "abstention_ok", "notes",
        )) + " |")
    return lines


def _conditions(config: dict) -> list[str]:
    repeated = isinstance(config.get("repeats"), int) and config["repeats"] >= 2
    order_note = (
        "実行順は質問ごとに方式を交互にし、次の反復では順を逆転。温度0でも回答や処理時間の一致は保証しない。"
        if repeated else
        "実行順は質問ごとに方式を交互にした。各問1回のため同じ質問の反復変動は確認できず、実行順の影響も十分には除けない。温度0でも回答や処理時間の一致は保証しない。"
    )
    return [
        f"- 実行ID：`{config.get('run_id', '不明')}`／開始：{config.get('started_at_jst', config.get('started_at_utc', '未取得'))}",
        f"- 対象：第1〜3回本講義の{config.get('corpus_pages', 214)}ページ。両方式で同じ資料・索引・埋め込みモデルを使用。",
        f"- 質問：{len(config['cases'])}問、各方式{config.get('repeats', '未記録')}回。1回答につき検索1回、生成API1回の比較。元のエージェントによるツール呼び出しループの比較ではない。",
        f"- 生成モデル：`{config.get('model', '未取得')}`／temperature={config.get('temperature', '未取得')}／出力上限={config.get('max_output_tokens', '未取得')}。共通の回答指示を使用。",
        f"- 返却本文：両方式{config.get('top_k', 5)}ページ。件数を揃え、ページの本文長や入力トークン数の違いは実測して記録。",
        "- 各試行で同じ原文の質問を独立に埋め込み、ベクトルのハッシュも記録。総時間は埋め込み・取得・生成を含み、環境準備と試行間の待機を除く。",
        "- " + order_note,
        "- 根拠ページ・期待事実・採点基準は事前登録した評価専用情報で、検索器や生成プロンプトに渡していない。",
        f"- 教材の参照コミット：`{config.get('upstream_commit', '未取得')}`。コード・資料のハッシュと実際の順番は`config.json`に記録。",
    ]


def _version_note(config: dict, records: list[dict]) -> str:
    rows = _successful_planned(config, records)
    versions = [row.get("generation", {}).get("model_version") for row in rows]
    known = [version for version in versions if isinstance(version, str) and version]
    distinct = sorted(set(known))
    detail = ", ".join(f"`{version}`" for version in distinct) or "未取得"
    note = f"応答で返されたmodel_version：{detail}（取得{len(known)}/{len(rows)}件）。"
    if len(distinct) > 1:
        note += "複数のモデル版が混在しているため、取得方式の差に加えてモデル版の変動が比較へ影響した可能性がある。"
    if len(known) < len(rows):
        note += "版が未取得の試行について同一版だったとは確認できない。"
    return note


def render_report(config: dict, records: list[dict], run_status: str, review: dict | None = None) -> str:
    successes = _successful_planned(config, records)
    total = len(config["task_plan"])
    complete = run_status == "completed" and len(successes) == total and total > 0
    errors = validate_review(config, review) if review is not None else ["人手確認は未実施です。"]
    lines = [
        "# Day5 比較実行レポート", "",
        f"**実行状態：{'実行完了' if complete else '未完了'}（{len(successes)}/{total}件）。人手確認：{'完了' if not errors else '未完了'}。**", "",
        f"記録された状態：`{run_status}`。全試行記録{len(records)}件。実行完了は、回答の正しさや発展課題の合格を意味しない。", "",
        "## 比較条件", "", *_conditions(config), "", _version_note(config, records), "",
        "## 成功試行の集計", "", *_aggregate_table(config, records), "",
        "## 予定タスク別の測定", "", *_trial_table(config, records), "",
        "参照グループ取得率は事前に選んだ非網羅的な根拠集合の代理指標。引用ID一致は、重複を除いた引用ページが取得本文に含まれるかの確認に限る。回答の正しさ・引用本文の裏付けは自動判定していない。資料に答えのない質問の参照取得率は対象外。", "",
        "## 質問と事前の確認基準", "",
    ]
    for case in config["cases"]:
        lines += [f"### {case['id']}：{case['kind']}", "", case["question"], ""]
        for group in case.get("reference_groups", []):
            lines.append(f"- {_cell(group['label'])}：{' または '.join(group['page_ids'])}。{group['expected_fact']}")
        if not case.get("reference_groups"):
            lines.append("- 根拠グループなし。資料に測定記録がないことを踏まえた回答保留を確認する。")
        lines += ["", "回答基準：", "", *[f"- {criterion}" for criterion in case.get("answer_criteria", [])], ""]
    lines += ["## 各試行の記録", ""]
    for index, record in enumerate(records, 1):
        generation = record.get("generation", {})
        retrieval = record.get("retrieval", {})
        lines += [
            f"### {index}. {record.get('task_id', '不明')}／試行{record.get('attempt', '?')}", "",
            f"- 状態：`{record.get('status', '不明')}`／段階：`{record.get('stage', '不明')}`／開始UTC：{record.get('started_at_utc', '未取得')}",
            f"- 総時間：{_fmt(record.get('elapsed_seconds'))}秒。埋め込み：{_fmt(record.get('embedding', {}).get('elapsed_seconds'))}秒／取得：{_fmt(retrieval.get('elapsed_seconds'))}秒／生成：{_fmt(generation.get('elapsed_seconds'))}秒。",
            f"- 生成要求数：{generation.get('request_count', '未取得')}／終了理由：{generation.get('finish_reason', '未取得')}／応答モデル版：{generation.get('model_version') or '未取得'}",
        ]
        usage = generation.get("usage", {})
        lines.append("- tokens：" + "、".join(f"{label}={_fmt(usage.get(key), 0)}" for label, key in [
            ("入力", "input_tokens"), ("出力", "output_tokens"), ("思考", "thinking_tokens"),
            ("キャッシュ入力", "cached_input_tokens"), ("合計", "total_tokens"),
        ]))
        cost = generation.get("cost_estimate", {})
        lines.append(f"- 生成API推定費用：{_cost(cost.get('usd'))}。{cost.get('reason') or cost.get('basis', '')}")
        if cost.get("assumptions"):
            lines.extend(f"  - 推定の仮定：{item}" for item in cost["assumptions"])
        if record.get("error"):
            lines += ["", "エラー記録：", "", _quoted(json.dumps(record["error"], ensure_ascii=False)), ""]
        lines += ["", "取得ページと経路：", "", "| 順位 | ページID | タイトル | 取得経路 |", "|---:|---|---|---|"]
        for rank, page in enumerate(retrieval.get("pages", []), 1):
            provenance = page.get("provenance", {})
            paths = provenance.get("paths", [])
            path_text = "; ".join(" → ".join(path.get("nodes", [])) for path in paths)
            details = f"{provenance.get('kind', '未記録')} / vector_rank={provenance.get('vector_rank', '?')}"
            lines.append(f"| {rank} | {_cell(_page_id(page))} | {_cell(page.get('title', ''))} | {_cell(details + (' / ' + path_text if path_text else ''))} |")
        trace = retrieval.get("trace", {})
        if trace:
            summary = {key: trace[key] for key in (
                "algorithm", "seed_page_ids", "query_terms", "ignored_query_terms", "limits",
                "relations_used", "relations_not_used", "candidate_count_before_cap",
                "candidate_count_after_cap", "weights", "rejected_cross_document_next_page_edges",
            ) if key in trace}
            lines += ["", "経路の要約：", "", _quoted(json.dumps(summary, ensure_ascii=False)), ""]
        answer = generation.get("answer")
        lines += ["", "回答：", "", _quoted(answer) if isinstance(answer, str) and answer else "回答未取得。", ""]
    lines += ["## 人手確認", ""]
    if errors:
        lines += ["人手確認は未完了。未確認の判定を正答として集計しない。", "", *[f"- {error}" for error in errors], ""]
    else:
        lines += [f"確認者：{review['reviewer']}／確認日：{review['reviewed_at']}", "", *_review_table(review), ""]
        labels = {
            "comparison_summary": "比較の観察", "improved_example": "改善・同等・悪化の具体例",
            "remaining_failure_or_limitation": "残る失敗・限界", "adoption_decision": "採否",
            "adoption_reason": "採否の理由", "q3": "Quri Q3",
        }
        for key, label in labels.items():
            lines += [f"### {label}", "", review["observations"][key], ""]
    lines += [
        "## 原記録", "",
        "- [実行設定と事前登録した評価基準](config.json)",
        "- [全試行・取得本文・完全な経路・応答・使用量](records.jsonl)",
        "- [人手確認用の参照ページ本文](reference_pages.json)",
        "- [人手判定と観察](human_review.json)", "",
        "実測していない値は未取得・算定不可として残す。未知の料金を0ドル、未知の判定を合格として扱わない。",
    ]
    return "\n".join(lines) + "\n"


def render_answer(config: dict, records: list[dict], review: dict, run_relative: str) -> str:
    errors = validate_review(config, review)
    if errors:
        raise ValueError("人手確認が未完了です: " + " / ".join(errors))
    rows = _successful_planned(config, records)
    if not config["task_plan"] or len(rows) != len(config["task_plan"]):
        raise ValueError("全予定タスクの成功記録が揃っていないため、提出本文を確定できません。")
    if any(not row.get("generation", {}).get("answer", "").strip() for row in rows):
        raise ValueError("回答本文のない成功記録があります。")
    relative = run_relative.rstrip("/")
    observations = review["observations"]
    lines = [
        "## 宿題", "", "### 取り組んだレベルと目的", "",
        "**発展**。基本RAGと、質問中の用語を手がかりに候補を選ぶGraph取得を実装・比較した。単一ページ、複数ページ、講義をまたぐ説明、資料に答えがない質問の4種類を事前に定め、根拠の取得と回答・引用を分けて確認した。", "",
        "### データの構造・検索方法・選択理由", "",
        "教材の1ページを1チャンクとして、講義ID・章・PDFページ・本文・768次元の埋め込みを保持する。ページ間の前後関係と、ページから用語への出現関係を用いたグラフを扱う。本文は両方式とも同じ第1〜3回本講義214ページを対象とする。", "",
        "基本RAGはコサイン距離の上位5ページを取得する。配布SQLiteのベクトルを標準ライブラリで読み、元のsqlite-vecと同じ距離順を再現する実装のため、浮動小数点の丸め差で同点付近の順が変わり得る。", "",
        "改良Graphは基本RAGの候補と、上位3ページから最大2hopでたどった候補を合わせる。同じ資料の前後ページ、またはページ→質問に含まれる用語→別ページを使う。32ページを超えて出現する用語は展開せず、追加候補をベクトル順位50位以内・候補集合24件以内に絞る。最上位のベクトル検索結果を残し、関連度0.72・未充足の質問用語0.23・重複への減点0.05で順に選び、返す本文を5ページに揃える。", "",
        "章や講義をまたぐ関連情報を補いながら、一般的な用語による過大な候補増加を抑えるためにこの設計を選んだ。重み・上限は設計時の固定値で、この4問の実行結果に合わせて学習・最適化した値ではない。関係があることだけでは回答の根拠にならないため、取得本文を別に確認する。", "",
        "### 実験条件", "", *_conditions(config), "", _version_note(config, records), "",
        "### 測定結果", "", *_aggregate_table(config, records), "", *_trial_table(config, records), "",
        "参照グループ取得率は非網羅的な事前参照集合に対する代理指標である。引用ID一致は本文が文脈に含まれるかを確認するだけで、意味的正しさを保証しない。資料に答えのないq4は根拠取得率を対象外とし、回答保留を人が評価した。", "",
        "### 回答と引用の人手確認", "",
        f"確認者：{review['reviewer']}／確認日：{review['reviewed_at']}。pass / fail / unsureを使い、判断できない項目を合格へ置き換えない。", "",
        *_review_table(review), "",
        "### 比較からの観察", "", observations["comparison_summary"], "",
        "### 改善・同等・悪化の具体例", "", observations["improved_example"], "",
        "### 残る失敗と限界", "", observations["remaining_failure_or_limitation"], "",
        "### 自分の用途に採用するか", "", observations["adoption_decision"], "", observations["adoption_reason"], "",
        "### 再現性とAI支援", "",
        "実装・比較設計・文章整理にAI支援を用いた。実行ログに保存された測定値と人手確認欄の観察を分けて記録している。4問の小規模な比較なので、方式全体の優位性や一般的な正答率を断定しない。APIエラーや再試行も原記録に残し、成功試行だけの集計を請求総額とは扱わない。", "",
        f"- [各回答・取得ページ・経路・使用量・費用の比較レポート]({relative}/report.md)",
        f"- [実行設定・コード版・データ版・事前登録した質問]({relative}/config.json)",
        f"- [全試行の原記録]({relative}/records.jsonl)",
        f"- [人手判定と観察の原記録]({relative}/human_review.json)",
        f"- [講座の課題説明](https://github.com/matsuolab/lecture-ai-engineering-2026/blob/{config.get('upstream_commit', 'main')}/lectures/05/problem.md)",
    ]
    return "\n".join(lines) + "\n"


def quri_text(review: dict) -> str:
    """Render Quri text after validate_review(config, review) has succeeded."""
    errors = _review_common_errors(review)
    if errors:
        raise ValueError("人手確認が未完了です: " + " / ".join(errors))
    q3 = review["observations"]["q3"]
    return (
        "# Day5 Quri入力用\n\n## Q1\n\n発展｜Advanced\n\n## Q2\n\n"
        + REPOSITORY_URL + "\n\n## Q3（" + str(len(q3)) + "文字／300文字以内）\n\n"
        + q3 + "\n"
    )
