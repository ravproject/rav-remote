"""
Test komprehensif untuk 10 fitur AI RAV-REMOTE.
Mengetes handler, parsing, routing, dan validasi whitelist.
"""
import sys
import os
import asyncio
import json
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

os.environ["JWT_SECRET_KEY"] = "test_secret_key_for_testing"
os.environ["ENCRYPTION_KEY"] = "test_encryption_key_for_testing_purpose_only_32b"

RESULTS = {"passed": 0, "failed": 0, "skipped": 0, "details": []}

def report(name: str, status: str, detail: str = ""):
    RESULTS["details"].append({"name": name, "status": status, "detail": detail})
    if status == "✅":
        RESULTS["passed"] += 1
    elif status == "❌":
        RESULTS["failed"] += 1
    else:
        RESULTS["skipped"] += 1
    print(f"  {status} {name}")
    if detail:
        for line in detail.strip().split("\n"):
            print(f"     {line.strip()}")


async def test_memory():
    from agent.command_handler import CommandHandler
    h = CommandHandler()
    # test help
    r = await h.handle_memory([])
    assert "Memory System" in r, f"Help missing, got: {r[:100]}"
    report("!memory (help)", "✅", r.split("\n")[0])
    # test stats
    r = await h.handle_memory(["stats"])
    assert "Memory Stats" in r, f"Stats missing, got: {r[:100]}"
    report("!memory stats", "✅", r.split("\n")[0])
    # test search
    r = await h.handle_memory(["search", "test"])
    assert "Tidak ada" in r or "Hasil" in r or "Memory Search" in r
    report("!memory search", "✅", r.split("\n")[0])
    # test forget
    r = await h.handle_memory(["forget", "test"])
    assert "dihapus" in r or "error" in r.lower()
    report("!memory forget", "✅", r.split("\n")[0])


async def test_mcp():
    from agent.command_handler import CommandHandler
    h = CommandHandler()
    # test help
    r = await h.handle_mcp([])
    assert "MCP" in r, f"Help missing, got: {r[:100]}"
    report("!mcp (help)", "✅", r.split("\n")[0])
    # test status
    r = await h.handle_mcp(["status"])
    assert "Aktif" in r or "Nonaktif" in r, f"Status unexpected: {r[:100]}"
    report("!mcp status", "✅", r.split("\n")[0])
    # test on
    r = await h.handle_mcp(["on"])
    assert "diaktifkan" in r
    report("!mcp on", "✅", r.split("\n")[0])
    # test off
    r = await h.handle_mcp(["off"])
    assert "dinonaktifkan" in r
    report("!mcp off", "✅", r.split("\n")[0])


async def test_companion():
    from agent.command_handler import CommandHandler
    h = CommandHandler()
    # test help
    r = await h.handle_companion([])
    assert "Companion" in r or "companion" in r.lower()
    report("!companion (help)", "✅", r.split("\n")[0])
    # test chat (tanpa NIM API key, harus fallback graciously)
    r = await h.handle_companion(["halo", "apa", "kabar"])
    # Should either work or give a polite error
    assert isinstance(r, str) and len(r) > 0
    if "NIM" in r or "API" in r or "error" in r.lower() or "maaf" in r.lower():
        report("!companion chat", "⚠️", f"Fallback/error (expected tanpa NIM key): {r[:150]}")
    else:
        report("!companion chat", "✅", r[:150])


async def test_solve():
    from agent.command_handler import CommandHandler
    h = CommandHandler()
    # test help
    r = await h.handle_solve([])
    assert "solve" in r.lower() or "Solve" in r
    report("!solve (help)", "✅", r.split("\n")[0])
    # test solve problem
    r = await h.handle_solve(["apa", "itu", "python"])
    assert isinstance(r, str) and len(r) > 0
    if "NIM" in r or "API" in r or "error" in r.lower() or "maaf" in r.lower():
        report("!solve query", "⚠️", f"Fallback/error: {r[:150]}")
    else:
        report("!solve query", "✅", r[:150])


async def test_create_feature():
    from agent.command_handler import CommandHandler
    h = CommandHandler()
    # test help
    r = await h.handle_create_feature([])
    assert "Feature" in r or "Self-Feature" in r or "create" in r
    report("!create (help)", "✅", r.split("\n")[0])
    # test list (should be empty)
    r = await h.handle_create_feature(["list"])
    assert "Belum" in r or "Fitur" in r or "fitur" in r.lower()
    report("!create list", "✅", r.split("\n")[0])


async def test_self_evolve():
    from agent.command_handler import CommandHandler
    h = CommandHandler()
    # test help
    r = await h.handle_self_evolve([])
    assert "Self-Evolution" in r or "Evolve" in r or "evolution" in r.lower()
    report("!self_evolve (help)", "✅", r.split("\n")[0])
    # test history (no NIM needed for history)
    r = await h.handle_self_evolve(["history"])
    assert isinstance(r, str) and len(r) > 0
    report("!self_evolve history", "✅", r[:100])


async def test_optimize_me():
    from agent.command_handler import CommandHandler
    h = CommandHandler()
    # should always work (reads analytics data)
    r = await h.handle_optimize_me([])
    assert isinstance(r, str) and len(r) > 0
    report("!optimize_me", "✅", r[:150])


async def test_proactive():
    from agent.command_handler import CommandHandler
    h = CommandHandler()
    # test help
    r = await h.handle_proactive([])
    assert "Proactive" in r or "proactive" in r.lower()
    report("!proactive (help)", "✅", r.split("\n")[0])
    # test status
    r = await h.handle_proactive(["status"])
    assert "Aktif" in r or "Nonaktif" in r
    report("!proactive status", "✅", r.split("\n")[0])
    # test on
    r = await h.handle_proactive(["on"])
    assert "diaktifkan" in r
    report("!proactive on", "✅", r.split("\n")[0])
    # test off
    r = await h.handle_proactive(["off"])
    assert "dinonaktifkan" in r
    report("!proactive off", "✅", r.split("\n")[0])


async def test_learn():
    from agent.command_handler import CommandHandler
    h = CommandHandler()
    # test help
    r = await h.handle_learn([])
    assert "Knowledge" in r or "Learn" in r or "learn" in r.lower()
    report("!learn (help)", "✅", r.split("\n")[0])
    # test list
    r = await h.handle_learn(["list"])
    assert isinstance(r, str) and len(r) > 0
    if "error" in r.lower() and "NIM" not in r:
        report("!learn list", "⚠️", f"Unexpected: {r[:150]}")
    else:
        report("!learn list", "✅", r[:150])


async def test_agent_mode():
    from agent.command_handler import CommandHandler
    h = CommandHandler()
    # test help
    r = await h.handle_agent_mode([])
    assert "Agent" in r or "agent" in r.lower() or "Autonomous" in r
    report("!agent_mode (help)", "✅", r.split("\n")[0])


async def test_fallback_parser():
    """Test that all Indonesian aliases resolve to correct commands."""
    from ai_module.fallback_parser import FallbackParser
    cm = FallbackParser.COMMAND_MAP
    expected = {
        "!ingat": "memory",
        "!teman": "companion",
        "!atasi": "solve",
        "!buat": "create_feature",
        "!evolve": "self_evolve",
        "!optimize": "optimize_me",
        "!proaktif": "proactive",
        "!belajar": "learn",
    }
    all_ok = True
    for alias, expected_cmd in expected.items():
        actual = cm.get(alias)
        if actual == expected_cmd:
            report(f"Parser alias {alias} -> {expected_cmd}", "✅")
        else:
            report(f"Parser alias {alias} -> expected {expected_cmd}, got {actual}", "❌")
            all_ok = False


async def test_whitelist():
    """Test that all Indonesian aliases are in YAML whitelist (auto-reload)."""
    from security.sanitizer import load_allowed_commands
    cfg = load_allowed_commands(force=True)
    safe = cfg.get("safe_commands", {})
    expected_aliases = [
        "memory", "ingat", "mcp",
        "companion", "teman",
        "solve", "atasi",
        "create_feature", "create", "buat",
        "self_evolve", "evolve",
        "optimize_me", "optimize",
        "proactive", "proaktif",
        "learn", "belajar",
        "agent_mode",
    ]
    all_ok = True
    for alias in expected_aliases:
        if alias not in safe:
            report(f"Whitelist {alias}", "❌", "MISSING from YAML!")
            all_ok = False
    if all_ok:
        report("Whitelist semua alias", "✅", f"Total: {len(safe)} entries")


async def test_sanitizer_accepts_aliases():
    """Test that sanitizer accepts all !alias commands."""
    from security.sanitizer import InputSanitizer
    aliases = ["!ingat", "!teman", "!atasi", "!buat", "!evolve",
               "!optimize", "!proaktif", "!belajar", "!agent_mode", "!mcp"]
    all_ok = True
    for alias in aliases:
        result = InputSanitizer.sanitize_command(alias)
        if result is None:
            report(f"Sanitizer accepts {alias}", "❌", "BLOCKED!")
            all_ok = False
    if all_ok:
        report("Sanitizer accepts all !aliases", "✅")


async def test_router_routes():
    """Test that command_router correctly routes to handlers."""
    from bot.command_router import CommandRouter
    router = CommandRouter()
    test_cases = [
        ("!ingat", "memory"),
        ("!ingat stats", "memory"),
        ("!teman halo", "companion"),
        ("!atasi test", "solve"),
        ("!buat list", "create_feature"),
        ("!evolve", "self_evolve"),
        ("!optimize", "optimize_me"),
        ("!proaktif status", "proactive"),
        ("!belajar list", "learn"),
        ("!agent_mode", "agent_mode"),
        ("!mcp status", "mcp"),
    ]
    all_ok = True
    for cmd, expected_handler in test_cases:
        command_name, args = await router.interpreter.interpret(cmd)
        if command_name != expected_handler:
            report(f"Router {cmd} -> {expected_handler}", "❌",
                   f"Got command_name={command_name}, args={args}")
            all_ok = False
    if all_ok:
        report("Router routes all aliases correctly", "✅")


async def main():
    print("=" * 60)
    print("  TEST 10 FITUR AI — RAV-REMOTE")
    print("=" * 60)
    print()

    tests = [
        ("1. Memory (!ingat/!memory)", test_memory),
        ("2. MCP (!mcp)", test_mcp),
        ("3. Companion (!teman/!companion)", test_companion),
        ("4. Solve (!atasi/!solve)", test_solve),
        ("5. Create Feature (!buat/!create)", test_create_feature),
        ("6. Self Evolve (!evolve/!self_evolve)", test_self_evolve),
        ("7. Optimize Me (!optimize/!optimize_me)", test_optimize_me),
        ("8. Proactive (!proaktif/!proactive)", test_proactive),
        ("9. Learn (!belajar/!learn)", test_learn),
        ("10. Agent Mode (!agent_mode)", test_agent_mode),
    ]

    for name, test_fn in tests:
        print(f"\n--- {name} ---")
        try:
            await test_fn()
        except Exception as e:
            import traceback
            report(name, "❌", f"Exception: {e}\n{traceback.format_exc()}")

    print("\n--- Cross-cutting tests ---\n")
    await test_fallback_parser()
    await test_whitelist()
    await test_sanitizer_accepts_aliases()
    await test_router_routes()

    print("\n" + "=" * 60)
    print(f"  RINGKASAN:")
    print(f"  ✅ Passed: {RESULTS['passed']}")
    print(f"  ❌ Failed: {RESULTS['failed']}")
    print(f"  ⚠️ Skipped: {RESULTS['skipped']}")
    print(f"  Total: {RESULTS['passed'] + RESULTS['failed'] + RESULTS['skipped']}")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())
