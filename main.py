"""
main.py
Entry point for IndusDiag — AI-powered industrial sensor diagnostics agent.

Usage:
    python main.py                              # runs default sample
    python main.py --file data/samples/conveyor_motor_overheat.csv --asset ConveyorMotorA
    python main.py --file data/samples/sensor_spike.csv --asset FurnaceSensorA --claude
    python main.py --interactive                # follow-up Q&A mode after diagnosis
"""

import argparse
import sys

from rich import print as rprint
from rich.rule import Rule

from app.agent import IndusDiagAgent


def parse_args():
    parser = argparse.ArgumentParser(
        description="IndusDiag: AI-powered industrial sensor diagnostics"
    )
    parser.add_argument(
        "--file",
        default="data/samples/sensor_spike.csv",
        help="Path to sensor CSV file",
    )
    parser.add_argument(
        "--asset",
        default="FurnaceSensorA",
        help="Asset name for the report and memory",
    )
    parser.add_argument(
        "--claude",
        action="store_true",
        help="Use Claude API instead of OpenRouter for reasoning",
    )
    parser.add_argument(
        "--interactive",
        action="store_true",
        help="After diagnosis, enter interactive Q&A mode",
    )
    parser.add_argument(
        "--quiet",
        action="store_true",
        help="Suppress verbose output",
    )
    return parser.parse_args()


def main():
    args = parse_args()

    rprint(Rule("[bold blue]IndusDiag — Industrial AI Diagnostics Agent[/bold blue]"))

    # Initialize the agent
    agent = IndusDiagAgent(
        asset_name=args.asset,
        use_claude=args.claude,
        verbose=not args.quiet,
    )

    # Run full diagnostic pipeline
    try:
        report = agent.run(file_path=args.file)
    except FileNotFoundError:
        rprint(f"[bold red]❌ File not found:[/bold red] {args.file}")
        sys.exit(1)
    except ValueError as e:
        rprint(f"[bold red]❌ Data error:[/bold red] {e}")
        sys.exit(1)
    except Exception as e:
        rprint(f"[bold red]❌ Agent error:[/bold red] {e}")
        sys.exit(1)

    # Optional interactive Q&A mode
    if args.interactive:
        rprint(Rule("[bold cyan]Interactive Q&A Mode[/bold cyan]"))
        rprint("[dim]Ask follow-up questions about the diagnosis. Type 'exit' to quit.[/dim]\n")

        while True:
            try:
                question = input("You: ").strip()
            except (EOFError, KeyboardInterrupt):
                rprint("\n[dim]Session ended.[/dim]")
                break

            if question.lower() in ("exit", "quit", "q"):
                rprint("[dim]Session ended.[/dim]")
                break

            if not question:
                continue

            agent.ask(question)

    rprint(Rule("[dim]Session complete[/dim]"))


if __name__ == "__main__":
    main()
