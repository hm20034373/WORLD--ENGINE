"""
╔══════════════════════════════════════════════════════════════════════╗
║        AGI WORLD ENGINE — LLM MIND v1.0                             ║
║        Phase 2: Claude-Powered Agent Reasoning                       ║
╠══════════════════════════════════════════════════════════════════════╣
║                                                                      ║
║  Replaces template-based cognition with real LLM reasoning.         ║
║  Each agent now has a genuine mind that:                             ║
║                                                                      ║
║  • REASONS     — thinks through situations in natural language       ║
║  • SPEAKS      — generates authentic dialogue when meeting others   ║
║  • DECIDES     — overrides BDI plan if reasoning says otherwise     ║
║  • TEACHES     — transfers knowledge via actual explanation          ║
║  • REFLECTS    — writes genuine lessons from experience             ║
║  • REMEMBERS   — summarises memories into compressed wisdom         ║
║                                                                      ║
║  Architecture:                                                       ║
║    LLMBudget  — token budget manager (keeps costs sane)             ║
║    LLMCache   — in-memory result cache (avoid repeat calls)         ║
║    AgentMind  — builds prompt context, calls API, parses response   ║
║    MindRouter — decides WHICH agents get LLM calls each tick        ║
║                                                                      ║
║  Integration:                                                        ║
║    from llm_mind import tick_llm_minds, init_llm_mind               ║
║    Call tick_llm_minds(world) from world_engine.tick()              ║
╚══════════════════════════════════════════════════════════════════════╝
"""

import json
import random
import math
import time
import hashlib
from datetime import datetime

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# CONFIGURATION
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

LLM_CONFIG = {
    # API
    "model":              "claude-sonnet-4-6",
    "max_tokens":         400,       # per agent response — keep tight
    "api_url":            "https://api.anthropic.com/v1/messages",

    # Budget — how many agents get LLM calls per tick
    "agents_per_tick":    3,         # max LLM-powered agents per tick
    "call_cooldown_ticks": 8,        # min ticks between LLM calls per agent
    "priority_cooldown":   4,        # priority agents get called more often

    # Priorities — which agents get LLM minds first
    "priority_types":     ["philosopher", "scholar", "priest", "legend"],
    "priority_emotions":  ["vengeful", "grieving", "inspired", "afraid"],

    # Features to enable
    "enable_reasoning":   True,      # inner monologue / decision reasoning
    "enable_dialogue":    True,      # natural language conversation
    "enable_teaching":    True,      # knowledge transfer explanations
    "enable_reflection":  True,      # deep post-event reflection
    "enable_memory_consolidation": True,  # compress old memories into wisdom

    # Cache
    "cache_ttl_ticks":    20,        # how long to cache LLM responses
    "cache_max_size":     200,       # max cached entries

    # Debug
    "log_prompts":        False,     # log full prompts (verbose)
    "log_responses":      True,      # log LLM responses
}

# Task types — what we ask the LLM to do
LLM_TASKS = {
    "reason":       "Think through your current situation and decide what to do.",
    "speak":        "Generate authentic dialogue for a conversation with another agent.",
    "teach":        "Explain a concept or skill to another agent in your own words.",
    "reflect":      "Write a deep reflection on a significant event you experienced.",
    "consolidate":  "Summarise your oldest memories into compressed wisdom.",
    "decide":       "Make a difficult decision with real stakes.",
    "react":        "React authentically to something surprising or shocking.",
}

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# LLM CACHE — avoid redundant calls for similar contexts
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

class LLMCache:
    def __init__(self, max_size=200, ttl_ticks=20):
        self._store    = {}   # hash → {response, tick_stored}
        self._max_size = max_size
        self._ttl      = ttl_ticks

    def _hash(self, prompt: str) -> str:
        return hashlib.md5(prompt.encode()).hexdigest()[:16]

    def get(self, prompt: str, current_tick: int):
        h = self._hash(prompt)
        entry = self._store.get(h)
        if entry and (current_tick - entry["tick"]) < self._ttl:
            return entry["response"]
        return None

    def set(self, prompt: str, response: str, current_tick: int):
        if len(self._store) >= self._max_size:
            # Evict oldest entry
            oldest = min(self._store, key=lambda k: self._store[k]["tick"])
            del self._store[oldest]
        self._store[self._hash(prompt)] = {"response": response, "tick": current_tick}

    def clear(self):
        self._store.clear()


# Global cache instance
_cache = LLMCache(
    max_size=LLM_CONFIG["cache_max_size"],
    ttl_ticks=LLM_CONFIG["cache_ttl_ticks"]
)


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# LLM BUDGET — per-tick call counter
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

class LLMBudget:
    def __init__(self):
        self.calls_this_tick = 0
        self.total_calls     = 0
        self.total_errors    = 0
        self.total_cached    = 0
        self.current_tick    = 0

    def reset_tick(self, tick: int):
        self.calls_this_tick = 0
        self.current_tick    = tick

    def can_call(self) -> bool:
        return self.calls_this_tick < LLM_CONFIG["agents_per_tick"]

    def record_call(self):
        self.calls_this_tick += 1
        self.total_calls     += 1

    def record_error(self):
        self.total_errors += 1

    def record_cache_hit(self):
        self.total_cached += 1

    def summary(self) -> dict:
        return {
            "total_calls":  self.total_calls,
            "total_errors": self.total_errors,
            "cache_hits":   self.total_cached,
            "current_tick": self.current_tick,
        }


_budget = LLMBudget()


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# LLM MIND INIT
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

def init_llm_mind(agent):
    """Attach LLM mind state to an agent. Safe to call multiple times."""
    if "llm_mind" in agent:
        return
    agent["llm_mind"] = {
        "last_call_tick":    -999,
        "last_task":         None,
        "last_response":     None,
        "call_count":        0,
        "error_count":       0,
        "wisdom":            [],      # compressed memory consolidations
        "llm_thoughts":      [],      # last 10 LLM-generated inner thoughts
        "llm_dialogues":     [],      # last 10 LLM-generated dialogue lines
        "llm_decisions":     [],      # last 10 LLM-generated decisions
        "llm_teachings":     [],      # teachings this agent has given
        "llm_reflections":   [],      # deep reflections
        "enabled":           True,    # can be disabled per-agent
    }


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# CONTEXT BUILDER — compress agent state into a rich prompt context
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

def build_agent_context(agent, world, task: str, extra: dict = None) -> str:
    """
    Build the complete context string for an agent's LLM prompt.
    Includes: identity, state, top memories, beliefs, goals, situation.
    """
    name    = agent["name"]
    atype   = agent["type"]
    faction = agent.get("faction", "?")
    age     = agent.get("age", 0)
    health  = agent.get("health", 100)
    emotion = agent.get("emotion", "content")
    year    = world.get("year", 1)
    season  = world.get("season", "spring")
    weather = world.get("weather", "clear")

    # ── MEMORIES (top 6 most important) ──────────────────────────────
    memories = sorted(
        agent.get("memories", []),
        key=lambda m: (m.get("importance", 1), m.get("tick", 0)),
        reverse=True
    )[:6]
    mem_lines = []
    for m in memories:
        mem_lines.append("  [%s] %s" % (m.get("type", "?"), m.get("content", "")))
    mem_str = "\n".join(mem_lines) if mem_lines else "  No significant memories yet."

    # ── BELIEFS (only strong or collapsed ones) ───────────────────────
    beliefs = agent.get("beliefs", {})
    belief_lines = []
    for bkey, bval in beliefs.items():
        conf = bval.get("confidence", 50)
        val  = bval.get("value", True)
        if conf > 70 or conf < 30 or val == False:
            label = bkey.replace("_", " ")
            status = "COLLAPSED" if val == False else ("strong" if conf > 70 else "shaken")
            belief_lines.append("  %s (%s, %d%%)" % (label, status, conf))
    belief_str = "\n".join(belief_lines) if belief_lines else "  No notable beliefs."

    # ── ACTIVE GOALS ──────────────────────────────────────────────────
    goals = [g for g in agent.get("originated_goals", []) if g.get("active")]
    goal_str = ", ".join(g["goal"] for g in goals) if goals else "None beyond survival."

    # ── SELF-MODEL ────────────────────────────────────────────────────
    sm = agent.get("self_model", {})
    self_label  = sm.get("self_label", "an agent")
    self_worth  = sm.get("self_worth", 50)
    world_under = sm.get("world_understanding", 30)
    id_stable   = sm.get("identity_stability", 70)

    # ── BDI STATE ─────────────────────────────────────────────────────
    bdi = agent.get("bdi", {})
    intention = bdi.get("current_intention", {})
    int_str   = intention.get("desire", "none") if intention else "none"
    desires   = bdi.get("desires", [])
    top_desires = ", ".join(d["desire"] for d in desires[:3]) if desires else "none"

    # ── SITUATION (what the agent can currently perceive) ─────────────
    percepts     = bdi.get("last_percepts", {})
    nearby_count = len(percepts.get("nearby_agents", []))
    enemy_count  = len(percepts.get("nearby_enemies", []))
    threat_count = len(percepts.get("threats", []))
    ally_count   = len(percepts.get("nearby_allies", []))
    nearby_names = [a["name"] for a in percepts.get("nearby_agents", [])[:3]]
    nearby_str   = ", ".join(nearby_names) if nearby_names else "nobody"

    # ── WORLD CONTEXT ─────────────────────────────────────────────────
    active_wars  = world.get("active_wars", [])
    war_str      = ", ".join(str(w) for w in active_wars[:2]) if active_wars else "none"
    faction_data = world.get("factions", {})

    # ── WISDOM (LLM-generated consolidated memories) ──────────────────
    llm_mind = agent.get("llm_mind") or {}
    wisdom   = llm_mind.get("wisdom", [])
    wisdom_str = (" | ".join(wisdom[-3:])) if wisdom else "None yet."

    # ── TASK-SPECIFIC EXTRA CONTEXT ───────────────────────────────────
    extra_str = ""
    if extra:
        if "other_agent" in extra:
            oa = extra["other_agent"]
            extra_str = "\nThe agent you are interacting with: %s (%s of %s), age %d, feeling %s." % (
                oa.get("name","?"), oa.get("type","?"), oa.get("faction","?"),
                oa.get("age",0), oa.get("emotion","content"))
        if "event" in extra:
            extra_str += "\nThe event you are reacting to: %s" % extra["event"]
        if "teach_topic" in extra:
            extra_str += "\nThe topic you are teaching: %s" % extra["teach_topic"]
        if "decision_stakes" in extra:
            extra_str += "\nThe decision you face: %s" % extra["decision_stakes"]

    context = """You are {name}, a {age}-year-old {type} of the {faction} faction.
You see yourself as {self_label}. Your self-worth is {self_worth}/100. 
Your understanding of the world is {world_under}/100. Identity stability: {id_stable}/100.

CURRENT STATE:
  Health: {health}/100 | Emotion: {emotion}
  Year {year}, {season}, {weather}
  Nearby: {nearby_str} ({nearby_count} agents, {ally_count} allies, {enemy_count} enemies)
  Active threats: {threat_count}
  Active wars: {war_str}

YOUR MOST IMPORTANT MEMORIES:
{mem_str}

YOUR BELIEFS:
{belief_str}

YOUR ACTIVE GOALS: {goal_str}

YOUR CONSOLIDATED WISDOM: {wisdom_str}

BDI COGNITIVE STATE:
  Current intention: {int_str}
  Top desires: {top_desires}
{extra_str}

TASK: {task}""".format(
        name=name, age=age, type=atype, faction=faction,
        self_label=self_label, self_worth=self_worth,
        world_under=world_under, id_stable=id_stable,
        health=health, emotion=emotion,
        year=year, season=season, weather=weather,
        nearby_str=nearby_str, nearby_count=nearby_count,
        ally_count=ally_count, enemy_count=enemy_count,
        threat_count=threat_count, war_str=war_str,
        mem_str=mem_str, belief_str=belief_str,
        goal_str=goal_str, wisdom_str=wisdom_str,
        int_str=int_str, top_desires=top_desires,
        extra_str=extra_str,
        task=LLM_TASKS.get(task, task),
    )

    return context


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# SYSTEM PROMPTS — persona + output format per task type
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

def build_system_prompt(task: str, agent_type: str) -> str:
    """Build a task-specific system prompt that shapes the LLM's output."""

    base = """You are roleplaying as a character in a living fantasy world simulation.
You must respond as this character — in their voice, with their knowledge, fears, and personality.
Never break character. Never mention AI, simulation, or the real world.
Your character only knows what they have experienced in this world."""

    task_instructions = {
        "reason": """
Respond with a short inner monologue (2-4 sentences). 
This is the character's PRIVATE thought — raw, honest, first-person.
Show genuine reasoning about what to do next. No formatting. Just thought.
Example: "Three enemies to the east. Mira is already wounded. I cannot protect her if I fight alone. I need to pull back and regroup."
""",
        "speak": """
Respond with ONE line of dialogue this character would say to another agent.
It must sound like this specific character — their age, role, and emotional state should come through.
NO quotation marks, NO stage directions, NO formatting.
Just the single line of speech.
Example: You carry the smell of Ironveil on you. I'll hear what you have to say, but I won't turn my back.
""",
        "teach": """
Respond with 2-3 sentences of actual teaching — the character explaining something they know.
It should reflect their personality and expertise. Sound like a real person who learned this the hard way.
No formatting. Just the teaching, as spoken aloud.
""",
        "reflect": """
Respond with a genuine 3-5 sentence reflection from the character.
This is written in their private journal or spoken to themselves.
It must grapple with a real tension — what they hoped, what happened, what it means.
No formatting.
""",
        "consolidate": """
Respond with JSON only. No prose. No backticks.
Format: {"wisdom": "A single sentence of compressed wisdom this character has derived from their life."}
The wisdom must be personal, specific to this character's experiences, and speak in first person.
Example: {"wisdom": "Every alliance I have made has broken when tested by war — trust must be earned through shared suffering, not shared comfort."}
""",
        "decide": """
Respond with JSON only. No prose. No backticks.
Format: {"decision": "what they choose to do", "reasoning": "1-2 sentences of why", "emotion": "how they feel about it"}
The decision must be concrete and consistent with the character's personality and beliefs.
""",
        "react": """
Respond with 1-2 sentences of raw reaction — the character's immediate, unfiltered response to something shocking.
This is visceral, emotional, and in character. No formatting.
""",
    }

    type_voices = {
        "warrior":      "You speak bluntly, think in terms of strength and survival, and trust actions over words.",
        "scholar":      "You think analytically, speak precisely, and find meaning in patterns and knowledge.",
        "merchant":     "You think in terms of value, relationships, and opportunity. Pragmatic above all.",
        "priest":       "You speak with quiet conviction, frame everything through faith, and seek divine meaning.",
        "spy":          "You are guarded, speak indirectly, observe more than you reveal.",
        "healer":       "You are practical about suffering, compassionate without sentimentality.",
        "explorer":     "You think in terms of horizons, possibilities, and what lies beyond the known.",
        "farmer":       "You are grounded, patient, speak simply and honestly about hard truths.",
        "assassin":     "You are cold, precise, speak rarely and deliberately.",
        "builder":      "You think in structures, foundations, long-term consequences.",
        "philosopher":  "You reason carefully, question everything, speak in insights and paradoxes.",
        "crime_lord":   "You see power and leverage in everything. Direct, shrewd, occasionally menacing.",
        "plague_doctor":"You are methodical, unsentimental about death, find beauty in biological systems.",
        "patriarch":    "You carry the weight of family and legacy. Protective, authoritative, warm.",
        "matriarch":    "You hold communities together. Wise, firm, deeply attuned to people's needs.",
    }

    voice = type_voices.get(agent_type, "You speak honestly and directly.")
    instruction = task_instructions.get(task, "\nRespond briefly and in character.")

    return base + "\n\nYOUR VOICE: " + voice + "\n" + instruction


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# CORE LLM CALL
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

async def call_llm_async(system_prompt: str, user_prompt: str, tick: int) -> str:
    """
    Async LLM call using the Anthropic API.
    Returns the text response or an error string.
    
    NOTE: This is designed to be called from a JavaScript/browser context
    via the artifact API bridge, OR from Python using the anthropic SDK.
    
    For direct Python use, install: pip install anthropic
    For browser artifact use: calls go through window fetch to the API.
    """
    import urllib.request
    import urllib.error

    # Check cache first
    cache_key = system_prompt[:100] + user_prompt[:200]
    cached = _cache.get(cache_key, tick)
    if cached:
        _budget.record_cache_hit()
        return cached

    payload = json.dumps({
        "model":      LLM_CONFIG["model"],
        "max_tokens": LLM_CONFIG["max_tokens"],
        "system":     system_prompt,
        "messages":   [{"role": "user", "content": user_prompt}],
    }).encode("utf-8")

    import os
    _api_key = os.environ.get("ANTHROPIC_API_KEY", "")
    if not _api_key:
        _budget.record_error()
        return None

    req = urllib.request.Request(
        LLM_CONFIG["api_url"],
        data=payload,
        headers={
            "Content-Type": "application/json",
            "x-api-key": _api_key,
            "anthropic-version": "2023-06-01",
        },
        method="POST"
    )

    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            text = data["content"][0]["text"].strip()
            _cache.set(cache_key, text, tick)
            _budget.record_call()
            return text
    except Exception as e:
        _budget.record_error()
        return None


def call_llm_sync(system_prompt: str, user_prompt: str, tick: int) -> str:
    """
    Synchronous wrapper. Uses the anthropic SDK if available,
    falls back to urllib. Returns None on failure.
    """
    # Check cache
    cache_key = system_prompt[:100] + user_prompt[:200]
    cached = _cache.get(cache_key, tick)
    if cached:
        _budget.record_cache_hit()
        return cached

    try:
        import anthropic
        client = anthropic.Anthropic()
        message = client.messages.create(
            model=LLM_CONFIG["model"],
            max_tokens=LLM_CONFIG["max_tokens"],
            system=system_prompt,
            messages=[{"role": "user", "content": user_prompt}],
        )
        text = message.content[0].text.strip()
        _cache.set(cache_key, text, tick)
        _budget.record_call()
        return text
    except ImportError:
        pass  # anthropic not installed, try urllib
    except Exception as e:
        _budget.record_error()
        return None

    # urllib fallback (no API key — returns None in most cases)
    return None


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# TASK EXECUTORS — one function per LLM task type
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

def task_reason(agent, world) -> str:
    """
    Agent reasons through their current situation.
    Output → agent["thought"] (replaces template-based thought)
    """
    system = build_system_prompt("reason", agent["type"])
    context = build_agent_context(agent, world, "reason")

    response = call_llm_sync(system, context, world["tick"])
    if not response:
        return None

    # Store as thought
    agent["thought"] = response
    lm = agent["llm_mind"]
    lm["llm_thoughts"].append({"tick": world["tick"], "thought": response})
    if len(lm["llm_thoughts"]) > 10:
        lm["llm_thoughts"] = lm["llm_thoughts"][-10:]

    _log_llm_event(agent, world, "THOUGHT", response[:80])
    return response


def task_speak(agent, world, other_agent=None) -> str:
    """
    Agent generates authentic dialogue.
    Output → stored in world["conversations"] and agent memory.
    """
    system  = build_system_prompt("speak", agent["type"])
    context = build_agent_context(agent, world, "speak",
                                  extra={"other_agent": other_agent} if other_agent else None)

    response = call_llm_sync(system, context, world["tick"])
    if not response:
        return None

    # Clean up response (remove any accidental quotes)
    speech = response.strip('"').strip("'").strip()

    # Store dialogue
    lm = agent["llm_mind"]
    lm["llm_dialogues"].append({
        "tick":    world["tick"],
        "year":    world.get("year", 1),
        "to":      other_agent["name"] if other_agent else "the air",
        "speech":  speech,
    })
    if len(lm["llm_dialogues"]) > 10:
        lm["llm_dialogues"] = lm["llm_dialogues"][-10:]

    # Add to world conversations
    conv = {
        "tick":       world["tick"],
        "year":       world.get("year", 1),
        "speaker_a":  agent["name"],
        "speaker_b":  other_agent["name"] if other_agent else "?",
        "type_a":     agent["type"],
        "type_b":     other_agent["type"] if other_agent else "?",
        "faction_a":  agent.get("faction", "?"),
        "faction_b":  other_agent.get("faction", "?") if other_agent else "?",
        "message":    "%s: \"%s\"" % (agent["name"], speech),
        "llm_generated": True,
    }
    world.setdefault("conversations", []).append(conv)
    if len(world["conversations"]) > 60:
        world["conversations"] = world["conversations"][-60:]

    # Memory for both agents
    _add_memory(agent, "person",
                "Said to %s: \"%s\" Y%d" % (
                    other_agent["name"] if other_agent else "someone",
                    speech[:60], world.get("year",1)),
                importance=2)

    if other_agent:
        _add_memory(other_agent, "person",
                    "%s said to me: \"%s\" Y%d" % (
                        agent["name"], speech[:60], world.get("year",1)),
                    importance=2)

    _log_llm_event(agent, world, "SPEECH",
                   '"%s" → %s' % (speech[:60], other_agent["name"] if other_agent else "?"))
    return speech


def task_teach(agent, world, student=None, topic=None) -> str:
    """
    Agent teaches another agent something they know.
    Transfers knowledge + skill points to student.
    """
    if not topic:
        # Pick a topic from agent's memories/skills
        skills = agent.get("skills", [])
        memories = agent.get("memories", [])
        discoveries = [m for m in memories if m["type"] == "discovery"]
        if skills:
            topic = random.choice(skills)
        elif discoveries:
            topic = discoveries[-1]["content"][:50]
        else:
            topic = "survival in this world"

    system  = build_system_prompt("teach", agent["type"])
    context = build_agent_context(agent, world, "teach",
                                  extra={
                                      "other_agent": student,
                                      "teach_topic": topic,
                                  })

    response = call_llm_sync(system, context, world["tick"])
    if not response:
        return None

    # Store teaching
    lm = agent["llm_mind"]
    lm["llm_teachings"].append({
        "tick":    world["tick"],
        "year":    world.get("year", 1),
        "student": student["name"] if student else "no one",
        "topic":   topic,
        "content": response,
    })

    # Teaching gives student a knowledge boost and memory
    if student:
        _add_memory(student, "discovery",
                    "Taught by %s (%s): \"%s\" Y%d" % (
                        agent["name"], agent["type"], response[:80],
                        world.get("year", 1)),
                    importance=4)

        # Small knowledge boost to student's world understanding
        sm = student.get("self_model", {})
        sm["world_understanding"] = min(100, sm.get("world_understanding", 30) + 5)

        # Chance to give student a new skill
        if random.random() < 0.3:
            topic_clean = topic.replace(" ", "_")[:20]
            skills = student.setdefault("skills", [])
            if topic_clean not in skills:
                skills.append(topic_clean)
                _log_llm_event(student, world, "SKILL_LEARNED",
                               "Learned '%s' from %s" % (topic_clean, agent["name"]))

    # Teaching also reinforces teacher's identity and self-worth
    sm_teacher = agent.get("self_model", {})
    sm_teacher["self_worth"] = min(100, sm_teacher.get("self_worth", 50) + 3)

    _log_llm_event(agent, world, "TEACHING",
                   "Taught '%s' to %s" % (topic[:40], student["name"] if student else "no one"))
    return response


def task_reflect(agent, world, event=None) -> str:
    """
    Agent writes a deep reflection on a significant event.
    Output → high-importance memory + potential belief change.
    """
    if not event:
        # Find the most significant recent memory
        memories = sorted(agent.get("memories", []),
                          key=lambda m: m.get("importance", 1), reverse=True)
        if memories:
            event = memories[0]["content"]
        else:
            event = "the passage of time and what I have become"

    system  = build_system_prompt("reflect", agent["type"])
    context = build_agent_context(agent, world, "reflect",
                                  extra={"event": event})

    response = call_llm_sync(system, context, world["tick"])
    if not response:
        return None

    # Store reflection
    lm = agent["llm_mind"]
    lm["llm_reflections"].append({
        "tick":    world["tick"],
        "year":    world.get("year", 1),
        "event":   event[:60],
        "content": response,
    })
    if len(lm["llm_reflections"]) > 10:
        lm["llm_reflections"] = lm["llm_reflections"][-10:]

    # High-importance memory
    _add_memory(agent, "discovery",
                "REFLECTION: %s Y%d" % (response[:100], world.get("year", 1)),
                importance=5)

    # Reflection can shift emotion
    if "regret" in response.lower() or "failed" in response.lower():
        agent["emotion"] = "grieving"
    elif "proud" in response.lower() or "achieved" in response.lower():
        agent["emotion"] = "proud"
    elif "understand" in response.lower() or "realise" in response.lower():
        agent["emotion"] = "inspired"

    # Reflection boosts world understanding
    sm = agent.get("self_model", {})
    sm["world_understanding"] = min(100, sm.get("world_understanding", 30) + 4)

    _log_llm_event(agent, world, "REFLECTION", response[:80])
    return response


def task_consolidate(agent, world) -> str:
    """
    Agent compresses old memories into a single wisdom statement.
    Old memories are pruned; wisdom is preserved in llm_mind.
    """
    memories = agent.get("memories", [])
    if len(memories) < 10:
        return None  # not enough to consolidate

    system  = build_system_prompt("consolidate", agent["type"])
    context = build_agent_context(agent, world, "consolidate")

    response = call_llm_sync(system, context, world["tick"])
    if not response:
        return None

    # Parse JSON response
    try:
        clean = response.replace("```json", "").replace("```", "").strip()
        data  = json.loads(clean)
        wisdom = data.get("wisdom", "")
    except Exception:
        # If JSON parse fails, use raw response
        wisdom = response[:150]

    if not wisdom:
        return None

    # Store wisdom
    lm = agent["llm_mind"]
    lm["wisdom"].append(wisdom)
    if len(lm["wisdom"]) > 5:
        lm["wisdom"] = lm["wisdom"][-5:]

    # Prune oldest low-importance memories (keep top memories)
    old_memories = sorted(memories, key=lambda m: (m.get("importance", 1), m.get("tick", 0)))
    to_prune = old_memories[:5]  # prune 5 oldest/least important
    for m in to_prune:
        if m in agent["memories"]:
            agent["memories"].remove(m)

    # Add wisdom as a special memory
    _add_memory(agent, "discovery",
                "WISDOM: %s Y%d" % (wisdom[:80], world.get("year", 1)),
                importance=5)

    _log_llm_event(agent, world, "WISDOM", wisdom[:80])
    return wisdom


def task_decide(agent, world, stakes: str = None) -> dict:
    """
    Agent makes a difficult decision. Returns structured decision dict.
    Can override BDI intention if decision conflicts with current plan.
    """
    if not stakes:
        # Find a situation that requires a decision
        bdi = agent.get("bdi", {})
        desires = bdi.get("desires", [])
        if len(desires) >= 2 and desires[0]["urgency"] == desires[1]["urgency"]:
            stakes = "I am torn between '%s' and '%s' — both feel equally urgent." % (
                desires[0]["desire"], desires[1]["desire"])
        else:
            threats = bdi.get("last_percepts", {}).get("threats", [])
            if threats:
                stakes = "I face a threat from %s. Do I fight, flee, or find another way?" % threats[0]["source"]
            else:
                stakes = "I must choose what to do next with the time I have."

    system  = build_system_prompt("decide", agent["type"])
    context = build_agent_context(agent, world, "decide",
                                  extra={"decision_stakes": stakes})

    response = call_llm_sync(system, context, world["tick"])
    if not response:
        return None

    try:
        clean = response.replace("```json", "").replace("```", "").strip()
        data  = json.loads(clean)
    except Exception:
        data = {"decision": response[:80], "reasoning": "", "emotion": agent.get("emotion", "content")}

    # Store decision
    lm = agent["llm_mind"]
    record = {
        "tick":      world["tick"],
        "year":      world.get("year", 1),
        "stakes":    stakes,
        "decision":  data.get("decision", ""),
        "reasoning": data.get("reasoning", ""),
        "emotion":   data.get("emotion", ""),
    }
    lm["llm_decisions"].append(record)
    if len(lm["llm_decisions"]) > 10:
        lm["llm_decisions"] = lm["llm_decisions"][-10:]

    # Emotion override if decision carries strong feeling
    new_emotion = data.get("emotion", "")
    if new_emotion and new_emotion in _valid_emotions():
        agent["emotion"] = new_emotion

    # Store as memory
    _add_memory(agent, "discovery",
                "DECISION: %s — %s Y%d" % (
                    data.get("decision","?")[:60],
                    data.get("reasoning","")[:40],
                    world.get("year",1)),
                importance=4)

    _log_llm_event(agent, world, "DECISION",
                   "%s → %s" % (stakes[:40], data.get("decision","?")[:40]))
    return data


def task_react(agent, world, event: str) -> str:
    """
    Agent reacts to a sudden event (death of ally, unexpected betrayal, miracle).
    Raw emotional reaction, stored as memory.
    """
    system  = build_system_prompt("react", agent["type"])
    context = build_agent_context(agent, world, "react",
                                  extra={"event": event})

    response = call_llm_sync(system, context, world["tick"])
    if not response:
        return None

    agent["thought"] = response

    _add_memory(agent, "trauma" if "death" in event.lower() or "war" in event.lower() else "discovery",
                "REACTION: %s Y%d" % (response[:80], world.get("year",1)),
                importance=4)

    _log_llm_event(agent, world, "REACTION", response[:80])
    return response


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# MIND ROUTER — decides which agents get LLM calls this tick
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

def route_llm_tasks(world) -> list:
    """
    Select which agents get LLM calls this tick and what task to run.
    Returns list of (agent, task, extra_kwargs) tuples.

    Priority order:
    1. Agents with urgent emotional states
    2. High-value types (philosopher, scholar, legend)
    3. Agents about to converse with someone
    4. Agents who haven't been called in a long time
    """
    alive  = [a for a in world["agents"] if a["alive"]]
    tick   = world["tick"]
    budget = LLM_CONFIG["agents_per_tick"]
    tasks  = []

    # Ensure all alive agents have llm_mind
    for a in alive:
        if "llm_mind" not in a:
            init_llm_mind(a)

    def cooldown_ok(agent, min_ticks=None):
        lm = agent.get("llm_mind") or {}
        last = lm.get("last_call_tick", -999)
        min_cd = min_ticks or LLM_CONFIG["call_cooldown_ticks"]
        return (tick - last) >= min_cd

    def is_priority(agent):
        atype   = agent.get("type", "")
        emotion = agent.get("emotion", "")
        return (atype in LLM_CONFIG["priority_types"] or
                emotion in LLM_CONFIG["priority_emotions"] or
                agent.get("is_legend", False))

    # ── PASS 1: URGENT REACTIONS ──────────────────────────────────────
    # Agents who just experienced something significant
    for agent in alive:
        if len(tasks) >= budget:
            break
        if not cooldown_ok(agent, 2):
            continue
        memories = agent.get("memories", [])
        recent_high = [m for m in memories[-3:] if m.get("importance", 1) >= 5]
        if recent_high:
            event = recent_high[-1]["content"]
            tasks.append((agent, "react", {"event": event}))

    # ── PASS 2: PRIORITY AGENTS — REASON ─────────────────────────────
    priority_agents = [a for a in alive if is_priority(a) and cooldown_ok(a)]
    random.shuffle(priority_agents)
    for agent in priority_agents:
        if len(tasks) >= budget:
            break
        if any(t[0]["id"] == agent["id"] for t in tasks):
            continue
        tasks.append((agent, "reason", {}))

    # ── PASS 3: CONVERSATIONS ─────────────────────────────────────────
    if LLM_CONFIG["enable_dialogue"]:
        for agent in alive:
            if len(tasks) >= budget:
                break
            if any(t[0]["id"] == agent["id"] for t in tasks):
                continue
            if not cooldown_ok(agent):
                continue
            # Check if agent has a nearby ally to talk to
            bdi = agent.get("bdi", {})
            percepts = bdi.get("last_percepts", {})
            nearby_allies = percepts.get("nearby_allies", [])
            if nearby_allies and random.random() < 0.3:
                other = random.choice(nearby_allies)
                # Resolve other agent dict from world
                other_full = next((a for a in alive if a["id"] == other["id"]), None)
                if other_full:
                    tasks.append((agent, "speak", {"other_agent": other_full}))

    # ── PASS 4: TEACHING ─────────────────────────────────────────────
    if LLM_CONFIG["enable_teaching"]:
        for agent in alive:
            if len(tasks) >= budget:
                break
            if any(t[0]["id"] == agent["id"] for t in tasks):
                continue
            if not cooldown_ok(agent):
                continue
            # Scholars/philosophers with high world_understanding teach
            sm  = agent.get("self_model", {})
            age = agent.get("age", 0)
            if (agent["type"] in ("scholar", "philosopher", "healer", "priest") and
                sm.get("world_understanding", 0) > 60 and age > 100):
                bdi = agent.get("bdi", {})
                percepts = bdi.get("last_percepts", {})
                nearby = percepts.get("nearby_agents", [])
                young  = [a for a in alive
                          if a["age"] < 80 and a["id"] != agent["id"]
                          and any(n["id"] == a["id"] for n in nearby)]
                if young and random.random() < 0.2:
                    student = random.choice(young)
                    tasks.append((agent, "teach", {"student": student}))

    # ── PASS 5: MEMORY CONSOLIDATION ─────────────────────────────────
    if LLM_CONFIG["enable_memory_consolidation"]:
        for agent in alive:
            if len(tasks) >= budget:
                break
            if any(t[0]["id"] == agent["id"] for t in tasks):
                continue
            if not cooldown_ok(agent, 30):
                continue
            memories = agent.get("memories", [])
            if len(memories) > 25:
                tasks.append((agent, "consolidate", {}))

    # ── PASS 6: DEEP REFLECTION ───────────────────────────────────────
    if LLM_CONFIG["enable_reflection"]:
        for agent in alive:
            if len(tasks) >= budget:
                break
            if any(t[0]["id"] == agent["id"] for t in tasks):
                continue
            if not cooldown_ok(agent, 20):
                continue
            if agent.get("emotion") in ("grieving", "inspired", "vengeful", "proud"):
                tasks.append((agent, "reflect", {}))

    # ── PASS 7: FILL WITH GENERAL REASONING ──────────────────────────
    if LLM_CONFIG["enable_reasoning"]:
        remaining = [a for a in alive
                     if cooldown_ok(a) and not any(t[0]["id"] == a["id"] for t in tasks)]
        random.shuffle(remaining)
        for agent in remaining:
            if len(tasks) >= budget:
                break
            tasks.append((agent, "reason", {}))

    return tasks[:budget]


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# MASTER TICK FUNCTION
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

# ── BACKGROUND THREAD POOL ────────────────────────────────────────
# LLM calls are ~1-3 s each. Running them synchronously would stall the
# world tick. Instead we fire them on a background thread pool and write
# results back to the agent dict when they complete — the engine never
# waits for a Claude response.
import threading as _threading
_llm_executor_lock = _threading.Lock()
_pending_results: list = []          # completed results waiting to be flushed

def _run_task_bg(agent_snapshot, task_name, kwargs, tick, result_list, lock):
    """Execute one LLM task in a background thread."""
    try:
        # We pass a *copy* of the agent's context keys so the thread
        # doesn't hold a live reference to the mutable agent dict.
        result = _execute_task(agent_snapshot, task_name,
                               agent_snapshot.get("_world_ref"), kwargs)
        with lock:
            result_list.append({
                "agent_id":  agent_snapshot["id"],
                "agent_name": agent_snapshot["name"],
                "task":      task_name,
                "result":    result,
                "tick":      tick,
                "ok":        result is not None,
            })
    except Exception as e:
        with lock:
            result_list.append({
                "agent_id": agent_snapshot["id"],
                "task": task_name, "result": None,
                "tick": tick, "ok": False, "error": str(e),
            })


def tick_llm_minds(world):
    """
    Fire LLM tasks for selected agents on background threads.
    Never blocks the main tick loop — results are flushed the following tick.

    Call from world_engine.tick() after tick_cognitive_loops():
        from llm_mind import tick_llm_minds
        tick_llm_minds(world)
    """
    global _pending_results
    tick = world["tick"]
    _budget.reset_tick(tick)

    # ── 1. FLUSH RESULTS FROM PREVIOUS TICKS ─────────────────────
    flushed = 0
    with _llm_executor_lock:
        done, _pending_results = list(_pending_results), []

    agents_by_id = {a["id"]: a for a in world.get("agents", []) if a.get("alive")}
    for r in done:
        agent = agents_by_id.get(r["agent_id"])
        if agent and r["ok"] and r["result"] is not None:
            lm = agent.setdefault("llm_mind", {})
            lm["last_call_tick"] = r["tick"]
            lm["last_task"]      = r["task"]
            lm["last_response"]  = str(r["result"])[:200]
            lm["call_count"]     = lm.get("call_count", 0) + 1
            flushed += 1

    world["stats"]["llm_calls_total"] = world["stats"].get("llm_calls_total", 0) + flushed

    # ── 2. SCHEDULE NEW TASKS FOR THIS TICK ──────────────────────
    tasks = route_llm_tasks(world)
    fired = 0
    for agent, task_name, kwargs in tasks:
        # Give the snapshot a weak reference to world for context building
        snapshot = dict(agent)          # shallow copy — safe for reading
        snapshot["_world_ref"] = world  # thread reads world but never writes it
        t = _threading.Thread(
            target=_run_task_bg,
            args=(snapshot, task_name, kwargs, tick, _pending_results, _llm_executor_lock),
            daemon=True,
        )
        t.start()
        fired += 1

    world["stats"]["llm_budget"] = _budget.summary()
    return {"fired": fired, "flushed": flushed}


def _execute_task(agent, task_name, world, kwargs):
    """Dispatch a task to the right executor function."""
    if task_name == "reason":
        return task_reason(agent, world)
    elif task_name == "speak":
        other = kwargs.get("other_agent")
        return task_speak(agent, world, other_agent=other)
    elif task_name == "teach":
        student = kwargs.get("student")
        topic   = kwargs.get("topic")
        return task_teach(agent, world, student=student, topic=topic)
    elif task_name == "reflect":
        event = kwargs.get("event")
        return task_reflect(agent, world, event=event)
    elif task_name == "consolidate":
        return task_consolidate(agent, world)
    elif task_name == "decide":
        stakes = kwargs.get("decision_stakes")
        return task_decide(agent, world, stakes=stakes)
    elif task_name == "react":
        event = kwargs.get("event", "something unexpected happened")
        return task_react(agent, world, event=event)
    return None


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# UTILITIES
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

def _add_memory(agent, mtype, content, importance=1):
    """Add a memory to an agent (safe wrapper)."""
    try:
        from world_engine import remember
        remember(agent, mtype, content, importance)
    except ImportError:
        agent.setdefault("memories", []).append({
            "type": mtype, "content": content,
            "tick": 0, "year": 0, "season": "?",
            "importance": importance,
        })


def _log_llm_event(agent, world, event_type, detail):
    """Log an LLM event to world log."""
    try:
        from world_engine import log, history
        msg = "LLM[%s] %s (%s): %s" % (event_type, agent["name"], agent["type"], detail)
        log(msg, "llm_mind")
        if event_type in ("WISDOM", "REFLECTION", "TEACHING"):
            history(msg, importance=3)
    except ImportError:
        print("[LLM %s] %s (%s): %s" % (event_type, agent["name"], agent["type"], detail))


def _valid_emotions():
    return ["content","curious","grieving","angry","inspired","afraid",
            "lonely","joyful","weary","vengeful","devoted","proud"]


def get_llm_mind_summary(agent) -> dict:
    """Return a readable summary of an agent's LLM mind state."""
    lm = agent.get("llm_mind", {})
    if not lm:
        return {"status": "not initialised"}
    return {
        "name":          agent["name"],
        "type":          agent["type"],
        "call_count":    lm.get("call_count", 0),
        "last_task":     lm.get("last_task", "none"),
        "last_thought":  lm.get("llm_thoughts", [{}])[-1].get("thought", "...") if lm.get("llm_thoughts") else "...",
        "last_speech":   lm.get("llm_dialogues", [{}])[-1].get("speech", "...") if lm.get("llm_dialogues") else "...",
        "wisdom_count":  len(lm.get("wisdom", [])),
        "wisdom":        lm.get("wisdom", []),
        "reflections":   len(lm.get("llm_reflections", [])),
        "teachings":     len(lm.get("llm_teachings", [])),
        "decisions":     len(lm.get("llm_decisions", [])),
    }


def get_world_llm_snapshot(world) -> dict:
    """Get a world-level summary of all LLM activity."""
    alive = [a for a in world["agents"] if a["alive"]]
    return {
        "tick":             world["tick"],
        "year":             world.get("year", 1),
        "budget":           _budget.summary(),
        "agents_with_llm":  sum(1 for a in alive if "llm_mind" in a),
        "total_wisdom":     sum(len(a.get("llm_mind", {}).get("wisdom", [])) for a in alive),
        "total_teachings":  sum(len(a.get("llm_mind", {}).get("llm_teachings", [])) for a in alive),
        "total_reflections":sum(len(a.get("llm_mind", {}).get("llm_reflections", [])) for a in alive),
        "recent_thoughts":  [
            {
                "agent": a["name"],
                "type":  a["type"],
                "thought": a.get("llm_mind", {}).get("llm_thoughts", [{}])[-1].get("thought", "...")
                if a.get("llm_mind", {}).get("llm_thoughts") else "..."
            }
            for a in alive if a.get("llm_mind", {}).get("llm_thoughts")
        ][-8:],
        "recent_speeches":  [
            conv for conv in world.get("conversations", [])
            if conv.get("llm_generated")
        ][-8:],
    }


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# INTEGRATION PATCH INSTRUCTIONS
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
"""
HOW TO INTEGRATE llm_mind.py INTO world_engine.py
===================================================

1. INSTALL SDK (recommended):
   pip install anthropic

2. Add to TOP of world_engine.py:
   ─────────────────────────────────────────────────
   from cognitive_loop import tick_cognitive_loops, init_bdi
   from llm_mind import tick_llm_minds, init_llm_mind, get_world_llm_snapshot

3. In spawn_agent(), after agent dict created:
   ─────────────────────────────────────────────────
   init_bdi(agent)
   init_llm_mind(agent)

4. In tick(), after tick_all_upgrades():
   ─────────────────────────────────────────────────
   tick_cognitive_loops(world)
   tick_llm_minds(world)        # LLM calls happen here

5. OPTIONAL: Log LLM snapshot every 50 ticks:
   ─────────────────────────────────────────────────
   if world["tick"] % 50 == 0:
       snap = get_world_llm_snapshot(world)
       world["llm_snapshot"] = snap

6. OPTIONAL: Tune the budget in LLM_CONFIG:
   ─────────────────────────────────────────────────
   LLM_CONFIG["agents_per_tick"] = 5      # more agents per tick
   LLM_CONFIG["call_cooldown_ticks"] = 5  # call agents more often
"""
