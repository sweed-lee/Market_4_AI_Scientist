"""
Checkpoint save/load utilities.

We support two checkpoint kinds:
1) founder_submitted: after founders have produced submissions, before investor evaluation
2) investor_evaluated: after investor evaluation has finished for a major round

The checkpoint is JSON and can be loaded to reconstruct the full system state and resume.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable, Dict, Optional, Tuple
import json

from agents.founder import Founder
from agents.investor import Investor, InvestorGroup


CHECKPOINT_VERSION = 1


def _utc_ts() -> str:
    return datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")


def save_checkpoint_file(path: str, checkpoint: Dict[str, Any]) -> str:
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    with open(p, "w", encoding="utf-8") as f:
        json.dump(checkpoint, f, indent=2, ensure_ascii=False)
    return str(p)


def load_checkpoint_file(path: str) -> Dict[str, Any]:
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def build_checkpoint(
    *,
    kind: str,
    config: Dict[str, Any],
    orchestrator: Any,
    major_round: int,
    payload: Dict[str, Any],
) -> Dict[str, Any]:
    """Build a serializable checkpoint dict."""
    founders_state = {}
    for f in orchestrator.founders:
        founders_state[f.name] = {
            "config": f.config,
            "history": f.history,
            "current_title": getattr(f, "current_title", None),
            "current_budget": getattr(f, "current_budget", None),
            "current_strategy": getattr(f, "current_strategy", None),
            "current_prototype": getattr(f, "current_prototype", None),
            "total_budget": getattr(f, "total_budget", 0),
            "accumulated_investment": getattr(f, "accumulated_investment", 0),
            "round_scores": getattr(f, "round_scores", []),
            "current_round": getattr(f, "current_round", None),
        }

    groups_state = {}
    for g in orchestrator.investor_groups:
        groups_state[g.name] = {
            "initial_capital": getattr(g, "initial_capital", None),
            "total_capital": getattr(g, "total_capital", None),
            "k_selection": getattr(g, "k_selection", None),
            "round1_max_workers": getattr(g, "round1_max_workers", None),
            "history": getattr(g, "history", []),
            "step1_cache": getattr(g, "step1_cache", {}),
            "investors": [
                {
                    "name": inv.name,
                    "criteria": getattr(inv, "criteria", ""),
                    "philosophy": getattr(inv, "philosophy", ""),
                    "model": getattr(inv, "model", None),
                    "history": getattr(inv, "history", []),
                }
                for inv in getattr(g, "investors", [])
            ],
        }

    return {
        "version": CHECKPOINT_VERSION,
        "kind": kind,
        "timestamp_utc": _utc_ts(),
        "major_round": int(major_round),
        "config": config,
        "orchestrator": {
            "history": orchestrator.history,
            "graph_mode": orchestrator.graph_mode,
        },
        "agents": {
            "founders": founders_state,
            "investor_groups": groups_state,
        },
        "payload": payload,
    }


def _create_agents_from_config(config: Dict[str, Any]) -> Tuple[list[Founder], list[InvestorGroup]]:
    """Local agent factory (avoids importing main scripts)."""
    founders = []
    for founder_cfg in config.get("founders", []):
        founders.append(
            Founder(
                name=founder_cfg["name"],
                config={
                    "specialization": founder_cfg.get("specialization"),
                    "model": founder_cfg.get("model"),
                    "instruction": founder_cfg.get("instruction"),
                },
            )
        )

    investor_groups = []
    for group_cfg in config.get("investor_groups", []):
        investors = []
        for inv_cfg in group_cfg.get("investors", []):
            investors.append(
                Investor(
                    name=inv_cfg["name"],
                    config={
                        "criteria": inv_cfg.get("criteria"),
                        "philosophy": inv_cfg.get("philosophy"),
                        "model": inv_cfg.get("model"),
                    },
                )
            )
        investor_groups.append(
            InvestorGroup(
                name=group_cfg["name"],
                investors=investors,
                total_capital=group_cfg.get("total_capital", 100.0),
                k_selection=group_cfg.get("k_selection", config.get("system", {}).get("k_selection")),
                round1_max_workers=group_cfg.get("round1_max_workers"),
            )
        )

    return founders, investor_groups


def orchestrator_from_checkpoint(
    checkpoint: Dict[str, Any],
    *,
    llm_callback: Optional[Callable] = None,
) -> Any:
    """Rebuild orchestrator + agents from checkpoint (no execution)."""
    config = checkpoint["config"]
    founders, groups = _create_agents_from_config(config)
    # Import here to avoid circular imports when orchestrator also uses checkpointing.
    from system.orchestrator import SystemOrchestrator  # noqa: WPS433

    orch = SystemOrchestrator(founders=founders, investor_groups=groups, config=config, llm_callback=llm_callback)

    orch.history = checkpoint.get("orchestrator", {}).get("history", []) or []

    # Restore founders
    f_state = checkpoint.get("agents", {}).get("founders", {}) or {}
    for f in orch.founders:
        st = f_state.get(f.name, {})
        f.history = st.get("history", []) or []
        f.current_title = st.get("current_title")
        f.current_budget = st.get("current_budget")
        f.current_strategy = st.get("current_strategy")
        f.current_prototype = st.get("current_prototype")
        f.total_budget = st.get("total_budget", 0)
        f.accumulated_investment = st.get("accumulated_investment", 0)
        f.round_scores = st.get("round_scores", []) or []
        f.current_round = st.get("current_round")

    # Restore investor groups
    g_state = checkpoint.get("agents", {}).get("investor_groups", {}) or {}
    for g in orch.investor_groups:
        st = g_state.get(g.name, {})
        if "total_capital" in st:
            g.total_capital = st["total_capital"]
        if "initial_capital" in st and st["initial_capital"] is not None:
            g.initial_capital = st["initial_capital"]
        g.k_selection = st.get("k_selection", g.k_selection)
        g.round1_max_workers = st.get("round1_max_workers", g.round1_max_workers)
        g.history = st.get("history", []) or []
        g.step1_cache = st.get("step1_cache", {}) or {}
        # Note: per-investor histories are not critical for execution; keep as-is.
    return orch


def resume_from_checkpoint(
    checkpoint_path: str,
    *,
    llm_callback: Optional[Callable] = None,
) -> Dict[str, Any]:
    """
    Load checkpoint and resume execution from that exact phase.

    Returns the final `orchestrator.run()` results-like dict.
    """
    ckpt = load_checkpoint_file(checkpoint_path)
    orch = orchestrator_from_checkpoint(ckpt, llm_callback=llm_callback)

    kind = ckpt.get("kind")
    major_round = int(ckpt.get("major_round", 1))
    payload = ckpt.get("payload", {}) or {}

    if kind == "founder_submitted":
        # We are right before investor evaluation for `major_round`.
        # Execute investor evaluation and then continue remaining major rounds.
        strategies = payload["strategies"]
        titles = payload["titles"]
        budgets = payload["budgets"]
        prototypes = payload.get("prototypes", {})
        proposals = payload.get("proposals", {})
        founder_requirements = payload.get("founder_requirements", {})
        previous_history = payload.get("previous_major_round_history")

        investment_result = orch._run_investment_rounds(  # noqa: SLF001 (intentional internal resume)
            strategies,
            titles,
            budgets,
            founder_requirements,
            previous_history,
            prototypes,
        )

        all_scores = investment_result["all_scores"]
        investor_feedback = investment_result["investor_feedback"]
        investment_history = investment_result["investment_history"]
        accumulated_investments = investment_result["accumulated_investments"]

        for f in orch.founders:
            f.accumulated_investment = accumulated_investments.get(f.name, 0)

        founder_scores = {}
        for f in orch.founders:
            total = 0.0
            for group in orch.investor_groups:
                if f.name in orch.interaction_graph.get(group.name, []):
                    total += all_scores.get(group.name, {}).get(f.name, 0.0)
            founder_scores[f.name] = total

        round_data = {
            "round": major_round,
            "strategies": strategies,
            "proposals": proposals,
            "titles": titles,
            "budgets": budgets,
            "budget_bounds": {
                name: {
                    "budget": int(budgets.get(name, 0) or 0),
                    "lower_bound": int((budgets.get(name, 0) or 0) * (1 - orch.budget_tolerance_percent)),
                    "upper_bound": int((budgets.get(name, 0) or 0) * (1 + orch.budget_tolerance_percent)),
                }
                for name in budgets.keys()
            },
            "prototypes": prototypes,
            "all_scores": all_scores,
            "founder_scores": founder_scores,
            "investor_feedback": investor_feedback,
            "investment_history": investment_history,
        }
        orch.history.append(round_data)

        # Continue remaining major rounds (iteration rounds)
        for rn in range(major_round + 1, orch.num_rounds + 1):
            orch.history.append(orch._iteration_round(rn))  # noqa: SLF001

        final_scores = orch._calculate_final_scores()  # noqa: SLF001
        winner = max(final_scores.items(), key=lambda x: x[1])
        all_investment_history = {}
        for mr in range(1, orch.num_rounds + 1):
            mr_key = f"major_round_{mr}"
            all_investment_history[mr_key] = orch.history[mr - 1].get("investment_history", {}) if mr - 1 < len(orch.history) else {}

        return {
            "winner": winner[0],
            "winner_score": winner[1],
            "final_scores": final_scores,
            "all_rounds": orch.history,
            "requirements": {f.name: getattr(f, "instruction", "") for f in orch.founders},
            "investment_history": all_investment_history,
        }

    if kind == "investor_evaluated":
        # We have a completed round_data that should be appended, then continue next rounds.
        round_data = payload["round_data"]
        if not orch.history or orch.history[-1].get("round") != round_data.get("round"):
            orch.history.append(round_data)
        for rn in range(int(round_data["round"]) + 1, orch.num_rounds + 1):
            orch.history.append(orch._iteration_round(rn))  # noqa: SLF001
        # Finish like run()
        final_scores = orch._calculate_final_scores()  # noqa: SLF001
        winner = max(final_scores.items(), key=lambda x: x[1])
        all_investment_history = {}
        for mr in range(1, orch.num_rounds + 1):
            mr_key = f"major_round_{mr}"
            all_investment_history[mr_key] = orch.history[mr - 1].get("investment_history", {}) if mr - 1 < len(orch.history) else {}
        return {
            "winner": winner[0],
            "winner_score": winner[1],
            "final_scores": final_scores,
            "all_rounds": orch.history,
            "requirements": {f.name: getattr(f, "instruction", "") for f in orch.founders},
            "investment_history": all_investment_history,
        }

    raise ValueError(f"Unknown checkpoint kind: {kind}")

