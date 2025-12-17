
import argparse
import csv
from typing import List

from recommendation_engine import AssessmentRecommendationEngine


def load_test_queries(path: str, query_id_col: str = "query_id", query_col: str = "query"):
    """Load test queries from CSV; returns list of (query_id, query_text)."""
    items = []
    with open(path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            qid = (row.get(query_id_col) or "").strip()
            text = (row.get(query_col) or "").strip()
            if qid and text:
                items.append((qid, text))
    return items


def write_predictions(
    path: str,
    predictions: List[tuple],
) -> None:
    with open(path, "w", encoding="utf-8", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["query_id", "rank", "assessment_id"])
        for qid, rank, aid in predictions:
            writer.writerow([qid, rank, aid])


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Generate predictions for unlabeled test queries."
    )
    parser.add_argument(
        "--test",
        required=True,
        help="Path to unlabeled test CSV file.",
    )
    parser.add_argument(
        "--output",
        required=True,
        help="Path to output predictions CSV file.",
    )
    parser.add_argument(
        "--catalogue",
        default="product_catalogue.json",
        help="Path to product catalogue JSON file (default: product_catalogue.json).",
    )
    parser.add_argument(
        "--k",
        type=int,
        default=10,
        help="Number of recommendations per query (default: 10).",
    )
    parser.add_argument(
        "--query-id-col",
        default="query_id",
        help="Column name for query ID in test CSV (default: query_id).",
    )
    parser.add_argument(
        "--query-col",
        default="query",
        help="Column name for query text in test CSV (default: query).",
    )

    args = parser.parse_args()

    engine = AssessmentRecommendationEngine(args.catalogue)
    test_queries = load_test_queries(
        args.test,
        query_id_col=args.query_id_col,
        query_col=args.query_col,
    )

    if not test_queries:
        print("[ERROR] No test queries loaded. Check your file and column names.")
        return 1

    predictions: List[tuple] = []

    for qid, text in test_queries:
        recs = engine.recommend_from_text(text, top_n=args.k)
        for rank, rec in enumerate(recs, start=1):
            aid = rec.get("id")
            if not aid:
                continue
            predictions.append((qid, rank, aid))

    write_predictions(args.output, predictions)
    print(f"[INFO] Wrote {len(predictions)} prediction rows to {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())


