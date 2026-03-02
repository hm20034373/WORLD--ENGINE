"""
╔══════════════════════════════════════════════════════════════════════╗
║           AGI WORLD ENGINE — COGNITIVE LOOP v1.0                    ║
║           Phase 1: BDI (Belief-Desire-Intention) Architecture        ║
╠══════════════════════════════════════════════════════════════════════╣
║  Each agent now runs a full cognitive cycle every tick:              ║
║                                                                      ║
║  1. PERCEIVE      — scan environment, build percept bundle           ║
║  2. BELIEVE       — update internal world model from percepts        ║
║  3. DESIRE        — generate desires ranked by urgency               ║
║  4. INTEND        — select best intention given beliefs + desires     ║
║  5. PLAN          — build multi-step action plan toward intention     ║
║  6. ACT           — execute next plan step                           ║
║  7. REFLECT       — evaluate outcome, update beliefs & self-model    ║
║                                                                      ║
║  Integrates with existing world_engine.py:                           ║
║    - Reads:  world dict, living(), recall(), personality()           ║
║    - Writes: agent["bdi"], agent["thought"], agent["target"]         ║
║    - Hooks:  replace agent_think() or wrap it                        ║
╚══════════════════════════════════════════════════════════════════════╝
"""

import random
import math
import json
from datetime import datetime

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# CONSTANTS
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

# How far an agent can "see" in each sense
PERCEPTION_RADIUS = {
    "sight":    12.0,   # physical entities
    "social":   8.0,    # agents to talk to
    "threat":   15.0,   # danger detection
    "resource": 10.0,   # buildings, resources
}

# Desire priority weights by agent type — what they care about most
DESIRE_WEIGHTS = {
    "warrior":      {"survive": 9, "fight": 8,    "protect": 6, "grow": 3, "connect": 2, "understand": 1},
    "explorer":     {"survive": 7, "discover": 9, "grow": 5,    "connect": 3, "fight": 2, "understand": 6},
    "builder":      {"survive": 7, "build": 9,    "grow": 6,    "connect": 4, "fight": 2, "understand": 3},
    "farmer":       {"survive": 8, "provide": 9,  "grow": 5,    "connect": 5, "fight": 1, "understand": 2},
    "scholar":      {"survive": 6, "understand": 9,"grow": 7,   "connect": 4, "fight": 1, "discover": 8},
    "merchant":     {"survive": 7, "trade": 9,    "grow": 7,    "connect": 7, "fight": 2, "understand": 4},
    "priest":       {"survive": 7, "convert": 8,  "protect": 5, "connect": 8, "fight": 1, "understand": 5},
    "spy":          {"survive": 9, "gather_intel": 9, "fight": 5, "connect": 3, "grow": 4, "understand": 7},
    "healer":       {"survive": 7, "heal": 9,     "protect": 8, "connect": 7, "fight": 1, "understand": 5},
    "assassin":     {"survive": 9, "hunt": 9,     "fight": 8,   "grow": 4,    "connect": 1, "understand": 3},
    "philosopher":  {"survive": 5, "understand": 10,"connect": 6,"grow": 5,   "fight": 1, "discover": 7},
    "crime_lord":   {"survive": 9, "control": 8,  "fight": 7,   "grow": 6,    "connect": 5, "trade": 5},
    "plague_doctor":{"survive": 8, "heal": 9,     "understand": 8,"protect": 7,"fight": 1, "discover": 6},
    "patriarch":    {"survive": 8, "protect": 9,  "connect": 8, "grow": 6,    "fight": 3, "understand": 4},
    "matriarch":    {"survive": 8, "protect": 9,  "connect": 9, "grow": 6,    "fight": 2, "understand": 5},
}

DEFAULT_DESIRE_WEIGHTS = {"survive": 7, "grow": 5, "connect": 4, "fight": 3, "understand": 4}

# Intentions map to concrete action plans
INTENTION_ACTIONS = {
    "survive":       ["seek_safety", "find_food", "flee_threat", "heal_self"],
    "fight":         ["approach_enemy", "attack", "regroup", "call_allies"],
    "discover":      ["move_to_unexplored", "examine_landmark", "map_area"],
    "build":         ["find_build_site", "gather_resources", "construct"],
    "trade":         ["find_merchant", "approach_trader", "negotiate"],
    "heal":          ["find_sick_agent", "approach_sick", "administer_care"],
    "convert":       ["find_nonbeliever", "approach_target", "preach"],
    "gather_intel":  ["shadow_target", "listen_nearby", "encode_intelligence"],
    "hunt":          ["track_target", "approach_stealthy", "strike"],
    "connect":       ["find_ally", "approach_friendly", "converse"],
    "protect":       ["find_vulnerable", "position_between", "guard"],
    "understand":    ["find_library", "observe_phenomenon", "contemplate"],
    "provide":       ["assess_food_need", "farm_area", "distribute"],
    "control":       ["identify_power_vacuum", "assert_dominance", "recruit"],
    "grow":          ["find_mentor", "practice_skill", "gain_experience"],
}

# How many ticks a plan persists before re-evaluation
PLAN_PERSISTENCE = (15, 40)

# Reflection outcomes map to memory types
REFLECTION_OUTCOMES = {
    "success":   ("joy",       4, "Plan succeeded: {plan} — outcome: {outcome}. Y{year}"),
    "partial":   ("discovery", 3, "Partial success on plan '{plan}'. Learned: {lesson}. Y{year}"),
    "failure":   ("discovery", 3, "Plan '{plan}' failed. Reassessing. Y{year}"),
    "abandoned": ("discovery", 2, "Abandoned plan '{plan}' — situation changed. Y{year}"),
}

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# BDI INITIALISATION
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

def init_bdi(agent):
    """
    Initialise the BDI mind for an agent.
    Safe to call multiple times — only sets missing fields.
    """
    if "bdi" in agent:
        return

    atype = agent.get("type", "explorer")

    agent["bdi"] = {
        # ── WORLD MODEL ─────────────────────────────────────────────
        "world_model": {
            "known_agents":     {},   # id → {name, type, faction, last_seen_tick, trust}
            "known_buildings":  {},   # id → {type, faction, position, last_seen_tick}
            "known_resources":  {},   # resource_type → estimated_quantity
            "threat_map":       [],   # [{position, severity, source, tick}]
            "opportunity_map":  [],   # [{type, position, value, tick}]
            "territory_belief": {},   # faction → estimated_power_zone
        },

        # ── DESIRE STACK ─────────────────────────────────────────────
        "desires": [],         # [{desire, priority, source, urgency, tick_born}]
        "desire_history": [],  # last 20 fulfilled/dropped desires

        # ── INTENTION ────────────────────────────────────────────────
        "current_intention": None,   # the chosen desire to act on now
        "intention_lock":    0,      # ticks remaining before can re-evaluate intention

        # ── PLAN ─────────────────────────────────────────────────────
        "current_plan": None,        # {name, steps, step_index, target, born_tick, reason}
        "plan_history": [],          # last 10 plans with outcomes

        # ── REFLECTION LOG ───────────────────────────────────────────
        "reflections":    [],        # last 20 reflections
        "last_reflection_tick": 0,

        # ── PERCEPT BUNDLE (last tick's perception) ──────────────────
        "last_percepts": {
            "nearby_agents":    [],
            "nearby_enemies":   [],
            "nearby_allies":    [],
            "nearby_buildings": [],
            "threats":          [],
            "opportunities":    [],
            "sensed_emotions":  [],
        },

        # ── COGNITIVE STATS ──────────────────────────────────────────
        "stats": {
            "total_cycles":       0,
            "plans_formed":       0,
            "plans_succeeded":    0,
            "plans_failed":       0,
            "intentions_changed": 0,
            "beliefs_updated":    0,
            "reflections_done":   0,
        },

        # ── META-COGNITION ───────────────────────────────────────────
        "meta": {
            "cognitive_load":     0.0,   # 0-1, how "busy" the mind is
            "confidence":         0.6,   # 0-1, general confidence in own decisions
            "decision_style":     _init_decision_style(atype),
            "last_cycle_quality": 0.0,   # self-assessed quality of last cognitive cycle
        },
    }


def _init_decision_style(atype):
    """Each agent type has a characteristic decision-making style."""
    styles = {
        "warrior":      {"deliberation": 0.3, "impulsiveness": 0.8, "risk_tolerance": 0.8},
        "explorer":     {"deliberation": 0.5, "impulsiveness": 0.5, "risk_tolerance": 0.7},
        "builder":      {"deliberation": 0.8, "impulsiveness": 0.2, "risk_tolerance": 0.3},
        "farmer":       {"deliberation": 0.7, "impulsiveness": 0.2, "risk_tolerance": 0.2},
        "scholar":      {"deliberation": 0.9, "impulsiveness": 0.1, "risk_tolerance": 0.4},
        "merchant":     {"deliberation": 0.7, "impulsiveness": 0.3, "risk_tolerance": 0.5},
        "priest":       {"deliberation": 0.6, "impulsiveness": 0.3, "risk_tolerance": 0.3},
        "spy":          {"deliberation": 0.8, "impulsiveness": 0.2, "risk_tolerance": 0.6},
        "healer":       {"deliberation": 0.7, "impulsiveness": 0.2, "risk_tolerance": 0.3},
        "assassin":     {"deliberation": 0.7, "impulsiveness": 0.4, "risk_tolerance": 0.7},
        "philosopher":  {"deliberation": 1.0, "impulsiveness": 0.0, "risk_tolerance": 0.3},
        "crime_lord":   {"deliberation": 0.7, "impulsiveness": 0.4, "risk_tolerance": 0.7},
        "plague_doctor":{"deliberation": 0.8, "impulsiveness": 0.2, "risk_tolerance": 0.5},
        "patriarch":    {"deliberation": 0.7, "impulsiveness": 0.3, "risk_tolerance": 0.4},
        "matriarch":    {"deliberation": 0.7, "impulsiveness": 0.3, "risk_tolerance": 0.4},
    }
    base = styles.get(atype, {"deliberation": 0.5, "impulsiveness": 0.5, "risk_tolerance": 0.5})
    # Add slight variation per agent
    return {k: max(0.0, min(1.0, v + random.uniform(-0.1, 0.1))) for k, v in base.items()}


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# PHASE 1 — PERCEIVE
# Build a percept bundle: what the agent can currently sense
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

def perceive(agent, world):
    """
    Scan the environment and return a percept bundle.
    This is pure sensing — no interpretation yet.
    """
    pos       = agent["position"]
    faction   = agent.get("faction", "?")
    all_alive = [a for a in world["agents"] if a["alive"] and a["id"] != agent["id"]]
    buildings = world.get("buildings", [])

    def d(other_pos):
        return math.sqrt((pos[0]-other_pos[0])**2 + (pos[1]-other_pos[1])**2)

    # ── NEARBY AGENTS (sight radius) ────────────────────────────────
    # Store lightweight summaries ONLY — avoids circular refs in JSON serialization
    def _summarise(a):
        return {
            "id": a["id"], "name": a["name"], "type": a.get("type","?"),
            "faction": a.get("faction","?"), "position": a["position"],
            "health": a.get("health",100), "emotion": a.get("emotion","content"),
            "battle_power": a.get("battle_power",10), "disease": a.get("disease"),
            "is_legend": a.get("is_legend",False), "age": a.get("age",0),
        }
    nearby_agents = [
        _summarise(a) for a in all_alive
        if d(a["position"]) <= PERCEPTION_RADIUS["sight"]
    ]

    # ── ALLIES vs ENEMIES ────────────────────────────────────────────
    from world_engine import get_diplo  # import from engine
    nearby_allies  = [s for s in nearby_agents if s["faction"] == faction]
    nearby_enemies = [
        s for s in nearby_agents
        if s["faction"] and s["faction"] != faction
        and get_diplo(faction, s["faction"]) == "war"
    ]

    # ── NEARBY BUILDINGS ─────────────────────────────────────────────
    nearby_buildings = [
        b for b in buildings
        if d(b["position"]) <= PERCEPTION_RADIUS["resource"]
    ]

    # ── THREATS ──────────────────────────────────────────────────────
    threats = []
    for enemy in nearby_enemies:
        severity = enemy.get("battle_power", 10) / max(1, agent.get("battle_power", 10))
        threats.append({
            "source":   enemy["name"],
            "faction":  enemy.get("faction", "?"),
            "position": enemy["position"],
            "severity": round(severity, 2),
            "type":     "enemy_agent",
        })

    # Detect disease carriers
    for a in nearby_agents:
        if a.get("disease"):
            threats.append({
                "source":   a["name"],
                "position": a["position"],
                "severity": 0.6,
                "type":     "disease_carrier",
            })

    # ── OPPORTUNITIES ────────────────────────────────────────────────
    opportunities = []

    # Injured allies = healing opportunity
    for ally in nearby_allies:
        if ally.get("health", 100) < 50 and agent.get("type") in ("healer", "plague_doctor"):
            opportunities.append({
                "type":     "heal_ally",
                "target":   ally["id"],
                "position": ally["position"],
                "value":    (100 - ally.get("health", 100)) / 10,
            })

    # Unguarded buildings = build/fortify opportunity
    enemy_buildings = [b for b in nearby_buildings if b.get("faction") != faction]
    for b in enemy_buildings:
        opportunities.append({
            "type":     "capture_building",
            "target":   b.get("id", "?"),
            "position": b["position"],
            "value":    3.0,
        })

    # Friendly agents to talk to
    for ally in nearby_allies:
        if d(ally["position"]) <= PERCEPTION_RADIUS["social"]:
            opportunities.append({
                "type":     "converse",
                "target":   ally["id"],
                "position": ally["position"],
                "value":    1.5,
            })

    # ── SENSED EMOTIONS ──────────────────────────────────────────────
    # Empathic agents sense the emotions of those nearby
    sensed_emotions = []
    if agent.get("type") in ("healer", "priest", "philosopher", "matriarch", "patriarch"):
        for a in nearby_agents[:5]:
            sensed_emotions.append({
                "agent": a["name"],
                "emotion": a.get("emotion", "content"),
                "health": a.get("health", 100),
            })

    percepts = {
        "nearby_agents":    nearby_agents,
        "nearby_allies":    nearby_allies,
        "nearby_enemies":   nearby_enemies,
        "nearby_buildings": nearby_buildings,
        "threats":          threats,
        "opportunities":    opportunities,
        "sensed_emotions":  sensed_emotions,
        "tick":             world["tick"],
        "weather":          world.get("weather", "clear"),
        "season":           world.get("season", "spring"),
        "biome":            _get_biome_safe(agent, world),
        "world_year":       world.get("year", 1),
    }

    # Store in agent's BDI
    agent["bdi"]["last_percepts"] = percepts
    return percepts


def _get_biome_safe(agent, world):
    try:
        from world_engine import get_biome
        return get_biome(agent["position"])
    except Exception:
        return "plains"


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# PHASE 2 — BELIEVE
# Update the agent's internal world model from percepts
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

def update_world_model(agent, percepts, world):
    """
    Integrate new percepts into the agent's persistent world model.
    The world model is the agent's BELIEFS about the world — it can be
    outdated, incomplete, or wrong.
    """
    bdi   = agent["bdi"]
    wm    = bdi["world_model"]
    tick  = world["tick"]
    faction = agent.get("faction", "?")

    # ── UPDATE KNOWN AGENTS ─────────────────────────────────────────
    for a in percepts["nearby_agents"]:
        aid = a["id"]
        existing = wm["known_agents"].get(aid, {})

        # Trust evolves: allies start trusted, enemies untrusted
        if a.get("faction") == faction:
            base_trust = existing.get("trust", 60)
        else:
            base_trust = existing.get("trust", 20)

        # Adjust trust based on memories
        memories = agent.get("memories", [])
        if any(a["name"] in m["content"] and m["type"] == "betrayal" for m in memories):
            base_trust = max(0, base_trust - 15)
        if any(a["name"] in m["content"] and m["type"] == "friend" for m in memories):
            base_trust = min(100, base_trust + 10)

        wm["known_agents"][aid] = {
            "name":          a["name"],
            "type":          a["type"],
            "faction":       a.get("faction", "?"),
            "last_seen_tick": tick,
            "last_position": a["position"],
            "trust":         base_trust,
            "health":        a.get("health", 100),
            "emotion":       a.get("emotion", "content"),
            "is_threat":     a in percepts["nearby_enemies"],
        }

    # ── UPDATE THREAT MAP ────────────────────────────────────────────
    # Decay old threats, add new ones
    wm["threat_map"] = [
        t for t in wm["threat_map"]
        if tick - t.get("tick", 0) < 30  # forget threats older than 30 ticks
    ]
    for threat in percepts["threats"]:
        wm["threat_map"].append({**threat, "tick": tick})

    # ── UPDATE OPPORTUNITY MAP ───────────────────────────────────────
    wm["opportunity_map"] = [
        o for o in wm["opportunity_map"]
        if tick - o.get("tick", 0) < 20
    ]
    for opp in percepts["opportunities"]:
        wm["opportunity_map"].append({**opp, "tick": tick})

    # ── UPDATE KNOWN BUILDINGS ───────────────────────────────────────
    for b in percepts["nearby_buildings"]:
        bid = b.get("id", str(b["position"]))
        wm["known_buildings"][bid] = {
            "type":          b["type"],
            "faction":       b.get("faction", "?"),
            "position":      b["position"],
            "last_seen_tick": tick,
        }

    # ── TERRITORY BELIEF UPDATE ──────────────────────────────────────
    # Count faction buildings in known_buildings to estimate territory
    from world_engine import FACTIONS
    faction_counts = {f: 0 for f in FACTIONS}
    for bid, bdata in wm["known_buildings"].items():
        bf = bdata.get("faction", "?")
        if bf in faction_counts:
            faction_counts[bf] += 1
    wm["territory_belief"] = faction_counts

    # ── RESOURCE BELIEF ──────────────────────────────────────────────
    # Agents don't know exact resources — they estimate from world state
    for res, amt in world.get("resources", {}).items():
        # Add noise — agents have imperfect knowledge
        noise = random.uniform(0.7, 1.3)
        wm["known_resources"][res] = round(amt * noise)

    bdi["stats"]["beliefs_updated"] += 1


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# PHASE 3 — DESIRE
# Generate a ranked stack of what the agent wants right now
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

def generate_desires(agent, percepts, world):
    """
    Build a prioritised desire stack from:
    - Basic needs (health, survival)
    - Type-specific drives
    - Active originated goals
    - Emotional state
    - Current situation (threats, opportunities)
    - Beliefs
    """
    bdi    = agent["bdi"]
    atype  = agent.get("type", "explorer")
    health = agent.get("health", 100)
    age    = agent.get("age", 0)
    emotion = agent.get("emotion", "content")
    beliefs = agent.get("beliefs", {})
    orig_goals = agent.get("originated_goals", [])
    memories = agent.get("memories", [])

    desires = []

    weights = DESIRE_WEIGHTS.get(atype, DEFAULT_DESIRE_WEIGHTS)

    def add_desire(name, priority, urgency, source, reasoning=""):
        desires.append({
            "desire":    name,
            "priority":  priority,
            "urgency":   urgency,
            "source":    source,
            "reasoning": reasoning,
            "tick_born": world["tick"],
        })

    # ── SURVIVAL DESIRES ─────────────────────────────────────────────
    if health < 25:
        add_desire("survive", 10, 10, "critical_health",
                   "Health critical at %d — must survive above all else." % health)
    elif health < 50:
        add_desire("survive", 8, 8, "low_health",
                   "Health low at %d — prioritising safety." % health)

    # Direct threat → fight or flee
    if percepts["threats"]:
        max_threat = max(percepts["threats"], key=lambda t: t["severity"])
        style = bdi["meta"]["decision_style"]
        if max_threat["severity"] > 1.5 or health < 40:
            # Threat is stronger than us or we're weak → flee
            add_desire("survive", 9, 9, "threat_detected",
                       "Threat from %s is severe (severity %.1f). Flee." % (
                           max_threat["source"], max_threat["severity"]))
        elif style["risk_tolerance"] > 0.6:
            # We're brave and capable → fight
            add_desire("fight", weights.get("fight", 3) + 3, 7, "threat_detected",
                       "Threat from %s detected. Capable of fighting." % max_threat["source"])

    # ── TYPE CORE DESIRES ────────────────────────────────────────────
    # Each type has a driving desire that never goes away
    # Type core urgency intentionally LOW (3) so emotional/situational/belief
    # desires (urgency 5-9) regularly beat it → cross-type BDI behaviour
    # e.g. a grieving warrior (connect, urgency 6) seeks allies instead of fighting
    # a lonely builder (connect, urgency 7) socialises instead of building
    type_core_desires = {
        "warrior":      ("fight",          5, 3, "type_drive"),
        "explorer":     ("discover",       6, 3, "type_drive"),
        "builder":      ("build",          6, 3, "type_drive"),
        "farmer":       ("provide",        5, 3, "type_drive"),
        "scholar":      ("understand",     6, 3, "type_drive"),
        "merchant":     ("trade",          6, 3, "type_drive"),
        "priest":       ("convert",        5, 3, "type_drive"),
        "spy":          ("gather_intel",   6, 3, "type_drive"),
        "healer":       ("heal",           6, 3, "type_drive"),
        "assassin":     ("hunt",           6, 3, "type_drive"),
        "philosopher":  ("understand",     6, 4, "type_drive"),
        "crime_lord":   ("control",        6, 3, "type_drive"),
        "plague_doctor":("heal",           6, 3, "type_drive"),
        "patriarch":    ("protect",        6, 3, "type_drive"),
        "matriarch":    ("protect",        6, 3, "type_drive"),
    }
    if atype in type_core_desires:
        add_desire(*type_core_desires[atype],
                   reasoning="Core drive of a %s." % atype)

    # ── ORIGINATED GOAL DESIRES ──────────────────────────────────────
    # Active originated goals become desires with high priority
    for goal in orig_goals:
        if not goal.get("active"):
            continue
        gtype = goal.get("type", "grow")
        desire_map = {
            "revenge":     ("fight",      8, 8),
            "protection":  ("protect",    8, 7),
            "legacy":      ("grow",       7, 6),
            "peace":       ("connect",    7, 6),
            "understanding":("understand",8, 7),
            "identity":    ("understand", 7, 6),
            "mastery":     ("grow",       8, 7),
            "resistance":  ("fight",      7, 6),
        }
        if gtype in desire_map:
            d, pri, urg = desire_map[gtype]
            add_desire(d, pri, urg, "originated_goal",
                       "Goal '%s' demands this." % goal["goal"])

    # ── EMOTION-DRIVEN DESIRES ───────────────────────────────────────
    emotion_desires = {
        "grieving":  ("connect",    5, 6, "need company in grief"),
        "angry":     ("fight",      7, 7, "anger demands outlet"),
        "inspired":  ("understand", 7, 6, "inspiration drives inquiry"),
        "afraid":    ("survive",    8, 8, "fear drives self-preservation"),
        "lonely":    ("connect",    7, 7, "loneliness demands connection"),
        "vengeful":  ("fight",      8, 8, "vengeance must be served"),
        "devoted":   ("convert",    7, 6, "devotion spreads faith"),
        "proud":     ("grow",       6, 5, "pride seeks more achievement"),
        "curious":   ("discover",   7, 6, "curiosity demands exploration"),
        "joyful":    ("connect",    6, 5, "joy wants to be shared"),
        "weary":     ("survive",    5, 4, "weariness demands rest"),
    }
    if emotion in emotion_desires:
        name, pri, urg, reason = emotion_desires[emotion]
        add_desire(name, pri, urg, "emotion",
                   "Feeling %s: %s." % (emotion, reason))

    # ── BELIEF-DRIVEN DESIRES ─────────────────────────────────────────
    if beliefs.get("knowledge_is_power", {}).get("confidence", 0) > 70:
        add_desire("understand", 6, 5, "belief",
                   "I believe knowledge is power. Seek it.")
    if beliefs.get("strength_wins", {}).get("confidence", 0) > 70:
        add_desire("fight", 6, 5, "belief",
                   "I believe strength wins. Demonstrate it.")
    if beliefs.get("cooperation_works", {}).get("confidence", 0) > 65:
        add_desire("connect", 5, 4, "belief",
                   "I believe cooperation works. Seek allies.")
    # Reversed beliefs
    if beliefs.get("cooperation_works", {}).get("value") == False:
        add_desire("survive", 6, 5, "belief_reversed",
                   "Trust no one — stay alert and independent.")

    # ── OPPORTUNITY DESIRES ───────────────────────────────────────────
    for opp in percepts["opportunities"]:
        if opp["type"] == "heal_ally" and atype in ("healer", "plague_doctor"):
            add_desire("heal", 8, 8, "opportunity",
                       "Wounded ally nearby — heal them now.")
        elif opp["type"] == "converse" and health > 60:
            add_desire("connect", 4, 3, "opportunity",
                       "Friendly agent nearby — opportunity to connect.")

    # ── AGE-DRIVEN DESIRES ────────────────────────────────────────────
    if age > 300:
        add_desire("connect", 6, 5, "elder_wisdom",
                   "At age %d, I want to pass on what I know." % age)
    if age < 30:
        add_desire("grow", 6, 5, "youth",
                   "Young and hungry to learn everything.")

    # ── DEDUPLICATE & SORT ────────────────────────────────────────────
    # Merge duplicate desire types by taking highest urgency
    desire_map_merged = {}
    for d in desires:
        key = d["desire"]
        if key not in desire_map_merged or d["urgency"] > desire_map_merged[key]["urgency"]:
            desire_map_merged[key] = d
    desires = sorted(desire_map_merged.values(), key=lambda d: -d["urgency"])

    bdi["desires"] = desires
    return desires


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# PHASE 4 — INTEND
# Select the best intention from the desire stack
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

def select_intention(agent, desires, world):
    """
    From the ranked desire stack, select a single intention to commit to.

    The agent doesn't always pick the top desire. Decision style affects:
    - Impulsive agents → pick top desire immediately
    - Deliberate agents → weigh options before committing
    - Risk-averse agents → avoid high-risk intentions when healthy

    Returns the selected desire dict, or None.
    """
    bdi   = agent["bdi"]
    style = bdi["meta"]["decision_style"]

    if not desires:
        return None

    # Intention lock — don't change intention every tick
    if bdi["intention_lock"] > 0:
        bdi["intention_lock"] -= 1
        return bdi.get("current_intention")

    # Impulsive agents → top desire wins
    if style["impulsiveness"] > 0.7 and random.random() < style["impulsiveness"]:
        chosen = desires[0]
    else:
        # Deliberate agents consider top 3 and may not pick #1
        top_n = desires[:3]

        # Risk-averse agents drop high-risk options when safe
        if style["risk_tolerance"] < 0.4:
            risky = {"fight", "hunt", "gather_intel"}
            health = agent.get("health", 100)
            if health > 70:  # only avoid risk when we can afford to
                top_n = [d for d in top_n if d["desire"] not in risky] or top_n

        # Deliberate agents add slight randomness (thinking leads to surprising choices)
        if style["deliberation"] > 0.7:
            weights_deliberate = [1.0 / (i + 1) for i in range(len(top_n))]
            chosen = random.choices(top_n, weights=weights_deliberate, k=1)[0]
        else:
            chosen = top_n[0]

    # Check if intention changed
    prev = bdi.get("current_intention")
    if prev and prev["desire"] != chosen["desire"]:
        bdi["stats"]["intentions_changed"] += 1
        # Abandon current plan if intention changed
        if bdi.get("current_plan"):
            _record_plan_outcome(agent, "abandoned", world)
            bdi["current_plan"] = None

    bdi["current_intention"] = chosen
    # Commit for a number of ticks proportional to deliberation
    lock_ticks = int(3 + style["deliberation"] * 10)
    bdi["intention_lock"] = lock_ticks

    return chosen


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# PHASE 5 — PLAN
# Build a concrete multi-step action plan for the intention
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

def form_plan(agent, intention, percepts, world):
    """
    Given an intention, build a concrete plan:
    - Select action steps from INTENTION_ACTIONS
    - Find a concrete target (agent, building, position)
    - Set a target position for movement

    Returns the plan dict.
    """
    bdi   = agent["bdi"]
    wm    = bdi["world_model"]

    # Already have an active plan for this intention? Keep it.
    cp = bdi.get("current_plan")
    if cp and cp.get("intention") == intention["desire"]:
        return cp

    desire    = intention["desire"]
    steps     = list(INTENTION_ACTIONS.get(desire, ["move_freely"]))
    target_pos = None
    target_id  = None
    reason     = intention.get("reasoning", "")

    # ── FIND CONCRETE TARGET ─────────────────────────────────────────
    pos = agent["position"]

    def nearest_pos_from(positions):
        if not positions:
            return None
        return min(positions, key=lambda p: math.sqrt((p[0]-pos[0])**2+(p[1]-pos[1])**2))

    if desire == "survive":
        # Move away from threats
        if percepts["threats"]:
            threat_pos = percepts["threats"][0]["position"]
            # Opposite direction
            dx = pos[0] - threat_pos[0]
            dy = pos[1] - threat_pos[1]
            length = math.sqrt(dx**2 + dy**2) or 1
            target_pos = [
                max(-38, min(38, pos[0] + (dx/length) * 20)),
                max(-38, min(38, pos[1] + (dy/length) * 20)),
            ]
        else:
            # Find nearest ally for safety
            if percepts["nearby_allies"]:
                target_pos = percepts["nearby_allies"][0]["position"]

    elif desire == "fight":
        if percepts["nearby_enemies"]:
            # Target weakest enemy
            target = min(percepts["nearby_enemies"],
                         key=lambda e: e.get("health", 100))
            target_pos = target["position"]
            target_id  = target["id"]
        elif wm["threat_map"]:
            target_pos = wm["threat_map"][-1]["position"]

    elif desire == "discover":
        # Head toward unexplored edge or random far position
        target_pos = [
            random.choice([-1, 1]) * random.uniform(25, 38),
            random.choice([-1, 1]) * random.uniform(25, 38),
        ]

    elif desire == "build":
        # Find a clear area near allies
        if percepts["nearby_allies"]:
            base = percepts["nearby_allies"][0]["position"]
            target_pos = [
                base[0] + random.uniform(-8, 8),
                base[1] + random.uniform(-8, 8),
            ]
        else:
            target_pos = [pos[0] + random.uniform(-10, 10),
                          pos[1] + random.uniform(-10, 10)]

    elif desire == "heal":
        # Find most injured nearby agent
        candidates = percepts["nearby_agents"]
        if candidates:
            injured = min(candidates, key=lambda a: a.get("health", 100))
            if injured.get("health", 100) < 80:
                target_pos = injured["position"]
                target_id  = injured["id"]

    elif desire == "connect":
        # Nearest ally or friendly agent
        candidates = percepts["nearby_allies"] + [
            a for a in percepts["nearby_agents"]
            if wm["known_agents"].get(a["id"], {}).get("trust", 50) > 50
        ]
        if candidates:
            target = random.choice(candidates[:3])
            target_pos = target["position"]
            target_id  = target["id"]

    elif desire == "trade":
        # Find a merchant or market
        merchants = [a for a in percepts["nearby_agents"] if a.get("type") == "merchant"]
        markets   = [b for b in percepts["nearby_buildings"] if b["type"] in ("market", "harbor")]
        if merchants:
            target_pos = merchants[0]["position"]
        elif markets:
            target_pos = markets[0]["position"]

    elif desire == "understand":
        # Find library, academy, or scholar
        knowledge_buildings = [b for b in percepts["nearby_buildings"]
                               if b["type"] in ("library", "academy")]
        scholars = [a for a in percepts["nearby_agents"] if a.get("type") in ("scholar", "philosopher")]
        if knowledge_buildings:
            target_pos = knowledge_buildings[0]["position"]
        elif scholars:
            target_pos = scholars[0]["position"]
        else:
            # Wander — knowledge comes from experience
            target_pos = [pos[0] + random.uniform(-15, 15),
                          pos[1] + random.uniform(-15, 15)]

    elif desire == "convert":
        # Find a non-believer
        nonbelievers = [a for a in percepts["nearby_agents"] if a.get("faith", 0) < 5]
        if nonbelievers:
            target_pos = nonbelievers[0]["position"]

    elif desire == "gather_intel":
        # Shadow a target of interest
        targets = [a for a in percepts["nearby_agents"]
                   if wm["known_agents"].get(a["id"], {}).get("trust", 50) < 50]
        if targets:
            target = random.choice(targets)
            # Stay close but not too close
            d_vec = [target["position"][0] - pos[0], target["position"][1] - pos[1]]
            length = math.sqrt(d_vec[0]**2 + d_vec[1]**2) or 1
            target_pos = [
                target["position"][0] - (d_vec[0]/length) * 4,  # 4 units away
                target["position"][1] - (d_vec[1]/length) * 4,
            ]
            target_id = target["id"]

    elif desire == "hunt":
        # Find a target from memories or enemies
        from world_engine import recall
        betrayals = recall(agent, "betrayal")
        if betrayals and percepts["nearby_agents"]:
            for a in percepts["nearby_agents"]:
                if any(a["name"] in m["content"] for m in betrayals):
                    target_pos = a["position"]
                    target_id  = a["id"]
                    break
        if not target_pos and percepts["nearby_enemies"]:
            target = percepts["nearby_enemies"][0]
            target_pos = target["position"]
            target_id  = target["id"]

    elif desire == "protect":
        # Find most vulnerable ally
        if percepts["nearby_allies"]:
            vulnerable = min(percepts["nearby_allies"],
                             key=lambda a: a.get("health", 100))
            target_pos = vulnerable["position"]
            target_id  = vulnerable["id"]

    elif desire in ("provide", "grow", "control"):
        # General purpose: move toward allied territory or random
        if percepts["nearby_allies"]:
            target_pos = percepts["nearby_allies"][0]["position"]
        else:
            target_pos = [pos[0] + random.uniform(-12, 12),
                          pos[1] + random.uniform(-12, 12)]

    # Fallback: wander
    if target_pos is None:
        target_pos = [
            max(-38, min(38, pos[0] + random.uniform(-10, 10))),
            max(-38, min(38, pos[1] + random.uniform(-10, 10))),
        ]

    plan = {
        "intention":  desire,
        "steps":      steps,
        "step_index": 0,
        "target_pos": target_pos,
        "target_id":  target_id,
        "born_tick":  world["tick"],
        "reason":     reason,
        "max_ticks":  random.randint(*PLAN_PERSISTENCE),
        "outcome":    None,
    }

    bdi["current_plan"] = plan
    bdi["stats"]["plans_formed"] += 1
    return plan


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# PHASE 6 — ACT
# Execute the next step of the current plan
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

def execute_plan(agent, plan, world):
    """
    Execute the current plan step and advance the plan.
    Sets agent["target"] which the main engine will move toward.
    Returns action_taken string.
    """
    bdi = agent["bdi"]

    if plan is None:
        return "idle"

    # Check plan expiry
    age_ticks = world["tick"] - plan.get("born_tick", world["tick"])
    if age_ticks > plan.get("max_ticks", 30):
        _record_plan_outcome(agent, "failure", world)
        bdi["current_plan"] = None
        return "plan_expired"

    # Set movement target
    if plan.get("target_pos"):
        agent["target"] = plan["target_pos"]

    # Advance step index
    steps = plan.get("steps", [])
    idx   = plan.get("step_index", 0)
    current_step = steps[idx] if idx < len(steps) else steps[-1]

    # Advance to next step (cycle through)
    plan["step_index"] = (idx + 1) % max(1, len(steps))

    # Generate thought string for the action
    desire   = plan.get("intention", "survive")
    thoughts = {
        "seek_safety":          "I need to get somewhere safe.",
        "find_food":            "I must find food to survive.",
        "flee_threat":          "Run. Now.",
        "heal_self":            "I need to tend my wounds.",
        "approach_enemy":       "Closing in on the target.",
        "attack":               "Strike now — no hesitation.",
        "regroup":              "Regroup with allies first.",
        "call_allies":          "I need support here.",
        "move_to_unexplored":   "That horizon beckons.",
        "examine_landmark":     "This needs a closer look.",
        "map_area":             "Mapping what I can see.",
        "find_build_site":      "Looking for the right spot.",
        "gather_resources":     "Gathering what I need to build.",
        "construct":            "Building. One stone at a time.",
        "find_merchant":        "Who here trades?",
        "approach_trader":      "Let's see what they have.",
        "negotiate":            "Every trade starts with a number.",
        "find_sick_agent":      "Someone here needs healing.",
        "approach_sick":        "Moving to the patient.",
        "administer_care":      "Treating the wound carefully.",
        "find_nonbeliever":     "I see doubt. I can help.",
        "approach_target":      "Coming closer. Carefully.",
        "preach":               "Let me share what I know.",
        "shadow_target":        "Stay close. Stay unseen.",
        "listen_nearby":        "What are they saying?",
        "encode_intelligence":  "Filing this away.",
        "track_target":         "Following the trail.",
        "approach_stealthy":    "Quiet now.",
        "strike":               "Now.",
        "find_ally":            "Looking for someone I trust.",
        "approach_friendly":    "Hello.",
        "converse":             "There is value in this conversation.",
        "find_vulnerable":      "Who needs protecting?",
        "position_between":     "Standing between them and danger.",
        "guard":                "I am watching.",
        "find_library":         "Where is the knowledge here?",
        "observe_phenomenon":   "I need to understand this.",
        "contemplate":          "Thinking. Just thinking.",
        "assess_food_need":     "Who is hungry?",
        "farm_area":            "This land can grow things.",
        "distribute":           "Sharing what I have.",
        "identify_power_vacuum":"Where is the opening?",
        "assert_dominance":     "They need to know who leads here.",
        "recruit":              "I need people who follow.",
        "find_mentor":          "Who can teach me here?",
        "practice_skill":       "Practice until it becomes instinct.",
        "gain_experience":      "Every action teaches something.",
        "move_freely":          "Moving. Not sure where.",
    }

    thought = thoughts.get(current_step, "Acting on intention: %s." % desire)
    agent["thought"] = thought
    agent["bdi_action"] = current_step

    return current_step


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# PHASE 7 — REFLECT
# Evaluate outcome of the plan and update beliefs + self-model
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

def reflect(agent, plan, percepts, world):
    """
    Meta-cognitive reflection: did the plan achieve its intention?
    Updates:
    - belief confidence
    - self-model (perceived_strength, world_understanding etc.)
    - BDI confidence
    - memory (if significant)
    """
    bdi   = agent["bdi"]
    tick  = world["tick"]

    # Only reflect every few ticks
    if tick - bdi["last_reflection_tick"] < 5:
        return
    bdi["last_reflection_tick"] = tick

    if plan is None:
        return

    intention = plan.get("intention", "survive")
    born_tick = plan.get("born_tick", tick)
    age       = tick - born_tick
    beliefs   = agent.get("beliefs", {})
    sm        = agent.get("self_model", {})
    health    = agent.get("health", 100)
    prev_health = agent.get("_prev_health", health)

    outcome = "partial"  # default

    # ── EVALUATE SUCCESS BY INTENTION TYPE ──────────────────────────
    if intention == "survive":
        if health > prev_health or not percepts["threats"]:
            outcome = "success"
        elif health < prev_health - 10:
            outcome = "failure"

    elif intention == "fight":
        recent_battles = [m for m in agent.get("memories", [])[-5:]
                          if m["type"] == "battle"]
        if recent_battles:
            last = recent_battles[-1]["content"].lower()
            if "survived" in last or "won" in last:
                outcome = "success"
            elif "fled" in last or "lost" in last:
                outcome = "failure"

    elif intention == "discover":
        recent_discoveries = [m for m in agent.get("memories", [])[-5:]
                               if m["type"] == "discovery"]
        if recent_discoveries:
            outcome = "success"

    elif intention in ("build", "provide", "grow"):
        # Success if we've been working at it for a while
        if age > 15:
            outcome = "success"

    elif intention == "heal":
        # Success if a nearby ally's health improved
        for a in percepts["nearby_allies"]:
            aid = a["id"]
            known = bdi["world_model"]["known_agents"].get(aid, {})
            if a.get("health", 100) > known.get("health", 100):
                outcome = "success"
                break

    elif intention == "connect":
        recent_persons = [m for m in agent.get("memories", [])[-5:]
                          if m["type"] == "person"]
        if recent_persons:
            outcome = "success"

    # ── UPDATE BELIEFS BASED ON OUTCOME ──────────────────────────────
    if outcome == "success":
        bdi["stats"]["plans_succeeded"] += 1
        bdi["meta"]["confidence"] = min(1.0, bdi["meta"]["confidence"] + 0.03)

        # Reinforce belief that aligns with the intention
        belief_reinforcement = {
            "fight":       "strength_wins",
            "connect":     "cooperation_works",
            "understand":  "knowledge_is_power",
            "convert":     "the_divine_exists",
            "survive":     "world_is_safe",
        }
        if intention in belief_reinforcement:
            bkey = belief_reinforcement[intention]
            if bkey in beliefs:
                beliefs[bkey]["confidence"] = min(100, beliefs[bkey]["confidence"] + 5)

        # Self-model: success increases self-worth and role confidence
        if sm:
            sm["self_worth"]      = min(100, sm.get("self_worth", 50) + 2)
            sm["role_confidence"] = min(100, sm.get("role_confidence", 60) + 3)

    elif outcome == "failure":
        bdi["stats"]["plans_failed"] += 1
        bdi["meta"]["confidence"] = max(0.1, bdi["meta"]["confidence"] - 0.05)

        # Shake belief that promised success
        belief_erosion = {
            "fight":      "strength_wins",
            "connect":    "cooperation_works",
            "survive":    "world_is_safe",
        }
        if intention in belief_erosion:
            bkey = belief_erosion[intention]
            if bkey in beliefs:
                beliefs[bkey]["confidence"] = max(0, beliefs[bkey]["confidence"] - 8)

        # Self-model: failure reduces self-worth, world_understanding increases
        if sm:
            sm["self_worth"]        = max(0, sm.get("self_worth", 50) - 3)
            sm["world_understanding"] = min(100, sm.get("world_understanding", 30) + 2)

    # ── STORE REFLECTION ──────────────────────────────────────────────
    reflection = {
        "tick":      tick,
        "intention": intention,
        "outcome":   outcome,
        "age_ticks": age,
        "confidence_after": round(bdi["meta"]["confidence"], 2),
    }
    bdi["reflections"].append(reflection)
    if len(bdi["reflections"]) > 20:
        bdi["reflections"] = bdi["reflections"][-20:]

    bdi["stats"]["reflections_done"] += 1

    # ── SIGNIFICANT REFLECTIONS → MEMORY ─────────────────────────────
    if outcome == "failure" and age > 20:
        from world_engine import remember
        lesson = _derive_lesson(agent, intention, outcome)
        remember(agent, "discovery",
                 "Reflection: My plan to '%s' failed. %s Y%d" % (intention, lesson, world["year"]),
                 importance=3)

    # Save health for next comparison
    agent["_prev_health"] = health


def _derive_lesson(agent, intention, outcome):
    """Generate a meaningful lesson from a failed plan."""
    lessons = {
        "fight":       "I overestimated my strength, or underestimated theirs.",
        "survive":     "I should have moved faster.",
        "discover":    "Not every horizon holds what I hoped.",
        "build":       "The site was wrong, or the time was wrong.",
        "connect":     "Not everyone wants to be found.",
        "heal":        "Some wounds cannot be closed.",
        "convert":     "Faith cannot be forced.",
        "gather_intel":"Shadows have their own secrets.",
        "hunt":        "Patience is not weakness.",
        "understand":  "Understanding takes longer than I thought.",
        "trade":       "Trust is the real currency.",
        "protect":     "I cannot be everywhere at once.",
    }
    return lessons.get(intention, "The world does not always cooperate with plans.")


def _record_plan_outcome(agent, outcome, world):
    """Record a plan's outcome in history."""
    bdi  = agent["bdi"]
    plan = bdi.get("current_plan")
    if not plan:
        return
    record = {
        "intention": plan.get("intention"),
        "outcome":   outcome,
        "age_ticks": world["tick"] - plan.get("born_tick", world["tick"]),
        "tick":      world["tick"],
    }
    bdi["plan_history"].append(record)
    if len(bdi["plan_history"]) > 10:
        bdi["plan_history"] = bdi["plan_history"][-10:]

    if outcome == "success":
        bdi["stats"]["plans_succeeded"] += 1
    elif outcome == "failure":
        bdi["stats"]["plans_failed"] += 1


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# MASTER COGNITIVE CYCLE
# Run the full BDI loop for one agent in one tick
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

def cognitive_cycle(agent, world):
    """
    The complete BDI cognitive loop for one agent.
    Call this instead of (or after) the engine's agent_think().

    Phases:
      1. Perceive     — sense the environment
      2. Believe      — update world model
      3. Desire       — generate desire stack
      4. Intend       — select intention
      5. Plan         — form action plan
      6. Act          — execute plan step (sets agent["target"])
      7. Reflect      — evaluate and learn

    Returns a summary dict for logging/research.
    """
    # Ensure BDI is initialised
    if "bdi" not in agent:
        init_bdi(agent)

    bdi = agent["bdi"]
    bdi["stats"]["total_cycles"] += 1

    # ── PHASE 1: PERCEIVE ────────────────────────────────────────────
    percepts = perceive(agent, world)

    # ── PHASE 2: BELIEVE ─────────────────────────────────────────────
    update_world_model(agent, percepts, world)

    # ── PHASE 3: DESIRE ──────────────────────────────────────────────
    desires = generate_desires(agent, percepts, world)

    # ── PHASE 4: INTEND ──────────────────────────────────────────────
    intention = select_intention(agent, desires, world)
    if intention is None:
        return {"phase": "intend", "result": "no_desires"}

    # ── PHASE 5: PLAN ────────────────────────────────────────────────
    plan = form_plan(agent, intention, percepts, world)

    # ── PHASE 6: ACT ─────────────────────────────────────────────────
    action = execute_plan(agent, plan, world)

    # ── PHASE 7: REFLECT ─────────────────────────────────────────────
    reflect(agent, plan, percepts, world)

    # ── UPDATE COGNITIVE LOAD ─────────────────────────────────────────
    # Cognitive load = how many competing desires we're managing
    n_desires = len(desires)
    n_threats = len(percepts["threats"])
    bdi["meta"]["cognitive_load"] = min(1.0, (n_desires * 0.05) + (n_threats * 0.15))

    # ── CYCLE QUALITY ─────────────────────────────────────────────────
    # Self-assessed quality: did we have a clear plan for a clear intention?
    quality = 0.5
    if plan and intention:
        quality += 0.3
    if desires:
        quality += 0.2 * min(1.0, desires[0]["urgency"] / 10)
    bdi["meta"]["last_cycle_quality"] = round(quality, 2)

    return {
        "phase":     "complete",
        "intention": intention["desire"],
        "action":    action,
        "n_desires": n_desires,
        "n_threats": n_threats,
        "quality":   quality,
    }


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# TICK FUNCTION — call this from world_engine.py's tick()
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

def tick_cognitive_loops(world):
    """
    Run the BDI cognitive cycle for all living agents.
    Designed to be called from world_engine.tick() alongside existing systems.

    Add this line to tick() in world_engine.py:
        from cognitive_loop import tick_cognitive_loops
        tick_cognitive_loops(world)
    """
    alive = [a for a in world["agents"] if a["alive"]]
    cycles_run = 0
    for agent in alive:
        try:
            result = cognitive_cycle(agent, world)
            cycles_run += 1
        except Exception as e:
            # Never crash the world engine due to a cognitive error
            pass

    world["stats"]["bdi_cycles"] = world["stats"].get("bdi_cycles", 0) + cycles_run
    return cycles_run


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# INTEGRATION HELPERS — useful utilities for world_engine.py
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

def get_agent_intention(agent):
    """Get the current intention label for display/logging."""
    bdi = agent.get("bdi", {})
    intention = bdi.get("current_intention")
    if intention:
        return intention["desire"]
    return "idle"


def get_agent_thought(agent):
    """Get the current thought string for display."""
    return agent.get("thought", "...")


def get_bdi_summary(agent):
    """Return a readable summary of the agent's BDI state."""
    bdi = agent.get("bdi", {})
    if not bdi:
        return "BDI not initialised."

    desires  = bdi.get("desires", [])
    top3     = [d["desire"] for d in desires[:3]]
    intention = bdi.get("current_intention", {})
    plan      = bdi.get("current_plan", {})
    meta      = bdi.get("meta", {})
    stats     = bdi.get("stats", {})

    return {
        "name":       agent["name"],
        "type":       agent["type"],
        "faction":    agent.get("faction", "?"),
        "age":        agent.get("age", 0),
        "emotion":    agent.get("emotion", "content"),
        "health":     agent.get("health", 100),
        "thought":    agent.get("thought", "..."),
        "intention":  intention.get("desire", "none") if intention else "none",
        "top_desires":top3,
        "plan":       plan.get("intention", "none") if plan else "none",
        "plan_step":  plan.get("step_index", 0) if plan else 0,
        "confidence": round(meta.get("confidence", 0.5), 2),
        "cog_load":   round(meta.get("cognitive_load", 0.0), 2),
        "cycles":     stats.get("total_cycles", 0),
        "plans_ok":   stats.get("plans_succeeded", 0),
        "plans_fail": stats.get("plans_failed", 0),
        "known_agents": len(bdi.get("world_model", {}).get("known_agents", {})),
        "known_buildings": len(bdi.get("world_model", {}).get("known_buildings", {})),
    }


def get_world_bdi_snapshot(world):
    """Get a snapshot of all agents' BDI states for the dashboard."""
    alive = [a for a in world["agents"] if a["alive"]]
    return {
        "tick":    world["tick"],
        "year":    world["year"],
        "agents":  [get_bdi_summary(a) for a in alive if "bdi" in a],
        "stats": {
            "total_bdi_cycles":   world["stats"].get("bdi_cycles", 0),
            "avg_confidence":     round(
                sum(a["bdi"]["meta"]["confidence"]
                    for a in alive if "bdi" in a) / max(1, len(alive)), 2
            ),
            "top_intentions":     _count_intentions(alive),
            "total_plans_formed": sum(
                a["bdi"]["stats"]["plans_formed"]
                for a in alive if "bdi" in a
            ),
        },
    }


def _count_intentions(alive):
    """Count the frequency of current intentions across all agents."""
    counts = {}
    for a in alive:
        bdi = a.get("bdi", {})
        intention = bdi.get("current_intention")
        if intention:
            key = intention["desire"]
            counts[key] = counts.get(key, 0) + 1
    return sorted(counts.items(), key=lambda x: -x[1])


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# WORLD ENGINE INTEGRATION PATCH
# How to add this to world_engine.py (3 small changes):
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
"""
PATCH INSTRUCTIONS FOR world_engine.py
=======================================

1. At the top of world_engine.py, add:
   ─────────────────────────────────────────
   from cognitive_loop import tick_cognitive_loops, init_bdi, get_bdi_summary

2. In spawn_agent() function, after agent dict is created, add:
   ─────────────────────────────────────────
   init_bdi(agent)

3. In tick() function, add after tick_all_upgrades():
   ─────────────────────────────────────────
   tick_cognitive_loops(world)

That's it. The cognitive loop runs ALONGSIDE existing engine systems.
It does not replace agent_think() — it enhances it by:
  • Setting agent["target"] via the plan
  • Setting agent["thought"] via the action
  • Updating beliefs, world model, self-model
  • Adding memories for significant cognitive events

To view a live BDI snapshot, call:
   from cognitive_loop import get_world_bdi_snapshot
   snapshot = get_world_bdi_snapshot(world)
"""
