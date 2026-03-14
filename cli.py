"""
CLI interface for SRS/SDD RAG Generator
Usage:
  python cli.py ingest <file_path> --collection <collection_name>
  python cli.py generate --type srs --project "My Project" --req requirements.txt
  python cli.py search "functional requirements for radar"
  python cli.py stats
"""

import argparse
import sys
import os

# Import from main app
from app import (
    ingest_document, generate_document, retrieve_context,
    save_as_docx, collections, OUTPUT_DIR
)


def cmd_ingest(args):
    """Ingest a document into a collection"""
    if not os.path.exists(args.file):
        print(f"Error: File not found: {args.file}")
        sys.exit(1)

    print(f"Ingesting: {args.file} → {args.collection}")
    chunks = ingest_document(args.file, args.collection)
    print(f"✓ Created {chunks} chunks in '{args.collection}'")


def cmd_ingest_dir(args):
    """Ingest all documents in a directory"""
    if not os.path.isdir(args.directory):
        print(f"Error: Directory not found: {args.directory}")
        sys.exit(1)

    extensions = {".docx", ".pdf", ".txt", ".md"}
    files = [
        os.path.join(args.directory, f)
        for f in os.listdir(args.directory)
        if os.path.splitext(f)[1].lower() in extensions
    ]

    print(f"Found {len(files)} documents in {args.directory}")
    total_chunks = 0

    for filepath in sorted(files):
        try:
            chunks = ingest_document(filepath, args.collection)
            total_chunks += chunks
            print(f"  ✓ {os.path.basename(filepath)} → {chunks} chunks")
        except Exception as e:
            print(f"  ✗ {os.path.basename(filepath)} → {e}")

    print(f"\nTotal: {total_chunks} chunks ingested into '{args.collection}'")


def cmd_generate(args):
    """Generate an SRS or SDD document"""
    # Read requirements from file or use direct text
    if args.req_file and os.path.exists(args.req_file):
        with open(args.req_file, "r") as f:
            requirements = f.read()
    elif args.requirements:
        requirements = args.requirements
    else:
        print("Error: Provide --requirements or --req-file")
        sys.exit(1)

    instructions = args.instructions or ""

    print(f"\nGenerating {args.type.upper()} for: {args.project}")
    print(f"Requirements length: {len(requirements)} chars")
    print("Retrieving context from knowledge base...")
    print("Sending to Ollama (this may take a few minutes)...\n")

    result = generate_document(
        doc_type=args.type,
        project_name=args.project,
        requirements_text=requirements,
        specific_instructions=instructions
    )

    # Print to console
    print("=" * 60)
    print(result)
    print("=" * 60)

    # Save files
    md_path = os.path.join(OUTPUT_DIR, f"{args.project.replace(' ', '_')}_{args.type.upper()}.md")
    docx_path = os.path.join(OUTPUT_DIR, f"{args.project.replace(' ', '_')}_{args.type.upper()}.docx")

    with open(md_path, "w") as f:
        f.write(result)

    save_as_docx(result, docx_path, title=f"{args.project} - {args.type.upper()}")

    print(f"\n✓ Saved: {md_path}")
    print(f"✓ Saved: {docx_path}")


def cmd_search(args):
    """Search the knowledge base"""
    results = retrieve_context(args.query, n_results=args.n)

    print(f"\nSearch: '{args.query}' ({len(results)} results)\n")
    for i, r in enumerate(results):
        print(f"--- Result {i+1} (distance: {r['distance']:.3f}) ---")
        print(f"Source: {r['metadata'].get('source_file', 'Unknown')}")
        print(f"Section: {r['metadata'].get('section_heading', 'N/A')}")
        print(f"Collection: {r['collection']}")
        print(f"Text: {r['text'][:300]}...")
        print()


def cmd_stats(args):
    """Show collection statistics"""
    print("\nCollection Statistics:")
    print("-" * 50)
    total = 0
    for name, coll in collections.items():
        count = coll.count()
        total += count
        print(f"  {name:<20} {count:>6} chunks")
    print("-" * 50)
    print(f"  {'TOTAL':<20} {total:>6} chunks\n")


def main():
    parser = argparse.ArgumentParser(
        description="SRS/SDD RAG Generator CLI",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    subparsers = parser.add_subparsers(dest="command")

    # Ingest single file
    p_ingest = subparsers.add_parser("ingest", help="Ingest a document")
    p_ingest.add_argument("file", help="Path to document")
    p_ingest.add_argument("--collection", "-c", required=True,
                          choices=list(collections.keys()),
                          help="Target collection")

    # Ingest directory
    p_ingest_dir = subparsers.add_parser("ingest-dir", help="Ingest all docs in a directory")
    p_ingest_dir.add_argument("directory", help="Path to directory")
    p_ingest_dir.add_argument("--collection", "-c", required=True,
                              choices=list(collections.keys()),
                              help="Target collection")

    # Generate
    p_gen = subparsers.add_parser("generate", help="Generate SRS/SDD")
    p_gen.add_argument("--type", "-t", required=True, choices=["srs", "sdd"])
    p_gen.add_argument("--project", "-p", required=True, help="Project name")
    p_gen.add_argument("--requirements", "-r", help="Requirements text")
    p_gen.add_argument("--req-file", "-f", help="Path to requirements file")
    p_gen.add_argument("--instructions", "-i", help="Additional instructions")

    # Search
    p_search = subparsers.add_parser("search", help="Search knowledge base")
    p_search.add_argument("query", help="Search query")
    p_search.add_argument("-n", type=int, default=5, help="Number of results")

    # Stats
    subparsers.add_parser("stats", help="Show collection statistics")

    args = parser.parse_args()

    commands = {
        "ingest": cmd_ingest,
        "ingest-dir": cmd_ingest_dir,
        "generate": cmd_generate,
        "search": cmd_search,
        "stats": cmd_stats,
    }

    if args.command in commands:
        commands[args.command](args)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
