"""
╔══════════════════════════════════════════════════════════════════════╗
║        AGI WORLD ENGINE — COLLECTIVE INTELLIGENCE v1.0              ║
║        Phase 4: Emergent Mind + Eternal Autonomous Loop              ║
╠══════════════════════════════════════════════════════════════════════╣
║                                                                      ║
║  TWO SYSTEMS:                                                        ║
║                                                                      ║
║  ── COLLECTIVE INTELLIGENCE ──────────────────────────────────────  ║
║                                                                      ║
║  1. KNOWLEDGE PROPAGATION NETWORK                                    ║
║     Knowledge doesn't just exist in agents — it flows between       ║
║     them like water finding its level. Ideas spread, mutate,        ║
║     get rediscovered, and die when no one carries them.             ║
║     Concepts link to other concepts; insight cascades are real.     ║
║                                                                      ║
║  2. INSTITUTIONAL CONSENSUS MIND                                     ║
║     Each institution develops a collective belief system that        ║
║     is more than the sum of its members. The institution can        ║
║     hold contradictory beliefs its individual members don't.        ║
║     It develops institutional memory that outlives any founder.     ║
║                                                                      ║
║  3. EMERGENT CULTURAL MOVEMENTS                                      ║
║     When enough agents share a value drift in the same direction,   ║
║     a cultural movement spontaneously coalesces — not by design     ║
║     but by convergence. Movements can spread, splinter, or die.     ║
║                                                                      ║
║  4. DISTRIBUTED PROBLEM SOLVING                                      ║
║     When the world faces a crisis (plague, famine, war), nearby     ║
║     agents pool cognitive effort. Problems get broken into pieces   ║
║     and assigned to agents most suited to solve them.               ║
║                                                                      ║
║  ── ETERNAL AUTONOMOUS LOOP ───────────────────────────────────────  ║
║                                                                      ║
║  5. WORLD HEALTH MONITOR                                             ║
║     Tracks 8 vital signs: population, diversity, knowledge, faith,  ║
║     conflict_balance, resource_balance, emotional_health, agency.   ║
║     Each vital has a healthy range — outside it, interventions fire.║
║                                                                      ║
║  6. SELF-HEALING ENGINE                                              ║
║     World imbalances trigger targeted responses: mass death →       ║
║     accelerated births + resource boost; total peace → tension      ║
║     seeds; knowledge collapse → new wandering scholars; monoculture ║
║     → faction schism. The world fights to stay interesting.         ║
║                                                                      ║
║  7. STAGNATION DETECTION + UPHEAVAL                                  ║
║     If the world goes 50+ ticks without history-worthy events,      ║
║     an upheaval fires: a legendary figure appears, a catastrophe    ║
║     strikes, a revelation spreads, or an ancient evil awakens.      ║
║     Entropy has a cure.                                              ║
║                                                                      ║
║  8. EPOCH TRANSITIONS                                                ║
║     Every 200 years, a new epoch begins. The world remembers the    ║
║     old one but reinvents itself: new faction alliances, new        ║
║     dominant values, new technologies discovered, old institutions  ║
║     collapse and new ones form. Time moves in ages.                 ║
║                                                                      ║
║  Integration (3 lines):                                              ║
║    from collective_loop import tick_collective, init_collective      ║
║    Call init_collective(world) from initialize()                    ║
║    Call tick_collective(world) from tick()                          ║
╚══════════════════════════════════════════════════════════════════════╝
"""

import random
import math
import json
from datetime import datetime

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# CONFIGURATION
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

COLLECTIVE_CONFIG = {
    # Knowledge Network
    "knowledge_spread_radius":   12.0,   # how far ideas can propagate
    "knowledge_decay_ticks":    200,     # ticks before unused knowledge fades
    "max_concepts_per_agent":    30,     # per-agent concept cap
    "concept_mutation_chance":   0.08,   # probability concept mutates in transit

    # Institutional Consensus
    "institution_mind_tick":     10,     # ticks between institution mind updates
    "consensus_drift_rate":      0.05,   # how fast institution beliefs drift

    # Cultural Movements
    "movement_threshold":        0.35,   # fraction of agents sharing a value for movement to form
    "movement_min_agents":       4,      # minimum agents for a movement
    "movement_spread_rate":      0.04,   # per-tick spread probability

    # Distributed Problem Solving
    "crisis_broadcast_radius":   25.0,   # how far a crisis call reaches
    "problem_solve_ticks":       30,     # max ticks for collaborative solving

    # World Health
    "health_check_interval":     10,     # ticks between health checks
    "stagnation_threshold":      50,     # ticks of low-event to trigger upheaval
    "upheaval_cooldown":         80,     # ticks before another upheaval can fire
    "epoch_length_years":       200,     # years per epoch
}

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# CONCEPT CATALOGUE — the knowledge atoms that propagate
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

# Concept categories and their base ideas
CONCEPT_SEEDS = {
    "philosophy": [
        "all suffering contains a lesson",
        "the self is a story we tell ourselves",
        "every system eventually devours itself",
        "truth and power are rarely allies",
        "identity is chosen, not given",
        "to understand an enemy is to become them slightly",
    ],
    "strategy": [
        "the weakest point is the most guarded",
        "patience outlasts aggression",
        "an army fights best when it has something to protect",
        "control the supply lines, control the war",
        "the second strike lands harder than the first",
    ],
    "medicine": [
        "disease follows the path of least resistance",
        "the body remembers every wound",
        "healing begins before the injury heals",
        "the cure and the poison share the same root",
        "prevention is invisible and therefore undervalued",
    ],
    "governance": [
        "power legitimised by fear requires constant violence",
        "the institution outlives the ideals that created it",
        "laws reflect the fears of those who wrote them",
        "every revolution becomes the thing it overthrew",
        "loyalty bought is loyalty that can be rebought",
    ],
    "nature": [
        "the forest remembers every fire",
        "water always finds the path of least resistance",
        "abundance breeds fragility",
        "the harshest winters produce the most resilient springs",
    ],
    "trade": [
        "trust is the currency that buys all others",
        "the merchant who cannot be trusted cannot trade",
        "scarcity is manufactured more often than found",
        "the price of a thing is what someone else will pay",
    ],
    "faith": [
        "belief requires no evidence but cannot survive its absence",
        "the divine appears most clearly in moments of despair",
        "ritual is the architecture of the sacred",
        "faith broken and rebuilt is stronger than faith never tested",
    ],
    "war": [
        "every war ends with the losers planning the next one",
        "the soldier who enjoys killing is the first to lose his soul",
        "a battle won by treachery cannot be held",
        "the longest peace is just a very long preparation",
    ],
}

# How concepts link to each other (concept → linked concepts)
CONCEPT_LINKS = {
    "all suffering contains a lesson":        ["the body remembers every wound", "identity is chosen, not given"],
    "every system eventually devours itself":  ["the institution outlives the ideals that created it", "every revolution becomes the thing it overthrew"],
    "power legitimised by fear":              ["loyalty bought is loyalty that can be rebought", "control the supply lines"],
    "trust is the currency":                  ["loyalty bought is loyalty that can be rebought", "belief requires no evidence"],
    "the cure and the poison":                ["understanding an enemy", "abundance breeds fragility"],
    "identity is chosen":                     ["the self is a story", "faith broken and rebuilt"],
    "every war ends with losers":             ["every revolution becomes", "patience outlasts aggression"],
}

# Mutations a concept can undergo in transit (word substitutions)
CONCEPT_MUTATIONS = [
    ("suffering", "loss"),
    ("always", "often"),
    ("every", "most"),
    ("truth", "wisdom"),
    ("power", "strength"),
    ("faith", "belief"),
    ("war", "conflict"),
    ("the self", "the mind"),
    ("devours", "destroys"),
    ("loyalty", "allegiance"),
]


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# WORLD HEALTH — vital signs
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

VITAL_RANGES = {
    # vital: (min_healthy, max_healthy, weight)
    "population":        (4,  40,   2.0),
    "faction_diversity": (2,   4,   1.5),   # number of factions with >1 agent
    "knowledge_level":   (30, 300,  1.0),
    "faith_level":       (0,  150,  0.5),
    "conflict_balance":  (0,   3,   1.0),   # active wars
    "resource_balance":  (30, 500,  1.0),   # total resources
    "emotional_health":  (0.3, 0.9, 1.5),  # fraction not in negative emotion
    "active_goals":      (2,   50,  1.0),   # total active goals across world
}

# Emotions considered negative
NEGATIVE_EMOTIONS = {"afraid", "grieving", "angry", "vengeful", "weary", "lonely"}

# Upheaval event types
UPHEAVAL_TYPES = [
    {
        "id":     "wandering_sage",
        "name":   "A Wandering Sage Arrives",
        "desc":   "A legendary wanderer appears from beyond the known world, carrying ancient knowledge.",
        "effect": "spawn_sage",
    },
    {
        "id":     "ancient_revelation",
        "name":   "Ancient Revelation",
        "desc":   "A cache of ancient texts is uncovered, triggering a surge of discovery across factions.",
        "effect": "knowledge_surge",
    },
    {
        "id":     "divine_sign",
        "name":   "A Divine Sign in the Sky",
        "desc":   "Something inexplicable occurs — interpreted differently by each faction.",
        "effect": "belief_cascade",
    },
    {
        "id":     "great_plague",
        "name":   "The Great Plague Returns",
        "desc":   "A virulent disease sweeps the land, forcing cooperation or extinction.",
        "effect": "plague_surge",
    },
    {
        "id":     "dark_prophet",
        "name":   "A Dark Prophet Rises",
        "desc":   "A charismatic figure preaches doom — some follow, some rebel.",
        "effect": "faction_schism",
    },
    {
        "id":     "forgotten_war",
        "name":   "The Forgotten War Resurfaces",
        "desc":   "A dormant grievance erupts — old enemies remember what was done to them.",
        "effect": "forced_war",
    },
    {
        "id":     "golden_age_signal",
        "name":   "Signs of a Golden Age",
        "desc":   "Resources multiply, children are born healthy, hope spreads like wildfire.",
        "effect": "prosperity_surge",
    },
    {
        "id":     "world_fracture",
        "name":   "The World Fractures",
        "desc":   "A catastrophic geological event reshapes the map and forces migrations.",
        "effect": "forced_migration",
    },
]

# Epoch names
EPOCH_NAMES = [
    "The Age of Fire",
    "The Age of Iron",
    "The Age of Faith",
    "The Age of Shadow",
    "The Age of Knowledge",
    "The Age of Blood",
    "The Age of Silence",
    "The Age of Gold",
    "The Age of Reckoning",
    "The Age of Renewal",
    "The Age of Fracture",
    "The Age of Convergence",
]


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# INITIALISATION
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

def init_collective(world):
    """Initialise all collective intelligence systems. Safe to call multiple times."""

    world.setdefault("knowledge_network", {
        "nodes":     {},  # concept_id → {text, category, origin_agent, origin_year, carriers, links, mutation_count}
        "edges":     [],  # [{from, to, strength, tick_formed}]
        "total_spread_events": 0,
        "total_mutations":     0,
        "concepts_lost":       0,
    })

    world.setdefault("cultural_movements", [])

    world.setdefault("distributed_problems", [])

    world.setdefault("world_health", {
        "vitals":         {},
        "overall_score":  1.0,
        "last_check_tick": 0,
        "interventions":  [],
        "alerts":         [],
    })

    world.setdefault("eternal_loop", {
        "last_upheaval_tick":   -999,
        "upheavals_fired":      [],
        "stagnation_ticks":     0,
        "last_major_event_tick": 0,
        "current_epoch":        0,
        "epoch_start_year":     1,
        "epoch_name":           EPOCH_NAMES[0],
        "epochs_elapsed":       0,
        "loop_ticks":           0,
    })

    world.setdefault("collective_stats", {
        "concepts_created":      0,
        "concepts_spread":       0,
        "concepts_mutated":      0,
        "concepts_lost":         0,
        "movements_formed":      0,
        "movements_dissolved":   0,
        "problems_solved":       0,
        "upheavals_fired":       0,
        "self_heals":            0,
        "epochs_completed":      0,
    })

    # Seed the knowledge network with starting concepts
    if not world["knowledge_network"]["nodes"]:
        _seed_knowledge_network(world)

    # Init agent knowledge sets
    for agent in world.get("agents", []):
        if agent.get("alive") and "concepts" not in agent:
            _init_agent_concepts(agent, world)


def _seed_knowledge_network(world):
    """Plant initial concepts in the knowledge network."""
    kn = world["knowledge_network"]
    alive = [a for a in world.get("agents", []) if a.get("alive")]

    # Pick one concept per category, assign to a random agent carrier
    for category, concepts in CONCEPT_SEEDS.items():
        concept_text = random.choice(concepts)
        cid = _concept_id(concept_text)
        carrier = random.choice(alive) if alive else None

        kn["nodes"][cid] = {
            "text":           concept_text,
            "category":       category,
            "origin_agent":   carrier["name"] if carrier else "the world",
            "origin_year":    world.get("year", 1),
            "carriers":       [carrier["id"]] if carrier else [],
            "links":          [],
            "mutation_count": 0,
            "tick_born":      world.get("tick", 0),
            "last_spread_tick": world.get("tick", 0),
        }

        if carrier:
            carrier.setdefault("concepts", {})[cid] = {
                "text": concept_text, "learned_tick": 0, "spread_count": 0
            }

    world["collective_stats"]["concepts_created"] += len(CONCEPT_SEEDS)


def _init_agent_concepts(agent, world):
    """Give a new agent 1-3 starting concepts based on their type."""
    agent.setdefault("concepts", {})
    kn = world["knowledge_network"]
    if not kn["nodes"]:
        return

    # Pick concepts aligned with agent type
    type_affinities = {
        "scholar":     ["philosophy", "governance"],
        "warrior":     ["war", "strategy"],
        "healer":      ["medicine", "nature"],
        "priest":      ["faith", "philosophy"],
        "merchant":    ["trade", "governance"],
        "spy":         ["strategy", "governance"],
        "farmer":      ["nature", "trade"],
        "philosopher": ["philosophy", "faith"],
        "explorer":    ["nature", "philosophy"],
        "builder":     ["strategy", "trade"],
        "assassin":    ["war", "strategy"],
    }
    preferred = type_affinities.get(agent.get("type", ""), ["philosophy"])
    relevant  = [cid for cid, nd in kn["nodes"].items()
                 if nd["category"] in preferred]

    for cid in random.sample(relevant, min(2, len(relevant))):
        agent["concepts"][cid] = {
            "text":         kn["nodes"][cid]["text"],
            "learned_tick": world.get("tick", 0),
            "spread_count": 0,
        }
        if agent["id"] not in kn["nodes"][cid]["carriers"]:
            kn["nodes"][cid]["carriers"].append(agent["id"])


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# SYSTEM 1 — KNOWLEDGE PROPAGATION NETWORK
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

def tick_knowledge_propagation(world):
    """
    Ideas flow between nearby agents.
    Concepts mutate, link, and die if no one carries them.
    """
    kn    = world["knowledge_network"]
    alive = [a for a in world["agents"] if a.get("alive") and "concepts" in a]
    tick  = world.get("tick", 0)
    year  = world.get("year", 1)

    if not alive:
        return

    radius = COLLECTIVE_CONFIG["knowledge_spread_radius"]

    # ── PROPAGATION ───────────────────────────────────────────────────
    for agent in alive:
        if random.random() > 0.12:
            continue
        if not agent.get("concepts"):
            continue

        # Find nearby agents
        pos   = agent["position"]
        nearby = [a for a in alive
                  if a["id"] != agent["id"] and _dist(pos, a["position"]) < radius]
        if not nearby:
            continue

        listener = random.choice(nearby)
        concept_id = random.choice(list(agent["concepts"].keys()))
        node       = kn["nodes"].get(concept_id)
        if not node:
            continue

        # Has listener already received this concept?
        if concept_id in listener.get("concepts", {}):
            # But might trigger an INSIGHT CASCADE — linked concept unlocks
            _trigger_insight_cascade(agent, listener, concept_id, kn, world)
            continue

        # Possibly mutate in transit
        text = node["text"]
        mutated = False
        if random.random() < COLLECTIVE_CONFIG["concept_mutation_chance"]:
            text, mutated = _mutate_concept(text)
            if mutated:
                node["mutation_count"] += 1
                kn["total_mutations"]  += 1

        # Transfer concept
        listener.setdefault("concepts", {})[concept_id] = {
            "text":         text,
            "learned_tick": tick,
            "spread_count": 0,
            "mutated":      mutated,
            "learned_from": agent["name"],
        }

        # Update node carriers
        if listener["id"] not in node["carriers"]:
            node["carriers"].append(listener["id"])
        node["last_spread_tick"] = tick
        agent["concepts"][concept_id]["spread_count"] = \
            agent["concepts"][concept_id].get("spread_count", 0) + 1

        kn["total_spread_events"] += 1
        world["collective_stats"]["concepts_spread"] += 1

        # Memory for both
        _remember(listener, "discovery",
                  '%s shared an idea: "%s" Y%d' % (
                      agent["name"], text[:55], year),
                  importance=2)

        # Concept's impact on listener values
        _apply_concept_value_impact(listener, node, world)

        if mutated:
            world["collective_stats"]["concepts_mutated"] += 1
            _log(world, 'KNOWLEDGE MUTATED: "%s" → "%s" (via %s → %s)' % (
                node["text"][:40], text[:40], agent["name"], listener["name"]), "collective")

    # ── NEW CONCEPT CREATION (from deep reflection or insight) ────────
    for agent in alive:
        if random.random() > 0.005:
            continue
        if len(agent.get("concepts", {})) < 3:
            continue

        # Agent synthesises a new concept from two they hold
        held      = list(agent["concepts"].keys())
        if len(held) < 2:
            continue
        cid_a, cid_b = random.sample(held, 2)
        na = kn["nodes"].get(cid_a, {})
        nb = kn["nodes"].get(cid_b, {})
        if not na or not nb:
            continue

        synthesis = _synthesise_concept(na["text"], nb["text"], agent)
        if not synthesis:
            continue

        new_cid = _concept_id(synthesis)
        if new_cid in kn["nodes"]:
            continue

        kn["nodes"][new_cid] = {
            "text":           synthesis,
            "category":       na.get("category", "philosophy"),
            "origin_agent":   agent["name"],
            "origin_year":    year,
            "carriers":       [agent["id"]],
            "links":          [cid_a, cid_b],
            "mutation_count": 0,
            "tick_born":      tick,
            "last_spread_tick": tick,
            "synthesised":    True,
        }
        agent["concepts"][new_cid] = {
            "text": synthesis, "learned_tick": tick, "spread_count": 0,
            "synthesised": True,
        }

        world["collective_stats"]["concepts_created"] += 1
        _remember(agent, "discovery",
                  'Synthesised new idea: "%s" Y%d' % (synthesis[:60], year),
                  importance=4)
        _log(world, 'CONCEPT BORN: "%s" — originated by %s (%s)' % (
            synthesis[:55], agent["name"], agent["type"]), "collective")
        _history(world, '%s conceived a new idea: "%s"' % (agent["name"], synthesis[:50]), 3)
        world["stats"]["concepts_synthesised"] = world["stats"].get("concepts_synthesised", 0) + 1

    # ── CONCEPT DECAY ─────────────────────────────────────────────────
    if tick % 50 == 0:
        alive_ids = {a["id"] for a in alive}
        decay_threshold = COLLECTIVE_CONFIG["knowledge_decay_ticks"]
        dead_concepts = []

        for cid, node in list(kn["nodes"].items()):
            # Remove dead carriers
            node["carriers"] = [c for c in node["carriers"] if c in alive_ids]

            # If no living carriers, concept is lost
            if not node["carriers"]:
                if tick - node.get("tick_born", 0) > decay_threshold:
                    dead_concepts.append(cid)

        for cid in dead_concepts:
            lost_text = kn["nodes"][cid]["text"]
            del kn["nodes"][cid]
            kn["concepts_lost"] += 1
            world["collective_stats"]["concepts_lost"] += 1
            _log(world, 'CONCEPT LOST: "%s" — no living carrier remains' % lost_text[:55], "collective")
            _history(world, 'A concept was forgotten: "%s"' % lost_text[:55], 2)


def _trigger_insight_cascade(teacher, student, seed_cid, kn, world):
    """
    When two agents who share a concept meet, linked concepts may unlock.
    This models how conversations deepen existing understanding.
    """
    seed_node = kn["nodes"].get(seed_cid, {})
    seed_text = seed_node.get("text", "")

    # Check if seed concept links to anything
    for other_text, linked_texts in CONCEPT_LINKS.items():
        if other_text[:20] in seed_text[:20]:
            for linked in linked_texts:
                new_cid = _concept_id(linked)
                if new_cid in kn["nodes"] and new_cid not in student.get("concepts", {}):
                    node = kn["nodes"][new_cid]
                    student.setdefault("concepts", {})[new_cid] = {
                        "text":         node["text"],
                        "learned_tick": world.get("tick", 0),
                        "spread_count": 0,
                        "via_cascade":  True,
                        "unlocked_by":  seed_cid,
                    }
                    if student["id"] not in node["carriers"]:
                        node["carriers"].append(student["id"])
                    world["collective_stats"]["concepts_spread"] += 1
                    world["stats"]["insight_cascades"] = world["stats"].get("insight_cascades", 0) + 1
                    _log(world, 'INSIGHT CASCADE: "%s" unlocked "%s" in %s' % (
                        seed_text[:30], node["text"][:30], student["name"]), "collective")
                    return  # one cascade per meeting


def _apply_concept_value_impact(agent, node, world):
    """A newly-learned concept nudges agent values."""
    if "values" not in agent:
        return
    category_impacts = {
        "philosophy":  {"truth": +2, "knowledge": +1},
        "strategy":    {"power": +1, "survival": +1},
        "medicine":    {"compassion": +2, "knowledge": +1},
        "governance":  {"justice": +2, "order": +1},
        "nature":      {"beauty": +1, "growth": +1},
        "trade":       {"connection": +1, "security": +1},
        "faith":       {"faith": +2, "transcendence": +1},
        "war":         {"survival": +1, "power": +1},
    }
    impacts = category_impacts.get(node.get("category", "philosophy"), {})
    vals = agent["values"]
    for v, delta in impacts.items():
        if v in vals:
            vals[v] = max(0, min(100, vals[v] + delta))


def _mutate_concept(text):
    """Apply a random word substitution to a concept string."""
    for orig, rep in CONCEPT_MUTATIONS:
        if orig in text and random.random() < 0.4:
            return text.replace(orig, rep, 1), True
    return text, False


def _synthesise_concept(text_a, text_b, agent):
    """Combine two concept texts into a plausible new synthesis."""
    # Extract key phrases
    words_a = text_a.split()
    words_b = text_b.split()

    if len(words_a) < 4 or len(words_b) < 4:
        return None

    # Take first clause of A and last clause of B
    half_a = " ".join(words_a[:len(words_a)//2])
    half_b = " ".join(words_b[len(words_b)//2:])

    synthesis = half_a + " — just as " + half_b

    # Quality check: must be a reasonable length
    if len(synthesis) < 20 or len(synthesis) > 120:
        return None

    return synthesis


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# SYSTEM 2 — INSTITUTIONAL CONSENSUS MIND
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

def tick_institutional_minds(world):
    """
    Each institution develops a collective mind:
    — Aggregates member beliefs into institutional consensus
    — Can hold beliefs individual members don't
    — Develops institutional memory that outlives founders
    — Can issue institutional directives to members
    """
    institutions = world.get("institutions", [])
    alive        = {a["id"]: a for a in world["agents"] if a.get("alive")}
    tick         = world.get("tick", 0)
    year         = world.get("year", 1)

    if tick % COLLECTIVE_CONFIG["institution_mind_tick"] != 0:
        return

    for inst in institutions:
        if not inst.get("active"):
            continue

        # Get living members
        members = [alive[mid] for mid in inst.get("members", []) if mid in alive]
        if len(members) < 2:
            continue

        # Ensure institution has collective mind
        if "collective_mind" not in inst:
            inst["collective_mind"] = {
                "consensus_beliefs": {},  # belief → {confidence, dissenters}
                "dominant_value":    None,
                "collective_memory": inst.get("collective_memory", []),
                "directives":        [],  # current institutional directives to members
                "tension":           0,   # internal disagreement 0-100
                "age_ticks":         0,
                "wisdom_archive":    [],  # condensed institutional wisdom
            }
        cm = inst["collective_mind"]
        cm["age_ticks"] += COLLECTIVE_CONFIG["institution_mind_tick"]

        # ── AGGREGATE BELIEFS ─────────────────────────────────────────
        belief_pool = {}
        for m in members:
            for bk, bv in m.get("beliefs", {}).items():
                if bk not in belief_pool:
                    belief_pool[bk] = []
                belief_pool[bk].append((bv["confidence"], bv.get("value", True)))

        # Compute consensus per belief
        for bk, entries in belief_pool.items():
            avg_conf  = sum(c for c, v in entries) / len(entries)
            holdingTF = sum(1 for c, v in entries if v != False)
            dissenters = len(entries) - holdingTF

            cm["consensus_beliefs"][bk] = {
                "confidence": round(avg_conf, 1),
                "value":      holdingTF > dissenters,
                "dissenters": dissenters,
                "total":      len(entries),
            }

        # ── INTERNAL TENSION ─────────────────────────────────────────
        # High when many beliefs have near-equal dissenters
        if cm["consensus_beliefs"]:
            contested = sum(
                1 for cb in cm["consensus_beliefs"].values()
                if cb["dissenters"] > 0 and cb["dissenters"] >= cb["total"] // 2
            )
            cm["tension"] = round(min(100, (contested / len(cm["consensus_beliefs"])) * 100), 1)

        # ── DOMINANT VALUE (from member values) ───────────────────────
        if all("values" in m for m in members):
            value_sums = {}
            for m in members:
                for v, score in m["values"].items():
                    value_sums[v] = value_sums.get(v, 0) + score
            if value_sums:
                dom = max(value_sums, key=value_sums.get)
                cm["dominant_value"] = dom

        # ── INSTITUTIONAL DIRECTIVES ──────────────────────────────────
        # Institution issues directives based on its collective mind
        cm["directives"] = []

        if cm["tension"] > 60:
            cm["directives"].append({
                "type":    "internal_debate",
                "message": "The %s is divided. Members must settle a disagreement." % inst["name"],
            })

        if inst["type"] == "academy" and cm["consensus_beliefs"].get("knowledge_is_power", {}).get("confidence", 0) > 70:
            cm["directives"].append({
                "type":    "research_drive",
                "message": "The academy calls its members to pursue knowledge above all else.",
            })
            # Actually boost knowledge
            world["resources"]["knowledge"] = world["resources"].get("knowledge", 0) + len(members)

        if inst["type"] == "war_council" and cm["dominant_value"] in ("power", "survival"):
            cm["directives"].append({
                "type":    "war_preparation",
                "message": "The council prepares for conflict. Warriors should fight.",
            })
            for m in members:
                m["battle_power"] = m.get("battle_power", 10) + 0.2

        if inst["type"] == "holy_order" and cm["consensus_beliefs"].get("the_divine_exists", {}).get("confidence", 0) > 65:
            cm["directives"].append({
                "type":    "faith_surge",
                "message": "The order calls for a renewal of faith.",
            })
            for m in members:
                m["faith"] = min(100, m.get("faith", 0) + 2)

        if inst["type"] == "healers_circle":
            # Identify sick members and direct healers to them
            sick = [m for m in members if m.get("health", 100) < 50]
            if sick:
                cm["directives"].append({
                    "type":    "healing_priority",
                    "message": "Circle prioritises healing %s members." % len(sick),
                })
                for m in sick:
                    m["health"] = min(100, m.get("health", 100) + 5)

        # ── HIGH TENSION → INSTITUTIONAL SCHISM ─────────────────────
        if cm["tension"] > 80 and len(members) >= 4 and random.random() < 0.05:
            _trigger_institutional_schism(inst, members, world)

        # ── RECORD IN INSTITUTIONAL MEMORY ──────────────────────────
        if random.random() < 0.02:
            directive_summary = cm["directives"][0]["message"] if cm["directives"] else "We held together."
            cm["collective_memory"].append({
                "year":    year,
                "tick":    tick,
                "tension": cm["tension"],
                "event":   directive_summary[:80],
                "members": len(members),
                "dominant_value": cm.get("dominant_value", "?"),
            })
            if len(cm["collective_memory"]) > 30:
                cm["collective_memory"] = cm["collective_memory"][-30:]

        # ── INSTITUTIONAL WISDOM (every 500 ticks) ──────────────────
        if cm["age_ticks"] % 500 == 0 and cm["collective_memory"]:
            wisdom = _derive_institutional_wisdom(inst, cm, members, year)
            if wisdom:
                cm["wisdom_archive"].append(wisdom)
                _log(world, 'INSTITUTIONAL WISDOM: %s — "%s"' % (inst["name"], wisdom[:60]), "collective")
                _history(world, '%s recorded institutional wisdom: "%s"' % (inst["name"], wisdom[:55]), 3)
                # Share wisdom with all members as a memory
                for m in members:
                    _remember(m, "discovery",
                              'Institutional wisdom of %s: "%s" Y%d' % (inst["name"], wisdom[:60], year),
                              importance=3)


def _trigger_institutional_schism(inst, members, world):
    """High internal tension splits an institution."""
    year = world.get("year", 1)
    half = len(members) // 2

    # Split members into two groups
    group_a = members[:half]
    group_b = members[half:]

    inst["active"] = False
    inst["dissolved_year"] = year
    inst["dissolution_cause"] = "schism"

    # Clear members' institution affiliation
    for m in group_a + group_b:
        m.pop("institution", None)
        m.pop("institution_type", None)

    # Each group remembers the schism
    for m in group_a:
        _remember(m, "betrayal",
                  "The %s fractured. I stand with those who share my values. Y%d" % (inst["name"], year),
                  importance=4)
    for m in group_b:
        _remember(m, "betrayal",
                  "The %s tore itself apart over disagreement. I survived the schism. Y%d" % (inst["name"], year),
                  importance=4)

    _log(world, "INSTITUTIONAL SCHISM: %s dissolved after internal conflict" % inst["name"], "collective")
    _history(world, "The %s shattered — schism split its members Y%d" % (inst["name"], year), 4)
    world["collective_stats"]["movements_dissolved"] = world["collective_stats"].get("movements_dissolved", 0) + 1
    world["stats"]["institutions_dissolved"] = world["stats"].get("institutions_dissolved", 0) + 1


def _derive_institutional_wisdom(inst, cm, members, year):
    """Generate an institutional wisdom statement from collective memory."""
    itype = inst.get("type", "")
    dom_val = cm.get("dominant_value", "survival")
    tension = cm.get("tension", 0)

    wisdom_templates = {
        "academy": [
            "Knowledge held by one is fragile. Knowledge shared is a fortress.",
            "We have outlasted three generations of scholars. The questions outlast the answers.",
            "Every member who left taught us something the ones who stayed did not know.",
        ],
        "war_council": [
            "We have sent hundreds to battle. Half returned. The ones who returned understood something the dead did not.",
            "Strategy is the art of making the enemy fight the war you prepared for.",
            "The council survives because it agrees on ends, not means.",
        ],
        "holy_order": [
            "Faith persists not because it is true but because it is needed.",
            "We have seen three collapses of faith and three renewals. The pattern is the teaching.",
            "The divine speaks most clearly in the spaces between belief and doubt.",
        ],
        "healers_circle": [
            "The body and the world heal by the same laws — slowly, from the inside, when left in peace.",
            "We have healed what could be healed. The rest we have learned to sit with.",
            "Medicine is the practice of buying time for the body to remember how to survive.",
        ],
        "elder_council": [
            "We have watched civilizations be born and die. The pattern is always the same.",
            "The young believe they are the first. We know they are the latest.",
            "Wisdom is not accumulated — it is recovered, generation by generation.",
        ],
    }

    templates = wisdom_templates.get(itype, [
        "We have lasted longer than those who doubted us.",
        "An institution is a collective memory with a name.",
    ])

    if tension > 50:
        return "We survived our own disagreements. That is rarer than it sounds."

    return random.choice(templates)


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# SYSTEM 3 — EMERGENT CULTURAL MOVEMENTS
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

def tick_cultural_movements(world):
    """
    When enough agents share a value drift, a movement spontaneously forms.
    Movements spread, evolve, and eventually dissolve or institutionalise.
    """
    movements = world.get("cultural_movements", [])
    alive     = [a for a in world["agents"] if a.get("alive") and "values" in a]
    tick      = world.get("tick", 0)
    year      = world.get("year", 1)

    if not alive or tick % 20 != 0:
        return

    # ── CHECK FOR NEW MOVEMENT CONDITIONS ────────────────────────────
    threshold   = COLLECTIVE_CONFIG["movement_threshold"]
    min_agents  = COLLECTIVE_CONFIG["movement_min_agents"]
    existing_values = {m["value"] for m in movements if m.get("active")}

    # Find which values have crossed the threshold
    for value_name in ["justice", "truth", "freedom", "transcendence",
                       "revenge", "chaos", "legacy", "compassion"]:
        if value_name in existing_values:
            continue

        high_agents = [a for a in alive if a["values"].get(value_name, 0) > 68]
        frac = len(high_agents) / len(alive)

        if frac >= threshold and len(high_agents) >= min_agents:
            # Form movement
            movement = _form_movement(value_name, high_agents, world, year)
            movements.append(movement)
            world["cultural_movements"] = movements
            world["collective_stats"]["movements_formed"] += 1

    # ── TICK EXISTING MOVEMENTS ──────────────────────────────────────
    for mov in movements:
        if not mov.get("active"):
            continue

        mov["age_ticks"] = mov.get("age_ticks", 0) + 1
        members = [a for a in alive if a.get("movement") == mov["id"]]

        # Spread to nearby non-members
        if random.random() < COLLECTIVE_CONFIG["movement_spread_rate"]:
            for m in members:
                nearby = [a for a in alive
                          if a["id"] != m["id"]
                          and not a.get("movement")
                          and _dist(m["position"], a["position"]) < 15]
                if not nearby:
                    continue
                recruit = random.choice(nearby)
                # Recruit if their value is already somewhat aligned
                if recruit["values"].get(mov["value"], 0) > 50:
                    recruit["movement"] = mov["id"]
                    mov["members"].append(recruit["id"])
                    _remember(recruit, "friend",
                              'Joined the %s movement — drawn to the idea of %s. Y%d' % (
                                  mov["name"], mov["value"].replace("_", " "), year),
                              importance=3)
                    break

        # Movement dissolves if it loses most members
        if len(members) < 2:
            mov["active"] = False
            mov["dissolved_year"] = year
            _log(world, "MOVEMENT DISSOLVED: %s — too few adherents" % mov["name"], "collective")
            world["collective_stats"]["movements_dissolved"] += 1
            for a in alive:
                if a.get("movement") == mov["id"]:
                    a.pop("movement", None)
            continue

        # Movement can crystallise into an institution if it grows large enough
        if len(members) >= 6 and mov.get("age_ticks", 0) > 100 and random.random() < 0.01:
            _crystallise_movement(mov, members, world)

        # Movement boosts value of all members
        for m in members:
            v = m["values"].get(mov["value"], 50)
            m["values"][mov["value"]] = min(100, v + 0.1)


def _form_movement(value_name, agents, world, year):
    """Create a new cultural movement centred on a shared value."""
    value_movement_names = {
        "justice":       ["The Just", "The Reckoning", "Truth and Consequence"],
        "truth":         ["The Unveiled", "The Honest Hand", "The Clear Eye"],
        "freedom":       ["The Unchained", "The Free Road", "The Open Sky"],
        "transcendence": ["The Ascendant", "Beyond the Veil", "The High Path"],
        "revenge":       ["The Debt", "Unpaid Blood", "The Long Memory"],
        "chaos":         ["The Breakers", "The Unmakers", "The New Fire"],
        "legacy":        ["The Builders of Tomorrow", "The Long Road", "What Remains"],
        "compassion":    ["The Healers of the Age", "The Open Hand", "The Tender Way"],
    }

    name = random.choice(value_movement_names.get(value_name, ["The Movement"]))
    leader = max(agents, key=lambda a: a["values"].get(value_name, 0))

    movement = {
        "id":          "mov_%d" % world.get("tick", 0),
        "name":        name,
        "value":       value_name,
        "leader":      leader["name"],
        "formed_year": year,
        "members":     [a["id"] for a in agents],
        "active":      True,
        "age_ticks":   0,
        "peak_size":   len(agents),
        "crystallised": False,
    }

    # Tag members
    for a in agents:
        a["movement"] = movement["id"]

    _log(world, "MOVEMENT FORMED: '%s' — %d agents united around '%s' (leader: %s)" % (
        name, len(agents), value_name, leader["name"]), "collective")
    _history(world, "A cultural movement emerged: '%s' — centred on %s Y%d" % (
        name, value_name.replace("_", " "), year), 4)
    world["stats"]["cultural_movements_formed"] = world["stats"].get("cultural_movements_formed", 0) + 1

    return movement


def _crystallise_movement(movement, members, world):
    """A movement large enough becomes a formal institution."""
    year = world.get("year", 1)
    movement["crystallised"] = True
    movement["active"]       = False

    inst_name = "The Order of %s" % movement["name"].replace("The ", "")
    institution = {
        "id":             "inst_cryst_%d" % world.get("tick", 0),
        "type":           "cultural_order",
        "name":           inst_name,
        "symbol":         "◈",
        "desc":           "An institution crystallised from the %s movement" % movement["name"],
        "goal":           "propagate %s as the highest value" % movement["value"],
        "founder":        movement["leader"],
        "founder_faction": members[0].get("faction", "?"),
        "members":        [m["id"] for m in members],
        "created_year":   year,
        "active":         True,
        "collective_memory": [],
        "resources":      {"gold": 0, "knowledge": 0, "faith": 0},
        "achievements":   [],
        "generation":     1,
        "born_from_movement": movement["id"],
    }

    world.setdefault("institutions", []).append(institution)
    for m in members:
        m["institution"]      = inst_name
        m["institution_type"] = "cultural_order"
        m.pop("movement", None)

    _log(world, "MOVEMENT CRYSTALLISED: '%s' became institution '%s'" % (
        movement["name"], inst_name), "collective")
    _history(world, "The movement '%s' crystallised into '%s' Y%d" % (
        movement["name"], inst_name, year), 4)
    world["stats"]["institutions_formed"] = world["stats"].get("institutions_formed", 0) + 1


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# SYSTEM 4 — DISTRIBUTED PROBLEM SOLVING
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

def tick_distributed_problems(world):
    """
    When the world faces a crisis, nearby agents pool cognitive effort.
    Problems broadcast a distress signal; agents with relevant skills respond.
    """
    problems   = world.get("distributed_problems", [])
    alive      = [a for a in world["agents"] if a.get("alive")]
    tick       = world.get("tick", 0)
    year       = world.get("year", 1)
    stats      = world.get("stats", {})

    # ── DETECT CRISES ────────────────────────────────────────────────
    active_wars   = len(world.get("active_wars", []))
    plague_active = world.get("plague_active", False)
    food          = world.get("resources", {}).get("food", 100)
    knowledge     = world.get("resources", {}).get("knowledge", 50)
    pop           = sum(1 for a in alive)

    existing_problem_types = {p["type"] for p in problems if p.get("active")}

    if plague_active and "epidemic" not in existing_problem_types:
        problems.append(_spawn_problem("epidemic",
            "A plague is killing the population — healers and scholars must find a cure.",
            ["healer", "scholar", "plague_doctor"], world))

    if food < 20 and "famine" not in existing_problem_types:
        problems.append(_spawn_problem("famine",
            "Food is critically scarce — farmers and builders must organise distribution.",
            ["farmer", "builder", "merchant"], world))

    if active_wars >= 3 and "war_fatigue" not in existing_problem_types:
        problems.append(_spawn_problem("war_fatigue",
            "Three wars rage simultaneously — strategists must find a path to peace.",
            ["warrior", "spy", "philosopher", "priest"], world))

    if pop <= 4 and "population_collapse" not in existing_problem_types:
        problems.append(_spawn_problem("population_collapse",
            "The world is nearly empty — survivors must cooperate to rebuild.",
            list(set(a["type"] for a in alive)), world))

    if knowledge < 15 and "knowledge_loss" not in existing_problem_types:
        problems.append(_spawn_problem("knowledge_loss",
            "The accumulated knowledge of civilisation is fading.",
            ["scholar", "philosopher", "elder_council", "explorer"], world))

    world["distributed_problems"] = problems

    # ── WORK ON ACTIVE PROBLEMS ───────────────────────────────────────
    for problem in problems:
        if not problem.get("active"):
            continue

        problem["ticks_active"] = problem.get("ticks_active", 0) + 1

        # Assign contributors
        relevant = [a for a in alive
                    if a.get("type") in problem["required_types"]
                    and a.get("id") not in problem["contributors"]]
        for a in relevant[:3]:
            if _dist(a.get("position", [0,0]),
                     problem.get("epicenter", [0,0])) < COLLECTIVE_CONFIG["crisis_broadcast_radius"]:
                problem["contributors"].append(a["id"])
                _remember(a, "discovery",
                          "Working with others to solve: %s Y%d" % (
                              problem["desc"][:60], year), importance=3)

        # Progress toward solution (each contributor adds effort)
        effort = len(problem["contributors"]) * random.uniform(0.5, 2.0)
        problem["progress"] = min(100, problem.get("progress", 0) + effort)

        # Solution
        if problem["progress"] >= 100:
            problem["active"]    = False
            problem["solved_year"] = year
            problem["solved_by"]   = problem["contributors"][:5]

            world["collective_stats"]["problems_solved"] += 1
            world["stats"]["distributed_problems_solved"] = world["stats"].get("distributed_problems_solved", 0) + 1

            # Apply solution effects
            _apply_problem_solution(problem, alive, world)

            _log(world, "PROBLEM SOLVED: '%s' — %d contributors over %d ticks" % (
                problem["type"], len(problem["contributors"]), problem["ticks_active"]), "collective")
            _history(world, "A collective effort solved the %s crisis Y%d" % (
                problem["type"].replace("_", " "), year), 4)

        # Problem times out (world failed to solve it)
        elif problem["ticks_active"] > COLLECTIVE_CONFIG["problem_solve_ticks"]:
            problem["active"]    = False
            problem["failed"]    = True
            problem["failed_year"] = year

            _log(world, "PROBLEM UNSOLVED: '%s' timed out with %d contributors" % (
                problem["type"], len(problem["contributors"])), "collective")
            _history(world, "The %s crisis was not solved — consequences will follow Y%d" % (
                problem["type"].replace("_", " "), year), 3)


def _spawn_problem(ptype, desc, required_types, world):
    alive = [a for a in world.get("agents", []) if a.get("alive")]
    epicenter = alive[0]["position"] if alive else [0, 0]
    problem = {
        "id":             "prob_%d" % world.get("tick", 0),
        "type":           ptype,
        "desc":           desc,
        "required_types": required_types,
        "epicenter":      epicenter,
        "progress":       0.0,
        "contributors":   [],
        "ticks_active":   0,
        "active":         True,
        "formed_year":    world.get("year", 1),
    }
    _log(world, "CRISIS BROADCAST: '%s' — needs: %s" % (ptype, ", ".join(required_types)), "collective")
    _history(world, "A crisis emerges: %s Y%d" % (desc[:60], world.get("year", 1)), 3)
    return problem


def _apply_problem_solution(problem, alive, world):
    """Apply the real-world effects of solving a distributed problem."""
    contributors_set = set(problem["contributors"])
    solvers = [a for a in alive if a["id"] in contributors_set]

    if problem["type"] == "epidemic":
        world["plague_active"] = False
        for a in alive:
            a["disease"] = None
            a["health"]  = min(100, a.get("health", 100) + 20)
        for s in solvers:
            _remember(s, "joy",
                      "We cured the plague together. I will not forget what we built here.", importance=4)

    elif problem["type"] == "famine":
        world["resources"]["food"] = world["resources"].get("food", 0) + 80
        for s in solvers:
            _remember(s, "joy", "The famine is over — collective effort fed us all.", importance=3)

    elif problem["type"] == "war_fatigue":
        # Force peace in one war
        wars = world.get("active_wars", [])
        if wars:
            peace_war = wars.pop()
            try:
                from world_engine import set_diplo
                set_diplo(peace_war["attacker"], peace_war["defender"], "neutral")
            except ImportError:
                pass
            _history(world, "Collective effort ended the war between %s and %s" % (
                peace_war.get("attacker", "?"), peace_war.get("defender", "?")), 4)

    elif problem["type"] == "population_collapse":
        # Boost all survivors
        for a in alive:
            a["health"] = min(150, a.get("health", 100) + 30)
            a["max_age"] = a.get("max_age", 300) + 50

    elif problem["type"] == "knowledge_loss":
        world["resources"]["knowledge"] = world["resources"].get("knowledge", 0) + 60
        for s in solvers:
            s.setdefault("skills", []).append("preserved_knowledge")
            _remember(s, "discovery",
                      "We saved what could be saved. The library lives.", importance=4)

    # All solvers gain meta-cognitive insight
    for s in solvers:
        sm = s.get("self_model", {})
        sm["world_understanding"] = min(100, sm.get("world_understanding", 30) + 8)
        if "values" in s:
            s["values"]["connection"] = min(100, s["values"].get("connection", 50) + 5)


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# SYSTEM 5 — WORLD HEALTH MONITOR
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

def tick_world_health(world):
    """
    Compute world vital signs. Alert when outside healthy range.
    Feed into self-healing engine.
    """
    tick = world.get("tick", 0)
    if tick % COLLECTIVE_CONFIG["health_check_interval"] != 0:
        return

    wh    = world.setdefault("world_health", {})
    alive = [a for a in world["agents"] if a.get("alive")]
    res   = world.get("resources", {})
    factions_alive = set(a.get("faction") for a in alive)

    vitals = {}

    vitals["population"]        = len(alive)
    vitals["faction_diversity"] = len([f for f in factions_alive
                                       if sum(1 for a in alive if a.get("faction") == f) >= 1])
    vitals["knowledge_level"]   = res.get("knowledge", 0)
    vitals["faith_level"]       = res.get("faith", 0)
    vitals["conflict_balance"]  = len(world.get("active_wars", []))
    vitals["resource_balance"]  = sum(res.get(r, 0) for r in
                                      ["food", "gold", "wood", "stone", "iron"])
    neg_emotion_count = sum(1 for a in alive if a.get("emotion") in NEGATIVE_EMOTIONS)
    vitals["emotional_health"]  = (1 - neg_emotion_count / max(1, len(alive)))
    total_goals = sum(len([g for g in a.get("originated_goals", []) if g.get("active")])
                      for a in alive)
    vitals["active_goals"]      = total_goals

    wh["vitals"] = vitals

    # Compute overall health score
    scores = []
    alerts = []
    for vital, (vmin, vmax, weight) in VITAL_RANGES.items():
        v = vitals.get(vital, 0)
        if vmin <= v <= vmax:
            scores.append(1.0 * weight)
        elif v < vmin:
            frac = max(0.0, v / vmin) if vmin > 0 else 0.0
            scores.append(frac * weight)
            alerts.append({"vital": vital, "value": v, "threshold": vmin, "type": "too_low"})
        else:
            frac = max(0.0, vmax / v) if v > 0 else 1.0
            scores.append(frac * weight)
            alerts.append({"vital": vital, "value": v, "threshold": vmax, "type": "too_high"})

    total_weight = sum(w for _, (_, _, w) in VITAL_RANGES.items())
    wh["overall_score"]  = round(sum(scores) / total_weight, 3)
    wh["alerts"]         = alerts
    wh["last_check_tick"] = tick

    return wh


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# SYSTEM 6 — SELF-HEALING ENGINE
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

def tick_self_healing(world):
    """
    Respond to world health alerts with targeted interventions.
    The world fights to stay in a fertile, interesting state.
    """
    wh     = world.get("world_health", {})
    alerts = wh.get("alerts", [])
    alive  = [a for a in world["agents"] if a.get("alive")]
    year   = world.get("year", 1)

    for alert in alerts:
        vital = alert["vital"]
        atype = alert["type"]

        # ── POPULATION TOO LOW ────────────────────────────────────────
        if vital == "population" and atype == "too_low":
            # Spawn agents from weakest faction
            factions = world.get("FACTIONS", {})
            if not factions:
                try:
                    from world_engine import FACTIONS, spawn_agent
                    for _ in range(2):
                        faction = min(
                            factions,
                            key=lambda f: sum(1 for a in alive if a.get("faction") == f)
                        )
                        spawn_agent(faction)
                    world["collective_stats"]["self_heals"] = world["collective_stats"].get("self_heals", 0) + 1
                    _log(world, "SELF-HEAL: Population too low — spawned 2 agents", "eternal_loop")
                    wh.setdefault("interventions", []).append(
                        {"tick": world["tick"], "type": "population_boost", "year": year})
                except ImportError:
                    # Boost health of all alive
                    for a in alive:
                        a["health"] = min(150, a.get("health", 100) + 25)

        # ── KNOWLEDGE TOO LOW ─────────────────────────────────────────
        elif vital == "knowledge_level" and atype == "too_low":
            world["resources"]["knowledge"] = world["resources"].get("knowledge", 0) + 40
            for a in alive:
                if a.get("type") in ("scholar", "philosopher", "explorer"):
                    a["emotion"] = "curious"
            _log(world, "SELF-HEAL: Knowledge collapsed — injecting knowledge resources", "eternal_loop")
            wh.setdefault("interventions", []).append(
                {"tick": world["tick"], "type": "knowledge_injection", "year": year})

        # ── TOO MANY WARS ────────────────────────────────────────────
        elif vital == "conflict_balance" and atype == "too_high":
            wars = world.get("active_wars", [])
            if wars:
                resolved = wars[0]
                try:
                    from world_engine import set_diplo
                    set_diplo(resolved["attacker"], resolved["defender"], "neutral")
                except ImportError:
                    pass
                world["active_wars"] = wars[1:]
                _log(world, "SELF-HEAL: Too many wars — forcing ceasefire", "eternal_loop")
                _history(world, "Exhaustion forced a ceasefire between %s and %s Y%d" % (
                    resolved.get("attacker", "?"), resolved.get("defender", "?"), year), 3)

        # ── EMOTIONAL COLLAPSE ───────────────────────────────────────
        elif vital == "emotional_health" and atype == "too_low":
            # Trigger a positive event for a random agent
            if alive:
                healed = random.sample(alive, min(3, len(alive)))
                for a in healed:
                    a["emotion"] = random.choice(["curious", "inspired", "joyful"])
                    _remember(a, "joy",
                              "Something shifted — hope returned unexpectedly. Y%d" % year, importance=2)
            _log(world, "SELF-HEAL: Emotional collapse — injecting hope", "eternal_loop")

        # ── FACTION EXTINCTION ───────────────────────────────────────
        elif vital == "faction_diversity" and atype == "too_low":
            _log(world, "SELF-HEAL: Faction diversity collapsed — seeding defectors", "eternal_loop")
            # Encourage some agents to found a new identity
            for a in random.sample(alive, min(2, len(alive))):
                if "values" in a and a["values"].get("freedom", 0) > 55:
                    a["emotion"] = "inspired"
                    _remember(a, "discovery",
                              "With the old order gone, I see a chance to build something new. Y%d" % year,
                              importance=4)


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# SYSTEM 7 — STAGNATION DETECTION + UPHEAVAL
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

def tick_stagnation_upheaval(world):
    """
    If nothing noteworthy has happened, force an upheaval.
    Entropy has a cure.
    """
    el   = world.setdefault("eternal_loop", {})
    tick = world.get("tick", 0)
    year = world.get("year", 1)

    # Track major events from world history
    wh  = world.get("world_history", [])
    recent_major = [e for e in wh[-20:]
                    if e.get("importance", 0) >= 3
                    and e.get("tick", 0) > tick - COLLECTIVE_CONFIG["stagnation_threshold"]]

    if recent_major:
        el["stagnation_ticks"] = 0
        el["last_major_event_tick"] = tick
    else:
        el["stagnation_ticks"] = el.get("stagnation_ticks", 0) + 1

    # Stagnation check
    stagnant = el["stagnation_ticks"] >= COLLECTIVE_CONFIG["stagnation_threshold"]
    cooldown_ok = (tick - el.get("last_upheaval_tick", -9999)) >= COLLECTIVE_CONFIG["upheaval_cooldown"]

    if stagnant and cooldown_ok:
        _fire_upheaval(world, el, year, tick)


def _fire_upheaval(world, el, year, tick):
    """Select and execute an upheaval event."""
    fired_types = {u["type"] for u in el.get("upheavals_fired", [])}
    candidates  = [u for u in UPHEAVAL_TYPES if u["id"] not in fired_types]
    if not candidates:
        candidates = UPHEAVAL_TYPES  # allow repeats once all have fired

    upheaval = random.choice(candidates)

    el["last_upheaval_tick"]   = tick
    el["stagnation_ticks"]     = 0
    el.setdefault("upheavals_fired", []).append({
        "type": upheaval["id"], "year": year, "tick": tick
    })

    world["collective_stats"]["upheavals_fired"] = world["collective_stats"].get("upheavals_fired", 0) + 1
    world["stats"]["upheavals_fired"] = world["stats"].get("upheavals_fired", 0) + 1

    _log(world, "UPHEAVAL: %s — %s" % (upheaval["name"], upheaval["desc"][:60]), "eternal_loop")
    _history(world, "UPHEAVAL: %s — %s Y%d" % (upheaval["name"], upheaval["desc"][:60], year), 5)

    alive = [a for a in world["agents"] if a.get("alive")]

    # Execute effect
    effect = upheaval["effect"]

    if effect == "spawn_sage":
        # Create a new legendary philosopher agent
        if alive:
            agent = random.choice(alive)
            agent["type"]        = "philosopher"
            agent["is_legend"]   = True
            agent["emotion"]     = "inspired"
            agent["age"]         = max(agent.get("age", 0), 250)
            agent["max_age"]     = max(agent.get("max_age", 300), 500)
            sm = agent.get("self_model", {})
            sm["world_understanding"] = min(100, sm.get("world_understanding", 50) + 40)
            sm["self_label"] = "a wandering sage from beyond the world's edge"
            _remember(agent, "discovery",
                      "I have arrived from places no map includes. I carry knowledge no one here has seen. Y%d" % year,
                      importance=5)

    elif effect == "knowledge_surge":
        world["resources"]["knowledge"] = world["resources"].get("knowledge", 0) + 120
        for a in alive:
            if random.random() < 0.5:
                _remember(a, "discovery",
                          "Ancient texts were uncovered. Everything we thought we knew is incomplete. Y%d" % year,
                          importance=3)
                a["emotion"] = random.choice(["curious", "inspired"])

    elif effect == "belief_cascade":
        # Each faction interprets a sign differently
        for a in alive:
            interp_pool = [
                ("faith", "A divine sign confirmed what I believed. I am not alone. Y%d" % year),
                ("skepticism", "The 'divine sign' was just an unusual weather event. We need to stop using the sky as a mirror. Y%d" % year),
                ("fear", "Something is coming. The sign was a warning. I felt it. Y%d" % year),
                ("hope", "The sign meant renewal. Things will be different now. Y%d" % year),
            ]
            _, content = random.choice(interp_pool)
            _remember(a, "discovery", content, importance=3)
            a["emotion"] = random.choice(["inspired", "afraid", "devoted", "curious"])

    elif effect == "plague_surge":
        world["plague_active"] = True
        for a in alive:
            if random.random() < 0.4:
                a["disease"] = "upheaval_plague"
                a["health"]  = max(1, a.get("health", 100) - random.randint(10, 40))

    elif effect == "faction_schism":
        # Turn a neutral into tense
        try:
            from world_engine import FACTIONS, set_diplo, get_diplo
            flist = list(FACTIONS.keys())
            for i, fa in enumerate(flist):
                for fb in flist[i+1:]:
                    if get_diplo(fa, fb) == "neutral" and random.random() < 0.4:
                        set_diplo(fa, fb, "tense")
                        _history(world, "Tensions erupted between %s and %s Y%d" % (fa, fb, year), 3)
                        break
        except ImportError:
            pass

    elif effect == "forced_war":
        try:
            from world_engine import FACTIONS, set_diplo, get_diplo
            flist = list(FACTIONS.keys())
            for i, fa in enumerate(flist):
                for fb in flist[i+1:]:
                    if get_diplo(fa, fb) in ("neutral", "tense") and random.random() < 0.5:
                        set_diplo(fa, fb, "war")
                        world.setdefault("active_wars", []).append({
                            "attacker": fa, "defender": fb,
                            "start_year": year, "cause": "upheaval"
                        })
                        _history(world, "Old grievances erupted into war: %s vs %s Y%d" % (fa, fb, year), 4)
                        break
        except ImportError:
            pass

    elif effect == "prosperity_surge":
        for res in ["food", "gold", "wood", "stone"]:
            world["resources"][res] = world["resources"].get(res, 0) + 60
        for a in alive:
            a["health"]  = min(150, a.get("health", 100) + 20)
            a["emotion"] = random.choice(["joyful", "inspired", "content"])
        _history(world, "A golden age of abundance began. Even old wounds seemed lighter. Y%d" % year, 4)

    elif effect == "forced_migration":
        # Move all agents toward center of world
        for a in alive:
            push = [random.uniform(-5, 5), random.uniform(-5, 5)]
            a["position"] = [
                max(-40, min(40, a["position"][0] + push[0])),
                max(-40, min(40, a["position"][1] + push[1]))
            ]
            a["target"] = [random.uniform(-20, 20), random.uniform(-20, 20)]
            _remember(a, "trauma",
                      "The world shifted. I had to leave everything I knew. Y%d" % year, importance=4)


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# SYSTEM 8 — EPOCH TRANSITIONS
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

def tick_epoch_transitions(world):
    """
    Every 200 years, a new epoch begins.
    The world reinvents itself — new alliances, new dominant values, old
    institutions collapse, new ones form, all agents gain new memories
    of living through history.
    """
    el   = world.setdefault("eternal_loop", {})
    year = world.get("year", 1)

    epoch_length = COLLECTIVE_CONFIG["epoch_length_years"]
    epoch_num    = (year - 1) // epoch_length
    current      = el.get("current_epoch", 0)

    if epoch_num <= current:
        return

    # Epoch transition!
    old_epoch = el.get("epoch_name", EPOCH_NAMES[0])
    new_epoch = EPOCH_NAMES[epoch_num % len(EPOCH_NAMES)]

    el["current_epoch"]    = epoch_num
    el["epoch_name"]       = new_epoch
    el["epoch_start_year"] = year
    el["epochs_elapsed"]   = el.get("epochs_elapsed", 0) + 1

    alive = [a for a in world["agents"] if a.get("alive")]
    tick  = world.get("tick", 0)

    _log(world, "EPOCH TRANSITION: '%s' → '%s' — Year %d" % (old_epoch, new_epoch, year), "eternal_loop")
    _history(world, "THE AGE TURNED: '%s' ended. '%s' begins. Year %d." % (
        old_epoch, new_epoch, year), 5)

    world["collective_stats"]["epochs_completed"] = world["collective_stats"].get("epochs_completed", 0) + 1
    world["stats"]["epochs_completed"] = world["stats"].get("epochs_completed", 0) + 1

    # ── EPOCH EFFECTS ─────────────────────────────────────────────────

    # 1. All living agents gain an epoch memory
    for a in alive:
        _remember(a, "discovery",
                  "I lived through the end of %s and the beginning of %s. Y%d" % (
                      old_epoch, new_epoch, year),
                  importance=4)
        a["emotion"] = random.choice(["inspired", "weary", "curious", "afraid"])

    # 2. Oldest institutions collapse (they've become too rigid)
    for inst in world.get("institutions", []):
        if not inst.get("active"):
            continue
        inst_age = year - inst.get("created_year", year)
        if inst_age > epoch_length * 0.7 and random.random() < 0.4:
            inst["active"] = False
            inst["dissolved_year"] = year
            inst["dissolution_cause"] = "epoch_transition"
            _history(world, "The ancient %s '%s' dissolved at the epoch's end. Y%d" % (
                inst["type"].replace("_", " "), inst["name"], year), 3)

    # 3. New knowledge seeds for the new epoch
    kn = world.get("knowledge_network", {})
    if kn.get("nodes") is not None:
        # Plant 2-3 new epoch-specific concepts
        for category in random.sample(list(CONCEPT_SEEDS.keys()), 3):
            concept_text = random.choice(CONCEPT_SEEDS[category])
            cid = _concept_id(concept_text + "_epoch_%d" % epoch_num)
            carrier = random.choice(alive) if alive else None
            kn["nodes"][cid] = {
                "text":           "[%s] %s" % (new_epoch, concept_text),
                "category":       category,
                "origin_agent":   "the new epoch",
                "origin_year":    year,
                "carriers":       [carrier["id"]] if carrier else [],
                "links":          [],
                "mutation_count": 0,
                "tick_born":      tick,
                "last_spread_tick": tick,
                "epoch_seed":     True,
            }
            if carrier:
                carrier.setdefault("concepts", {})[cid] = {
                    "text": kn["nodes"][cid]["text"],
                    "learned_tick": tick,
                    "spread_count": 0,
                }

    # 4. Reset cultural movements (old movements don't outlast epochs easily)
    for mov in world.get("cultural_movements", []):
        if mov.get("active") and random.random() < 0.5:
            mov["active"]         = False
            mov["dissolved_year"] = year
            _log(world, "EPOCH: Movement '%s' dissolved at epoch's end" % mov["name"], "eternal_loop")

    # 5. Force value drift toward new epoch's dominant theme
    epoch_value_themes = {
        0: "survival",
        1: "power",
        2: "faith",
        3: "truth",
        4: "knowledge",
        5: "justice",
        6: "truth",
        7: "legacy",
        8: "justice",
        9: "compassion",
        10: "chaos",
        11: "transcendence",
    }
    theme = epoch_value_themes.get(epoch_num % len(epoch_value_themes), "survival")
    for a in alive:
        if "values" in a:
            current_v = a["values"].get(theme, 40)
            a["values"][theme] = min(100, current_v + random.uniform(3, 8))

    _history(world, "The %s is defined by the value of %s Y%d" % (
        new_epoch, theme.replace("_", " "), year), 3)


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# MASTER TICK
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

def tick_collective(world):
    """
    Master tick for all collective intelligence and eternal loop systems.
    
    Add to world_engine.tick() after tick_all_upgrades():
        from collective_loop import tick_collective
        tick_collective(world)
    
    Safe to call every tick.
    """
    try:
        tick_knowledge_propagation(world)
    except Exception:
        pass

    try:
        tick_institutional_minds(world)
    except Exception:
        pass

    try:
        tick_cultural_movements(world)
    except Exception:
        pass

    try:
        tick_distributed_problems(world)
    except Exception:
        pass

    try:
        tick_world_health(world)
    except Exception:
        pass

    try:
        tick_self_healing(world)
    except Exception:
        pass

    try:
        tick_stagnation_upheaval(world)
    except Exception:
        pass

    try:
        tick_epoch_transitions(world)
    except Exception:
        pass

    world.setdefault("eternal_loop", {})
    world["eternal_loop"]["loop_ticks"] = world["eternal_loop"].get("loop_ticks", 0) + 1


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# UTILITIES
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

def get_collective_snapshot(world) -> dict:
    """Full summary of collective intelligence state."""
    kn  = world.get("knowledge_network", {})
    el  = world.get("eternal_loop", {})
    wh  = world.get("world_health", {})
    cs  = world.get("collective_stats", {})

    alive = [a for a in world.get("agents", []) if a.get("alive")]
    concept_counts = {a["name"]: len(a.get("concepts", {})) for a in alive}
    top_carriers = sorted(concept_counts.items(), key=lambda x: -x[1])[:5]

    active_movements = [m for m in world.get("cultural_movements", []) if m.get("active")]
    active_problems  = [p for p in world.get("distributed_problems", []) if p.get("active")]

    return {
        "tick":              world.get("tick", 0),
        "year":              world.get("year", 1),
        "epoch":             el.get("epoch_name", "?"),
        "epoch_number":      el.get("current_epoch", 0),

        "knowledge_network": {
            "total_concepts":  len(kn.get("nodes", {})),
            "total_spread":    kn.get("total_spread_events", 0),
            "total_mutations": kn.get("total_mutations", 0),
            "concepts_lost":   kn.get("concepts_lost", 0),
            "top_carriers":    top_carriers,
        },

        "institutions": {
            "active": sum(1 for i in world.get("institutions", []) if i.get("active")),
            "with_collective_mind": sum(
                1 for i in world.get("institutions", [])
                if i.get("active") and "collective_mind" in i
            ),
        },

        "movements": {
            "active":   len(active_movements),
            "names":    [m["name"] for m in active_movements],
        },

        "distributed_problems": {
            "active":   len(active_problems),
            "types":    [p["type"] for p in active_problems],
        },

        "world_health": {
            "score":   wh.get("overall_score", 1.0),
            "alerts":  len(wh.get("alerts", [])),
            "vitals":  wh.get("vitals", {}),
        },

        "eternal_loop": {
            "upheavals":       len(el.get("upheavals_fired", [])),
            "stagnation_ticks": el.get("stagnation_ticks", 0),
            "epochs_elapsed":  el.get("epochs_elapsed", 0),
            "loop_ticks":      el.get("loop_ticks", 0),
        },

        "stats": cs,
    }


def get_agent_concepts_str(agent) -> str:
    """Return a readable summary of concepts an agent holds."""
    concepts = agent.get("concepts", {})
    if not concepts:
        return "(no concepts)"
    return " | ".join(
        '"%s"' % c["text"][:35]
        for c in list(concepts.values())[:4]
    )


def _concept_id(text):
    """Generate a stable ID from concept text."""
    return "c_" + str(hash(text[:40]) % 999999).replace("-", "n")


def _dist(a, b):
    return math.sqrt((a[0]-b[0])**2 + (a[1]-b[1])**2)


def _remember(agent, mtype, content, importance=1):
    try:
        from world_engine import remember
        remember(agent, mtype, content, importance)
    except ImportError:
        agent.setdefault("memories", []).append({
            "type": mtype, "content": content,
            "tick": 0, "year": 0, "season": "?",
            "importance": importance, "kg_indexed": True,
        })


def _log(world, msg, cat="collective"):
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
        entry = {"message": msg, "importance": importance,
                 "tick": world.get("tick", 0), "year": world.get("year", 1)}
        world.setdefault("world_history", []).append(entry)
