"""CLI client for eval-runner service."""
from __future__ import annotations

import json
import os
import sys
import time
from typing import Optional

import click
import httpx
from rich.console import Console
from rich.table import Table
from rich import box

console = Console()


def _service() -> str:
    return os.getenv("EVAL_SERVICE", "http://localhost:8020")


def _headers() -> dict:
    key = os.getenv("EVAL_API_KEY", "")
    return {"Authorization": f"Bearer {key}"} if key else {}


def _get(path: str, params: dict | None = None) -> dict:
    url = f"{_service()}{path}"
    try:
        r = httpx.get(url, headers=_headers(), params=params, timeout=10)
        r.raise_for_status()
        return r.json()
    except httpx.HTTPStatusError as e:
        console.print(f"[red]HTTP {e.response.status_code}:[/red] {e.response.text}")
        sys.exit(1)
    except httpx.ConnectError:
        console.print(f"[red]Cannot connect to eval-runner at {_service()}[/red]")
        console.print("Set EVAL_SERVICE env var or ensure the service is running.")
        sys.exit(1)


def _post(path: str, body: dict) -> dict:
    url = f"{_service()}{path}"
    try:
        r = httpx.post(url, json=body, headers=_headers(), timeout=10)
        r.raise_for_status()
        return r.json()
    except httpx.HTTPStatusError as e:
        console.print(f"[red]HTTP {e.response.status_code}:[/red] {e.response.text}")
        sys.exit(1)
    except httpx.ConnectError:
        console.print(f"[red]Cannot connect to eval-runner at {_service()}[/red]")
        sys.exit(1)


def _poll_run(run_id: str, timeout: int = 300) -> dict:
    """Poll a run until it finishes or times out."""
    deadline = time.monotonic() + timeout
    last_passed = 0
    last_total = 0
    with console.status(f"[cyan]Running {run_id[:8]}…[/cyan]", spinner="dots") as status:
        while time.monotonic() < deadline:
            run = _get(f"/runs/{run_id}")
            total = run.get("total_cases", 0)
            passed = run.get("passed", 0)
            failed = run.get("failed", 0)
            done = passed + failed + run.get("errored", 0)
            if total and (passed != last_passed or total != last_total):
                pct = f"{passed}/{done} passed" if done else "starting…"
                status.update(f"[cyan]{pct} ({done}/{total})[/cyan]")
                last_passed, last_total = passed, total
            if run["status"] in ("done", "failed"):
                return run
            time.sleep(2)
    console.print("[yellow]Timed out waiting for run[/yellow]")
    return _get(f"/runs/{run_id}")


def _print_run_summary(run: dict) -> None:
    console.print()
    model = run.get("model", "?")
    suite = run.get("suite_name") or "ad-hoc"
    run_id = run.get("run_id", "?")[:8]
    pass_rate = run.get("pass_rate")
    rate_str = f"{pass_rate * 100:.1f}%" if pass_rate is not None else "—"
    p50 = run.get("p50_latency_ms")
    p95 = run.get("p95_latency_ms")

    console.rule(f"[bold]Run {run_id}  |  {model}  |  {suite}[/bold]")
    console.print(
        f"  Passed: [green]{run.get('passed',0)}[/green]  "
        f"Failed: [red]{run.get('failed',0)}[/red]  "
        f"Errored: [yellow]{run.get('errored',0)}[/yellow]  "
        f"Total: {run.get('total_cases',0)}"
    )
    color = "green" if (pass_rate or 0) >= 0.8 else "yellow" if (pass_rate or 0) >= 0.6 else "red"
    console.print(f"  Pass rate: [{color}]{rate_str}[/{color}]", end="")
    if p50:
        console.print(f"   P50 latency: {p50:.0f}ms", end="")
    if p95:
        console.print(f"   P95: {p95:.0f}ms", end="")
    console.print()


def _print_failures(run_id: str) -> None:
    results = _get(f"/runs/{run_id}/results", params={"status": "fail", "limit": 50})
    if not results["results"]:
        return
    console.print()
    console.print("[bold red]FAILURES:[/bold red]")
    for r in results["results"]:
        scorers = json.loads(r.get("scorer_details_json", "[]"))
        failed_scorers = [s for s in scorers if not s.get("passed")]
        for s in failed_scorers:
            console.print(f"  [dim]{r['case_id']}[/dim] — {s['scorer_type']}: {s['detail']}")


# ---------------------------------------------------------------------------
# CLI commands
# ---------------------------------------------------------------------------

@click.group()
@click.option("--service", envvar="EVAL_SERVICE", help="Eval-runner service URL")
@click.pass_context
def cli(ctx: click.Context, service: Optional[str]):
    """Homelab model eval framework."""
    if service:
        os.environ["EVAL_SERVICE"] = service


@cli.command("run")
@click.option("--model", "-m", required=True, help="Model ID (as known to llm-router)")
@click.option("--suite", "-s", default=None, help="Suite name")
@click.option("--tags", "-t", default=None, help="Comma-separated tags filter")
@click.option("--cases", "-c", default=None, help="Comma-separated case IDs")
@click.option("--concurrency", default=1, show_default=True, help="Parallel case execution")
@click.option("--timeout", default=60, show_default=True, help="Per-case timeout (seconds)")
@click.option("--wait/--no-wait", default=True, show_default=True, help="Wait for completion")
@click.option("--wait-timeout", default=600, show_default=True, help="Max wait seconds")
@click.option("--json-out", is_flag=True, help="Output JSON instead of table")
def cmd_run(model, suite, tags, cases, concurrency, timeout, wait, wait_timeout, json_out):
    """Run evals against a model."""
    body: dict = {"model": model, "concurrency": concurrency, "timeout_seconds": timeout}
    if suite:
        body["suite"] = suite
    if tags:
        body["tags"] = [t.strip() for t in tags.split(",")]
    if cases:
        body["case_ids"] = [c.strip() for c in cases.split(",")]
    if not suite and not tags and not cases:
        body["tags"] = []  # will trigger "run all"

    run = _post("/runs", body)
    run_id = run["run_id"]

    if json_out:
        if wait:
            run = _poll_run(run_id, timeout=wait_timeout)
        print(json.dumps(run, indent=2))
        return

    console.print(f"\n  Run ID: [cyan]{run_id}[/cyan]  ({run['total_cases']} cases)")

    if wait:
        run = _poll_run(run_id, timeout=wait_timeout)
        _print_run_summary(run)
        _print_failures(run_id)

        # Exit 1 if pass rate below 80% (for CI use)
        if run.get("pass_rate", 1.0) < 0.8:
            sys.exit(1)
    else:
        console.print(f"  [dim]Poll with: eval results {run_id}[/dim]")


@cli.command("results")
@click.argument("run_id")
@click.option("--status", default=None, type=click.Choice(["pass", "fail", "error"]))
@click.option("--category", "-c", default=None)
@click.option("--full", is_flag=True, help="Show full response text")
@click.option("--json-out", is_flag=True)
def cmd_results(run_id, status, category, full, json_out):
    """Show results for a run."""
    run = _get(f"/runs/{run_id}")
    results = _get(f"/runs/{run_id}/results", params={
        "status": status, "category": category, "limit": 200
    })

    if json_out:
        print(json.dumps({"run": run, "results": results["results"]}, indent=2))
        return

    _print_run_summary(run)

    table = Table(box=box.SIMPLE, show_header=True, header_style="bold")
    table.add_column("Case ID", style="dim", max_width=45)
    table.add_column("Category")
    table.add_column("Status", width=8)
    table.add_column("Latency", justify="right")
    table.add_column("Detail", max_width=50)

    for r in results["results"]:
        status_icon = "[green]pass[/green]" if r["status"] == "pass" else "[red]fail[/red]" if r["status"] == "fail" else "[yellow]err[/yellow]"
        lat = f"{r['latency_ms']:.0f}ms" if r.get("latency_ms") else "—"
        scorers = json.loads(r.get("scorer_details_json", "[]"))
        failed = [s for s in scorers if not s.get("passed")]
        detail = failed[0]["detail"][:50] if failed else (r.get("error", "")[:50] if r["status"] == "error" else "✓")
        table.add_row(r["case_id"], r["category"], status_icon, lat, detail)

        if full and r.get("response_text"):
            console.print(f"  [dim]Response:[/dim] {r['response_text'][:200]}")

    console.print(table)


@cli.command("runs")
@click.option("--model", "-m", default=None)
@click.option("--suite", "-s", default=None)
@click.option("--status", default=None, type=click.Choice(["running", "done", "failed"]))
@click.option("--limit", default=20, show_default=True)
@click.option("--json-out", is_flag=True)
def cmd_runs(model, suite, status, limit, json_out):
    """List recent eval runs."""
    data = _get("/runs", params={"model": model, "suite": suite, "status": status, "limit": limit})

    if json_out:
        print(json.dumps(data, indent=2))
        return

    table = Table(box=box.SIMPLE, show_header=True, header_style="bold")
    table.add_column("Run ID", width=10)
    table.add_column("Model")
    table.add_column("Suite")
    table.add_column("Status", width=9)
    table.add_column("Pass Rate", justify="right")
    table.add_column("P50", justify="right")
    table.add_column("Started")

    for r in data["runs"]:
        rid = r.get("run_id", "")[:8]
        pr = r.get("pass_rate")
        rate_str = f"{pr * 100:.1f}%" if pr is not None else "—"
        color = "green" if (pr or 0) >= 0.8 else "yellow" if (pr or 0) >= 0.6 else "red"
        status_color = "green" if r["status"] == "done" else "yellow" if r["status"] == "running" else "red"
        p50 = f"{r['p50_latency_ms']:.0f}ms" if r.get("p50_latency_ms") else "—"
        started = r.get("started_at", "")[:16].replace("T", " ")
        table.add_row(
            rid,
            r.get("model", "?"),
            r.get("suite_name") or "—",
            f"[{status_color}]{r['status']}[/{status_color}]",
            f"[{color}]{rate_str}[/{color}]",
            p50,
            started,
        )
    console.print(table)


@cli.command("compare")
@click.argument("run_a")
@click.argument("run_b")
@click.option("--json-out", is_flag=True)
def cmd_compare(run_a, run_b, json_out):
    """Compare two eval runs side by side."""
    data = _get("/runs/compare", params={"a": run_a, "b": run_b})

    if json_out:
        print(json.dumps(data, indent=2))
        return

    ra = data["run_a"]
    rb = data["run_b"]
    console.rule(f"[bold]Comparing {run_a[:8]} vs {run_b[:8]}[/bold]")
    console.print(f"  A: [cyan]{ra.get('model')}[/cyan]  pass_rate={ra.get('pass_rate', 0) * 100:.1f}%  P50={ra.get('p50_latency_ms') or '—'}")
    console.print(f"  B: [cyan]{rb.get('model')}[/cyan]  pass_rate={rb.get('pass_rate', 0) * 100:.1f}%  P50={rb.get('p50_latency_ms') or '—'}")
    if data.get("latency_delta_p50_ms") is not None:
        d = data["latency_delta_p50_ms"]
        console.print(f"  Latency Δ (B−A): {'[red]' if d > 0 else '[green]'}{d:+.0f}ms[/{'red' if d > 0 else 'green'}]")
    console.print()

    table = Table(box=box.SIMPLE, show_header=True, header_style="bold")
    table.add_column("Category")
    table.add_column("A rate", justify="right")
    table.add_column("B rate", justify="right")
    table.add_column("Δ", justify="right")
    table.add_column("Winner", width=5)

    for cat in data["by_category"]:
        a_r = f"{cat['a_pass_rate'] * 100:.1f}%"
        b_r = f"{cat['b_pass_rate'] * 100:.1f}%"
        delta = cat["delta"]
        w = cat["winner"]
        delta_str = f"{'[green]' if delta > 0 else '[red]' if delta < 0 else ''}{delta * 100:+.1f}%{']' if delta != 0 else ''}"
        winner_str = "[green]B[/green]" if w == "b" else "[red]A[/red]" if w == "a" else "[dim]tie[/dim]"
        table.add_row(cat["category"], a_r, b_r, delta_str, winner_str)
    console.print(table)

    if data.get("cases_a_wins"):
        console.print(f"  A wins ({len(data['cases_a_wins'])}): {', '.join(data['cases_a_wins'][:5])}")
    if data.get("cases_b_wins"):
        console.print(f"  B wins ({len(data['cases_b_wins'])}): {', '.join(data['cases_b_wins'][:5])}")


@cli.command("temp-sweep")
@click.option("--model", "-m", required=True, help="Model ID (as known to llm-router)")
@click.option("--temps", default="0.0,0.5,0.7,0.9", show_default=True, help="Comma-separated temperatures")
@click.option("--suite", "-s", default=None, help="Suite name")
@click.option("--tags", "-t", default=None, help="Comma-separated tags filter")
@click.option("--cases", "-c", default=None, help="Comma-separated case IDs")
@click.option("--concurrency", default=1, show_default=True)
@click.option("--timeout", default=60, show_default=True, help="Per-case timeout (seconds)")
@click.option("--wait-timeout", default=600, show_default=True, help="Max wait seconds per run")
@click.option("--json-out", is_flag=True)
def cmd_temp_sweep(model, temps, suite, tags, cases, concurrency, timeout, wait_timeout, json_out):
    """Run the same cases at multiple temperatures and compare pass rates."""
    temperature_list = [float(t.strip()) for t in temps.split(",")]

    # Build shared case selector
    selector: dict = {"model": model, "concurrency": concurrency, "timeout_seconds": timeout}
    if suite:
        selector["suite"] = suite
    if tags:
        selector["tags"] = [t.strip() for t in tags.split(",")]
    if cases:
        selector["case_ids"] = [c.strip() for c in cases.split(",")]
    if not suite and not tags and not cases:
        selector["tags"] = []

    # Fire one run per temperature
    console.print(f"\n  [bold]Temperature Sweep[/bold] — {model}  |  {suite or tags or 'all'}")
    run_ids: dict[float, str] = {}
    for temp in temperature_list:
        body = {**selector, "temperature_override": temp}
        run = _post("/runs", body)
        run_ids[temp] = run["run_id"]
        console.print(f"  T={temp}: run [cyan]{run['run_id'][:8]}[/cyan] ({run['total_cases']} cases)")

    # Poll all runs to completion
    console.print()
    runs_done: dict[float, dict] = {}
    for temp, run_id in run_ids.items():
        with console.status(f"[cyan]Waiting for T={temp} ({run_id[:8]})…[/cyan]", spinner="dots"):
            runs_done[temp] = _poll_run(run_id, timeout=wait_timeout)

    # Fetch results per run
    results_by_temp: dict[float, dict[str, dict]] = {}
    for temp, run_id in run_ids.items():
        data = _get(f"/runs/{run_id}/results", params={"limit": 500})
        results_by_temp[temp] = {r["case_id"]: r for r in data["results"]}

    if json_out:
        out = {
            str(temp): {
                "run_id": run_ids[temp],
                "pass_rate": runs_done[temp].get("pass_rate"),
                "results": {cid: r["status"] for cid, r in results_by_temp[temp].items()},
            }
            for temp in temperature_list
        }
        print(json.dumps(out, indent=2))
        return

    # Build matrix: rows=cases, cols=temperatures
    all_case_ids = sorted(set(cid for res in results_by_temp.values() for cid in res))

    table = Table(box=box.SIMPLE, show_header=True, header_style="bold", title=f"{model}")
    table.add_column("Case", max_width=45)
    for temp in temperature_list:
        table.add_column(f"T={temp}", justify="center", width=8)

    for case_id in all_case_ids:
        row: list = [f"[dim]{case_id}[/dim]"]
        for temp in temperature_list:
            r = results_by_temp[temp].get(case_id)
            if r is None:
                row.append("[dim]—[/dim]")
            elif r["status"] == "pass":
                row.append("[green]pass[/green]")
            elif r["status"] == "fail":
                row.append("[red]fail[/red]")
            else:
                row.append("[yellow]err[/yellow]")
        table.add_row(*row)

    console.print(table)

    # Summary line
    console.print("  Overall pass rate: ", end="")
    for temp in temperature_list:
        run = runs_done[temp]
        pr = run.get("pass_rate") or 0
        color = "green" if pr >= 0.8 else "yellow" if pr >= 0.6 else "red"
        console.print(f"T={temp} [{color}]{pr * 100:.0f}%[/{color}]  ", end="")
    console.print()

    # Flag the sweet spot: highest temp that still passes everything
    passing_temps = [t for t in temperature_list if (runs_done[t].get("pass_rate") or 0) >= 0.8]
    if passing_temps:
        sweet = max(passing_temps)
        console.print(f"\n  [green]Sweet spot:[/green] T={sweet} (highest temp with ≥80% pass rate)")
    else:
        console.print("\n  [red]No temperature reached 80% pass rate[/red]")


@cli.command("cases")
@click.option("--category", "-c", default=None)
@click.option("--tag", "-t", default=None)
@click.option("--json-out", is_flag=True)
def cmd_cases(category, tag, json_out):
    """List available eval cases."""
    params: dict = {}
    if category:
        params["category"] = category
    if tag:
        params["tag"] = [tag]
    data = _get("/cases", params=params)

    if json_out:
        print(json.dumps(data, indent=2))
        return

    table = Table(box=box.SIMPLE, show_header=True, header_style="bold")
    table.add_column("Case ID", max_width=50)
    table.add_column("Category")
    table.add_column("Tags")
    for c in data["cases"]:
        table.add_row(c["id"], c["category"], ", ".join(c["tags"]))
    console.print(table)
    console.print(f"  [dim]{data['total']} cases[/dim]")


@cli.command("suites")
def cmd_suites():
    """List available eval suites."""
    data = _get("/suites")
    table = Table(box=box.SIMPLE, show_header=True, header_style="bold")
    table.add_column("Suite")
    table.add_column("Cases", justify="right")
    table.add_column("Tags")
    table.add_column("Description")
    for s in data["suites"]:
        table.add_row(
            s["name"],
            str(s["case_count"]),
            ", ".join(s.get("tags", [])),
            s.get("description", ""),
        )
    console.print(table)


@cli.command("stats")
@click.option("--json-out", is_flag=True)
def cmd_stats(json_out):
    """Show aggregate stats across all eval runs."""
    data = _get("/stats")
    if json_out:
        print(json.dumps(data, indent=2))
        return
    console.print(f"\n  Total runs: {data['total_runs']}  (last 7d: {data['runs_last_7_days']})")
    if data.get("best_model"):
        b = data["best_model"]
        console.print(f"  Best model: [green]{b['model']}[/green]  ({b['avg_pass_rate'] * 100:.1f}% avg pass rate)")
    if data.get("by_model"):
        table = Table(box=box.SIMPLE, show_header=True, header_style="bold", title="By Model")
        table.add_column("Model")
        table.add_column("Runs", justify="right")
        table.add_column("Avg Pass Rate", justify="right")
        table.add_column("Avg P50", justify="right")
        for m in data["by_model"]:
            pr = m.get("avg_pass_rate", 0)
            color = "green" if pr >= 0.8 else "yellow" if pr >= 0.6 else "red"
            table.add_row(
                m["model"],
                str(m["runs"]),
                f"[{color}]{pr * 100:.1f}%[/{color}]",
                f"{m['avg_p50_latency_ms']:.0f}ms" if m.get("avg_p50_latency_ms") else "—",
            )
        console.print(table)


@cli.command("models")
def cmd_models():
    """List models available in the router."""
    data = _get("/models")
    for m in data.get("models", []):
        console.print(f"  {m}")
    if data.get("error"):
        console.print(f"  [yellow]Router error: {data['error']}[/yellow]")


if __name__ == "__main__":
    cli()
