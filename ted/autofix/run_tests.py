"""
Full test suite for TED Auto-Fix Engine
Tests: diagnostics, rule matching, executor, reporter, engine pipeline
"""
import sys, os, time
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from autofix import diagnostics
from autofix.engine import AutoFixEngine
from autofix.executor import run_local, run_ssh
from autofix.reporter import generate_report

PASS = "✅ PASS"
FAIL = "❌ FAIL"
WARN = "⚠️  WARN"

results = []

def test(name, fn):
    try:
        msg = fn()
        status = PASS
        print(f"{PASS}  {name}: {msg}")
        results.append((name, True))
    except AssertionError as e:
        print(f"{FAIL}  {name}: {e}")
        results.append((name, False))
    except Exception as e:
        print(f"{FAIL}  {name}: {type(e).__name__}: {e}")
        results.append((name, False))

print("\n" + "="*60)
print("  TED Auto-Fix Engine — Test Suite")
print("="*60 + "\n")

# ── 1. DIAGNOSTICS ───────────────────────────────────────────────────────

print("── Diagnostics (psutil) ──────────────────────────────────")

def test_collect():
    m = diagnostics.collect()
    assert 0 <= m.cpu_percent <= 100, f"CPU% out of range: {m.cpu_percent}"
    assert 0 <= m.memory_percent <= 100, f"RAM% out of range: {m.memory_percent}"
    assert m.disk_total_gb > 0, "Disk total is 0"
    assert m.hostname, "Hostname empty"
    return f"CPU={m.cpu_percent}% RAM={m.memory_percent}% Disk={m.disk_free_gb}GB free Host={m.hostname}"

def test_metrics_dict():
    m = diagnostics.collect()
    d = diagnostics.metrics_to_dict(m)
    assert "cpu" in d and "memory" in d and "disk" in d
    assert "percent" in d["cpu"]
    return "dict structure OK"

def test_battery():
    m = diagnostics.collect()
    # Battery can be None on desktops — just check it doesn't crash
    d = diagnostics.metrics_to_dict(m)
    if m.battery_percent is not None:
        assert 0 <= m.battery_percent <= 100
        return f"Battery={m.battery_percent}% plugged={m.battery_plugged}"
    return "No battery (desktop) — skipped"

test("collect() returns valid metrics",  test_collect)
test("metrics_to_dict() structure",      test_metrics_dict)
test("battery handling",                 test_battery)

# ── 2. RULE MATCHING ─────────────────────────────────────────────────────

print("\n── Rule Matching ─────────────────────────────────────────")

engine = AutoFixEngine()

def test_no_rules_normal():
    metrics = {"cpu": {"percent": 30}, "memory": {"percent": 50},
               "disk": {"percent": 40, "free_gb": 50}, "battery": {"percent": 80}}
    triggered = engine._match_rules(metrics)
    assert triggered == [], f"Expected no rules, got {[r['id'] for r in triggered]}"
    return "No rules fired for healthy machine"

def test_high_cpu():
    metrics = {"cpu": {"percent": 92}, "memory": {"percent": 50},
               "disk": {"percent": 40, "free_gb": 50}, "battery": {"percent": 80}}
    triggered = engine._match_rules(metrics)
    ids = [r["id"] for r in triggered]
    assert "HIGH_CPU" in ids, f"HIGH_CPU not triggered. Got: {ids}"
    return f"HIGH_CPU triggered at 92%"

def test_high_memory():
    metrics = {"cpu": {"percent": 30}, "memory": {"percent": 95},
               "disk": {"percent": 40, "free_gb": 50}, "battery": {"percent": 80}}
    triggered = engine._match_rules(metrics)
    ids = [r["id"] for r in triggered]
    assert "HIGH_MEMORY" in ids, f"HIGH_MEMORY not triggered. Got: {ids}"
    return "HIGH_MEMORY triggered at 95%"

def test_low_disk():
    metrics = {"cpu": {"percent": 30}, "memory": {"percent": 50},
               "disk": {"percent": 40, "free_gb": 2.5}, "battery": {"percent": 80}}
    triggered = engine._match_rules(metrics)
    ids = [r["id"] for r in triggered]
    assert "LOW_DISK" in ids, f"LOW_DISK not triggered. Got: {ids}"
    return "LOW_DISK triggered at 2.5 GB free"

def test_critical_battery():
    metrics = {"cpu": {"percent": 30}, "memory": {"percent": 50},
               "disk": {"percent": 40, "free_gb": 50}, "battery": {"percent": 10}}
    triggered = engine._match_rules(metrics)
    ids = [r["id"] for r in triggered]
    assert "LOW_BATTERY" in ids, f"LOW_BATTERY not triggered. Got: {ids}"
    return "LOW_BATTERY triggered at 10%"

def test_multiple_rules():
    metrics = {"cpu": {"percent": 95}, "memory": {"percent": 93},
               "disk": {"percent": 95, "free_gb": 1.0}, "battery": {"percent": 5}}
    triggered = engine._match_rules(metrics)
    ids = [r["id"] for r in triggered]
    assert len(ids) >= 4, f"Expected ≥4 rules, got {ids}"
    return f"All rules fired: {ids}"

test("healthy machine — no rules",       test_no_rules_normal)
test("HIGH_CPU rule trigger",            test_high_cpu)
test("HIGH_MEMORY rule trigger",         test_high_memory)
test("LOW_DISK rule trigger",            test_low_disk)
test("LOW_BATTERY rule trigger",         test_critical_battery)
test("multiple simultaneous rules",      test_multiple_rules)

# ── 3. EXECUTOR ──────────────────────────────────────────────────────────

print("\n── Executor ──────────────────────────────────────────────")

def test_local_no_commands():
    rule = {"id": "HIGH_MEMORY", "fix_commands": {"windows": [], "linux": []}}
    r = run_local(rule)
    assert r.method == "manual"
    assert r.success is True
    return "No-command rule → manual method"

def test_local_with_command():
    rule = {"id": "TEST_CMD", "fix_commands": {"windows": ["echo TED_TEST_OK"], "linux": ["echo TED_TEST_OK"]}}
    r = run_local(rule)
    assert r.success, f"Command failed: {r.error}"
    assert "TED_TEST_OK" in r.output or r.method == "manual"
    return f"Local command executed: method={r.method}"

def test_ssh_no_target():
    """SSH to invalid host should fail gracefully."""
    rule = {"id": "TEST_SSH", "fix_commands": {"ssh": ["echo hello"]}}
    r = run_ssh(rule, host="192.168.99.99", username="testuser", password="x", port=22)
    assert r.success is False
    assert r.error is not None
    return f"SSH failure handled gracefully: {r.error[:50]}"

test("local executor — no commands",     test_local_no_commands)
test("local executor — echo command",    test_local_with_command)
test("SSH executor — unreachable host",  test_ssh_no_target)

# ── 4. REPORTER ──────────────────────────────────────────────────────────

print("\n── Reporter (python-docx) ───────────────────────────────")

def test_report_generated():
    path = generate_report(
        session_id="UNIT-TEST-001",
        employee={"name": "Test User", "id": "EMP-TEST", "dept": "QA"},
        metrics={
            "timestamp": "2026-06-15T12:00:00",
            "hostname": "TEST-HOST",
            "platform": "Windows 11",
            "cpu":     {"percent": 92, "cores": 4, "freq_mhz": 2600},
            "memory":  {"percent": 95, "used_gb": 4.0, "total_gb": 4.3},
            "disk":    {"percent": 46, "used_gb": 50, "total_gb": 100, "free_gb": 50},
            "battery": {"percent": None, "plugged": None},
            "network": [],
            "flags":   ["HIGH_CPU", "HIGH_MEMORY"],
        },
        triggered_rules=[
            {"id": "HIGH_CPU",    "name": "High CPU Usage",    "severity": "medium"},
            {"id": "HIGH_MEMORY", "name": "High Memory Usage", "severity": "medium"},
        ],
        fix_results=[
            {"rule_id": "HIGH_MEMORY", "success": True, "method": "manual",
             "commands_run": [], "output": "Manual steps presented.", "error": None},
        ],
        diagnosis={
            "diagnosis": "Device is under heavy load due to multiple background processes.",
            "confidence": 0.88,
            "severity": "medium",
            "fix_steps": ["Open Task Manager", "End high-CPU processes", "Restart device"],
            "action": "guided_fix",
            "llm_model": "rule_engine",
        },
        outcome="guided_fix",
        output_dir="reports",
    )
    assert os.path.exists(path), f"Report not found at {path}"
    size_kb = os.path.getsize(path) / 1024
    assert size_kb > 5, f"Report too small: {size_kb:.1f} KB"
    return f"Report created: {os.path.basename(path)} ({size_kb:.1f} KB)"

test("report generated successfully", test_report_generated)

# ── 5. FULL PIPELINE ─────────────────────────────────────────────────────

print("\n── Full Engine Pipeline ─────────────────────────────────")

def test_full_run_healthy():
    """Simulate a healthy machine — no rules should fire."""
    # We can't fake psutil, so we just run it and verify structure
    r = engine.run(
        session_id="PIPELINE-TEST-001",
        employee={"name": "Alice Vance", "id": "EMP-1029", "dept": "Engineering"},
        diagnosis={"action": "self_resolve", "confidence": 0.95,
                   "diagnosis": "Test diagnosis", "fix_steps": ["Step 1", "Step 2"],
                   "severity": "medium", "llm_model": "rule_engine"},
        generate_report=True,
    )
    assert r.session_id == "PIPELINE-TEST-001"
    assert r.metrics is not None
    assert r.action in ("auto_resolved", "guided_fix", "escalate")
    assert r.report_path and os.path.exists(r.report_path)
    size_kb = os.path.getsize(r.report_path) / 1024
    return (f"action={r.action} rules={[x['id'] for x in r.triggered_rules]} "
            f"report={os.path.basename(r.report_path)} ({size_kb:.1f} KB)")

def test_full_run_escalate():
    """Escalation path when AI says create_ticket."""
    r = engine.run(
        session_id="PIPELINE-TEST-002",
        employee={"name": "Bob Miller", "id": "EMP-4552", "dept": "Sales"},
        diagnosis={"action": "create_ticket", "confidence": 0.30,
                   "diagnosis": "Unknown issue", "fix_steps": [],
                   "severity": "medium", "llm_model": "mock"},
        generate_report=True,
    )
    assert r.action == "escalate", f"Expected escalate, got {r.action}"
    return f"Escalation path correct — report={os.path.basename(r.report_path or '')}"

test("full pipeline — real hardware",    test_full_run_healthy)
test("full pipeline — escalation path",  test_full_run_escalate)

# ── SUMMARY ──────────────────────────────────────────────────────────────

print("\n" + "="*60)
passed = sum(1 for _, ok in results if ok)
failed = sum(1 for _, ok in results if not ok)
total  = len(results)
print(f"  Results: {passed}/{total} passed  |  {failed} failed")
print("="*60)

# List any failures
if failed:
    print("\nFailed tests:")
    for name, ok in results:
        if not ok:
            print(f"  ✗ {name}")

# List all generated reports
print("\nGenerated reports:")
report_dir = "reports"
if os.path.isdir(report_dir):
    for f in sorted(os.listdir(report_dir)):
        size = os.path.getsize(os.path.join(report_dir, f)) / 1024
        print(f"  📄 {f}  ({size:.1f} KB)")
