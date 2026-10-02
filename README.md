# 🪄 patronum

> **Expecto networkum!** A wizard-themed network diagnostic CLI — pure Python, zero dependencies.

<p align="center">
  <img src="https://img.shields.io/badge/python-3.9%2B-blue" alt="python"/>
  <img src="https://img.shields.io/badge/dependencies-0-brightgreen" alt="deps"/>
  <img src="https://img.shields.io/badge/license-MIT-green" alt="license"/>
</p>

## ✨ Spells

| Spell | What it does |
|---|---|
| `ip` | Reveal your public IP, location & ISP |
| `dns <domain>` | Resolve a domain (IPv4 + IPv6) |
| `ping <host>` | Measure latency, packet loss |
| `port <host> <port>` | Check if a TCP gate is open |
| `speed` | Download throughput test |
| `cast` | Run **everything** in one sequence |

## 🚀 Usage

```bash
# no install, no venv, no pip — just run it
python3 patronum.py ip
python3 patronum.py dns github.com
python3 patronum.py ping google.com
python3 patronum.py port github.com 443
python3 patronum.py speed
python3 patronum.py cast --json   # full diagnostic, machine-readable
```

## 🧪 Tests

```bash
python3 test_patronum.py -v
```

## ⚙️ CI

GitHub Actions runs syntax check, unit tests and a live smoke test on every push.

---

<div align="center">
<i>🐍 Slytherin-coded. Works best after midnight.</i>
</div>
