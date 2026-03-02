"""
emergence_detector.py — Real-time Emergence Detector
AGI World Engine — Phase 5B

Watches world_state.json and flags events that are genuinely novel —
things that have never happened before in this run, statistically
surprising, or structurally significant.

Run alongside world_engine.py:
    python emergence_detector.py                  # default: watch world_state.json
    python emergence_detector.py --file my.json   # custom file
    python emergence_detector.py --log             # also write to emergence_log.json
    python emergence_detector.py --verbose         # explain every detection

The detector builds an internal model of the world's history and flags
events that deviate meaningfully from that history.
"""

import argparse
import json
import math
import os
import time
from collections import defaultdict
from datetime import datetime


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# DETECTION RULES — each rule is a function that returns a list of
# EmergenceEvent objects (empty list = nothing detected this tick)
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

class EmergenceEvent:
    def __init__(self, tick, year, category, title, description,
                 significance, evidence=None):
        self.tick        = tick
        self.year        = year
        self.category    = category   # COGNITIVE / CULTURAL / POLITICAL / BIOLOGICAL / META
        self.title       = title
        self.description = description
        self.significance = significance  # 1-5 (5 = world-altering)
        self.evidence    = evidence or {}
        self.timestamp   = datetime.now().isoformat()

    def to_dict(self):
        return {
            "tick": self.tick, "year": self.year,
            "category": self.category, "title": self.title,
            "description": self.description,
            "significance": self.significance,
            "evidence": self.evidence,
            "timestamp": self.timestamp,
        }

    def __str__(self):
        stars = "★" * self.significance + "☆" * (5 - self.significance)
        return (f"\n  [{stars}] [{self.category}] Y{self.year} T{self.tick}\n"
                f"  {self.title}\n"
                f"  {self.description}")


class EmergenceDetector:
    """
    Maintains running history of the world and detects emergent events
    by comparing current state against that history.
    """

    def __init__(self, verbose=False):
        self.verbose = verbose

        # History trackers
        self.seen_value_profiles   = set()    # frozenset of (name, value) pairs
        self.seen_concept_texts    = set()    # concept texts ever seen
        self.concept_mutation_chain= defaultdict(list)  # concept_id → mutation history
        self.seen_belief_combos    = set()    # frozenset of (belief, value) pairs per agent
        self.war_outcomes          = []       # list of (attacker, defender, winner) past wars
        self.faction_win_paths     = defaultdict(set)   # faction → set of win_types seen
        self.agent_lifespan_history= []       # list of ages at death
        self.legend_paths          = []       # list of (type, faction, battles, discoveries)
        self.concept_carrier_peaks = {}       # concept_id → max carriers seen
        self.movement_lifespans    = []       # ticks a movement lasted before dissolving
        self.tech_order_history    = []       # order of tech discoveries
        self.faction_power_history = defaultdict(list)  # faction → [power over time]

        # Seen IDs
        self.seen_agent_ids        = set()
        self.seen_concept_ids      = set()
        self.seen_movement_names   = set()
        self.seen_institution_names= set()
        self.seen_war_pairs        = set()     # frozenset({attacker, defender})

        # Baselines (computed from first 50 ticks)
        self.baseline_computed     = False
        self.baseline_war_freq     = None      # wars per 100 ticks (baseline)
        self.baseline_legend_rate  = None
        self.early_war_count       = 0
        self.early_legend_count    = 0
        self.baseline_ticks        = 50

        # Previous state for delta detection
        self.prev_tick             = 0
        self.prev_population       = 0
        self.prev_concepts         = 0
        self.prev_beliefs          = {}        # agent_id → belief snapshot
        self.prev_faction_power    = {}
        self.prev_diplo            = {}

        # Output
        self.all_events            = []
        self.tick_event_counts     = defaultdict(int)

    # ── MAIN ENTRY POINT ────────────────────────────────────────────

    def process(self, state: dict) -> list:
        """Process one world state snapshot. Returns list of EmergenceEvents."""
        tick = state.get("tick", 0)
        year = state.get("year", 1)

        if tick <= self.prev_tick:
            return []   # no new tick

        events = []

        # Run all detectors
        events += self._detect_novel_value_profile(state)
        events += self._detect_concept_mutations(state)
        events += self._detect_belief_inversions(state)
        events += self._detect_statistical_anomalies(state)
        events += self._detect_political_novelty(state)
        events += self._detect_biological_extremes(state)
        events += self._detect_cultural_crystallisation(state)
        events += self._detect_cognitive_awakening(state)
        events += self._detect_collective_thresholds(state)
        events += self._detect_meta_patterns(state)

        # Update baselines
        self._update_history(state)

        self.prev_tick = tick
        self.all_events.extend(events)
        for e in events:
            self.tick_event_counts[tick] += 1

        return events

    # ── DETECTORS ────────────────────────────────────────────────────

    def _detect_novel_value_profile(self, state: dict) -> list:
        """
        Flag an agent whose value profile is unlike any seen before.
        Uses a hash of the top-3 dominant values as a fingerprint.
        """
        events = []
        for a in state.get("alive_agents", []):
            vals = a.get("values", {})
            if not vals: continue
            top3  = tuple(sorted(sorted(vals, key=vals.get, reverse=True)[:3]))
            score = round(max(vals.values(), default=0))
            fp    = (top3, score // 10)    # bin score to reduce noise

            if fp not in self.seen_value_profiles and score > 65:
                self.seen_value_profiles.add(fp)
                events.append(EmergenceEvent(
                    tick=state["tick"], year=state["year"],
                    category="COGNITIVE",
                    title=f"Novel value archetype: {a['name']}",
                    description=(f"{a['name']} ({a['type']}, {a.get('faction','?')}) "
                                 f"has crystallised a value profile never seen before. "
                                 f"Dominant values: {', '.join(top3)} (peak {score})"),
                    significance=2,
                    evidence={"agent": a["name"], "top_values": top3, "peak_score": score},
                ))
        return events

    def _detect_concept_mutations(self, state: dict) -> list:
        """Flag concepts that have mutated 3+ times — rare creative drift."""
        events = []
        kn = state.get("knowledge_network", {})
        for cid, node in kn.get("nodes", {}).items():
            mutations = node.get("mutation_count", 0)
            carriers  = len(node.get("carriers", []))

            # New concept
            if cid not in self.seen_concept_ids:
                self.seen_concept_ids.add(cid)
                # Seed concept — only flag if it spreads unusually fast
                if carriers > 8:
                    events.append(EmergenceEvent(
                        tick=state["tick"], year=state["year"],
                        category="CULTURAL",
                        title=f"Viral concept: \"{node.get('text','?')[:60]}\"",
                        description=(f"A new concept spread to {carriers} carriers "
                                     f"(category: {node.get('category','?')})"),
                        significance=2,
                        evidence={"concept": node.get("text"), "carriers": carriers},
                    ))

            # Heavily mutated concept
            chain_key = f"{cid}_mut"
            prev_mut  = self.concept_mutation_chain.get(chain_key, 0)
            if mutations >= 3 and mutations > prev_mut:
                self.concept_mutation_chain[chain_key] = mutations
                events.append(EmergenceEvent(
                    tick=state["tick"], year=state["year"],
                    category="CULTURAL",
                    title=f"Idea evolution (×{mutations}): \"{node.get('text','?')[:50]}\"",
                    description=(f"A concept has mutated {mutations} times — rare memetic "
                                 f"evolution. Still carried by {carriers} agents."),
                    significance=3,
                    evidence={"concept": node.get("text"), "mutations": mutations,
                              "carriers": carriers, "origin": node.get("origin_agent","?")},
                ))

            # Concept that peaked in carriers and is now declining (concept death)
            peak = self.concept_carrier_peaks.get(cid, 0)
            if carriers > peak:
                self.concept_carrier_peaks[cid] = carriers
            elif peak > 10 and carriers < peak * 0.3:
                del self.concept_carrier_peaks[cid]   # avoid re-firing
                events.append(EmergenceEvent(
                    tick=state["tick"], year=state["year"],
                    category="CULTURAL",
                    title=f"Idea extinction: \"{node.get('text','?')[:50]}\"",
                    description=(f"An idea that once reached {peak} carriers has "
                                 f"collapsed to {carriers}. Memetic extinction event."),
                    significance=2,
                    evidence={"concept": node.get("text"), "peak": peak, "now": carriers},
                ))
        return events

    def _detect_belief_inversions(self, state: dict) -> list:
        """Flag agents whose core beliefs completely flipped since last seen."""
        events = []
        for a in state.get("alive_agents", []):
            aid  = a.get("id")
            b    = a.get("beliefs", {})
            prev = self.prev_beliefs.get(aid, {})
            if not prev or not b: continue

            inversions = []
            for key, bstate in b.items():
                prev_val = prev.get(key, {}).get("value")
                curr_val = bstate.get("value")
                prev_conf = prev.get(key, {}).get("confidence", 50)
                curr_conf = bstate.get("confidence", 50)
                if (prev_val is not None and curr_val is not None and
                        prev_val != curr_val and
                        prev_conf > 60 and curr_conf > 40):
                    inversions.append(key)

            if len(inversions) >= 2:
                events.append(EmergenceEvent(
                    tick=state["tick"], year=state["year"],
                    category="COGNITIVE",
                    title=f"Belief system collapse: {a['name']}",
                    description=(f"{a['name']} ({a.get('emotion','?')}) reversed "
                                 f"{len(inversions)} strongly-held beliefs: "
                                 f"{', '.join(inversions[:3])}. Age {a.get('age',0)}."),
                    significance=3,
                    evidence={"agent": a["name"], "beliefs_flipped": inversions,
                              "emotion": a.get("emotion"), "age": a.get("age")},
                ))
        return events

    def _detect_statistical_anomalies(self, state: dict) -> list:
        """
        Flag values that deviate more than 2 standard deviations from
        the running mean — statistical outliers in the world's history.
        """
        events = []
        tick  = state["tick"]
        stats = state.get("stats", {})

        # Population crash (>30% drop in one tick)
        pop = state.get("population", 0)
        if (self.prev_population > 10 and pop > 0 and
                pop < self.prev_population * 0.7):
            lost = self.prev_population - pop
            events.append(EmergenceEvent(
                tick=tick, year=state["year"],
                category="BIOLOGICAL",
                title=f"Population collapse: -{lost} souls in one tick",
                description=(f"Population dropped from {self.prev_population} to {pop} "
                             f"({lost/self.prev_population*100:.0f}% loss). "
                             f"Disease, war, or mass death event."),
                significance=4,
                evidence={"before": self.prev_population, "after": pop, "lost": lost},
            ))

        # Knowledge network explosion
        kn      = state.get("knowledge_network", {})
        concepts = len(kn.get("nodes", {}))
        if (self.prev_concepts > 0 and
                concepts > self.prev_concepts * 1.5 and
                concepts - self.prev_concepts > 5):
            new = concepts - self.prev_concepts
            events.append(EmergenceEvent(
                tick=tick, year=state["year"],
                category="CULTURAL",
                title=f"Knowledge explosion: +{new} concepts",
                description=(f"The knowledge network grew by {new} concepts in one tick "
                             f"({self.prev_concepts} → {concepts}). "
                             f"Rare burst of collective creativity."),
                significance=3,
                evidence={"before": self.prev_concepts, "after": concepts, "gain": new},
            ))
        return events

    def _detect_political_novelty(self, state: dict) -> list:
        """Flag unprecedented political configurations."""
        events = []
        tick   = state["tick"]
        fsum   = state.get("faction_summary", {})

        # First time this specific war pair has fought
        for w in state.get("active_wars", []):
            att = w.get("attacker","?")
            dft = w.get("defender","?")
            pair = frozenset({att, dft})
            if pair not in self.seen_war_pairs:
                self.seen_war_pairs.add(pair)
                cause = w.get("cause", "unknown")
                events.append(EmergenceEvent(
                    tick=tick, year=state["year"],
                    category="POLITICAL",
                    title=f"First war: {att} vs {dft}",
                    description=(f"{att} and {dft} are at war for the first time. "
                                 f"Cause: {cause}"),
                    significance=2,
                    evidence={"attacker": att, "defender": dft, "cause": cause},
                ))

        # All-faction alliance (all 4 at peace with each other)
        diplo = state.get("diplomacy", {})
        factions = list(fsum.keys())
        if len(factions) >= 4:
            all_allied = all(
                state.get("diplomacy", {}).get(
                    f"{min(a,b)}:{max(a,b)}", "neutral") in ("allied","neutral")
                for i, a in enumerate(factions)
                for b in factions[i+1:]
            )
            wars = state.get("active_wars", [])
            if all_allied and not wars and tick > 100:
                # Only fire once per peace period
                if not hasattr(self, "_last_peace_tick") or tick - self._last_peace_tick > 100:
                    self._last_peace_tick = tick
                    events.append(EmergenceEvent(
                        tick=tick, year=state["year"],
                        category="POLITICAL",
                        title="Global peace achieved",
                        description="All four factions are simultaneously at peace. "
                                    "Statistically rare — previous wars: "
                                    f"{state.get('stats',{}).get('wars_fought',0)}",
                        significance=4,
                        evidence={"total_wars_before": state.get("stats",{}).get("wars_fought",0)},
                    ))

        # Power reversal (faction that was weakest becomes strongest)
        if fsum:
            powers = {f: fsum[f].get("power", 0) for f in fsum}
            if self.prev_faction_power:
                prev_dominant = max(self.prev_faction_power, key=self.prev_faction_power.get)
                curr_dominant = max(powers, key=powers.get)
                if (curr_dominant != prev_dominant and
                        self.prev_faction_power.get(curr_dominant, 0) ==
                        min(self.prev_faction_power.values())):
                    events.append(EmergenceEvent(
                        tick=tick, year=state["year"],
                        category="POLITICAL",
                        title=f"Power reversal: {curr_dominant} rises from last to first",
                        description=(f"{curr_dominant} was the weakest faction and is now "
                                     f"dominant (power {powers[curr_dominant]}). "
                                     f"Displaced {prev_dominant}."),
                        significance=4,
                        evidence={"new_dominant": curr_dominant,
                                  "displaced": prev_dominant,
                                  "power": powers[curr_dominant]},
                    ))

        return events

    def _detect_biological_extremes(self, state: dict) -> list:
        """Flag unusual biological/demographic events."""
        events = []
        tick   = state["tick"]
        recent_grave = state.get("recent_graveyard", [])

        for g in recent_grave:
            age = g.get("age", 0)

            # Centenarian death (age 200+ in world-years)
            if age >= 200 and g.get("id") not in self.seen_agent_ids:
                self.seen_agent_ids.add(g.get("id", ""))
                events.append(EmergenceEvent(
                    tick=tick, year=state["year"],
                    category="BIOLOGICAL",
                    title=f"Ancient dies: {g.get('name','?')} (age {age})",
                    description=(f"{g.get('name','?')} the {g.get('type','?')} of "
                                 f"{g.get('faction','?')} died at age {age}. "
                                 f"\"{g.get('epitaph','...')}\""),
                    significance=3,
                    evidence={"name": g.get("name"), "age": age,
                              "faction": g.get("faction"), "epitaph": g.get("epitaph")},
                ))

        # Multigenerational legend (is_legend = True with lineage)
        for a in state.get("alive_agents", []):
            if (a.get("is_legend") and
                    a.get("parent_a") and
                    a.get("id") not in self.seen_agent_ids):
                # Check if parent was also a legend
                parent_name = a.get("parent_a", "")
                legends = state.get("legends", [])
                parent_legend = any(l.get("name") == parent_name for l in legends)
                if parent_legend:
                    self.seen_agent_ids.add(a["id"])
                    events.append(EmergenceEvent(
                        tick=tick, year=state["year"],
                        category="BIOLOGICAL",
                        title=f"Dynasty: {a['name']} born of legend {parent_name}",
                        description=(f"A child of legend {parent_name} has themselves "
                                     f"become legendary. A true dynasty."),
                        significance=4,
                        evidence={"child": a["name"], "parent": parent_name,
                                  "faction": a.get("faction")},
                    ))
        return events

    def _detect_cultural_crystallisation(self, state: dict) -> list:
        """Flag the formation of novel cultural structures."""
        events = []
        tick   = state["tick"]

        # New movement forming
        for m in state.get("cultural_movements", []):
            name = m.get("name", "")
            if name and name not in self.seen_movement_names:
                self.seen_movement_names.add(name)
                size = len(m.get("members", []))
                events.append(EmergenceEvent(
                    tick=tick, year=state["year"],
                    category="CULTURAL",
                    title=f"Movement born: {name}",
                    description=(f"A cultural movement crystallised around the value "
                                 f"'{m.get('value','?')}'. Leader: {m.get('leader','?')}. "
                                 f"{size} initial members."),
                    significance=3,
                    evidence={"name": name, "value": m.get("value"),
                              "leader": m.get("leader"), "size": size},
                ))

        # New institution forming
        for inst in state.get("institutions", []):
            iname = inst.get("name","")
            if iname and iname not in self.seen_institution_names:
                self.seen_institution_names.add(iname)
                events.append(EmergenceEvent(
                    tick=tick, year=state["year"],
                    category="CULTURAL",
                    title=f"Institution founded: {iname}",
                    description=(f"A {inst.get('type','?').replace('_',' ')} institution "
                                 f"formed in {inst.get('faction','?')} with "
                                 f"{len(inst.get('members',[]))} members."),
                    significance=2,
                    evidence={"name": iname, "type": inst.get("type"),
                              "faction": inst.get("faction")},
                ))
        return events

    def _detect_cognitive_awakening(self, state: dict) -> list:
        """Flag agents showing unusual cognitive depth."""
        events = []
        tick   = state["tick"]

        for a in state.get("alive_agents", []):
            aid = a.get("id")

            # Agent with identity archetype + high value peak + BDI active
            identity = a.get("identity_system", {}).get("current_identity","")
            vals = a.get("values", {})
            top_val = max(vals.values(), default=0) if vals else 0
            bdi_cycles = a.get("bdi", {}).get("stats", {}).get("total_cycles", 0)
            llm_calls  = a.get("llm_mind", {}).get("call_count", 0)

            # Highly autonomous agent: has own goals, high values, active BDI
            originated = a.get("originated_goals", [])
            active_goals = sum(1 for g in originated if g.get("active"))
            if (active_goals >= 3 and top_val > 75 and
                    identity and aid not in self.seen_agent_ids):
                self.seen_agent_ids.add(aid)
                events.append(EmergenceEvent(
                    tick=tick, year=state["year"],
                    category="COGNITIVE",
                    title=f"Autonomous agent: {a['name']}",
                    description=(f"{a['name']} ({a.get('type')}) has {active_goals} "
                                 f"self-originated active goals, identity '{identity}', "
                                 f"peak value {top_val:.0f}. Age {a.get('age',0)}."),
                    significance=3,
                    evidence={"agent": a["name"], "goals": active_goals,
                              "identity": identity, "top_value": top_val,
                              "bdi_cycles": bdi_cycles, "llm_calls": llm_calls},
                ))

            # Agent whose LLM thought is substantially different from their type default
            llm_thought = a.get("llm_mind", {}).get("last_response", "")
            if llm_thought and len(llm_thought) > 80 and llm_calls > 5:
                # Look for reflection keywords
                reflection_words = ["regret","wonder","question","doubt",
                                    "believe","purpose","meaning","alone"]
                if any(w in llm_thought.lower() for w in reflection_words):
                    key = f"reflect_{aid}"
                    if key not in self.seen_agent_ids:
                        self.seen_agent_ids.add(key)
                        events.append(EmergenceEvent(
                            tick=tick, year=state["year"],
                            category="COGNITIVE",
                            title=f"Deep reflection: {a['name']}",
                            description=(f"{a['name']} is showing genuine introspective "
                                         f"cognition (LLM call #{llm_calls}): "
                                         f"\"{llm_thought[:120]}...\""),
                            significance=3,
                            evidence={"agent": a["name"], "thought": llm_thought[:200],
                                      "llm_calls": llm_calls},
                        ))
        return events

    def _detect_collective_thresholds(self, state: dict) -> list:
        """Flag when the collective intelligence layer crosses major thresholds."""
        events = []
        tick   = state["tick"]
        cs     = state.get("collective_stats", {})
        el     = state.get("eternal_loop", {})

        # Epoch transition
        epoch_name = el.get("epoch_name","")
        key = f"epoch_{epoch_name}"
        if epoch_name and key not in self.seen_movement_names:
            self.seen_movement_names.add(key)
            if tick > 10:   # don't flag the initial epoch
                events.append(EmergenceEvent(
                    tick=tick, year=state["year"],
                    category="META",
                    title=f"Epoch transition: {epoch_name}",
                    description=(f"The world has entered a new epoch: '{epoch_name}'. "
                                 f"Epochs completed: {el.get('epochs_completed',0)}. "
                                 f"Upheavals to date: {len(el.get('upheavals_fired',[]))}"),
                    significance=5,
                    evidence={"epoch": epoch_name,
                              "upheavals": len(el.get("upheavals_fired",[]))},
                ))

        # Upheaval
        upheavals = el.get("upheavals_fired", [])
        key2 = f"upheaval_count_{len(upheavals)}"
        if upheavals and key2 not in self.seen_institution_names:
            self.seen_institution_names.add(key2)
            latest = upheavals[-1] if isinstance(upheavals[-1], dict) else {"type":"?"}
            events.append(EmergenceEvent(
                tick=tick, year=state["year"],
                category="META",
                title=f"Upheaval #{len(upheavals)}: {latest.get('type','?').replace('_',' ').upper()}",
                description=(f"A major world upheaval has fired. The eternal loop is "
                             f"forcing change to prevent stagnation."),
                significance=4,
                evidence={"type": latest.get("type"), "count": len(upheavals)},
            ))

        # World health crisis
        wh = state.get("world_health", {})
        score = wh.get("overall_score", 1.0)
        key3 = f"health_crisis_{int(score*10)}"
        if score < 0.35 and key3 not in self.seen_institution_names:
            self.seen_institution_names.add(key3)
            events.append(EmergenceEvent(
                tick=tick, year=state["year"],
                category="META",
                title=f"World health crisis: {score*100:.0f}% vitality",
                description=(f"The world health monitor is critical ({score*100:.0f}%). "
                             f"Self-healing systems should be intervening."),
                significance=4,
                evidence={"score": score, "vitals": wh.get("vitals",{})},
            ))
        return events

    def _detect_meta_patterns(self, state: dict) -> list:
        """Detect patterns across the whole run — structural emergence."""
        events = []
        tick   = state["tick"]

        # All-tech world: every faction has researched everything
        all_tech = {"bronze_working","agriculture","writing","masonry",
                    "medicine","theology","iron_working","philosophy"}
        faction_techs = {f: set(t.get("researched",[]))
                         for f, t in state.get("faction_tech",{}).items()}
        all_researched = set.union(*faction_techs.values()) if faction_techs else set()
        if all_researched >= all_tech:
            key = "all_tech_discovered"
            if key not in self.seen_institution_names:
                self.seen_institution_names.add(key)
                events.append(EmergenceEvent(
                    tick=tick, year=state["year"],
                    category="META",
                    title="Technological singularity: all 8 technologies known",
                    description="Every technology in the tree has been discovered "
                                "by at least one faction. Knowledge is universal.",
                    significance=5,
                    evidence={"tick": tick, "year": state["year"]},
                ))

        # Legend density (>20% of living population are legends)
        pop     = state.get("population", 1)
        legends = len(state.get("legends", []))
        if pop > 0 and legends / pop > 0.2 and pop > 10:
            key = f"legend_density_{legends}"
            if key not in self.seen_institution_names:
                self.seen_institution_names.add(key)
                events.append(EmergenceEvent(
                    tick=tick, year=state["year"],
                    category="META",
                    title=f"Heroic age: {legends} legends among {pop} living",
                    description=(f"More than 20% of the living population are legends. "
                                 f"Extraordinary density of remarkable individuals."),
                    significance=4,
                    evidence={"legends": legends, "population": pop,
                              "ratio": round(legends/pop, 2)},
                ))
        return events

    # ── HISTORY UPDATER ──────────────────────────────────────────────

    def _update_history(self, state: dict):
        self.prev_population = state.get("population", 0)
        self.prev_concepts   = len(state.get("knowledge_network",{}).get("nodes",{}))
        self.prev_faction_power = {
            f: d.get("power", 0)
            for f, d in state.get("faction_summary", {}).items()
        }
        # Update belief snapshots
        for a in state.get("alive_agents", []):
            aid = a.get("id")
            if aid:
                self.prev_beliefs[aid] = {
                    k: {"value": v.get("value"), "confidence": v.get("confidence", 50)}
                    for k, v in a.get("beliefs", {}).items()
                }


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# MAIN WATCH LOOP
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

SIGNIFICANCE_LABELS = {1: "minor", 2: "notable", 3: "significant",
                       4: "major", 5: "historic"}
CATEGORY_COLORS = {
    "COGNITIVE":  "\033[94m",   # blue
    "CULTURAL":   "\033[95m",   # purple
    "POLITICAL":  "\033[91m",   # red
    "BIOLOGICAL": "\033[92m",   # green
    "META":       "\033[93m",   # yellow
}
RESET = "\033[0m"
BOLD  = "\033[1m"


def load_state(path: str) -> dict:
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}


def print_event(event: EmergenceEvent, verbose: bool = False):
    col   = CATEGORY_COLORS.get(event.category, "")
    stars = "★" * event.significance + "☆" * (5 - event.significance)
    print(f"\n  {col}{BOLD}[{stars}] [{event.category}]{RESET}  "
          f"Y{event.year} T{event.tick}")
    print(f"  {BOLD}{event.title}{RESET}")
    print(f"  {event.description}")
    if verbose and event.evidence:
        for k, v in event.evidence.items():
            if v:
                val_str = str(v)[:80]
                print(f"  {col}  evidence.{k}:{RESET} {val_str}")


def print_summary(detector: EmergenceDetector, tick: int):
    total = len(detector.all_events)
    if total == 0: return
    by_cat = defaultdict(int)
    by_sig = defaultdict(int)
    for e in detector.all_events:
        by_cat[e.category] += 1
        by_sig[e.significance] += 1
    sig_str = " | ".join(f"★×{k}:{v}" for k,v in sorted(by_sig.items(), reverse=True))
    cat_str = " | ".join(f"{k}:{v}" for k,v in sorted(by_cat.items()))
    print(f"\n  {'─'*60}")
    print(f"  EMERGENCE SUMMARY  T{tick}  |  {total} events detected")
    print(f"  {sig_str}")
    print(f"  {cat_str}")
    print(f"  {'─'*60}")


def watch(state_file: str, log_file: str | None, verbose: bool, min_sig: int):
    detector    = EmergenceDetector(verbose=verbose)
    last_mtime  = 0
    last_tick   = 0
    log_entries = []

    print(f"\n  {BOLD}EMERGENCE DETECTOR{RESET} watching {state_file}")
    print(f"  Min significance: {'★'*min_sig}  |  verbose: {verbose}")
    print(f"  Press Ctrl+C to stop\n")

    try:
        while True:
            try:
                mtime = os.path.getmtime(state_file)
            except FileNotFoundError:
                time.sleep(1)
                continue

            if mtime <= last_mtime:
                time.sleep(0.5)
                continue

            last_mtime = mtime
            state = load_state(state_file)
            if not state or state.get("tick", 0) <= last_tick:
                time.sleep(0.5)
                continue

            last_tick = state.get("tick", 0)
            events    = detector.process(state)

            for event in events:
                if event.significance >= min_sig:
                    print_event(event, verbose)
                    if log_file:
                        log_entries.append(event.to_dict())

            # Summary every 50 ticks
            if last_tick % 50 == 0 and last_tick > 0:
                print_summary(detector, last_tick)

            # Save log
            if log_file and log_entries:
                with open(log_file, "w", encoding="utf-8") as f:
                    json.dump(log_entries, f, indent=2, ensure_ascii=False)

    except KeyboardInterrupt:
        print(f"\n\n  Stopping detector...")
        print_summary(detector, last_tick)
        if log_file and log_entries:
            with open(log_file, "w", encoding="utf-8") as f:
                json.dump(log_entries, f, indent=2, ensure_ascii=False)
            print(f"  Log saved → {log_file}")
        print(f"\n  {BOLD}Top 10 most significant events:{RESET}")
        top = sorted(detector.all_events, key=lambda e: e.significance, reverse=True)[:10]
        for e in top:
            print(f"    {'★'*e.significance} [{e.category}] Y{e.year} {e.title}")
        print()


def main():
    parser = argparse.ArgumentParser(description="AGI World Engine — Emergence Detector")
    parser.add_argument("--file",    type=str, default="world_state.json",
                        help="Path to world_state.json (default: world_state.json)")
    parser.add_argument("--log",     type=str, default=None,
                        help="Save all events to this JSON file")
    parser.add_argument("--verbose", action="store_true",
                        help="Show evidence data for each event")
    parser.add_argument("--min",     type=int, default=2,
                        help="Minimum significance to display (1-5, default 2)")
    args = parser.parse_args()

    log_path = args.log or (
        "emergence_log.json" if args.log is not None else None
    )

    watch(
        state_file = args.file,
        log_file   = args.log,
        verbose    = args.verbose,
        min_sig    = args.min,
    )


if __name__ == "__main__":
    main()
