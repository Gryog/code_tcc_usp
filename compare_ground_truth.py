import argparse
import json
import re
from glob import glob
from typing import Dict, Iterable, List, Tuple

from tests.testes_sinteticos import gerar_dataset_sintetico


def _load_results(paths: Iterable[str]) -> List[dict]:
    results: List[dict] = []
    for pattern in paths:
        for path in glob(pattern):
            with open(path, "r", encoding="utf-8") as handle:
                payload = json.load(handle)
                if isinstance(payload, dict) and "results" in payload:
                    results.extend(payload["results"])
                elif isinstance(payload, list):
                    results.extend(payload)
                else:
                    raise ValueError(f"Formato inesperado em {path}")
    return results


def _extract_id(file_path: str) -> str:
    if not file_path:
        return ""
    match = re.search(r"([A-Z]+_\d+)", file_path)
    if match:
        return match.group(1)
    match = re.search(r"\b([A-Za-z0-9_-]+)\b$", file_path)
    return match.group(1) if match else file_path


def _build_synthetic_ground_truth() -> Dict[str, dict]:
    dataset = gerar_dataset_sintetico()
    expected_by_id: Dict[str, dict] = {}
    for category, examples in dataset["categories"].items():
        for example in examples:
            expected_status = "pass"
            if category == "medium":
                expected_status = "warning"
            elif category == "poor":
                expected_status = "fail"
            expected_by_id[example["id"]] = {
                "expected_score_min": example.get("expected_score_min"),
                "expected_score_max": example.get("expected_score_max"),
                "expected_keywords": example.get("expected_keywords", []),
                "expected_violations": example.get("expected_violations", []),
                "expected_status": expected_status,
                "expected_category": category,
            }
    return expected_by_id


def _build_repo_ground_truth(path: str) -> Dict[str, dict]:
    with open(path, "r", encoding="utf-8") as handle:
        data = json.load(handle)
    expected_by_id: Dict[str, dict] = {}
    for entry in data:
        metadata = entry.get("metadata", {})
        expected_by_id[entry["id"]] = {
            "expected_score_min": metadata.get("expected_score_min"),
            "expected_score_max": metadata.get("expected_score_max"),
            "expected_keywords": metadata.get("expected_keywords", []),
            "expected_violations": metadata.get("expected_violations", []),
            "expected_category": metadata.get("expected_category"),
            "expected_status": metadata.get("expected_status"),
        }
    return expected_by_id


def _collect_llm_text(result: dict) -> str:
    texts: List[str] = []
    texts.append(result.get("summary", ""))
    for violation in result.get("violations", []):
        texts.append(violation.get("description", ""))
        texts.append(violation.get("suggestion", ""))
    return " ".join(texts).lower()


def _match_expected_violations(result: dict, expected_violations: List[str]) -> Tuple[int, int]:
    if not expected_violations:
        return 0, 0
    expected = [v.lower() for v in expected_violations]
    found = 0
    for expected_item in expected:
        for violation in result.get("violations", []):
            if expected_item in violation.get("rule_category", "").lower():
                found += 1
                break
            if expected_item in violation.get("check_failed", "").lower():
                found += 1
                break
    return found, len(expected)


def _compare_results(results: List[dict], ground_truth: Dict[str, dict]) -> dict:
    totals = {
        "matched": 0,
        "missing": 0,
        "score_matches": 0,
        "status_matches": 0,
        "status_total": 0,
        "score_total": 0,
        "expected_violation_hits": 0,
        "expected_violation_total": 0,
        "keyword_examples": 0,
        "keyword_example_hits": 0,
        "keyword_hits": 0,
        "keyword_total": 0,
    }
    missing_ids = []

    for result in results:
        result_id = result.get("file_path") or result.get("id")
        result_id = _extract_id(result_id)
        expected = ground_truth.get(result_id)
        if not expected:
            totals["missing"] += 1
            missing_ids.append(result_id)
            continue

        totals["matched"] += 1
        score = result.get("overall_score", result.get("score"))
        score_min = expected.get("expected_score_min")
        score_max = expected.get("expected_score_max")
        if score is not None and score_min is not None and score_max is not None:
            totals["score_total"] += 1
            if score_min <= score <= score_max:
                totals["score_matches"] += 1

        expected_status = expected.get("expected_status")
        if expected_status:
            totals["status_total"] += 1
            if result.get("overall_status") == expected_status:
                totals["status_matches"] += 1

        found, expected_total = _match_expected_violations(
            result, expected.get("expected_violations", [])
        )
        totals["expected_violation_hits"] += found
        totals["expected_violation_total"] += expected_total

        expected_keywords = expected.get("expected_keywords", [])
        if expected_keywords:
            totals["keyword_examples"] += 1
            llm_text = _collect_llm_text(result)
            hits = sum(1 for k in expected_keywords if k.lower() in llm_text)
            if hits:
                totals["keyword_example_hits"] += 1
            totals["keyword_hits"] += hits
            totals["keyword_total"] += len(expected_keywords)

    score_accuracy = (
        totals["score_matches"] / totals["score_total"] * 100
        if totals["score_total"]
        else 0
    )
    status_accuracy = (
        totals["status_matches"] / totals["status_total"] * 100
        if totals["status_total"]
        else 0
    )
    violation_recall = (
        totals["expected_violation_hits"] / totals["expected_violation_total"] * 100
        if totals["expected_violation_total"]
        else 0
    )
    keyword_example_recall = (
        totals["keyword_example_hits"] / totals["keyword_examples"] * 100
        if totals["keyword_examples"]
        else 0
    )
    keyword_token_recall = (
        totals["keyword_hits"] / totals["keyword_total"] * 100
        if totals["keyword_total"]
        else 0
    )

    return {
        "summary": {
            "total_results": len(results),
            "matched_results": totals["matched"],
            "missing_ground_truth": totals["missing"],
            "score_accuracy": round(score_accuracy, 2),
            "status_accuracy": round(status_accuracy, 2),
            "violation_recall": round(violation_recall, 2),
            "keyword_example_recall": round(keyword_example_recall, 2),
            "keyword_token_recall": round(keyword_token_recall, 2),
        },
        "details": {
            "score_total": totals["score_total"],
            "status_total": totals["status_total"],
            "expected_violation_total": totals["expected_violation_total"],
            "keyword_examples": totals["keyword_examples"],
            "keyword_total": totals["keyword_total"],
            "missing_ids": missing_ids,
        },
    }


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Compara resultados dos LLMs com ground truth (sintéticos ou repositórios)."
    )
    parser.add_argument(
        "--results",
        nargs="+",
        required=True,
        help="Arquivos JSON de resultados ou glob patterns.",
    )
    parser.add_argument(
        "--ground-truth",
        choices=["synthetic", "repo"],
        required=True,
        help="Tipo de ground truth a usar.",
    )
    parser.add_argument(
        "--ground-truth-file",
        default="tests/repo_endpoints.json",
        help="Arquivo JSON de ground truth para repos (default: tests/repo_endpoints.json).",
    )
    parser.add_argument(
        "--output",
        help="Caminho para salvar o relatório em JSON.",
    )
    args = parser.parse_args()

    results = _load_results(args.results)
    if args.ground_truth == "synthetic":
        ground_truth = _build_synthetic_ground_truth()
    else:
        ground_truth = _build_repo_ground_truth(args.ground_truth_file)

    report = _compare_results(results, ground_truth)

    print("=== Comparação com Ground Truth ===")
    print(json.dumps(report["summary"], indent=2, ensure_ascii=False))
    if report["details"]["missing_ids"]:
        print("\nIDs sem ground truth (amostra):")
        print(report["details"]["missing_ids"][:10])

    if args.output:
        with open(args.output, "w", encoding="utf-8") as handle:
            json.dump(report, handle, indent=2, ensure_ascii=False)
        print(f"\nRelatório salvo em: {args.output}")


if __name__ == "__main__":
    main()