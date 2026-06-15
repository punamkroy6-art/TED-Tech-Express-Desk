import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from autofix.engine import AutoFixEngine

engine = AutoFixEngine()

result = engine.run(
    session_id="TEST-DEMO-001",
    employee={"name": "Alice Vance", "id": "EMP-1029", "dept": "Engineering"},
    diagnosis={
        "diagnosis": "Driver IRQL not less or equal (BSOD)",
        "confidence": 0.95,
        "severity": "critical",
        "fix_steps": ["Reboot in Safe Mode", "Uninstall graphics driver", "Run Memory Diagnostic"],
        "action": "self_resolve",
        "llm_model": "rule_engine",
    },
    generate_report=True,
)

print("=== AUTO-FIX ENGINE RESULT ===")
print(f"Action  : {result.action}")
print(f"Summary : {result.summary}")
print(f"Rules   : {[r['id'] for r in result.triggered_rules]}")
print(f"Fixes   : {len(result.fix_results)} executed")
print(f"Report  : {result.report_path}")
print()
print("Hardware snapshot:")
m = result.metrics
print(f"  CPU   : {m['cpu']['percent']}%  ({m['cpu']['cores']} cores @ {m['cpu']['freq_mhz']} MHz)")
print(f"  RAM   : {m['memory']['percent']}%  ({m['memory']['used_gb']}/{m['memory']['total_gb']} GB)")
print(f"  Disk  : {m['disk']['percent']}%  ({m['disk']['free_gb']} GB free)")
print(f"  Host  : {m['hostname']}")
print(f"  OS    : {m['platform']}")
