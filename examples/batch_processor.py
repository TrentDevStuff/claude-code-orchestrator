#!/usr/bin/env python3
"""
Batch Document Processor Example

Demonstrates:
- Batch processing of multiple documents
- Parallel execution using worker pool
- Progress tracking
- Error handling for partial failures
- Cost optimization with model selection
"""

import sys
sys.path.append('..')

import time
from pathlib import Path
from client.claude_client import ClaudeClient, Model, BatchResponse


# Sample documents to process
SAMPLE_DOCUMENTS = [
    """
    Title: Introduction to Python
    Python is a high-level, interpreted programming language known for its
    simplicity and readability. It was created by Guido van Rossum and first
    released in 1991. Python emphasizes code readability with its use of
    significant indentation.
    """,
    """
    Title: Machine Learning Basics
    Machine learning is a branch of artificial intelligence that focuses on
    building systems that can learn from data. It uses algorithms to identify
    patterns and make decisions with minimal human intervention. Common types
    include supervised learning, unsupervised learning, and reinforcement learning.
    """,
    """
    Title: Web Development Overview
    Web development involves building and maintaining websites. It includes
    aspects such as web design, web programming, and database management.
    Modern web development typically involves front-end technologies like HTML,
    CSS, and JavaScript, and back-end technologies like Python, Node.js, or PHP.
    """,
    """
    Title: Cloud Computing Explained
    Cloud computing delivers computing services over the internet, including
    storage, processing power, and applications. Major providers include AWS,
    Azure, and Google Cloud. Benefits include scalability, cost-efficiency,
    and accessibility from anywhere with an internet connection.
    """,
    """
    Title: Database Fundamentals
    Databases are organized collections of structured information or data.
    They can be relational (SQL) or non-relational (NoSQL). SQL databases like
    PostgreSQL and MySQL use structured query language, while NoSQL databases
    like MongoDB offer more flexibility in data structure.
    """
]


def process_documents_batch(documents: list, model: Model = Model.HAIKU):
    """
    Process multiple documents in batch using the Claude API.

    Args:
        documents: List of document texts to process
        model: Model to use for processing (Haiku recommended for cost)

    Returns:
        Tuple of (results, statistics)
    """
    print(f"Processing {len(documents)} documents with model: {model.value}")
    print()

    # Initialize client
    with ClaudeClient(project_id="batch-processor", timeout=60.0) as client:
        # Check API health
        health = client.health()
        print(f"✓ API Status: {health['status']}")
        print()

        # Create prompts for each document
        prompts = [
            f"Summarize this document in 2-3 sentences:\\n\\n{doc.strip()}"
            for doc in documents
        ]

        # Start timer
        start_time = time.time()

        # Submit batch request
        print("Submitting batch request...")
        try:
            batch_response = client.batch(
                prompts=prompts,
                model=model,
                timeout=60.0  # Per-document timeout
            )
        except Exception as e:
            print(f"❌ Batch request failed: {e}")
            return None, None

        # Calculate elapsed time
        elapsed = time.time() - start_time

        # Display results
        print()
        print("=" * 70)
        print("BATCH RESULTS")
        print("=" * 70)
        print()

        print(f"Status: {batch_response.completed}/{batch_response.total} completed")
        if batch_response.failed > 0:
            print(f"Failed: {batch_response.failed} documents")
        print()

        print(f"Processing time: {elapsed:.2f}s")
        print(f"Average per document: {elapsed / len(documents):.2f}s")
        print()

        print(f"Total cost: ${batch_response.total_cost:.4f}")
        print(f"Total tokens: {batch_response.total_tokens:,}")
        print(f"Average cost per document: ${batch_response.total_cost / len(documents):.4f}")
        print()

        # Display individual results
        print("-" * 70)
        print("DOCUMENT SUMMARIES")
        print("-" * 70)
        print()

        for i, result in enumerate(batch_response.results, 1):
            print(f"Document {i}:")
            print()

            if result.status == "completed":
                # Extract title from original document
                lines = documents[i-1].strip().split('\\n')
                title = lines[0].replace("Title:", "").strip() if lines else "Untitled"
                print(f"  Title: {title}")
                print(f"  Summary: {result.content}")
                print(f"  Tokens: {result.usage.total_tokens if result.usage else 'N/A'}")
                print(f"  Cost: ${result.cost:.6f}" if result.cost else "  Cost: N/A")
            else:
                print(f"  Status: FAILED")
                print(f"  Error: {result.error}")

            print()

        return batch_response, {
            "elapsed_time": elapsed,
            "avg_time_per_doc": elapsed / len(documents),
            "success_rate": (batch_response.completed / batch_response.total) * 100
        }


def compare_models(documents: list):
    """
    Compare different models for batch processing.

    Args:
        documents: List of documents to process
    """
    print("=" * 70)
    print("MODEL COMPARISON")
    print("=" * 70)
    print()

    models = [Model.HAIKU, Model.SONNET]
    results = {}

    for model in models:
        print(f"\\nTesting {model.value.upper()}...")
        print("-" * 70)

        batch_response, stats = process_documents_batch(documents, model)

        if batch_response and stats:
            results[model.value] = {
                "cost": batch_response.total_cost,
                "time": stats["elapsed_time"],
                "tokens": batch_response.total_tokens,
                "success_rate": stats["success_rate"]
            }

        # Brief pause between models
        time.sleep(1)

    # Summary comparison
    if results:
        print()
        print("=" * 70)
        print("COMPARISON SUMMARY")
        print("=" * 70)
        print()

        print(f"{'Model':<10} {'Cost':>12} {'Time':>10} {'Tokens':>12} {'Success':>10}")
        print("-" * 70)

        for model_name, data in results.items():
            print(f"{model_name:<10} ${data['cost']:>11.4f} {data['time']:>9.2f}s "
                  f"{data['tokens']:>11,} {data['success_rate']:>9.1f}%")

        print()

        # Cost comparison
        if "haiku" in results and "sonnet" in results:
            haiku_cost = results["haiku"]["cost"]
            sonnet_cost = results["sonnet"]["cost"]
            savings = ((sonnet_cost - haiku_cost) / sonnet_cost) * 100

            print(f"Cost savings using Haiku: {savings:.1f}%")
            print(f"Haiku is {sonnet_cost / haiku_cost:.1f}x cheaper than Sonnet")
        print()


def process_directory(directory_path: str):
    """
    Process all text files in a directory.

    Args:
        directory_path: Path to directory containing text files
    """
    path = Path(directory_path)

    if not path.exists():
        print(f"Error: Directory not found: {directory_path}")
        return

    # Find all text files
    text_files = list(path.glob("*.txt"))

    if not text_files:
        print(f"No .txt files found in {directory_path}")
        return

    print(f"Found {len(text_files)} text files")
    print()

    # Read file contents
    documents = []
    for file_path in text_files:
        try:
            content = file_path.read_text()
            documents.append(content)
        except Exception as e:
            print(f"Warning: Could not read {file_path.name}: {e}")

    if documents:
        process_documents_batch(documents, model=Model.HAIKU)


def main():
    """Main entry point."""
    print("=" * 70)
    print("Claude Code API - Batch Document Processor")
    print("=" * 70)
    print()

    print("Options:")
    print("  1. Process sample documents (Haiku)")
    print("  2. Compare models (Haiku vs Sonnet)")
    print("  3. Process directory of text files")
    print()

    choice = input("Select option (1-3): ").strip()

    if choice == "1":
        print()
        process_documents_batch(SAMPLE_DOCUMENTS, model=Model.HAIKU)

    elif choice == "2":
        print()
        compare_models(SAMPLE_DOCUMENTS)

    elif choice == "3":
        print()
        directory = input("Enter directory path: ").strip()
        print()
        process_directory(directory)

    else:
        print("Invalid choice")
        return

    # Show final usage statistics
    print()
    print("=" * 70)
    print("PROJECT USAGE STATISTICS")
    print("=" * 70)
    print()

    try:
        with ClaudeClient(project_id="batch-processor") as client:
            stats = client.get_usage(period="month")

            print(f"Project: {stats.project_id}")
            print(f"Total tokens: {stats.total_tokens:,}")
            print(f"Total cost: ${stats.total_cost:.4f}")

            if stats.limit:
                usage_pct = (stats.total_tokens / stats.limit) * 100
                print(f"Budget usage: {usage_pct:.1f}%")
                print(f"Remaining: {stats.remaining:,} tokens")

            print()
            print("By model:")
            for model_name, model_stats in stats.by_model.items():
                print(f"  {model_name}: {model_stats['tokens']:,} tokens, ${model_stats['cost']:.4f}")

    except Exception as e:
        print(f"Could not retrieve usage statistics: {e}")

    print()


if __name__ == "__main__":
    main()
