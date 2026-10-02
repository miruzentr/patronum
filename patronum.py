#!/usr/bin/env python3
"""
patronum — a wizard-themed network diagnostic CLI. 🪄

Pure standard library: no dependencies, no install step, just `python3 patronum.py`.

Spells (commands):
    ip              Reveal your public IP and where in the world you are
    dns <domain>    Resolve a domain into its hidden addresses
    ping <host>     Measure how far the owl has to fly (latency)
    port <host> <p> Check whether a gate is open on a remote castle
    speed           Test how fast your Patronum can carry data
    cast            Run every spell in sequence (full diagnostic)
"""

from __future__ import annotations

import argparse
import json
import socket
import statistics
import subprocess
import sys
import time
import urllib.error
import urllib.request

__version__ = "1.0.0"

# --- House colours (ANSI, gracefully degrade when piped) --------------------

USE_COLOR = sys.stdout.isatty()


def _c(code: str, text: str) -> str:
    return f"\033[{code}m{text}\033[0m" if USE_COLOR else text


def green(t: str) -> str:
    return _c("38;5;40", t)


def red(t: str) -> str:
    return _c("38;5;196", t)


def yellow(t: str) -> str:
    return _c("38;5;220", t)


def silver(t: str) -> str:
    return _c("38;5;250", t)


def bold(t: str) -> str:
    return _c("1", t)


BANNER = r"""
   ___          _
  / _ \__ _ ___| |_ _ __ ___  _ __  _   _ _ __ ___
 / /_)/ _` / __| __| '__/ _ \| '_ \| | | | '_ ` _ \
/ ___/ (_| \__ \ |_| | | (_) | | | | |_| | | | | | |
\/    \__,_|___/\__|_|  \___/|_| |_|\__,_|_| |_| |_|
"""


def header(title: str) -> None:
    print()
    print(bold(silver(f"  ✦ {title}")))
    print(silver("  " + "─" * 52))


def banner() -> None:
    print(silver(BANNER))
    print(silver(f"  patronum v{__version__} — expecto networkum! 🪄"))
    print(silver("  " + "═" * 52))


# --- Spells -----------------------------------------------------------------


def spell_ip() -> dict:
    """Reveal the public IP address and its location."""
    header("Lumos — revealing your public address")
    url = "http://ip-api.com/json/?fields=status,message,query,country,city,isp,org,timezone"
    try:
        with urllib.request.urlopen(url, timeout=8) as resp:
            data = json.loads(resp.read().decode())
    except (urllib.error.URLError, TimeoutError, OSError) as exc:
        print(red(f"  ✗ The mirror is foggy: {exc}"))
        return {"ok": False, "error": str(exc)}

    if data.get("status") != "success":
        print(red(f"  ✗ Enchantment failed: {data.get('message', 'unknown')}"))
        return {"ok": False, "error": data.get("message")}

    print(f"  IP        {green(data['query'])}")
    print(f"  Location  {data.get('city', '?')}, {data.get('country', '?')}")
    print(f"  Provider  {data.get('isp', '?')}")
    print(f"  Timezone  {data.get('timezone', '?')}")
    return {"ok": True, **data}


def spell_dns(domain: str) -> dict:
    """Resolve a domain to its addresses (IPv4 + IPv6)."""
    header(f"Revelio — resolving {domain}")
    result: dict = {"ok": False, "domain": domain, "ipv4": [], "ipv6": []}
    try:
        infos = socket.getaddrinfo(domain, None)
    except socket.gaierror as exc:
        print(red(f"  ✗ The name is shrouded: {exc}"))
        return result

    for info in infos:
        addr = info[4][0]
        family = info[0]
        if family == socket.AF_INET and addr not in result["ipv4"]:
            result["ipv4"].append(addr)
        elif family == socket.AF_INET6 and addr not in result["ipv6"]:
            result["ipv6"].append(addr)

    for addr in result["ipv4"]:
        print(f"  IPv4      {green(addr)}")
    for addr in result["ipv6"]:
        print(f"  IPv6      {silver(addr)}")
    if not result["ipv4"] and not result["ipv6"]:
        print(red("  ✗ No addresses found."))
        return result

    result["ok"] = True
    print(green(f"\n  ✓ {len(result['ipv4']) + len(result['ipv6'])} address(es) revealed."))
    return result


def spell_ping(host: str, count: int = 4) -> dict:
    """Measure latency to a host using the system ping binary."""
    header(f"Accio — measuring distance to {host}")
    cmd = ["ping", "-c", str(count), "-W", "2", host]
    try:
        proc = subprocess.run(cmd, capture_output=True, text=True, timeout=count * 3 + 5)
    except (subprocess.TimeoutExpired, FileNotFoundError) as exc:
        print(red(f"  ✗ Ping spell unavailable: {exc}"))
        return {"ok": False, "host": host, "error": str(exc)}

    if proc.returncode != 0:
        print(red("  ✗ No reply — the owl never returned."))
        return {"ok": False, "host": host, "error": proc.stderr.strip() or "no reply"}

    lines = [ln for ln in proc.stdout.splitlines() if "time=" in ln]
    times = []
    for ln in lines:
        try:
            times.append(float(ln.split("time=")[1].split()[0]))
        except (IndexError, ValueError):
            continue

    if not times:
        print(red("  ✗ Reply received but no timing data."))
        return {"ok": False, "host": host, "error": "no timing data"}

    result = {
        "ok": True,
        "host": host,
        "min_ms": round(min(times), 2),
        "max_ms": round(max(times), 2),
        "avg_ms": round(statistics.mean(times), 2),
        "loss_percent": round((count - len(times)) / count * 100, 1),
    }
    print(f"  Sent      {count} owls")
    print(f"  Received  {green(str(len(times)))}")
    print("  Avg       " + green(f"{result['avg_ms']} ms"))
    print(f"  Range     {result['min_ms']} – {result['max_ms']} ms")
    loss = result["loss_percent"]
    print("  Loss      " + (green(f"{loss}%") if loss == 0 else red(f"{loss}%")))
    return result


def spell_port(host: str, port: int, timeout: float = 3.0) -> dict:
    """Check whether a TCP port is open on a host."""
    header(f"Alohomora — testing {host}:{port}")
    started = time.perf_counter()
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.settimeout(timeout)
    try:
        code = sock.connect_ex((host, port))
    except socket.gaierror as exc:
        print(red(f"  ✗ Cannot find {host}: {exc}"))
        return {"ok": False, "host": host, "port": port, "open": False, "error": str(exc)}
    finally:
        sock.close()

    elapsed = round((time.perf_counter() - started) * 1000, 1)
    if code == 0:
        print(f"  Status    {green('OPEN ✓')} (handshake in {elapsed} ms)")
        return {"ok": True, "host": host, "port": port, "open": True, "latency_ms": elapsed}

    print("  Status    " + red(f"CLOSED ✗ ({elapsed} ms)"))
    return {"ok": True, "host": host, "port": port, "open": False, "latency_ms": elapsed}


def spell_speed(url: str | None = None, timeout: int = 15) -> dict:
    """Measure download throughput by fetching a known payload."""
    url = url or "https://speed.cloudflare.com/__down?bytes=10000000"
    header("Vroom — how fast can data fly?")
    print(silver(f"  Fetching a 10 MB payload …"))
    started = time.perf_counter()
    total = 0
    try:
        with urllib.request.urlopen(url, timeout=timeout) as resp:
            while True:
                chunk = resp.read(65536)
                if not chunk:
                    break
                total += len(chunk)
    except (urllib.error.URLError, TimeoutError, OSError) as exc:
        print(red(f"  ✗ The broom crashed: {exc}"))
        return {"ok": False, "error": str(exc)}

    elapsed = time.perf_counter() - started
    mbps = round((total * 8) / elapsed / 1_000_000, 2) if elapsed else 0.0
    mbytes = round(total / 1_000_000, 2)
    print(f"  Downloaded {green(f'{mbytes} MB')} in {round(elapsed, 2)} s")
    print(f"  Speed      {green(f'{mbps} Mbps')}")
    return {"ok": True, "mb": mbytes, "seconds": round(elapsed, 2), "mbps": mbps}


# --- CLI --------------------------------------------------------------------


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="patronum",
        description="🪄 A wizard-themed network diagnostic CLI.",
        epilog="Example: python3 patronum.py cast --host github.com --json",
    )
    parser.add_argument("--version", action="version", version=f"patronum {__version__}")
    sub = parser.add_subparsers(dest="spell")

    sub.add_parser("ip", help="reveal your public IP and location")
    sub.add_parser("speed", help="measure download speed")

    p_dns = sub.add_parser("dns", help="resolve a domain")
    p_dns.add_argument("domain")

    p_ping = sub.add_parser("ping", help="measure latency to a host")
    p_ping.add_argument("host")
    p_ping.add_argument("-c", "--count", type=int, default=4)

    p_port = sub.add_parser("port", help="check whether a TCP port is open")
    p_port.add_argument("host")
    p_port.add_argument("port", type=int)

    p_cast = sub.add_parser("cast", help="run every spell in sequence")
    p_cast.add_argument("--host", default="github.com")
    p_cast.add_argument("--port", type=int, default=443)
    p_cast.add_argument("--json", action="store_true", help="emit machine-readable JSON")

    args = parser.parse_args(argv)
    if not args.spell:
        parser.print_help()
        return 1

    if args.spell == "ip":
        banner()
        result = spell_ip()
    elif args.spell == "dns":
        banner()
        result = spell_dns(args.domain)
    elif args.spell == "ping":
        banner()
        result = spell_ping(args.host, args.count)
    elif args.spell == "port":
        banner()
        result = spell_port(args.host, args.port)
    elif args.spell == "speed":
        banner()
        result = spell_speed()
    elif args.spell == "cast":
        if not args.json:
            banner()
        result = {
            "ip": spell_ip(),
            "dns": spell_dns(args.host),
            "ping": spell_ping(args.host),
            "port": spell_port(args.host, args.port),
            "speed": spell_speed(),
        }
        if args.json:
            print(json.dumps(result, indent=2))
    else:  # pragma: no cover - argparse guards this
        parser.print_help()
        return 1

    ok = result.get("ok", True) if isinstance(result, dict) else True
    return 0 if ok else 2


if __name__ == "__main__":
    raise SystemExit(main())
