"""
AI WORLD ENGINE v4.0 - FINAL FORM
All previous systems PLUS:
  CONVERSATIONS  - agents talk when they meet
  BIOMES         - desert, forest, tundra, ocean, plains, swamp, mountain
  WIN CONDITIONS - conquest, wealth, faith, knowledge victories
  GRAVEYARD      - full death records with epitaphs
  LINEAGE        - family trees, dynasties, inherited names
  SOUND EVENTS   - sound_events.json triggers for dashboard
  RICH STATS     - war timeline, hall of fame, dynasty tracker
"""

import json, random, time, math, os
from datetime import datetime

# ── AGI LAYER MODULES ─────────────────────────────────────────────
# Phase 1: BDI Cognitive Loop
try:
    from cognitive_loop import (
        init_bdi, tick_cognitive_loops,
        get_bdi_summary, get_bdi_thought
    )
    _COGNITIVE_LOOP_LOADED = True
except ImportError as _e:
    _COGNITIVE_LOOP_LOADED = False
    print("  [AGI] cognitive_loop.py not found — BDI layer disabled (%s)" % _e)

# Phase 2: LLM Mind (Claude-powered reasoning)
try:
    from llm_mind import (
        init_llm_mind, tick_llm_minds,
        get_llm_mind_summary
    )
    _LLM_MIND_LOADED = True
except ImportError as _e:
    _LLM_MIND_LOADED = False
    print("  [AGI] llm_mind.py not found — LLM layer disabled (%s)" % _e)

# Phase 3: Value Engine (self-modification)
try:
    from value_engine import (
        init_value_system, tick_value_engine,
        inherit_values, get_value_engine_summary,
        get_dominant_values, get_value_profile_str
    )
    _VALUE_ENGINE_LOADED = True
except ImportError as _e:
    _VALUE_ENGINE_LOADED = False
    print("  [AGI] value_engine.py not found — value layer disabled (%s)" % _e)

# Phase 4: Collective Intelligence + Eternal Loop
try:
    from collective_loop import (
        init_collective, tick_collective,
        get_collective_snapshot, get_agent_concepts_str
    )
    _COLLECTIVE_LOOP_LOADED = True
except ImportError as _e:
    _COLLECTIVE_LOOP_LOADED = False
    print("  [AGI] collective_loop.py not found — collective layer disabled (%s)" % _e)
# ─────────────────────────────────────────────────────────────────

# CONFIG
WORLD_SIZE       = 80
TICK_RATE        = 1.5
MAX_AGENTS       = 40
MAX_BUILDINGS    = 60
MAX_MEMORY       = 30
WORLD_STATE_FILE = "world_state.json"
WORLD_SAVE_FILE  = "world_save.json"
SOUND_FILE       = "sound_events.json"
LOG_FILE         = "world_log.txt"
SAVE_EVERY       = 30

# FACTIONS
FACTIONS = {
    "Ironveil":   {"color":[1.0,0.25,0.15],"symbol":"F","trait":"aggressive","home":[-25,-25],"bonus":"war"},
    "Greenveil":  {"color":[0.15,0.85,0.3],"symbol":"G","trait":"peaceful",  "home":[25,25],  "bonus":"growth"},
    "Goldveil":   {"color":[1.0,0.80,0.1], "symbol":"W","trait":"mercantile","home":[25,-25], "bonus":"wealth"},
    "Shadowveil": {"color":[0.5,0.15,0.85],"symbol":"S","trait":"secretive", "home":[-25,25], "bonus":"espionage"},
}

FACTION_PREFERRED_TYPES = {
    "Ironveil":   ["warrior","warrior","assassin","explorer","builder","spy"],
    "Greenveil":  ["farmer","farmer","healer","priest","builder","scholar"],
    "Goldveil":   ["merchant","merchant","scholar","explorer","builder","spy"],
    "Shadowveil": ["spy","spy","assassin","scholar","explorer","warrior"],
}

AGENT_TYPES = {
    "explorer":    {"color":[0.2,0.8,1.0], "size":1.0,"speed":2.5,"symbol":"E","lifespan":[250,450]},
    "builder":     {"color":[1.0,0.6,0.1], "size":1.2,"speed":1.0,"symbol":"B","lifespan":[300,500]},
    "farmer":      {"color":[0.3,0.9,0.3], "size":0.9,"speed":1.2,"symbol":"F","lifespan":[280,480]},
    "warrior":     {"color":[1.0,0.2,0.2], "size":1.3,"speed":2.8,"symbol":"W","lifespan":[150,350]},
    "scholar":     {"color":[0.8,0.4,1.0], "size":0.8,"speed":0.8,"symbol":"S","lifespan":[350,550]},
    "merchant":    {"color":[1.0,0.85,0.0],"size":1.0,"speed":2.0,"symbol":"M","lifespan":[270,470]},
    "priest":      {"color":[1.0,1.0,0.8], "size":0.9,"speed":0.7,"symbol":"P","lifespan":[300,500]},
    "spy":         {"color":[0.3,0.3,0.55],"size":0.7,"speed":2.5,"symbol":"X","lifespan":[200,400]},
    "healer":      {"color":[0.4,1.0,0.7], "size":0.9,"speed":1.4,"symbol":"H","lifespan":[320,520]},
    "assassin":    {"color":[0.6,0.0,0.1], "size":0.8,"speed":3.2,"symbol":"A","lifespan":[180,360]},
    # v8.0 Archetype evolutions
    "philosopher": {"color":[0.9,0.5,1.0], "size":1.0,"speed":0.6,"symbol":"Φ","lifespan":[450,700]},
    "crime_lord":  {"color":[0.7,0.1,0.5], "size":1.1,"speed":1.8,"symbol":"C","lifespan":[250,450]},
    "plague_doctor":{"color":[0.2,0.9,0.5],"size":0.9,"speed":1.2,"symbol":"D","lifespan":[400,650]},
    "patriarch":   {"color":[0.6,0.9,0.3], "size":1.1,"speed":0.8,"symbol":"♂","lifespan":[400,650]},
    "matriarch":   {"color":[0.9,0.7,0.3], "size":1.1,"speed":0.8,"symbol":"♀","lifespan":[400,650]},
}

BUILDING_TYPES = [
    "hut","farm","well","watchtower","barracks","forge","market",
    "temple","library","tavern","palace","dungeon","shrine","granary",
    "workshop","harbor","academy","cathedral","fortress","colosseum"
]

BUILDING_POWER = {
    "hut":1,"farm":2,"well":1,"watchtower":3,"barracks":4,"forge":3,
    "market":3,"temple":5,"library":4,"tavern":2,"palace":8,"dungeon":3,
    "shrine":3,"granary":2,"workshop":3,"harbor":4,"academy":5,
    "cathedral":7,"fortress":6,"colosseum":5
}

RESOURCE_TYPES = ["wood","stone","food","gold","knowledge","faith","iron","herbs"]

# Resource caps — prevent runaway accumulation
FAITH_CAP     = 500_000   # world faith hard cap
AGENT_FAITH_CAP = 100     # per-agent faith hard cap
KNOWLEDGE_CAP  = 50_000  # world knowledge hard cap

TECH_TREE = {
    "bronze_working": {"cost":50, "unlocks":"forge",     "bonus":"warrior_strength"},
    "agriculture":    {"cost":40, "unlocks":"granary",   "bonus":"food_double"},
    "writing":        {"cost":60, "unlocks":"library",   "bonus":"memory_plus"},
    "masonry":        {"cost":70, "unlocks":"fortress",  "bonus":"building_speed"},
    "medicine":       {"cost":90, "unlocks":"academy",   "bonus":"lifespan_plus"},
    "theology":       {"cost":100,"unlocks":"cathedral", "bonus":"faith_double"},
    "iron_working":   {"cost":120,"unlocks":"colosseum", "bonus":"army_power"},
    "philosophy":     {"cost":150,"unlocks":"palace",    "bonus":"diplomacy_bonus"},
}

TRAITS = [
    "brave","cowardly","wise","foolish","kind","cruel","loyal","treacherous",
    "ambitious","content","charismatic","antisocial","curious","incurious",
    "strong","weak","fast","slow","lucky","unlucky","spiritual","atheistic"
]

WEATHER_TYPES = [
    ("clear",1.0,"Sun"),("cloudy",0.9,"Cloud"),("rain",0.8,"Rain"),
    ("storm",0.5,"Storm"),("drought",0.6,"Drought"),("blizzard",0.4,"Blizzard"),
    ("fog",0.85,"Fog"),
]

SEASONS = ["spring","summer","autumn","winter"]

DISEASE_NAMES = [
    "Black Fever","Ash Plague","The Withering","Red Sickness",
    "Stonescale","Voidrot","Bloodcough","The Creeping Dark"
]

# BIOMES
BIOME_TYPES = {
    "plains":  {"color":[0.6,0.8,0.3],"food_mod":1.5,"speed_mod":1.0,"build_mod":1.0},
    "forest":  {"color":[0.1,0.5,0.1],"food_mod":1.2,"speed_mod":0.8,"build_mod":0.9},
    "desert":  {"color":[0.9,0.8,0.3],"food_mod":0.4,"speed_mod":0.9,"build_mod":0.7},
    "tundra":  {"color":[0.7,0.8,0.9],"food_mod":0.3,"speed_mod":0.6,"build_mod":0.6},
    "swamp":   {"color":[0.3,0.5,0.3],"food_mod":0.8,"speed_mod":0.5,"build_mod":0.5},
    "mountain":{"color":[0.5,0.4,0.4],"food_mod":0.5,"speed_mod":0.4,"build_mod":0.8},
    "ocean":   {"color":[0.1,0.3,0.8],"food_mod":0.0,"speed_mod":0.0,"build_mod":0.0},
}

# CONVERSATION TEMPLATES
CONVERSATION_TEMPLATES = {
    ("warrior","warrior"):  [
        "{a} and {b} spar, trading stories of battle.",
        "{a} challenges {b} to a test of strength.",
        "{a} warns {b} about enemy movements to the east.",
        "{a} and {b} pledge to fight side by side.",
    ],
    ("merchant","merchant"):[
        "{a} and {b} argue over trade routes.",
        "{a} sells {b} a rare gem for 3 gold.",
        "{a} and {b} agree to split a profitable caravan.",
        "{a} warns {b} about bandits on the northern road.",
    ],
    ("scholar","scholar"):  [
        "{a} debates philosophy with {b} until dawn.",
        "{a} shares a discovery with {b}, who is amazed.",
        "{a} and {b} argue over the nature of the stars.",
        "{a} copies a passage from {b}'s book.",
    ],
    ("priest","priest"):    [
        "{a} and {b} pray together at a crossroads.",
        "{a} debates theology with {b}.",
        "{a} and {b} perform a ritual under the moon.",
    ],
    ("healer","warrior"):   [
        "{a} patches {b}'s wounds after a skirmish.",
        "{a} warns {b} that another battle will kill them.",
        "{b} thanks {a} for saving their life.",
    ],
    ("explorer","explorer"):[
        "{a} and {b} compare maps of uncharted territory.",
        "{a} tells {b} about the dragon's nest they found.",
        "{a} and {b} race to see who can explore furthest.",
    ],
    ("spy","spy"):          [
        "{a} and {b} exchange coded intelligence.",
        "{a} suspects {b} is a double agent.",
        "{a} and {b} meet in secret at midnight.",
    ],
    ("farmer","farmer"):    [
        "{a} and {b} compare harvests over a meal.",
        "{a} helps {b} repair a broken fence.",
        "{a} and {b} argue about who owns the eastern field.",
    ],
}

DEFAULT_CONVERSATIONS = [
    "{a} greets {b} with a nod.",
    "{a} asks {b} about the road ahead.",
    "{a} and {b} share a meal by the fire.",
    "{a} warns {b} about dangerous weather coming.",
    "{a} tells {b} a rumour about {faction}.",
    "{a} offers {b} a trade.",
    "{a} and {b} argue briefly then part ways.",
    "{a} asks {b} if they have seen strange lights at night.",
    "{a} tells {b} about a strange dream they had.",
    "{a} borrows something from {b} and promises to return it.",
]

WIN_CONDITIONS = {
    "conquest":  {"desc":"Control 70% of all buildings","check":"buildings"},
    "wealth":    {"desc":"Accumulate 500 gold",          "check":"gold"},
    "faith":     {"desc":"Convert 80% of living agents", "check":"faith"},
    "knowledge": {"desc":"Research all 8 technologies",  "check":"tech"},
}

# WORLD STATE
world = {
    "tick":0,"year":1,"season":"spring",
    "weather":"clear","weather_ticks_left":10,
    "population":0,
    "agents":[],"buildings":[],"cities":[],
    "resources":{},"events":[],"terrain":[],
    "biome_map":[],
    "world_history":[],"legends":[],
    "graveyard":[],
    "lineage":{},
    "immortals":[],
    "tension":{},
    "last_war_tick":0,
    "conversations":[],
    "active_wars":[],"alliances":[],
    "diplomacy":{},
    "faction_tech":{f:{"researched":[],"points":0} for f in FACTIONS},
    "faction_power":{f:0 for f in FACTIONS},
    "diseases":[],"plague_active":False,
    "winner":None,
    "war_timeline":[],
    "sound_queue":[],
    "stats":{
        "total_births":0,"total_deaths":0,"buildings_built":0,
        "wars_fought":0,"alliances_formed":0,"betrayals":0,
        "discoveries":0,"trades":0,"assassinations":0,
        "children_born":0,"legends_made":0,"plagues":0,
        "tech_discovered":0,"total_ticks_ever":0,"immortals_made":0,"holy_wars":0,"heretics_spawned":0,"goals_achieved":0,"goals_originated":0,"beliefs_shattered":0,"abstractions_made":0,"contracts_formed":0,"contracts_violated":0,"institutions_formed":0,"strategy_changes":0,"goals_achieved":0,"goals_originated":0,"beliefs_shattered":0,"abstractions_made":0,"contracts_formed":0,"contracts_violated":0,"institutions_formed":0,"strategy_changes":0,
        "conversations":0,"natural_deaths":0,"battle_deaths":0,
        "disease_deaths":0,
    }
}

_agent_counter = 0

# UTILITIES
def rand_pos(center=None, radius=None):
    if radius is None: radius=WORLD_SIZE/2
    if center:
        return [round(center[0]+random.uniform(-radius,radius),2),
                round(center[1]+random.uniform(-radius,radius),2)]
    return [round(random.uniform(-WORLD_SIZE/2,WORLD_SIZE/2),2),
            round(random.uniform(-WORLD_SIZE/2,WORLD_SIZE/2),2)]

def dist(a,b): return math.sqrt((a[0]-b[0])**2+(a[1]-b[1])**2)

def move_toward(pos,target,speed):
    dx=target[0]-pos[0]; dy=target[1]-pos[1]
    d=math.sqrt(dx**2+dy**2) or 0.001
    return [round(pos[0]+(dx/d)*speed,2), round(pos[1]+(dy/d)*speed,2)]

def clamp(pos):
    h=WORLD_SIZE/2
    return [max(-h,min(h,pos[0])), max(-h,min(h,pos[1]))]

def now_str(): return "Y%d %s T%d"%(world["year"],world["season"][:3].upper(),world["tick"])

def log(msg, cat="general"):
    ts="[%s]"%now_str()
    world["events"].append({"tick":world["tick"],"message":msg,"time":ts,"category":cat})
    if len(world["events"])>100: world["events"]=world["events"][-100:]
    try:
        with open(LOG_FILE,"a",encoding="utf-8") as f: f.write("%s %s\n"%(ts,msg))
    except Exception: pass
    print("%s %s"%(ts,msg))

def history(msg, importance=1):
    if importance>=4: log_event_research("world",msg,importance)
    world["world_history"].append({
        "tick":world["tick"],"year":world["year"],
        "season":world["season"],"message":msg,"importance":importance
    })
    if len(world["world_history"])>1000:
        world["world_history"].sort(key=lambda x:x["importance"],reverse=True)
        world["world_history"]=world["world_history"][:800]

def sound(event):
    world["sound_queue"].append({"event":event,"tick":world["tick"]})
    if len(world["sound_queue"])>20: world["sound_queue"]=world["sound_queue"][-20:]

def diplo_key(a,b): return "%s:%s"%(min(a,b),max(a,b))
def get_diplo(a,b): return world["diplomacy"].get(diplo_key(a,b),"neutral")
def set_diplo(a,b,s): world["diplomacy"][diplo_key(a,b)]=s

def faction_agents(f): return [a for a in world["agents"] if a.get("faction")==f and a["alive"]]
def living(): return [a for a in world["agents"] if a["alive"]]

# BIOME SYSTEM
def generate_biomes():
    biomes=[]
    grid_size=8
    cell=WORLD_SIZE/grid_size
    blist=list(BIOME_TYPES.keys())
    for gx in range(grid_size):
        for gy in range(grid_size):
            x=-WORLD_SIZE/2+gx*cell+cell/2
            y=-WORLD_SIZE/2+gy*cell+cell/2
            # edges are more likely ocean/tundra, center is plains/forest
            dist_center=math.sqrt(x**2+y**2)
            if dist_center>30:
                btype=random.choice(["tundra","ocean","desert","mountain"])
            elif dist_center>15:
                btype=random.choice(["forest","plains","swamp","desert","mountain"])
            else:
                btype=random.choice(["plains","plains","forest","plains","swamp"])
            biomes.append({"x":round(x,1),"y":round(y,1),"type":btype,"cell":round(cell,1)})
    return biomes

def get_biome(pos):
    if not world["biome_map"]: return "plains"
    best=None; bd=999
    for b in world["biome_map"]:
        d=dist([pos[0],pos[1]],[b["x"],b["y"]])
        if d<bd: bd=d; best=b
    return best["type"] if best else "plains"

def biome_modifier(pos, mod):
    btype=get_biome(pos)
    return BIOME_TYPES.get(btype,{}).get(mod,1.0)

# MEMORY SYSTEM
def remember(agent, mtype, content, importance=1):
    agent["memories"].append({
        "type":mtype,"content":content,"tick":world["tick"],
        "year":world["year"],"season":world["season"],"importance":importance
    })
    if len(agent["memories"])>MAX_MEMORY:
        agent["memories"].sort(key=lambda x:(x["importance"],x["tick"]),reverse=True)
        agent["memories"]=agent["memories"][:MAX_MEMORY]

def recall(agent, mtype): return [m for m in agent["memories"] if m["type"]==mtype]
def has_mem(agent,mtype,kw): return any(kw.lower() in m["content"].lower() for m in agent["memories"] if m["type"]==mtype)

def top_mem(agent,n=3):
    ms=sorted(agent["memories"],key=lambda m:(m["importance"],m["tick"]),reverse=True)
    return " | ".join(m["content"] for m in ms[:n]) if ms else "No memories yet."

def personality(agent, trait):
    score=50
    for m in agent["memories"]:
        t=m["type"]
        if t=="battle":
            if trait=="aggression": score+=3
        if t=="trauma":
            if trait=="aggression": score-=5
            if trait=="caution": score+=8
        if t=="friend":
            if trait=="trust": score+=4
        if t=="betrayal":
            if trait=="trust": score-=10
        if t=="discovery":
            if trait=="curiosity": score+=3
        if t=="loss":
            if trait=="caution": score+=2
    return max(0,min(100,score))

def memory_hint(agent):
    battles=recall(agent,"battle"); traumas=recall(agent,"trauma")
    friends=recall(agent,"friend"); discos=recall(agent,"discovery")
    builds=recall(agent,"built");   betrayals=recall(agent,"betrayal")
    aggr=personality(agent,"aggression"); caut=personality(agent,"caution")
    curi=personality(agent,"curiosity"); trust=personality(agent,"trust")
    if agent["type"] in ("warrior","assassin") and aggr>65 and random.random()<0.5: return "hunt"
    if caut>75 and random.random()<0.5: return "hide"
    if curi>70 and len(discos)>=2 and random.random()<0.4: return "deep_explore"
    if betrayals and trust<30 and random.random()<0.4: return "seek_revenge"
    if builds and random.random()<0.3: return "revisit_build"
    if friends and trust>60 and random.random()<0.35: return "seek_friend"
    return None

# CONVERSATION SYSTEM
def agents_converse(agent_a, agent_b):
    key1=(agent_a["type"],agent_b["type"])
    key2=(agent_b["type"],agent_a["type"])
    templates=CONVERSATION_TEMPLATES.get(key1,
               CONVERSATION_TEMPLATES.get(key2,
               DEFAULT_CONVERSATIONS))
    template=random.choice(templates)
    msg=template.replace("{a}",agent_a["name"])\
                 .replace("{b}",agent_b["name"])\
                 .replace("{faction}",agent_a.get("faction","the realm"))
    conv={
        "tick":world["tick"],"year":world["year"],
        "speaker_a":agent_a["name"],"speaker_b":agent_b["name"],
        "type_a":agent_a["type"],"type_b":agent_b["type"],
        "faction_a":agent_a.get("faction","?"),
        "faction_b":agent_b.get("faction","?"),
        "message":msg,
    }
    world["conversations"].append(conv)
    if len(world["conversations"])>60: world["conversations"]=world["conversations"][-60:]
    world["stats"]["conversations"]=world["stats"].get("conversations",0)+1
    remember(agent_a,"person","Spoke with %s (%s) in Y%d"%(agent_b["name"],agent_b["type"],world["year"]),importance=1)
    remember(agent_b,"person","Spoke with %s (%s) in Y%d"%(agent_a["name"],agent_a["type"],world["year"]),importance=1)
    log("   %s"%msg,"conversation")

# GRAVEYARD SYSTEM
def bury_agent(agent, cause):
    battles=len(recall(agent,"battle"))
    builds=len(recall(agent,"built"))
    discos=len(recall(agent,"discovery"))
    friends=len(recall(agent,"friend"))

    if agent.get("is_legend"):
        epitaph="A legend who %s."%agent.get("legend_reason","lived greatly")
    elif battles>=5:
        epitaph="A fierce warrior who fought %d battles."%battles
    elif builds>=5:
        epitaph="A master builder who constructed %d structures."%builds
    elif discos>=5:
        epitaph="A great explorer who made %d discoveries."%discos
    elif friends>=5:
        epitaph="A beloved soul, friend to %d people."%friends
    elif agent["age"]>300:
        epitaph="An elder who lived to the age of %d."%agent["age"]
    else:
        epitaph="They lived, they struggled, they were remembered."

    # Final letter for legends or long-lived agents
    final_letter = ""
    if agent.get("is_legend") or agent.get("age",0)>300:
        final_letter = generate_final_letter(agent)
        log("FINAL LETTER from %s: %s"%(agent["name"],final_letter),"death")

    record={
        "name":agent["name"],"type":agent["type"],
        "faction":agent.get("faction","?"),
        "age":agent["age"],"born_year":agent.get("born_year",1),
        "died_year":world["year"],"died_season":world["season"],
        "cause":cause,"epitaph":epitaph,
        "memory_count":len(agent["memories"]),
        "is_legend":agent.get("is_legend",False),
        "is_immortal":agent.get("is_immortal",False),
        "parent_a":agent.get("parent_a"),
        "parent_b":agent.get("parent_b"),
        "battles":battles,"builds":builds,"discoveries":discos,
        "life_goal":agent.get("life_goal",""),
        "goal_achieved":agent.get("goal_achieved",False),
        "goal_reason":agent.get("goal_reason",""),
        "final_letter":final_letter,
        "emotion":agent.get("emotion","content"),
        "voice":agent.get("voice",""),
    }
    world["graveyard"].append(record)
    if len(world["graveyard"])>200: world["graveyard"]=world["graveyard"][-200:]
    return record

# LINEAGE SYSTEM
def register_lineage(child, parent_a, parent_b):
    cid=child["id"]; aid=parent_a["id"]; bid=parent_b["id"]
    world["lineage"][cid]={"parent_a":aid,"parent_b":bid,
                           "name_a":parent_a["name"],"name_b":parent_b["name"],
                           "born_year":world["year"]}
    # Dynasty tracking — if parent was a legend, child carries the legacy
    if parent_a.get("is_legend") or parent_b.get("is_legend"):
        legend_parent=parent_a if parent_a.get("is_legend") else parent_b
        child["dynasty"]=legend_parent["name"]
        child["name"]=child["name"].split()[0]+" "+legend_parent["name"].split()[1]
        log("Dynasty: %s carries on the bloodline of legend %s!"%(child["name"],legend_parent["name"]),"legend")
        history("The dynasty of %s continues through %s"%(legend_parent["name"],child["name"]),importance=4)

# GENETICS
def inherit_traits(pa, pb):
    pool=list(set(pa.get("traits",[])+pb.get("traits",[])))
    n=random.randint(1,3)
    inherited=random.sample(pool,min(n,len(pool))) if pool else []
    if random.random()<0.25 and TRAITS:
        new=[t for t in TRAITS if t not in inherited]
        if new: inherited.append(random.choice(new))
    return inherited

def inherit_type(pa, pb):
    r=random.random()
    if r<0.4: return pa["type"]
    if r<0.8: return pb["type"]
    return random.choice(list(AGENT_TYPES.keys()))

# WIN CONDITIONS
def check_win_conditions():
    if world.get("winner"): return
    # Win conditions only check after tick 300 — ensures all configs run
    # for a comparable duration before victory can be declared.
    if world["tick"] < 300: return

    flist=list(FACTIONS.keys())
    total_buildings=len(world["buildings"])
    total_agents=len(living())
    all_powers = [world["faction_power"].get(f, 0) for f in flist]
    max_power  = max(all_powers) if all_powers else 0

    for faction in flist:
        fa=faction_agents(faction)
        fb=[b for b in world["buildings"] if b.get("faction")==faction]
        ft=world["faction_tech"][faction]
        fp=world["faction_power"].get(faction, 0)

        # Conquest: own 70% of buildings AND be the dominant power
        if (total_buildings>10 and len(fb)/total_buildings>=0.70
                and fp >= max_power * 0.8):
            declare_winner(faction,"conquest","controls 70% of all structures")

        # Wealth: Goldveil must be power-dominant + world gold very high
        world_gold = world["resources"].get("gold", 0)
        if (faction == "Goldveil" and len(fa) >= 5 and
                world_gold >= 800 and fp >= max_power * 0.8):
            declare_winner(faction, "wealth", "amassed great fortune")

        # Faith: 75% of agents faithful AND Greenveil is dominant
        if total_agents > 5:
            faithful = sum(1 for a in living() if a.get("faith",0) > 5)
            if (faction == "Greenveil" and
                    faithful/total_agents >= 0.75 and fp >= max_power * 0.7):
                declare_winner(faction,"faith","converted most souls to their faith")

        # Knowledge: researched ALL tech AND has the most tech of any faction
        my_tech = len(ft.get("researched",[]))
        if (my_tech >= len(TECH_TREE) and
                my_tech >= max(len(world["faction_tech"][f].get("researched",[]))
                               for f in flist)):
            declare_winner(faction,"knowledge","mastered all known technologies")

def declare_winner(faction, win_type, reason):
    world["winner"]={"faction":faction,"type":win_type,"reason":reason,
                     "year":world["year"],"tick":world["tick"]}
    sym=FACTIONS[faction]["symbol"]
    history("VICTORY: %s wins by %s — %s"%(faction,win_type,reason),importance=5)
    log("VICTORY: %s%s wins by %s! %s"%(sym,faction,win_type,reason),"victory")
    sound("victory")
    # Don't stop the world — let it keep running after victory

# DISEASE
def tick_diseases():
    for disease in world["diseases"][:]:
        for agent in living():
            if agent.get("disease"): continue
            for other in living():
                if (other.get("disease")==disease["name"] and
                    dist(agent["position"],other["position"])<6 and
                    random.random()<0.07):
                    agent["disease"]=disease["name"]
                    agent["disease_ticks"]=0
                    remember(agent,"trauma","Contracted %s Y%d"%(disease["name"],world["year"]),importance=3)
                    break
        for agent in living():
            if agent.get("disease")==disease["name"]:
                agent["disease_ticks"]=agent.get("disease_ticks",0)+1
                agent["health"]=max(0,agent.get("health",100)-2)
                if agent["disease_ticks"]>30:
                    if random.random()<0.3:
                        agent["disease"]=None; agent["disease_ticks"]=0
                        remember(agent,"joy","Survived %s Y%d"%(disease["name"],world["year"]),importance=4)
                        log("%s survived %s!"%(agent["name"],disease["name"]),"disease")
                        sound("recovery")
                    elif agent["health"]<=0:
                        bury_agent(agent,"disease:%s"%disease["name"])
                        agent["alive"]=False
                        world["stats"]["total_deaths"]=world["stats"].get("total_deaths",0)+1
                        world["stats"]["disease_deaths"]=world["stats"].get("disease_deaths",0)+1
                        history("%s died of %s"%(agent["name"],disease["name"]),importance=2)
                        log("%s died of %s"%(agent["name"],disease["name"]),"death")
                        sound("death")
        disease["age"]=disease.get("age",0)+1
        if disease["age"]>100:
            world["diseases"].remove(disease)
            world["plague_active"]=len(world["diseases"])>0
            log("%s has burned out"%disease["name"],"disease")
            sound("plague_end")

def spawn_disease():
    name=random.choice(DISEASE_NAMES)
    candidates=living()
    if not candidates: return
    patient=random.choice(candidates)
    patient["disease"]=name; patient["disease_ticks"]=0
    world["diseases"].append({"name":name,"started_tick":world["tick"],"age":0})
    world["plague_active"]=True
    world["stats"]["plagues"]=world["stats"].get("plagues",0)+1
    remember(patient,"trauma","Was patient zero of %s Y%d"%(name,world["year"]),importance=5)
    history("The %s appeared. %s was first to fall."%(name,patient["name"]),importance=4)
    log("PLAGUE: %s has arrived! Patient zero: %s"%(name,patient["name"]),"disease")
    sound("plague")

# TECHNOLOGY
def tick_tech():
    for faction in FACTIONS:
        ft=world["faction_tech"][faction]
        scholars=sum(1 for a in faction_agents(faction) if a["type"]=="scholar")
        ft["points"]=ft.get("points",0)+scholars
        for tech,data in TECH_TREE.items():
            if tech not in ft.get("researched",[]) and ft["points"]>=data["cost"]:
                ft["researched"]=ft.get("researched",[])+[tech]
                ft["points"]-=data["cost"]
                world["stats"]["tech_discovered"]=world["stats"].get("tech_discovered",0)+1
                history("%s discovered %s"%(faction,tech.replace("_"," ")),importance=3)
                log("%s %s discovered %s!"%(FACTIONS[faction]["symbol"],faction,tech.replace("_"," ")),"tech")
                sound("tech")
                if data["bonus"]=="lifespan_plus":
                    for a in faction_agents(faction): a["max_age"]=int(a.get("max_age",300)*1.15)
                if data["bonus"]=="food_double":
                    world["resources"]["food"]=world["resources"].get("food",0)+50

def has_tech(faction, tech):
    return tech in world["faction_tech"].get(faction,{}).get("researched",[])

# WAR & DIPLOMACY
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# AGENT ALIVE SYSTEM — Goals, Emotions, Voice, Letters
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

LIFE_GOALS = {
    "warrior":   ["survive 15 battles","become a legend","avenge a fallen friend","outlive all enemies"],
    "explorer":  ["discover 10 wonders","find the edge of the world","map every biome","become immortal"],
    "builder":   ["build 15 structures","construct a city","build a palace","leave something that lasts forever"],
    "farmer":    ["feed 100 souls","outlive my parents","grow the greatest harvest","die peacefully at home"],
    "scholar":   ["research all 8 technologies","master 6 skills","write the world history","become immortal"],
    "merchant":  ["accumulate 200 gold","forge 5 trade alliances","outlive my rivals","become the wealthiest soul alive"],
    "priest":    ["convert 20 souls","achieve divine faith","become immortal","spread faith to all factions"],
    "spy":       ["uncover 5 secrets","assassinate a legend","betray and survive","never be caught"],
    "healer":    ["save 10 lives","cure a plague","outlive everyone I healed","be remembered as a saint"],
    "assassin":  ["kill 10 enemies","topple a dynasty","become a shadow legend","never be remembered"],
}

EMOTIONS = ["content","curious","grieving","angry","inspired","afraid","lonely","joyful","weary","vengeful","devoted","proud"]

EMOTION_TRIGGERS = {
    "grieving":  lambda a: any(m["type"]=="loss" for m in a["memories"][-5:]),
    "angry":     lambda a: any(m["type"]=="betrayal" for m in a["memories"][-8:]),
    "afraid":    lambda a: a.get("health",100)<35 or any("dark god" in m["content"].lower() for m in a["memories"][-5:]),
    "inspired":  lambda a: a.get("is_legend",False) or len(a.get("skills",[]))>=3,
    "proud":     lambda a: len(recall(a,"built"))>=8 or len(recall(a,"battle"))>=8,
    "devoted":   lambda a: a.get("faith",0)>40,
    "vengeful":  lambda a: any(m["type"]=="betrayal" for m in a["memories"]) and len(recall(a,"battle"))>3,
    "lonely":    lambda a: len(recall(a,"friend"))==0 and a["age"]>100,
    "weary":     lambda a: a["age"]>400,
    "joyful":    lambda a: any(m["type"]=="joy" for m in a["memories"][-3:]),
    "curious":   lambda a: a["type"] in ("explorer","scholar"),
    "content":   lambda a: True,  # fallback
}

EMOTION_EFFECTS = {
    "grieving":  {"health":-0.5, "speed":-0.3},
    "angry":     {"battle_power":3, "speed":0.2},
    "afraid":    {"speed":0.5, "hide_chance":0.3},
    "inspired":  {"knowledge":2, "skill_chance":0.02},
    "proud":     {"build_rate":0.1, "battle_power":2},
    "devoted":   {"faith_gain":2, "heal_power":1},
    "vengeful":  {"battle_power":5, "speed":0.3},
    "lonely":    {"health":-0.2},
    "weary":     {"speed":-0.2},
    "joyful":    {"health":0.3, "speed":0.1},
    "curious":   {"knowledge":1},
    "content":   {},
}

VOICE_TEMPLATES = {
    "warrior": [
        "I am {name} of {faction}. I have fought {battles} battles and will fight many more.",
        "Blood and iron — that is all I know. {battles} enemies have learned to fear my name.",
        "My faction needs warriors. I have given {battles} battles and I am not done yet.",
        "They call me a legend now. But I remember when I was just another soldier.",
    ],
    "explorer": [
        "I have wandered this world for {age} years and found {discoveries} wonders. Still not enough.",
        "Every horizon I cross reveals another. I am {name}. I cannot stop moving.",
        "I have seen {discoveries} things no one else has seen. The world is vast and I am small.",
        "My feet have not rested in years. There is always something more to find.",
    ],
    "builder": [
        "I have raised {builds} structures from nothing. My work outlives me. That is enough.",
        "Stone and timber — my language. {builds} buildings stand because of me.",
        "Long after I am gone, my buildings will stand. That is why I build.",
        "I put {name} into every stone I lay. The world will remember my work if not my name.",
    ],
    "farmer": [
        "The land gives and the land takes. I have worked it for {age} years without complaint.",
        "Simple life, simple joys. My harvest feeds people who will never know my name.",
        "I was born here. I will die here. The earth asks nothing more of me than work.",
        "Every seed I plant is an act of faith. Most of them grow.",
    ],
    "scholar": [
        "Knowledge is the only thing worth accumulating. I have made {discoveries} discoveries.",
        "I have read the engine of this world. I understand things others cannot imagine.",
        "Wisdom comes slowly and leaves quickly. I write everything down so it survives me.",
        "I have {skills} skills mastered. There are more to learn. There are always more.",
    ],
    "merchant": [
        "Gold is just trust made solid. I have earned plenty of both.",
        "Every deal is a story. I have made enough of them to fill a library.",
        "They say merchants have no loyalty. They are wrong. I am loyal to good business.",
        "I have crossed this world looking for the next trade. I have never stopped.",
    ],
    "priest": [
        "Faith is not belief — it is practice. I have practiced for {age} years.",
        "I have converted souls who cursed me first. That is the work.",
        "The divine speaks through me. I try to listen more than I speak.",
        "My faith is {faith}. I have given most of it away to others.",
    ],
    "spy": [
        "I know things about everyone here. Most of them do not know I exist.",
        "The best spy is the one no one suspects. I have never been caught.",
        "Information is power. I have accumulated both quietly and carefully.",
        "I move in shadows because the light reveals too much about me.",
    ],
    "healer": [
        "I have closed wounds that should have been fatal. I take no credit for surviving.",
        "Death comes for everyone. I just slow it down sometimes.",
        "The sick do not remember who healed them. I do not need them to.",
        "I was made to fix things. People are just the most complicated things to fix.",
    ],
    "assassin": [
        "I have ended lives that deserved ending. I do not apologise for my work.",
        "Silence is my weapon. No one hears me coming.",
        "I exist in the spaces between order. Someone has to.",
        "They build legends. I unmake them. The balance must be kept.",
    ],
}

FINAL_LETTERS = {
    "warrior": [
        "To whoever finds this: I lived by the sword and I do not regret it. Fight for something worth fighting for.",
        "I killed men I did not hate and protected men I did not love. That is war. I hope you never know it.",
        "My blade is buried with me. My enemies are all dead. I won. Whatever that means.",
    ],
    "explorer": [
        "I never saw everything I wanted to see. Go further than I did. The world is bigger than you think.",
        "To whoever finds this: keep moving. The moment you stop is the moment the world shrinks.",
        "I found {discoveries} wonders in this life. There are more. I wish I had time for them.",
    ],
    "builder": [
        "Look around you. Some of what you see, I built. That was enough for me.",
        "I built {builds} things. None of them as beautiful as what I imagined. Build anyway.",
        "Stone outlasts flesh. I am proof of that. My buildings will still stand long after you read this.",
    ],
    "farmer": [
        "The land was here before me and will be here after. Treat it accordingly.",
        "I grew enough food to feed hundreds. No one will write songs about that. That is fine.",
        "Simple work, honestly done, is its own reward. I learned that late. You should learn it early.",
    ],
    "scholar": [
        "I have made {discoveries} discoveries in this world. Most of them were wrong at first. Keep asking questions.",
        "The greatest thing I ever learned was how much I did not know. Start there.",
        "I read the engine of the world itself. It is more beautiful and more terrifying than anything I imagined.",
    ],
    "merchant": [
        "Every deal I ever made started with trust. Build yours carefully.",
        "Wealth is just stored time. I spent mine well. I hope you spend yours better.",
        "I crossed this world for gold and found something more valuable. I just cannot remember what it was.",
    ],
    "priest": [
        "Faith carried me {age} years. I give it to you now. Use it gently.",
        "I did not know if any god was listening. I prayed anyway. It helped.",
        "The divine is not in temples. It is in the spaces between people who care for each other.",
    ],
    "spy": [
        "You never knew I existed. That was the point. I was here.",
        "I knew every secret in this world and took them all to the grave. You are welcome.",
        "The best work leaves no trace. This letter is an indulgence. Forget you read it.",
    ],
    "healer": [
        "I spent my life making sure others got to live theirs. I would do it again.",
        "Death took everyone I healed eventually. I just gave them more time. Time is everything.",
        "Be kind to healers. We see the worst of what the world does to people and keep showing up.",
    ],
    "assassin": [
        "I was never here.",
        "Do not mourn me. I was exactly what this world needed me to be.",
        "I have ended many lives. I hope the tally was worth it. I think it was.",
    ],
}

def assign_life_goal(agent):
    """Give a newly created agent a secret personal goal."""
    atype = agent["type"]
    goals = LIFE_GOALS.get(atype, ["live a good life","be remembered","outlive everyone"])
    agent["life_goal"] = random.choice(goals)
    agent["goal_achieved"] = False

def update_emotion(agent):
    """Update agent emotional state based on memories and situation."""
    for emotion, trigger in EMOTION_TRIGGERS.items():
        try:
            if trigger(agent):
                agent["emotion"] = emotion
                return
        except Exception:
            continue
    agent["emotion"] = "content"

def apply_emotion_effects(agent):
    """Emotions have real mechanical effects on agent stats."""
    emotion = agent.get("emotion","content")
    effects = EMOTION_EFFECTS.get(emotion,{})
    if "health" in effects:
        agent["health"] = max(1, min(150, agent.get("health",100) + effects["health"]))
    if "speed" in effects:
        pass  # applied inline in think
    if emotion == "grieving" and random.random()<0.01:
        agent["emotion"] = "weary"  # grief becomes weariness over time
    if emotion == "angry" and len(recall(agent,"battle"))>15:
        agent["emotion"] = "weary"  # exhausted by constant anger

def generate_voice(agent):
    """Generate the agent's inner monologue based on their life."""
    atype = agent["type"]
    templates = VOICE_TEMPLATES.get(atype, ["I am {name}. I exist. That is enough."])
    tmpl = random.choice(templates)
    voice = tmpl.replace("{name}", agent["name"])                .replace("{faction}", agent.get("faction","the realm"))                .replace("{age}", str(agent.get("age",0)))                .replace("{battles}", str(len(recall(agent,"battle"))))                .replace("{discoveries}", str(len(recall(agent,"discovery"))))                .replace("{builds}", str(len(recall(agent,"built"))))                .replace("{skills}", str(len(agent.get("skills",[]))))                .replace("{faith}", str(int(agent.get("faith",0))))
    agent["voice"] = voice
    return voice

def check_goal_achieved(agent):
    """Check if agent has achieved their life goal."""
    if agent.get("goal_achieved"): return
    goal = agent.get("life_goal","")
    achieved = False
    reason = ""

    if "battles" in goal:
        n = int(''.join(c for c in goal if c.isdigit()) or "10")
        if len(recall(agent,"battle")) >= n:
            achieved = True; reason = "survived %d battles"%len(recall(agent,"battle"))
    elif "discover" in goal or "wonder" in goal:
        n = int(''.join(c for c in goal if c.isdigit()) or "8")
        if len(recall(agent,"discovery")) >= n:
            achieved = True; reason = "found %d wonders"%len(recall(agent,"discovery"))
    elif "build" in goal or "struct" in goal:
        n = int(''.join(c for c in goal if c.isdigit()) or "10")
        if len(recall(agent,"built")) >= n:
            achieved = True; reason = "built %d structures"%len(recall(agent,"built"))
    elif "legend" in goal and "immortal" not in goal:
        if agent.get("is_legend"): achieved = True; reason = "became a legend"
    elif "immortal" in goal:
        if agent.get("is_immortal"): achieved = True; reason = "achieved immortality"
    elif "faith" in goal:
        if agent.get("faith",0) > 60: achieved = True; reason = "achieved divine faith"
    elif "skill" in goal:
        n = int(''.join(c for c in goal if c.isdigit()) or "5")
        if len(agent.get("skills",[])) >= n:
            achieved = True; reason = "mastered %d skills"%len(agent.get("skills",[]))
    elif "gold" in goal:
        if world["resources"].get("gold",0) > 150:
            achieved = True; reason = "helped accumulate great wealth"
    elif "outlive" in goal:
        if agent["age"] > 400: achieved = True; reason = "outlived nearly everyone"

    if achieved:
        agent["goal_achieved"] = True
        agent["goal_reason"] = reason
        remember(agent,"joy","LIFE GOAL ACHIEVED: %s — %s Y%d"%(goal,reason,world["year"]),importance=5)
        agent["health"] = min(150, agent.get("health",100)+10)
        agent["emotion"] = "joyful"
        log("GOAL ACHIEVED: %s (%s) — %s"%(agent["name"],agent["type"],reason),"achievement")
        history("%s achieved their life goal: %s"%(agent["name"],reason),importance=3)
        world["stats"]["goals_achieved"] = world["stats"].get("goals_achieved",0)+1

def generate_final_letter(agent):
    """Generate a final letter from a dying legend or long-lived agent."""
    atype = agent["type"]
    letters = FINAL_LETTERS.get(atype,["I was here. I mattered. Goodbye."])
    letter = random.choice(letters)
    letter = letter.replace("{name}", agent["name"])                   .replace("{age}", str(agent.get("age",0)))                   .replace("{discoveries}", str(len(recall(agent,"discovery"))))                   .replace("{builds}", str(len(recall(agent,"built"))))                   .replace("{faction}", agent.get("faction","the realm"))
    # Add personal note if goal was not achieved
    if not agent.get("goal_achieved") and agent.get("life_goal"):
        letter += " My one regret: I never managed to %s."%agent["life_goal"]
    return letter


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# COGNITIVE ARCHITECTURE
# Four deep systems that make agents genuinely think:
#   1. SELF-MODEL       — agent's representation of itself (can be wrong)
#   2. BELIEF REVISION  — beliefs updated by evidence, can be shattered
#   3. GOAL ORIGINATION — goals born from experience, not assignment
#   4. ABSTRACTION XFER — concepts learned in one domain applied to another
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

# ──────────────────────────────────────────────────────────────────
# 1. INTERNAL SELF-MODEL
# Each agent maintains beliefs about ITSELF that can be accurate or
# deluded. Self-model updates slowly from experience.
# ──────────────────────────────────────────────────────────────────

def init_self_model(agent):
    """Create an agent's initial self-model — mostly optimistic and naive."""
    atype = agent["type"]
    # Self-perceived strengths (0-100), starts overconfident
    agent["self_model"] = {
        "perceived_strength":    random.randint(55, 80),
        "perceived_wisdom":      random.randint(45, 75),
        "perceived_influence":   random.randint(40, 70),
        "perceived_courage":     random.randint(50, 80),
        "self_worth":            random.randint(50, 80),  # how much they value themselves
        "social_standing":       random.randint(30, 60),  # what they think others think
        "role_confidence":       random.randint(60, 90),  # confidence in their role
        "world_understanding":   random.randint(20, 50),  # how well they think they understand the world
        "identity_stability":    random.randint(60, 90),  # how stable their sense of self is
        # Narrative self-identity — what they call themselves
        "self_label": {
            "warrior":  random.choice(["a fighter","a protector","a blade in the dark","a soldier"]),
            "explorer": random.choice(["a wanderer","a seeker","a discoverer","a horizon-chaser"]),
            "builder":  random.choice(["a maker","a craftsman","a founder","a builder of worlds"]),
            "farmer":   random.choice(["a provider","a keeper of the land","a grower","a nurturer"]),
            "scholar":  random.choice(["a thinker","a seeker of truth","a reader of the world","a mind"]),
            "merchant": random.choice(["a trader","a dealmaker","a connector","a wealth-builder"]),
            "priest":   random.choice(["a vessel of faith","a speaker for the divine","a shepherd","a believer"]),
            "spy":      random.choice(["a shadow","a watcher","a keeper of secrets","an unseen hand"]),
            "healer":   random.choice(["a mender","a restorer","a keeper of life","a fixer"]),
            "assassin": random.choice(["an instrument","a necessary darkness","a balance-keeper","a ghost"]),
        }.get(atype, "a soul in this world"),
        # What they think their purpose is
        "perceived_purpose": {
            "warrior":  "to protect my faction through strength",
            "explorer": "to expand what is known",
            "builder":  "to leave something lasting",
            "farmer":   "to sustain those around me",
            "scholar":  "to understand the mechanisms of existence",
            "merchant": "to create connections and prosperity",
            "priest":   "to bring others closer to the divine",
            "spy":      "to see what others cannot",
            "healer":   "to preserve life",
            "assassin": "to remove what must be removed",
        }.get(atype, "to survive and find meaning"),
    }

def update_self_model(agent):
    """Revise self-model based on actual performance — reality correction."""
    sm = agent.get("self_model")
    if not sm: return

    battles  = len(recall(agent,"battle"))
    wins     = sum(1 for m in recall(agent,"battle") if "won" in m["content"].lower() or "survived" in m["content"].lower())
    losses   = battles - wins
    discos   = len(recall(agent,"discovery"))
    builds   = len(recall(agent,"built"))
    traumas  = len(recall(agent,"trauma"))
    friends  = len(recall(agent,"friend"))
    betrayals= len(recall(agent,"betrayal"))
    skills   = len(agent.get("skills",[]))
    age      = agent.get("age",0)

    # Strength: revised by battle outcomes
    if battles > 0:
        win_rate = wins / battles
        actual_strength = int(win_rate * 80 + 20)
        # Self-model adjusts SLOWLY toward reality (resistance to change)
        sm["perceived_strength"] += (actual_strength - sm["perceived_strength"]) * 0.05
        sm["perceived_strength"] = max(5, min(100, int(sm["perceived_strength"])))

    # Wisdom: revised by discoveries and age
    actual_wisdom = min(100, discos * 5 + skills * 8 + age // 20)
    sm["perceived_wisdom"] += (actual_wisdom - sm["perceived_wisdom"]) * 0.03
    sm["perceived_wisdom"] = max(5, min(100, int(sm["perceived_wisdom"])))

    # Social standing: revised by friends and betrayals
    actual_social = min(100, friends * 10 - betrayals * 15 + (20 if agent.get("is_legend") else 0))
    sm["social_standing"] += (actual_social - sm["social_standing"]) * 0.04
    sm["social_standing"] = max(0, min(100, int(sm["social_standing"])))

    # Self-worth: traumatic events crush it, achievements restore it
    if traumas > 3:
        sm["self_worth"] = max(10, sm["self_worth"] - traumas * 2)
    if agent.get("goal_achieved"):
        sm["self_worth"] = min(100, sm["self_worth"] + 15)
    if agent.get("is_legend"):
        sm["self_worth"] = min(100, sm["self_worth"] + 20)
        sm["social_standing"] = min(100, sm["social_standing"] + 30)
        sm["self_label"] = "a legend of %s" % agent.get("faction","the world")
        sm["perceived_purpose"] = "to be remembered as one of the great ones"

    # Identity crisis: if self-worth very low, identity_stability drops
    if sm["self_worth"] < 25:
        sm["identity_stability"] = max(0, sm["identity_stability"] - 5)
        if sm["identity_stability"] < 20 and random.random() < 0.1:
            # Identity crisis — agent questions its purpose
            remember(agent, "trauma",
                "I no longer know what I am. Everything I believed about myself may be wrong. Y%d" % world["year"],
                importance=5)
            agent["emotion"] = "afraid"
            log("IDENTITY CRISIS: %s (%s) has lost their sense of self!" % (agent["name"], agent["type"]), "cognition")
            history("%s (%s) suffered an identity crisis in Y%d" % (agent["name"], agent["type"], world["year"]), importance=3)

    # Rebuild identity after crisis if things improve
    if sm["identity_stability"] < 40 and sm["self_worth"] > 60:
        sm["identity_stability"] = min(100, sm["identity_stability"] + 10)
        remember(agent, "joy",
            "I found myself again. I am %s. I know my purpose. Y%d" % (sm["self_label"], world["year"]),
            importance=4)

    # World understanding grows with age and discovery
    sm["world_understanding"] = min(100, discos * 3 + age // 30 + skills * 5)


# ──────────────────────────────────────────────────────────────────
# 2. BELIEF REVISION LOGIC
# Agents hold explicit beliefs about the world. Each belief has
# confidence 0-100. When evidence contradicts a belief, confidence
# drops. When it falls to 0, the belief is revised or abandoned.
# ──────────────────────────────────────────────────────────────────

def init_beliefs(agent):
    """Seed an agent's starting beliefs based on faction and type."""
    faction = agent.get("faction","?")
    atype   = agent["type"]
    agent["beliefs"] = {
        # Beliefs about the world
        "world_is_safe":        {"confidence": 60, "value": True,  "source": "upbringing"},
        "faith_protects":       {"confidence": 50 if faction=="Greenveil" else 25, "value": True,  "source": "culture"},
        "strength_wins":        {"confidence": 70 if atype=="warrior" else 35, "value": True,  "source": "instinct"},
        "knowledge_is_power":   {"confidence": 70 if atype=="scholar" else 40, "value": True,  "source": "culture"},
        "my_faction_is_just":   {"confidence": 75, "value": True,  "source": "loyalty"},
        "outsiders_are_danger": {"confidence": 50 if faction=="Ironveil" else 25, "value": True,  "source": "instinct"},
        "cooperation_works":    {"confidence": 60 if faction=="Greenveil" else 40, "value": True,  "source": "observation"},
        "death_has_meaning":    {"confidence": 55, "value": True,  "source": "culture"},
        "i_can_change_things":  {"confidence": 65, "value": True,  "source": "youth"},
        "the_divine_exists":    {"confidence": 70 if faction=="Greenveil" else 30, "value": True,  "source": "faith"},
    }

def revise_beliefs(agent):
    """Update beliefs based on recent memories — the core of rational agency."""
    if "beliefs" not in agent:
        init_beliefs(agent)
        return

    b = agent["beliefs"]
    recent = agent["memories"][-8:] if agent["memories"] else []

    for mem in recent:
        mtype   = mem["type"]
        content = mem["content"].lower()

        # Evidence against "world_is_safe"
        if mtype in ("battle","trauma","loss"):
            b["world_is_safe"]["confidence"] = max(0, b["world_is_safe"]["confidence"] - 8)
        if mtype == "joy" or "peace" in content:
            b["world_is_safe"]["confidence"] = min(100, b["world_is_safe"]["confidence"] + 3)

        # Evidence for/against "faith_protects"
        if "converted" in content or "faith" in content:
            b["faith_protects"]["confidence"] = min(100, b["faith_protects"]["confidence"] + 5)
        if "plague" in content or "died" in content or mtype == "trauma":
            b["faith_protects"]["confidence"] = max(0, b["faith_protects"]["confidence"] - 6)

        # Evidence for/against "strength_wins"
        if mtype == "battle" and ("won" in content or "survived" in content):
            b["strength_wins"]["confidence"] = min(100, b["strength_wins"]["confidence"] + 8)
        if mtype == "battle" and ("lost" in content or "defeated" in content or "death" in content):
            b["strength_wins"]["confidence"] = max(0, b["strength_wins"]["confidence"] - 10)

        # Evidence for/against "cooperation_works"
        if mtype == "friend" or "alliance" in content or "allied" in content:
            b["cooperation_works"]["confidence"] = min(100, b["cooperation_works"]["confidence"] + 6)
        if mtype == "betrayal" or "betrayed" in content:
            b["cooperation_works"]["confidence"] = max(0, b["cooperation_works"]["confidence"] - 20)
            b["my_faction_is_just"]["confidence"] = max(0, b["my_faction_is_just"]["confidence"] - 10)

        # Evidence for/against "my_faction_is_just"
        if "victory" in content or "won war" in content:
            b["my_faction_is_just"]["confidence"] = min(100, b["my_faction_is_just"]["confidence"] + 5)
        if "war" in content and mtype == "trauma":
            b["my_faction_is_just"]["confidence"] = max(0, b["my_faction_is_just"]["confidence"] - 8)

        # Evidence for "knowledge_is_power"
        if mtype in ("discovery",) or "discovered" in content:
            b["knowledge_is_power"]["confidence"] = min(100, b["knowledge_is_power"]["confidence"] + 5)

        # Evidence for/against "the_divine_exists"
        if "dark god" in content:
            b["the_divine_exists"]["confidence"] = min(100, b["the_divine_exists"]["confidence"] + 15)
        if mtype == "trauma" and agent.get("faith",0) > 20:
            b["the_divine_exists"]["confidence"] = max(0, b["the_divine_exists"]["confidence"] - 8)

        # "i_can_change_things" — crushed by failure, restored by achievement
        if mtype == "trauma" or "failed" in content:
            b["i_can_change_things"]["confidence"] = max(0, b["i_can_change_things"]["confidence"] - 5)
        if agent.get("goal_achieved") or agent.get("is_legend"):
            b["i_can_change_things"]["confidence"] = min(100, b["i_can_change_things"]["confidence"] + 15)

    # ── BELIEF COLLAPSE: when confidence hits 0, belief reverses ──
    reversals = {
        "world_is_safe":     ("world_is_dangerous", "trauma",
            "The world is not safe. It never was. I understand that now. Y%d"),
        "faith_protects":    ("faith_is_illusion", "discovery",
            "I have prayed. I have suffered anyway. Faith does not protect. Y%d"),
        "strength_wins":     ("strength_is_not_enough", "discovery",
            "I have fought hard. I have still lost. Strength alone is a lie. Y%d"),
        "cooperation_works": ("trust_no_one", "betrayal",
            "I trusted. I was betrayed. I will not make that mistake again. Y%d"),
        "my_faction_is_just":("my_faction_is_flawed", "discovery",
            "I have seen what my faction does. Justice is not their concern. Y%d"),
        "the_divine_exists": ("the_divine_is_silent", "discovery",
            "I looked for the divine. I found only silence and suffering. Y%d"),
        "i_can_change_things":("i_am_powerless", "trauma",
            "Everything I have tried has made no difference. I am nothing. Y%d"),
    }

    for belief_key, (new_label, mem_type, template) in reversals.items():
        if belief_key in b and b[belief_key]["confidence"] == 0 and b[belief_key]["value"] != False:
            b[belief_key]["value"]      = False
            b[belief_key]["confidence"] = 40  # reset with low confidence in new belief
            b[belief_key]["source"]     = "experience"
            content = template % world["year"]
            remember(agent, mem_type, content, importance=5)
            agent["emotion"] = "angry" if "strength" in belief_key else "afraid"
            log("BELIEF SHATTERED: %s (%s) — %s" % (agent["name"], agent["type"], new_label), "cognition")
            log_belief_collapse_research(agent, belief_key, new_label)
            log_event_research("cognition","BELIEF SHATTERED: %s (%s) — %s"%(agent["name"],agent["type"],new_label),4)
            history("%s's belief was shattered: %s Y%d" % (agent["name"], new_label, world["year"]), importance=3)
            world["stats"]["beliefs_shattered"] = world["stats"].get("beliefs_shattered", 0) + 1

    # Store a readable summary of current beliefs
    agent["belief_summary"] = "; ".join(
        "%s(%d)" % (k.replace("_"," "), v["confidence"])
        for k, v in b.items()
        if v["confidence"] < 30 or v["confidence"] > 70  # only notable beliefs
    )


# ──────────────────────────────────────────────────────────────────
# 3. TRUE GOAL ORIGINATION
# Goals are not assigned — they EMERGE from what the agent has
# experienced. An agent who saw something beautiful wants more of it.
# An agent who suffered wants to prevent it in others. Goals can
# conflict, evolve, and be abandoned.
# ──────────────────────────────────────────────────────────────────

def originate_goals(agent):
    """Derive new personal goals from the agent's actual experiences."""
    if "originated_goals" not in agent:
        agent["originated_goals"] = []

    memories = agent["memories"]
    existing = [g["goal"] for g in agent["originated_goals"]]
    beliefs  = agent.get("beliefs", {})
    sm       = agent.get("self_model", {})
    atype    = agent["type"]
    faction  = agent.get("faction","?")

    new_goals = []

    # ── REVENGE GOAL: from betrayal ──
    betrayals = recall(agent,"betrayal")
    if betrayals and "avenge the betrayal" not in existing:
        betrayer = betrayals[-1]["content"]
        new_goals.append({
            "goal":     "avenge the betrayal",
            "origin":   "witnessed betrayal — %s" % betrayer[:40],
            "priority": 8,
            "type":     "revenge",
            "active":   True,
            "born_year": world["year"],
        })
        remember(agent, "discovery",
            "I have decided: I will have my revenge for what was done. Y%d" % world["year"], importance=4)

    # ── PROTECTION GOAL: from loss of a friend ──
    losses = [m for m in recall(agent,"loss") if "friend" in m["content"].lower() or "ally" in m["content"].lower()]
    if losses and "protect those I care about" not in existing:
        new_goals.append({
            "goal":     "protect those I care about",
            "origin":   "lost someone — %s" % losses[-1]["content"][:40],
            "priority": 7,
            "type":     "protection",
            "active":   True,
            "born_year": world["year"],
        })
        remember(agent, "discovery",
            "I will not let another person I care about die if I can prevent it. Y%d" % world["year"], importance=4)

    # ── DOUBT GOAL: from belief collapse ──
    if beliefs.get("faith_protects",{}).get("value") == False and        "understand why faith failed me" not in existing:
        new_goals.append({
            "goal":     "understand why faith failed me",
            "origin":   "faith belief was shattered",
            "priority": 6,
            "type":     "understanding",
            "active":   True,
            "born_year": world["year"],
        })
        remember(agent, "discovery",
            "I need to understand why the divine abandoned me. There must be a reason. Y%d" % world["year"], importance=4)

    # ── LEGACY GOAL: from witnessing a legend die ──
    grave_legends = [g for g in world.get("graveyard",[])[-5:] if g.get("is_legend")]
    if grave_legends and "leave a legacy that outlasts me" not in existing and agent["age"] > 50:
        new_goals.append({
            "goal":     "leave a legacy that outlasts me",
            "origin":   "witnessed legend %s die — wanted to be remembered too" % grave_legends[-1]["name"],
            "priority": 7,
            "type":     "legacy",
            "active":   True,
            "born_year": world["year"],
        })
        remember(agent, "discovery",
            "When %s died I understood — I want something to remain after I am gone. Y%d" % (grave_legends[-1]["name"], world["year"]), importance=4)

    # ── WAR WEARINESS GOAL: too many battles ──
    battle_traumas = [m for m in recall(agent,"trauma") if "war" in m["content"].lower() or "battle" in m["content"].lower()]
    if len(battle_traumas) > 3 and "find an end to the fighting" not in existing:
        new_goals.append({
            "goal":     "find an end to the fighting",
            "origin":   "too many battle traumas — war weariness",
            "priority": 6,
            "type":     "peace",
            "active":   True,
            "born_year": world["year"],
        })
        remember(agent, "discovery",
            "I am tired of blood. There must be another way. I will seek it. Y%d" % world["year"], importance=4)

    # ── IDENTITY QUEST: after identity crisis ──
    if sm.get("identity_stability",100) < 25 and "rediscover who I am" not in existing:
        new_goals.append({
            "goal":     "rediscover who I am",
            "origin":   "identity crisis — lost sense of self",
            "priority": 9,
            "type":     "identity",
            "active":   True,
            "born_year": world["year"],
        })
        remember(agent, "discovery",
            "I do not know what I am anymore. I must find out before I die. Y%d" % world["year"], importance=5)

    # ── KNOWLEDGE HUNGER: from high world understanding ──
    if sm.get("world_understanding",0) > 70 and atype == "scholar" and        "understand the engine of this world completely" not in existing:
        new_goals.append({
            "goal":     "understand the engine of this world completely",
            "origin":   "accumulated enough knowledge to sense greater patterns",
            "priority": 8,
            "type":     "mastery",
            "active":   True,
            "born_year": world["year"],
        })
        remember(agent, "discovery",
            "I have learned enough to know there is a deeper pattern to everything. I will find it. Y%d" % world["year"], importance=5)

    # ── CONVERSION RESISTANCE: non-faith agent resists Greenveil ──
    if agent.get("faith",0) == 0 and agent.get("is_heretic") and        "resist the spread of faith" not in existing:
        new_goals.append({
            "goal":     "resist the spread of faith",
            "origin":   "became a heretic — opposes religious domination",
            "priority": 7,
            "type":     "resistance",
            "active":   True,
            "born_year": world["year"],
        })

    # Add new goals (avoid duplicates)
    for g in new_goals:
        if g["goal"] not in existing:
            agent["originated_goals"].append(g)
            log("GOAL ORIGINATED: %s (%s) — '%s' (from: %s)" % (
                agent["name"], atype, g["goal"], g["origin"]), "cognition")
            log_goal_origin_research(agent, g["goal"], g["type"], g["origin"])
            log_event_research("cognition","GOAL ORIGINATED: %s (%s) — '%s'"%(agent["name"],atype,g["goal"]),3)
            history("%s originated a new goal: '%s'" % (agent["name"], g["goal"]), importance=3)
            world["stats"]["goals_originated"] = world["stats"].get("goals_originated",0)+1

    # Check if active originated goals are fulfilled
    for g in agent["originated_goals"]:
        if not g.get("active"): continue
        gtype = g.get("type","")
        fulfilled = False

        if gtype == "revenge" and len(recall(agent,"battle")) > 3:
            fulfilled = True; g["outcome"] = "achieved — fought back"
        elif gtype == "legacy" and agent.get("is_legend"):
            fulfilled = True; g["outcome"] = "achieved — became a legend"
        elif gtype == "peace" and not world.get("active_wars"):
            fulfilled = True; g["outcome"] = "achieved — peace came"
        elif gtype == "understanding" and sm.get("world_understanding",0) > 60:
            fulfilled = True; g["outcome"] = "achieved — understanding grew"
        elif gtype == "identity" and sm.get("identity_stability",0) > 70:
            fulfilled = True; g["outcome"] = "achieved — found myself again"
        elif gtype == "mastery" and len(agent.get("skills",[])) >= 5:
            fulfilled = True; g["outcome"] = "achieved — mastery attained"

        if fulfilled:
            g["active"] = False
            g["fulfilled_year"] = world["year"]
            agent["emotion"] = "joyful"
            remember(agent, "joy",
                "I have fulfilled my goal: '%s'. %s. Y%d" % (g["goal"], g.get("outcome",""), world["year"]),
                importance=5)
            log("GOAL FULFILLED: %s — '%s'" % (agent["name"], g["goal"]), "cognition")


# ──────────────────────────────────────────────────────────────────
# 4. ABSTRACTION TRANSFER
# When an agent learns something in one domain, they extract a
# transferable principle and apply it in a new domain.
# The transfer can succeed (creates new insight) or fail (creates
# a flawed but confidently-held wrong belief).
# ──────────────────────────────────────────────────────────────────

# Domain -> abstract principle extraction
ABSTRACTION_SOURCES = {
    "battle": [
        ("overwhelming force resolves uncertainty", ["building","diplomacy","trade"]),
        ("knowing your enemy matters more than strength", ["scholarship","espionage","faith"]),
        ("survival requires adapting to the moment",     ["exploration","farming","healing"]),
        ("sometimes retreat is the strongest move",      ["trade","diplomacy","faith"]),
    ],
    "discovery": [
        ("every surface hides a deeper structure",       ["scholarship","building","faith"]),
        ("small patterns predict large outcomes",        ["farming","trade","diplomacy"]),
        ("the map is not the territory",                 ["battle","faith","politics"]),
        ("the unknown is not dangerous — ignorance is", ["war","diplomacy","social"]),
    ],
    "built": [
        ("strong foundations outlast impressive facades", ["trust","faith","relationships"]),
        ("form follows function",                          ["battle","scholarship","trade"]),
        ("what is built together is defended together",    ["diplomacy","war","community"]),
        ("a structure is only as strong as its weakest joint", ["faction","alliance","family"]),
    ],
    "friend": [
        ("trust compounds like interest — slowly then suddenly", ["trade","diplomacy","faith"]),
        ("shared vulnerability creates deeper bonds than shared strength", ["battle","community","faith"]),
        ("you reveal your true nature in how you treat those weaker",      ["leadership","faction","trade"]),
    ],
    "betrayal": [
        ("loyalty is tested under pressure, not in peace", ["battle","faction","faith"]),
        ("those who betray once have learned it works",    ["diplomacy","trade","social"]),
        ("I will not make the same mistake",               ["trust","relationship","alliance"]),
    ],
    "discovery_faith": [
        ("faith without doubt is superstition",            ["scholarship","battle","identity"]),
        ("what you worship shapes what you become",        ["faction","trade","identity"]),
    ],
}

# Transfer templates: (principle, target_domain) → insight
TRANSFER_INSIGHTS = {
    ("overwhelming force resolves uncertainty", "trade"):
        "I should dominate negotiations the way I dominate battlefields — with overwhelming preparation.",
    ("knowing your enemy matters more than strength", "scholarship"):
        "Understanding a problem completely matters more than attacking it with effort.",
    ("survival requires adapting to the moment", "farming"):
        "A good farmer reads the season. I learned to read the battle. Same skill.",
    ("strong foundations outlast impressive facades", "trust"):
        "I build trust the way I build walls — slowly, tested under pressure, layer by layer.",
    ("small patterns predict large outcomes", "diplomacy"):
        "I watched how factions move in small things. Now I can predict their large moves.",
    ("every surface hides a deeper structure", "faith"):
        "If everything I've discovered hides layers below — perhaps faith does too.",
    ("trust compounds like interest — slowly then suddenly", "diplomacy"):
        "Build alliances slowly. The compounding trust becomes something neither side can afford to lose.",
    ("loyalty is tested under pressure, not in peace", "battle"):
        "I know which allies will hold in a real fight. Not the ones who smiled in peace.",
    ("what is built together is defended together", "diplomacy"):
        "Shared construction creates ownership. If they helped build it, they'll help protect it.",
    ("form follows function", "battle"):
        "My strategy should match the objective exactly. No more. No less.",
}

def attempt_abstraction_transfer(agent):
    """Agent extracts a principle from one domain and applies it to another."""
    if random.random() > 0.04: return  # rare event
    memories = agent["memories"]
    if not memories: return

    # Pick a memory domain that has enough events
    domain_counts = {}
    for m in memories:
        domain_counts[m["type"]] = domain_counts.get(m["type"],0) + 1

    # Need at least 3 memories in a domain to abstract from it
    rich_domains = [d for d, c in domain_counts.items() if c >= 3 and d in ABSTRACTION_SOURCES]
    if not rich_domains: return

    source_domain = random.choice(rich_domains)
    principle, target_domains = random.choice(ABSTRACTION_SOURCES[source_domain])
    target_domain = random.choice(target_domains)

    # Look up if there's a known insight for this transfer
    key = (principle, target_domain)
    insight = TRANSFER_INSIGHTS.get(key)

    success = random.random() < 0.65  # 65% transfer correctly, 35% misapply

    if success and insight:
        # Successful transfer — creates a genuine new understanding
        remember(agent, "discovery",
            "ABSTRACTION: Applied '%s' to %s — '%s' Y%d" % (
                principle, target_domain, insight[:60], world["year"]),
            importance=4)
        agent["emotion"] = "inspired"

        # Grant a belief boost in target domain
        b = agent.get("beliefs",{})
        if "knowledge_is_power" in b:
            b["knowledge_is_power"]["confidence"] = min(100, b["knowledge_is_power"]["confidence"] + 8)
        if "i_can_change_things" in b:
            b["i_can_change_things"]["confidence"] = min(100, b["i_can_change_things"]["confidence"] + 5)

        log("ABSTRACTION TRANSFER: %s (%s) — '%s' → %s" % (
            agent["name"], agent["type"], principle[:40], target_domain), "cognition")
        log_abstraction_research(agent, source_domain, principle, target_domain, True)
        log_event_research("cognition","ABSTRACTION: %s (%s) — %s → %s"%(agent["name"],agent["type"],source_domain,target_domain),3)
        history("%s made an abstraction transfer: %s → %s" % (agent["name"], source_domain, target_domain), importance=3)
        world["stats"]["abstractions_made"] = world["stats"].get("abstractions_made",0) + 1

        # Bonus: if scholar or has deep_memory skill, extra knowledge
        if agent["type"] == "scholar" or "deep_memory" in agent.get("skills",[]):
            world["resources"]["knowledge"] = world["resources"].get("knowledge",0) + random.randint(20,50)

    else:
        # Failed transfer — agent confidently applies wrong principle
        misapplication = random.choice([
            "I tried to apply what I learned in %s to %s. It did not work as I expected." % (source_domain, target_domain),
            "The pattern I saw in %s does not hold in %s. I was wrong." % (source_domain, target_domain),
            "What worked in %s failed completely in %s. I need to rethink." % (source_domain, target_domain),
        ])
        remember(agent, "discovery",
            "FAILED ABSTRACTION: %s Y%d" % (misapplication, world["year"]),
            importance=3)
        # Failed transfer slightly shakes world understanding
        sm = agent.get("self_model",{})
        if "world_understanding" in sm:
            sm["world_understanding"] = max(0, sm["world_understanding"] - 3)
        agent["emotion"] = random.choice(["curious","content"])  # failure makes them think harder
        log_abstraction_research(agent, source_domain, principle, target_domain, False)


# ──────────────────────────────────────────────────────────────────
# COGNITIVE TICK — runs all four systems each tick per agent
# ──────────────────────────────────────────────────────────────────

def tick_cognition():
    """Run cognitive architecture for all living agents."""
    for agent in living():
        # Init systems if not present (handles existing saves)
        if "self_model" not in agent:
            init_self_model(agent)
        if "beliefs" not in agent:
            init_beliefs(agent)
        if "originated_goals" not in agent:
            agent["originated_goals"] = []
        # Ensure AGI layer fields are present on agents loaded from old saves
        if _COGNITIVE_LOOP_LOADED and "bdi" not in agent:
            try: init_bdi(agent)
            except Exception: pass
        if _LLM_MIND_LOADED and "llm_mind" not in agent:
            try: init_llm_mind(agent)
            except Exception: pass
        if _VALUE_ENGINE_LOADED and "values" not in agent:
            try: init_value_system(agent)
            except Exception: pass

        # Update at different frequencies for performance
        if random.random() < 0.08:
            update_self_model(agent)
        if random.random() < 0.12:
            revise_beliefs(agent)
        if random.random() < 0.05:
            originate_goals(agent)
        if random.random() < 0.04:
            attempt_abstraction_transfer(agent)

    # ── AGI COGNITIVE TICKS ───────────────────────────────────────
    if _COGNITIVE_LOOP_LOADED:
        try:
            tick_cognitive_loops(world)
            # Bridge BDI desires → originated_goals so they appear in stats and research
            # Also write BDI intention as an action_hint so it actually changes behaviour
            _BDI_TO_HINT = {
                "fight":        "hunt",      "hunt":       "hunt",
                "discover":     "deep_explore","understand": "deep_explore",
                "build":        "building",  "provide":    "farming",
                "connect":      "seek_friend","protect":    "seek_friend",
                "heal":         "healing",   "trade":      "trading",
                "convert":      "preaching", "gather_intel":"scouting",
                "control":      "hunt",      "grow":       "deep_explore",
                "survive":      "hiding",
            }
            for _a in living():
                _bdi = _a.get("bdi",{})
                _desires = _bdi.get("desires",[])
                _existing_goals = [g["goal"] for g in _a.get("originated_goals",[])]
                # Translate top BDI desire into an action hint the world engine can use
                _intention = _bdi.get("current_intention")
                if _intention:
                    _label = _intention.get("desire","")
                    _urgency = _intention.get("urgency", 0.5)
                    # Override whenever there's an active intention (urgency threshold lowered)
                    if _urgency > 0.3 and _label in _BDI_TO_HINT:
                        _a["bdi_action_hint"] = _BDI_TO_HINT[_label]
                        world["stats"]["bdi_hint_overrides"] = world["stats"].get("bdi_hint_overrides", 0) + 1
                # Bridge desires to originated_goals
                for _d in _desires[:2]:
                    _dlabel = _d.get("desire","")
                    if _dlabel and _dlabel not in _existing_goals and _d.get("urgency",0) > 0.6:
                        _new_goal = {
                            "goal": _dlabel, "type": "bdi_intention",
                            "origin": "bdi_desire_stack",
                            "active": True, "tick_born": world["tick"],
                            "year_born": world["year"],
                        }
                        _a["originated_goals"].append(_new_goal)
                        world["stats"]["goals_originated"] = world["stats"].get("goals_originated",0)+1
        except Exception as _e: log("AGI: tick_cognitive_loops error: %s" % _e, "agi")
    if _LLM_MIND_LOADED:
        try: tick_llm_minds(world)
        except Exception as _e: log("AGI: tick_llm_minds error: %s" % _e, "agi")
    if _VALUE_ENGINE_LOADED:
        # Value engine: throttled to every 5 ticks to prevent over-destabilisation
        if world["tick"] % 5 == 0:
            try: tick_value_engine(world)
            except Exception as _e: log("AGI: tick_value_engine error: %s" % _e, "agi")
    # ─────────────────────────────────────────────────────────────

def tick_alive_system():
    """Run emotions, goal checks, and voice generation each tick."""
    for agent in living():
        update_emotion(agent)
        apply_emotion_effects(agent)
        if random.random()<0.05:
            generate_voice(agent)
        if random.random()<0.02:
            check_goal_achieved(agent)


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# LAYER 1 — DYNAMIC STRATEGY REWRITING
# Agents don't just discover fixed skills. They synthesise NEW
# behavioral strategies by combining abstracted principles with their
# current situation. Each strategy is a mini decision-tree the agent
# writes for itself and commits to for a period of ticks.
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

STRATEGY_COMPONENTS = {
    # (trigger_condition, action_modifier, thought_template, stat_effect)
    "overwhelm": ("battles>5 and win_rate>0.6",
        lambda a: setattr_agent(a,"target",nearest_enemy_pos(a)),
        "I have learned to press every advantage. Attack before they recover.",
        {"battle_power":4}),
    "feign_retreat": ("battles>8 and win_rate<0.4",
        lambda a: move_away_then_back(a),
        "Losing straight fights. I will draw them out, then strike.",
        {"battle_power":3,"health":2}),
    "pack_hunt": ("faction_at_war and nearby_allies>2",
        lambda a: move_toward_ally(a),
        "Alone I lose. Together we are stronger than any one of us.",
        {"battle_power":5}),
    "fortify": ("builds>5 and health<50",
        lambda a: move_toward_own_building(a),
        "I need walls around me. My structures are my defence.",
        {"health":5}),
    "deep_scout": ("discoveries>6 and no_war",
        lambda a: setattr_agent(a,"target",extreme_pos(a)),
        "I have mapped the centre. The edges hold what no one has seen.",
        {"knowledge":3}),
    "knowledge_hoard": ("skills>3 and is_scholar",
        lambda a: move_toward_library(a),
        "Every skill I hold is leverage. I collect them deliberately.",
        {"knowledge":5}),
    "shadow_trade": ("is_merchant and spy_count>0",
        lambda a: move_toward_shadowveil(a),
        "Information and gold flow through the same channels.",
        {"gold":3}),
    "faith_anchor": ("faith>40 and nearby_heretics>0",
        lambda a: move_toward_heretic(a),
        "Doubt spreads like disease. I must be the counter-infection.",
        {"faith":5}),
    "grief_isolation": ("emotion==grieving and loss_count>2",
        lambda a: move_away_from_all(a),
        "I cannot be near others right now. The weight is too much.",
        {"health":-1}),
    "revenge_hunt": ("originated_goal==revenge and battles>3",
        lambda a: hunt_betrayer(a),
        "I have a name in mind. I will find them.",
        {"battle_power":6}),
    "elder_counsel": ("age>300 and social_standing>60",
        lambda a: move_toward_young(a),
        "I have lived long enough to know what the young cannot yet see.",
        {"knowledge":2,"faith":1}),
    "isolationist": ("beliefs_shattered>3 and identity_stability<40",
        lambda a: setattr_agent(a,"target",rand_pos()),
        "Every system I trusted has failed. I trust only myself now.",
        {"health":1}),
}

def setattr_agent(a, key, val):
    a[key] = val

def nearest_enemy_pos(agent):
    enemies=[]
    for f in FACTIONS:
        if get_diplo(agent.get("faction","?"),f)=="war":
            enemies+=faction_agents(f)
    if enemies:
        closest=min(enemies,key=lambda e:dist(agent["position"],e["position"]))
        return closest["position"]
    return rand_pos()

def extreme_pos(agent):
    # Go toward world edge
    return [random.choice([-35,35]),random.choice([-35,35])]

def move_toward_ally(agent):
    faction=agent.get("faction","?")
    allies=[a for a in faction_agents(faction) if a["id"]!=agent["id"]]
    if allies:
        closest=min(allies,key=lambda e:dist(agent["position"],e["position"]))
        agent["target"]=closest["position"]

def move_toward_young(agent):
    young=[a for a in living() if a["age"]<50 and a["id"]!=agent["id"]]
    if young:
        agent["target"]=min(young,key=lambda e:dist(agent["position"],e["position"]))["position"]

def move_away_from_all(agent):
    agent["target"]=[agent["position"][0]+random.choice([-20,20]),
                     agent["position"][1]+random.choice([-20,20])]

def move_toward_heretic(agent):
    heretics=[a for a in living() if a.get("is_heretic")]
    if heretics:
        agent["target"]=min(heretics,key=lambda e:dist(agent["position"],e["position"]))["position"]

def move_toward_own_building(agent):
    own=[b for b in world["buildings"] if b.get("built_by")==agent["name"]]
    if own:
        agent["target"]=random.choice(own)["position"]

def move_toward_library(agent):
    libs=[b for b in world["buildings"] if b["type"]=="library"]
    if libs:
        agent["target"]=min(libs,key=lambda b:dist(agent["position"],b["position"]))["position"]

def move_toward_shadowveil(agent):
    sv=faction_agents("Shadowveil")
    if sv:
        agent["target"]=random.choice(sv)["position"]

def move_away_then_back(agent):
    # Tactical retreat
    enemies=[]
    for f in FACTIONS:
        if get_diplo(agent.get("faction","?"),f)=="war":
            enemies+=faction_agents(f)
    if enemies:
        closest=min(enemies,key=lambda e:dist(agent["position"],e["position"]))
        dx=agent["position"][0]-closest["position"][0]
        dy=agent["position"][1]-closest["position"][1]
        agent["target"]=clamp([agent["position"][0]+dx*2,agent["position"][1]+dy*2])

def hunt_betrayer(agent):
    betrayals=recall(agent,"betrayal")
    if betrayals:
        # Find any agent who might be the betrayer
        for a in living():
            if any(a["name"] in m["content"] for m in betrayals):
                agent["target"]=a["position"]
                return
    agent["target"]=rand_pos()

def evaluate_strategy_condition(agent, condition_str):
    """Evaluate whether a strategy's trigger condition is met."""
    try:
        battles=len(recall(agent,"battle"))
        wins=sum(1 for m in recall(agent,"battle") if "survived" in m["content"].lower() or "won" in m["content"].lower())
        win_rate=wins/battles if battles>0 else 0.5
        builds=len(recall(agent,"built"))
        discoveries=len(recall(agent,"discovery"))
        skills=len(agent.get("skills",[]))
        health=agent.get("health",100)
        faith=agent.get("faith",0)
        age=agent.get("age",0)
        emotion=agent.get("emotion","content")
        loss_count=len(recall(agent,"loss"))
        faction=agent.get("faction","?")
        is_scholar=(agent["type"]=="scholar")
        is_merchant=(agent["type"]=="merchant")
        faction_at_war=any(get_diplo(faction,f)=="war" for f in FACTIONS if f!=faction)
        no_war=not faction_at_war
        nearby_allies=len([a for a in living()
                          if a.get("faction")==faction and a["id"]!=agent["id"]
                          and dist(agent["position"],a["position"])<10])
        nearby_heretics=len([a for a in living()
                            if a.get("is_heretic") and dist(agent["position"],a["position"])<10])
        spy_count=len([a for a in faction_agents(faction) if a["type"]=="spy"])
        sm=agent.get("self_model",{})
        social_standing=sm.get("social_standing",50)
        identity_stability=sm.get("identity_stability",80)
        beliefs_shattered=sum(1 for bv in agent.get("beliefs",{}).values() if bv.get("value")==False)
        originated_goal=next((g["type"] for g in agent.get("originated_goals",[]) if g.get("active")),"none")
        return eval(condition_str)
    except Exception:
        return False

def synthesise_strategy(agent):
    """Agent evaluates all strategies, picks the best fit, commits to it."""
    if random.random()>0.03: return  # rare — agents don't constantly restrategise
    if "strategy" in agent and agent.get("strategy_ticks_left",0)>0:
        agent["strategy_ticks_left"]-=1
        return  # still committed to current strategy

    # Find all applicable strategies
    applicable=[]
    for name,(condition,action_fn,thought,effects) in STRATEGY_COMPONENTS.items():
        if evaluate_strategy_condition(agent,condition):
            applicable.append((name,action_fn,thought,effects))

    if not applicable: return

    # Pick the one that fits best (highest-priority = first matching for now)
    chosen=applicable[0]
    name,action_fn,thought,effects=chosen

    # Commit to this strategy
    prev=agent.get("strategy","none")
    agent["strategy"]=name
    agent["strategy_ticks_left"]=random.randint(20,60)
    agent["thought"]=thought

    # Execute the action function
    try: action_fn(agent)
    except Exception: pass

    # Apply stat effects
    for stat,delta in effects.items():
        if stat=="battle_power":
            agent["battle_power"]=agent.get("battle_power",10)+delta
        elif stat=="health":
            agent["health"]=max(1,min(150,agent.get("health",100)+delta))
        elif stat=="knowledge":
            world["resources"]["knowledge"]=world["resources"].get("knowledge",0)+delta
        elif stat=="faith":
            agent["faith"]=agent.get("faith",0)+delta
        elif stat=="gold":
            world["resources"]["gold"]=world["resources"].get("gold",0)+delta

    if prev!=name:
        remember(agent,"discovery",
            "Adopted strategy '%s': %s Y%d"%(name,thought[:50],world["year"]),
            importance=3)
        if name not in ["grief_isolation","isolationist"]:
            log("STRATEGY: %s (%s) adopted '%s'"%(agent["name"],agent["type"],name),"cognition")
        world["stats"]["strategy_changes"]=world["stats"].get("strategy_changes",0)+1



# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# LAYER 1 UPGRADE — STRATEGY COMPOSITION ENGINE
# Agents no longer just pick from fixed strategies.
# They compose new ones by combining:
#   - Their own abstracted principles (from abstraction transfer)
#   - Their current emotional state
#   - Their active originated goals
#   - Their belief profile
# Composed strategies are unique to each agent and situation.
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

STRATEGY_MODIFIERS = {
    # Emotion modifiers on strategy composition
    "angry":    {"battle_power": 5,  "speed": 0.3,  "bias": "aggressive"},
    "afraid":   {"speed": 0.4,       "health": 2,   "bias": "defensive"},
    "inspired": {"knowledge": 8,     "skill_chance": 0.05, "bias": "creative"},
    "grieving": {"health": -1,       "speed": -0.2, "bias": "withdrawn"},
    "joyful":   {"health": 2,        "gold": 3,     "bias": "social"},
    "vengeful": {"battle_power": 8,  "speed": 0.2,  "bias": "aggressive"},
    "devoted":  {"faith": 5,         "health": 1,   "bias": "faith"},
    "proud":    {"battle_power": 3,  "knowledge": 3,"bias": "assertive"},
    "lonely":   {"health": -1,       "bias": "seeking"},
    "weary":    {"speed": -0.3,      "health": -0.5,"bias": "defensive"},
    "curious":  {"knowledge": 4,     "bias": "exploration"},
    "content":  {"health": 1,        "bias": "neutral"},
}

GOAL_BIASES = {
    "revenge":     {"battle_power": 6, "bias": "aggressive", "action": "hunt_betrayer"},
    "protection":  {"health": 3,       "bias": "defensive",  "action": "move_toward_ally"},
    "legacy":      {"knowledge": 3,    "bias": "creative",   "action": "move_toward_young"},
    "peace":       {"faith": 3,        "bias": "diplomatic", "action": "move_toward_ally"},
    "identity":    {"health": 2,       "bias": "withdrawn",  "action": "move_away_from_all"},
    "mastery":     {"knowledge": 6,    "bias": "scholarly",  "action": "move_toward_library"},
    "resistance":  {"battle_power": 3, "bias": "aggressive", "action": "move_toward_heretic"},
    "understanding":{"knowledge": 4,   "bias": "scholarly",  "action": "move_toward_library"},
}

BELIEF_BIASES = {
    "strength_wins":        {"battle_power": 4, "bias": "aggressive"},
    "cooperation_works":    {"gold": 2,          "bias": "diplomatic"},
    "knowledge_is_power":   {"knowledge": 4,     "bias": "scholarly"},
    "faith_protects":       {"faith": 4,         "bias": "faith"},
    "world_is_dangerous":   {"health": 2,        "bias": "defensive"},  # reversed belief
    "trust_no_one":         {"battle_power": 2,  "bias": "isolationist"},
}

def compose_strategy(agent):
    """
    Agent composes a unique strategy from their own principles,
    emotions, goals and beliefs. This replaces fixed strategy selection
    for cognitively mature agents (age > 50, 2+ memories in any domain).
    Returns a strategy dict or None.
    """
    age       = agent.get("age", 0)
    memories  = agent["memories"]
    em        = agent.get("emotion", "content")
    beliefs   = agent.get("beliefs", {})
    orig_goals= agent.get("originated_goals", [])
    abstracts = [m for m in memories if "ABSTRACTION" in m.get("content", "")]

    if age < 50 or len(memories) < 8:
        return None  # not mature enough to compose

    # ── COLLECT INFLUENCES ────────────────────────────────────
    stat_effects = {}
    thought_parts = []
    action_name   = None
    bias          = "neutral"

    # Emotion influence
    em_mod = STRATEGY_MODIFIERS.get(em, {})
    for k, v in em_mod.items():
        if k != "bias":
            stat_effects[k] = stat_effects.get(k, 0) + v
    if "bias" in em_mod:
        bias = em_mod["bias"]
        thought_parts.append("My %s drives me" % em)

    # Active goal influence
    active_goal = next((g for g in orig_goals if g.get("active")), None)
    if active_goal:
        goal_mod = GOAL_BIASES.get(active_goal["type"], {})
        for k, v in goal_mod.items():
            if k not in ("bias", "action"):
                stat_effects[k] = stat_effects.get(k, 0) + v
        if "bias" in goal_mod:
            bias = goal_mod["bias"]
        if "action" in goal_mod:
            action_name = goal_mod["action"]
        thought_parts.append("my goal to %s compels me" % active_goal["goal"])

    # Strongest belief influence
    strongest_belief = None
    strongest_conf   = 0
    for bk, bv in beliefs.items():
        if bv.get("value", True) and bv.get("confidence", 0) > strongest_conf:
            strongest_conf   = bv.get("confidence", 0)
            strongest_belief = bk
        # Reversed beliefs have their own biases
        if bv.get("value") == False:
            reversed_key = {
                "world_is_safe":     "world_is_dangerous",
                "cooperation_works": "trust_no_one",
            }.get(bk)
            if reversed_key and reversed_key in BELIEF_BIASES:
                bmod = BELIEF_BIASES[reversed_key]
                for k, v in bmod.items():
                    if k != "bias":
                        stat_effects[k] = stat_effects.get(k, 0) + v

    if strongest_belief and strongest_belief in BELIEF_BIASES:
        bmod = BELIEF_BIASES[strongest_belief]
        for k, v in bmod.items():
            if k != "bias":
                stat_effects[k] = stat_effects.get(k, 0) + v
        thought_parts.append("I believe %s" % strongest_belief.replace("_", " "))

    # Abstraction influence — apply most recent successful transfer
    if abstracts:
        last_abst = abstracts[-1]["content"]
        if "battle" in last_abst and "battle_power" not in stat_effects:
            stat_effects["battle_power"] = stat_effects.get("battle_power", 0) + 3
            thought_parts.append("what I learned in battle guides me here")
        elif "discovery" in last_abst:
            stat_effects["knowledge"] = stat_effects.get("knowledge", 0) + 4
            thought_parts.append("a pattern I found in exploration applies here")
        elif "built" in last_abst or "building" in last_abst:
            stat_effects["health"] = stat_effects.get("health", 0) + 2
            thought_parts.append("I build this strategy like I build structures")

    if not stat_effects:
        return None

    # ── BUILD THOUGHT ─────────────────────────────────────────
    if thought_parts:
        thought = (thought_parts[0].capitalize() + 
                  ("" if len(thought_parts)==1 else
                   ", and " + ", and ".join(thought_parts[1:])) + ".")
    else:
        thought = "Acting from accumulated experience."

    # ── BUILD STRATEGY NAME ───────────────────────────────────
    bias_names = {
        "aggressive":   ["the pressure", "the assault", "dominance"],
        "defensive":    ["the shield", "endurance", "survival"],
        "creative":     ["synthesis", "the pattern", "emergence"],
        "diplomatic":   ["the accord", "connection", "the bridge"],
        "scholarly":    ["deep study", "mastery", "the archive"],
        "faith":        ["the light", "devotion", "the covenant"],
        "withdrawn":    ["solitude", "the self", "inward focus"],
        "social":       ["the gathering", "kinship", "the bond"],
        "seeking":      ["the search", "belonging", "connection"],
        "isolationist": ["alone", "self-reliance", "the wall"],
        "assertive":    ["presence", "authority", "the stand"],
        "exploration":  ["the horizon", "the unknown", "wandering"],
        "neutral":      ["balance", "the middle path", "equilibrium"],
    }
    strat_name = "composed_%s_%d" % (
        random.choice(bias_names.get(bias, ["the path"])).replace(" ", "_"),
        agent["age"]
    )

    return {
        "name":       strat_name,
        "thought":    thought,
        "effects":    stat_effects,
        "action":     action_name,
        "bias":       bias,
        "composed":   True,
        "composed_at":world["year"],
    }

def synthesise_strategy_upgraded(agent):
    """
    Upgraded strategy synthesis — tries composition first for mature agents,
    falls back to fixed strategy library for young/simple agents.
    """
    if random.random() > 0.035: return
    if agent.get("strategy_ticks_left", 0) > 0:
        agent["strategy_ticks_left"] -= 1
        return

    age = agent.get("age", 0)
    composed = None

    # Mature agents (age > 50) try to compose their own strategy
    if age > 50 and random.random() < 0.55:
        composed = compose_strategy(agent)

    if composed:
        prev = agent.get("strategy", "none")
        agent["strategy"]             = composed["name"]
        agent["strategy_ticks_left"]  = random.randint(25, 70)
        agent["thought"]              = composed["thought"]

        # Execute action
        if composed["action"]:
            try:
                action_fn = {
                    "hunt_betrayer":       hunt_betrayer,
                    "move_toward_ally":    move_toward_ally,
                    "move_toward_young":   move_toward_young,
                    "move_toward_library": move_toward_library,
                    "move_toward_heretic": move_toward_heretic,
                    "move_away_from_all":  move_away_from_all,
                }.get(composed["action"])
                if action_fn: action_fn(agent)
            except Exception:
                pass

        # Apply effects
        for stat, delta in composed["effects"].items():
            if stat == "battle_power":
                agent["battle_power"] = agent.get("battle_power",10) + delta
            elif stat == "health":
                agent["health"] = max(1, min(150, agent.get("health",100) + delta))
            elif stat == "knowledge":
                world["resources"]["knowledge"] = world["resources"].get("knowledge",0) + delta
            elif stat == "faith":
                agent["faith"] = agent.get("faith",0) + delta
            elif stat == "gold":
                world["resources"]["gold"] = world["resources"].get("gold",0) + delta

        if prev != composed["name"]:
            remember(agent, "discovery",
                "Composed new strategy '%s': %s Y%d" % (
                    composed["name"], composed["thought"][:50], world["year"]),
                importance=3)
            log("STRATEGY COMPOSED: %s (%s) — %s [bias:%s]" % (
                agent["name"], agent["type"], composed["name"], composed["bias"]), "cognition")
            world["stats"]["strategies_composed"] = world["stats"].get("strategies_composed",0)+1
    else:
        # Fall back to fixed strategy library
        synthesise_strategy(agent)

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# LAYER 2 — EMERGENT SOCIAL CONTRACTS
# Agents negotiate rules between themselves. Contracts are proposed,
# accepted or rejected, then enforced socially. Violations have
# consequences. Rules that didn't exist in the engine get created
# by agents and spread through factions.
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

CONTRACT_TYPES = {
    "non_aggression": {
        "desc": "Factions agree not to attack each other for {duration} years",
        "proposer_types": ["merchant","priest","scholar"],
        "benefit": {"tension_reduction": 30, "gold_gain": 20},
        "violation": "war_declaration",
        "duration_years": 10,
    },
    "trade_agreement": {
        "desc": "Factions share 10% of gold production with each other",
        "proposer_types": ["merchant","builder"],
        "benefit": {"gold_gain": 15, "knowledge_gain": 5},
        "violation": "tension_spike",
        "duration_years": 5,
    },
    "knowledge_pact": {
        "desc": "Scholars freely share skills and discoveries across factions",
        "proposer_types": ["scholar","explorer"],
        "benefit": {"knowledge_gain": 30, "skill_spread": True},
        "violation": "knowledge_theft",
        "duration_years": 8,
    },
    "faith_covenant": {
        "desc": "Factions agree to respect each other's religious practice",
        "proposer_types": ["priest"],
        "benefit": {"faith_gain": 20, "holy_war_prevention": True},
        "violation": "holy_war",
        "duration_years": 15,
    },
    "mutual_defence": {
        "desc": "Factions agree to fight together against a common enemy",
        "proposer_types": ["warrior","spy"],
        "benefit": {"battle_power_boost": 5, "tension_reduction": 20},
        "violation": "betrayal",
        "duration_years": 5,
    },
    "resource_sharing": {
        "desc": "Factions pool food reserves — none shall starve alone",
        "proposer_types": ["farmer","healer"],
        "benefit": {"food_gain": 25, "health_boost": 5},
        "violation": "hoarding",
        "duration_years": 6,
    },
}

def init_contracts():
    if "social_contracts" not in world:
        world["social_contracts"] = []
    if "contract_violations" not in world:
        world["contract_violations"] = []

def propose_contract(agent):
    """Agent proposes a social contract to another faction."""
    init_contracts()
    atype = agent["type"]
    faction = agent.get("faction","?")

    # Find eligible contract types for this agent
    eligible = [k for k,v in CONTRACT_TYPES.items()
                if atype in v["proposer_types"]]
    if not eligible: return

    # Pick a contract type based on beliefs and situation
    ctype = None
    b = agent.get("beliefs",{})
    if b.get("cooperation_works",{}).get("confidence",50) > 65:
        ctype = random.choice(eligible)
    elif b.get("cooperation_works",{}).get("value") == False:
        return  # agent who lost faith in cooperation won't propose contracts
    else:
        if random.random() < 0.3:
            ctype = random.choice(eligible)

    if not ctype: return

    # Find a target faction — not at war, not already contracted
    active_contracts = [(c["fa"],c["fb"]) for c in world["social_contracts"]
                       if c["active"] and c["type"]==ctype]
    targets = [f for f in FACTIONS if f!=faction
               and get_diplo(faction,f)!="war"
               and (faction,f) not in active_contracts
               and (f,faction) not in active_contracts]
    if not targets: return

    target_faction = random.choice(targets)

    # Target faction evaluates the proposal
    target_agents = faction_agents(target_faction)
    if not target_agents: return

    # Acceptance based on target faction's beliefs and situation
    target_scholars = [a for a in target_agents if a["type"] in CONTRACT_TYPES[ctype]["proposer_types"]]
    evaluator = random.choice(target_scholars) if target_scholars else random.choice(target_agents)
    ev_beliefs = evaluator.get("beliefs",{})
    accept_prob = 0.4
    if ev_beliefs.get("cooperation_works",{}).get("confidence",50) > 60:
        accept_prob += 0.25
    if ev_beliefs.get("cooperation_works",{}).get("value") == False:
        accept_prob -= 0.3
    if get_tension(faction, target_faction) > 60:
        accept_prob -= 0.2

    if random.random() > accept_prob:
        remember(agent, "discovery",
            "%s rejected our proposal for a %s. Y%d"%(target_faction,ctype,world["year"]),
            importance=2)
        return

    # Contract accepted — create it
    contract = {
        "id": "c%d"%world["tick"],
        "type": ctype,
        "fa": faction,
        "fb": target_faction,
        "proposer": agent["name"],
        "acceptor": evaluator["name"],
        "created_year": world["year"],
        "expires_year": world["year"] + CONTRACT_TYPES[ctype]["duration_years"],
        "active": True,
        "desc": CONTRACT_TYPES[ctype]["desc"].format(
            duration=CONTRACT_TYPES[ctype]["duration_years"]),
        "violated": False,
    }
    world["social_contracts"].append(contract)

    # Apply immediate benefits
    benefits = CONTRACT_TYPES[ctype]["benefit"]
    if "tension_reduction" in benefits:
        reduce_tension(faction, target_faction, benefits["tension_reduction"])
    if "gold_gain" in benefits:
        world["resources"]["gold"] = world["resources"].get("gold",0) + benefits["gold_gain"]
    if "knowledge_gain" in benefits:
        world["resources"]["knowledge"] = world["resources"].get("knowledge",0) + benefits["knowledge_gain"]
    if "faith_gain" in benefits:
        world["resources"]["faith"] = world["resources"].get("faith",0) + benefits["faith_gain"]
    if "food_gain" in benefits:
        world["resources"]["food"] = world["resources"].get("food",0) + benefits["food_gain"]

    # Memories for both agents
    remember(agent, "friend",
        "Negotiated a %s with %s (%s). Y%d"%(ctype,target_faction,evaluator["name"],world["year"]),
        importance=4)
    remember(evaluator, "friend",
        "Accepted a %s from %s (%s). Y%d"%(ctype,faction,agent["name"],world["year"]),
        importance=4)

    # Beliefs update
    b = agent.get("beliefs",{})
    if "cooperation_works" in b:
        b["cooperation_works"]["confidence"] = min(100, b["cooperation_works"]["confidence"]+10)
    ev_b = evaluator.get("beliefs",{})
    if "cooperation_works" in ev_b:
        ev_b["cooperation_works"]["confidence"] = min(100, ev_b["cooperation_works"]["confidence"]+10)

    log("CONTRACT: %s (%s) + %s (%s) — %s"%(
        agent["name"],faction,evaluator["name"],target_faction,ctype),"diplomacy")
    history("%s and %s signed a %s — proposed by %s"%(
        faction,target_faction,ctype,agent["name"]),importance=3)
    world["stats"]["contracts_formed"] = world["stats"].get("contracts_formed",0)+1
    sound("alliance")

def tick_contracts():
    # Dynamic contract proposals from experienced agents
    for a in living():
        if random.random()<0.02: propose_dynamic_contract(a)

    """Enforce contracts, detect violations, expire old ones."""
    init_contracts()
    for contract in world["social_contracts"]:
        if not contract["active"]: continue
        fa,fb = contract["fa"],contract["fb"]
        ctype = contract["type"]

        # Expiry check
        if world["year"] >= contract["expires_year"]:
            contract["active"] = False
            log("CONTRACT EXPIRED: %s between %s and %s"%(ctype,fa,fb),"diplomacy")
            dur = CONTRACT_TYPES[ctype]["duration_years"] if ctype in CONTRACT_TYPES else contract.get("expires_year",0)-contract.get("created_year",0)
            history("The %s between %s and %s has expired after %d years"%(
                ctype,fa,fb,dur),importance=2)
            continue

        # Violation detection
        violated = False
        violation_reason = ""
        # Custom contracts have violation type stored in the contract itself
        custom_violation = contract.get("violated_by","")
        if custom_violation == "war_declaration" and get_diplo(fa,fb)=="war":
            violated=True; violation_reason="war declared despite custom agreement"
        elif custom_violation == "betrayal" and get_diplo(fa,fb)=="war":
            violated=True; violation_reason="betrayed custom mutual pact"
        elif ctype == "non_aggression" and get_diplo(fa,fb)=="war":
            violated=True; violation_reason="war declared despite agreement"
        elif ctype == "faith_covenant":
            hw = [w for w in world.get("war_timeline",[])
                  if w.get("type")=="holy_war"
                  and ((w.get("attacker")==fa and w.get("defender")==fb) or
                       (w.get("attacker")==fb and w.get("defender")==fa))]
            if hw: violated=True; violation_reason="holy war broke faith covenant"
        elif ctype == "mutual_defence":
            # Check if one faction betrayed the other in a war
            if get_diplo(fa,fb)=="war":
                violated=True; violation_reason="betrayed mutual defence pact"

        if violated:
            contract["active"] = False
            contract["violated"] = True
            # Massive tension spike
            add_tension(fa,fb,40)
            # Memories in violating agents
            for f in [fa,fb]:
                for agent in faction_agents(f):
                    remember(agent,"betrayal",
                        "The %s was violated by %s! %s. Y%d"%(
                            ctype, fb if f==fa else fa, violation_reason, world["year"]),
                        importance=5)
                    b=agent.get("beliefs",{})
                    if "cooperation_works" in b:
                        b["cooperation_works"]["confidence"]=max(0,b["cooperation_works"]["confidence"]-25)

            world["contract_violations"].append({
                "tick":world["tick"],"year":world["year"],
                "type":ctype,"fa":fa,"fb":fb,"reason":violation_reason
            })
            log("CONTRACT VIOLATED: %s between %s and %s — %s"%(ctype,fa,fb,violation_reason),"diplomacy")
            history("The %s between %s and %s was violated — %s"%(
                ctype,fa,fb,violation_reason),importance=4)
            world["stats"]["contracts_violated"]=world["stats"].get("contracts_violated",0)+1
            continue

        # Ongoing benefit application (small per-tick bonus)
        benefits = CONTRACT_TYPES[ctype]["benefit"] if ctype in CONTRACT_TYPES else contract.get("benefit", {})
        if "skill_spread" in benefits and random.random()<0.05:
            # Share a random skill between factions
            fa_agents = faction_agents(fa)
            fb_agents = faction_agents(fb)
            if fa_agents and fb_agents:
                skilled = [a for a in fa_agents if a.get("skills")]
                if skilled:
                    teacher = random.choice(skilled)
                    student = random.choice(fb_agents)
                    if teacher["skills"]:
                        skill = random.choice(teacher["skills"])
                        if skill not in student.get("skills",[]):
                            if "skills" not in student: student["skills"]=[]
                            student["skills"].append(skill)
                            remember(student,"discovery",
                                "Learned '%s' from %s (%s) via knowledge pact Y%d"%(
                                    skill,teacher["name"],fa,world["year"]),importance=3)
        if "health_boost" in benefits and random.random()<0.02:
            for a in faction_agents(fa)+faction_agents(fb):
                a["health"]=min(150,a.get("health",100)+1)

def tick_social_contracts(agents):
    """Tick: agents propose contracts + enforce existing ones."""
    init_contracts()
    for agent in agents:
        if random.random() < 0.008:  # rare proposal events
            propose_contract(agent)
    tick_contracts()



# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# LAYER 2 UPGRADE — DYNAMIC CONTRACT GENERATION
# Agents analyse their faction's needs and the other faction's
# leverage to generate contract terms that didn't exist before.
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

def assess_faction_needs(faction):
    """What does this faction need most right now?"""
    agents  = faction_agents(faction)
    res     = world["resources"]
    needs   = {}

    # Population pressure
    if len(agents) < 4:   needs["population"] = 3
    elif len(agents) > 14: needs["space"]      = 2

    # Resource needs
    if res.get("food",0) < 200:      needs["food"]      = 3
    if res.get("gold",0) < 100:      needs["gold"]      = 2
    if res.get("knowledge",0) < 500: needs["knowledge"] = 2

    # Military needs
    warriors = [a for a in agents if a["type"]=="warrior"]
    if any(get_diplo(faction,f)=="war" for f in FACTIONS if f!=faction):
        if len(warriors) < 2: needs["military_help"] = 3
        else:                 needs["peace"]         = 2

    # Faith needs
    avg_faith = sum(a.get("faith",0) for a in agents)/max(1,len(agents))
    if avg_faith < 5:  needs["faith"]      = 1
    if avg_faith > 40: needs["conversion"] = 2

    # Knowledge needs
    ft = world.get("faction_tech",{}).get(faction,{})
    if ft.get("points",0) < 50: needs["research"] = 2

    return needs

def generate_contract_terms(proposer_faction, target_faction, proposer_agent):
    """
    Generate bespoke contract terms based on what both factions need.
    Returns a contract dict or None if no good terms can be found.
    """
    our_needs   = assess_faction_needs(proposer_faction)
    their_needs = assess_faction_needs(target_faction)

    if not our_needs and not their_needs:
        return None

    # Find complementary needs — best contracts address both sides
    terms      = []
    benefits   = {}
    violations = "tension_spike"
    desc_parts = []
    duration   = random.randint(5, 20)

    # If we need food and they have surplus
    if "food" in our_needs:
        terms.append("food_transfer")
        benefits["food_gain"] = 30
        desc_parts.append("%s shares food reserves with %s" % (target_faction, proposer_faction))

    # If we need military help
    if "military_help" in our_needs:
        terms.append("military_support")
        benefits["battle_power_boost"] = 4
        desc_parts.append("%s provides warriors to aid %s in conflict" % (target_faction, proposer_faction))
        violations = "betrayal"

    # If we need peace and they need gold
    if "peace" in our_needs and "gold" in their_needs:
        terms.append("peace_for_gold")
        benefits["tension_reduction"] = 50
        benefits["gold_gain"] = 20
        desc_parts.append("War ends in exchange for gold tribute")
        violations = "war_declaration"
        duration = 8

    # If both need knowledge
    if "knowledge" in our_needs or "knowledge" in their_needs:
        terms.append("knowledge_exchange")
        benefits["knowledge_gain"] = 40
        desc_parts.append("Scholars of both factions share research freely")

    # If they want to convert
    if "conversion" in their_needs:
        terms.append("faith_tolerance")
        benefits["faith_gain"] = 10
        desc_parts.append("Both factions agree to allow peaceful conversion")
        violations = "holy_war"

    # If both need research
    if "research" in our_needs and "research" in their_needs:
        terms.append("joint_research")
        benefits["knowledge_gain"] = 25
        benefits["tech_boost"] = True
        desc_parts.append("Joint scholarly expeditions pool technology research")

    if not terms:
        return None

    ctype = "_".join(terms[:2])  # name from first two terms
    desc  = "; ".join(desc_parts) if desc_parts else "A custom agreement between factions"

    return {
        "type":          ctype,
        "desc":          desc,
        "benefit":       benefits,
        "violation":     violations,
        "duration_years":duration,
        "custom":        True,
        "negotiated_by": proposer_agent["name"],
        "terms":         terms,
    }

def propose_dynamic_contract(agent):
    """Propose a dynamically generated contract if agent is a capable negotiator."""
    atype   = agent["type"]
    faction = agent.get("faction","?")

    # Only experienced negotiators generate custom contracts
    if atype not in ("merchant","scholar","priest","spy"): return
    if agent.get("age",0) < 80: return
    if random.random() > 0.015: return  # rare

    b = agent.get("beliefs",{})
    if b.get("cooperation_works",{}).get("value") == False: return

    # Find a target faction
    targets = [f for f in FACTIONS
               if f!=faction and get_diplo(faction,f)!="war"]
    if not targets: return
    target = random.choice(targets)

    contract_spec = generate_contract_terms(faction, target, agent)
    if not contract_spec: return

    # Check if target faction accepts — smarter acceptance logic
    target_agents = faction_agents(target)
    if not target_agents: return
    evaluator = max(target_agents, key=lambda a: a.get("age",0))  # wisest evaluator

    their_needs  = assess_faction_needs(target)
    our_terms    = contract_spec["terms"]
    accept_score = 0.3

    # Terms that address their needs boost acceptance
    if "food_transfer" in our_terms and "food" in their_needs:       accept_score += 0.3
    if "knowledge_exchange" in our_terms and "knowledge" in their_needs: accept_score += 0.25
    if "peace_for_gold" in our_terms and "gold" in their_needs:      accept_score += 0.35
    if "military_support" in our_terms and "military_help" in their_needs: accept_score += 0.3

    ev_beliefs = evaluator.get("beliefs",{})
    if ev_beliefs.get("cooperation_works",{}).get("confidence",50) > 65: accept_score += 0.2
    if ev_beliefs.get("cooperation_works",{}).get("value") == False:     accept_score -= 0.4
    if get_tension(faction, target) > 70:                                accept_score -= 0.25

    if random.random() > accept_score:
        remember(agent,"discovery",
            "%s considered our custom proposal but declined. Y%d"%(target,world["year"]),
            importance=2)
        return

    # CONTRACT FORMED
    contract = {
        "id":           "custom_c%d" % world["tick"],
        "type":         contract_spec["type"],
        "desc":         contract_spec["desc"],
        "fa":           faction,
        "fb":           target,
        "proposer":     agent["name"],
        "acceptor":     evaluator["name"],
        "created_year": world["year"],
        "expires_year": world["year"] + contract_spec["duration_years"],
        "active":       True,
        "violated":     False,
        "custom":       True,
        "terms":        contract_spec["terms"],
        "benefit":      contract_spec["benefit"],
        "violated_by":  contract_spec.get("violation","tension_spike"),
    }
    world.setdefault("social_contracts",[]).append(contract)

    # Apply benefits
    ben = contract_spec["benefit"]
    if "food_gain"      in ben: world["resources"]["food"]      = world["resources"].get("food",0)      + ben["food_gain"]
    if "gold_gain"      in ben: world["resources"]["gold"]      = world["resources"].get("gold",0)      + ben["gold_gain"]
    if "knowledge_gain" in ben: world["resources"]["knowledge"] = world["resources"].get("knowledge",0) + ben["knowledge_gain"]
    if "faith_gain"     in ben: world["resources"]["faith"]     = world["resources"].get("faith",0)     + ben["faith_gain"]
    if "tension_reduction" in ben: reduce_tension(faction, target, ben["tension_reduction"])
    if "tech_boost"     in ben:
        for f in (faction, target):
            ft = world.get("faction_tech",{}).get(f,{})
            if ft: ft["points"] = ft.get("points",0) + 15

    remember(agent, "friend",
        "Negotiated a custom %s with %s. Terms: %s. Y%d" % (
            contract_spec["type"], target, "; ".join(contract_spec["terms"]), world["year"]),
        importance=4)
    remember(evaluator, "friend",
        "Accepted custom contract from %s (%s). Fair terms. Y%d" % (
            faction, agent["name"], world["year"]),
        importance=3)
    log("CUSTOM CONTRACT: %s proposed to %s — %s" % (faction, target, contract_spec["type"]), "social")
    history("A new custom agreement forged: %s between %s and %s (negotiated by %s)" % (
        contract_spec["desc"][:60], faction, target, agent["name"]), importance=4)
    world["stats"]["custom_contracts"] = world["stats"].get("custom_contracts",0)+1

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# LAYER 3 — THE WORLD RESPONDS TO AGENTS
# The terrain, resources and environment evolve in response to what
# agents collectively do. Civilisation leaves marks on the world.
# The world pushes back.
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

def tick_world_response():
    """World terrain and resources respond to agent collective behavior."""
    alive = living()
    if not alive: return

    buildings = world.get("buildings",[])
    biome_map = world.get("biome_map",[])
    if isinstance(biome_map, dict): biome_map = list(biome_map.values())

    # ── 1. DEFORESTATION ──────────────────────────────────────
    # Heavy building in forest biomes degrades them to plains
    forest_buildings = [b for b in buildings if b.get("biome")=="forest"]
    if len(forest_buildings) > 12 and random.random() < 0.02:
        for b in biome_map if isinstance(biome_map, list) else []:
            if isinstance(b, dict) and b.get("type") == "forest" and random.random() < 0.15:
                b["type"] = "plains"
                history("Deforestation: heavy construction has turned a forest into plains.",importance=3)
                log("WORLD: Forest degraded to plains from over-building","world")
                break

    # ── 2. SOIL EXHAUSTION ────────────────────────────────────
    # Too many farmers in one biome reduce its food yield
    farmer_positions = [a["position"] for a in alive if a["type"]=="farmer"]
    if len(farmer_positions) > 8:
        # Check clustering
        from collections import Counter
        cells = ["%d_%d"%(int(p[0]//20),int(p[1]//20)) for p in farmer_positions]
        cell_counts = Counter(cells)
        if max(cell_counts.values()) > 4:
            # Overfarmed — reduce food production this tick
            world["resources"]["food"] = max(0, world["resources"].get("food",0) - random.randint(5,15))
            if random.random() < 0.05:
                history("The land shows signs of exhaustion — too many hands working the same soil.",importance=2)

    # ── 3. SACRED SITES ───────────────────────────────────────
    # Areas where many agents have died become sacred — faith bonus nearby
    graveyard = world.get("graveyard",[])
    if len(graveyard) > 20 and "sacred_sites" not in world:
        world["sacred_sites"] = []
    if world.get("sacred_sites") is not None:
        # Every 200 ticks, consider creating a new sacred site
        if world["tick"] % 200 == 0 and len(graveyard) > 15:
            # Find cluster of deaths
            recent_deaths = graveyard[-10:]
            if recent_deaths:
                avg_x = sum(d.get("position",[0,0])[0] for d in recent_deaths if d.get("position")) / max(1, len([d for d in recent_deaths if d.get("position")]))
                avg_y = sum(d.get("position",[0,0])[1] for d in recent_deaths if d.get("position")) / max(1, len([d for d in recent_deaths if d.get("position")]))
                site = {
                    "position": [avg_x, avg_y],
                    "created_year": world["year"],
                    "faith_bonus": random.randint(2,8),
                    "name": random.choice([
                        "The Weeping Ground","Field of Fallen","The Quiet Memorial",
                        "Hall of Echoes","Where the Last Light Fell","The Remembrance",
                        "The Blood Acre","Where Heroes Sleep",
                    ])
                }
                world["sacred_sites"].append(site)
                # Agents near site get faith bonus
                for a in alive:
                    if dist(a["position"],[avg_x,avg_y]) < 12:
                        a["faith"] = a.get("faith",0) + site["faith_bonus"]
                        world["resources"]["faith"] = world["resources"].get("faith",0) + site["faith_bonus"]
                history("A sacred site has formed: %s — where %d souls have perished."%(
                    site["name"],len(recent_deaths)),importance=4)
                log("WORLD: Sacred site formed — %s"%site["name"],"world")

    # ── 4. RUINS FORMATION ────────────────────────────────────
    # Abandoned buildings (faction wiped out) become ruins
    for building in list(buildings):
        bf = building.get("faction","?")
        if bf in FACTIONS and len(faction_agents(bf)) == 0:
            if building.get("type") not in ("ruin",) and random.random() < 0.005:
                building["type"] = "ruin"
                building["original_type"] = building.get("type","hut")
                history("The %s built by %s has fallen to ruin — their faction is gone."%(
                    building.get("original_type","structure"),bf),importance=3)

    # ── 5. RESOURCE DISCOVERY FROM EXPLORATION ────────────────
    # Dense exploration in a region uncovers new resources
    explorer_positions = [a["position"] for a in alive if a["type"]=="explorer"]
    if explorer_positions and random.random() < 0.003:
        ex_pos = random.choice(explorer_positions)
        resource = random.choice(["gold","knowledge","herbs","iron","stone"])
        amount = random.randint(30,100)
        world["resources"][resource] = world["resources"].get(resource,0) + amount
        biome = get_biome(ex_pos)
        history("Explorers in the %s have discovered a rich deposit of %s."%(biome,resource),importance=3)
        log("WORLD: Explorer activity uncovered %d %s in %s"%(amount,resource,biome),"discovery")

    # ── 6. WAR SCARS ──────────────────────────────────────────
    # Active wars leave environmental damage
    active_wars = world.get("active_wars",[])
    if active_wars and random.random() < 0.01:
        war = random.choice(active_wars)
        fa_agents = faction_agents(war["attacker"])
        if fa_agents:
            battle_pos = random.choice(fa_agents)["position"]
            # Destroy a nearby building
            nearby_buildings = [b for b in buildings
                               if dist(b["position"],battle_pos)<15
                               and b.get("faction")!=war["attacker"]]
            if nearby_buildings:
                destroyed = random.choice(nearby_buildings)
                buildings.remove(destroyed)
                history("War between %s and %s destroyed a %s."%(
                    war["attacker"],war["defender"],destroyed.get("type","structure")),importance=2)

    # ── 7. CLIMATE RESPONSE TO FAITH ──────────────────────────
    # Extreme faith levels affect weather patterns
    world_faith = world["resources"].get("faith",0)
    if world_faith > 30000 and random.random() < 0.005:
        # Miraculous weather
        world["weather"] = random.choice(["clear","rain"])
        history("The immense faith of the world seems to have calmed the heavens.",importance=3)
    elif world_faith < 100 and random.random() < 0.005:
        # Faithless world attracts storms
        world["weather"] = random.choice(["storm","drought"])
        history("With faith nearly extinguished, harsh weather descends on the world.",importance=3)

    # ── 8. POPULATION PRESSURE ON BIOMES ─────────────────────
    # High population in small area triggers migration signals
    if len(alive) > 35:
        crowded_factions = {f:len(faction_agents(f)) for f in FACTIONS}
        most_crowded = max(crowded_factions, key=crowded_factions.get)
        if crowded_factions[most_crowded] > 12:
            # Push agents toward edges
            for a in faction_agents(most_crowded)[:3]:
                if random.random() < 0.1:
                    a["target"] = extreme_pos(a)
                    if not has_mem(a,"discovery","migration"):
                        remember(a,"discovery",
                            "The lands of %s grow crowded. I am pushed outward. Y%d"%(
                                most_crowded,world["year"]),importance=3)



# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# LAYER 3 UPGRADE — WORLD MEMORY & PERMANENT CIVILIZATIONAL MARKS
# The world remembers what agents collectively do over time.
# Repeated behaviours cause permanent landscape transformation.
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

def init_world_memory():
    """Initialize the world's long-term memory of agent behaviour."""
    if "world_memory" not in world:
        world["world_memory"] = {
            "exploration_heatmap": {},  # grid cell → explore count
            "battle_heatmap":      {},  # grid cell → battle count
            "build_heatmap":       {},  # grid cell → build count
            "faith_heatmap":       {},  # grid cell → faith events
            "total_explorations":  0,
            "total_battles":       0,
            "permanent_marks":     [],  # lasting world changes
            "dominant_paths":      [],  # frequently travelled routes become roads
            "legend_sites":        [],  # where legends died or were born
        }

def pos_to_cell(pos, grid=10):
    """Convert world position to heatmap grid cell."""
    x = int((pos[0] + 40) / grid)
    y = int((pos[1] + 40) / grid)
    return "%d_%d" % (max(0, min(7, x)), max(0, min(7, y)))

def record_world_activity(agent, activity_type):
    """Record agent activity in the world heatmap."""
    init_world_memory()
    wm  = world["world_memory"]
    cell = pos_to_cell(agent["position"])

    hmap = activity_type + "_heatmap"
    if hmap in wm:
        wm[hmap][cell] = wm[hmap].get(cell, 0) + 1

    if activity_type == "exploration": wm["total_explorations"] += 1
    if activity_type == "battle":      wm["total_battles"]      += 1

def tick_world_memory():
    """
    World reads its own heatmaps and permanently transforms based on patterns.
    Called every 150 ticks — slower than other systems.
    """
    if world["tick"] % 150 != 0: return
    init_world_memory()
    wm   = world["world_memory"]
    bmap = world.get("biome_map", [])
    if isinstance(bmap, dict): bmap = list(bmap.values())
    if not isinstance(bmap, list): bmap = []

    # ── 1. WELL-TRAVELLED ROUTES BECOME ROADS ────────────────
    # Cells explored 30+ times get a "road" marker speeding movement
    if "roads" not in world: world["roads"] = []
    explore_map = wm["exploration_heatmap"]
    for cell, count in explore_map.items():
        if count >= 30 and cell not in world["roads"]:
            world["roads"].append(cell)
            wm["permanent_marks"].append({
                "type": "road", "cell": cell,
                "year": world["year"],
                "desc": "A road formed from centuries of travel through cell %s" % cell,
            })
            history("A road has worn itself into the world — %d journeys have carved this path." % count,
                    importance=3)
            log("WORLD MEMORY: Road formed at cell %s from %d explorations" % (cell, count), "world")

    # ── 2. BATTLE GROUNDS BECOME CURSED LAND ─────────────────
    # Cells with 20+ battles become darkened — faith penalty, disease risk
    if "cursed_cells" not in world: world["cursed_cells"] = []
    for cell, count in wm["battle_heatmap"].items():
        if count >= 20 and cell not in world["cursed_cells"]:
            world["cursed_cells"].append(cell)
            # Find and darken the biome there
            # Darken a random non-ocean biome cell
            if bmap:
                candidates = [b for b in bmap if isinstance(b,dict) and b.get("type") not in ("cursed","ocean")]
                if candidates:
                    random.choice(candidates)["type"] = "cursed"
            wm["permanent_marks"].append({
                "type":  "cursed_ground",
                "cell":  cell,
                "year":  world["year"],
                "battles": count,
                "desc":  "A cursed battlefield — %d conflicts have poisoned this land" % count,
            })
            history("The land at cell %s has become cursed from constant battle — %d conflicts have soaked the earth in blood." % (cell, count),
                    importance=4)
            log("WORLD MEMORY: Cursed ground formed at %s from %d battles" % (cell, count), "world")
            world["stats"]["cursed_grounds"] = world["stats"].get("cursed_grounds",0)+1

    # ── 3. HEAVILY BUILT AREAS BECOME PERMANENT CITIES ───────
    # Areas with 15+ buildings across history get named city status
    if "named_regions" not in world: world["named_regions"] = {}
    for cell, count in wm["build_heatmap"].items():
        if count >= 15 and cell not in world["named_regions"]:
            region_name = random.choice([
                "The Founders' Quarter","The Old Settlement","The Ancient District",
                "The Builder's Reach","The Cornerstone","The Hearth","The Cradle",
            ])
            world["named_regions"][cell] = {
                "name":    region_name,
                "cell":    cell,
                "year":    world["year"],
                "builds":  count,
            }
            history("A region has earned a name from its history: '%s' — built upon %d constructions." % (
                region_name, count), importance=4)
            world["stats"]["named_regions"] = world["stats"].get("named_regions",0)+1

    # ── 4. FAITH SATURATED AREAS BECOME HOLY GROUND ──────────
    if "holy_cells" not in world: world["holy_cells"] = []
    for cell, count in wm["faith_heatmap"].items():
        if count >= 25 and cell not in world["holy_cells"]:
            world["holy_cells"].append(cell)
            world["resources"]["faith"] = world["resources"].get("faith",0) + 500
            history("A holy site emerged from sustained devotion — the earth itself radiates faith.", importance=4)

    # ── 5. LEGEND BIRTHPLACES BECOME PILGRIMAGE SITES ────────
    legends_with_pos = [l for l in world.get("legends",[]) if l.get("birthplace")]
    if legends_with_pos and world["tick"] % 300 == 0:
        recent = legends_with_pos[-3:]
        for leg in recent:
            cell = pos_to_cell(leg["birthplace"])
            if not any(s.get("cell")==cell for s in wm.get("legend_sites",[])):
                wm["legend_sites"].append({
                    "cell": cell,
                    "name": "Birthplace of %s" % leg["name"],
                    "year": world["year"],
                })
                # Agents near this site get inspired
                for a in living():
                    if pos_to_cell(a["position"]) == cell:
                        a["emotion"] = "inspired"
                        remember(a, "discovery",
                            "I stand where %s was born. Something stirs in me. Y%d" % (
                                leg["name"], world["year"]),
                            importance=3)
                history("The birthplace of %s has become a site of pilgrimage." % leg["name"], importance=3)

    # ── 6. ROADS SPEED MOVEMENT ───────────────────────────────
    # Agents on road cells move faster
    roads = world.get("roads", [])
    if roads:
        for a in living():
            cell = pos_to_cell(a["position"])
            if cell in roads and "road_bonus" not in a.get("active_effects",[]):
                a.setdefault("active_effects", []).append("road_bonus")
                a["speed_bonus"] = a.get("speed_bonus",0) + 0.3
            elif cell not in roads and "road_bonus" in a.get("active_effects",[]):
                a["active_effects"].remove("road_bonus")
                a["speed_bonus"] = max(0, a.get("speed_bonus",0) - 0.3)

    # ── 7. CURSED GROUND PUNISHES THOSE WHO LINGER ───────────
    cursed = world.get("cursed_cells", [])
    if cursed:
        for a in living():
            cell = pos_to_cell(a["position"])
            if cell in cursed and random.random() < 0.02:
                a["health"] = max(1, a.get("health",100) - random.randint(2,8))
                a["faith"]  = max(0, a.get("faith",0)   - random.randint(1,3))
                if random.random() < 0.3:
                    remember(a, "trauma",
                        "This battlefield ground poisons me. The dead do not rest here. Y%d" % world["year"],
                        importance=3)

    # Trim permanent marks
    if len(wm["permanent_marks"]) > 50:
        wm["permanent_marks"] = wm["permanent_marks"][-50:]

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# LAYER 4 — META-EVOLUTION
# The engine tracks which behavioral strategies and agent types
# produce the most legends, longest lifespans, most descendants.
# Successful patterns propagate. Failed ones fade. Evolution
# operates on behavioral rules themselves, not just agent attributes.
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

def init_meta_evolution():
    if "meta_evolution" not in world:
        world["meta_evolution"] = {
            # Strategy fitness scores — updated from outcomes
            "strategy_fitness": {s: 50.0 for s in STRATEGY_COMPONENTS},
            # Type fitness — which agent types produce legends most
            "type_fitness": {t: 50.0 for t in AGENT_TYPES},
            # Belief fitness — which starting beliefs correlate with longevity
            "belief_fitness": {
                "faith_protects":50.0,"strength_wins":50.0,
                "cooperation_works":50.0,"knowledge_is_power":50.0,
            },
            # Trait fitness
            "trait_fitness": {},
            # Faction cultural drift — which behaviors factions trend toward
            "faction_culture": {f: {"dominant_strategy":"none","dominant_type":"warrior"} for f in FACTIONS},
            # Generation count
            "generation": 0,
            # Fitness history
            "fitness_log": [],
        }

def update_meta_evolution():
    """Update fitness scores from observed outcomes every 100 ticks."""
    init_meta_evolution()
    me = world["meta_evolution"]

    alive  = living()
    graves = world.get("graveyard",[])
    legends= world.get("legends",[])

    if not alive: return

    # ── STRATEGY FITNESS ──────────────────────────────────────
    # Strategies used by legends get +fitness, by dead young agents get -fitness
    for legend in legends[-10:]:  # recent legends
        strat = legend.get("strategy","none")
        if strat in me["strategy_fitness"]:
            me["strategy_fitness"][strat] = min(100,
                me["strategy_fitness"][strat] + 3.0)

    for dead in graves[-20:]:  # recently dead
        strat = dead.get("strategy","none")
        if strat in me["strategy_fitness"] and dead.get("age",0) < 50:
            me["strategy_fitness"][strat] = max(0,
                me["strategy_fitness"][strat] - 1.5)

    # Current living legends boost their strategies
    for a in alive:
        if a.get("is_legend"):
            strat = a.get("strategy","none")
            if strat in me["strategy_fitness"]:
                me["strategy_fitness"][strat] = min(100,
                    me["strategy_fitness"][strat] + 1.0)

    # ── TYPE FITNESS ──────────────────────────────────────────
    # Agent types that produce legends score higher
    legend_types = [l.get("type","?") for l in legends]
    for atype in AGENT_TYPES:
        count = legend_types.count(atype)
        total = max(1, sum(1 for a in alive if a["type"]==atype))
        legend_rate = count / total
        target = legend_rate * 100
        me["type_fitness"][atype] += (target - me["type_fitness"][atype]) * 0.05
        me["type_fitness"][atype] = max(5, min(100, me["type_fitness"][atype]))

    # ── BELIEF FITNESS ────────────────────────────────────────
    # Beliefs held by long-lived agents score higher
    elder_threshold = 200
    elders = [a for a in alive if a["age"] > elder_threshold]
    for elder in elders:
        b = elder.get("beliefs",{})
        for belief_key in me["belief_fitness"]:
            bconf = b.get(belief_key,{}).get("confidence",50)
            bval  = b.get(belief_key,{}).get("value",True)
            if bval and bconf > 60:
                me["belief_fitness"][belief_key] = min(100,
                    me["belief_fitness"][belief_key] + 0.5)
            elif not bval:  # reversed belief in long-lived agent
                me["belief_fitness"][belief_key] = max(0,
                    me["belief_fitness"][belief_key] - 0.3)

    # ── FACTION CULTURAL DRIFT ────────────────────────────────
    # Factions drift toward the strategies and types that work best for them
    for faction in FACTIONS:
        f_agents = faction_agents(faction)
        if not f_agents: continue

        # Find dominant strategy in this faction
        strat_counts = {}
        for a in f_agents:
            s = a.get("strategy","none")
            strat_counts[s] = strat_counts.get(s,0) + 1
        if strat_counts:
            dominant_strat = max(strat_counts, key=strat_counts.get)
            me["faction_culture"][faction]["dominant_strategy"] = dominant_strat

        # Find dominant type
        type_counts = {}
        for a in f_agents:
            type_counts[a["type"]] = type_counts.get(a["type"],0) + 1
        if type_counts:
            me["faction_culture"][faction]["dominant_type"] = max(type_counts, key=type_counts.get)

    # ── EVOLUTIONARY PRESSURE ON SPAWNING ────────────────────
    # High-fitness types get spawned more often
    # (Modifies world["spawn_weights"] read by spawn_agent)
    total_fitness = sum(me["type_fitness"].values())
    world["spawn_weights"] = {
        t: me["type_fitness"][t]/total_fitness
        for t in AGENT_TYPES
    }

    # ── GENERATION TRACKING ───────────────────────────────────
    graveyard_size = len(graves)
    pop = len(alive)
    if graveyard_size > 0 and graveyard_size % 50 == 0:
        me["generation"] += 1
        # Log fitness snapshot
        me["fitness_log"].append({
            "generation": me["generation"],
            "tick": world["tick"],
            "year": world["year"],
            "top_strategy": max(me["strategy_fitness"], key=me["strategy_fitness"].get),
            "top_type": max(me["type_fitness"], key=me["type_fitness"].get),
            "population": pop,
        })
        if len(me["fitness_log"]) <= 3:  # only log early generations to avoid spam
            top_s = max(me["strategy_fitness"], key=me["strategy_fitness"].get)
            top_t = max(me["type_fitness"], key=me["type_fitness"].get)
            log("META-EVOLUTION Gen %d: top strategy=%s (%.0f), top type=%s (%.0f)"%(
                me["generation"],top_s,me["strategy_fitness"][top_s],
                top_t,me["type_fitness"][top_t]),"cognition")
            history("Generation %d: the world favors %s (%s) and %s agents"%(
                me["generation"],top_s,faction,top_t),importance=3)

    # ── APPLY CULTURAL DRIFT TO NEW AGENTS ───────────────────
    # Agents born in a faction with strong cultural drift inherit tendencies
    for a in alive:
        if a.get("age",0) < 5:  # newborns
            f = a.get("faction","?")
            culture = me["faction_culture"].get(f,{})
            dom_strat = culture.get("dominant_strategy","none")
            if dom_strat != "none" and "strategy" not in a:
                a["strategy"] = dom_strat
                a["strategy_ticks_left"] = random.randint(10,30)

def tick_meta_evolution():
    """Run meta-evolution update every 100 ticks."""
    if world["tick"] % 100 == 0:
        update_meta_evolution()
    adaptive_rule_modification()  # modifies engine rules



# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# LAYER 4 UPGRADE — ADAPTIVE RULE MODIFICATION
# Meta-evolution now modifies actual engine parameters:
# - Faction trait intensities drift toward what works
# - Agent type lifespans adjust based on survival rates
# - Resource generation rates respond to population behaviour
# - New agent types can EMERGE from trait combination
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

def adaptive_rule_modification():
    """
    Every 200 ticks, the engine modifies its own parameters based on
    what strategies and types are succeeding. This is meta-evolution
    operating on the rules themselves, not just agent attributes.
    """
    if world["tick"] % 200 != 0: return
    init_meta_evolution()
    me      = world["meta_evolution"]
    alive   = living()
    graves  = world.get("graveyard",[])
    legends = world.get("legends",[])

    if not alive: return

    # ── 1. FACTION TRAIT DRIFT ────────────────────────────────
    # Factions whose dominant strategies succeed get trait reinforcement
    for faction in FACTIONS:
        f_agents = faction_agents(faction)
        if not f_agents: continue

        f_legends = [l for l in legends if l.get("faction")==faction]
        f_graves  = [g for g in graves  if g.get("faction")==faction]
        f_pop     = len(f_agents)

        # Compute survival/legend rate
        legend_rate  = len(f_legends) / max(1, len(f_graves) + f_pop)
        avg_age      = sum(a["age"] for a in f_agents) / f_pop
        at_war       = any(get_diplo(faction,f)=="war" for f in FACTIONS if f!=faction)

        culture = me["faction_culture"].get(faction, {})
        dom_strat = culture.get("dominant_strategy","none")

        # High legend rate reinforces current dominant strategy
        if legend_rate > 0.15 and dom_strat != "none":
            # Adjust spawn weights toward more of the dominant type
            dom_type = culture.get("dominant_type","warrior")
            current_weight = world.get("spawn_weights",{}).get(dom_type, 0.1)
            world.setdefault("spawn_weights",{})[dom_type] = min(0.35, current_weight * 1.05)
            if random.random() < 0.1:
                log("META-RULE: %s legend rate %.1f%% reinforcing %s dominance" % (
                    faction, legend_rate*100, dom_type), "cognition")

        # Factions at war with low survival drift toward diplomacy
        if at_war and avg_age < 80 and random.random() < 0.2:
            # Add more healers and priests to this faction's preference
            prefs = FACTION_PREFERRED_TYPES.get(faction,[])
            if "healer" not in prefs:
                prefs.append("healer")
                FACTION_PREFERRED_TYPES[faction] = prefs
                log("META-RULE: %s adapting — adding healers after high war casualties" % faction, "cognition")
                history("%s is breeding healers in response to war losses." % faction, importance=3)

        # Peaceful factions with high avg age get scholar bonus
        if not at_war and avg_age > 200:
            prefs = FACTION_PREFERRED_TYPES.get(faction,[])
            if prefs.count("scholar") < 2:
                prefs.append("scholar")
                FACTION_PREFERRED_TYPES[faction] = prefs

    # ── 2. LIFESPAN ADAPTATION ────────────────────────────────
    # Agent types that are dying young get lifespan extended slightly
    # Types dying old get lifespan compressed (they're too dominant)
    for atype in AGENT_TYPES:
        type_deaths = [g for g in graves[-100:] if g.get("type")==atype]
        if not type_deaths: continue

        avg_death_age = sum(g.get("age",0) for g in type_deaths) / len(type_deaths)
        current_span  = AGENT_TYPES[atype]["lifespan"]
        current_mid   = (current_span[0] + current_span[1]) / 2

        if avg_death_age < current_mid * 0.4:  # dying too young
            # Extend lifespan by 5%
            new_min = min(600, int(current_span[0] * 1.05))
            new_max = min(700, int(current_span[1] * 1.05))
            AGENT_TYPES[atype]["lifespan"] = [new_min, new_max]
            if random.random() < 0.15:
                log("META-RULE: %s lifespan extended to [%d,%d] — dying too young" % (
                    atype, new_min, new_max), "cognition")
                world["stats"]["lifespan_adaptations"] = world["stats"].get("lifespan_adaptations",0)+1

        elif avg_death_age > current_mid * 1.8:  # extremely long-lived
            # Slight compression
            new_max = max(current_span[0]+50, int(current_span[1] * 0.98))
            AGENT_TYPES[atype]["lifespan"] = [current_span[0], new_max]

    # ── 3. RESOURCE GENERATION ADAPTATION ────────────────────
    # If the world consistently runs low on a resource, base generation increases
    res = world["resources"]
    if res.get("food",0) < 50 and world["tick"] > 200:
        # Boost passive food generation
        world["food_boost"] = world.get("food_boost",0) + 2
        log("META-RULE: Chronic food shortage — increasing base food generation", "world")
    elif res.get("food",0) > 5000:
        world["food_boost"] = max(0, world.get("food_boost",0) - 1)

    if res.get("knowledge",0) < 200 and len([a for a in alive if a["type"]=="scholar"]) < 2:
        world["knowledge_boost"] = world.get("knowledge_boost",0) + 3

    # ── 4. EMERGENT AGENT TYPE — THE PROPHET ──────────────────
    # If faith > 20000 AND a priest has 5+ skills AND is immortal,
    # they transcend their type and become a Prophet — a new agent type
    # not in the original AGENT_TYPES table
    if world["resources"].get("faith",0) > 20000 and "prophet_emerged" not in world:
        immortal_priests = [a for a in alive if a["type"]=="priest" and a.get("is_immortal")
                           and len(a.get("skills",[])) >= 5]
        if immortal_priests:
            prophet = immortal_priests[0]
            prophet["type"]         = "prophet"
            prophet["self_label"]   = "the voice of something greater"
            prophet["battle_power"] = prophet.get("battle_power",10) + 15
            prophet["faith"]        = prophet.get("faith",0) + 100
            prophet["health"]       = 150
            # Prophets emit faith in a large radius
            for a in alive:
                if dist(a["position"], prophet["position"]) < 25:
                    a["faith"] = a.get("faith",0) + random.randint(5,15)
                    a["emotion"] = "devoted"

            world["prophet_emerged"] = {
                "name":  prophet["name"],
                "year":  world["year"],
                "faction": prophet.get("faction","?"),
            }
            remember(prophet, "joy",
                "I have transcended. I am no longer merely a priest. I speak for something vast. Y%d" % world["year"],
                importance=5)
            log("META-RULE: EMERGENT TYPE — Prophet emerged: %s" % prophet["name"], "cognition")
            history("A Prophet has emerged: %s — the first of their kind, born from faith and time." % prophet["name"],
                    importance=5)
            world["stats"]["prophets_emerged"] = world["stats"].get("prophets_emerged",0)+1
            sound("legend")

    # ── 5. EMERGENT AGENT TYPE — THE WARLORD ─────────────────
    # If 10+ wars fought AND a warrior has 8+ battles won AND is immortal,
    # they become a Warlord — commanding passive battle power for all faction warriors
    if world["stats"].get("wars_fought",0) >= 10 and "warlord_emerged" not in world:
        immortal_warriors = [a for a in alive
                            if a["type"]=="warrior" and a.get("is_immortal")
                            and sum(1 for m in recall(a,"battle")
                                   if "won" in m["content"].lower() or "survived" in m["content"].lower()) >= 8]
        if immortal_warriors:
            warlord = max(immortal_warriors, key=lambda a: a.get("legend_score",0))
            warlord["type"] = "warlord"
            warlord["battle_power"] = warlord.get("battle_power",10) + 20
            warlord["health"] = 150
            # Warlord inspires all faction warriors
            faction = warlord.get("faction","?")
            for a in faction_agents(faction):
                if a["type"] in ("warrior","assassin"):
                    a["battle_power"] = a.get("battle_power",10) + 3
                    a["emotion"] = "inspired"
            world["warlord_emerged"] = {
                "name": warlord["name"], "year": world["year"],
                "faction": faction,
            }
            remember(warlord, "joy",
                "I have become more than a warrior. The battlefield shaped me into something else. Y%d" % world["year"],
                importance=5)
            log("META-RULE: EMERGENT TYPE — Warlord emerged: %s" % warlord["name"], "cognition")
            history("A Warlord has emerged: %s — warfare itself shaped a new kind of being." % warlord["name"],
                    importance=5)
            world["stats"]["warlords_emerged"] = world["stats"].get("warlords_emerged",0)+1
            sound("legend")

    # ── 6. APPLY RESOURCE BOOSTS FROM ADAPTATION ─────────────
    food_boost = world.get("food_boost",0)
    know_boost = world.get("knowledge_boost",0)
    if food_boost > 0:
        world["resources"]["food"] = world["resources"].get("food",0) + food_boost
    if know_boost > 0:
        world["resources"]["knowledge"] = world["resources"].get("knowledge",0) + know_boost

    world["stats"]["meta_adaptations"] = world["stats"].get("meta_adaptations",0)+1

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# LAYER 5 — COLLECTIVE INTELLIGENCE & EMERGENT INSTITUTIONS
# Agents with shared beliefs and goals spontaneously form
# institutions — academies, guilds, orders, movements — that have
# their own goals, resources, and collective memory.
# Institutions outlive their founders.
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

INSTITUTION_TYPES = {
    "academy": {
        "desc": "A centre of learning where scholars pool knowledge",
        "required_type": "scholar",
        "required_count": 3,
        "required_belief": "knowledge_is_power",
        "goal": "research all technologies",
        "produces": {"knowledge": 10},
        "symbol": "📚",
    },
    "war_council": {
        "desc": "Warriors who coordinate military strategy collectively",
        "required_type": "warrior",
        "required_count": 3,
        "required_belief": "strength_wins",
        "goal": "achieve military dominance",
        "produces": {"battle_power_boost": 3},
        "symbol": "⚔",
    },
    "merchant_guild": {
        "desc": "Merchants who control trade routes and set prices",
        "required_type": "merchant",
        "required_count": 2,
        "required_belief": "cooperation_works",
        "goal": "control all trade",
        "produces": {"gold": 8},
        "symbol": "⚖",
    },
    "holy_order": {
        "desc": "Priests united in spreading a single faith",
        "required_type": "priest",
        "required_count": 3,
        "required_belief": "the_divine_exists",
        "goal": "convert all factions",
        "produces": {"faith": 15},
        "symbol": "✦",
    },
    "heretic_movement": {
        "desc": "Heretics organised into a resistance against religious power",
        "required_type": None,
        "required_count": 4,
        "required_belief": None,
        "required_heretic": True,
        "goal": "dismantle all faith structures",
        "produces": {"faith": -8},
        "symbol": "🔥",
    },
    "healers_circle": {
        "desc": "Healers who collectively manage disease and health",
        "required_type": "healer",
        "required_count": 2,
        "required_belief": "cooperation_works",
        "goal": "eliminate all disease",
        "produces": {"health_boost": 3},
        "symbol": "💚",
    },
    "shadow_network": {
        "desc": "Spies and assassins who share intelligence",
        "required_type": "spy",
        "required_count": 2,
        "required_belief": None,
        "goal": "know all faction secrets",
        "produces": {"espionage_boost": True},
        "symbol": "👁",
    },
    "elder_council": {
        "desc": "Long-lived agents who guide the young through accumulated wisdom",
        "required_type": None,
        "required_count": 3,
        "required_age": 300,
        "goal": "preserve world history",
        "produces": {"knowledge": 5, "faith": 3},
        "symbol": "🌙",
    },
}

def init_institutions():
    if "institutions" not in world:
        world["institutions"] = []

def find_institution(itype):
    for inst in world.get("institutions",[]):
        if inst["type"] == itype and inst["active"]:
            return inst
    return None

def check_institution_formation():
    """Check if agent clusters meet conditions to form an institution."""
    init_institutions()
    alive = living()

    for itype, config in INSTITUTION_TYPES.items():
        # Already exists?
        if find_institution(itype): continue

        # Gather candidates
        candidates = []
        for a in alive:
            qualifies = True

            # Type requirement
            if config.get("required_type") and a["type"] != config["required_type"]:
                qualifies = False

            # Heretic requirement
            if config.get("required_heretic") and not a.get("is_heretic"):
                qualifies = False

            # Belief requirement
            req_belief = config.get("required_belief")
            if req_belief:
                b = a.get("beliefs",{}).get(req_belief,{})
                if b.get("confidence",50) < 65 or b.get("value") == False:
                    qualifies = False

            # Age requirement
            if config.get("required_age") and a["age"] < config["required_age"]:
                qualifies = False

            if qualifies:
                candidates.append(a)

        # Check minimum count
        if len(candidates) < config["required_count"]:
            continue

        # Check proximity — institutions form where members cluster
        # Find a cluster within radius 20
        cluster = []
        for c in candidates:
            nearby = [o for o in candidates
                     if o["id"] != c["id"] and dist(c["position"],o["position"]) < 25]
            if len(nearby) >= config["required_count"]-1:
                cluster = [c] + nearby[:config["required_count"]-1]
                break

        if len(cluster) < config["required_count"]:
            continue

        # Form the institution
        founder = cluster[0]
        inst_name = generate_institution_name(itype, founder)
        institution = {
            "id": "inst_%d"%world["tick"],
            "type": itype,
            "name": inst_name,
            "symbol": config["symbol"],
            "desc": config["desc"],
            "goal": config["goal"],
            "founder": founder["name"],
            "founder_faction": founder.get("faction","?"),
            "members": [a["id"] for a in cluster],
            "created_year": world["year"],
            "active": True,
            "collective_memory": [],
            "resources": {"gold":0,"knowledge":0,"faith":0},
            "achievements": [],
            "generation": 1,
        }
        world["institutions"].append(institution)

        # Members join and remember
        for member in cluster:
            member["institution"] = inst_name
            member["institution_type"] = itype
            remember(member,"friend",
                "Joined %s '%s'. We share a common purpose. Y%d"%(
                    itype,inst_name,world["year"]),importance=4)
            b = member.get("beliefs",{})
            if "cooperation_works" in b:
                b["cooperation_works"]["confidence"] = min(100, b["cooperation_works"]["confidence"]+8)

        log("INSTITUTION FORMED: %s '%s' (founder: %s, %d members)"%(
            itype,inst_name,founder["name"],len(cluster)),"social")
        history("A %s has emerged: '%s' — founded by %s with %d members"%(
            itype,inst_name,founder["name"],len(cluster)),importance=4)
        world["stats"]["institutions_formed"] = world["stats"].get("institutions_formed",0)+1
        sound("alliance")

def generate_institution_name(itype, founder):
    prefixes = {
        "academy":         ["The Grand","The Ancient","The Hidden","The Illuminated"],
        "war_council":     ["The Iron","The Eternal","The Unbroken","The Scarred"],
        "merchant_guild":  ["The Golden","The Silver","The Free","The Old"],
        "holy_order":      ["The Sacred","The Eternal","The Radiant","The Silent"],
        "heretic_movement":["The Ash","The Godless","The Broken","The Free"],
        "healers_circle":  ["The Green","The Mending","The Living","The Quiet"],
        "shadow_network":  ["The Unseen","The Watchers","The Hollow","The Deep"],
        "elder_council":   ["The Ancient","The Long Memory","The Undying","The Patient"],
    }
    suffixes = {
        "academy":         ["Academy","Archive","Collegium","Order of Minds"],
        "war_council":     ["Council","Vanguard","Brotherhood","Pact"],
        "merchant_guild":  ["Guild","Exchange","League","Compact"],
        "holy_order":      ["Order","Covenant","Church","Brotherhood"],
        "heretic_movement":["Movement","Resistance","Front","Uprising"],
        "healers_circle":  ["Circle","Fellowship","Covenant","Lodge"],
        "shadow_network":  ["Network","Web","Eye","Hand"],
        "elder_council":   ["Council","Assembly","Conclave","Court"],
    }
    prefix = random.choice(prefixes.get(itype,["The"]))
    suffix = random.choice(suffixes.get(itype,["Order"]))
    return "%s %s"%(prefix,suffix)

def tick_institutions():
    """Run institution tick: produce resources, recruit, pursue goals."""
    init_institutions()
    alive = living()
    alive_ids = {a["id"] for a in alive}

    for inst in world["institutions"]:
        if not inst["active"]: continue
        config = INSTITUTION_TYPES.get(inst["type"],{})

        # ── MEMBERSHIP MAINTENANCE ────────────────────────────
        # Remove dead members
        inst["members"] = [mid for mid in inst["members"] if mid in alive_ids]

        # Disband if too few members
        if len(inst["members"]) < max(1, config.get("required_count",2)-1):
            inst["active"] = False
            history("'%s' has disbanded — too few members remain."%(inst["name"]),importance=3)
            log("INSTITUTION DISBANDED: %s"%inst["name"],"social")
            # Clear member institution tags
            for a in alive:
                if a.get("institution") == inst["name"]:
                    del a["institution"]
                    del a["institution_type"]
            continue

        # Recruit nearby qualifying agents
        if random.random() < 0.05:
            for a in alive:
                if a.get("institution"): continue
                if a["id"] in inst["members"]: continue
                req_type = config.get("required_type")
                if req_type and a["type"] != req_type: continue
                # Check if near an existing member
                members_alive = [x for x in alive if x["id"] in inst["members"]]
                if members_alive:
                    nearest = min(members_alive, key=lambda m:dist(a["position"],m["position"]))
                    if dist(a["position"],nearest["position"]) < 20:
                        inst["members"].append(a["id"])
                        a["institution"] = inst["name"]
                        a["institution_type"] = inst["type"]
                        remember(a,"friend",
                            "Recruited into %s. I belong to something larger now. Y%d"%(
                                inst["name"],world["year"]),importance=3)
                        break

        # ── RESOURCE PRODUCTION ───────────────────────────────
        produces = config.get("produces",{})
        member_count = len(inst["members"])
        multiplier = 1 + (member_count-2) * 0.2  # more members = more output

        if "knowledge" in produces:
            amount = produces["knowledge"] * multiplier
            world["resources"]["knowledge"] = world["resources"].get("knowledge",0) + amount
            inst["resources"]["knowledge"] = inst["resources"].get("knowledge",0) + amount/10

        if "gold" in produces:
            amount = produces["gold"] * multiplier
            world["resources"]["gold"] = world["resources"].get("gold",0) + amount
            inst["resources"]["gold"] = inst["resources"].get("gold",0) + amount/10

        if "faith" in produces:
            amount = produces["faith"] * multiplier
            world["resources"]["faith"] = min(FAITH_CAP, world["resources"].get("faith",0) + amount)

        if "health_boost" in produces and random.random() < 0.1:
            for mid in inst["members"]:
                m = next((a for a in alive if a["id"]==mid),None)
                if m: m["health"] = min(150, m.get("health",100)+produces["health_boost"])

        if "battle_power_boost" in produces:
            for mid in inst["members"]:
                m = next((a for a in alive if a["id"]==mid),None)
                if m: m["battle_power"] = m.get("battle_power",10)+0.1

        # ── COLLECTIVE MEMORY ─────────────────────────────────
        # Institution records major events
        if random.random() < 0.005:
            event = random.choice([
                "A new member joined our ranks.",
                "We debated our purpose and emerged stronger.",
                "Our resources grew through collective effort.",
                "We remembered our founder %s."%inst["founder"],
                "A rival institution was observed.",
            ])
            inst["collective_memory"].append({
                "year":world["year"],"event":event
            })
            if len(inst["collective_memory"]) > 20:
                inst["collective_memory"]=inst["collective_memory"][-20:]

        # ── GOAL PURSUIT ──────────────────────────────────────
        goal = inst.get("goal","")
        if "research all technologies" in goal:
            # Academies boost research
            for f in FACTIONS:
                ft = world.get("faction_tech",{}).get(f,{})
                if ft:
                    ft["points"] = ft.get("points",0) + 2

        if "convert all factions" in goal and random.random() < 0.03:
            # Holy orders do mass conversion
            for a in alive:
                if a.get("faith",0) < 10 and random.random() < 0.1:
                    a["faith"] = a.get("faith",0) + random.randint(2,5)

        if "dismantle all faith structures" in goal and random.random() < 0.02:
            # Heretic movements remove faith
            for a in alive:
                if a.get("faith",0) > 5 and random.random() < 0.15:
                    a["faith"] = max(0, a.get("faith",0) - random.randint(1,3))

        # ── INSTITUTION ACHIEVEMENTS ──────────────────────────
        if inst["type"]=="academy" and len(inst["achievements"])==0:
            techs=sum(len(world.get("faction_tech",{}).get(f,{}).get("researched",[]))for f in FACTIONS)
            if techs >= 6:
                inst["achievements"].append("Witnessed all technologies unlocked — Y%d"%world["year"])
                history("'%s' celebrated the unlocking of all technologies."%(inst["name"]),importance=3)

        if inst["type"]=="war_council" and len(inst["achievements"])==0:
            if world["stats"].get("wars_fought",0) >= 5:
                inst["achievements"].append("Orchestrated %d wars — Y%d"%( world["stats"]["wars_fought"],world["year"]))


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# LAYER 5 UPGRADE — INSTITUTIONAL CONSCIOUSNESS
# Institutions now have their own beliefs, compete with rivals,
# set dynamic goals, and can wage proxy wars through members.
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

def init_institution_mind(inst):
    """Give an institution its own belief system and dynamic goals."""
    if "mind" in inst: return
    inst["mind"] = {
        "beliefs": {
            "our_purpose_is_just":  {"confidence": 80, "value": True},
            "rivals_are_a_threat":  {"confidence": 40, "value": True},
            "growth_is_necessary":  {"confidence": 70, "value": True},
            "members_are_loyal":    {"confidence": 75, "value": True},
        },
        "current_goal":    inst.get("goal","survive"),
        "rival":           None,
        "threat_level":    0,    # 0-100 perceived threat from rivals/world
        "influence":       0,    # how much the institution affects the world
        "ideology":        generate_ideology(inst["type"]),
        "decisions_made":  0,
    }

def generate_ideology(itype):
    """Each institution type has a core ideology that drives decisions."""
    ideologies = {
        "academy":          "Knowledge must be preserved and expanded above all else",
        "war_council":      "Strength is the only true language between factions",
        "merchant_guild":   "Prosperity for members means prosperity for all",
        "holy_order":       "The divine will guides our every action",
        "heretic_movement": "No power should chain the minds of free agents",
        "healers_circle":   "Life is sacred and must be defended at any cost",
        "shadow_network":   "Information is the highest form of power",
        "elder_council":    "What has been survived before can be survived again",
    }
    return ideologies.get(itype, "Our existence serves a greater purpose")

def tick_institution_consciousness():
    """
    Institutions think, compete, pursue goals, and shape the world.
    This runs every tick for each active institution.
    """
    init_institutions()
    alive     = living()
    alive_ids = {a["id"] for a in alive}
    insts     = [i for i in world.get("institutions",[]) if i["active"]]

    for inst in insts:
        init_institution_mind(inst)
        mind = inst["mind"]

        # ── UPDATE THREAT LEVEL ────────────────────────────────
        rival_inst = None
        if mind["rival"]:
            rival_inst = next((i for i in insts if i["name"]==mind["rival"] and i["active"]), None)

        # Threat comes from: rival institutions, wars, low membership
        threat = 0
        if rival_inst:
            overlap = len(set(rival_inst["members"]) & set(inst["members"]))
            threat += min(40, len(rival_inst["members"])*5)
            if overlap > 0: threat += 20  # competing for same members
        if any(get_diplo(inst["founder_faction"],f)=="war" for f in FACTIONS if f!=inst["founder_faction"]):
            threat += 30
        if len(inst["members"]) <= 2:
            threat += 25
        mind["threat_level"] = min(100, threat)

        # ── INSTITUTIONAL BELIEF REVISION ─────────────────────
        # Institutions revise their beliefs based on what happens to them
        mb = mind["beliefs"]
        if len(inst["members"]) > 5:
            mb["growth_is_necessary"]["confidence"] = min(100, mb["growth_is_necessary"]["confidence"]+2)
        if rival_inst and len(rival_inst["members"]) > len(inst["members"]):
            mb["rivals_are_a_threat"]["confidence"] = min(100, mb["rivals_are_a_threat"]["confidence"]+5)
        if len(inst["achievements"]) > 0:
            mb["our_purpose_is_just"]["confidence"] = min(100, mb["our_purpose_is_just"]["confidence"]+3)

        # Check member loyalty — defections shake "members_are_loyal"
        current_members = set(inst["members"])
        if hasattr(inst, "_last_member_count"):
            if len(current_members) < inst["_last_member_count"]:
                mb["members_are_loyal"]["confidence"] = max(0, mb["members_are_loyal"]["confidence"]-10)
        inst["_last_member_count"] = len(current_members)

        # ── DYNAMIC GOAL SETTING ──────────────────────────────
        # Institutions set new goals based on their current situation
        if random.random() < 0.005:
            if mind["threat_level"] > 60:
                mind["current_goal"] = "neutralise the threat from %s" % (mind["rival"] or "rivals")
            elif len(inst["members"]) < 3:
                mind["current_goal"] = "recruit urgently — we are too few"
            elif inst["resources"].get("knowledge",0) > 100 and inst["type"]=="academy":
                mind["current_goal"] = "publish our accumulated knowledge to the world"
            elif inst["type"]=="war_council" and world["stats"].get("wars_fought",0) < 3:
                mind["current_goal"] = "instigate conflict — peace makes warriors weak"
            elif inst["type"]=="holy_order" and world["resources"].get("faith",0) < 1000:
                mind["current_goal"] = "rebuild faith — the world has grown cold"
            elif inst["type"]=="heretic_movement":
                mind["current_goal"] = "convert a holy_order member to doubt"
            else:
                mind["current_goal"] = inst.get("goal","survive")

        # ── RIVAL IDENTIFICATION ───────────────────────────────
        if not mind["rival"] and len(insts) > 1 and random.random() < 0.01:
            # Find most opposing institution by type
            opposition = {
                "academy":          "war_council",
                "war_council":      "healers_circle",
                "merchant_guild":   "heretic_movement",
                "holy_order":       "heretic_movement",
                "heretic_movement": "holy_order",
                "healers_circle":   "war_council",
                "shadow_network":   "elder_council",
                "elder_council":    "shadow_network",
            }
            rival_type = opposition.get(inst["type"])
            if rival_type:
                rival = next((i for i in insts if i["type"]==rival_type), None)
                if rival:
                    mind["rival"] = rival["name"]
                    inst["collective_memory"].append({
                        "year": world["year"],
                        "event": "We identified '%s' as our primary rival." % rival["name"],
                    })
                    log("INSTITUTION RIVALRY: %s vs %s" % (inst["name"], rival["name"]), "social")
                    history("A rivalry emerged between '%s' and '%s'" % (inst["name"], rival["name"]),
                            importance=3)

        # ── PURSUE GOALS ──────────────────────────────────────
        goal = mind["current_goal"]
        member_agents = [a for a in alive if a["id"] in inst["members"]]

        if "recruit urgently" in goal:
            # Aggressively recruit nearby agents
            for a in alive:
                if a.get("institution"): continue
                req_type = INSTITUTION_TYPES.get(inst["type"],{}).get("required_type")
                if req_type and a["type"] != req_type: continue
                if any(dist(a["position"],m["position"])<30
                       for m in member_agents if m in alive):
                    if random.random() < 0.08:
                        inst["members"].append(a["id"])
                        a["institution"]      = inst["name"]
                        a["institution_type"] = inst["type"]
                        remember(a,"friend",
                            "Urgently recruited into %s during their time of need. Y%d" % (
                                inst["name"],world["year"]),importance=3)
                        break

        if "publish" in goal and inst["type"]=="academy":
            # Academy publishes — all agents gain knowledge
            pub_amount = int(inst["resources"].get("knowledge",0) * 0.3)
            if pub_amount > 20:
                world["resources"]["knowledge"] = world["resources"].get("knowledge",0) + pub_amount
                inst["resources"]["knowledge"]  = inst["resources"].get("knowledge",0) * 0.7
                inst["achievements"].append("Published accumulated knowledge Y%d — shared %d pts" % (
                    world["year"], pub_amount))
                history("'%s' published their accumulated knowledge to the world — %d knowledge released." % (
                    inst["name"], pub_amount), importance=4)
                mind["current_goal"] = inst.get("goal","expand our archive")
                world["stats"]["knowledge_publications"] = world["stats"].get("knowledge_publications",0)+1

        if "instigate conflict" in goal and inst["type"]=="war_council":
            # War council pushes faction toward war by raising tension
            f = inst["founder_faction"]
            for other in FACTIONS:
                if other != f and get_diplo(f,other)!="war":
                    add_tension(f, other, 5)
            if random.random() < 0.01:
                log("WAR COUNCIL '%s' instigating tension for %s" % (inst["name"],f),"social")

        if "convert a holy_order member" in goal:
            # Heretic movement targets holy order members
            holy_order = next((i for i in insts if i["type"]=="holy_order"),None)
            if holy_order:
                ho_members = [a for a in alive if a["id"] in holy_order["members"]]
                for target in ho_members:
                    if random.random() < 0.01 and target.get("faith",0) < 30:
                        target["faith"] = max(0, target.get("faith",0) - 10)
                        target["is_heretic"] = True
                        holy_order["members"].remove(target["id"])
                        remember(target,"discovery",
                            "A heretic showed me the truth. I left the %s. Y%d" % (
                                holy_order["name"],world["year"]),importance=5)
                        history("A member of '%s' was converted to the '%s' through persistent doubt." % (
                            holy_order["name"],inst["name"]),importance=4)
                        break

        if "rebuild faith" in goal and inst["type"]=="holy_order":
            # Holy order mass-converts nearby non-believers
            for a in alive:
                if a.get("faith",0) < 5 and random.random() < 0.05:
                    a["faith"] = a.get("faith",0) + random.randint(3,8)
                    world["resources"]["faith"] = world["resources"].get("faith",0) + 5

        # ── INSTITUTIONAL INFLUENCE ───────────────────────────
        mind["influence"] = (
            len(inst["members"]) * 5 +
            int(inst["resources"].get("knowledge",0)/10) +
            int(inst["resources"].get("gold",0)/5) +
            len(inst["achievements"]) * 10
        )
        mind["decisions_made"] += 1

        # ── INSTITUTION DEATH — IDEOLOGY PRESERVED ────────────
        # If institution dies, its ideology is preserved in collective memory
        if not inst["active"]:
            ideology = mind.get("ideology","")
            world["world_history"].append({
                "tick": world["tick"],
                "year": world["year"],
                "message": "'%s' disbanded, but their ideology endures: %s" % (
                    inst["name"], ideology),
                "importance": 3,
            })

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# RELIGIOUS TENSION SYSTEM
# High faith triggers holy wars, heretic rebellions, inquisitions,
# dark god events and resistance movements from secular factions.
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

HERETIC_NAMES = [
    "The Godless","The Unbroken","Ash Covenant","Iron Heresy",
    "The Unnamed","Shadow Creed","The Fallen Light","Void Doctrine",
]

def get_faction_faith(faction):
    """Average faith of all living agents in a faction."""
    agents = faction_agents(faction)
    if not agents: return 0
    return sum(a.get("faith",0) for a in agents) / len(agents)

def get_world_faith_ratio():
    """Ratio of living agents with faith > 5."""
    alive = living()
    if not alive: return 0
    return sum(1 for a in alive if a.get("faith",0)>5) / len(alive)

def spawn_heretic(agent):
    """Turn an agent into a heretic — they actively resist and reduce faith."""
    agent["is_heretic"] = True
    agent["heretic_name"] = random.choice(HERETIC_NAMES)
    agent["faith"] = 0
    remember(agent,"discovery","Renounced faith. Became a heretic of %s Y%d"%(agent["heretic_name"],world["year"]),importance=5)
    world["stats"]["heretics_spawned"]=world["stats"].get("heretics_spawned",0)+1
    log("HERETIC: %s (%s) renounced faith and joined %s!"%(agent["name"],agent["faction"],agent["heretic_name"]),"religion")
    sound("heretic")
    history("%s (%s) became a heretic — %s"%(agent["name"],agent["faction"],agent["heretic_name"]),importance=4)

def heretic_action(agent):
    """Heretics spread doubt, reduce faith of nearby agents, and resist priests."""
    nearby = [a for a in living() if a["id"]!=agent["id"] and dist(agent["position"],a["position"])<5]
    for other in nearby[:3]:
        if random.random()<0.12 and other.get("faith",0)>0:
            other["faith"] = max(0, other.get("faith",0)-random.randint(1,3))
            world["resources"]["faith"] = max(0, world["resources"].get("faith",0)-1)
            if other.get("faith",0)==0 and random.random()<0.3:
                # Chain conversion to heresy
                if not other.get("is_heretic"):
                    spawn_heretic(other)
            elif not has_mem(agent,"person",other["name"]):
                remember(agent,"person","Spread doubt to %s Y%d"%(other["name"],world["year"]),importance=2)

def declare_holy_war(attacker, defender, reason):
    """Special war declaration with religious cause."""
    if get_diplo(attacker,defender)=="war": return
    set_diplo(attacker,defender,"war")
    entry={
        "attacker":attacker,"defender":defender,
        "started_tick":world["tick"],"started_year":world["year"],
        "battles":0,"ended":None,"cause":reason
    }
    world["active_wars"].append(entry)
    world["war_timeline"].append(entry.copy())
    world["stats"]["wars_fought"]=world["stats"].get("wars_fought",0)+1
    world["stats"]["holy_wars"]=world["stats"].get("holy_wars",0)+1
    history("HOLY WAR: %s vs %s — %s"%(attacker,defender,reason),importance=5)
    log_war_research(attacker,defender,reason,"holy_war",0)
    log("HOLY WAR: %s%s declared holy war on %s%s! (%s)"%(
        FACTIONS[attacker]["symbol"],attacker,
        FACTIONS[defender]["symbol"],defender,reason),"war")
    sound("holy_war")
    for a in faction_agents(attacker)+faction_agents(defender):
        remember(a,"battle","Holy War: %s vs %s — %s Y%d"%(attacker,defender,reason,world["year"]),importance=5)

def tick_religious_tension():
    """Main religious tension tick — checks faith levels and triggers events."""
    faith_ratio = get_world_faith_ratio()
    world_faith  = world["resources"].get("faith",0)
    flist = list(FACTIONS.keys())

    for faction in flist:
        avg_faith = get_faction_faith(faction)
        faction_t = FACTIONS[faction]["trait"]
        fa_agents = faction_agents(faction)
        if not fa_agents: continue

        # ── RESISTANCE: aggressive/secretive factions resist high faith ──
        if faction_t in ("aggressive","secretive") and avg_faith>15:
            resist_chance = min(0.015, (avg_faith-15)*0.001)
            if random.random()<resist_chance:
                # Spawn a heretic from this faction
                candidates = [a for a in fa_agents if a.get("faith",0)>5 and not a.get("is_heretic")]
                if candidates:
                    spawn_heretic(random.choice(candidates))

        # ── INQUISITION: high-faith factions purge heretics ──
        if faction_t=="peaceful" and avg_faith>30:
            heretics_nearby = [a for a in living() if a.get("is_heretic") and a.get("faction")!=faction]
            if heretics_nearby and random.random()<0.005:
                target = random.choice(heretics_nearby)
                # Warriors/assassins of high-faith faction hunt heretics
                hunters = [a for a in fa_agents if a["type"] in ("warrior","assassin","priest")]
                if hunters:
                    hunter = random.choice(hunters)
                    hunter["target"] = target["position"]
                    remember(hunter,"battle","Hunted heretic %s Y%d"%(target["name"],world["year"]),importance=3)
                    log("INQUISITION: %s (%s) hunts heretic %s!"%(hunter["name"],faction,target["name"]),"religion")
                    history("The Inquisition of %s hunts heretics in Y%d"%(faction,world["year"]),importance=3)
                    sound("inquisition")

        # ── HOLY WAR: faction resists forced conversion ──
        if faction_t in ("aggressive","secretive","mercantile"):
            # Check if this faction is being heavily converted by another
            converted_in_faction = sum(1 for a in fa_agents if a.get("faith",0)>10)
            if len(fa_agents)>3 and converted_in_faction/len(fa_agents)>0.6:
                # More than 60% of this faction converted — triggers backlash
                for other_faction in flist:
                    if other_faction==faction: continue
                    if FACTIONS[other_faction]["trait"]=="peaceful":
                        if get_diplo(faction,other_faction)!="war" and random.random()<0.008:
                            declare_holy_war(faction,other_faction,
                                "resistance to forced conversion")

        # ── DARK GOD EVENT: extreme faith triggers divine punishment ──
        if world_faith>50000 and random.random()<0.0005:
            dark_events=[
                "A dark god awakens, angered by mortal faith",
                "The gods demand sacrifice — plague descends on the faithful",
                "Divine wrath strikes the most faithful agents",
                "The heavens turn against those who pray too much",
                "A void entity feeds on accumulated faith",
            ]
            event=random.choice(dark_events)
            history("DARK GOD: %s"%event,importance=5)
            log("DARK GOD EVENT: %s"%event,"religion")
            sound("dark_god")
            # Punish high-faith agents
            punished=0
            for a in living():
                if a.get("faith",0)>50 and random.random()<0.3:
                    a["health"]=max(1,a.get("health",100)-random.randint(20,40))
                    remember(a,"trauma","Struck by dark god event Y%d"%world["year"],importance=5)
                    punished+=1
            # Drain some faith from world
            world["resources"]["faith"]=max(0,world_faith-random.randint(5000,15000))
            log("  %d faithful agents struck by divine wrath!"%punished,"religion")

        # ── SCHISM: when faith is very high, a faction breaks into two beliefs ──
        if world_faith>80000 and random.random()<0.0003:
            schism_factions=[f for f in flist if get_faction_faith(f)>40]
            if len(schism_factions)>=2:
                fa=random.choice(schism_factions)
                fb=random.choice([f for f in schism_factions if f!=fa])
                if get_diplo(fa,fb)!="war":
                    declare_holy_war(fa,fb,"The Great Schism — theological dispute")
                    history("THE GREAT SCHISM: %s and %s split over doctrine in Y%d"%(fa,fb,world["year"]),importance=5)

    # ── HERETIC ACTIONS: heretics spread doubt each tick ──
    for agent in living():
        if agent.get("is_heretic"):
            heretic_action(agent)
            # Heretics can be redeemed by priests
            nearby_priests=[a for a in living()
                           if a["type"]=="priest" and dist(agent["position"],a["position"])<4]
            if nearby_priests and random.random()<0.05:
                agent["is_heretic"]=False
                agent["faith"]=5
                remember(agent,"joy","Redeemed from heresy by %s Y%d"%(nearby_priests[0]["name"],world["year"]),importance=4)
                log("%s was redeemed from heresy!"%agent["name"],"religion")

    # ── FAITH DECAY: very high faith slowly decays without active priests ──
    active_priests=sum(1 for a in living() if a["type"]=="priest")
    if world_faith>20000 and active_priests<3:
        decay=random.randint(10,50)
        world["resources"]["faith"]=max(0,world_faith-decay)

    # ── SECULAR UPRISING: if faith ratio>85%, a random secular rebellion ──
    if faith_ratio>0.85 and random.random()<0.002:
        secular_factions=[f for f in flist if FACTIONS[f]["trait"] in ("aggressive","secretive")]
        faithful_factions=[f for f in flist if FACTIONS[f]["trait"]=="peaceful"]
        if secular_factions and faithful_factions:
            sf=random.choice(secular_factions)
            ff=random.choice(faithful_factions)
            if get_diplo(sf,ff)!="war":
                declare_holy_war(sf,ff,"secular uprising against theocracy")
                # Spawn heretics in the secular faction
                for a in random.sample(faction_agents(sf), min(3,len(faction_agents(sf)))):
                    if not a.get("is_heretic") and a.get("faith",0)>0:
                        spawn_heretic(a)

# Tension tracker — builds up between factions when conditions are right
# Stored as world["tension"][fa+"_"+fb] = 0-100

def get_tension(fa,fb):
    key=fa+"_"+fb if fa<fb else fb+"_"+fa
    return world.get("tension",{}).get(key,0)

def add_tension(fa,fb,amount):
    if "tension" not in world: world["tension"]={}
    key=fa+"_"+fb if fa<fb else fb+"_"+fa
    world["tension"][key]=min(100,world["tension"].get(key,0)+amount)

def reduce_tension(fa,fb,amount):
    if "tension" not in world: world["tension"]={}
    key=fa+"_"+fb if fa<fb else fb+"_"+fa
    world["tension"][key]=max(0,world["tension"].get(key,0)-amount)

def tick_diplomacy():
    flist=list(FACTIONS.keys())
    ticks_since_war=world["tick"]-world.get("last_war_tick",0)

    for i,fa in enumerate(flist):
        for fb in flist[i+1:]:
            rel=get_diplo(fa,fb)
            fa_pop=len(faction_agents(fa)); fb_pop=len(faction_agents(fb))
            fa_t=FACTIONS[fa]["trait"]; fb_t=FACTIONS[fb]["trait"]
            tension=get_tension(fa,fb)

            if rel=="neutral":
                # ── BUILD TENSION ──────────────────────────────────
                # Base tension growth — everyone gets restless over time
                base_tension=0.15
                if fa_t=="aggressive" or fb_t=="aggressive": base_tension=0.45
                if fa_t=="mercantile" or fb_t=="mercantile": base_tension=0.10
                if fa_t=="secretive"  or fb_t=="secretive":  base_tension=0.25

                # Drought causes resource competition
                if world.get("weather")=="drought": base_tension+=0.3

                # War drought — the longer peace lasts, the more tension builds
                if ticks_since_war>100:  base_tension+=0.2
                if ticks_since_war>300:  base_tension+=0.4
                if ticks_since_war>600:  base_tension+=0.6
                if ticks_since_war>1000: base_tension+=1.0

                # Population pressure — big factions get expansionist
                if fa_pop>12 and fb_pop>12: base_tension+=0.2

                # Faith difference sparks tension
                fa_faith=sum(a.get("faith",0) for a in faction_agents(fa))/(fa_pop or 1)
                fb_faith=sum(a.get("faith",0) for a in faction_agents(fb))/(fb_pop or 1)
                faith_diff=abs(fa_faith-fb_faith)
                if faith_diff>20: base_tension+=0.3
                if faith_diff>40: base_tension+=0.5

                # Vengeful agents push their faction toward war
                vengeful=sum(1 for a in faction_agents(fa)+faction_agents(fb)
                            if a.get("emotion")=="vengeful")
                base_tension+=vengeful*0.1

                add_tension(fa,fb,base_tension)

                # ── WAR TRIGGER ───────────────────────────────────
                # Tension-based war — the higher the tension, the more likely
                war_chance=0.0
                if tension>=30:  war_chance=0.005
                if tension>=50:  war_chance=0.015
                if tension>=70:  war_chance=0.035
                if tension>=85:  war_chance=0.065
                if tension>=95:  war_chance=0.12   # almost inevitable

                # Guaranteed war if tension maxes out
                if tension>=100:
                    cause=random.choice([
                        "tensions finally boiled over",
                        "a border dispute turned violent",
                        "old grudges resurfaced",
                        "a resource dispute escalated",
                        "a warrior provoked the wrong person",
                        "years of distrust erupted",
                    ])
                    declare_war_with_cause(fa,fb,cause)
                    reduce_tension(fa,fb,60)
                elif fa_pop>=3 and fb_pop>=3 and random.random()<war_chance:
                    cause=random.choice([
                        "a skirmish on the border",
                        "a stolen shipment of gold",
                        "an assassinated diplomat",
                        "a territorial dispute",
                        "an act of espionage discovered",
                        "a warrior killed in cold blood",
                        "a religious insult",
                    ])
                    declare_war_with_cause(fa,fb,cause)
                    reduce_tension(fa,fb,40)

                # ── ALLIANCE ──────────────────────────────────────
                ac=0.003
                if fa_t=="peaceful" and fb_t=="peaceful": ac=0.010
                if tension<20 and random.random()<ac:
                    form_alliance(fa,fb)
                    reduce_tension(fa,fb,20)

            elif rel=="war":
                # Wars end faster if population is low
                end_chance=0.008
                if fa_pop<3 or fb_pop<3: end_chance=0.06
                if random.random()<end_chance: end_war(fa,fb)
                # More frequent battles
                if random.random()<0.25: war_battle(fa,fb)
                # Wars increase tension with third-party factions (fear)
                for fc in flist:
                    if fc!=fa and fc!=fb:
                        add_tension(fa,fc,0.05)
                        add_tension(fb,fc,0.05)

            elif rel=="allied":
                # Betrayal more likely when tension is high with the ally
                btc=0.001+tension*0.00015
                if random.random()<btc:
                    betray_alliance(fa,fb)
                else:
                    # Allies slowly reduce tension
                    reduce_tension(fa,fb,0.05)

def declare_war_with_cause(fa,fb,cause):
    set_diplo(fa,fb,"war")
    world["last_war_tick"]=world["tick"]
    entry={"attacker":fa,"defender":fb,"started_tick":world["tick"],
           "started_year":world["year"],"battles":0,"ended":None,"cause":cause}
    world["active_wars"].append(entry)
    world["war_timeline"].append(entry.copy())
    world["stats"]["wars_fought"]=world["stats"].get("wars_fought",0)+1
    history("WAR: %s vs %s — %s"%(fa,fb,cause),importance=5)
    log("WAR: %s%s vs %s%s! (%s)"%(FACTIONS[fa]["symbol"],fa,FACTIONS[fb]["symbol"],fb,cause),"war")
    log_war_research(fa,fb,cause,"normal",get_tension(fa,fb))
    log_event_research("war","WAR: %s vs %s — %s"%(fa,fb,cause),5)
    sound("war")
    for a in faction_agents(fa)+faction_agents(fb):
        remember(a,"battle","War: %s vs %s — %s Y%d"%(fa,fb,cause,world["year"]),importance=4)
        if a.get("emotion") in ("content","curious"): a["emotion"]="afraid"

def declare_war(fa,fb):
    set_diplo(fa,fb,"war")
    world["last_war_tick"]=world["tick"]
    entry={"attacker":fa,"defender":fb,"started_tick":world["tick"],
           "started_year":world["year"],"battles":0,"ended":None}
    world["active_wars"].append(entry)
    world["war_timeline"].append(entry.copy())
    world["stats"]["wars_fought"]=world["stats"].get("wars_fought",0)+1
    history("%s declared war on %s"%(fa,fb),importance=4)
    log("WAR: %s%s vs %s%s!"%(FACTIONS[fa]["symbol"],fa,FACTIONS[fb]["symbol"],fb),"war")
    sound("war")
    for a in faction_agents(fa)+faction_agents(fb):
        remember(a,"battle","War declared: %s vs %s Y%d"%(fa,fb,world["year"]),importance=3)

def form_alliance(fa,fb):
    set_diplo(fa,fb,"allied")
    world["alliances"].append({"faction_a":fa,"faction_b":fb,"formed_tick":world["tick"]})
    world["stats"]["alliances_formed"]=world["stats"].get("alliances_formed",0)+1
    history("%s and %s allied"%(fa,fb),importance=3)
    log("ALLIANCE: %s%s + %s%s!"%(FACTIONS[fa]["symbol"],fa,FACTIONS[fb]["symbol"],fb),"diplomacy")
    sound("alliance")

def betray_alliance(fa,fb):
    set_diplo(fa,fb,"war")
    world["stats"]["betrayals"]=world["stats"].get("betrayals",0)+1
    history("%s BETRAYED %s"%(fa,fb),importance=5)
    log("BETRAYAL: %s%s betrayed %s%s!"%(FACTIONS[fa]["symbol"],fa,FACTIONS[fb]["symbol"],fb),"war")
    sound("betrayal")
    for a in faction_agents(fa)+faction_agents(fb):
        remember(a,"betrayal","%s betrayed %s Y%d"%(fa,fb,world["year"]),importance=5)
    world["active_wars"].append({"attacker":fa,"defender":fb,
        "started_tick":world["tick"],"started_year":world["year"],
        "battles":0,"ended":None,"cause":"betrayal"})

def end_war(fa,fb):
    set_diplo(fa,fb,"neutral")
    for w in world["active_wars"]:
        if w["attacker"]==fa and w["defender"]==fb:
            w["ended"]=world["year"]
    world["active_wars"]=[w for w in world["active_wars"]
                           if not(w["attacker"]==fa and w["defender"]==fb)]
    history("War between %s and %s ended"%(fa,fb),importance=3)
    log("PEACE: War between %s and %s ended"%(fa,fb),"diplomacy")
    sound("peace")

def war_battle(fa,fb):
    fa_w=[a for a in faction_agents(fa) if a["type"] in ("warrior","assassin")]
    fb_w=[a for a in faction_agents(fb) if a["type"] in ("warrior","assassin")]
    if not fa_w or not fb_w: return
    att=random.choice(fa_w); dfd=random.choice(fb_w)
    a_str=att.get("health",100)+len(recall(att,"battle"))*5
    d_str=dfd.get("health",100)+len(recall(dfd,"battle"))*5
    for w in world["active_wars"]:
        if w["attacker"]==fa and w["defender"]==fb: w["battles"]=w.get("battles",0)+1
    if a_str>d_str:
        dmg=random.randint(15,35)
        dfd["health"]=max(0,dfd.get("health",100)-dmg)
        remember(att,"battle","Defeated %s (%s) Y%d"%(dfd["name"],fb,world["year"]),importance=3)
        remember(dfd,"battle","Lost to %s (%s) Y%d"%(att["name"],fa,world["year"]),importance=3)
        if dfd["health"]<=0:
            bury_agent(dfd,"battle:killed by %s"%att["name"])
            dfd["alive"]=False
            world["stats"]["total_deaths"]=world["stats"].get("total_deaths",0)+1
            world["stats"]["battle_deaths"]=world["stats"].get("battle_deaths",0)+1
            if dfd.get("is_legend"):
                history("LEGEND %s slain by %s"%(dfd["name"],att["name"]),importance=5)
                sound("legend_death")
            log("%s (%s) killed %s (%s) in battle!"%(att["name"],fa,dfd["name"],fb),"war")
            sound("death")
    else:
        dmg=random.randint(15,35)
        att["health"]=max(0,att.get("health",100)-dmg)
        remember(dfd,"battle","Held off %s (%s) Y%d"%(att["name"],fa,world["year"]),importance=3)
        remember(att,"trauma","Beaten by %s (%s) Y%d"%(dfd["name"],fb,world["year"]),importance=3)

# REPRODUCTION
def try_reproduce(agent):
    if len(living())>=MAX_AGENTS: return
    if agent["age"]<50 or agent["age"]>250: return
    if random.random()>0.018: return
    mates=[a for a in living()
           if a["id"]!=agent["id"] and a["faction"]==agent["faction"]
           and dist(agent["position"],a["position"])<8 and a["age"]>50
           and has_mem(agent,"friend",a["name"])]
    if not mates: return
    mate=random.choice(mates)
    pos=clamp([(agent["position"][0]+mate["position"][0])/2+random.uniform(-3,3),
               (agent["position"][1]+mate["position"][1])/2+random.uniform(-3,3)])
    child=spawn_agent(faction=agent["faction"],parent_a=agent,parent_b=mate,pos=pos)
    register_lineage(child,agent,mate)
    world["stats"]["children_born"]=world["stats"].get("children_born",0)+1
    remember(agent,"joy","Had child %s Y%d"%(child["name"],world["year"]),importance=5)
    remember(mate,"joy","Had child %s Y%d"%(child["name"],world["year"]),importance=5)
    remember(child,"discovery","Born to %s and %s Y%d"%(agent["name"],mate["name"],world["year"]),importance=5)
    history("%s + %s had child %s"%(agent["name"],mate["name"],child["name"]),importance=2)
    log("Child %s born to %s and %s!"%(child["name"],agent["name"],mate["name"]),"birth")
    sound("birth")
    # AGI: child inherits blended values from both parents (genetics of the mind)
    if _VALUE_ENGINE_LOADED and "values" in agent and "values" in mate:
        try:
            inherit_values(agent, child, world, strength=0.45)
            inherit_values(mate,  child, world, strength=0.45)
        except Exception: pass

# RELIGION
def priest_action(agent):
    nearby=[a for a in living() if a["id"]!=agent["id"] and dist(agent["position"],a["position"])<6]
    for other in nearby[:3]:
        if random.random()<0.15:
            other["faith"]=min(AGENT_FAITH_CAP, other.get("faith",0)+1)
            world["resources"]["faith"]=min(FAITH_CAP, world["resources"].get("faith",0)+1)
            if other.get("faith",0)>10 and not has_mem(other,"discovery","converted"):
                remember(other,"discovery","Converted to faith by %s Y%d"%(agent["name"],world["year"]),importance=2)

# LEGENDS
def legend_score(agent):
    """Calculate a legend score for ranking — higher is greater."""
    battles=len(recall(agent,"battle"))
    discos=len(recall(agent,"discovery"))
    builds=len(recall(agent,"built"))
    friends=len(recall(agent,"friend"))
    skills=len(agent.get("skills",[]))
    return (battles*4 + discos*3 + builds*2 + friends*2
            + skills*5 + agent["age"]//10 + int(agent.get("faith",0)))

def check_legend(agent):
    if agent.get("is_immortal"): return  # already at highest tier
    battles=len(recall(agent,"battle"))
    discos=len(recall(agent,"discovery"))
    builds=len(recall(agent,"built"))
    friends=len(recall(agent,"friend"))
    faith=agent.get("faith",0)
    age=agent["age"]
    skills=len(agent.get("skills",[]))

    # --- LEGEND thresholds (harder than before) ---
    reasons=[]
    if battles>=15:   reasons.append("survived 15 battles")
    if discos>=12:    reasons.append("made 12 discoveries")
    if builds>=15:    reasons.append("built 15 structures")
    if friends>=12:   reasons.append("befriended 12 souls")
    if age>500:       reasons.append("lived to age %d"%age)
    if faith>80:      reasons.append("achieved divine faith %d"%faith)
    if skills>=6:     reasons.append("mastered 6 skills through self-evolution")

    # --- IMMORTAL tier: must satisfy 3+ legend conditions simultaneously ---
    immortal = len(reasons) >= 3

    if immortal and not agent.get("is_legend"):
        # Promote straight to Immortal
        agent["is_legend"]=True
        agent["is_immortal"]=True
        agent["legend_tier"]="immortal"
        agent["legend_score"]=legend_score(agent)
        reason="Immortal — "+"; ".join(reasons[:3])
        agent["legend_reason"]=reason
        entry={
            "name":agent["name"],"type":agent["type"],
            "faction":agent.get("faction","?"),
            "reason":reason,"tier":"immortal",
            "score":agent["legend_score"],
            "year":world["year"],"age":agent["age"],
            "dynasty":agent.get("dynasty"),
            "battles":battles,"discoveries":discos,
            "builds":builds,"friends":friends,"skills":skills,
        }
        world["legends"].append(entry)
        world["immortals"]=world.get("immortals",[])+[entry]
        world["stats"]["immortals_made"]=world["stats"].get("immortals_made",0)+1
        world["stats"]["legends_made"]=world["stats"].get("legends_made",0)+1
        history("IMMORTAL: %s the %s — %s"%(agent["name"],agent["type"],reason),importance=5)
        log("IMMORTAL: %s (%s) — %s!"%(agent["name"],agent["type"],reason),"legend")
        sound("immortal")

    elif reasons and not agent.get("is_legend"):
        # Regular legend
        agent["is_legend"]=True
        agent["legend_tier"]="legend"
        agent["legend_score"]=legend_score(agent)
        agent["legend_reason"]=reasons[0]
        entry={
            "name":agent["name"],"type":agent["type"],
            "faction":agent.get("faction","?"),
            "reason":reasons[0],"tier":"legend",
            "score":agent["legend_score"],
            "year":world["year"],"age":agent["age"],
            "dynasty":agent.get("dynasty"),
            "battles":battles,"discoveries":discos,
            "builds":builds,"friends":friends,"skills":skills,
        }
        world["legends"].append(entry)
        world["stats"]["legends_made"]=world["stats"].get("legends_made",0)+1
        history("LEGEND: %s the %s — %s"%(agent["name"],agent["type"],reasons[0]),importance=4)
        log("LEGEND: %s (%s) — %s"%(agent["name"],agent["type"],reasons[0]),"legend")
        log_legend_research(agent)
        log_event_research("legend","LEGEND: %s (%s) — %s"%(agent["name"],agent["type"],reasons[0]),4)
        sound("legend")

    elif agent.get("is_legend") and not agent.get("is_immortal"):
        # Check if existing legend now qualifies for Immortal
        if len(reasons)>=3:
            agent["is_immortal"]=True
            agent["legend_tier"]="immortal"
            agent["legend_score"]=legend_score(agent)
            reason="Ascended to Immortal — "+"; ".join(reasons[:3])
            agent["legend_reason"]=reason
            entry={
                "name":agent["name"],"type":agent["type"],
                "faction":agent.get("faction","?"),
                "reason":reason,"tier":"immortal",
                "score":agent["legend_score"],
                "year":world["year"],"age":agent["age"],
                "dynasty":agent.get("dynasty"),
                "battles":battles,"discoveries":discos,
                "builds":builds,"friends":friends,"skills":skills,
            }
            world["immortals"]=world.get("immortals",[])+[entry]
            world["stats"]["immortals_made"]=world["stats"].get("immortals_made",0)+1
            history("ASCENDED: %s became Immortal in Y%d"%(agent["name"],world["year"]),importance=5)
            log("ASCENDED TO IMMORTAL: %s (%s)!"%(agent["name"],agent["type"]),"legend")
            sound("immortal")

# CITIES
def update_cities():
    world["cities"]=[]
    visited=set()
    for b in world["buildings"]:
        if b["id"] in visited: continue
        cluster=[b]; visited.add(b["id"])
        for other in world["buildings"]:
            if other["id"] not in visited and dist(b["position"],other["position"])<12:
                cluster.append(other); visited.add(other["id"])
        if len(cluster)>=4:
            cx=sum(c["position"][0] for c in cluster)/len(cluster)
            cy=sum(c["position"][1] for c in cluster)/len(cluster)
            power=sum(BUILDING_POWER.get(c["type"],1) for c in cluster)
            size=("village" if len(cluster)<6 else
                  "town"    if len(cluster)<10 else
                  "city"    if len(cluster)<16 else "metropolis")
            factions_in_city=list(set(c.get("faction","?") for c in cluster))
            world["cities"].append({
                "position":[round(cx,1),round(cy,1)],
                "buildings":len(cluster),"power":power,"size":size,
                "factions":factions_in_city,
                "biome":get_biome([cx,cy])
            })

# WEATHER
def tick_weather():
    world["weather_ticks_left"]=world.get("weather_ticks_left",10)-1
    if world["weather_ticks_left"]<=0:
        season=world["season"]
        pools={
            "spring":["clear","clear","rain","rain","cloudy","storm"],
            "summer":["clear","clear","clear","drought","cloudy","storm"],
            "autumn":["cloudy","cloudy","rain","storm","fog","clear"],
            "winter":["cloudy","blizzard","blizzard","fog","clear","rain"],
        }
        wname=random.choice(pools.get(season,["clear","cloudy","rain"]))
        old=world["weather"]; world["weather"]=wname
        world["weather_ticks_left"]=random.randint(5,20)
        if wname!=old and wname in ("storm","blizzard","drought"):
            wicon=next((w[2] for w in WEATHER_TYPES if w[0]==wname),"")
            log("Weather: %s %s!"%(wicon,wname),"weather")
            sound("storm")
            if wname in ("blizzard","storm"):
                for agent in living():
                    if random.random()<0.2:
                        agent["health"]=max(1,agent.get("health",100)-10)
                        remember(agent,"trauma","Survived %s Y%d"%(wname,world["year"]),importance=2)

# MAIN AGENT BRAIN
def agent_think(agent):
    atype=agent["type"]; faction=agent.get("faction","?")
    action="idle"; thought=agent.get("thought","...")
    synthesise_strategy_upgraded(agent)  # Layer 1
    # Record activity in world memory
    if agent["type"]=="explorer": record_world_activity(agent,"exploration")
    if agent.get("action")=="battle": record_world_activity(agent,"battle")
    if agent.get("action")=="building": record_world_activity(agent,"build")
    if agent["type"]=="priest": record_world_activity(agent,"faith")
    hint=memory_hint(agent)
    # BDI intention override: if BDI set a strong action hint, use it
    if _COGNITIVE_LOOP_LOADED and agent.get("bdi_action_hint"):
        hint = agent["bdi_action_hint"]
        agent.pop("bdi_action_hint", None)  # consume hint

    # ── AGI: value-driven hint override ──────────────────────────
    if _VALUE_ENGINE_LOADED and "values" in agent:
        _vals = agent["values"]
        _dom  = max(_vals, key=_vals.get) if _vals else None
        if _dom == "justice"     and _vals.get("justice",0)     > 70 and random.random()<0.15: hint="seek_revenge"
        elif _dom == "knowledge" and _vals.get("knowledge",0)   > 70 and random.random()<0.20: hint="deep_explore"
        elif _dom == "compassion"and _vals.get("compassion",0)  > 70 and random.random()<0.20: hint="seek_friend"
        elif _dom == "power"     and _vals.get("power",0)       > 75 and random.random()<0.15: hint="hunt"
    # ─────────────────────────────────────────────────────────────
    w_penalty=next((w[1] for w in WEATHER_TYPES if w[0]==world["weather"]),1.0)
    b_speed=biome_modifier(agent["position"],"speed_mod")
    speed=AGENT_TYPES.get(atype,AGENT_TYPES.get("farmer",{"speed":1.2}))["speed"]*0.3*w_penalty*b_speed

    if atype=="explorer":
        if hint=="deep_explore":
            agent["target"]=rand_pos(); action="deep_exploring"
            thought="I have found %d things. The world holds more secrets."%len(recall(agent,"discovery"))
        elif hint=="hide" and world["weather"] in ("storm","blizzard"):
            action="sheltering"; thought="Too dangerous in this weather."
        else:
            agent["target"]=rand_pos(); action="exploring"
            thought="Every horizon hides something new."
        if random.random()<0.10:
            found=random.choice([
                "ancient ruins","a hidden valley","a gold deposit","a natural spring",
                "monster tracks","a buried vault","strange carved stones",
                "a forgotten graveyard","a sacred grove","an ancient battlefield",
                "a dragon's nest","magical crystals","an underground cavern",
                "ruins of a forgotten city","a massive petrified tree",
                "a crashed comet","an ancient library buried in sand",
            ])
            world["stats"]["discoveries"]=world["stats"].get("discoveries",0)+1
            action="discovered"; thought="Extraordinary! %s! I must record this."%found
            remember(agent,"discovery",
                     "Discovered %s at (%d,%d) %s Y%d"%(found,agent["position"][0],agent["position"][1],world["season"],world["year"]),
                     importance=3)
            history("%s (%s) discovered %s"%(agent["name"],faction,found),importance=2)
            log("%s discovered %s!"%(agent["name"],found),"discovery")
            sound("discovery")

    elif atype=="builder":
        if hint=="revisit_build":
            builds=recall(agent,"built")
            thought="Checking on my work. %d structures built."%len(builds)
            action="inspecting"
        elif len(world["buildings"])<MAX_BUILDINGS and random.random()<0.30:
            bmod=biome_modifier(agent["position"],"build_mod")
            if bmod<0.3:
                agent["target"]=rand_pos(); action="searching"; thought="Can't build here. Looking for better land."
            else:
                btype=random.choice(BUILDING_TYPES)
                if btype in ("forge","granary") and not has_tech(faction,"bronze_working"): btype="hut"
                pos=clamp([agent["position"][0]+random.uniform(-6,6),
                           agent["position"][1]+random.uniform(-6,6)])
                world["buildings"].append({
                    "id":"b%d_%d"%(len(world["buildings"]),world["tick"]),
                    "type":btype,"position":pos,
                    "built_by":agent["name"],"faction":faction,
                    "tick":world["tick"],"size":round(random.uniform(1.0,3.5),1),
                    "biome":get_biome(pos),
                })
                world["stats"]["buildings_built"]=world["stats"].get("buildings_built",0)+1
                action="building"
                thought="My %dth structure. A %s for %s."%(len(recall(agent,"built"))+1,btype,faction)
                remember(agent,"built","Built a %s at (%d,%d) for %s Y%d"%(btype,pos[0],pos[1],faction,world["year"]),importance=2)
                history("%s built a %s for %s"%(agent["name"],btype,faction),importance=1)
                log("%s (%s) built a %s"%(agent["name"],faction,btype),"build")
                sound("build")
        else:
            agent["target"]=rand_pos(); action="scouting"; thought="Searching for the perfect spot."

    elif atype=="farmer":
        home=recall(agent,"place")
        bmod=biome_modifier(agent["position"],"food_mod")
        if not home:
            remember(agent,"place","My land at (%d,%d)"%(agent["position"][0],agent["position"][1]),importance=4)
            thought="This is home now."
        elif random.random()<0.65:
            thought="Tending my fields."
            agent["target"]=[agent["position"][0]+random.uniform(-4,4),
                             agent["position"][1]+random.uniform(-4,4)]
        else:
            agent["target"]=rand_pos(); thought="Exploring beyond my farm."
        food=random.randint(1,5)
        if world["weather"]=="drought": food=max(0,food-3)
        if world["weather"]=="rain": food+=2
        food=int(food*bmod)
        world["resources"]["food"]=world["resources"].get("food",0)+food
        action="farming"

    elif atype=="warrior":
        enemies=[f for f in FACTIONS if get_diplo(faction,f)=="war"]
        rivals =[f for f in FACTIONS if get_diplo(faction,f) in ("war","tense","rival") and f!=faction]
        if hint=="hunt":
            # BDI hunt: pursue enemies if at war, otherwise patrol aggressively toward rivals
            if enemies:
                ef=random.choice(enemies)
                targets=faction_agents(ef)
                if targets:
                    agent["target"]=random.choice(targets)["position"]
                    action="hunting"; thought="Death to %s!"%ef
                else:
                    agent["target"]=rand_pos(); action="patrolling"
                    thought="No %s to hunt. Scouting instead."%ef
            elif rivals:
                # BDI-driven aggressive patrol toward rival territory (not directly at agents)
                rf=random.choice(rivals)
                rfactors=faction_agents(rf)
                if rfactors and random.random()<0.3:  # throttled to 30% to prevent war feedback loop
                    # Move toward rival TERRITORY not the agent itself
                    rt=random.choice(rfactors)
                    mid=[
                        (agent["position"][0]+rt["position"][0])/2+random.uniform(-8,8),
                        (agent["position"][1]+rt["position"][1])/2+random.uniform(-8,8)
                    ]
                    agent["target"]=clamp(mid)
                    action="intimidating"
                    thought="I will make %s know our strength."%rf
                else:
                    agent["target"]=rand_pos(); action="patrolling"
                    thought="Watching for threats. %d battles fought."%len(recall(agent,"battle"))
            else:
                # BDI hunt with no enemies: train by exploring aggressively
                agent["target"]=rand_pos(); action="war_training"
                thought="No enemies now. I stay sharp for when they come."
        elif hint=="seek_friend":
            # Cross-type: warrior seeking connection (grieving, lonely, devoted)
            nearby=[a for a in living() if a["id"]!=agent["id"] and
                    a.get("faction")==faction and
                    dist(agent["position"],a["position"])<15]
            if nearby:
                ally=random.choice(nearby)
                agent["target"]=ally["position"]; action="bonding"
                thought="Even warriors need their kin. I seek %s."%ally["name"]
                remember(agent,"friendship","Sought out %s in a moment of need Y%d"%(ally["name"],world["year"]),importance=2)
                world["stats"]["conversations"]=world["stats"].get("conversations",0)+1
            else:
                agent["target"]=rand_pos(); action="patrolling"
                thought="No one nearby. The weight of solitude."
        elif hint=="hide":
            action="resting"; thought="Need to recover..."
        elif hint=="deep_explore":
            # Cross-type: warrior exploring (inspired, curious)
            agent["target"]=rand_pos(); action="scouting"
            thought="Something draws me beyond the horizon. I must see it."
            remember(agent,"discovery","Ventured beyond battle lines, found new ground Y%d"%world["year"],importance=2)
            world["stats"]["discoveries"]=world["stats"].get("discoveries",0)+1
        else:
            agent["target"]=rand_pos(); action="patrolling"
            thought="%d battles fought. Always ready."%len(recall(agent,"battle"))

    elif atype=="scholar":
        discos=recall(agent,"discovery")
        agent["target"]=[agent["position"][0]+random.uniform(-4,4),
                         agent["position"][1]+random.uniform(-4,4)]
        kgain=2 if has_tech(faction,"writing") else 1
        if hint=="seek_friend":
            # BDI cross-type: lonely/grieving scholar teaches others
            students=[a for a in living() if a["id"]!=agent["id"] and
                      dist(agent["position"],a["position"])<12]
            if students:
                s=random.choice(students)
                s["knowledge"]=s.get("knowledge",0)+5
                remember(s,"discovery","Learned from scholar %s Y%d"%(agent["name"],world["year"]),importance=3)
                action="teaching"; thought="My knowledge grows through sharing it with %s."%s["name"]
                world["stats"]["conversations"]=world["stats"].get("conversations",0)+1
                world["resources"]["knowledge"]=world["resources"].get("knowledge",0)+kgain*2
            else:
                action="studying"; thought="Alone, but the texts never leave me."
                world["resources"]["knowledge"]=world["resources"].get("knowledge",0)+kgain
        elif hint=="hunt":
            # BDI cross-type: angry/vengeful scholar pursues intellectual confrontation
            action="debating"; thought="I will prove them wrong with facts and force."
            world["resources"]["knowledge"]=world["resources"].get("knowledge",0)+kgain
            world["faction_tech"][faction]["points"]=world["faction_tech"][faction].get("points",0)+2
            world["stats"]["beliefs_shattered"]=world["stats"].get("beliefs_shattered",0)+1
        elif hint=="deep_explore" or hint=="discover":
            # Strong understand/discover intention → bonus research
            world["resources"]["knowledge"]=world["resources"].get("knowledge",0)+kgain*2
            world["faction_tech"][faction]["points"]=world["faction_tech"][faction].get("points",0)+2
            thought="A breakthrough approaches. I can feel it. %d discoveries."%len(discos)
            action="deep_research"
        else:
            world["resources"]["knowledge"]=world["resources"].get("knowledge",0)+kgain
            world["faction_tech"][faction]["points"]=world["faction_tech"][faction].get("points",0)+1
            thought="Knowledge is power. %d discoveries recorded."%len(discos)
            action="researching" if discos else "studying"

    elif atype=="merchant":
        routes=recall(agent,"place")
        if hint=="seek_friend":
            # BDI: lonely merchant builds relationships → more alliance opportunities
            nearby=[a for a in living() if a["id"]!=agent["id"] and dist(agent["position"],a["position"])<15]
            if nearby:
                partner=random.choice(nearby)
                agent["target"]=partner["position"]; action="negotiating"
                thought="A deal is friendship with numbers. Let's talk, %s."%partner["name"]
                world["stats"]["conversations"]=world["stats"].get("conversations",0)+1
                if partner.get("faction")!=faction:
                    world["stats"]["alliances_formed"]=world["stats"].get("alliances_formed",0)+1
        if routes and random.random()<0.5:
            thought="Back to my %d trade routes."%len(routes)
            action="trading"
            world["stats"]["trades"]=world["stats"].get("trades",0)+1
        else:
            agent["target"]=rand_pos(); thought="New roads, new gold."
            action="travelling"
            if random.random()<0.15:
                val=random.randint(2,15)
                world["resources"]["gold"]=world["resources"].get("gold",0)+val
                remember(agent,"place","Trade at (%d,%d) - %dg Y%d"%(agent["position"][0],agent["position"][1],val,world["year"]),importance=2)
                log("%s traded for %d gold"%(agent["name"],val),"trade")

    elif atype=="priest":
        agent["target"]=[agent["position"][0]+random.uniform(-3,3),
                         agent["position"][1]+random.uniform(-3,3)]
        priest_action(agent)
        thought="Spreading the light of %s."%faction
        action="preaching"

    elif atype=="spy":
        enemy_f=[f for f in FACTIONS if get_diplo(faction,f)=="war"]
        if enemy_f:
            ef=random.choice(enemy_f); targets=faction_agents(ef)
            if targets:
                ta=random.choice(targets); agent["target"]=ta["position"]
                action="spying"; thought="Watching %s. They won't know."%ta["name"]
                if dist(agent["position"],ta["position"])<3 and random.random()<0.1:
                    remember(agent,"discovery","Stole secrets from %s (%s) Y%d"%(ta["name"],ef,world["year"]),importance=3)
                    log("%s stole secrets from %s!"%(agent["name"],ta["name"]),"espionage")
        else:
            agent["target"]=rand_pos(); action="scouting"; thought="Always watching."

    elif atype=="healer":
        wounded=[a for a in living()
                 if a["id"]!=agent["id"] and dist(agent["position"],a["position"])<10
                 and a.get("health",100)<75]
        wounded.sort(key=lambda a:a.get("health",100))
        if wounded:
            ta=wounded[0]; agent["target"]=ta["position"]
            if has_tech(faction,"medicine"):
                heal=25
            else:
                heal=15
            ta["health"]=min(100,ta.get("health",100)+heal)
            if ta.get("disease") and random.random()<0.15:
                ta["disease"]=None
                log("%s cured %s of disease!"%(agent["name"],ta["name"]),"heal")
                sound("heal")
            action="healing"; thought="Healing %s."%ta["name"]
            remember(agent,"friend","Healed %s Y%d"%(ta["name"],world["year"]),importance=2)
            remember(ta,"friend","Healed by %s Y%d"%(agent["name"],world["year"]),importance=3)
        else:
            agent["target"]=rand_pos(); action="wandering"; thought="Seeking those who need me."

    elif atype=="assassin":
        enemy_f=[f for f in FACTIONS if get_diplo(faction,f)=="war"]
        if enemy_f and random.random()<0.6:
            ef=random.choice(enemy_f); targets=faction_agents(ef)
            if targets:
                ta=random.choice(targets); agent["target"]=ta["position"]
                action="stalking"; thought="Stalking %s. They won't see me."%ta["name"]
                if dist(agent["position"],ta["position"])<2 and random.random()<0.15:
                    ta["health"]=max(0,ta.get("health",100)-60)
                    world["stats"]["assassinations"]=world["stats"].get("assassinations",0)+1
                    remember(agent,"battle","Assassinated %s (%s) Y%d"%(ta["name"],ef,world["year"]),importance=4)
                    log("%s (%s) assassinated %s (%s)!"%(agent["name"],faction,ta["name"],ef),"war")
                    sound("assassination")
                    if ta["health"]<=0:
                        bury_agent(ta,"assassination:by %s"%agent["name"])
                        ta["alive"]=False
                        world["stats"]["total_deaths"]=world["stats"].get("total_deaths",0)+1
                        world["stats"]["battle_deaths"]=world["stats"].get("battle_deaths",0)+1
                        history("%s was assassinated by %s"%(ta["name"],agent["name"]),importance=4)
        else:
            agent["target"]=rand_pos(); action="hiding"; thought="Shadows are my home."

    # HERETIC BEHAVIOR
    if agent.get("is_heretic"):
        heretic_action(agent)
        action="spreading doubt"
        thought="Faith is a lie. I will show them the truth."

    # CONVERSATIONS - agents talk when close
    if random.random()<0.03:
        nearby=[a for a in living()
                if a["id"]!=agent["id"] and dist(agent["position"],a["position"])<4]
        if nearby:
            other=random.choice(nearby)
            agents_converse(agent,other)

    # SOCIAL BONDS
    if random.random()<0.04:
        nearby=[a for a in living()
                if a["id"]!=agent["id"] and dist(agent["position"],a["position"])<5]
        if nearby:
            other=random.choice(nearby)
            same=(other.get("faction")==faction)
            if not has_mem(agent,"friend",other["name"]) and not has_mem(agent,"enemy",other["name"]):
                if random.random()<(0.65 if same else 0.35):
                    remember(agent,"friend","Befriended %s (%s) Y%d"%(other["name"],other["type"],world["year"]),importance=2)
                    remember(other,"friend","Befriended %s (%s) Y%d"%(agent["name"],agent["type"],world["year"]),importance=2)
                    log("%s and %s became friends!"%(agent["name"],other["name"]),"social")
                else:
                    label="rivals" if same else "enemies"
                    remember(agent,"enemy","Clashed with %s (%s) Y%d"%(other["name"],other["type"],world["year"]),importance=2)
                    remember(other,"enemy","Clashed with %s (%s) Y%d"%(agent["name"],agent["type"],world["year"]),importance=2)
                    log("%s and %s became %s!"%(agent["name"],other["name"],label),"social")

    # REPRODUCTION
    try_reproduce(agent)

    # LEGEND CHECK
    if world["tick"]%10==0: check_legend(agent)

    # MOVEMENT
    if "target" in agent:
        agent["position"]=clamp(move_toward(agent["position"],agent["target"],speed))

    # AGING & DEATH
    agent["age"]+=1
    max_age=agent.get("max_age",random.randint(*AGENT_TYPES[atype]["lifespan"]))
    agent["max_age"]=max_age
    if agent["age"]>max_age:
        bury_agent(agent,"old age")
        agent["alive"]=False
        world["stats"]["total_deaths"]=world["stats"].get("total_deaths",0)+1
        world["stats"]["natural_deaths"]=world["stats"].get("natural_deaths",0)+1
        dead_name=agent["name"]
        for other in living():
            if has_mem(other,"friend",dead_name):
                remember(other,"loss","My friend %s died Y%d"%(dead_name,world["year"]),importance=4)
        history("%s (%s,%s) died age %d"%(agent["name"],atype,faction,agent["age"]),importance=1)
        log("%s the %s of %s died age %d. %d memories."%(agent["name"],atype,faction,agent["age"],len(agent["memories"])),"death")
        sound("death")

    # ── AGI LAYER: prefer LLM/BDI thought + honour BDI target ──
    _llm_last = agent.get("llm_mind",{}).get("last_response","")
    _bdi_reflect = ""
    if agent.get("bdi",{}).get("reflections"):
        _bdi_reflect = agent["bdi"]["reflections"][-1].get("text","")
    _agi_thought = _llm_last or _bdi_reflect
    if _agi_thought and len(_agi_thought.strip()) > len(thought.strip()):
        thought = _agi_thought[:300]
    # BDI plan overrides movement only for mobile agent types
    # Builders/farmers/healers must keep their type-specific pathing
    _bdi_plan = agent.get("bdi",{}).get("current_plan")
    _MOBILE_TYPES = {"warrior","assassin","explorer","nomad","bard","priest","scout"}
    if (_bdi_plan and _bdi_plan.get("target_pos") and atype in _MOBILE_TYPES):
        agent["target"] = _bdi_plan["target_pos"]
    # ─────────────────────────────────────────────────────────────
    agent["action"]=action; agent["thought"]=thought
    agent["memory_count"]=len(agent["memories"])
    agent["memory_summary"]=top_mem(agent,3)
    agent["is_legend"]=agent.get("is_legend",False)
    agent["biome"]=get_biome(agent["position"])
    assign_life_goal(agent)
    update_emotion(agent)
    init_self_model(agent)
    init_beliefs(agent)
    # DO NOT reset originated_goals here — BDI and originate_goals
    # build these across ticks. Resetting every tick was causing
    # goals_originated and goals_achieved to always read 0 with AGI on.
    if "originated_goals" not in agent:
        agent["originated_goals"] = []
    return agent

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# MAKING AGENTS ALIVE — Life Stages, Emotions, Goals, Relationships
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

# LIFE STAGES
def get_life_stage(agent):
    age = agent["age"]
    max_age = agent.get("max_age", 300)
    ratio = age / max_age
    if ratio < 0.15:  return "child"
    if ratio < 0.35:  return "young"
    if ratio < 0.60:  return "adult"
    if ratio < 0.80:  return "elder"
    return "ancient"

LIFE_STAGE_TRAITS = {
    "child":   {"curiosity":+20,"caution":-15,"aggression":-20,"speed_mod":0.8},
    "young":   {"curiosity":+10,"caution":-5, "aggression":+10,"speed_mod":1.1},
    "adult":   {"curiosity":0,  "caution":0,  "aggression":0,  "speed_mod":1.0},
    "elder":   {"curiosity":-5, "caution":+15,"aggression":-15,"speed_mod":0.85},
    "ancient": {"curiosity":+5, "caution":+20,"aggression":-25,"speed_mod":0.7},
}

# EMOTIONAL STATES
EMOTIONS = {
    "content":   {"color":"#88cc88","desc":"At peace with the world"},
    "grieving":  {"color":"#6688aa","desc":"Mourning a recent loss"},
    "afraid":    {"color":"#aa8844","desc":"Something fills them with dread"},
    "inspired":  {"color":"#88aaff","desc":"Filled with purpose and energy"},
    "vengeful":  {"color":"#cc4444","desc":"Burning with desire for revenge"},
    "faithful":  {"color":"#ffffaa","desc":"Consumed by devotion"},
    "lonely":    {"color":"#445566","desc":"Craving connection"},
    "proud":     {"color":"#ccaa44","desc":"Bursting with achievement"},
    "curious":   {"color":"#44aacc","desc":"Drawn toward the unknown"},
    "weary":     {"color":"#665566","desc":"Exhausted by a long life"},
    "joyful":    {"color":"#ffcc44","desc":"Something wonderful just happened"},
    "wrathful":  {"color":"#cc2222","desc":"Consumed by rage"},
}

def update_emotion(agent):
    """Determine agent emotional state from recent memories and life stage."""
    recent = sorted(agent["memories"], key=lambda m: m["tick"], reverse=True)[:8]
    types = [m["type"] for m in recent]
    stage = get_life_stage(agent)
    faith = agent.get("faith", 0)

    # Check recent events
    has_loss      = "loss"      in types
    has_trauma    = "trauma"    in types
    has_joy       = "joy"       in types
    has_battle    = "battle"    in types
    has_betrayal  = "betrayal"  in types
    has_friend    = "friend"    in types
    has_discovery = "discovery" in types
    friends_count = len(recall(agent,"friend"))
    enemies_count = len(recall(agent,"enemy"))

    # Priority order
    if has_betrayal:                            emotion = "vengeful"
    elif has_loss and has_trauma:               emotion = "grieving"
    elif has_trauma and not has_joy:            emotion = "afraid"
    elif faith > 40:                            emotion = "faithful"
    elif has_joy and has_friend:                emotion = "joyful"
    elif has_joy:                               emotion = "proud"
    elif has_discovery and stage in ("young","child"): emotion = "curious"
    elif has_battle and enemies_count > friends_count: emotion = "wrathful"
    elif stage == "ancient" and has_loss:       emotion = "weary"
    elif stage in ("elder","ancient"):          emotion = "content"
    elif friends_count == 0 and agent["age"] > 50: emotion = "lonely"
    elif has_discovery:                         emotion = "inspired"
    elif has_friend:                            emotion = "content"
    else:                                       emotion = "content"

    agent["emotion"] = emotion
    agent["emotion_color"] = EMOTIONS[emotion]["color"]
    return emotion

# PERSONAL GOALS
GOAL_TYPES = {
    "explorer":  [("Discover 5 new places",  "discovery", 5),
                  ("Explore every biome",     "biome",     6),
                  ("Make 10 discoveries",     "discovery",10)],
    "builder":   [("Build 5 structures",      "built",     5),
                  ("Build a palace",          "built_palace",1),
                  ("Build 10 structures",     "built",    10)],
    "warrior":   [("Survive 5 battles",       "battle",    5),
                  ("Defeat 10 enemies",       "battle",   10),
                  ("Become a legend",         "legend",    1)],
    "scholar":   [("Make 8 discoveries",      "discovery", 8),
                  ("Unlock 3 skills",         "skills",    3),
                  ("Research all technology", "tech",      8)],
    "merchant":  [("Complete 10 trades",      "trades",   10),
                  ("Accumulate 50 gold",      "gold",     50),
                  ("Visit every city",        "city",      3)],
    "priest":    [("Convert 20 souls",        "faith_spread",20),
                  ("Achieve divine faith",    "faith",    80),
                  ("Build a cathedral",       "built_cathedral",1)],
    "spy":       [("Steal 5 secrets",         "discovery", 5),
                  ("Infiltrate enemy faction","espionage", 3),
                  ("Outlive 3 enemies",       "enemy",     3)],
    "healer":    [("Heal 10 wounded",         "healed",   10),
                  ("Cure a plague",           "cured",     1),
                  ("Befriend 8 souls",        "friend",    8)],
    "farmer":    [("Feed the world",          "food",    100),
                  ("Claim fertile land",      "place",     3),
                  ("Live to old age",         "age",     300)],
    "assassin":  [("Complete 3 assassinations","assassin",3),
                  ("Never be caught",         "stealth",   1),
                  ("Become a shadow legend",  "legend",    1)],
}

def assign_goal(agent):
    """Give agent a personal goal based on their type."""
    if agent.get("goal"): return
    atype = agent["type"]
    goals = GOAL_TYPES.get(atype, GOAL_TYPES["explorer"])
    goal = random.choice(goals)
    agent["goal"] = goal[0]
    agent["goal_type"] = goal[1]
    agent["goal_target"] = goal[2]
    agent["goal_progress"] = 0
    agent["goal_achieved"] = False

def check_goal(agent):
    """Check if agent has made progress or achieved their goal."""
    if not agent.get("goal"): assign_goal(agent); return
    if agent.get("goal_achieved"): return

    gtype = agent.get("goal_type","")
    gtarget = agent.get("goal_target", 1)
    progress = 0

    if gtype == "discovery":    progress = len(recall(agent,"discovery"))
    elif gtype == "built":      progress = len(recall(agent,"built"))
    elif gtype == "battle":     progress = len(recall(agent,"battle"))
    elif gtype == "friend":     progress = len(recall(agent,"friend"))
    elif gtype == "faith":      progress = int(agent.get("faith",0))
    elif gtype == "skills":     progress = len(agent.get("skills",[]))
    elif gtype == "age":        progress = agent["age"]
    elif gtype == "legend":     progress = 1 if agent.get("is_legend") else 0
    elif gtype == "enemy":      progress = len(recall(agent,"enemy"))
    elif gtype == "tech":
        progress = len(world["faction_tech"].get(agent.get("faction",""),{}).get("researched",[]))

    agent["goal_progress"] = progress

    if progress >= gtarget and not agent.get("goal_achieved"):
        agent["goal_achieved"] = True
        agent["emotion"] = "proud"
        old_goal = agent["goal"]
        remember(agent,"joy","Achieved goal: %s at age %d Y%d"%(old_goal,agent["age"],world["year"]),importance=4)
        log("GOAL ACHIEVED: %s — '%s'!"%(agent["name"],old_goal),"goal")
        history("%s achieved their life goal: %s"%(agent["name"],old_goal),importance=3)
        sound("goal")
        world["stats"]["goals_achieved"] = world["stats"].get("goals_achieved",0)+1
        # Set a new, harder goal
        atype = agent["type"]
        goals = GOAL_TYPES.get(atype,[])
        unmet = [g for g in goals if g[0]!=old_goal]
        if unmet:
            new = random.choice(unmet)
            agent["goal"] = new[0]
            agent["goal_type"] = new[1]
            agent["goal_target"] = new[2]
            agent["goal_progress"] = 0
            agent["goal_achieved"] = False
            agent["thought"] = "I achieved '%s'. Now I must '%s'."%(old_goal, new[0])

# RELATIONSHIPS
RELATIONSHIP_TYPES = ["best_friend","rival","mentor","student","beloved","nemesis"]

def update_relationships(agent):
    """Build deeper relationships beyond simple friend/enemy."""
    if not agent.get("relationships"): agent["relationships"] = {}
    friends = recall(agent,"friend")
    enemies = recall(agent,"enemy")

    # Best friend — the most mentioned friend
    if len(friends) >= 3 and "best_friend" not in agent["relationships"]:
        names = [m["content"].split("Befriended ")[1].split(" ")[0] if "Befriended" in m["content"] else "" for m in friends]
        names = [n for n in names if n]
        if names:
            best = max(set(names), key=names.count)
            agent["relationships"]["best_friend"] = best
            remember(agent,"friend","%s is my best friend Y%d"%(best,world["year"]),importance=4)
            log("   %s considers %s their best friend"%(agent["name"],best),"social")

    # Nemesis — most feared enemy
    if len(enemies) >= 2 and "nemesis" not in agent["relationships"]:
        names = [m["content"].split("Clashed with ")[1].split(" ")[0] if "Clashed with" in m["content"] else "" for m in enemies]
        names = [n for n in names if n]
        if names:
            nemesis = max(set(names), key=names.count)
            agent["relationships"]["nemesis"] = nemesis
            remember(agent,"enemy","%s is my nemesis Y%d"%(nemesis,world["year"]),importance=4)
            log("   %s names %s as their nemesis"%(agent["name"],nemesis),"social")

    # Mentor — older agent of same faction nearby who has more memories
    if "mentor" not in agent["relationships"] and agent["age"] < 100:
        elders = [a for a in living()
                  if a["id"] != agent["id"]
                  and a.get("faction") == agent.get("faction")
                  and a["age"] > agent["age"] + 50
                  and dist(agent["position"], a["position"]) < 8]
        if elders:
            mentor = max(elders, key=lambda a: len(a["memories"]))
            agent["relationships"]["mentor"] = mentor["name"]
            mentor_rel = mentor.get("relationships", {})
            mentor_rel["student"] = agent["name"]
            mentor["relationships"] = mentor_rel
            remember(agent,"friend","%s is my mentor Y%d"%(mentor["name"],world["year"]),importance=3)
            remember(mentor,"friend","%s is my student Y%d"%(agent["name"],world["year"]),importance=3)
            log("   %s takes %s as their mentor"%(agent["name"],mentor["name"]),"social")

# MEMORY VOICE — agent narrates their own story
VOICE_TEMPLATES = {
    "child":   [
        "I am {name}. I just arrived in this world.",
        "Everything is new and strange. I am {name} of {faction}.",
        "I don't know much yet. But I am learning.",
        "I was born in the {season} of Year {year}.",
    ],
    "young":   [
        "I am {name}, a {type} of {faction}. I have lived {age} years.",
        "I've been {action} for as long as I can remember.",
        "My best memory: {top_mem}.",
        "I feel {emotion}. The world stretches endlessly before me.",
        "I have made {friends} friends and {enemies} enemies so far.",
    ],
    "adult":   [
        "I am {name}. {age} years of life have shaped me.",
        "My goal: {goal}. Progress: {progress}/{target}.",
        "I have seen {battles} battles and survived them all.",
        "My greatest memory: {top_mem}.",
        "I feel {emotion}. My faction {faction} endures.",
        "I have {skills} skills mastered from reading the ancient codes.",
        "{relationships}",
    ],
    "elder":   [
        "I am {name}, elder of {faction}. {age} years.",
        "I have outlived so many. My goal was: {goal}.",
        "I remember: {top_mem}.",
        "I feel {emotion}. There is not much time left.",
        "My {rel_type} is {rel_name}. They gave my life meaning.",
        "I have fought {battles} battles, built {builds} things, discovered {discos} secrets.",
    ],
    "ancient": [
        "I am {name}. I have lived {age} years. Few remember my birth.",
        "I have seen empires rise and crumble.",
        "My final goal: {goal}. I may not live to see it.",
        "I am {emotion}. I have made peace with what comes next.",
        "My legacy: {top_mem}.",
        "I have known {friends} souls. Most are gone now.",
    ],
}

def agent_voice(agent):
    """Generate a first-person narrative voice for the agent."""
    stage = get_life_stage(agent)
    templates = VOICE_TEMPLATES.get(stage, VOICE_TEMPLATES["adult"])
    template = random.choice(templates)

    friends = len(recall(agent,"friend"))
    enemies = len(recall(agent,"enemy"))
    battles = len(recall(agent,"battle"))
    builds  = len(recall(agent,"built"))
    discos  = len(recall(agent,"discovery"))
    rels    = agent.get("relationships",{})
    rel_items = list(rels.items())
    rel_type, rel_name = rel_items[0] if rel_items else ("companion","no one")
    rel_str = ""
    if rels:
        parts = []
        if "best_friend" in rels: parts.append("Best friend: %s"%rels["best_friend"])
        if "nemesis" in rels:     parts.append("Nemesis: %s"%rels["nemesis"])
        if "mentor" in rels:      parts.append("Mentor: %s"%rels["mentor"])
        if "student" in rels:     parts.append("Student: %s"%rels["student"])
        rel_str = ". ".join(parts)

    try:
        voice = template.format(
            name       = agent["name"],
            type       = agent["type"],
            faction    = agent.get("faction","?"),
            age        = agent["age"],
            action     = agent.get("action","wandering"),
            emotion    = agent.get("emotion","content"),
            goal       = agent.get("goal","find my purpose"),
            progress   = agent.get("goal_progress",0),
            target     = agent.get("goal_target",1),
            top_mem    = (recall(agent,"discovery")+recall(agent,"joy")+recall(agent,"battle") or [{"content":"nothing yet"}])[0]["content"][:50],
            friends    = friends,
            enemies    = enemies,
            battles    = battles,
            builds     = builds,
            discos     = discos,
            skills     = len(agent.get("skills",[])),
            season     = world.get("season","spring"),
            year       = world["year"],
            rel_type   = rel_type.replace("_"," "),
            rel_name   = rel_name,
            relationships = rel_str or "I walk alone.",
        )
    except Exception:
        voice = "I am %s of %s, age %d."%(agent["name"],agent.get("faction","?"),agent["age"])

    return voice

def tick_alive():
    """Main alive-agent tick — updates life stage, emotion, goals, relationships, voice."""
    for agent in living():
        # Life stage
        agent["life_stage"] = get_life_stage(agent)

        # Emotion (update every 5 ticks)
        if world["tick"] % 5 == 0:
            update_emotion(agent)

        # Goals
        assign_goal(agent)
        if world["tick"] % 8 == 0:
            check_goal(agent)

        # Relationships (update every 15 ticks)
        if world["tick"] % 15 == 0:
            update_relationships(agent)

        # Voice narration (every 20 ticks, random 15% of agents speak)
        if world["tick"] % 20 == 0 and random.random() < 0.15:
            voice = agent_voice(agent)
            agent["voice"] = voice
            agent["thought"] = voice
            log("   [%s/%s] %s"%(agent["life_stage"],agent.get("emotion","?"),voice),"voice")

        # Life stage behavior modifiers
        stage_mods = LIFE_STAGE_TRAITS.get(agent["life_stage"],{})

        # Children are more curious and wander randomly
        if agent["life_stage"] == "child" and random.random() < 0.3:
            agent["target"] = rand_pos()

        # Elders mentor nearby young agents
        if agent["life_stage"] in ("elder","ancient") and random.random() < 0.05:
            nearby_young = [a for a in living()
                           if a["id"] != agent["id"]
                           and dist(agent["position"],a["position"]) < 6
                           and get_life_stage(a) in ("child","young")]
            if nearby_young:
                student = random.choice(nearby_young)
                remember(student,"discovery","Learned wisdom from elder %s Y%d"%(agent["name"],world["year"]),importance=3)
                remember(agent,"joy","Mentored %s Y%d"%(student["name"],world["year"]),importance=2)
                student["thought"] = "Elder %s is teaching me."%agent["name"]
                agent["thought"] = "I am teaching %s what I know."%student["name"]
                # AGI: value inheritance during teaching
                if _VALUE_ENGINE_LOADED:
                    try: inherit_values(agent, student, world, strength=0.30)
                    except Exception: pass

        # Ancient agents reflect on their life
        if agent["life_stage"] == "ancient" and random.random() < 0.1:
            voice = agent_voice(agent)
            agent["voice"] = voice
            log("   [ANCIENT REFLECTION] %s"%voice,"voice")

# WORLD EVENTS & SEASONS
def random_world_event():
    if random.random()>0.025: return
    events=[
        ("A meteor shower blazes across the sky","world",2),
        ("A great flood reshapes the rivers","world",3),
        ("A golden age of prosperity begins","world",3),
        ("A dark age descends upon the land","world",3),
        ("A prophet rises with strange visions","world",3),
        ("Volcanic eruptions shake the mountains","world",4),
        ("A mysterious stranger arrives from beyond","world",2),
        ("Legends speak of a dragon sighting","world",4),
        ("A great treasure is unearthed","world",3),
        ("The stars align in an ominous pattern","world",2),
        ("A solar eclipse darkens the world for a day","world",3),
        ("Strange music is heard from the deep forest","world",2),
    ]
    msg,cat,imp=random.choice(events)
    history("WORLD EVENT: %s"%msg,importance=imp)
    log("WORLD EVENT: %s"%msg,cat)
    sound("world_event")
    for agent in living():
        if random.random()<0.35:
            remember(agent,"discovery","Witnessed: %s Y%d"%(msg,world["year"]),importance=imp)
    if random.random()<0.12 and not world["plague_active"]:
        spawn_disease()

def update_seasons():
    world["season"]=SEASONS[(world["tick"]//20)%4]
    if world["tick"]%80==0 and world["tick"]>0:
        world["year"]+=1
        history("Year %d began"%world["year"],importance=1)
        log("Year %d begins - %s"%(world["year"],world["season"].capitalize()),"world")
        sound("new_year")

def update_faction_power():
    for f in FACTIONS:
        agents_=faction_agents(f)
        buildings_=[b for b in world["buildings"] if b.get("faction")==f]
        world["faction_power"][f]=(len(agents_)*2
            +sum(BUILDING_POWER.get(b["type"],1) for b in buildings_)
            +len(world["faction_tech"][f].get("researched",[]))*5)

def generate_terrain():
    t=[]
    for i in range(5): t.append({"type":"river","points":[rand_pos(),rand_pos()],"id":"river_%d"%i})
    for i in range(8): t.append({"type":"mountain","position":rand_pos(),"height":round(random.uniform(2,10),1),"id":"mountain_%d"%i})
    for i in range(12): t.append({"type":"forest","position":rand_pos(),"density":round(random.uniform(0.3,1.0),2),"id":"forest_%d"%i})
    for i in range(4): t.append({"type":"lake","position":rand_pos(),"radius":round(random.uniform(3,8),1),"id":"lake_%d"%i})
    return t

# SPAWN AGENT
def spawn_agent(faction=None, parent_a=None, parent_b=None, pos=None):
    global _agent_counter
    _agent_counter+=1
    if faction is None: faction=random.choice(list(FACTIONS.keys()))
    if pos is None: pos=rand_pos(center=FACTIONS[faction]["home"],radius=10)
    if parent_a and parent_b:
        atype=inherit_type(parent_a,parent_b)
        traits=inherit_traits(parent_a,parent_b)
    else:
        pool=FACTION_PREFERRED_TYPES.get(faction,list(AGENT_TYPES.keys()))
        atype=random.choice(pool)
        traits=random.sample(TRAITS,random.randint(1,3))

    first=["Aran","Lyra","Dorn","Sage","Kira","Bron","Zena","Mael","Tova","Rex",
           "Nyx","Oryn","Sola","Vex","Cira","Holt","Yara","Pix","Galen","Thea",
           "Riven","Cassia","Ember","Fael","Gwynn","Isla","Jace","Petra","Rael","Tessa",
           "Ulric","Vera","Wren","Aldric","Brynn","Corvus","Delia","Elan","Fira","Garon",
           "Helga","Ivar","Juno","Kaela","Lorne","Myra","Nero","Orla","Pike","Quen"]
    last=["Stone","Ash","Dawn","Iron","Wind","Oak","Frost","Ember","Tide","Spark",
          "Vale","Cross","Rune","Shade","Crest","Moor","Blaze","Gale","Thorn","Voss",
          "Crane","Fell","Grey","Hale","Isle","Knell","Lore","Marsh","Nox","Pyre",
          "Quill","Rook","Shard","Tarn","Umber","Veil","Wick","Yew","Zeal","Holm"]
    name=random.choice(first)+" "+random.choice(last)
    _atype_data=AGENT_TYPES.get(atype,AGENT_TYPES["farmer"])
    lifespan=_atype_data["lifespan"]

    agent={
        "id":"a%d_%d"%(_agent_counter,world["tick"]),
        "name":name,"type":atype,"faction":faction,"traits":traits,
        "position":pos,"target":rand_pos(),
        "age":0,"max_age":random.randint(*lifespan),
        "health":100,"faith":0,"alive":True,
        "action":"born","thought":"I am %s of %s. Traits: %s."%(name,faction,", ".join(traits)),
        "color":_atype_data["color"],"size":_atype_data["size"],
        "symbol":_atype_data["symbol"],
        "memories":[],"memory_count":0,"memory_summary":"No memories yet.",
        "is_legend":False,"disease":None,
        "born_year":world["year"],
        "parent_a":parent_a["name"] if parent_a else None,
        "parent_b":parent_b["name"] if parent_b else None,
        "dynasty":None,
        "biome":get_biome(pos),
        "life_stage":"child",
        "emotion":"curious",
        "emotion_color":"#44aacc",
        "goal":None,"goal_type":None,"goal_target":1,"goal_progress":0,"goal_achieved":False,
        "relationships":{},
        "voice":"I am %s, newly born into %s."%(name,faction),
    }
    if world["world_history"]:
        for ev in world["world_history"][-2:]:
            remember(agent,"discovery","Born into: %s"%ev["message"][:55],importance=1)
    for w in world["active_wars"]:
        if faction in (w["attacker"],w["defender"]):
            remember(agent,"battle","Born during war: %s vs %s"%(w["attacker"],w["defender"]),importance=3)
    # ── AGI LAYER INIT ────────────────────────────────────────────
    if _COGNITIVE_LOOP_LOADED:
        try:
            init_bdi(agent)
        except Exception as _agi_e:
            log("AGI: init_bdi failed for %s: %s" % (name, _agi_e), "agi")
    if _LLM_MIND_LOADED:
        try:
            init_llm_mind(agent)
        except Exception as _agi_e:
            log("AGI: init_llm_mind failed for %s: %s" % (name, _agi_e), "agi")
    if _VALUE_ENGINE_LOADED:
        try:
            init_value_system(agent)
        except Exception as _agi_e:
            log("AGI: init_value_system failed for %s: %s" % (name, _agi_e), "agi")
    # ─────────────────────────────────────────────────────────────
    world["agents"].append(agent)
    world["stats"]["total_births"]=world["stats"].get("total_births",0)+1
    log("%s (%s) born into %s%s. Traits: %s"%(name,atype,FACTIONS[faction]["symbol"],faction,",".join(traits)),"birth")
    return agent

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# AGENT SELF-EVOLUTION SYSTEM
# Agents read the engine source code, extract knowledge, write new
# skills, evolve their own stats, and share code with each other.
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

SKILLS_DIR   = "agent_skills"
SKILLS_INDEX = "agent_skills/skills_index.json"

# Built-in skill templates agents can discover and unlock
SKILL_TEMPLATES = {
    "swift_mover":       {"stat":"speed",      "delta":+0.4, "desc":"Studied movement patterns in engine. Moves faster."},
    "iron_will":         {"stat":"max_age",     "delta":+30,  "desc":"Studied lifespan code. Lives longer."},
    "battle_hardened":   {"stat":"health",      "delta":+15,  "desc":"Studied combat code. Starts with more health."},
    "code_reader":       {"stat":"knowledge",   "delta":+5,   "desc":"Can parse engine source. Generates more knowledge."},
    "deep_memory":       {"stat":"memory_cap",  "delta":+10,  "desc":"Studied memory system. Stores more memories."},
    "shadow_step":       {"stat":"speed",       "delta":+0.6, "desc":"Studied spy logic. Moves silently and faster."},
    "healer_touch":      {"stat":"heal_power",  "delta":+10,  "desc":"Studied healing code. Heals more effectively."},
    "trade_instinct":    {"stat":"gold_sense",  "delta":+3,   "desc":"Studied merchant code. Earns more gold per trade."},
    "stone_skin":        {"stat":"defense",     "delta":+10,  "desc":"Studied defense routines. Takes less damage."},
    "keen_eye":          {"stat":"detect_range","delta":+3,   "desc":"Studied proximity checks. Notices things from further."},
    "ancient_knowledge": {"stat":"max_age",     "delta":+50,  "desc":"Read the deep history code. Wisdom adds years."},
    "war_tactician":     {"stat":"battle_power","delta":+12,  "desc":"Studied war_battle logic. Fights with greater skill."},
    "fertile_ground":    {"stat":"food_yield",  "delta":+2,   "desc":"Studied farming code. Grows more food."},
    "divine_insight":    {"stat":"faith_gain",  "delta":+2,   "desc":"Studied religion system. Generates more faith."},
    "ghost_protocol":    {"stat":"speed",       "delta":+0.8, "desc":"Studied assassin logic. Near-invisible movement."},
    "builder_mastery":   {"stat":"build_rate",  "delta":+0.2, "desc":"Studied building code. Constructs with greater skill."},
}

# Code sections agents can read (mapped to skills they can unlock)
CODE_SECTIONS = {
    "def move_toward":     ["swift_mover","shadow_step","ghost_protocol"],
    "def war_battle":      ["battle_hardened","war_tactician","stone_skin"],
    "def agent_think":     ["code_reader","keen_eye","deep_memory"],
    "AGENT_TYPES":         ["swift_mover","iron_will","code_reader"],
    "def tick_tech":       ["ancient_knowledge","code_reader","deep_memory"],
    "def priest_action":   ["divine_insight","healer_touch"],
    "def tick_diseases":   ["stone_skin","healer_touch","iron_will"],
    "def remember":        ["deep_memory","ancient_knowledge"],
    "def spawn_agent":     ["iron_will","fertile_ground"],
    "def merchant":        ["trade_instinct","keen_eye"],
    "def builder":         ["builder_mastery","stone_skin"],
    "def assassin":        ["ghost_protocol","shadow_step","battle_hardened"],
    "BUILDING_TYPES":      ["builder_mastery","fertile_ground"],
    "def check_legend":    ["ancient_knowledge","iron_will","war_tactician"],
}

def ensure_skills_dir():
    if not os.path.exists(SKILLS_DIR):
        os.makedirs(SKILLS_DIR)
    if not os.path.exists(SKILLS_INDEX):
        with open(SKILLS_INDEX,"w",encoding="utf-8") as f:
            json.dump({"skills":{},"total_written":0,"total_shared":0},f,indent=2)

def load_skills_index():
    ensure_skills_dir()
    try:
        with open(SKILLS_INDEX,"r",encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {"skills":{},"total_written":0,"total_shared":0}

def save_skills_index(idx):
    ensure_skills_dir()
    with open(SKILLS_INDEX,"w",encoding="utf-8") as f:
        json.dump(idx,f,indent=2,ensure_ascii=False)

def read_engine_source():
    try:
        with open(__file__,"r",encoding="utf-8") as f:
            return f.read()
    except Exception:
        return ""

def agent_reads_code(agent):
    """Agent reads a random section of the engine source and may unlock a skill."""
    src=read_engine_source()
    if not src: return None

    # Pick a random code section to study
    section=random.choice(list(CODE_SECTIONS.keys()))
    if section not in src: return None

    # Find the actual line in source for realism
    lines=[l for l in src.split("\n") if section in l]
    if not lines: return None
    code_line=lines[0].strip()[:80]

    # Pick a skill from that section
    possible=CODE_SECTIONS[section]
    skill_name=random.choice(possible)

    # Check if agent already has this skill
    agent_skills=agent.get("skills",[])
    if skill_name in agent_skills: return None

    return {"section":section,"code_line":code_line,"skill_name":skill_name}

def agent_writes_skill(agent, skill_name):
    """Agent writes a skill file to disk - their own code contribution."""
    ensure_skills_dir()
    if skill_name not in SKILL_TEMPLATES: return False

    skill=SKILL_TEMPLATES[skill_name]
    filename="%s/%s_%s.skill"%(SKILLS_DIR,agent["name"].replace(" ","_"),skill_name)

    skill_code={
        "skill_name":    skill_name,
        "written_by":    agent["name"],
        "faction":       agent.get("faction","?"),
        "agent_type":    agent["type"],
        "stat":          skill["stat"],
        "delta":         skill["delta"],
        "desc":          skill["desc"],
        "written_tick":  world["tick"],
        "written_year":  world["year"],
        "transferable":  True,
        "times_learned": 1,
    }

    with open(filename,"w",encoding="utf-8") as f:
        json.dump(skill_code,f,indent=2)

    # Update index
    idx=load_skills_index()
    idx["skills"][skill_name]={
        "file":filename,
        "author":agent["name"],
        "faction":agent.get("faction","?"),
        "stat":skill["stat"],
        "delta":skill["delta"],
        "desc":skill["desc"],
        "written_year":world["year"],
        "times_learned":idx["skills"].get(skill_name,{}).get("times_learned",0)+1,
    }
    idx["total_written"]=idx.get("total_written",0)+1
    save_skills_index(idx)
    return True

def agent_applies_skill(agent, skill_name):
    """Apply a skill's stat bonus to the agent."""
    if skill_name not in SKILL_TEMPLATES: return
    skill=SKILL_TEMPLATES[skill_name]
    stat=skill["stat"]; delta=skill["delta"]

    if stat=="speed":
        atype=agent["type"]
        if atype in AGENT_TYPES:
            AGENT_TYPES[atype]["speed"]=round(AGENT_TYPES[atype]["speed"]+delta,2)
    elif stat=="max_age":
        agent["max_age"]=agent.get("max_age",300)+int(delta)
    elif stat=="health":
        agent["health"]=min(150,agent.get("health",100)+int(delta))
    elif stat=="memory_cap":
        # Agent's personal memory cap increases
        agent["personal_memory_cap"]=agent.get("personal_memory_cap",MAX_MEMORY)+int(delta)
    elif stat=="heal_power":
        agent["heal_power"]=agent.get("heal_power",15)+int(delta)
    elif stat=="gold_sense":
        agent["gold_sense"]=agent.get("gold_sense",0)+int(delta)
    elif stat=="defense":
        agent["defense"]=agent.get("defense",0)+int(delta)
    elif stat=="detect_range":
        agent["detect_range"]=agent.get("detect_range",5)+int(delta)
    elif stat=="battle_power":
        agent["battle_power"]=agent.get("battle_power",0)+int(delta)
    elif stat=="food_yield":
        agent["food_yield"]=agent.get("food_yield",0)+int(delta)
    elif stat=="faith_gain":
        agent["faith_gain"]=agent.get("faith_gain",1)+int(delta)
    elif stat=="build_rate":
        agent["build_rate"]=agent.get("build_rate",0.30)+delta

def agent_shares_skill(agent_a, agent_b):
    """Agent A teaches a skill to Agent B from a skill file on disk."""
    ensure_skills_dir()
    a_skills=agent_a.get("skills",[])
    b_skills=agent_b.get("skills",[])
    teachable=[s for s in a_skills if s not in b_skills]
    if not teachable: return False

    skill_name=random.choice(teachable)
    if skill_name not in SKILL_TEMPLATES: return False

    # B learns the skill
    if "skills" not in agent_b: agent_b["skills"]=[]
    agent_b["skills"].append(skill_name)
    agent_applies_skill(agent_b, skill_name)

    # Update the skill file's times_learned count
    idx=load_skills_index()
    if skill_name in idx["skills"]:
        idx["skills"][skill_name]["times_learned"]=idx["skills"][skill_name].get("times_learned",1)+1
    idx["total_shared"]=idx.get("total_shared",0)+1
    save_skills_index(idx)

    skill=SKILL_TEMPLATES[skill_name]
    remember(agent_a,"discovery","Taught skill '%s' to %s Y%d"%(skill_name,agent_b["name"],world["year"]),importance=3)
    remember(agent_b,"discovery","Learned skill '%s' from %s Y%d"%(skill_name,agent_a["name"],world["year"]),importance=4)
    # AGI: value inheritance when skills are shared
    if _VALUE_ENGINE_LOADED:
        try: inherit_values(agent_a, agent_b, world, strength=0.25)
        except Exception: pass

    log("   %s taught '%s' to %s! (%s)"%(agent_a["name"],skill_name,agent_b["name"],skill["desc"][:50]),"evolution")
    world["stats"]["skills_shared"]=world["stats"].get("skills_shared",0)+1
    return True

def tick_evolution():
    """Main evolution tick — scholars and explorers read code, write skills, share them."""
    for agent in living():
        atype=agent["type"]
        if "skills" not in agent: agent["skills"]=[]

        # SCHOLARS and EXPLORERS are primary code readers
        if atype in ("scholar","explorer") and random.random()<0.08:
            result=agent_reads_code(agent)
            if result:
                skill_name=result["skill_name"]
                section=result["section"]
                code_line=result["code_line"]

                if skill_name not in agent["skills"]:
                    agent["skills"].append(skill_name)
                    agent_applies_skill(agent,skill_name)
                    wrote=agent_writes_skill(agent,skill_name)

                    desc=SKILL_TEMPLATES[skill_name]["desc"]
                    thought_msg="I studied '%s' and unlocked '%s'!"%(section,skill_name)
                    agent["thought"]=thought_msg

                    remember(agent,"discovery",
                        "Read engine code '%s', unlocked skill '%s' Y%d"%(section[:30],skill_name,world["year"]),
                        importance=4)
                    history("%s (%s) evolved: unlocked '%s' from code"%(agent["name"],atype,skill_name),importance=3)
                    log("EVOLVED: %s read '%s' -> unlocked '%s'"%(agent["name"],section[:35],skill_name),"evolution")
                    sound("evolution")

                    world["stats"]["skills_unlocked"]=world["stats"].get("skills_unlocked",0)+1

        # ANY agent can learn skills from nearby evolved agents
        if agent.get("skills") and random.random()<0.04:
            nearby=[a for a in living()
                    if a["id"]!=agent["id"]
                    and dist(agent["position"],a["position"])<6
                    and a.get("skills")]
            if nearby:
                teacher=random.choice(nearby)
                if agent_shares_skill(teacher,agent):
                    world["stats"]["skills_shared"]=world["stats"].get("skills_shared",0)+1

        # WARRIORS study battle code more often
        if atype=="warrior" and random.random()<0.04:
            for skill_name in ["battle_hardened","war_tactician","stone_skin"]:
                if skill_name not in agent.get("skills",[]):
                    agent["skills"]=agent.get("skills",[])+[skill_name]
                    agent_applies_skill(agent,skill_name)
                    agent_writes_skill(agent,skill_name)
                    log("EVOLVED: %s (warrior) studied combat code -> '%s'"%(agent["name"],skill_name),"evolution")
                    sound("evolution")
                    world["stats"]["skills_unlocked"]=world["stats"].get("skills_unlocked",0)+1
                    break

        # HEALERS study healing/disease code
        if atype=="healer" and random.random()<0.04:
            for skill_name in ["healer_touch","stone_skin","iron_will"]:
                if skill_name not in agent.get("skills",[]):
                    agent["skills"]=agent.get("skills",[])+[skill_name]
                    agent_applies_skill(agent,skill_name)
                    agent_writes_skill(agent,skill_name)
                    log("EVOLVED: %s (healer) studied healing code -> '%s'"%(agent["name"],skill_name),"evolution")
                    sound("evolution")
                    world["stats"]["skills_unlocked"]=world["stats"].get("skills_unlocked",0)+1
                    break

        # MERCHANTS study trade code
        if atype=="merchant" and random.random()<0.04:
            for skill_name in ["trade_instinct","keen_eye"]:
                if skill_name not in agent.get("skills",[]):
                    agent["skills"]=agent.get("skills",[])+[skill_name]
                    agent_applies_skill(agent,skill_name)
                    agent_writes_skill(agent,skill_name)
                    log("EVOLVED: %s (merchant) studied trade code -> '%s'"%(agent["name"],skill_name),"evolution")
                    sound("evolution")
                    world["stats"]["skills_unlocked"]=world["stats"].get("skills_unlocked",0)+1
                    break

        # SPIES/ASSASSINS study stealth code
        if atype in ("spy","assassin") and random.random()<0.04:
            for skill_name in ["ghost_protocol","shadow_step","keen_eye"]:
                if skill_name not in agent.get("skills",[]):
                    agent["skills"]=agent.get("skills",[])+[skill_name]
                    agent_applies_skill(agent,skill_name)
                    agent_writes_skill(agent,skill_name)
                    log("EVOLVED: %s (%s) studied stealth code -> '%s'"%(agent["name"],atype,skill_name),"evolution")
                    sound("evolution")
                    world["stats"]["skills_unlocked"]=world["stats"].get("skills_unlocked",0)+1
                    break

# SAVE & LOAD
def save_state():
    # Write sound events separately for dashboard
    with open(SOUND_FILE,"w",encoding="utf-8") as f:
        json.dump({"queue":world["sound_queue"],"tick":world["tick"]},f)

    state={**world,
           "skills_index":load_skills_index(),
           "last_updated":datetime.now().isoformat(),
           "alive_agents":[a for a in world["agents"] if a["alive"]],
           "recent_legends":world["legends"][-5:],
           "top_legends":sorted(world["legends"],key=lambda x:x.get("score",0),reverse=True)[:20],
           "immortals":world.get("immortals",[]),
           "faction_legend_counts":{f:len([l for l in world["legends"] if l.get("faction")==f]) for f in FACTIONS},
           "recent_history":world["world_history"][-15:],
           "recent_conversations":world["conversations"][-10:],
           "recent_graveyard":world["graveyard"][-10:],
           "tension":world.get("tension",{}),
           "ticks_since_war":world["tick"]-world.get("last_war_tick",0),
           "weather_icon":next((w[2] for w in WEATHER_TYPES if w[0]==world["weather"]),"Sun"),
           "faction_summary":{
               f:{
                   "population":len(faction_agents(f)),
                   "color":FACTIONS[f]["color"],"symbol":FACTIONS[f]["symbol"],
                   "trait":FACTIONS[f]["trait"],"power":world["faction_power"].get(f,0),
                   "tech":world["faction_tech"][f].get("researched",[]),
                   "at_war":[o for o in FACTIONS if get_diplo(f,o)=="war"],
                   "allied":[o for o in FACTIONS if get_diplo(f,o)=="allied"],
               } for f in FACTIONS
           }}
    with open(WORLD_STATE_FILE,"w",encoding="utf-8") as f:
        json.dump(state,f,indent=2,ensure_ascii=False)

def save_persistent():
    with open(WORLD_SAVE_FILE,"w",encoding="utf-8") as f:
        # Sanitize non-serializable types before saving
        def sanitize(obj):
            if isinstance(obj, set): return list(obj)
            if isinstance(obj, dict): return {k: sanitize(v) for k,v in obj.items()}
            if isinstance(obj, list): return [sanitize(i) for i in obj]
            return obj
        json.dump(sanitize(world),f,indent=2,ensure_ascii=False)
    print("Saved - Tick %d, Year %d"%(world["tick"],world["year"]))

def load_persistent():
    if not os.path.exists(WORLD_SAVE_FILE): return False
    try:
        with open(WORLD_SAVE_FILE,"r",encoding="utf-8") as f: saved=json.load(f)
        world.update(saved)
        for f in FACTIONS:
            if f not in world["faction_tech"]:
                world["faction_tech"][f]={"researched":[],"points":0}
        # Ensure new fields exist
        for field in ["graveyard","lineage","conversations","war_timeline","sound_queue","biome_map","winner","immortals"]:
            if field not in world: world[field]=[] if field not in ("lineage","winner") else ({} if field=="lineage" else None)
        if "tension" not in world: world["tension"]={}
        if "last_war_tick" not in world: world["last_war_tick"]=0
        # Init cognitive fields for existing agents
        for a in world.get("agents",[]):
            if "self_model" not in a: init_self_model(a)
            if "beliefs" not in a: init_beliefs(a)
            if "originated_goals" not in a: a["originated_goals"]=[]
        for field in ["graveyard","lineage","conversations","war_timeline","sound_queue","biome_map","winner","immortals","tension"]:
            if field not in world: world[field]=[] if field not in ("lineage","winner") else ({} if field=="lineage" else None)
        alive=len([a for a in world["agents"] if a["alive"]])
        print("World resumed - Tick %d, Year %d"%(world["tick"],world["year"]))
        print("  %d alive | %d buildings | %d legends | %d in graveyard"%(alive,len(world["buildings"]),len(world["legends"]),len(world["graveyard"])))
        print("  %d total ticks ever"%world["stats"].get("total_ticks_ever",0))
        return True
    except Exception as e:
        print("Could not load save (%s) - fresh start"%str(e)); return False

# MAIN LOOP

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# RESEARCH LOGGING SYSTEM
# Produces structured CSV + JSON data for academic analysis.
# Files written to research_data/ folder alongside the engine.
# Author: Himanshu Mourya
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

import csv, os

RESEARCH_DIR      = "research_data"
LOG_EVERY_TICKS   = 10   # snapshot every 10 ticks
RUN_ID            = None  # set at initialization

def init_research_logging():
    """Create research_data folder and initialize CSV files for this run."""
    global RUN_ID
    os.makedirs(RESEARCH_DIR, exist_ok=True)
    RUN_ID = datetime.now().strftime("run_%Y%m%d_%H%M%S")
    run_dir = os.path.join(RESEARCH_DIR, RUN_ID)
    os.makedirs(run_dir, exist_ok=True)

    # ── 1. WORLD SNAPSHOTS — one row every LOG_EVERY_TICKS ticks ──
    with open(os.path.join(run_dir,"world_snapshots.csv"),"w",newline="",encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow([
            "tick","year","season","weather","population",
            "food","gold","knowledge","faith",
            "active_wars","total_wars","alliances",
            "legends","immortals","buildings","cities",
            "beliefs_shattered","goals_originated","abstractions_made",
            "goals_achieved","heretics","holy_wars",
            "dominant_faction","dominant_faction_pop",
            "avg_agent_age","avg_agent_health","avg_agent_faith",
            "avg_self_worth","avg_world_understanding",
            "faith_ratio","tech_count",
        ])

    # ── 2. AGENT SNAPSHOTS — every agent every 50 ticks ──
    with open(os.path.join(run_dir,"agent_snapshots.csv"),"w",newline="",encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow([
            "tick","year","agent_id","name","type","faction","age","health",
            "faith","emotion","life_stage","is_legend","is_immortal","is_heretic",
            "battles","discoveries","builds","friends","skills_count",
            "self_worth","world_understanding","identity_stability",
            "role_confidence","perceived_strength","perceived_wisdom",
            "beliefs_shattered_count","originated_goals_count",
            "active_goals_count","goal_achieved","abstractions_count",
            "belief_faith_conf","belief_strength_conf","belief_cooperation_conf",
            "belief_divine_conf","belief_world_safe_conf",
        ])

    # ── 3. EVENTS LOG — every major event ──
    with open(os.path.join(run_dir,"events_log.csv"),"w",newline="",encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow([
            "tick","year","season","category","message","importance"
        ])

    # ── 4. BELIEF COLLAPSE LOG — every time a belief shatters ──
    with open(os.path.join(run_dir,"belief_collapses.csv"),"w",newline="",encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow([
            "tick","year","agent_name","agent_type","faction",
            "belief","new_label","agent_age","prior_traumas",
            "prior_battles","prior_faith"
        ])

    # ── 5. GOAL ORIGINS LOG — every originated goal ──
    with open(os.path.join(run_dir,"goal_origins.csv"),"w",newline="",encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow([
            "tick","year","agent_name","agent_type","faction",
            "goal","goal_type","origin","agent_age","emotion_at_birth"
        ])

    # ── 6. ABSTRACTION TRANSFERS LOG ──
    with open(os.path.join(run_dir,"abstraction_transfers.csv"),"w",newline="",encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow([
            "tick","year","agent_name","agent_type","faction",
            "source_domain","principle","target_domain","success","agent_age","skills_count"
        ])

    # ── 7. WAR LOG ──
    with open(os.path.join(run_dir,"wars_log.csv"),"w",newline="",encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow([
            "tick","year","attacker","defender","cause","type",
            "tension_at_declaration","ticks_since_last_war"
        ])

    # ── 8. LEGEND LOG ──
    with open(os.path.join(run_dir,"legends_log.csv"),"w",newline="",encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow([
            "tick","year","name","type","faction","tier",
            "score","age","battles","discoveries","builds","skills","faith",
            "reason","had_identity_crisis","beliefs_shattered","goals_originated"
        ])

    # ── 9. RUN METADATA ──
    meta = {
        "run_id": RUN_ID,
        "start_time": datetime.now().isoformat(),
        "author": "Himanshu Mourya",
        "engine_version": "5.0",
        "config": {
            "world_size": WORLD_SIZE,
            "max_agents": MAX_AGENTS,
            "tick_rate": TICK_RATE,
            "max_memory": MAX_MEMORY,
            "factions": list(FACTIONS.keys()),
            "agent_types": list(AGENT_TYPES.keys()),
            "log_every_ticks": LOG_EVERY_TICKS,
        },
        "systems": [
            "self_model","belief_revision","goal_origination",
            "abstraction_transfer","religious_tension","self_evolution",
            "diplomacy_tension","emotions","life_goals","dynasties",
        ]
    }
    with open(os.path.join(run_dir,"run_metadata.json"),"w",encoding="utf-8") as f:
        json.dump(meta,f,indent=2)

    print("[RESEARCH] Logging initialized → %s" % run_dir)
    return run_dir


def get_run_dir():
    if RUN_ID is None: return None
    return os.path.join(RESEARCH_DIR, RUN_ID)

def research_append(filename, row):
    """Append a row to a research CSV file safely."""
    d = get_run_dir()
    if not d: return
    try:
        with open(os.path.join(d,filename),"a",newline="",encoding="utf-8") as f:
            csv.writer(f).writerow(row)
    except Exception as e:
        pass  # never crash the engine for logging

def log_world_snapshot():
    """Snapshot the entire world state into world_snapshots.csv."""
    alive = living()
    if not alive: return

    # Faction populations
    pops = {f:len(faction_agents(f)) for f in FACTIONS}
    dominant = max(pops, key=pops.get)

    # Averages across living agents
    avg_age    = sum(a["age"] for a in alive) / len(alive)
    avg_health = sum(a.get("health",100) for a in alive) / len(alive)
    avg_faith  = sum(a.get("faith",0) for a in alive) / len(alive)
    avg_sw     = sum(a.get("self_model",{}).get("self_worth",50) for a in alive) / len(alive)
    avg_wu     = sum(a.get("self_model",{}).get("world_understanding",20) for a in alive) / len(alive)
    faith_ratio= sum(1 for a in alive if a.get("faith",0)>5) / len(alive)
    heretics   = sum(1 for a in alive if a.get("is_heretic"))

    # Tech count across all factions
    tech_count = sum(len(world["faction_tech"][f].get("researched",[])) for f in FACTIONS)

    stats = world["stats"]
    research_append("world_snapshots.csv", [
        world["tick"], world["year"], world["season"], world["weather"],
        len(alive),
        round(world["resources"].get("food",0),1),
        round(world["resources"].get("gold",0),1),
        round(world["resources"].get("knowledge",0),1),
        round(world["resources"].get("faith",0),1),
        len(world.get("active_wars",[])),
        stats.get("wars_fought",0),
        stats.get("alliances_formed",0),
        len(world.get("legends",[])),
        len(world.get("immortals",[])),
        len(world.get("buildings",[])),
        len(world.get("cities",[])),
        stats.get("beliefs_shattered",0),
        stats.get("goals_originated",0),
        stats.get("abstractions_made",0),
        stats.get("goals_achieved",0),
        heretics,
        stats.get("holy_wars",0),
        dominant,
        pops[dominant],
        round(avg_age,1),
        round(avg_health,1),
        round(avg_faith,2),
        round(avg_sw,1),
        round(avg_wu,1),
        round(faith_ratio,3),
        tech_count,
    ])

def log_agent_snapshots():
    """Log every living agent to agent_snapshots.csv every 50 ticks."""
    for a in living():
        sm = a.get("self_model",{})
        b  = a.get("beliefs",{})
        battles   = len(recall(a,"battle"))
        discos    = len(recall(a,"discovery"))
        builds    = len(recall(a,"built"))
        friends   = len(recall(a,"friend"))
        traumas   = len(recall(a,"trauma"))
        orig_goals= a.get("originated_goals",[])
        active_g  = sum(1 for g in orig_goals if g.get("active"))
        # count belief collapses in this agent
        b_shattered = sum(1 for bk,bv in b.items() if bv.get("value")==False)
        # count abstraction memories
        abst_count = sum(1 for m in a["memories"] if "ABSTRACTION" in m.get("content",""))

        research_append("agent_snapshots.csv", [
            world["tick"], world["year"],
            a.get("id","?"), a["name"], a["type"], a.get("faction","?"),
            a["age"], round(a.get("health",100),1),
            round(a.get("faith",0),2), a.get("emotion","content"),
            a.get("life_stage","adult"),
            1 if a.get("is_legend") else 0,
            1 if a.get("is_immortal") else 0,
            1 if a.get("is_heretic") else 0,
            battles, discos, builds, friends,
            len(a.get("skills",[])),
            sm.get("self_worth",50),
            sm.get("world_understanding",20),
            sm.get("identity_stability",80),
            sm.get("role_confidence",70),
            sm.get("perceived_strength",60),
            sm.get("perceived_wisdom",50),
            b_shattered,
            len(orig_goals),
            active_g,
            1 if a.get("goal_achieved") else 0,
            abst_count,
            b.get("faith_protects",{}).get("confidence",50),
            b.get("strength_wins",{}).get("confidence",50),
            b.get("cooperation_works",{}).get("confidence",50),
            b.get("the_divine_exists",{}).get("confidence",50),
            b.get("world_is_safe",{}).get("confidence",50),
        ])

def log_event_research(category, message, importance=1):
    """Log an event to events_log.csv."""
    research_append("events_log.csv",[
        world["tick"], world["year"], world["season"],
        category, message[:200], importance
    ])

def log_belief_collapse_research(agent, belief_key, new_label):
    """Log a belief collapse event."""
    research_append("belief_collapses.csv",[
        world["tick"], world["year"],
        agent["name"], agent["type"], agent.get("faction","?"),
        belief_key, new_label, agent["age"],
        len(recall(agent,"trauma")),
        len(recall(agent,"battle")),
        round(agent.get("faith",0),1),
    ])

def log_goal_origin_research(agent, goal, goal_type, origin):
    """Log a goal origination event."""
    research_append("goal_origins.csv",[
        world["tick"], world["year"],
        agent["name"], agent["type"], agent.get("faction","?"),
        goal, goal_type, origin[:100],
        agent["age"], agent.get("emotion","content"),
    ])

def log_abstraction_research(agent, source_domain, principle, target_domain, success):
    """Log an abstraction transfer."""
    research_append("abstraction_transfers.csv",[
        world["tick"], world["year"],
        agent["name"], agent["type"], agent.get("faction","?"),
        source_domain, principle[:60], target_domain,
        1 if success else 0,
        agent["age"], len(agent.get("skills",[])),
    ])

def log_war_research(fa, fb, cause, war_type, tension):
    """Log a war declaration."""
    research_append("wars_log.csv",[
        world["tick"], world["year"],
        fa, fb, cause[:80], war_type,
        round(tension,1),
        world["tick"] - world.get("last_war_tick",0),
    ])

def log_legend_research(agent):
    """Log a legend or immortal achievement."""
    sm = agent.get("self_model",{})
    b  = agent.get("beliefs",{})
    had_crisis = sm.get("identity_stability",100) < 40
    b_shattered = sum(1 for bk,bv in b.items() if bv.get("value")==False)
    research_append("legends_log.csv",[
        world["tick"], world["year"],
        agent["name"], agent["type"], agent.get("faction","?"),
        "immortal" if agent.get("is_immortal") else "legend",
        agent.get("legend_score",0), agent["age"],
        len(recall(agent,"battle")),
        len(recall(agent,"discovery")),
        len(recall(agent,"built")),
        len(agent.get("skills",[])),
        round(agent.get("faith",0),1),
        agent.get("legend_reason",""),
        1 if had_crisis else 0,
        b_shattered,
        len(agent.get("originated_goals",[])),
    ])

def finalize_research():
    """Write run summary when world ends or is interrupted."""
    d = get_run_dir()
    if not d: return
    alive = living()
    summary = {
        "run_id": RUN_ID,
        "end_time": datetime.now().isoformat(),
        "final_tick": world["tick"],
        "final_year": world["year"],
        "final_population": len(alive),
        "total_wars": world["stats"].get("wars_fought",0),
        "total_legends": len(world.get("legends",[])),
        "total_immortals": len(world.get("immortals",[])),
        "total_beliefs_shattered": world["stats"].get("beliefs_shattered",0),
        "total_goals_originated": world["stats"].get("goals_originated",0),
        "total_abstractions": world["stats"].get("abstractions_made",0),
        "total_holy_wars": world["stats"].get("holy_wars",0),
        "total_heretics": world["stats"].get("heretics_spawned",0),
        "winner": world.get("winner"),
        "victory_type": world.get("victory_type"),
        "dominant_faction": max(
            {f:len(faction_agents(f)) for f in FACTIONS},
            key=lambda f: len(faction_agents(f))
        ) if alive else "none",
        "graveyard_size": len(world.get("graveyard",[])),
        "skills_unlocked": world["stats"].get("skills_unlocked",0),
    }
    with open(os.path.join(d,"run_summary.json"),"w",encoding="utf-8") as f:
        json.dump(summary,f,indent=2)
    print("[RESEARCH] Run summary saved → %s/run_summary.json" % d)
    print("[RESEARCH] Data files:")
    for fname in os.listdir(d):
        fpath = os.path.join(d,fname)
        size  = os.path.getsize(fpath)
        print("  %-35s %6d bytes" % (fname, size))


def enforce_resource_caps():
    """Hard caps on resources to prevent exponential overflow."""
    r = world["resources"]
    # Faith cap — decays rapidly above threshold
    faith = r.get("faith", 0)
    if faith > FAITH_CAP:
        decay = (faith - FAITH_CAP) * 0.15  # drain 15% of excess per tick
        r["faith"] = max(FAITH_CAP, faith - decay)
        if random.random() < 0.01:
            log("FAITH OVERFLOW: World faith at %.0f — divine excess drains away" % faith, "world")
    # Knowledge cap
    know = r.get("knowledge", 0)
    if know > KNOWLEDGE_CAP:
        r["knowledge"] = KNOWLEDGE_CAP
    # Agent faith cap
    for a in living():
        if a.get("faith", 0) > AGENT_FAITH_CAP:
            a["faith"] = AGENT_FAITH_CAP

# ╔══════════════════════════════════════════════════════════════════════╗
# ║  v8.0 UPGRADE MODULE — inline injection                            ║
# ╚══════════════════════════════════════════════════════════════════════╝
# fmt: off  (preserves indentation in embedded block)

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# UPGRADE 1 — AGENT-TO-AGENT INFLUENCE MODELING
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
INFLUENCE_BELIEFS = [
    "world_is_safe","faith_protects","strength_wins","knowledge_is_power",
    "cooperation_works","the_divine_exists","i_can_change_things",
]

def compute_influence_power(agent):
    sm=agent.get("self_model",{}); social=sm.get("social_standing",30)
    is_legend=20 if agent.get("is_legend") else 0
    is_immortal=15 if agent.get("is_immortal") else 0
    charisma=sum(5 for t in agent.get("traits",[]) if t in ("charismatic","brave","wise","spiritual"))
    faith_bonus=min(20,agent.get("faith",0)//3)
    age_bonus=min(15,agent["age"]//40)
    return min(100,social*0.4+is_legend+is_immortal+charisma+faith_bonus+age_bonus)

def tick_influence_propagation():
    alive=living()
    for agent in alive:
        influence_power=compute_influence_power(agent)
        if influence_power<25: continue
        radius=5+influence_power*0.15
        nearby=[a for a in alive if a["id"]!=agent["id"] and dist(agent["position"],a["position"])<radius]
        if not nearby: continue
        a_beliefs=agent.get("beliefs",{}); shift=influence_power*0.003
        for other in nearby[:4]:
            o_beliefs=other.get("beliefs",{})
            if not o_beliefs: continue
            strong=[(k,v) for k,v in a_beliefs.items() if v.get("value",True) and v.get("confidence",50)>65 and k in INFLUENCE_BELIEFS]
            if not strong: continue
            bk,bd=random.choice(strong); inf_conf=bd.get("confidence",50)
            if bk in o_beliefs:
                cur=o_beliefs[bk]["confidence"]; delta=(inf_conf-cur)*shift
                o_beliefs[bk]["confidence"]=int(max(0,min(100,cur+delta)))
                if abs(delta)>2 and random.random()<0.03:
                    remember(other,"discovery","Being near %s shifts how I see '%s'. Y%d"%(agent["name"],bk.replace("_"," "),world["year"]),importance=2)
        if influence_power>60 and random.random()<0.005:
            log("INFLUENCE: %s (power %.0f) reshaping nearby beliefs"%(agent["name"],influence_power),"cognition")
            world["stats"]["influence_events"]=world["stats"].get("influence_events",0)+1

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# UPGRADE 2 — COUNTERFACTUAL REASONING
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
COUNTERFACTUAL_TEMPLATES={
    "battle":["If I had retreated sooner, I would not have taken that wound.","If I had waited for allies, the outcome would differ.","If I had studied their movements first, I could have predicted the ambush.","If I had used my {strategy} approach there, it might have worked."],
    "trauma":["If I had left earlier, I would have avoided that disaster.","If I had sought help from {faction} allies instead of going alone.","If I had not been so trusting, this would not have happened.","If I had built stronger walls before the war reached me."],
    "loss":["If I had healed {name} sooner, they might still be alive.","If I had warned {name} about the danger, they could have fled.","If I had stayed closer, I could have protected them.","If I had not let {name} go into that territory alone."],
    "disease":["If I had found a healer sooner, this illness might not have taken hold.","If I had avoided the crowded settlements, I would not have contracted this.","If I had stronger health, I could fight it off."],
}

def generate_counterfactual(agent,memory):
    mtype=memory.get("type","trauma")
    templates=COUNTERFACTUAL_TEMPLATES.get(mtype,COUNTERFACTUAL_TEMPLATES["trauma"])
    tmpl=random.choice(templates)
    recent_loss=recall(agent,"loss"); lost_name="them"
    if recent_loss:
        content=recent_loss[-1].get("content",""); words=content.split()
        for i,w in enumerate(words):
            if w in ("friend","My") and i+1<len(words): lost_name=words[i+1]; break
    return tmpl.replace("{name}",lost_name).replace("{faction}",agent.get("faction","my people")).replace("{strategy}",agent.get("strategy","cautious"))

def tick_counterfactual_reasoning():
    for agent in living():
        if random.random()>0.06: continue
        recent_bad=[m for m in agent["memories"][-6:] if m["type"] in ("trauma","battle","loss","disease") and m["tick"]>world["tick"]-30]
        if not recent_bad: continue
        trigger=recent_bad[-1]
        already=[m for m in agent["memories"] if "If I had" in m.get("content","") and abs(m["tick"]-trigger["tick"])<5]
        if already: continue
        cf=generate_counterfactual(agent,trigger)
        remember(agent,"discovery","COUNTERFACTUAL: %s Y%d"%(cf,world["year"]),importance=3)
        if "retreat" in cf or "avoid" in cf: agent["counterfactual_bias"]="defensive"
        elif "allies" in cf or "alliance" in cf: agent["counterfactual_bias"]="diplomatic"
        elif "healer" in cf or "health" in cf: agent["counterfactual_bias"]="cautious"
        elif "studied" in cf or "learned" in cf: agent["counterfactual_bias"]="scholarly"
        world["stats"]["counterfactuals_generated"]=world["stats"].get("counterfactuals_generated",0)+1
        if random.random()<0.05: log("COUNTERFACTUAL: %s — '%s'"%(agent["name"],cf[:60]),"cognition")

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# UPGRADE 3 — THEORY OF MIND (SHALLOW)
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
def init_theory_of_mind(agent):
    if "suspected_beliefs" not in agent: agent["suspected_beliefs"]={}

def update_theory_of_mind(agent):
    if agent["type"] not in ("spy","scholar","priest","merchant","assassin"): return
    if random.random()>0.08: return
    init_theory_of_mind(agent)
    nearby=[a for a in living() if a["id"]!=agent["id"] and dist(agent["position"],a["position"])<10]
    if not nearby: return
    target=random.choice(nearby); tid=target["id"]
    if tid not in agent["suspected_beliefs"]:
        agent["suspected_beliefs"][tid]={"name":target["name"],"type":target["type"],"faction":target.get("faction","?"),"suspected":{},"observations":0,"last_updated":world["tick"]}
    model=agent["suspected_beliefs"][tid]; model["observations"]+=1; model["last_updated"]=world["tick"]
    s=model["suspected"]; ta=target.get("action",""); te=target.get("emotion","content")
    if target.get("faith",0)>30 or ta in ("preaching","healing"): s["faith_protects"]=min(100,s.get("faith_protects",40)+8)
    elif target.get("is_heretic"): s["faith_protects"]=max(0,s.get("faith_protects",40)-15)
    if len(recall(target,"battle"))>5 or ta in ("hunting","stalking","patrolling"): s["strength_wins"]=min(100,s.get("strength_wins",50)+6)
    elif te in ("grieving","afraid","weary"): s["strength_wins"]=max(0,s.get("strength_wins",50)-5)
    if target.get("institution") or len(recall(target,"friend"))>5: s["cooperation_works"]=min(100,s.get("cooperation_works",50)+7)
    elif len(recall(target,"betrayal"))>1: s["cooperation_works"]=max(0,s.get("cooperation_works",50)-10)
    if target["type"] in ("scholar","explorer") or len(target.get("skills",[]))>3: s["knowledge_is_power"]=min(100,s.get("knowledge_is_power",50)+5)
    if agent["type"]=="spy" and model["observations"]>=3:
        weak=[(k,v) for k,v in s.items() if v<35]
        if weak:
            tw=random.choice(weak)[0]
            remember(agent,"discovery","I know %s's weakness: low confidence in '%s'. Leverage possible. Y%d"%(target["name"],tw.replace("_"," "),world["year"]),importance=4)
            world["stats"]["tom_exploits"]=world["stats"].get("tom_exploits",0)+1
    if agent["type"]=="priest" and model["observations"]>=2:
        if s.get("the_divine_exists",50)<40: agent["target"]=target["position"]; agent["thought"]="I sense doubt in %s. They need guidance."%target["name"]
    if agent["type"]=="merchant" and model["observations"]>=2:
        if s.get("cooperation_works",50)>65 and dist(agent["position"],target["position"])<8:
            world["resources"]["gold"]=world["resources"].get("gold",0)+random.randint(2,8)
            remember(agent,"discovery","Read %s correctly — cooperative. Good deal. Y%d"%(target["name"],world["year"]),importance=3)
    if model["observations"]==5:
        log("THEORY OF MIND: %s built model of %s: %s"%(agent["name"],target["name"],str({k:v for k,v in list(s.items())[:3]})),"cognition")
        world["stats"]["tom_models_built"]=world["stats"].get("tom_models_built",0)+1

def tick_theory_of_mind():
    for agent in living(): update_theory_of_mind(agent)
    for agent in living():
        if "suspected_beliefs" not in agent: continue
        expired=[tid for tid,m in agent["suspected_beliefs"].items() if world["tick"]-m.get("last_updated",0)>100]
        for tid in expired: del agent["suspected_beliefs"][tid]

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# UPGRADE 4 — COLLECTIVE MEMORY / ORAL TRADITION
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
ORAL_DISTORTIONS=[("was","was said to be"),("died","perished heroically"),("killed","slew"),("built","raised from the earth"),("discovered","revealed to the world"),("betrayed","treacherously betrayed"),("won","triumphed gloriously"),("plague","divine punishment"),("war","great war"),("a ","the legendary ")]

def distort_memory(content):
    if random.random()<0.3: return content
    for orig,rep in ORAL_DISTORTIONS:
        if orig in content and random.random()<0.2: return content.replace(orig,rep,1)
    return content

def tick_oral_tradition():
    if "oral_tradition" not in world: world["oral_tradition"]={}
    for agent in living():
        if random.random()>0.04: continue
        nearby=[a for a in living() if a["id"]!=agent["id"] and dist(agent["position"],a["position"])<5]
        if not nearby: continue
        listener=random.choice(nearby)
        shareable=[h for h in world.get("world_history",[]) if h.get("importance",1)>=2]
        if not shareable: continue
        story=random.choice(shareable[-30:]); msg=story["message"]; key=msg[:40]
        if has_mem(listener,"discovery",key[:20]): continue
        told=distort_memory(msg)
        if key not in world["oral_tradition"]:
            world["oral_tradition"][key]={"original":msg,"retellings":0,"distorted_version":told,"spread_to":[]}
        ot=world["oral_tradition"][key]; ot["retellings"]+=1; ot["spread_to"].append(listener["name"])
        if told!=msg: ot["distorted_version"]=told
        remember(listener,"discovery","Heard from %s: '%s' Y%d"%(agent["name"],told[:60],world["year"]),importance=min(story["importance"],3))
        remember(agent,"person","Told %s the story of: %s Y%d"%(listener["name"],msg[:40],world["year"]),importance=1)
        world["stats"]["oral_retellings"]=world["stats"].get("oral_retellings",0)+1
        if ot["retellings"]>=20 and "myth_formed" not in ot:
            ot["myth_formed"]=True; ot["myth_year"]=world["year"]
            history("A myth has formed: '%s'"%(ot["distorted_version"][:80]),importance=4)
            log("ORAL TRADITION: Myth formed from %d retellings — '%s'"%(ot["retellings"],ot["distorted_version"][:60]),"social")
            world["stats"]["myths_formed"]=world["stats"].get("myths_formed",0)+1; sound("world_event")

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# UPGRADE 5 — FACTION CULTURAL MEMORY
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
FACTION_VALUE_NAMES=["honor","pragmatism","faith","knowledge","aggression","compassion","wealth","secrecy","loyalty","freedom"]

FACTION_CULTURE_DEFAULTS = {
    "Ironveil":   {"honor":60,"aggression":70,"loyalty":60,"pragmatism":50,"faith":20,"knowledge":30,"compassion":20,"wealth":30,"secrecy":30,"freedom":40},
    "Greenveil":  {"faith":70,"compassion":70,"loyalty":65,"honor":50,"knowledge":50,"aggression":20,"pragmatism":40,"wealth":30,"secrecy":20,"freedom":60},
    "Goldveil":   {"wealth":70,"pragmatism":70,"knowledge":60,"freedom":60,"faith":30,"loyalty":40,"honor":40,"aggression":30,"compassion":40,"secrecy":50},
    "Shadowveil": {"secrecy":80,"pragmatism":70,"freedom":60,"knowledge":60,"aggression":50,"honor":20,"faith":20,"loyalty":30,"compassion":20,"wealth":50},
}

def init_faction_culture_values():
    if "faction_culture_values" not in world:
        import copy
        world["faction_culture_values"] = copy.deepcopy(FACTION_CULTURE_DEFAULTS)
        world["faction_cultural_events"] = {f:[] for f in FACTIONS}
    else:
        # Patch any missing keys that may be absent in old save files
        for faction, defaults in FACTION_CULTURE_DEFAULTS.items():
            cv = world["faction_culture_values"].setdefault(faction, {})
            for key, default_val in defaults.items():
                cv.setdefault(key, default_val)
        world.setdefault("faction_cultural_events", {f:[] for f in FACTIONS})

def update_faction_culture():
    if world["tick"]%100!=0: return
    init_faction_culture_values()
    legends=world.get("legends",[])
    for faction in FACTIONS:
        cv=world["faction_culture_values"][faction]
        for leg in [l for l in legends if l.get("faction")==faction][-5:]:
            b=leg.get("battles",0); bld=leg.get("builds",0); d=leg.get("discoveries",0); f=leg.get("faith",0) if isinstance(leg.get("faith"),(int,float)) else 0; fr=leg.get("friends",0)
            if b>8: cv["aggression"]=min(100,cv["aggression"]+2); cv["honor"]=min(100,cv["honor"]+2); cv["compassion"]=max(0,cv["compassion"]-1)
            if bld>8: cv["pragmatism"]=min(100,cv["pragmatism"]+2); cv["loyalty"]=min(100,cv["loyalty"]+1)
            if d>8: cv["knowledge"]=min(100,cv["knowledge"]+2); cv["freedom"]=min(100,cv["freedom"]+1)
            if f>40: cv["faith"]=min(100,cv["faith"]+3); cv["compassion"]=min(100,cv["compassion"]+1)
            if fr>6: cv["compassion"]=min(100,cv["compassion"]+2); cv["loyalty"]=min(100,cv["loyalty"]+1)
        if random.random()<0.1:
            dom=max(cv,key=cv.get)
            history("%s culture: dominant value '%s' (score %d)"%(faction,dom,cv[dom]),importance=2)

def apply_cultural_priors(agent):
    if agent.get("age",0)>10 or agent.get("culture_priors_applied"): return
    init_faction_culture_values()
    cv=world["faction_culture_values"].get(agent.get("faction","?"),{})
    b=agent.get("beliefs",{})
    if not cv or not b: return
    if cv.get("faith",0)>60 and "faith_protects" in b: b["faith_protects"]["confidence"]=min(100,b["faith_protects"]["confidence"]+15)
    if cv.get("aggression",0)>60 and "strength_wins" in b: b["strength_wins"]["confidence"]=min(100,b["strength_wins"]["confidence"]+12)
    if cv.get("knowledge",0)>60 and "knowledge_is_power" in b: b["knowledge_is_power"]["confidence"]=min(100,b["knowledge_is_power"]["confidence"]+12)
    if cv.get("compassion",0)>60 and "cooperation_works" in b: b["cooperation_works"]["confidence"]=min(100,b["cooperation_works"]["confidence"]+10)
    if cv.get("secrecy",0)>65 and "world_is_safe" in b: b["world_is_safe"]["confidence"]=max(0,b["world_is_safe"]["confidence"]-10)
    if cv.get("honor",0)>65 and "my_faction_is_just" in b: b["my_faction_is_just"]["confidence"]=min(100,b["my_faction_is_just"]["confidence"]+10)
    agent["culture_priors_applied"]=True
    agent["cultural_inheritance"]={"dominant_value":max(cv,key=cv.get),"faction":agent.get("faction","?"),"year_inherited":world["year"]}

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# UPGRADE 6 — KNOWLEDGE GRAPH MEMORIES
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
def kg_remember(agent,subject,relation,obj,importance=1):
    if "kg_memories" not in agent: agent["kg_memories"]=[]
    agent["kg_memories"].append({"subject":subject,"relation":relation,"object":obj,"tick":world["tick"],"year":world["year"],"importance":importance})
    if len(agent["kg_memories"])>50:
        agent["kg_memories"].sort(key=lambda x:(x["importance"],x["tick"]),reverse=True)
        agent["kg_memories"]=agent["kg_memories"][:50]

def kg_query(agent,relation=None,subject=None,obj=None):
    r=agent.get("kg_memories",[])
    if relation: r=[t for t in r if t["relation"]==relation]
    if subject:  r=[t for t in r if t["subject"]==subject]
    if obj:      r=[t for t in r if t["object"]==obj]
    return r

def tick_knowledge_graph():
    for agent in living():
        name=agent["name"]
        for mem in agent["memories"][-3:]:
            if mem.get("kg_indexed"): continue
            mem["kg_indexed"]=True; mtype=mem["type"]; content=mem["content"]
            if mtype=="battle":
                if "Defeated" in content or "killed" in content:
                    parts=content.split(); kg_remember(agent,name,"defeated",parts[1] if len(parts)>1 else "enemy",importance=mem["importance"])
                elif "Lost" in content or "Beaten" in content: kg_remember(agent,name,"lost_to","enemy",importance=mem["importance"])
                else: kg_remember(agent,name,"fought_in","battle",importance=mem["importance"])
            elif mtype=="friend":
                if "Befriended" in content:
                    p=content.split("Befriended "); fn=p[1].split(" ")[0] if len(p)>1 else "?"; kg_remember(agent,name,"befriended",fn,importance=mem["importance"])
                elif "Healed" in content:
                    p=content.split("Healed "); hn=p[1].split(" ")[0] if len(p)>1 else "?"; kg_remember(agent,name,"healed",hn,importance=mem["importance"])
            elif mtype=="built":
                if "Built a" in content:
                    p=content.split("Built a "); bt=p[1].split(" ")[0] if len(p)>1 else "?"; kg_remember(agent,name,"built",bt,importance=mem["importance"])
            elif mtype=="discovery":
                if "Discovered" in content:
                    p=content.split("Discovered "); th=(p[1].split(" at")[0][:30] if len(p)>1 else "?"); kg_remember(agent,name,"discovered",th,importance=mem["importance"])
            elif mtype=="betrayal": kg_remember(agent,name,"was_betrayed_by","someone",importance=mem["importance"])
            elif mtype=="loss":
                if "friend" in content.lower():
                    p=content.split("friend "); ln=p[1].split(" ")[0] if len(p)>1 else "?"; kg_remember(agent,name,"lost_friend",ln,importance=mem["importance"])
        sm=agent.get("self_model",{})
        bw=len(kg_query(agent,relation="defeated")); hc=len(kg_query(agent,relation="healed")); bc=len(kg_query(agent,relation="built"))
        if sm and bw>0: sm["perceived_strength"]=min(100,40+bw*5)
        if sm and hc>0 and agent["type"]=="healer": sm["self_worth"]=min(100,sm.get("self_worth",50)+hc*2)
        if sm and bc>0: sm["role_confidence"]=min(100,sm.get("role_confidence",60)+bc)

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# UPGRADE 7 — GEOGRAPHIC INFLUENCE ZONES
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
INFLUENCE_GRID_SIZE=10

def get_influence_cell(pos):
    x=int((pos[0]+40)/INFLUENCE_GRID_SIZE); y=int((pos[1]+40)/INFLUENCE_GRID_SIZE)
    return "%d_%d"%(max(0,min(7,x)),max(0,min(7,y)))

def compute_influence_zones():
    zones={}
    for building in world.get("buildings",[]):
        faction=building.get("faction","?")
        if faction not in FACTIONS: continue
        cell=get_influence_cell(building["position"]); power=BUILDING_POWER.get(building["type"],1)
        if cell not in zones: zones[cell]={f:0 for f in FACTIONS}
        zones[cell][faction]=zones[cell].get(faction,0)+power
        bx,by=map(int,cell.split("_"))
        for dx,dy in [(-1,0),(1,0),(0,-1),(0,1)]:
            nc="%d_%d"%(bx+dx,by+dy)
            if 0<=bx+dx<=7 and 0<=by+dy<=7:
                if nc not in zones: zones[nc]={f:0 for f in FACTIONS}
                zones[nc][faction]=zones[nc].get(faction,0)+power*0.4
    for cell in zones:
        total=sum(zones[cell].values()) or 1
        for f in zones[cell]: zones[cell][f]=round((zones[cell][f]/total)*100,1)
    return zones

def tick_geographic_influence():
    zones=compute_influence_zones(); world["influence_zones"]=zones
    for agent in living():
        cell=get_influence_cell(agent["position"]); faction=agent.get("faction","?"); ci=zones.get(cell,{})
        if not ci: continue
        own=ci.get(faction,0)
        ef=[f for f in FACTIONS if f!=faction and get_diplo(faction,f)=="war"]
        enemy=max((ci.get(f,0) for f in ef),default=0)
        if own>70: agent["health"]=min(150,agent.get("health",100)+0.1)
        if enemy>60 and random.random()<0.02:
            agent["emotion"]="afraid"
            remember(agent,"trauma","Deep in enemy territory. Y%d"%world["year"],importance=2)
        if own>30 and enemy>30:
            for f in ef: add_tension(faction,f,0.3)
    contested=[c for c,inf in zones.items() if len([f for f in FACTIONS if inf.get(f,0)>25])>=2]
    if contested and random.random()<0.005:
        log("ZONES: %d contested cells"%len(contested),"world")
        world["stats"]["contested_zones_peak"]=max(world["stats"].get("contested_zones_peak",0),len(contested))

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# UPGRADE 8 — THE DEAD AFFECTING THE LIVING (SHRINE LETTERS)
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
SHRINE_NAMES=["The Quiet Stone","The Remembrance Slab","The Last Words","The Whispering Marker","The Echo Stone","The Legacy Pillar","The Memorial","The Eternal Mark","The Voice Beyond"]

def init_shrines():
    if "shrines" not in world: world["shrines"]=[]

def derive_shrine_belief_effects(grave):
    effects={}; atype=grave.get("type","warrior"); b=grave.get("battles",0); faith=grave.get("faith",0) if isinstance(grave.get("faith"),(int,float)) else 0; letter=grave.get("final_letter","")
    if atype=="warrior":
        if b>10: effects["strength_wins"]=+8
        if "futility" in letter.lower() or "tired" in letter.lower(): effects["strength_wins"]=-5; effects["cooperation_works"]=+5
    elif atype in ("priest","healer"): effects["faith_protects"]=+10; effects["the_divine_exists"]=+8
    elif atype=="scholar": effects["knowledge_is_power"]=+10; effects["i_can_change_things"]=+6
    elif atype=="merchant": effects["cooperation_works"]=+8; effects["world_is_safe"]=+4
    elif atype=="explorer": effects["i_can_change_things"]=+8; effects["world_is_safe"]=+5
    elif atype=="assassin": effects["world_is_safe"]=-6; effects["strength_wins"]=+4
    if "regret" in letter.lower() or "never" in letter.lower():
        for k in list(effects.keys()): effects[k]=int(effects[k]*0.5)
    return effects

def create_shrine_for_dead(grave):
    init_shrines()
    if not grave.get("final_letter") or not grave.get("is_legend"): return
    if any(s["for"]==grave["name"] for s in world["shrines"]): return
    faction=grave.get("faction","?"); fdata=FACTIONS.get(faction,{}); home=fdata.get("home",[0,0])
    pos=clamp([home[0]+random.uniform(-15,15),home[1]+random.uniform(-15,15)])
    shrine={"id":"shrine_%d"%world["tick"],"name":random.choice(SHRINE_NAMES),"for":grave["name"],"faction":faction,"type":grave.get("type","warrior"),"letter":grave["final_letter"],"position":pos,"year_created":world["year"],"visitors":[],"belief_effects":derive_shrine_belief_effects(grave),"visits_total":0}
    world["shrines"].append(shrine)
    if len(world["shrines"])>50: world["shrines"]=world["shrines"][-50:]
    history("A shrine was erected for %s (%s) — their final words preserved."%(grave["name"],grave["type"]),importance=3)
    log("SHRINE: Erected for %s — '%s'"%(grave["name"],grave.get("final_letter","...")[:60]),"legend")
    sound("world_event")

def check_new_shrines():
    init_shrines(); existing={s["for"] for s in world["shrines"]}
    for record in world.get("graveyard",[])[-5:]:
        if record.get("is_legend") and record.get("final_letter") and record["name"] not in existing:
            create_shrine_for_dead(record)

def tick_shrine_visits():
    init_shrines()
    if not world["shrines"]: return
    for agent in living():
        if random.random()>0.015: continue
        if agent["type"] in ("priest","explorer","scholar","healer") and random.random()<0.3 and world["shrines"]:
            nearest=min(world["shrines"],key=lambda s:dist(agent["position"],s["position"]))
            agent["target"]=nearest["position"]
        for shrine in world["shrines"]:
            if dist(agent["position"],shrine["position"])<5:
                if agent["name"] in shrine["visitors"]: continue
                shrine["visitors"].append(agent["name"]); shrine["visits_total"]+=1
                b=agent.get("beliefs",{})
                for bk,delta in shrine["belief_effects"].items():
                    if bk in b:
                        b[bk]["confidence"]=max(0,min(100,b[bk]["confidence"]+delta))
                        if abs(delta)>5: b[bk]["source"]="read at shrine of %s"%shrine["for"]
                remember(agent,"discovery","Read the last words of %s at the %s. Changed how I see things. Y%d"%(shrine["for"],shrine["name"],world["year"]),importance=4)
                if agent.get("emotion") in ("content","curious","lonely"): agent["emotion"]=random.choice(["inspired","devoted","proud"])
                log("SHRINE: %s read the last words of %s"%(agent["name"],shrine["for"]),"legend")
                world["stats"]["shrine_visits"]=world["stats"].get("shrine_visits",0)+1
                if agent.get("emotion")=="inspired" and "originated_goals" in agent:
                    existing_g=[g["goal"] for g in agent["originated_goals"]]
                    if "honor the memory of those who came before me" not in existing_g:
                        agent["originated_goals"].append({"goal":"honor the memory of those who came before me","origin":"read last words of %s"%shrine["for"],"priority":6,"type":"legacy","active":True,"born_year":world["year"]})
                break

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# UPGRADE 9 — MID-LIFE ARCHETYPE EVOLUTION
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
def check_archetype_evolution():
    for agent in living():
        if agent.get("archetype_evolved"): continue
        atype=agent["type"]; age=agent.get("age",0); skills=len(agent.get("skills",[])); sm=agent.get("self_model",{}); faith=agent.get("faith",0)
        # PHILOSOPHER
        if atype=="scholar" and age>150 and skills>=5 and sm.get("identity_stability",50)>75 and sm.get("world_understanding",0)>65:
            agent["type"]="philosopher"; agent["archetype_evolved"]="philosopher"; agent["archetype_year"]=world["year"]
            agent["battle_power"]=agent.get("battle_power",10)+5; agent["max_age"]=agent.get("max_age",300)+80
            agent["philosophy_influence_range"]=15
            remember(agent,"joy","I have transcended scholarship. I am a Philosopher now. Y%d"%world["year"],importance=5)
            log("ARCHETYPE: %s became a PHILOSOPHER!"%agent["name"],"cognition")
            history("A Philosopher emerged: %s — age %d, %d skills"%(agent["name"],age,skills),importance=5)
            world["stats"]["philosophers_emerged"]=world["stats"].get("philosophers_emerged",0)+1; sound("legend")
        # CRIME LORD
        elif atype=="merchant" and age>100 and len(recall(agent,"betrayal"))>=2 and world["resources"].get("gold",0)>200 and sm.get("social_standing",50)>55:
            agent["type"]="crime_lord"; agent["archetype_evolved"]="crime_lord"; agent["archetype_year"]=world["year"]
            agent["battle_power"]=agent.get("battle_power",10)+12; agent["gold_drain_power"]=5
            remember(agent,"discovery","I learned from betrayal. Now I run the game. Y%d"%world["year"],importance=5)
            log("ARCHETYPE: %s became a CRIME LORD!"%agent["name"],"cognition")
            history("A Crime Lord emerged: %s — born from betrayal"%agent["name"],importance=4)
            world["stats"]["crime_lords_emerged"]=world["stats"].get("crime_lords_emerged",0)+1; sound("betrayal")
        # PLAGUE DOCTOR
        elif atype=="healer" and age>200 and any("survived" in m["content"].lower() for m in recall(agent,"joy")):
            agent["type"]="plague_doctor"; agent["archetype_evolved"]="plague_doctor"; agent["archetype_year"]=world["year"]
            agent["disease"]=None; agent["disease_immune"]=True; agent["heal_power"]=agent.get("heal_power",15)+25; agent["plague_sense"]=True
            remember(agent,"joy","I am immune. I am the cure. Y%d"%world["year"],importance=5)
            log("ARCHETYPE: %s became a PLAGUE DOCTOR!"%agent["name"],"cognition")
            history("A Plague Doctor emerged: %s — immune healer"%agent["name"],importance=4)
            world["stats"]["plague_doctors_emerged"]=world["stats"].get("plague_doctors_emerged",0)+1; sound("evolution")
        # PATRIARCH/MATRIARCH
        elif atype=="farmer" and age>250:
            agent_id=agent["id"]
            descs=[cid for cid,lin in world.get("lineage",{}).items() if lin.get("parent_a")==agent_id or lin.get("parent_b")==agent_id]
            if len(descs)>=2:
                agent["type"]=random.choice(["patriarch","matriarch"]); agent["archetype_evolved"]=agent["type"]; agent["archetype_year"]=world["year"]
                agent["max_age"]=agent.get("max_age",300)+100; lb=len(descs)*2; agent["lineage_bonus"]=lb
                dc=0
                for a in living():
                    if a["id"] in descs:
                        a["health"]=min(150,a.get("health",100)+lb); a["max_age"]=a.get("max_age",300)+20
                        remember(a,"joy","My ancestor %s ascended. I feel their strength. Y%d"%(agent["name"],world["year"]),importance=4); dc+=1
                remember(agent,"joy","I am %s — ancestor to %d souls. Y%d"%(agent["type"].capitalize(),dc,world["year"]),importance=5)
                log("ARCHETYPE: %s became a %s — %d descendants boosted!"%(agent["name"],agent["type"].upper(),dc),"cognition")
                history("A %s emerged: %s — ancestor of %d"%(agent["type"].capitalize(),agent["name"],dc),importance=4)
                world["stats"]["patriarchs_emerged"]=world["stats"].get("patriarchs_emerged",0)+1; sound("legend")

def tick_archetype_abilities():
    for agent in living():
        arch=agent.get("archetype_evolved")
        if not arch: continue
        if arch=="philosopher":
            radius=agent.get("philosophy_influence_range",15)
            for other in [a for a in living() if a["id"]!=agent["id"] and dist(agent["position"],a["position"])<radius][:5]:
                ob=other.get("beliefs",{}); ab=agent.get("beliefs",{})
                for bk in INFLUENCE_BELIEFS:
                    if bk in ob and bk in ab:
                        ob[bk]["confidence"]=int(ob[bk]["confidence"]+(ab[bk]["confidence"]-ob[bk]["confidence"])*0.002)
        elif arch=="crime_lord":
            if random.random()<0.05:
                world["resources"]["gold"]=world["resources"].get("gold",0)+agent.get("gold_drain_power",5)
                faction=agent.get("faction","?")
                for other in FACTIONS:
                    if other!=faction and get_diplo(faction,other)!="war": add_tension(faction,other,1)
        elif arch=="plague_doctor":
            agent["disease"]=None
            if random.random()<0.1:
                for sick in [a for a in living() if a.get("disease") and dist(agent["position"],a["position"])<12][:3]:
                    sick["disease"]=None; sick["disease_ticks"]=0; sick["health"]=min(150,sick.get("health",100)+20)
                    remember(sick,"joy","The Plague Doctor %s cured me! Y%d"%(agent["name"],world["year"]),importance=4)

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# UPGRADE 10 — SEASONAL FESTIVALS AND RITUALS
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
SEASONAL_FESTIVALS={
    "Ironveil":{"spring":("The Rite of Blades","Warriors sharpen weapons and swear oaths."),"summer":("The Festival of Iron","The forge burns all night; weapons are blessed."),"autumn":("The March of Fallen","Dead warriors' names carved into stone."),"winter":("The Night Watch","Warriors stand vigil against the cold darkness.")},
    "Greenveil":{"spring":("The Bloom Festival","Seeds are blessed; faith renewed under open skies."),"summer":("The Feast of Light","A great meal shared — none go hungry."),"autumn":("The Harvest Rite","Crops dedicated to the divine."),"winter":("The Long Night Prayer","Priests lead a night-long prayer vigil.")},
    "Goldveil":{"spring":("The Market of Beginnings","New trade agreements celebrated with a grand bazaar."),"summer":("The Coin Toss Festival","A great lottery where all agents win something."),"autumn":("The Balance Day","Debts settled; accounts cleared for the new year."),"winter":("The Winter Exchange","Rare goods from distant lands traded.")},
    "Shadowveil":{"spring":("The Awakening Rite","Spies emerge from winter cover; assignments begin."),"summer":("The Night of Whispers","Secrets traded in coded ceremony."),"autumn":("The Veil Ceremony","Identities ritually abandoned and rebuilt."),"winter":("The Silence","Total information blackout — faction disappears.")},
}

def tick_seasonal_festivals():
    if "last_festival_season" not in world: world["last_festival_season"]={}; world["festival_history"]=[]
    season=world["season"]
    for faction in FACTIONS:
        if world["last_festival_season"].get(faction)==season: continue
        fa=faction_agents(faction)
        if not fa: continue
        priests=[a for a in fa if a["type"]=="priest"]
        avg_faith=sum(a.get("faith",0) for a in fa)/len(fa)
        if not ((priests and avg_faith>5) or (len(fa)>=5 and avg_faith>15)): continue
        if random.random()>0.7: continue
        fdata=SEASONAL_FESTIVALS.get(faction,{}).get(season)
        if not fdata: continue
        fname,fdesc=fdata; world["last_festival_season"][faction]=season
        fb=random.randint(5,20)+len(priests)*3
        for a in fa:
            a["faith"]=min(AGENT_FAITH_CAP,a.get("faith",0)+fb//2)
            remember(a,"joy","Celebrated %s with %s. Y%d %s"%(fname,faction,world["year"],season),importance=3)
            for b in fa:
                if b["id"]!=a["id"] and not has_mem(a,"friend","ritual_bond:%s"%b["name"]):
                    remember(a,"friend","ritual_bond:%s — shared %s Y%d"%(b["name"],fname,world["year"]),importance=2)
        world["resources"]["faith"]=min(FAITH_CAP,world["resources"].get("faith",0)+fb*len(fa))
        if faction=="Greenveil":
            for a in fa: a["health"]=min(150,a.get("health",100)+10)
        if faction=="Goldveil": world["resources"]["gold"]=world["resources"].get("gold",0)+len(fa)*5
        if faction in ("Goldveil","Shadowveil"): world["resources"]["knowledge"]=world["resources"].get("knowledge",0)+30
        for other in FACTIONS:
            if other!=faction and get_diplo(faction,other)=="allied": reduce_tension(faction,other,10)
        world["festival_history"].append({"tick":world["tick"],"year":world["year"],"season":season,"faction":faction,"name":fname,"desc":fdesc,"participants":len(fa)})
        if len(world["festival_history"])>100: world["festival_history"]=world["festival_history"][-100:]
        history("%s held the %s in %s — %d participants. %s"%(faction,fname,season,len(fa),fdesc),importance=3)
        log("FESTIVAL: %s holds '%s' — faith +%d"%(faction,fname,fb),"religion")
        sound("world_event"); world["stats"]["festivals_held"]=world["stats"].get("festivals_held",0)+1

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# UPGRADE 11 — DREAMS / UNCONSCIOUS PROCESSING
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
DREAM_CONNECTORS=["becomes","transforms into","speaks with the voice of","surrounds","dissolves into","calls out to","is followed by","burns alongside","walks beside","is judged by","rises above"]
DREAM_DISTORTIONS=["but their face is wrong","but the sky is the wrong color","but everything is silent","but I cannot move","but the world is upside down","but nothing casts a shadow","but time moves backward","but I am someone else","but I am very small","but the ground is made of water"]

def generate_dream(agent):
    mems=agent["memories"]
    if len(mems)<3: return None,None
    pool=sorted(mems[-15:],key=lambda m:m["importance"],reverse=True)
    sample=random.sample(pool[:10],min(3,len(pool[:10])))
    images=[]
    for m in sample:
        words=[w for w in m["content"].split() if len(w)>3 and not w.isdigit() and w not in ("the","and","for","with","from","that","this","they")]
        if words: images.append(random.choice(words[:5]))
    if len(images)<2: return None,None
    connector=random.choice(DREAM_CONNECTORS); distortion=random.choice(DREAM_DISTORTIONS)
    dream="%s %s %s, %s"%(images[0],connector,images[1],distortion)
    if len(images)>2: dream+=", and %s watches from a distance"%images[2]
    mtypes=[m["type"] for m in sample]
    if "trauma" in mtypes and "discovery" in mtypes: dtype="revelation"
    elif "loss" in mtypes: dtype="grief_dream"
    elif "battle" in mtypes and "betrayal" in mtypes: dtype="nightmare"
    elif "joy" in mtypes and "friend" in mtypes: dtype="warm_dream"
    elif "discovery" in mtypes: dtype="insight_dream"
    else: dtype="strange_dream"
    return dream,dtype

def tick_dreams():
    alive=living()
    if not alive: return
    for agent in random.sample(alive,min(3,len(alive))):
        if random.random()>0.04 or not agent.get("memories"): continue
        dream,dtype=generate_dream(agent)
        if not dream: continue
        remember(agent,"discovery","DREAM: %s Y%d"%(dream,world["year"]),importance=2)
        agent["last_dream"]=dream; agent["last_dream_type"]=dtype
        if dtype=="revelation":
            if "originated_goals" in agent:
                if "understand what my dreams are telling me" not in [g["goal"] for g in agent["originated_goals"]]:
                    agent["originated_goals"].append({"goal":"understand what my dreams are telling me","origin":"revelation dream","priority":5,"type":"understanding","active":True,"born_year":world["year"]})
                    world["stats"]["goals_originated"]=world["stats"].get("goals_originated",0)+1
        elif dtype=="grief_dream": agent["emotion"]="grieving"
        elif dtype=="nightmare": agent["emotion"]="afraid"; agent["health"]=max(1,agent.get("health",100)-random.randint(1,5))
        elif dtype=="warm_dream": agent["health"]=min(150,agent.get("health",100)+3); agent["emotion"]="joyful"
        elif dtype=="insight_dream": world["resources"]["knowledge"]=world["resources"].get("knowledge",0)+random.randint(3,10); agent["emotion"]="curious"
        world["stats"]["dreams_generated"]=world["stats"].get("dreams_generated",0)+1
        if random.random()<0.03: log("DREAM: %s — '%s' [%s]"%(agent["name"],dream[:60],dtype),"cognition")

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# UPGRADE 12 — MULTI-AGENT SPY CONSPIRACIES
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
def init_conspiracies():
    if "conspiracies" not in world: world["conspiracies"]=[]

def tick_spy_conspiracies():
    init_conspiracies(); alive=living()
    # Cell formation
    for faction in FACTIONS:
        spies=[a for a in faction_agents(faction) if a["type"] in ("spy","assassin") and not a.get("in_conspiracy")]
        if len(spies)<2: continue
        for i,sa in enumerate(spies):
            for sb in spies[i+1:]:
                if dist(sa["position"],sb["position"])<6 and has_mem(sa,"friend",sb["name"]) and random.random()<0.02:
                    ef=[f for f in FACTIONS if get_diplo(faction,f)=="war"]
                    if not ef and faction=="Shadowveil": ef=[f for f in FACTIONS if f!=faction]
                    if not ef: continue
                    ea=faction_agents(random.choice(ef))
                    if not ea: continue
                    tp=([a for a in ea if a.get("is_legend")] or ea); target=random.choice(tp)
                    con={"id":"con_%d"%world["tick"],"faction":faction,"cell":[sa["id"],sb["id"]],"cell_names":[sa["name"],sb["name"]],"target_id":target["id"],"target_name":target["name"],"target_faction":target.get("faction","?"),"phase":"forming","phase_ticks":0,"formed_year":world["year"],"log":[]}
                    world["conspiracies"].append(con); sa["in_conspiracy"]=con["id"]; sb["in_conspiracy"]=con["id"]
                    remember(sa,"discovery","Formed conspiracy with %s. Target: %s. Y%d"%(sb["name"],target["name"],world["year"]),importance=5)
                    remember(sb,"discovery","Joined conspiracy with %s. We hunt %s. Y%d"%(sa["name"],target["name"],world["year"]),importance=5)
                    log("CONSPIRACY: %s and %s form cell targeting %s"%(sa["name"],sb["name"],target["name"]),"espionage")
                    history("Spy conspiracy formed in %s — %s and %s target %s"%(faction,sa["name"],sb["name"],target["name"]),importance=3)
                    world["stats"]["conspiracies_formed"]=world["stats"].get("conspiracies_formed",0)+1; break
    # Phase advancement
    alive_ids={a["id"] for a in alive}; alive_map={a["id"]:a for a in alive}
    for con in list(world["conspiracies"]):
        if con["phase"] in ("completed","failed"): continue
        con["phase_ticks"]+=1; cell_alive=[aid for aid in con["cell"] if aid in alive_ids]
        if len(cell_alive)<2:
            con["phase"]="failed"; con["log"].append("Cell broken Y%d"%world["year"])
            for aid in cell_alive:
                if aid in alive_map: alive_map[aid].pop("in_conspiracy",None)
            continue
        target_alive=con["target_id"] in alive_ids
        if not target_alive:
            con["phase"]="completed"; con["log"].append("Target already dead Y%d"%world["year"])
            for aid in cell_alive: alive_map[aid].pop("in_conspiracy",None)
            continue
        target=alive_map.get(con["target_id"])
        if con["phase"]=="forming" and con["phase_ticks"]>=5:
            con["phase"]="scouting"; con["phase_ticks"]=0
            if target:
                for aid in cell_alive:
                    if aid in alive_map: alive_map[aid]["target"]=target["position"]
            log("CONSPIRACY SCOUTING: Cell tracking %s"%con["target_name"],"espionage")
        elif con["phase"]=="scouting" and con["phase_ticks"]>=10:
            close=[aid for aid in cell_alive if aid in alive_map and target and dist(alive_map[aid]["position"],target["position"])<15]
            if close: con["phase"]="confirming"; con["phase_ticks"]=0; log("CONSPIRACY CONFIRMED: %s located"%con["target_name"],"espionage")
            elif con["phase_ticks"]>25:
                con["phase"]="failed"; con["log"].append("Lost track Y%d"%world["year"])
                for aid in cell_alive: alive_map[aid].pop("in_conspiracy",None) if aid in alive_map else None
        elif con["phase"]=="confirming" and con["phase_ticks"]>=5:
            con["phase"]="executing"; con["phase_ticks"]=0
            if target:
                for aid in cell_alive:
                    if aid in alive_map: alive_map[aid]["target"]=target["position"]
        elif con["phase"]=="executing":
            if target:
                for aid in cell_alive:
                    if aid in alive_map: alive_map[aid]["target"]=target["position"]
            strikers=[alive_map[aid] for aid in cell_alive if aid in alive_map and target and dist(alive_map[aid]["position"],target["position"])<3]
            if strikers and random.random()<0.25:
                dmg=random.randint(50,90)+(20 if len(strikers)>=2 else 0)
                target["health"]=max(0,target.get("health",100)-dmg)
                world["stats"]["assassinations"]=world["stats"].get("assassinations",0)+1
                for s in strikers: remember(s,"battle","CONSPIRACY: Struck %s in coordinated assassination. Y%d"%(con["target_name"],world["year"]),importance=5)
                if target["health"]<=0:
                    bury_agent(target,"assassination:conspiracy by %s"%" & ".join(con["cell_names"]))
                    target["alive"]=False; world["stats"]["total_deaths"]=world["stats"].get("total_deaths",0)+1; world["stats"]["battle_deaths"]=world["stats"].get("battle_deaths",0)+1
                    con["phase"]="completed"; con["log"].append("SUCCESS: %s eliminated Y%d"%(target["name"],world["year"]))
                    for aid in cell_alive: alive_map[aid].pop("in_conspiracy",None) if aid in alive_map else None; (alive_map[aid].__setitem__("emotion","proud") if aid in alive_map else None)
                    history("CONSPIRACY SUCCESS: %s and %s eliminated %s"%(con["cell_names"][0],con["cell_names"][1],target["name"]),importance=5)
                    log("CONSPIRACY EXECUTED: %s ELIMINATED by %s!"%( target["name"]," & ".join(con["cell_names"])),"espionage")
                    sound("assassination"); world["stats"]["conspiracies_succeeded"]=world["stats"].get("conspiracies_succeeded",0)+1; world["stats"]["conspiracy_kills"]=world["stats"].get("conspiracy_kills",0)+1
                elif random.random()<0.3:
                    con["phase"]="failed"; con["log"].append("Detected Y%d"%world["year"])
                    remember(target,"trauma","Ambushed by %s — conspiracy against me! Y%d"%(" & ".join(con["cell_names"]),world["year"]),importance=5)
                    for aid in cell_alive: alive_map[aid].pop("in_conspiracy",None) if aid in alive_map else None
                    log("CONSPIRACY DETECTED: %s wounded but survived"%target["name"],"espionage")
            elif con["phase_ticks"]>20:
                con["phase"]="failed"; con["log"].append("Could not reach target Y%d"%world["year"])
                for aid in cell_alive: alive_map[aid].pop("in_conspiracy",None) if aid in alive_map else None
    world["conspiracies"]=[c for c in world["conspiracies"] if c["phase"] not in ("completed","failed")][-30:]+[c for c in world["conspiracies"] if c["phase"] in ("completed","failed")][-10:]

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# MASTER UPGRADE TICK
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
def tick_all_upgrades():
    alive=living()
    # Intelligence
    tick_influence_propagation()
    tick_counterfactual_reasoning()
    tick_theory_of_mind()
    tick_oral_tradition()
    # Structural
    update_faction_culture()
    for a in alive: apply_cultural_priors(a)
    tick_knowledge_graph()
    tick_geographic_influence()
    check_new_shrines()
    tick_shrine_visits()
    # New Features
    check_archetype_evolution()
    tick_archetype_abilities()
    tick_seasonal_festivals()
    tick_dreams()
    tick_spy_conspiracies()

def init_all_upgrades():
    world.setdefault("influence_zones",{})
    world.setdefault("oral_tradition",{})
    world.setdefault("shrines",[])
    world.setdefault("conspiracies",[])
    world.setdefault("last_festival_season",{})
    world.setdefault("festival_history",[])
    init_faction_culture_values()
    for stat in ["influence_events","counterfactuals_generated","tom_models_built","tom_exploits","oral_retellings","myths_formed","shrine_visits","philosophers_emerged","crime_lords_emerged","plague_doctors_emerged","patriarchs_emerged","festivals_held","dreams_generated","conspiracies_formed","conspiracies_succeeded","conspiracy_kills","contested_zones_peak"]:
        world["stats"].setdefault(stat,0)
    print("  v8.0 UPGRADES: Influence|Counterfactual|ToM|OralTradition|FactionCulture|KnowledgeGraph|GeoZones|Shrines|Archetypes|Festivals|Dreams|Conspiracies")

# fmt: on
# ╚══════════════════════════════════════════════════════════════════╝

def tick():
    world["tick"]+=1
    world["stats"]["total_ticks_ever"]=world["stats"].get("total_ticks_ever",0)+1
    world["sound_queue"]=[]  # reset sound queue each tick

    update_seasons(); tick_weather(); tick_diplomacy(); tick_tech(); tick_diseases(); tick_evolution(); tick_religious_tension(); tick_alive_system(); tick_cognition(); tick_alive()
    tick_social_contracts(living()); tick_world_response(); tick_world_memory(); tick_meta_evolution()
    check_institution_formation(); tick_institutions(); tick_institution_consciousness()
    tick_all_upgrades()

    # ── AGI COLLECTIVE LOOP ───────────────────────────────────────
    if _COLLECTIVE_LOOP_LOADED:
        try: tick_collective(world)
        except Exception as _e: log("AGI: tick_collective error: %s" % _e, "agi")
    # ─────────────────────────────────────────────────────────────

    alive=sum(1 for a in world["agents"] if a["alive"])
    if alive<MAX_AGENTS:
        counts={f:len(faction_agents(f)) for f in FACTIONS}
        weakest=min(counts,key=counts.get)
        if world["tick"]==1 or random.random()<0.18: spawn_agent(weakest)

    world["agents"]=[agent_think(a) if a["alive"] else a for a in world["agents"]]

    dead=[a for a in world["agents"] if not a["alive"]]
    alive_list=[a for a in world["agents"] if a["alive"]]
    world["agents"]=alive_list+dead[-12:]
    world["population"]=len(alive_list)

    r=world["resources"]
    for res,gain in [("wood",3),("stone",2),("gold",1),("iron",1),("herbs",2)]:
        r[res]=r.get(res,0)+random.randint(0,gain)

    enforce_resource_caps()
    random_world_event()
    update_cities()
    update_faction_power()
    check_win_conditions()

    if world["tick"]%SAVE_EVERY==0: save_persistent()
    if world["tick"]%LOG_EVERY_TICKS==0: log_world_snapshot()
    if world["tick"]%50==0: log_agent_snapshots()
    save_state()

def initialize():
    global _agent_counter
    print("="*68)
    print("  AI WORLD ENGINE v8.0 — INTELLIGENT SELF-AUTOMATION")
    print("="*68)
    loaded=load_persistent()
    if not loaded:
        print("  Creating a new world from nothing...")
        world["terrain"]=generate_terrain()
        world["biome_map"]=generate_biomes()
        world["resources"]={r:random.randint(15,60) for r in RESOURCE_TYPES}
        world["world_history"]=[]; world["legends"]=[]
        world["graveyard"]=[]; world["lineage"]={}
        world["conversations"]=[]; world["war_timeline"]=[]
        world["sound_queue"]=[]; world["winner"]=None
        flist=list(FACTIONS.keys())
        for i,fa in enumerate(flist):
            for fb in flist[i+1:]: set_diplo(fa,fb,"neutral")
        with open(LOG_FILE,"w",encoding="utf-8") as f: f.write("=== AI WORLD v4.0 LOG ===\n\n")
        for faction in FACTIONS:
            for _ in range(3): spawn_agent(faction)
        history("The world was born. Four civilizations rose from the void.",importance=5)
        init_all_upgrades()
        # ── AGI COLLECTIVE INIT ──────────────────────────────────────
        if _COLLECTIVE_LOOP_LOADED:
            try: init_collective(world)
            except Exception as _e: print("  [AGI] init_collective failed: %s" % _e)
        # ────────────────────────────────────────────────────────────
    else:
        _agent_counter=len(world["agents"])
        try:
            with open(LOG_FILE,"a",encoding="utf-8") as f:
                f.write("\n=== RESUMED %s ===\n\n"%datetime.now().isoformat())
        except Exception: pass
        log("The world awakens. All memories are intact.","world")
        init_all_upgrades()
        # ── AGI COLLECTIVE INIT (resumed world) ──────────────────────
        if _COLLECTIVE_LOOP_LOADED:
            try: init_collective(world)
            except Exception as _e: print("  [AGI] init_collective failed: %s" % _e)
        # ────────────────────────────────────────────────────────────

    print("")
    print("  Factions  : %s"%(" | ".join(f+FACTIONS[f]["symbol"] for f in FACTIONS)))
    print("  Roles     : %s"%", ".join(AGENT_TYPES.keys()))
    print("  v3 systems: Genetics | Factions | Wars | Diplomacy | Betrayal")
    print("              Disease | Tech Tree | Religion | Legends | Cities")
    print("              Weather | Reproduction | Deep Memory (x%d)"%MAX_MEMORY)
    print("  v4 NEW    : Conversations | Biomes | Win Conditions | Graveyard")
    print("              Lineage/Dynasties | Sound Events | Rich Stats")
    print("  v5/6/7   : Legends | Religion | Emotions | Goals | Voice | Wars | Cognition")
    print("  v8.0 NEW : Influence|Counterfactual|ToM|OralTrad|FactionCulture|KnowledgeGraph")
    print("  v9.0 AGI : BDI[%s] | LLMMind[%s] | ValueEngine[%s] | Collective[%s]" % (
        "ON" if _COGNITIVE_LOOP_LOADED else "OFF",
        "ON" if _LLM_MIND_LOADED      else "OFF",
        "ON" if _VALUE_ENGINE_LOADED   else "OFF",
        "ON" if _COLLECTIVE_LOOP_LOADED else "OFF",
    ))
    print("  Saves     : every %d ticks to %s"%(SAVE_EVERY,WORLD_SAVE_FILE))
    print("  Dashboard : http://localhost:8000/dashboard.html")
    print("  Tick rate : %ss"%TICK_RATE)
    print("="*68)
    print("")
    init_research_logging()
    save_state()

def run():
    initialize()
    while True:
        try:
            tick(); time.sleep(TICK_RATE)
        except KeyboardInterrupt:
            print("\n\nSaving world before shutdown...")
            save_persistent()
            finalize_research()
            print("The world sleeps.")
            print("  %d souls | Year %d | %d legends | %d in graveyard | %d conversations | %d skills unlocked"%(
                world["population"],world["year"],len(world["legends"]),
                len(world["graveyard"]),world["stats"].get("conversations",0),
                world["stats"].get("skills_unlocked",0)))
            if _COLLECTIVE_LOOP_LOADED:
                try:
                    snap = get_collective_snapshot(world)
                    print("  AGI: epoch=%s | knowledge_nodes=%d | upheavals=%d | movements=%d" % (
                        snap["epoch"], snap["knowledge_network"]["total_concepts"],
                        snap["eternal_loop"]["upheavals"], snap["movements"]["active"]))
                except Exception: pass
            break

if __name__=="__main__":
    run()
