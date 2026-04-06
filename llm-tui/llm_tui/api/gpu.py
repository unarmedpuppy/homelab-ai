import asyncio

from llm_tui.models import GPUStats

_QUERY_FIELDS = (
    "index,name,temperature.gpu,power.draw,power.limit,"
    "memory.total,memory.used,memory.free,utilization.gpu"
)


def _parse_value(val: str, dtype: type = int):
    """Strip units like ' W', ' MiB', ' %' and convert."""
    cleaned = val.strip().split()[0]
    if cleaned in ("N/A", "[N/A]", ""):
        return 0
    try:
        return dtype(cleaned)
    except (ValueError, TypeError):
        return 0


async def poll_gpu_stats() -> list[GPUStats]:
    """Query nvidia-smi for per-GPU stats."""
    try:
        proc = await asyncio.create_subprocess_exec(
            "nvidia-smi",
            f"--query-gpu={_QUERY_FIELDS}",
            "--format=csv,noheader",
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        stdout, _ = await asyncio.wait_for(proc.communicate(), timeout=5)
    except (FileNotFoundError, asyncio.TimeoutError, OSError):
        return []

    gpus = []
    for line in stdout.decode().strip().splitlines():
        parts = [p.strip() for p in line.split(",")]
        if len(parts) < 9:
            continue
        gpus.append(GPUStats(
            index=_parse_value(parts[0]),
            name=parts[1].strip(),
            temp_c=_parse_value(parts[2]),
            power_draw_w=_parse_value(parts[3], float),
            power_limit_w=_parse_value(parts[4], float),
            vram_total_mb=_parse_value(parts[5]),
            vram_used_mb=_parse_value(parts[6]),
            vram_free_mb=_parse_value(parts[7]),
            utilization_pct=_parse_value(parts[8]),
        ))
    return gpus
