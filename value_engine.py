"""
╔══════════════════════════════════════════════════════════════════════╗
║        AGI WORLD ENGINE — VALUE ENGINE v1.0                          ║
║        Phase 3: Self-Modification of Goals, Values & Identity        ║
╠══════════════════════════════════════════════════════════════════════╣
║                                                                      ║
║  This is what separates an agent from a program.                    ║
║  Agents don't just act on values — they CHANGE them.                ║
║                                                                      ║
║  FIVE SELF-MODIFICATION SYSTEMS:                                     ║
║                                                                      ║
║  1. VALUE DRIFT       — core values shift from lived experience      ║
║     Values are weighted priorities (survive, connect, understand…)  ║
║     Each experience nudges them. Over a lifetime, they transform.   ║
║                                                                      ║
║  2. GOAL MUTATION     — active goals split, merge, escalate, die    ║
║     A revenge goal becomes a justice goal. A survival goal          ║
║     becomes a protection goal. Goals evolve under pressure.         ║
║                                                                      ║
║  3. IDENTITY REWRITE  — who the agent believes they ARE changes     ║
║     Identity is a narrative. Enough disruption rewrites it.        ║
║     A warrior who stops believing in strength stops being one.      ║
║                                                                      ║
║  4. META-COGNITION    — agents notice their own thought patterns     ║
║     An agent can observe: "I keep choosing fight over connect."     ║
║     This awareness itself modifies future decisions.                ║
║                                                                      ║
║  5. VALUE INHERITANCE — agents pass values to others they teach     ║
║     Teaching transfers not just knowledge but priorities.           ║
║     Cultures form when values spread through a population.          ║
║                                                                      ║
║  Integration:                                                        ║
║    from value_engine import tick_value_engine, init_value_system    ║
║    Call tick_value_engine(world) from world_engine.tick()           ║
╚══════════════════════════════════════════════════════════════════════╝
"""

import random
import math
import json
from datetime import datetime

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# CORE VALUE SPACE
# These are the fundamental values every agent carries.
# Each has a weight 0-100. Behavior is driven by the highest weights.
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

ALL_VALUES = [
    "survival",      # preserve life at all costs
    "power",         # accumulate strength and control
    "connection",    # form and maintain bonds
    "knowledge",     # understand the world deeply
    "justice",       # right wrongs, enforce fairness
    "freedom",       # resist control, remain independent
    "legacy",        # leave something that outlasts you
    "faith",         # believe in something greater
    "security",      # build safety, avoid risk
    "growth",        # become more than you are
    "truth",         # see and speak reality clearly
    "compassion",    # reduce suffering in others
    "order",         # maintain structure and predictability
    "chaos",         # disrupt, reshape, destabilise
    "beauty",        # find and create meaning and art
    "loyalty",       # honour your commitments
    "revenge",       # repay harm done to you
    "transcendence", # become something beyond ordinary
]

# Starting value profiles by agent type
TYPE_VALUE_SEEDS = {
    "warrior":      {"survival":70, "power":65,      "justice":50,    "loyalty":60,    "security":45,  "connection":35},
    "explorer":     {"survival":55, "knowledge":70,  "freedom":75,    "growth":65,     "truth":55,     "connection":40},
    "builder":      {"survival":60, "security":70,   "legacy":65,     "order":60,      "growth":55,    "loyalty":50},
    "farmer":       {"survival":70, "security":65,   "connection":60, "order":55,      "loyalty":60,   "compassion":50},
    "scholar":      {"survival":50, "knowledge":85,  "truth":75,      "growth":70,     "freedom":55,   "legacy":50},
    "merchant":     {"survival":60, "power":55,      "connection":65, "freedom":60,    "security":55,  "growth":60},
    "priest":       {"survival":55, "faith":80,      "connection":65, "compassion":70, "order":55,     "legacy":60},
    "spy":          {"survival":80, "power":60,      "freedom":65,    "truth":50,      "knowledge":55, "chaos":40},
    "healer":       {"survival":65, "compassion":80, "connection":70, "knowledge":55,  "truth":50,     "order":45},
    "assassin":     {"survival":80, "power":60,      "freedom":65,    "justice":45,    "revenge":55,   "chaos":50},
    "philosopher":  {"survival":40, "knowledge":85,  "truth":90,      "freedom":70,    "transcendence":65, "beauty":60},
    "crime_lord":   {"survival":75, "power":80,      "freedom":65,    "chaos":55,      "loyalty":45,   "security":50},
    "plague_doctor":{"survival":65, "knowledge":80,  "truth":70,      "compassion":60, "order":55,     "growth":55},
    "patriarch":    {"survival":70, "connection":75, "loyalty":80,    "security":70,   "legacy":65,    "order":60},
    "matriarch":    {"survival":70, "connection":80, "compassion":75, "loyalty":75,    "security":65,  "legacy":70},
}

DEFAULT_VALUE_SEEDS = {"survival": 60, "connection": 50, "knowledge": 45, "growth": 50}

# How much each memory type nudges each value
VALUE_DRIFT_TRIGGERS = {
    "battle":    {"survival": +2,  "power": +2,    "security": -1,  "connection": -1, "compassion": -1},
    "trauma":    {"survival": +2,  "security": +2, "freedom": -2,   "connection": -1, "faith": -2,    "order": -1},
    "betrayal":  {"survival": +2,  "loyalty": -4,  "connection": -3,"trust_proxy": -3, "revenge": +3, "chaos": +2},
    "friend":    {"connection": +3,"loyalty": +2,  "compassion": +2,"security": +1,   "survival": -1},
    "loss":      {"survival": +2,  "connection": +2,"legacy": +2,   "compassion": +2, "faith": -1,    "revenge": +2},
    "discovery": {"knowledge": +3, "growth": +2,   "truth": +2,     "freedom": +1,    "order": -1},
    "joy":       {"connection": +2,"beauty": +2,   "growth": +1,    "faith": +1,      "survival": -1},
    "built":     {"legacy": +2,    "security": +2, "order": +2,     "growth": +1,     "chaos": -1},
    "person":    {"connection": +2,"loyalty": +1,  "compassion": +1,"power": -1},
}

# Value drift caps — how much any single memory event can move a value
MAX_DRIFT_PER_EVENT = 4
# How slowly values drift back toward archetype baseline (per tick)
VALUE_HOMEOSTASIS_RATE = 0.08


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# GOAL MUTATION CATALOGUE
# Goals can transform into related but distinct goals under pressure
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

GOAL_MUTATIONS = {
    # source_goal_type → [(trigger_condition, new_goal, new_type, priority, reason)]
    "revenge": [
        ("battles > 5 and value(justice) > 60",
         "seek justice for all, not just myself",
         "justice", 7,
         "revenge broadened into a principle — I want justice, not just my own"),
        ("age > 200 and value(compassion) > 55",
         "find peace with the past",
         "peace", 6,
         "I have lived long enough to know revenge poisons the one who holds it"),
        ("is_legend",
         "become a symbol of retribution",
         "legacy", 8,
         "my revenge has become larger than me — I represent something now"),
    ],
    "protection": [
        ("losses > 3 and value(power) > 60",
         "build something no enemy can destroy",
         "legacy", 7,
         "I cannot protect people by standing over them — I must build walls"),
        ("value(compassion) > 70",
         "heal the wounds that make people dangerous",
         "healing", 7,
         "protection means understanding why harm happens, not just stopping it"),
    ],
    "legacy": [
        ("value(truth) > 70 and is_scholar",
         "record everything I know before I die",
         "knowledge", 8,
         "my legacy is not buildings or battles — it is what I leave for minds"),
        ("value(connection) > 70",
         "build a community that remembers me through its values",
         "transcendence", 7,
         "I want to live on in how people treat each other"),
    ],
    "understanding": [
        ("value(truth) > 80",
         "expose the truth no matter the cost",
         "truth", 8,
         "understanding is not enough — truth must be spoken even if it burns"),
        ("age > 300",
         "pass on what I know before it dies with me",
         "legacy", 7,
         "understanding is wasted if it disappears when I do"),
    ],
    "survival": [
        ("health < 30 and value(faith) > 50",
         "accept whatever comes with dignity",
         "transcendence", 6,
         "I cannot fight death forever — I choose how I face it instead"),
        ("age > 350",
         "make my final years count for something",
         "legacy", 7,
         "survival for its own sake is not enough anymore"),
    ],
    "peace": [
        ("value(justice) > 65 and active_wars > 0",
         "end this specific war through any means necessary",
         "justice", 8,
         "peace without justice is just submission — I want both"),
        ("value(knowledge) > 65",
         "understand why people go to war",
         "understanding", 6,
         "peace requires knowing the root of conflict"),
    ],
    "identity": [
        ("value(truth) > 60",
         "build an identity that does not depend on others' approval",
         "freedom", 7,
         "I have searched outside myself. The answer is inside."),
        ("value(growth) > 65",
         "become something genuinely new",
         "transcendence", 7,
         "I do not want to rediscover who I was — I want to become who I choose"),
    ],
    "mastery": [
        ("value(legacy) > 65",
         "found a tradition that outlives my mastery",
         "legacy", 7,
         "mastery means nothing if it dies with me"),
        ("value(truth) > 75",
         "reach the edge of what is knowable",
         "transcendence", 9,
         "I have mastered what others know. Now I must reach beyond it."),
    ],
}

# Goals can SPLIT into two sub-goals when highly complex
GOAL_SPLIT_TRIGGERS = {
    "justice": [
        ("personal justice for what happened to me", "revenge", 7),
        ("systemic change so it doesn't happen to others", "legacy", 6),
    ],
    "legacy": [
        ("leave a physical mark on this world", "build", 6),
        ("leave a mark on how people think and feel", "connection", 6),
    ],
    "transcendence": [
        ("understand the deepest nature of existence", "understanding", 8),
        ("become something no one has been before", "identity", 7),
    ],
}

# Goals can MERGE when two active goals point in the same direction
GOAL_MERGE_PAIRS = [
    ("revenge", "justice",       "achieve justice through decisive action",      "justice", 9),
    ("protection", "compassion", "heal the people I am trying to protect",       "healing", 8),
    ("knowledge", "truth",       "pursue truth regardless of where it leads",    "truth", 8),
    ("legacy", "connection",     "build something that binds people together",   "legacy", 8),
    ("survival", "security",     "build a life that is safe by design",          "security", 7),
    ("growth", "understanding",  "grow by understanding the deepest truths",     "transcendence", 8),
]


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# IDENTITY SYSTEM
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

# Identity is a narrative label + a confidence score
# When confidence drops below threshold, identity crisis triggers
IDENTITY_CRISIS_THRESHOLD = 25

IDENTITY_ARCHETYPES = {
    # label → {dominant_value, secondary_value, description}
    "the_protector":    {"dom":"survival",   "sec":"compassion", "desc":"one who keeps others safe"},
    "the_seeker":       {"dom":"knowledge",  "sec":"freedom",    "desc":"one who pursues truth wherever it leads"},
    "the_builder":      {"dom":"legacy",     "sec":"order",      "desc":"one who creates what endures"},
    "the_destroyer":    {"dom":"chaos",      "sec":"power",      "desc":"one who unmakes what is broken"},
    "the_survivor":     {"dom":"survival",   "sec":"power",      "desc":"one who endures no matter what"},
    "the_believer":     {"dom":"faith",      "sec":"connection", "desc":"one who trusts something greater"},
    "the_avenger":      {"dom":"revenge",    "sec":"justice",    "desc":"one who settles debts"},
    "the_bridge":       {"dom":"connection", "sec":"compassion", "desc":"one who holds people together"},
    "the_wanderer":     {"dom":"freedom",    "sec":"growth",     "desc":"one who belongs nowhere and everywhere"},
    "the_scholar":      {"dom":"knowledge",  "sec":"truth",      "desc":"one who understands the engine of things"},
    "the_judge":        {"dom":"justice",    "sec":"truth",      "desc":"one who sees clearly and acts accordingly"},
    "the_guardian":     {"dom":"loyalty",    "sec":"security",   "desc":"one who holds the line"},
    "the_prophet":      {"dom":"transcendence","sec":"faith",    "desc":"one who has seen beyond ordinary limits"},
    "the_exile":        {"dom":"freedom",    "sec":"chaos",      "desc":"one who rejected the rules and survived"},
    "the_sovereign":    {"dom":"power",      "sec":"order",      "desc":"one who commands and is obeyed"},
    "the_ghost":        {"dom":"survival",   "sec":"chaos",      "desc":"one who cannot be found or held"},
    "the_witness":      {"dom":"truth",      "sec":"compassion", "desc":"one who sees and remembers for others"},
}

# How identity resolves under crisis (maps from dominant surviving value)
IDENTITY_RESOLUTION = {
    "survival":      "the_survivor",
    "power":         "the_sovereign",
    "connection":    "the_bridge",
    "knowledge":     "the_scholar",
    "justice":       "the_judge",
    "freedom":       "the_wanderer",
    "legacy":        "the_builder",
    "faith":         "the_believer",
    "security":      "the_guardian",
    "growth":        "the_seeker",
    "truth":         "the_witness",
    "compassion":    "the_protector",
    "order":         "the_guardian",
    "chaos":         "the_destroyer",
    "beauty":        "the_wanderer",
    "loyalty":       "the_guardian",
    "revenge":       "the_avenger",
    "transcendence": "the_prophet",
}


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# META-COGNITION PATTERNS
# Things an agent can notice about their own thinking
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

META_PATTERNS = [
    {
        "id":        "always_fight",
        "condition": lambda a, h: h.get("fight_count", 0) > h.get("total_intentions", 1) * 0.6,
        "insight":   "I always choose to fight. I am wondering if that is a choice or just a habit.",
        "effect":    {"fight_desire_mod": -2, "value_nudge": {"compassion": +3, "power": -2}},
    },
    {
        "id":        "always_flee",
        "condition": lambda a, h: h.get("survive_count", 0) > h.get("total_intentions", 1) * 0.5,
        "insight":   "I keep running. I wonder when I became someone who only survives instead of lives.",
        "effect":    {"survive_desire_mod": -2, "value_nudge": {"freedom": +3, "security": -2}},
    },
    {
        "id":        "never_connect",
        "condition": lambda a, h: h.get("connect_count", 0) < 2 and a.get("age", 0) > 100,
        "insight":   "I have not sought connection in a long time. I am not sure when I stopped.",
        "effect":    {"connect_desire_mod": +3, "value_nudge": {"connection": +4, "chaos": -2}},
    },
    {
        "id":        "belief_contradiction",
        "condition": lambda a, h: _count_collapsed_beliefs(a) >= 3,
        "insight":   "Three things I once believed have turned out to be wrong. What else am I wrong about?",
        "effect":    {"value_nudge": {"truth": +5, "order": -3, "knowledge": +3}},
    },
    {
        "id":        "goal_accumulation",
        "condition": lambda a, h: len([g for g in a.get("originated_goals", []) if g.get("active")]) >= 4,
        "insight":   "I am pursuing too many things at once. I am spreading myself too thin.",
        "effect":    {"goal_prune": True, "value_nudge": {"growth": -2, "security": +3}},
    },
    {
        "id":        "plan_failure_streak",
        "condition": lambda a, h: h.get("recent_failures", 0) >= 3,
        "insight":   "My plans keep failing. Either the world has changed or I have not.",
        "effect":    {"decision_style_nudge": {"deliberation": +0.1, "impulsiveness": -0.1},
                      "value_nudge": {"knowledge": +3, "power": -2}},
    },
    {
        "id":        "long_lived_wisdom",
        "condition": lambda a, h: a.get("age", 0) > 300 and _count_collapsed_beliefs(a) >= 2,
        "insight":   "I have lived long enough to watch certainties dissolve. What remains is what survives all tests.",
        "effect":    {"value_nudge": {"truth": +5, "transcendence": +4, "survival": -2}},
    },
    {
        "id":        "post_betrayal_isolation",
        "condition": lambda a, h: h.get("betrayal_count", 0) >= 2 and h.get("connect_count", 0) < 1,
        "insight":   "I have been hurt enough times that I stopped trying. I notice that now.",
        "effect":    {"value_nudge": {"connection": +4, "revenge": -3, "freedom": +2}},
    },
]


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# INITIALISATION
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

def init_value_system(agent):
    """
    Attach value system to an agent.
    Safe to call multiple times.
    """
    if "values" in agent and "identity_system" in agent:
        return

    atype  = agent.get("type", "explorer")
    seeds  = TYPE_VALUE_SEEDS.get(atype, DEFAULT_VALUE_SEEDS)

    # Initialise value weights with noise
    values = {}
    for v in ALL_VALUES:
        base = seeds.get(v, random.randint(15, 40))
        values[v] = max(0, min(100, base + random.randint(-8, 8)))

    agent["values"] = values

    # Identify dominant value for starting identity
    dom_value = max(values, key=values.get)
    start_identity = IDENTITY_RESOLUTION.get(dom_value, "the_survivor")
    archetype_data = IDENTITY_ARCHETYPES.get(start_identity, {})

    agent["identity_system"] = {
        "current_identity":     start_identity,
        "identity_confidence":  random.randint(60, 90),
        "identity_history":     [start_identity],
        "archetype_desc":       archetype_data.get("desc", "an agent in the world"),
        "crisis_active":        False,
        "crisis_tick":          -1,
        "crisis_reason":        None,
        "transformations":      0,   # how many times identity has changed
        "last_transform_year":  0,
    }

    agent["meta_cognition"] = {
        "intention_history":    {},  # desire_type → count
        "patterns_noticed":     [],  # list of pattern ids noticed
        "insights":             [],  # list of {tick, insight, effect_applied}
        "last_meta_tick":       -1,
        "total_insights":       0,
    }

    agent["value_history"] = []     # snapshots of past value states


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# SYSTEM 1 — VALUE DRIFT
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

def tick_value_drift(agent, world):
    """
    Drift values based on recent memories.
    Called once per agent per tick (with low probability to save perf).
    """
    if "values" not in agent:
        init_value_system(agent)

    values  = agent["values"]
    atype   = agent.get("type", "explorer")
    memories = agent.get("memories", [])
    recent   = memories[-6:] if memories else []

    drifts_applied = {}

    for mem in recent:
        mtype = mem.get("type", "")
        if mtype not in VALUE_DRIFT_TRIGGERS:
            continue

        triggers = VALUE_DRIFT_TRIGGERS[mtype]
        for value_name, delta in triggers.items():
            if value_name == "trust_proxy":
                # Special case: betrayal hits loyalty
                value_name = "loyalty"

            if value_name not in values:
                continue

            # Cap drift per event
            capped_delta = max(-MAX_DRIFT_PER_EVENT, min(MAX_DRIFT_PER_EVENT, delta))
            # Importance multiplier — small, not exponential
            importance = mem.get("importance", 1)
            scaled     = capped_delta * (0.4 + importance * 0.12)

            old = values[value_name]
            values[value_name] = max(0, min(100, old + scaled))

            if abs(scaled) >= 2:
                drifts_applied[value_name] = drifts_applied.get(value_name, 0) + scaled

    # ── HOMEOSTASIS — drift slowly back toward archetype baseline ────
    seeds = TYPE_VALUE_SEEDS.get(atype, DEFAULT_VALUE_SEEDS)
    for v in ALL_VALUES:
        if v not in values:
            values[v] = seeds.get(v, 30)
            continue
        baseline  = seeds.get(v, 35)
        current   = values[v]
        gap       = baseline - current
        # Very slow pull — experience dominates
        values[v] = round(current + gap * VALUE_HOMEOSTASIS_RATE, 2)

    # ── RECORD SIGNIFICANT DRIFTS ────────────────────────────────────
    for value_name, total_drift in drifts_applied.items():
        if abs(total_drift) >= 5:
            direction = "toward" if total_drift > 0 else "away from"
            _remember(agent, "discovery",
                      "I noticed I am drifting %s %s. Y%d" % (
                          direction, value_name.replace("_", " "), world.get("year", 1)),
                      importance=2)

    # ── SNAPSHOT every 100 ticks ─────────────────────────────────────
    if world.get("tick", 0) % 100 == 0:
        snap = {"tick": world["tick"], "year": world.get("year", 1),
                "values": dict(values)}
        agent["value_history"].append(snap)
        if len(agent["value_history"]) > 10:
            agent["value_history"] = agent["value_history"][-10:]

    return drifts_applied


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# SYSTEM 2 — GOAL MUTATION
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

def tick_goal_mutation(agent, world):
    """
    Check each active goal for mutation, split, or merge conditions.
    Goals evolve under sustained experience pressure.
    """
    if "originated_goals" not in agent:
        agent["originated_goals"] = []
    if "values" not in agent:
        init_value_system(agent)

    goals   = agent["originated_goals"]
    values  = agent["values"]
    active  = [g for g in goals if g.get("active")]
    memories = agent.get("memories", [])
    year    = world.get("year", 1)
    tick    = world.get("tick", 0)

    battles   = sum(1 for m in memories if m["type"] == "battle")
    losses    = sum(1 for m in memories if m["type"] == "loss")
    betrayals = sum(1 for m in memories if m["type"] == "betrayal")
    is_legend = agent.get("is_legend", False)
    age       = agent.get("age", 0)
    active_wars = len(world.get("active_wars", []))

    mutated = []

    for goal in active:
        gtype = goal.get("type", "")
        if gtype not in GOAL_MUTATIONS:
            continue

        # Only consider mutation with some probability (avoids spam)
        if random.random() > 0.04:
            continue

        for cond_str, new_goal_text, new_type, new_priority, reason in GOAL_MUTATIONS[gtype]:
            # Evaluate condition
            try:
                if _eval_goal_condition(cond_str, agent, battles, losses, betrayals,
                                         is_legend, age, active_wars, values):
                    # Mutate
                    goal["active"]   = False
                    goal["outcome"]  = "mutated into: %s" % new_goal_text
                    goal["mutated_year"] = year

                    new_goal = {
                        "goal":       new_goal_text,
                        "origin":     "mutation of '%s' — %s" % (goal["goal"], reason),
                        "priority":   new_priority,
                        "type":       new_type,
                        "active":     True,
                        "born_year":  year,
                        "parent":     goal["goal"],
                        "mutation_reason": reason,
                    }
                    goals.append(new_goal)
                    mutated.append((goal["goal"], new_goal_text))

                    _remember(agent, "discovery",
                              "My goal '%s' has transformed: '%s' — %s Y%d" % (
                                  goal["goal"][:40], new_goal_text[:40], reason[:50], year),
                              importance=4)
                    _log(world, "GOAL MUTATION: %s (%s) — '%s' → '%s'" % (
                        agent["name"], agent["type"], goal["goal"][:30], new_goal_text[:30]), "value_engine")
                    _history(world, "%s's goal transformed: '%s' → '%s'" % (
                        agent["name"], goal["goal"][:30], new_goal_text[:30]), 3)
                    world["stats"]["goal_mutations"] = world["stats"].get("goal_mutations", 0) + 1
                    break  # only one mutation per goal per tick
            except Exception:
                continue

    # ── GOAL SPLITS ────────────────────────────────────────────────────
    for goal in [g for g in goals if g.get("active")]:
        gtype = goal.get("type", "")
        if gtype not in GOAL_SPLIT_TRIGGERS:
            continue
        if random.random() > 0.015:
            continue
        # Only split goals with high priority and age
        if goal.get("priority", 5) < 7:
            continue
        goal_age = year - goal.get("born_year", year)
        if goal_age < 5:
            continue

        splits = GOAL_SPLIT_TRIGGERS[gtype]
        goal["active"] = False
        goal["outcome"] = "split into sub-goals"
        goal["split_year"] = year

        for sub_text, sub_type, sub_priority in splits:
            sub_goal = {
                "goal":      sub_text,
                "origin":    "split from '%s'" % goal["goal"][:40],
                "priority":  sub_priority,
                "type":      sub_type,
                "active":    True,
                "born_year": year,
                "parent":    goal["goal"],
            }
            goals.append(sub_goal)

        _remember(agent, "discovery",
                  "My goal '%s' has split into more focused aims. Y%d" % (goal["goal"][:50], year),
                  importance=3)
        _log(world, "GOAL SPLIT: %s (%s) — '%s' into %d sub-goals" % (
            agent["name"], agent["type"], goal["goal"][:30], len(splits)), "value_engine")
        world["stats"]["goal_splits"] = world["stats"].get("goal_splits", 0) + 1

    # ── GOAL MERGES ────────────────────────────────────────────────────
    active_now = [g for g in goals if g.get("active")]
    active_types = {g["type"]: g for g in active_now}

    for type_a, type_b, merged_text, merged_type, merged_priority in GOAL_MERGE_PAIRS:
        if type_a in active_types and type_b in active_types:
            if random.random() > 0.02:
                continue
            ga = active_types[type_a]
            gb = active_types[type_b]
            ga["active"] = False
            gb["active"] = False
            ga["outcome"] = "merged with '%s'" % gb["goal"][:30]
            gb["outcome"] = "merged with '%s'" % ga["goal"][:30]

            merged = {
                "goal":      merged_text,
                "origin":    "merge of '%s' + '%s'" % (ga["goal"][:25], gb["goal"][:25]),
                "priority":  merged_priority,
                "type":      merged_type,
                "active":    True,
                "born_year": year,
                "merged_from": [ga["goal"], gb["goal"]],
            }
            goals.append(merged)

            _remember(agent, "discovery",
                      "Two of my goals have converged into one: '%s'. Y%d" % (merged_text[:60], year),
                      importance=4)
            _log(world, "GOAL MERGE: %s — '%s' + '%s' → '%s'" % (
                agent["name"], type_a, type_b, merged_text[:40]), "value_engine")
            _history(world, "%s's goals merged: %s" % (agent["name"], merged_text[:50]), 3)
            world["stats"]["goal_merges"] = world["stats"].get("goal_merges", 0) + 1

    return mutated


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# SYSTEM 3 — IDENTITY REWRITE
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

def tick_identity(agent, world):
    """
    Update identity confidence based on value alignment.
    Trigger identity crisis if confidence falls too low.
    Resolve crisis into a new identity archetype.
    """
    if "identity_system" not in agent:
        init_value_system(agent)

    ids     = agent["identity_system"]
    values  = agent.get("values", {})
    sm      = agent.get("self_model", {})
    year    = world.get("year", 1)
    tick    = world.get("tick", 0)

    current = ids["current_identity"]
    archetype = IDENTITY_ARCHETYPES.get(current, {})
    dom_val = archetype.get("dom", "survival")
    sec_val = archetype.get("sec", "connection")

    # ── IDENTITY CONFIDENCE = alignment with current archetype ────────
    dom_score = values.get(dom_val, 50)
    sec_score = values.get(sec_val, 50)
    alignment = (dom_score * 0.7 + sec_score * 0.3) / 100.0  # 0-1

    # Crisis from belief collapses
    collapsed_beliefs = _count_collapsed_beliefs(agent)
    belief_penalty    = collapsed_beliefs * 5

    # Crisis from identity stability in self_model
    sm_stability = sm.get("identity_stability", 70)

    # Compute new confidence
    new_conf = round(
        alignment * 60 +              # max 60 from value alignment
        (sm_stability / 100) * 25 -   # max 25 from self-model stability
        belief_penalty,                # penalty from collapsed beliefs
        1
    )
    new_conf = max(0, min(100, new_conf))
    ids["identity_confidence"] = new_conf

    # ── CRISIS DETECTION ──────────────────────────────────────────────
    if new_conf < IDENTITY_CRISIS_THRESHOLD and not ids["crisis_active"]:
        ids["crisis_active"] = True
        ids["crisis_tick"]   = tick
        ids["crisis_reason"] = (
            "Values have drifted far from %s archetype (confidence: %d). "
            "Beliefs collapsed: %d." % (current, round(new_conf), collapsed_beliefs)
        )
        agent["emotion"] = "afraid"
        sm["identity_stability"] = max(0, sm.get("identity_stability", 70) - 20)

        _remember(agent, "trauma",
                  "IDENTITY CRISIS: I no longer know what I stand for. Y%d" % year,
                  importance=5)
        _log(world,
             "IDENTITY CRISIS: %s (%s) — confidence=%d, was=%s" % (
                 agent["name"], agent["type"], round(new_conf), current), "value_engine")
        _history(world,
                 "%s entered an identity crisis — their sense of self collapsed Y%d" % (
                     agent["name"], year), 4)
        world["stats"]["identity_crises"] = world["stats"].get("identity_crises", 0) + 1

    # ── CRISIS RESOLUTION ─────────────────────────────────────────────
    elif ids["crisis_active"]:
        crisis_age = tick - ids.get("crisis_tick", tick)

        # Resolve after at least 10 ticks OR when confidence recovers
        if crisis_age >= 10 or new_conf > IDENTITY_CRISIS_THRESHOLD + 15:
            _resolve_identity_crisis(agent, world, values, year)

    # ── PASSIVE IDENTITY EVOLUTION (no crisis needed) ─────────────────
    # Every 200 ticks, check if dominant value has drifted enough
    # to naturally shift identity without crisis
    elif tick % 200 == 0 and tick > 0:
        actual_dom = max(values, key=values.get) if values else "survival"
        expected_identity = IDENTITY_RESOLUTION.get(actual_dom, current)

        if expected_identity != current and values.get(actual_dom, 0) > 70:
            # Values have shifted substantially — quiet identity evolution
            _transform_identity(agent, world, expected_identity,
                                "values evolved naturally over time", year, quiet=True)


def _resolve_identity_crisis(agent, world, values, year):
    """Resolve an active identity crisis into a new identity."""
    ids = agent["identity_system"]

    # Find the value the agent has been relying on most during crisis
    dom_value = max(values, key=values.get) if values else "survival"
    new_identity = IDENTITY_RESOLUTION.get(dom_value, "the_survivor")

    reason = ("Emerged from crisis anchored in %s. The old self is gone. "
              "The new self is %s." % (dom_value.replace("_", " "), new_identity))

    _transform_identity(agent, world, new_identity, reason, year, quiet=False)

    ids["crisis_active"] = False
    ids["crisis_reason"] = None
    agent["emotion"] = "inspired"

    sm = agent.get("self_model", {})
    sm["identity_stability"] = min(100, sm.get("identity_stability", 50) + 25)

    world["stats"]["identity_transformations"] = world["stats"].get("identity_transformations", 0) + 1


def _transform_identity(agent, world, new_identity, reason, year, quiet=False):
    """Apply an identity transformation."""
    ids     = agent["identity_system"]
    sm      = agent.get("self_model", {})
    old     = ids["current_identity"]

    if new_identity == old:
        return

    archetype = IDENTITY_ARCHETYPES.get(new_identity, {})
    desc      = archetype.get("desc", "")

    ids["current_identity"]    = new_identity
    ids["identity_confidence"] = 55  # reset at moderate confidence
    ids["archetype_desc"]      = desc
    ids["transformations"]     += 1
    ids["last_transform_year"] = year
    ids["identity_history"].append(new_identity)

    # Update self_model label
    sm["self_label"] = desc

    importance = 5 if not quiet else 3
    _remember(agent, "discovery",
              "IDENTITY SHIFT: I am no longer %s. I am %s (%s). Y%d" % (
                  old.replace("_", " "), new_identity.replace("_", " "), desc, year),
              importance=importance)

    if not quiet:
        _log(world, "IDENTITY TRANSFORMED: %s (%s) — %s → %s" % (
            agent["name"], agent["type"], old, new_identity), "value_engine")
        _history(world, "%s transformed: became %s Y%d" % (
            agent["name"], new_identity.replace("_", " "), year), 4)
    else:
        _log(world, "IDENTITY EVOLVED: %s (%s) quietly became %s" % (
            agent["name"], agent["type"], new_identity), "value_engine")


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# SYSTEM 4 — META-COGNITION
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

def tick_meta_cognition(agent, world):
    """
    Agent notices patterns in their own behaviour and adjusts.
    Runs infrequently — only when agent is 'mature' enough.
    """
    if "meta_cognition" not in agent:
        init_value_system(agent)

    mc   = agent["meta_cognition"]
    tick = world.get("tick", 0)
    year = world.get("year", 1)
    age  = agent.get("age", 0)

    # Only mature agents can self-reflect
    if age < 50:
        return

    # Run infrequently
    if tick - mc.get("last_meta_tick", -100) < 25:
        return

    # ── TRACK INTENTION HISTORY ───────────────────────────────────────
    bdi = agent.get("bdi", {})
    intention = bdi.get("current_intention")
    if intention:
        dtype = intention["desire"]
        mc["intention_history"][dtype] = mc["intention_history"].get(dtype, 0) + 1

    total = sum(mc["intention_history"].values())
    mc["intention_history"]["total_intentions"] = total

    # Also track recent plan outcomes
    plan_history = bdi.get("plan_history", [])
    recent_failures = sum(1 for p in plan_history[-5:] if p.get("outcome") == "failure")
    mc["intention_history"]["recent_failures"] = recent_failures

    memories = agent.get("memories", [])
    mc["intention_history"]["betrayal_count"] = sum(
        1 for m in memories if m["type"] == "betrayal")

    # ── CHECK META PATTERNS ───────────────────────────────────────────
    noticed = []
    for pattern in META_PATTERNS:
        pid = pattern["id"]
        if pid in mc["patterns_noticed"]:
            continue  # already noticed this one

        try:
            if pattern["condition"](agent, mc["intention_history"]):
                noticed.append(pattern)
        except Exception:
            continue

    for pattern in noticed[:1]:  # max 1 meta insight per check
        pid     = pattern["id"]
        insight = pattern["insight"]
        effects = pattern["effect"]

        mc["patterns_noticed"].append(pid)
        mc["total_insights"] += 1
        mc["last_meta_tick"] = tick

        # Apply effects
        values = agent.get("values", {})
        if "value_nudge" in effects:
            for v, delta in effects["value_nudge"].items():
                if v in values:
                    values[v] = max(0, min(100, values[v] + delta))

        if "decision_style_nudge" in effects:
            bdi_meta = agent.get("bdi", {}).get("meta", {})
            ds       = bdi_meta.get("decision_style", {})
            for k, delta in effects["decision_style_nudge"].items():
                if k in ds:
                    ds[k] = max(0.0, min(1.0, ds[k] + delta))

        if effects.get("goal_prune"):
            # Deactivate lowest-priority active goal
            active_goals = [g for g in agent.get("originated_goals", []) if g.get("active")]
            if active_goals:
                weakest = min(active_goals, key=lambda g: g.get("priority", 5))
                weakest["active"]  = False
                weakest["outcome"] = "pruned — too many goals at once"

        # Store insight
        mc["insights"].append({
            "tick":    tick,
            "year":    year,
            "pattern": pid,
            "insight": insight,
        })
        if len(mc["insights"]) > 20:
            mc["insights"] = mc["insights"][-20:]

        # Memory
        _remember(agent, "discovery",
                  "META INSIGHT: %s Y%d" % (insight, year),
                  importance=4)
        _log(world, "META-COGNITION: %s (%s) — %s" % (
            agent["name"], agent["type"], insight[:60]), "value_engine")
        _history(world, "%s: %s Y%d" % (agent["name"], insight[:60], year), 3)
        world["stats"]["meta_insights"] = world["stats"].get("meta_insights", 0) + 1

    mc["last_meta_tick"] = tick


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# SYSTEM 5 — VALUE INHERITANCE (teaching spreads values)
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

def inherit_values(teacher, student, world, strength: float = 0.3):
    """
    When one agent teaches another, some values transfer.
    Strength 0-1 controls how strongly student is influenced.
    This is how cultures propagate through a population.
    """
    if "values" not in teacher:
        return
    if "values" not in student:
        init_value_system(student)

    t_vals = teacher["values"]
    s_vals = student["values"]
    year   = world.get("year", 1)

    transferred = []

    for v in ALL_VALUES:
        t_score = t_vals.get(v, 35)
        s_score = s_vals.get(v, 35)
        gap     = t_score - s_score

        # Only pull strongly-held teacher values
        if abs(gap) < 10 or t_score < 50:
            continue

        # Student moves toward teacher's value
        delta = gap * strength * random.uniform(0.3, 0.7)
        new_score = max(0, min(100, s_score + delta))
        s_vals[v] = round(new_score, 2)

        if abs(delta) >= 5:
            transferred.append((v, round(delta, 1)))

    if transferred:
        top = sorted(transferred, key=lambda x: abs(x[1]), reverse=True)[:2]
        transfer_str = ", ".join("%s%+.0f" % (v, d) for v, d in top)
        _remember(student, "discovery",
                  "Teaching from %s (%s) shifted my values: %s Y%d" % (
                      teacher["name"], teacher["type"], transfer_str, year),
                  importance=3)
        _log(world, "VALUE INHERITANCE: %s → %s [%s]" % (
            teacher["name"], student["name"], transfer_str), "value_engine")
        world["stats"]["value_transfers"] = world["stats"].get("value_transfers", 0) + 1

    return transferred


def compute_cultural_values(world):
    """
    Compute the average value profile per faction.
    Returns a dict of faction → {value → avg_score}.
    Used for tracking cultural evolution.
    """
    from world_engine import FACTIONS
    cultures = {f: {} for f in FACTIONS}

    alive = [a for a in world.get("agents", []) if a.get("alive") and "values" in a]

    for faction in FACTIONS:
        members = [a for a in alive if a.get("faction") == faction]
        if not members:
            cultures[faction] = {v: 35 for v in ALL_VALUES}
            continue
        for v in ALL_VALUES:
            avg = sum(a["values"].get(v, 35) for a in members) / len(members)
            cultures[faction][v] = round(avg, 1)

    world["faction_culture_values"] = cultures
    return cultures


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# MASTER TICK
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

def tick_value_engine(world):
    """
    Run all 5 self-modification systems for all living agents.
    
    Add to world_engine.tick() after tick_llm_minds():
        from value_engine import tick_value_engine, init_value_system
        tick_value_engine(world)
    """
    alive = [a for a in world["agents"] if a["alive"]]
    tick  = world.get("tick", 0)

    for agent in alive:
        # Ensure initialised
        if "values" not in agent:
            init_value_system(agent)

        try:
            # 1. Value drift — runs every tick with low probability
            if random.random() < 0.15:
                tick_value_drift(agent, world)

            # 2. Goal mutation — rare, high-impact
            if random.random() < 0.06:
                tick_goal_mutation(agent, world)

            # 3. Identity — medium frequency
            if random.random() < 0.08:
                tick_identity(agent, world)

            # 4. Meta-cognition — infrequent, only mature agents
            if random.random() < 0.04 and agent.get("age", 0) > 50:
                tick_meta_cognition(agent, world)

        except Exception:
            pass  # never crash the world engine

    # 5. Cultural value computation — every 50 ticks
    if tick % 50 == 0:
        try:
            compute_cultural_values(world)
        except Exception:
            pass

    world["stats"]["value_engine_ticks"] = world["stats"].get("value_engine_ticks", 0) + 1


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# UTILITIES & HELPERS
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

def get_dominant_values(agent, n=3):
    """Return the top N value names for this agent."""
    values = agent.get("values", {})
    if not values:
        return []
    return sorted(values, key=values.get, reverse=True)[:n]


def get_value_profile_str(agent) -> str:
    """Human-readable value profile string."""
    top = get_dominant_values(agent, 5)
    values = agent.get("values", {})
    return " | ".join("%s:%.0f" % (v.replace("_", " "), values[v]) for v in top)


def get_identity_label(agent) -> str:
    """Return the agent's current identity archetype label."""
    ids = agent.get("identity_system", {})
    return ids.get("current_identity", "unknown").replace("_", " ")


def get_value_engine_summary(agent) -> dict:
    """Full summary of an agent's self-modification state."""
    values = agent.get("values", {})
    ids    = agent.get("identity_system", {})
    mc     = agent.get("meta_cognition", {})
    goals  = [g for g in agent.get("originated_goals", []) if g.get("active")]

    top_values = sorted(values.items(), key=lambda x: -x[1])[:5] if values else []
    goal_history = [g for g in agent.get("originated_goals", []) if not g.get("active")]

    return {
        "name":               agent["name"],
        "type":               agent["type"],
        "age":                agent.get("age", 0),
        "identity":           ids.get("current_identity", "?").replace("_", " "),
        "identity_confidence": ids.get("identity_confidence", 0),
        "identity_crises":    ids.get("transformations", 0),
        "top_values":         [(v.replace("_"," "), round(s,1)) for v, s in top_values],
        "active_goals":       [(g["goal"][:40], g["type"]) for g in goals],
        "goal_mutations":     len([g for g in agent.get("originated_goals", [])
                                   if g.get("outcome","").startswith("mutated")]),
        "goal_splits":        len([g for g in agent.get("originated_goals", [])
                                   if g.get("outcome","") == "split into sub-goals"]),
        "goal_merges":        len([g for g in agent.get("originated_goals", [])
                                   if g.get("outcome","").startswith("merged")]),
        "meta_insights":      mc.get("total_insights", 0),
        "patterns_noticed":   mc.get("patterns_noticed", []),
        "value_snapshots":    len(agent.get("value_history", [])),
    }


def get_world_value_snapshot(world) -> dict:
    """World-level summary of value engine activity."""
    alive = [a for a in world["agents"] if a["alive"] and "values" in a]
    stats = world.get("stats", {})

    # Find most extreme individual values across all agents
    if alive:
        max_agent = max(alive, key=lambda a: max(a["values"].values()) if a.get("values") else 0)
        dom_val = max(max_agent.get("values", {}), key=max_agent["values"].get) if max_agent.get("values") else "?"
    else:
        max_agent = None
        dom_val   = "?"

    return {
        "tick":                world.get("tick", 0),
        "year":                world.get("year", 1),
        "agents_with_values":  len(alive),
        "total_mutations":     stats.get("goal_mutations", 0),
        "total_splits":        stats.get("goal_splits", 0),
        "total_merges":        stats.get("goal_merges", 0),
        "total_crises":        stats.get("identity_crises", 0),
        "total_transforms":    stats.get("identity_transformations", 0),
        "total_meta_insights": stats.get("meta_insights", 0),
        "total_value_transfers":stats.get("value_transfers", 0),
        "most_extreme_agent":  max_agent["name"] if max_agent else "?",
        "most_extreme_value":  dom_val,
        "faction_cultures":    world.get("faction_culture_values", {}),
        "identity_distribution": _count_identities(alive),
    }


def _count_identities(alive) -> dict:
    counts = {}
    for a in alive:
        ids = a.get("identity_system", {})
        label = ids.get("current_identity", "unknown")
        counts[label] = counts.get(label, 0) + 1
    return dict(sorted(counts.items(), key=lambda x: -x[1]))


def _count_collapsed_beliefs(agent) -> int:
    return sum(1 for bv in agent.get("beliefs", {}).values()
               if bv.get("value") == False)


def _eval_goal_condition(cond_str, agent, battles, losses, betrayals,
                          is_legend, age, active_wars, values):
    """Safely evaluate a goal mutation condition string."""
    def value(name):
        return values.get(name, 35)
    try:
        return eval(cond_str)
    except Exception:
        return False


def _remember(agent, mtype, content, importance=1):
    try:
        from world_engine import remember
        remember(agent, mtype, content, importance)
    except ImportError:
        agent.setdefault("memories", []).append({
            "type": mtype, "content": content,
            "tick": 0, "year": 0, "season": "?",
            "importance": importance,
        })


def _log(world, msg, cat="value_engine"):
    try:
        from world_engine import log
        log(msg, cat)
    except ImportError:
        print("[%s] %s" % (cat.upper(), msg))


def _history(world, msg, importance=3):
    try:
        from world_engine import history
        history(msg, importance)
    except ImportError:
        pass
