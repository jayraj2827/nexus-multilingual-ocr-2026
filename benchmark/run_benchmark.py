"""
CLI Runner for NexusOCR Benchmark Suite.
Generates synthetic PDFs if needed, executes profiling, and prints a formatted Markdown table.
"""

from pathlib import Path
from tabulate import tabulate
from benchmark.harness import BenchmarkHarness
import config


def run_full_benchmark():
    print("=" * 60)
    print("      NexusOCR Empirical Benchmark Evaluation")
    print("=" * 60)

    test_dir = config.BENCHMARK_DIR
    harness = BenchmarkHarness(use_gpu=False)

    print("\n[1/3] Ensuring benchmark test dataset is available...")
    harness.create_synthetic_test_pdfs(test_dir)

    pdf_files = list(test_dir.glob("*.pdf"))
    print(f"Found {len(pdf_files)} test documents in benchmark suite.\n")

    results_table = []
    print("[2/3] Running OCR pipeline across test corpus...")

    for pdf_path in pdf_files:
        print(f" -> Testing: {pdf_path.name}...")
        profile = harness.run_single_test(str(pdf_path))
        results_table.append([
            profile.document_name,
            profile.total_pages,
            f"{profile.latency_ms:.1f} ms",
            f"{profile.latency_per_page_ms:.1f} ms",
            f"{profile.peak_rss_mb:.1f} MB",
            f"{profile.cer * 100.0:.2f}%"
        ])

    print("\n[3/3] Benchmark Execution Complete!\n")
    headers = ["Document", "Pages", "Total Latency", "Latency / Page", "Peak RAM", "CER"]
    print(tabulate(results_table, headers=headers, tablefmt="github"))


if __name__ == "__main__":
    run_full_benchmark()
