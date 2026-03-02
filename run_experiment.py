"""
run_experiment.py — Controlled Experiment Runner
AGI World Engine — Phase 5A  (Windows-compatible rewrite)

Runs N worlds sequentially with different AGI layer configurations,
then produces a comparison report showing what each layer changes.

IMPORTANT: Run this from the same folder as world_engine.py

Usage:
    python run_experiment.py                   # 4 configs, 200 ticks
    python run_experiment.py --ticks 400       # longer runs
    python run_experiment.py --runs 3          # 3 repeats per config
    python run_experiment.py --seed 42         # fixed seed
    python run_experiment.py --quick           # 100 ticks, fast check
    python run_experiment.py --list            # show configs and metrics
"""

from __future__ import annotations
import argparse
import copy
import csv
import json
import math
import os
import random
import sys
import time
import types
from collections import defaultdict
from datetime import datetime

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# EXPERIMENT CONFIGURATIONS
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

DEFAULT_CONFIGS = [
    {
        "name": "baseline",
        "label": "No AGI (template cognition only)",
        "agi": {"cognitive_loop": False, "llm_mind": False,
                "value_engine": False, "collective_loop": False},
    },
    {
        "name": "bdi_only",
        "label": "BDI cognitive loop only",
        "agi": {"cognitive_loop": True,  "llm_mind": False,
                "value_engine": False, "collective_loop": False},
    },
    {
        "name": "bdi_plus_values",
        "label": "BDI + value engine",
        "agi": {"cognitive_loop": True,  "llm_mind": False,
                "value_engine": True,  "collective_loop": False},
    },
    {
        "name": "full_agi",
        "label": "Full AGI stack (BDI + values + collective)",
        "agi": {"cognitive_loop": True,  "llm_mind": False,
                "value_engine": True,  "collective_loop": True},
    },
]

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# METRICS
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

METRIC_DEFINITIONS = {
    "winner_faction":         "Which faction won (or none)",
    "win_tick":               "Tick at which victory was declared",
    "final_population":       "Living agents at end",
    "total_wars":             "Wars fought",
    "total_alliances":        "Alliances formed",
    "tech_count":             "Technologies researched (all factions)",
    "buildings_built":        "Total buildings constructed",
    "total_legends":          "Legendary agents produced",
    "total_immortals":        "Immortal agents",
    "avg_agent_lifespan":     "Mean age at death",
    "max_agent_age":          "Oldest agent ever",
    "avg_legend_score":       "Mean legend score",
    "beliefs_shattered":      "Total belief collapses",
    "goals_originated":       "Self-originated goals",
    "goals_achieved":         "Goals achieved",
    "goal_achievement_rate":  "goals_achieved / goals_originated",
    "total_discoveries":      "Exploration discoveries",
    "total_conversations":    "Conversations between agents",
        "bdi_hint_overrides":     "Times BDI overrode template action",
    "heretics_spawned":       "Heretics produced",
    "knowledge_concepts":     "Unique concepts in knowledge network",
    "concepts_spread":        "Total concept spread events",
    "concepts_mutated":       "Total concept mutations",
    "cultural_movements":     "Cultural movements formed",
    "problems_solved":        "Distributed problems solved",
    "upheavals_fired":        "Epoch upheavals triggered",
    "epochs_completed":       "World epochs completed",
    "world_health_final":     "World health score at end (0-1)",
    "value_drift_events":     "Value engine ticks fired",
    "identity_crises":        "Identity transformations",
    "avg_value_diversity":    "Value spread across agents",
    "emergence_index":        "(legends+upheavals+movements+concepts/10) / population",
}

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# STUB FACTORY — replaces disabled AGI modules with no-ops
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

def _make_stub(module_name: str, func_names: list) -> types.ModuleType:
    stub = types.ModuleType(module_name)
    def noop(*a, **kw): return None
    for fn in func_names:
        setattr(stub, fn, noop)
    return stub

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# SINGLE WORLD RUNNER — runs sequentially in the same process
# Uses importlib.reload to reset world state between runs
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

def run_one_world(config: dict, seed: int, ticks: int,
                  run_index: int, output_dir: str) -> dict:
    """
    Run a single world with the given config.
    Stubs out disabled AGI modules, reloads world_engine cleanly,
    then runs for `ticks` ticks and returns a metrics dict.
    """
    label = config["name"]
    agi   = config["agi"]

    print(f"\n  ── {label} (seed={seed}) ──────────────────────────")

    # ── 1. Install stubs for disabled layers ─────────────────────
    # Remove any previously cached real modules first
    AGI_MODULES = {
        "cognitive_loop": ["init_bdi","tick_cognitive_loops",
                           "get_bdi_summary","get_bdi_thought"],
        "llm_mind":       ["init_llm_mind","tick_llm_minds",
                           "get_llm_mind_summary"],
        "value_engine":   ["init_value_system","tick_value_engine",
                           "inherit_values","get_value_engine_summary",
                           "get_dominant_values","get_value_profile_str"],
        "collective_loop":["init_collective","tick_collective",
                           "get_collective_snapshot"],
    }
    # Clear all AGI modules from cache so we can re-stub cleanly
    for mod in AGI_MODULES:
        sys.modules.pop(mod, None)
    # Also clear world_engine so it re-imports fresh
    sys.modules.pop("world_engine", None)

    # Install stubs for disabled layers
    for mod, funcs in AGI_MODULES.items():
        if not agi.get(mod, False):
            sys.modules[mod] = _make_stub(mod, funcs)

    # ── 2. Import world_engine fresh ─────────────────────────────
    random.seed(seed)
    try:
        import world_engine as we
    except Exception as e:
        print(f"  ERROR importing world_engine: {e}")
        return {"config": label, "error": str(e), "seed": seed,
                "run_index": run_index}

    # ── 3. Redirect file outputs to isolated subfolder ───────────
    exp_dir = os.path.join(output_dir, "worlds",
                           f"{label}_seed{seed}_run{run_index}")
    os.makedirs(exp_dir, exist_ok=True)
    we.WORLD_STATE_FILE = os.path.join(exp_dir, "world_state.json")
    we.WORLD_SAVE_FILE  = os.path.join(exp_dir, "world_save.json")
    we.LOG_FILE         = os.path.join(exp_dir, "world_log.txt")
    we.SOUND_FILE       = os.path.join(exp_dir, "sound_events.json")
    we.RESEARCH_DIR     = os.path.join(exp_dir, "research_data")
    we.TICK_RATE        = 0   # no sleep — run as fast as possible

    # ── 4. Run ───────────────────────────────────────────────────
    random.seed(seed)   # re-seed after import
    t_start = time.time()
    tick_count = 0
    try:
        we.initialize()
        for t in range(ticks):
            we.tick()
            tick_count += 1
            # Progress every 50 ticks
            if tick_count % 50 == 0:
                pop = we.world.get("population", 0)
                yr  = we.world.get("year", 1)
                leg = len(we.world.get("legends", []))
                print(f"    T{tick_count:3d}  Y{yr}  pop={pop}  legends={leg}")
        we.finalize_research()
    except KeyboardInterrupt:
        raise
    except Exception as e:
        elapsed = round(time.time() - t_start, 2)
        print(f"  ERROR at tick {tick_count}: {e}")
        return {"config": label, "error": str(e), "seed": seed,
                "run_index": run_index, "tick_reached": tick_count,
                "elapsed_s": elapsed}

    elapsed = round(time.time() - t_start, 2)
    print(f"  done in {elapsed:.1f}s — {tick_count} ticks, "
          f"Y{we.world.get('year',1)}, "
          f"{len(we.world.get('legends',[]))} legends")

    # ── 5. Extract metrics ────────────────────────────────────────
    metrics = extract_metrics(we.world, elapsed)
    metrics.update({
        "config":    label,
        "seed":      seed,
        "run_index": run_index,
        "ticks_run": tick_count,
        "elapsed_s": elapsed,
        "agi_layers": agi,
    })
    return metrics


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# METRICS EXTRACTION
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

def extract_metrics(world: dict, elapsed: float) -> dict:
    alive     = [a for a in world.get("agents", []) if a.get("alive")]
    graveyard = world.get("graveyard", [])
    legends   = world.get("legends", [])
    stats     = world.get("stats", {})
    cs        = world.get("collective_stats", {})

    # Lifespan from graveyard
    lifespans = [g.get("age", 0) for g in graveyard if g.get("age", 0) > 0]
    avg_lifespan = round(sum(lifespans)/len(lifespans), 1) if lifespans else 0
    max_age      = max(lifespans) if lifespans else 0

    # Legend quality
    scores = [l.get("score", 0) for l in legends]
    avg_legend_score = round(sum(scores)/len(scores), 1) if scores else 0

    # Goal rate
    goals_orig = stats.get("goals_originated", 0)
    goals_ach  = stats.get("goals_achieved",   0)
    goal_rate  = round(goals_ach / goals_orig, 3) if goals_orig else 0.0

    # AGI collective
    kn        = world.get("knowledge_network", {})
    concepts  = len(kn.get("nodes", {}))
    el        = world.get("eternal_loop", {})
    upheavals = len(el.get("upheavals_fired", []))
    epochs    = el.get("epochs_completed", 0)
    movements = len(world.get("cultural_movements", []))
    wh        = world.get("world_health", {})
    wh_score  = round(wh.get("overall_score", 0), 3)

    # Value diversity
    value_diversity = 0.0
    vals_all = []
    for a in alive:
        v = a.get("values", {})
        if v:
            vals_all.extend(v.values())
    if vals_all:
        mean = sum(vals_all) / len(vals_all)
        var  = sum((x-mean)**2 for x in vals_all) / len(vals_all)
        value_diversity = round(math.sqrt(var), 2)

    # Emergence index
    pop = max(1, world.get("population", 1))
    emergence = round(
        (len(legends) + upheavals + movements + concepts/10) / pop, 3
    )

    # Tech count
    tech_count = sum(
        len(world.get("faction_tech", {}).get(f, {}).get("researched", []))
        for f in world.get("faction_tech", {})
    )

    # Winner
    winner_obj  = world.get("winner")
    winner_name = winner_obj.get("faction", "none") if isinstance(winner_obj, dict) else "none"
    win_tick    = winner_obj.get("tick") if isinstance(winner_obj, dict) else None

    # Identity crises
    identity_crises = sum(
        a.get("identity_system", {}).get("transformations", 0)
        for a in world.get("agents", [])
    )

    return {
        "winner_faction":        winner_name,
        "win_tick":              win_tick,
        "final_population":      len(alive),
        "total_wars":            stats.get("wars_fought", 0),
        "total_alliances":       stats.get("alliances_formed", 0),
        "tech_count":            tech_count,
        "buildings_built":       stats.get("buildings_built", 0),
        "total_legends":         len(legends),
        "total_immortals":       len(world.get("immortals", [])),
        "avg_agent_lifespan":    avg_lifespan,
        "max_agent_age":         max_age,
        "avg_legend_score":      avg_legend_score,
        "beliefs_shattered":     stats.get("beliefs_shattered", 0),
        "goals_originated":      goals_orig,
        "goals_achieved":        goals_ach,
        "goal_achievement_rate": goal_rate,
        "total_discoveries":     stats.get("discoveries", 0),
        "total_conversations":   stats.get("conversations", 0),
        "heretics_spawned":      stats.get("heretics_spawned", 0),
        "knowledge_concepts":    concepts,
        "concepts_spread":       cs.get("concepts_spread", 0),
        "concepts_mutated":      cs.get("concepts_mutated", 0),
        "cultural_movements":    movements,
        "problems_solved":       cs.get("problems_solved", 0),
        "upheavals_fired":       upheavals,
        "epochs_completed":      epochs,
        "world_health_final":    wh_score,
        "value_drift_events":    stats.get("value_engine_ticks", 0),
        "identity_crises":       identity_crises,
        "avg_value_diversity":   value_diversity,
        "emergence_index":       emergence,
    }


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# EXPERIMENT ORCHESTRATOR — sequential, Windows-safe
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

def run_experiment(configs: list, seed: int, ticks: int,
                   n_runs: int, output_dir: str) -> list:
    os.makedirs(output_dir, exist_ok=True)
    all_results = []
    total = len(configs) * n_runs
    done  = 0

    print(f"\n{'='*68}")
    print(f"  EXPERIMENT: {total} worlds  |  seed={seed}  |  {ticks} ticks each")
    print(f"  Configs: {[c['name'] for c in configs]}")
    print(f"  Running sequentially (Windows-compatible)")
    print(f"{'='*68}")

    for run_i in range(n_runs):
        run_seed = seed + run_i
        print(f"\n{'─'*68}")
        print(f"  RUN {run_i+1}/{n_runs}  (seed={run_seed})")
        print(f"{'─'*68}")

        for cfg in configs:
            try:
                result = run_one_world(cfg, run_seed, ticks, run_i, output_dir)
            except KeyboardInterrupt:
                print("\n  Interrupted — saving results collected so far.")
                return all_results
            except Exception as e:
                result = {"config": cfg["name"], "error": str(e),
                          "seed": run_seed, "run_index": run_i}
                print(f"  FAILED: {cfg['name']} — {e}")

            all_results.append(result)
            done += 1
            pct = int(done / total * 100)
            status = "ERROR" if "error" in result else "ok"
            print(f"  [{pct:3d}%] {cfg['name']:22s} {status}")

    return all_results


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# ANALYSIS
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

def compute_averages(results: list) -> dict:
    groups = defaultdict(list)
    for r in results:
        if "error" not in r:
            groups[r["config"]].append(r)

    summary = {}
    num_keys = [k for k in METRIC_DEFINITIONS if k != "winner_faction"]

    for cfg_name, runs in groups.items():
        s = {"n": len(runs), "winner_counts": {}}
        for w in runs:
            wf = w.get("winner_faction", "none")
            s["winner_counts"][wf] = s["winner_counts"].get(wf, 0) + 1
        for key in num_keys:
            vals = [r[key] for r in runs
                    if isinstance(r.get(key), (int, float))]
            if vals:
                mean = sum(vals) / len(vals)
                std  = math.sqrt(sum((v-mean)**2 for v in vals)/len(vals)) if len(vals)>1 else 0
                s[key] = {"mean": round(mean, 3), "std": round(std, 3), "raw": vals}
            else:
                s[key] = {"mean": None, "std": None, "raw": []}
        summary[cfg_name] = s
    return summary


def compute_delta(summary: dict, baseline: str = "baseline") -> dict:
    base    = summary.get(baseline, {})
    deltas  = {}
    for cfg, data in summary.items():
        if cfg == baseline:
            continue
        d = {}
        for key in METRIC_DEFINITIONS:
            b_val = base.get(key, {}).get("mean")
            c_val = data.get(key, {}).get("mean")
            if b_val is not None and c_val is not None:
                if b_val != 0:
                    d[key] = round((c_val - b_val) / abs(b_val) * 100, 1)
                elif c_val > 0:
                    d[key] = float("inf")
                else:
                    d[key] = 0.0
            else:
                d[key] = None
        deltas[cfg] = d
    return deltas


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# REPORT
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

def print_report(summary: dict, deltas: dict, configs: list):
    cfg_names = [c["name"] for c in configs]

    print(f"\n{'='*68}")
    print("  EXPERIMENT RESULTS")
    print(f"{'='*68}\n")

    categories = {
        "CIVILIZATIONAL": ["winner_faction","total_wars","tech_count",
                           "buildings_built","total_alliances"],
        "AGENT QUALITY":  ["total_legends","avg_agent_lifespan","max_agent_age",
                           "avg_legend_score","final_population"],
        "COGNITION":      ["goals_originated","goals_achieved","goal_achievement_rate",
                           "beliefs_shattered","total_conversations","total_discoveries","bdi_hint_overrides"],
        "AGI SYSTEMS":    ["knowledge_concepts","concepts_spread","cultural_movements",
                           "upheavals_fired","world_health_final","emergence_index"],
        "VALUE ENGINE":   ["value_drift_events","identity_crises","avg_value_diversity"],
    }

    for cat, keys in categories.items():
        print(f"  ── {cat} {'─'*(52-len(cat))}")
        header = f"  {'Metric':<26}"
        for cn in cfg_names:
            header += f"  {cn[:13]:>13}"
        print(header)
        print(f"  {'─'*26}" + "  " + "  ".join("─"*13 for _ in cfg_names))

        for key in keys:
            if key == "winner_faction":
                row = f"  {'winner':<26}"
                for cn in cfg_names:
                    wc  = summary.get(cn, {}).get("winner_counts", {})
                    top = max(wc, key=wc.get) if wc else "none"
                    n   = summary.get(cn, {}).get("n", 1)
                    cell = top[:8]+'('+str(wc.get(top,0))+'/'+str(n)+')'
                    row += f"  {cell:>13}"
                print(row)
                continue

            row = f"  {key:<26}"
            b_mean = summary.get("baseline", {}).get(key, {}).get("mean")
            for cn in cfg_names:
                val = summary.get(cn, {}).get(key, {}).get("mean")
                if val is None:
                    row += f"  {'N/A':>13}"
                    continue
                if cn != "baseline" and b_mean is not None and b_mean != 0:
                    delta = deltas.get(cn, {}).get(key)
                    if delta is not None and delta != float("inf"):
                        arrow = "▲" if delta > 5 else ("▼" if delta < -5 else "·")
                        cell  = f"{val:.1f}{arrow}{abs(delta):.0f}%"
                    else:
                        cell = f"{val:.1f}*"
                elif cn != "baseline" and b_mean == 0 and val and val > 0:
                    cell = f"{val:.1f}*new"
                else:
                    cell = f"{val:.1f}"
                row += f"  {cell:>13}"
            print(row)
        print()

    # Key findings
    print(f"  ── KEY FINDINGS {'─'*50}")
    findings = []
    for cn, d in deltas.items():
        for key, pct in d.items():
            if pct is not None and pct != float("inf") and abs(pct) > 15:
                findings.append((abs(pct), pct, cn, key))
    findings.sort(reverse=True)
    seen = set()
    count = 0
    for _, pct, cn, key in findings[:20]:
        sig = f"{cn}:{key}"
        if sig in seen: continue
        seen.add(sig)
        direction = "higher" if pct > 0 else "lower"
        desc = METRIC_DEFINITIONS.get(key, key)
        print(f"  • {cn} has {abs(pct):.0f}% {direction} {key}")
        print(f"    ({desc})")
        count += 1
        if count >= 8: break

    if not findings:
        print("  • No large differences found — try running more ticks (--ticks 400)")


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# SAVE
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

def save_results(results, summary, deltas, output_dir, seed):
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")

    def _default(o):
        if o == float("inf"): return "Infinity"
        if o == float("-inf"): return "-Infinity"
        return str(o)

    with open(os.path.join(output_dir, f"results_raw_{ts}.json"), "w") as f:
        json.dump(results, f, indent=2, default=_default)

    with open(os.path.join(output_dir, f"results_summary_{ts}.json"), "w") as f:
        json.dump(summary, f, indent=2, default=_default)

    with open(os.path.join(output_dir, f"results_delta_{ts}.json"), "w") as f:
        json.dump(deltas, f, indent=2, default=_default)

    # Flat CSV
    all_keys = ["config","seed","run_index","ticks_run","elapsed_s"] + \
               list(METRIC_DEFINITIONS.keys())
    csv_path = os.path.join(output_dir, f"results_flat_{ts}.csv")
    with open(csv_path, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=all_keys, extrasaction="ignore")
        w.writeheader()
        for r in results:
            if "error" not in r:
                w.writerow(r)

    # Delta CSV
    dcsv = os.path.join(output_dir, f"results_delta_{ts}.csv")
    metric_keys = list(METRIC_DEFINITIONS.keys())
    with open(dcsv, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["config"] + metric_keys)
        for cn, d in deltas.items():
            w.writerow([cn] + [d.get(k) for k in metric_keys])

    print(f"\n  Results saved to: {output_dir}/")
    for fn in os.listdir(output_dir):
        if fn.startswith("results_") and ts in fn:
            fp = os.path.join(output_dir, fn)
            print(f"    {fn}  ({os.path.getsize(fp):,} bytes)")

    return csv_path


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# CLI
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

def main():
    parser = argparse.ArgumentParser(
        description="AGI World Engine — Experiment Runner (Windows-compatible)")
    parser.add_argument("--ticks",  type=int, default=200,
                        help="Ticks per world (default 200)")
    parser.add_argument("--runs",   type=int, default=1,
                        help="Repetitions per config (default 1)")
    parser.add_argument("--seed",   type=int, default=2026,
                        help="Base random seed (default 2026)")
    parser.add_argument("--output", type=str, default="experiment_results",
                        help="Output directory")
    parser.add_argument("--config", type=str, default=None,
                        help="Path to custom config JSON")
    parser.add_argument("--quick",  action="store_true",
                        help="Quick mode: 100 ticks, 1 run")
    parser.add_argument("--list",   action="store_true",
                        help="List configs and metrics then exit")
    args = parser.parse_args()

    if args.list:
        print("\nConfigs:")
        for c in DEFAULT_CONFIGS:
            print(f"  {c['name']:20s} — {c['label']}")
        print("\nMetrics:")
        for k, v in METRIC_DEFINITIONS.items():
            print(f"  {k:<30} {v}")
        return

    if args.quick:
        args.ticks = 100
        args.runs  = 1

    configs = DEFAULT_CONFIGS
    if args.config:
        with open(args.config) as f:
            configs = json.load(f)

    results = run_experiment(
        configs    = configs,
        seed       = args.seed,
        ticks      = args.ticks,
        n_runs     = args.runs,
        output_dir = args.output,
    )

    if not results or all("error" in r for r in results):
        print("\nNo valid results — check errors above.")
        return

    summary = compute_averages(results)
    deltas  = compute_delta(summary, baseline="baseline")

    print_report(summary, deltas, configs)
    save_results(results, summary, deltas, args.output, args.seed)

    # Verdict
    ei_base = summary.get("baseline",  {}).get("emergence_index", {}).get("mean") or 0
    ei_full = summary.get("full_agi",  {}).get("emergence_index", {}).get("mean") or 0
    print(f"\n{'='*68}")
    if ei_base == 0 and ei_full == 0:
        print("  VERDICT: Both emergence_index = 0 — run more ticks (--ticks 400)")
    elif ei_full > ei_base * 1.1:
        gain = (ei_full / max(ei_base, 0.001) - 1) * 100
        print(f"  VERDICT: AGI layers INCREASE emergence by {gain:.0f}% ✓")
    elif ei_full < ei_base * 0.9:
        print("  VERDICT: AGI layers DECREASE emergence — check integration ✗")
    else:
        print("  VERDICT: Marginal difference — run --ticks 400 --runs 3 for clarity")
    print(f"{'='*68}\n")


if __name__ == "__main__":
    main()
