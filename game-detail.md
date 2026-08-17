# Python Games

## Title

Title: TBD (Medieval Fantasy Colony Survival)

## Background

Mid century fantasy. Includes magical creature (werewolf, vampire etc.) and magic.
Player is the Lord (領主), controlling everyone's work assignments.
Medieval magic style (中世紀 魔法風).

## Game System

### Core System

> Base on Oxygen Not Included task system.

Player is the Lord of a territory, the player can control NPCs to manage their territory.
Player can placed tasks, for example, ask NPCs to destroy a item on the map, or build a defence building.

### Sight and Map

Top-down view 2D map, the map is composed by squares, each squares might be empty or contained with a resource.

### Round System (回合制)

The game is turn/round-based. Each round consists of:

1. **Daytime (白天)** — Player assigns work:
   - Gather food (採集/打獵/種植)
   - Expand territory (開拓領土)
   - Build structures

2. **Night (晚上)** — Monster attack phase:
   - Nests spawn monsters (巢穴生成怪物)
   - Monsters advance toward territory (怪物朝領地前進)
   - Characters fight or defend
   - Basically rest at night, but need shift/watch duty (基本夜晚休息，但要有人排班)

3. **Post-round** — Skill upgrades:
   - If all monsters killed → extra skill reward points
   - If remaining monsters → ability boost based on kill count
   - Select skill upgrades before next round starts

#### Character Growth
- Start with **3 characters** (三隻角色)
- Every **3 rounds**, gain **1 additional character** (經過三回合增加一隻)

### Map Item

#### Defensive Buildings (防禦性建築)
Different facilities have different values:
- **Wall (城牆)** — blocks monster advance
- **Arrow Tower (箭塔)** — ranged defense
- **House (房子)** — increases population capacity (提升人口)
- **Farmland (農地)** — enables crop planting

#### Resources

**Construction Materials (建築):**
- Marble (大理石)
- Wood (木頭)
- Bricks (磚頭)

**Magic Materials (魔法原料):**
- Berries (莓果)
- Raw Stone (原石)

**Food Sources (食物):**

| Method | Items |
|--------|-------|
| Gather Wild (採集野生) | Mushrooms (香菇) |
| Hunt (打獵) | Flying Squirrel (飛鼠), Wild Boar (山豬), Fish (魚), Horse (馬) |
| Farm/Plant (種植) | Vegetables (蔬菜), Tomatoes (番茄) |

- Hunted animals can be either **Tamed (馴服)** or used as **Food (食物)**
- **Food spoils over time (食物放久會腐敗)**

#### Creatures

**Hostile (怪物):**
- Werewolf
- Vampire
- Zombie
- Spawned from nests, advance toward player territory

**Animals (can be hunted or tamed):**
- Wolf
- Bear
- Wild Boar (山豬)
- Flying Squirrel (飛鼠)
- Fish (魚)
- Horse (馬)

## NPC Related

### Roles (角色)

Three character classes, each with different specialties:

| Role | Chinese | Specialty 1 | Specialty 2 |
|------|---------|-------------|-------------|
| **Farmer** | 農民 | Gather Speed (採集速度) | Taming Ability (馴服能力) |
| **Knight** | 騎士 | Hunting Accuracy (打獵準度) | Defense Ability (防禦能力) |
| **Mage** | 魔法師 | Magic Attack (魔法攻擊) | AoE Attack (群體攻擊) |

Every NPC has a role, and each role has different abilities. For example, a builder can build buildings faster than a farmer, a knight has higher attack power.

### Skills System (技能)

Upgradeable skills (earned after combat rounds):
- Gather Speed (採集速度)
- Hunting Accuracy (打獵準度)
- Taming Ability (馴服能力)
- Defense Ability (防禦能力)
- Magic Attack (魔法攻擊)
- AoE Attack (群體攻擊)

### Magic System (魔法)

Available spells:
- **Fire (火焰)** — fire-based damage
- **Lightning (閃電)** — electric-based damage
- **Freeze (凍結)** — ice-based crowd control

### Character Status Bars

Each character has two status bars:
- **Health/Stamina Bar (體力血條)** — depleted by monster attacks
- **Hunger Bar (飢餓血條)** — depleted over time, requires food

### Task System

NPC's task system is the core of this games, every NPC may work on any tasks, but they will follow their task priority (player may set the priority).

### Time System

Fixed real-time timer per phase, not player-triggered: ~2 minutes per Day, ~1 minute per Night. Simulation runs live and is pausable (pausing freezes the sim, camera/input still work) — player queues tasks while paused, unpauses to watch them execute, day advances to night automatically when the timer runs out.

## Game Over Conditions (遊戲結束判定)

The game ends when **all characters die** (所有角色死亡). Characters can die from:
- **Monster attack (被攻擊而死亡)** — health bar reaches 0
- **Starvation (因飢餓而死亡)** — hunger falls below daily food requirement

## Win Condition

No fixed win state — endless survival. Score = number of rounds survived.

## Implementation Decisions

Resolved through a scoping interview (1-week solo dev budget). These fill in the mechanics the sections above leave open-ended.

**Execution model**: Real-time, pausable simulation (see Time System above), not strict turn-based menus.

**Map & camera**: Grid is procedurally generated once at new-game start, fixed size, larger than the viewport — camera scrolls/pans. "Expand territory" is the task that does double duty: it both clears fog-of-war on nearby unrevealed tiles and marks them as claimed/buildable in one action. Buildings can be freely placed on any claimed empty tile — no adjacency or line-of-sight placement rules (e.g. Walls don't need to connect to form a perimeter).

**NPC movement**: Continuous pixel movement with A* pathfinding on the grid (not discrete tile-stepping). Monsters use the same movement system to advance on territory.

**Task system**: Global task queue; each NPC has its own priority ranking per task type (full ONI-style per-NPC priority table, not one shared list) — idle NPCs auto-claim the highest-priority task available to them. Gathered/harvested resources go straight into a shared global inventory the moment a task completes — no separate Haul task, no ground items, no storage buildings.

**Combat**: Base combat is auto-engage-by-proximity — NPCs/towers and monsters fight automatically based on stats when adjacent/in range, no manual per-attack targeting. "Shift/watch duty" from the Round System section is flavor, not a separate assignable task — any NPC near a threat at night auto-defends. Magic spells are cooldown-based (no mana bar) and auto-target the nearest threat when cast — this is the one place combat has live player input (choosing when to trigger a spell).

**Monster nests**: Not fixed solely at map generation — new nests can appear over time as rounds progress, escalating difficulty. Exact spawn rate/cap is a tunable balance value, not locked yet.

**Taming**: Player queues a Tame task on a hunted-but-uneaten animal (this is the Farmer's Taming Ability specialty). Tamed animals live in a pen and passively produce resources over time — they are not controllable combat/work units like NPCs.

**Skill upgrades**: Post-round upgrade phase is player-driven — each NPC that leveled up offers a choice of 1-of-3 skills to improve, not automatic.

**Character population cap**: Still open (TBD). Growth is +1 NPC every 3 rounds starting from 3; a hard cap (likely tied to House count) will be defined later.

**Save/load**: Basic save/load needed, checkpoint-style — only saves at the day/night phase boundary, not mid-simulation.

**Art**: Primitive shapes + color coding (`pygame.draw`), no sprite assets for the 1-week build — swappable for real sprites later without touching game logic.

**Build order** (cut from the tail if the week runs short):
1. Core loop — grid, fog/claim, task queue + priority table, one generic NPC, day/night timer, Wall/Tower, auto-combat, gather → inventory, save/load
2. Role split (Farmer/Knight/Mage stats)
3. Combat depth — A* monster movement, nest spawn ramp, magic
4. Taming, skill-tree upgrades, food spoilage polish
