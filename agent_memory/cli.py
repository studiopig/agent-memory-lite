"""CLI entry point for Agent Memory Lite."""
import argparse


def main():
    parser = argparse.ArgumentParser(
        prog="agent-memory",
        description="Agent Memory Lite — lightweight long-term memory for AI agents",
    )
    sub = parser.add_subparsers(dest="command")

    serve_parser = sub.add_parser("serve", help="Start MCP server")
    serve_parser.add_argument("--storage", default="./agent_memory",
                              help="SQLite database directory (env: MEMORY_STORAGE)")
    serve_parser.add_argument("--model", default="sentence-transformers/all-MiniLM-L6-v2",
                              help="Embedding model name (env: MEMORY_MODEL)")

    args = parser.parse_args()

    if args.command == "serve":
        from .server import serve
        serve(storage=args.storage, model=args.model)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
