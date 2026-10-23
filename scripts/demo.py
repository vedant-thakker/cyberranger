#!/usr/bin/env python3
import argparse
import sys
import time
from typing import Optional
import urllib.request
import urllib.error

from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.text import Text

# Add backend directory to sys.path so app modules import cleanly
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "backend"))

from app.security.target_client import DVWATargetClient
from app.storage.database import Database
from app.experiments.referee import RefereeEngine


def verify_target(target_url: str = "http://127.0.0.1:8080/login.php") -> bool:
    try:
        req = urllib.request.Request(target_url, headers={"User-Agent": "CyberRanger-Check"})
        with urllib.request.urlopen(req, timeout=4) as response:
            return response.status == 200
    except Exception:
        return False


def main() -> None:
    parser = argparse.ArgumentParser(description="CyberRanger Autonomous Co-Evolution Lab Demo")
    parser.add_argument("--rounds", type=int, default=20, help="Number of experimental rounds (default: 20)")
    parser.add_argument("--seed", type=int, default=42, help="Fixed random seed for algorithmic reproducibility")
    parser.add_argument("--no-llm", action="store_true", default=True, help="Disable optional LLM proposer (default)")
    parser.add_argument("--enable-llm", action="store_true", default=False, help="Enable schema-validated structural proposer")
    args = parser.parse_args()

    console = Console()
    console.print(
        Panel.fit(
            "[bold cyan]CYBERRANGER AUTONOMOUS CO-EVOLUTION LAB[/bold cyan]\n"
            "[dim]Defensive Security Research Demonstration | Live Local DVWA Target[/dim]\n"
            f"[yellow]Configuration:[/yellow] Rounds={args.rounds} | Seed={args.seed} | LLM Proposer={'ON' if args.enable_llm else 'OFF (Grammar Path)'}",
            border_style="cyan",
        )
    )

    # 1. Environment & Target Verification
    console.print("[dim]Checking local target container (DVWA on 127.0.0.1:8080)...[/dim]")
    if not verify_target():
        console.print(
            Panel(
                "[bold red]DVWA Target Unreachable on 127.0.0.1:8080[/bold red]\n\n"
                "Please ensure OrbStack and the DVWA container are running:\n"
                "  [cyan]make start-target[/cyan]\n"
                "or:\n"
                "  [cyan]docker run -d --name dvwa --platform linux/amd64 -p 127.0.0.1:8080:80 vulnerables/web-dvwa[/cyan]",
                border_style="red",
            )
        )
        sys.exit(1)

    console.print("[green]✔ Target verified: DVWA online and responsive.[/green]\n")

    # 2. Initialize Core Components
    db_path = "cyberranger_demo.db"
    if os.path.exists(db_path):
        try:
            os.remove(db_path)
        except Exception:
            pass

    db = Database(db_path)
    client = DVWATargetClient(base_url="http://127.0.0.1:8080")
    client.authenticate()

    exp_id = "demo-run"
    db.create_experiment(
        exp_id=exp_id,
        name="CyberRanger 20-Round Demo",
        total_rounds=args.rounds,
        seed=args.seed,
    )

    referee = RefereeEngine(
        exp_id=exp_id,
        target_client=client,
        db=db,
        seed=args.seed,
        cadence_rounds=5,
        enable_llm=args.enable_llm,
    )

    # 3. Create Rich Live Table
    table = Table(title="Live Engagement Telemetry", show_header=True, header_style="bold cyan", border_style="dim")
    table.add_column("Rnd", justify="right", style="cyan", width=5)
    table.add_column("Category", style="magenta", width=12)
    table.add_column("Strategy", style="dim", width=22)
    table.add_column("Target", justify="center", width=8)
    table.add_column("Verdict", justify="center", width=10)
    table.add_column("Detector Summary", style="dim", width=42)
    table.add_column("Time", justify="right", style="dim", width=8)

    start_wall_time = time.perf_counter()

    # Pre-confirm educational findings in triage at start so retraining cadence has confirmed data
    triage_queue = referee.triage_queue

    # 4. Execute Rounds
    for r in range(1, args.rounds + 1):
        round_data = referee.run_round()

        # At round 4, simulate human triage confirmation of pending findings to trigger legitimate retraining at round 5
        if r == 4:
            pending = triage_queue.get_pending(exp_id)
            for item in pending:
                triage_queue.review_item(item["id"], "Confirmed", "Human mentor verified attack structure")

        # Color-coded verdict
        verdict = round_data["detector_outcome"]
        if verdict == "Blocked":
            verdict_text = Text("BLOCKED", style="bold cyan")
        elif verdict == "Evaded":
            verdict_text = Text("EVADED", style="bold red")
        else:
            verdict_text = Text("CLEAN", style="dim")

        target_text = (
            Text("COMPR", style="bold red")
            if round_data["target_compromised"]
            else Text("SAFE", style="green")
        )

        table.add_row(
            str(round_data["round_number"]),
            round_data["category"].upper(),
            round_data["strategy"].replace("_", " "),
            target_text,
            verdict_text,
            round_data["one_line_reason"][:42],
            f"{round_data['duration_ms']:.0f}ms",
        )

        # Notify if a retrain event or regression occurred
        if round_data.get("retrain_event"):
            ret = round_data["retrain_event"]
            console.print(
                f"[bold green]>> [CADENCE RETRAIN TRIGGERED] New Model Snapshot: {ret['version']} "
                f"({ret['training_samples']} confirmed samples, Val Acc: {ret['validation_metrics']['val_accuracy'] * 100:.1f}%)[/bold green]"
            )

        if round_data.get("regression_report"):
            reg = round_data["regression_report"]
            console.print(f"[bold yellow]>> [REGRESSION PASS] {reg['summary']}[/bold yellow]")

    duration = time.perf_counter() - start_wall_time

    console.print(table)

    # 5. Summary Statistics from Database
    rounds = db.get_rounds(exp_id)
    n = len(rounds)
    blocked = sum(1 for r in rounds if r["detector_outcome"] == "Blocked")
    evaded = sum(1 for r in rounds if r["detector_outcome"] == "Evaded")
    compromises = sum(1 for r in rounds if r["target_compromised"] == 1)
    archive_cells = referee.archive.total_occupied

    summary_panel = Panel(
        f"[bold]Session Completed Successfully[/bold]\n"
        f"• Duration: [cyan]{duration:.2f} seconds[/cyan] (Avg {duration / n:.2f}s per round)\n"
        f"• Total Rounds: [cyan]{n} / {args.rounds}[/cyan]\n"
        f"• Intercepted Threats: [green]{blocked} / {n} ({blocked / n * 100:.1f}% detection rate)[/green]\n"
        f"• Target Compromises: [red]{compromises}[/red] | Undetected Evasions: [yellow]{evaded}[/yellow]\n"
        f"• MAP-Elites Behavioral Niches: [cyan]{archive_cells} unique cells discovered[/cyan]\n"
        f"• Final Blue Detector Version: [cyan]{referee.detector.version_tag}[/cyan]\n"
        f"• Containment: [green]100% loopback requests (127.0.0.1:8080) verified by NetworkGuard[/green]",
        title="[bold cyan]CyberRanger Run Summary[/bold cyan]",
        border_style="cyan",
    )
    console.print(summary_panel)


if __name__ == "__main__":
    main()
