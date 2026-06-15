"""
engine.py — TED Auto-Fix Engine
Orchestrates: hardware diagnostics → rule matching → fix execution → report generation.

Usage:
    from autofix.engine import AutoFixEngine
    engine = AutoFixEngine()
    result = engine.run(session_id="abc123", employee={"name": "Alice", "id": "EMP001"})
    print(result)
"""

import os
import yaml
import logging
from pathlib import Path
from dataclasses import dataclass, field
from typing import Optional

from autofix import diagnostics, executor, reporter

logger = logging.getLogger("ted.autofix.engine")

CONFIG_PATH = Path(__file__).parent / "config.yaml"


@dataclass
class EngineResult:
    session_id: str
    metrics: dict
    triggered_rules: list
    fix_results: list
    report_path: Optional[str]
    action: str          # 'auto_resolved' | 'guided_fix' | 'escalate'
    summary: str


class AutoFixEngine:
    def __init__(self, config_path: str = None):
        path = config_path or CONFIG_PATH
        with open(path, "r") as f:
            self.config = yaml.safe_load(f)
        self.rules = self.config.get("rules", [])
        logger.info(f"AutoFixEngine loaded {len(self.rules)} rules from {path}")

    def run(
        self,
        session_id: str,
        employee: dict,
        diagnosis: dict = None,
        ssh_host: str = None,
        ssh_user: str = None,
        ssh_password: str = None,
        generate_report: bool = True,
    ) -> EngineResult:
        """
        Full auto-fix pipeline:
        1. Collect hardware metrics
        2. Match rules against thresholds
        3. Execute fix commands (local or SSH)
        4. Generate Word incident report
        """

        # ── 1. Collect hardware diagnostics ─────────────────────────────
        logger.info(f"[{session_id}] Collecting hardware metrics...")
        metrics_obj = diagnostics.collect()
        metrics = diagnostics.metrics_to_dict(metrics_obj)

        # ── 2. Match rules ───────────────────────────────────────────────
        triggered = self._match_rules(metrics)
        metrics["flags"] = [r["id"] for r in triggered]
        logger.info(f"[{session_id}] Rules triggered: {[r['id'] for r in triggered]}")

        # ── 3. Execute fixes ─────────────────────────────────────────────
        fix_results = []
        for rule in triggered:
            if ssh_host and rule.get("fix_commands", {}).get("ssh"):
                result = executor.run_ssh(rule, ssh_host, ssh_user, ssh_password)
            else:
                result = executor.run_local(rule)
            fix_results.append({
                "rule_id":      result.rule_id,
                "success":      result.success,
                "method":       result.method,
                "commands_run": result.commands_run,
                "output":       result.output,
                "error":        result.error,
            })
            logger.info(f"[{session_id}] Fix {result.rule_id}: {'OK' if result.success else 'FAILED'}")

        # ── 4. Determine outcome ─────────────────────────────────────────
        # Priority: AI create_ticket > hardware fix failed > hardware fix ok > no issues
        ai_escalate = diagnosis and diagnosis.get("action") == "create_ticket"

        if ai_escalate:
            # AI couldn't diagnose — escalate regardless of hardware fixes
            action = "escalate"
            summary = "Issue requires Service Desk attention — ticket will be created."
        elif fix_results and all(fr["success"] for fr in fix_results):
            action = "auto_resolved"
            summary = f"Auto-fixed {len(fix_results)} hardware issue(s): {', '.join(r['id'] for r in triggered)}."
        elif not triggered:
            action = "auto_resolved"
            summary = "No hardware issues detected. Device is operating within normal parameters."
        else:
            action = "guided_fix"
            summary = "Guided fix steps presented to the employee."

        # ── 5. Generate Word report ──────────────────────────────────────
        report_path = None
        if generate_report:
            try:
                output_dir = self.config.get("report", {}).get("output_dir", "reports")
                report_path = reporter.generate_report(
                    session_id=session_id,
                    employee=employee,
                    metrics=metrics,
                    triggered_rules=triggered,
                    fix_results=fix_results,
                    diagnosis=diagnosis or {},
                    outcome=action,
                    output_dir=output_dir,
                )
                logger.info(f"[{session_id}] Report saved: {report_path}")
            except Exception as e:
                logger.error(f"[{session_id}] Report generation failed: {e}")

        return EngineResult(
            session_id=session_id,
            metrics=metrics,
            triggered_rules=triggered,
            fix_results=fix_results,
            report_path=report_path,
            action=action,
            summary=summary,
        )

    def _match_rules(self, metrics: dict) -> list:
        """Check each rule's trigger condition against collected metrics."""
        triggered = []
        flat = {
            "cpu_percent":    metrics["cpu"]["percent"],
            "memory_percent": metrics["memory"]["percent"],
            "disk_percent":   metrics["disk"]["percent"],
            "disk_free_gb":   metrics["disk"]["free_gb"],
            "battery_percent": metrics["battery"]["percent"] if metrics["battery"]["percent"] else 100,
        }

        ops = {">": lambda a, b: a > b, "<": lambda a, b: a < b,
               ">=": lambda a, b: a >= b, "<=": lambda a, b: a <= b,
               "==": lambda a, b: a == b}

        for rule in self.rules:
            trigger = rule.get("trigger", {})
            metric  = trigger.get("metric")
            op_str  = trigger.get("operator", ">")
            value   = trigger.get("value")
            if metric and metric in flat and op_str in ops:
                if ops[op_str](flat[metric], value):
                    triggered.append(rule)

        return triggered
