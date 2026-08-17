# Medievil — Project Implementation Roadmap & Missing Features (TODO)

This document tracks all missing features identified from [`game-detail.md`](file:///Users/miohitokiri5474/school_hw/PyGame/final/game-detail.md) and the Figma design board, organized by development phases with comprehensive technical and game design details.

---

## Phase 1: Character Roles & Colony Growth (角色與人口系統)

### 1.1 Character Role Differentiation (Farmer / Knight / Mage)
- [ ] **Role Assignment**:
  - Assign each starting character one of the 3 roles upon game start (e.g. 1 Farmer, 1 Knight, 1 Mage).
  - Newly recruited characters have an assigned role (random or player-selected).
- [ ] **Specialty Attributes & Stat Scaling**:
  - **Farmer (農民)**:
    - Base Gather Duration Multiplier: `0.6x` (harvests 40% faster).
    - Base Taming Multiplier: `1.5x` success and speed.
    - Combat: Standard melee (`Attack: 8`, `Defense: 3`).
  - **Knight (騎士)**:
    - Base Combat Stats: `Attack: 18`, `Defense: 8`, `Max Health: 140`.
    - Base Hunting Accuracy: High critical hit chance on fauna.
    - Work: Standard gather duration (`1.0x`).
  - **Mage (魔法師)**:
    - Base Combat Stats: `Attack: 22` (Ranged magical strike, range: 3 tiles), `Defense: 2`, `Max Health: 70`.
    - Magic Spell bonus damage: `+25%` spell potency.
- [ ] **Visual Distinction**:
  - Color-code or badge NPC sprites according to role:
    - Farmer: Greenish / Golden badge
    - Knight: Silver / Steel blue badge
    - Mage: Violet / Purple badge
  - Display Role in hover tooltip: `NPC #0 [Farmer] (HP: 100/100, Hunger: 80/100)`.

### 1.2 Character Population Growth (+1 NPC Every 3 Rounds)
- [ ] **Reinforcement Trigger**:
  - At the end of every 3rd round (Round 3, 6, 9, etc.), generate +1 new NPC in the colony.
- [ ] **Spawn Location**:
  - Spawn at the starting colony center tile or at an existing `House` structure.
- [ ] **Population Limits**:
  - Base population cap of 3. Building `House` structures increases the cap by +1 per house.

---

## Phase 2: Post-Round Skill Upgrade & Progression (技能體系與結算)

### 2.1 Wave Settlement & Skill Point Rewards
- [ ] **End-of-Night Wave Evaluation**:
  - **Full Clear (怪物全部打完)**: If all spawned monsters are eliminated before Day starts, grant **2 Skill Upgrade Points** (Bonus reward).
  - **Partial Clear (有剩餘怪物沒打完)**: If the night timer expires with remaining monsters, grant **1 Skill Upgrade Point** per `N` monsters defeated.
- [ ] **Round Settlement Transition**:
  - Pause the simulation at the start of each new Day if skill points are available, prompting the player to spend points.

### 2.2 Skill Upgrade UI & Tree
- [ ] **Skill Upgrade Screen**:
  - An interactive modal overlay presenting the 6 core skills:
    1. **Gather Speed (採集速度)**: Decreases work time for Gather & Farmland harvest by 10% per level.
    2. **Hunting Accuracy (打獵準度)**: Increases hunting damage and yield from wild animals.
    3. **Taming Ability (馴服能力)**: Decreases taming time and increases taming success rate.
    4. **Defense Ability (防禦能力)**: Grants +2 Defense and +10 Max Health per level to characters.
    5. **Magic Attack (魔法攻擊)**: Increases base spell damage by +15% per level.
    6. **AoE Attack (群體攻擊)**: Expands radius and splash damage of AoE spells.
- [ ] **State Persistence**:
  - Store skill levels globally or per-character.

---

## Phase 3: Active Magic Spells (魔法系統)

### 3.1 Combat Spells
- [ ] **Fire (火焰)**:
  - *Effect*: Deals high immediate damage to targeted monster plus burn damage-over-time (DoT) for 3 seconds.
  - *Cooldown*: 15 seconds.
  - *Hotkey / Trigger*: `[Q]` key or UI button.
- [ ] **Lightning (閃電)**:
  - *Effect*: Fast high-voltage electrical strike dealing immense single-target burst damage.
  - *Cooldown*: 20 seconds.
  - *Hotkey / Trigger*: `[W]` key or UI button.
- [ ] **Freeze (凍結)**:
  - *Effect*: Freezes/slows all monsters in a 3x3 tile radius for 4 seconds, stopping their advance.
  - *Cooldown*: 25 seconds.
  - *Hotkey / Trigger*: `[E]` key or UI button.

### 3.2 Targeting & Visual FX
- [ ] **Auto / Manual Target**:
  - Auto-casts on the nearest monster threat to territory or targeted on mouse cursor.
- [ ] **Visual Effects**:
  - Render colorful particle/flash overlays for Fire (Orange/Red), Lightning (Yellow/White), and Freeze (Cyan/Light Blue).

---

## Phase 4: Additional Buildings & Expanded Resources (建築與材料原料)

### 4.1 New Buildings
- [ ] **House (房子)**:
  - *Cost*: 4 Wood + 2 Bricks (or crops in early game).
  - *Function*: Increases max colony population cap (+1 NPC slot).
  - *Work Duration*: 4.0 seconds.
- [ ] **Farmland (農地)**:
  - *Cost*: 2 Wood + 1 Water/Crop.
  - *Function*: A designated farming tile where crops (Vegetables, Tomatoes) can be repeatedly planted, grown, and harvested by Farmers.
  - *Work Duration*: 3.0 seconds.

### 4.2 Expanded Material Taxonomy
- [ ] **Construction Materials**:
  - `wood` (木頭) — harvested from forest/tree tiles.
  - `marble` (大理石) — quarried from marble deposits.
  - `bricks` (磚頭) — crafted or mined from clay/stone deposits.
- [ ] **Magic Materials**:
  - `berries` (莓果) — gathered from berry bushes, used for magic catalysts.
  - `raw_stone` (原石) — mined crystals, used to power spells.
- [ ] **Recipe Updates**:
  - Update `WALL_COST` (e.g. `{"wood": 2}` or `{"bricks": 2}`).
  - Update `TOWER_COST` (e.g. `{"wood": 3, "marble": 2}`).

---

## Phase 5: Wildlife, Hunting & Animal Taming (生態、打獵與馴服)

### 5.1 Wildlife / Animal Fauna
- [ ] **Neutral Animals on Map**:
  - Spawn wild animals in unrevealed/unclaimed frontier areas:
    - Small Game: **Flying Squirrel (飛鼠)**, **Fish (魚)**.
    - Large Game: **Wild Boar (山豬)**, **Horse (馬)**.
    - Dangerous Beasts: **Wolf (狼)**, **Bear (熊)**.
- [ ] **Animal AI**:
  - Passive wandering in nature; dangerous beasts retaliate if attacked.

### 5.2 Hunting Task (`Hunt`)
- [ ] **`Hunt` Task Type**:
  - Player designates wild animals for hunting.
  - Knights / NPCs track down the animal and engage in hunting combat.

### 5.3 Post-Hunt Decision: Food vs. Taming
- [ ] **Process for Food (食物)**:
  - Harvest meat, increasing colony food inventory.
- [ ] **Tame Task (`Tame`)**:
  - Farmer captures and tames the animal.
  - Place animal in an **Animal Pen (畜欄)** to passively generate food (milk/eggs/meat) or utility (horses increase travel speed).

---

## Phase 6: Food Spoilage System (食物腐敗)

### 6.1 Spoilage Decay
- [ ] **Food Freshness Tracker**:
  - Stored food items have a shelf-life timer (e.g. 3-5 game days).
  - Cooked / processed foods spoil slower than raw mushrooms or wild meat.
- [ ] **Spoilage Effects**:
  - Spoiled food is automatically discarded from inventory with a HUD notification alert.

---

## Phase 7: Specialized Monster Types (多種怪物)

### 7.1 Enemy Variety
- [ ] **Werewolf (狼人)**:
  - Fast movement speed (`80 px/s`), medium health (`50 HP`), fast melee claw attacks (`14 Attack`).
- [ ] **Vampire (吸血鬼)**:
  - High speed, life-stealing attack (recovers health when dealing damage), avoids direct wall collisions.
- [ ] **Zombie (殭屍)**:
  - Slow movement speed (`40 px/s`), high health pool (`90 HP`), high building siege damage.

---

## Phase 8: Checkpoint Save / Load Persistence (存檔讀檔)

### 8.1 Serialization & State Checkpointing
- [ ] **Save Snapshot at Phase Boundaries**:
  - Save full state (Grid claim/fog/resources, NPCs positions/health/hunger/priority/roles, Inventory, Buildings, Nests, Wave count, Skills) to JSON/binary checkpoint.
- [ ] **Load on Startup**:
  - Automatically load the latest checkpoint on game launch, or allow fresh game start.
