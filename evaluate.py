"""
Evaluate the recommendation engine using Mean Recall@K.

This script loads a labeled query dataset, runs text-based recommendations
for each query, and computes Mean Recall@K as described in the assignment:

Recall@K for a query i:
    (# relevant assessments in top K) / (total relevant assessments for query i)

MeanRecall@K:
    (1 / N) * sum_i Recall@K_i, where N is the number of queries.

Expected labeled file format (CSV):
    query_id,query,relevant_ids
    1,"I am hiring for Java developers ...","OPQ32|G+|Verify-IT"

You can change the separator and column names via CLI arguments.
"""

import argparse
import csv
from typing import List, Set, Tuple

from recommendation_engine import AssessmentRecommendationEngine


def load_labeled_queries(
    path: str,
    query_col: str = "query",
    relevant_col: str = "relevant_ids",
    sep: str = "|",
) -> List[Tuple[str, Set[str]]]:
    """
    Load labeled queries and relevant assessment IDs from a CSV file.

    Returns a list of (query_text, relevant_ids_set).
    """
    queries: List[Tuple[str, Set[str]]] = []
    with open(path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            query_text = (row.get(query_col) or "").strip()
            raw_ids = row.get(relevant_col) or ""
            relevant_ids = {
                rid.strip()
                for rid in raw_ids.split(sep)
                if rid.strip()
            }
            if query_text and relevant_ids:
                queries.append((query_text, relevant_ids))
    return queries


def recall_at_k(
    predicted_ids: List[str],
    relevant_ids: Set[str],
    k: int,
) -> float:
    """Compute Recall@K for a single query."""
    if not relevant_ids:
        return 0.0
    top_k = predicted_ids[:k]
    hits = sum(1 for pid in top_k if pid in relevant_ids)
    return hits / float(len(relevant_ids))


def compute_mean_recall_at_k(
    engine: AssessmentRecommendationEngine,
    labeled_queries: List[Tuple[str, Set[str]]],
    k: int,
) -> float:
    """Compute Mean Recall@K over all labeled queries."""
    if not labeled_queries:
        return 0.0

    recalls = []
    for idx, (query_text, relevant_ids) in enumerate(labeled_queries, start=1):
        recs = engine.recommend_from_text(query_text, top_n=k)
        predicted_ids = [r.get("id") for r in recs if r.get("id")]
        r_at_k = recall_at_k(predicted_ids, relevant_ids, k)
        recalls.append(r_at_k)
        print(f"[INFO] Query {idx}: Recall@{k} = {r_at_k:.3f}")

    mean_recall = sum(recalls) / float(len(recalls))
    return mean_recall


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Evaluate SHL recommendation engine using Mean Recall@K",
    )
    parser.add_argument(
        "--labels",
        required=True,
        help="Path to labeled CSV file (with query and relevant IDs).",
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
        help="K for Recall@K (default: 10).",
    )
    parser.add_argument(
        "--query-col",
        default="query",
        help="Column name for query text (default: query).",
    )
    parser.add_argument(
        "--relevant-col",
        default="relevant_ids",
        help="Column name for relevant IDs (default: relevant_ids).",
    )
    parser.add_argument(
        "--sep",
        default="|",
        help="Separator for multiple relevant IDs in the relevant_ids column (default: |).",
    )

    args = parser.parse_args()

    engine = AssessmentRecommendationEngine(args.catalogue)
    labeled = load_labeled_queries(
        args.labels,
        query_col=args.query_col,
        relevant_col=args.relevant_col,
        sep=args.sep,
    )

    if not labeled:
        print("[ERROR] No labeled queries loaded. Check your file and column names.")
        return 1

    mean_recall = compute_mean_recall_at_k(engine, labeled, args.k)
    print(
        f"\nMean Recall@{args.k} over {len(labeled)} queries: {mean_recall:.4f}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())


