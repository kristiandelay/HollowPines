# HOLLOW PINES

**Game Design Document — Version 1.0 — 08 October 2026**

Survive together. Die alone.

![Third-person forest survival concept showing a survivor approaching teammates reviving a player beside a cave and shallow river.](hollow_pines_assets/00_cover_crop.png)

*Atmosphere study: a rescue at the river, with danger above and below ground. Cropped from A01.*

Modern-day, third-person multiplayer survival horror. Up to eight squads of four enter a storm-bound forest. Cooperation is a choice. Getting everyone out is the challenge.

| FORMAT | DESIGN TARGET | ENGINE TARGET |
| --- | --- | --- |
| Session-based survival | 32 players / 8 squads / 4 per squad | Unreal Engine 5.8.3 |

Version 1.0  |  08 October 2026  |  Design baseline and prototype handoff

> HOLLOW PINES is the canonical title. Earlier artwork retains ROOTBOUND or THE HOLLOW PINES branding and exploratory interface text. The written specification in this document overrides those labels. These images are concept mockups, not engine captures or completed game assets.


---

## Document control & reading guide

*START HERE*

This document combines the agreed game direction with proposed rules needed to build and test it. It is a design baseline, not a claim that the game, networking, artwork, or performance targets have already been implemented.

| STATUS | MEANING |
| --- | --- |
| Confirmed | Hollow Pines; modern day; third-person; up to 8 squads of 4; optional cooperation between squads; lush redwood-like forest, shallow rivers and caves; enemies can down, capture, bait or kill; player revives; a four-seat stormy campfire lobby. |
| Proposed baseline | PvE-first public mode, no player damage, 45–60-minute sessions, shared escape opportunities, two prototype enemies, gear-based roles and no persistent base building. These are recommendations, not additional user approvals. |
| Tuning target | All speeds, dimensions, timers, resource counts, AI budgets and performance thresholds are initial test values, not final balance or measured results. |
| Reference only | AI-generated visual studies. Branding, captions, anatomy, duplicate side views and character numbering must be reviewed before production. |

### Contents

- [01 / Game vision & boundaries](#01--game-vision--boundaries) — PDF/Word pp. 3
- [02 / Session structure & escape](#02--session-structure--escape) — PDF/Word pp. 4
- [03 / Squads, alliances & social rules](#03--squads-alliances--social-rules) — PDF/Word pp. 5
- [04 / Survival & moment-to-moment play](#04--survival--moment-to-moment-play) — PDF/Word pp. 6
- [05 / Injury, rescue & capture](#05--injury-rescue--capture) — PDF/Word pp. 7–8
- [06 / World layout & traversal](#06--world-layout--traversal) — PDF/Word pp. 9–10
- [07 / Enemy ecology](#07--enemy-ecology) — PDF/Word pp. 11–14
- [08 / Modern survival equipment](#08--modern-survival-equipment) — PDF/Word pp. 15–17
- [09 / In-game HUD](#09--in-game-hud) — PDF/Word pp. 18–19
- [10 / Main menu & campfire lobby](#10--main-menu--campfire-lobby) — PDF/Word pp. 20–21
- [11 / Playable survivors](#11--playable-survivors) — PDF/Word pp. 22–29
- [12 / Animation, sound & atmosphere](#12--animation-sound--atmosphere) — PDF/Word pp. 30
- [13 / Unreal Engine 5.8.3 plan](#13--unreal-engine-583-plan) — PDF/Word pp. 31
- [14 / Multiplayer & data architecture](#14--multiplayer--data-architecture) — PDF/Word pp. 32–33
- [15 / Prototype milestones & tests](#15--prototype-milestones--tests) — PDF/Word pp. 34
- [16 / Scope, backlog & open decisions](#16--scope-backlog--open-decisions) — PDF/Word pp. 35
- [17 / Technical references](#17--technical-references) — PDF/Word pp. 36–37

Read the vision and rescue rules before building assets. Programmers should also read the multiplayer and test sections. Artists should use the embedded plates together with the corrections and asset acceptance rules; image labels alone are not production specifications.


---

## 01 / Game vision & boundaries

*THE PLAYER PROMISE*

> You hear someone calling for help from the trees. It might be another squad. It might be your missing friend. It might be something that has learned how people find each other.

### High concept

Hollow Pines is a modern-day survival-horror game set during one violent night in a remote forest reserve. Roads are blocked, communications are unreliable and something moves between the enormous trunks. Squads navigate by light, landmarks and one another, searching for an escape while predators turn separation into opportunity.

The central question is not “Who wins the firefight?” It is “How much will we risk to bring someone home?” Up to 32 people inhabit the same world, but the player’s emotional anchor remains a squad of four. Other squads can become rescuers, trading partners, distractions or strangers who refuse to stop.

### Four design pillars

| PILLAR | DESIGN CONSEQUENCE |
| --- | --- |
| People are the lifeline | Revive, drag, carry, share supplies and coordinate distractions. Cooperation is useful without a mandatory proximity buff. |
| The forest hides intent | Large silhouettes, occluded sightlines, shifting rain and deliberate audio cues create uncertainty. Encounters have learnable rules. |
| Tools, not superpowers | Modern camping, rescue and navigation equipment. Characters are ordinary adults; no magical classes or futuristic scanners. |
| Fear comes from decisions | Taking a noisy shortcut, answering a distress call or lighting a fire changes risk. Threats cannot simply teleport onto isolated players. |

### What this version is not

Not a battle royale, mandatory betrayal game, military shooter, endless crafting sandbox or persistent settlement simulator. The early screenshot’s “mist shrinks” timer is not a supported rule. Several squads—or everyone—can survive the same session.

### Tone and audience

Grounded contemporary realism with supernatural ecology. Intended for an adult horror audience; final age classification is not yet assessed. Present peril, disturbing creatures, injury and aftermath without making extended cruelty the core interaction. Blood intensity, flashes and camera effects are configurable.


---

## 02 / Session structure & escape

*SURVIVE THE NIGHT*

Proposed public format: 45–60 minutes, with a 20–30-minute prototype scenario. Squads arrive at separated authored spawn sites inside the same reserve. The map layout is hand-authored; supply locations, blocked routes, weather beats and objective combinations vary through a validated session seed.

| PHASE | PLAYER ACTIVITY | PRESSURE |
| --- | --- | --- |
| Arrival / 0–5 min | Orient, collect a local map and check starting supplies. Find the nearest landmark. | Predator signs establish danger before the first committed attack. |
| Search / 5–20 min | Locate two useful sites: communications and an escape route. Meet or avoid other squads. | Travel consumes batteries and stamina; storms interrupt clear sightlines. |
| Commit / 20–40 min | Restore a relay, recover a key component and open a route. Rescue missing players. | Generators, calls and repeated travel attract investigation. |
| Escape / final 10–15 min | Move survivors to an activated road exit, service tunnel or rescue corridor. | A clearly announced local escape window creates urgency without a shrinking map. |

### Objective model

Use two linked tasks per escape route, with multiple equivalent component spawn locations. Example: recover a replacement relay module at the ranger depot, then power the Blackwater radio station to request a road convoy. Restoring a public facility helps every squad; no single player permanently owns the objective.

Critical items have protected quest storage, public recovery rules and a fallback spawn after verified loss. A disconnect or a player refusing to hand over one object cannot make the whole session unwinnable. Optional supplies remain scarce and tradable.

### Success and failure

A survivor escapes when the server confirms route activation, physical presence in the departure volume and completion of the departure interaction. Routes support repeated departures or sufficient total capacity for all remaining survivors. Arrival order does not create a last-team-standing contest.

A squad is fully successful when all four original members escape, partially successful when some escape, and lost when none remain recoverable. Individual survivors can choose to wait for a rescue. The session ends when every player is escaped, dead or the announced final rescue window has closed.

> No instant global knowledge: the field HUD does not reveal exactly how many strangers are alive. Full squad and survival statistics belong in the post-session report.


---

## 03 / Squads, alliances & social rules

*FOUR IS HOME; THIRTY-TWO IS THE WORLD*

A party contains 1–4 players; public fill can complete the squad. A match contains up to 8 independent squads. Smaller private tests are valid, but the full design must be tested with 32 connected players rather than simulated only as four-player co-op.

### Cross-squad cooperation

Any survivor may revive, free or help carry any other survivor. Two squad leaders can exchange a temporary alliance invitation that enables a shared radio channel and optional shared map pins. It does not merge parties, create extra lobby seats, reveal private inventories or grant remote tracking without consent.

Alliances may be dissolved at any time. A local notification makes the change clear; already supplied rescue information does not vanish mid-interaction. Manual proximity cooperation also works without an alliance. Players who avoid other squads still have viable objective routes.

| SYSTEM | BASELINE RULE |
| --- | --- |
| Player damage | Off in the initial public mode. No executions, harmful friendly melee or PvP loot farming. Optional PvPvE is a separate future design decision. |
| Inventory and trade | Explicit offer / accept transfer. Teammates cannot open living players’ inventories or forcibly take equipped tools. |
| Communication | Squad radio, opt-in alliance radio and local proximity voice. Independent mute, block, report and push-to-talk controls. |
| Physical cooperation | Prompt-based drag and carry, with a release control for the carried player. Use soft teammate collision to limit doorway blocking. |
| Player information | Always show own-squad status. Strangers gain a local nameplate only when seen or deliberately contacted. No global enemy or stranger radar. |

### Avoid the 32-person steamroller

Large groups generate more footsteps, light, supply demand and congestion, but the game must not secretly punish friendship with arbitrary damage multipliers. Useful sites are distributed, entrances have limited comfortable capacity, and objective work benefits from smaller coordinated task groups. AI reacts to evidence such as noise and visible lights, not an invisible “too many friends” debuff.

### Anti-grief provisions

Limit repeated radio requests and unwanted alliance prompts. Protect quest progression from item deletion. Let victims cancel being carried and report intentional luring. Test fire placement, doors and ropes for trapping exploits. No vote can delete another player’s items or kill their character.


---

## 04 / Survival & moment-to-moment play

*MOVE, LISTEN, PREPARE*

The core loop is observe → choose a route → manage light and exertion → scavenge or complete work → respond to a threat → recover and regroup. Survival pressure should produce decisions every few minutes, not constant maintenance bars.

| RESOURCE | PROPOSED FUNCTION | READABILITY |
| --- | --- | --- |
| Health / 100 | Injury reduces the ability to absorb another attack. At zero, enter Downed unless a clearly telegraphed lethal situation applies. | Health bar and distinct state icon; injury animations support, not replace, the HUD. |
| Stamina / 100 | Spent on sprinting, vaulting, heavy swings and carrying. Regenerates after a short rest. | Bar appears while spending or below full; tired breathing can be reduced in settings. |
| Light and batteries | Finite charge encourages choosing broad light for work or narrow light for travel. | Current device charge; warning before failure; a spare can be checked without opening the full inventory. |
| Wetness and exposure | Prolonged wet conditions slow stamina recovery. Shelter or warmth reverses the penalty. | One three-stage exposure icon rather than several competing meters. |
| Food and water | Limited-use recovery supplies. No separate hunger/thirst death clocks in the first version. | Effects stated as game mechanics, not real medical or survival advice. |

### Movement and camera

Over-the-shoulder third-person with shoulder switching, crouch, vault, wade, contextual climb, drag and carry. Prototype speeds: walk 2.0 m/s, jog 3.5 m/s, sprint 5.5 m/s and carry 1.6 m/s. These values require camera, animation and encounter testing together.

Use a collision-aware spring arm, local foliage fading and an adjustable field of view. Do not reveal the world through walls when the camera clips into a cave. Interaction targeting uses the character’s valid reach, not the camera’s remote position.

### Combat is an escape tool

A shove, hatchet or improvised obstacle creates space. Telegraph heavy attacks, charge stamina and prevent endless stagger loops. A flare can redirect one creature but expose the group to another. Starting kits have no firearms; scarce civilian firearms are a later test only if they preserve fear and do not displace rescue play.

### Shelter and crafting

Temporary rest sites support a fire, bandaging and equipment checks. They are not invulnerable safe zones. First-version crafting is limited to small combinations such as repaired straps or simple noise alarms; no resource-grinding base construction or world-wide tree felling.


---

## 05 / Injury, rescue & capture

*KEEP PLAYERS INVOLVED*

Downing, being carried and captivity are recoverable states. Death is a clear terminal event, not an ambiguous missing icon. All authoritative transitions and timers are owned by the server.

| STATE | PLAYER AGENCY | EXIT |
| --- | --- | --- |
| Active / injured | Move, use tools and help others; visible injury does not randomly remove controls. | Treatment, Downed, Escaped or a telegraphed lethal hazard. |
| Downed | Crawl slowly, call for help or stay quiet; the player can see their rescue timer. | Revive, voluntary transport, predator capture or death at expiry. |
| Dragged / carried | Remain aware and able to communicate. A release input prevents kidnapping by teammates. | Set down at a valid location; original downed timer continues. |
| Captured / bait | Look around, choose a distress call, work toward a limited self-escape or warn rescuers. | Freeing interaction, self-escape opportunity or capture deadline. |
| Dead | Choose squad-only spectator view or return to lobby. No map-wide free camera. | Next session; no paid or instant respawn. |
| Escaped | Debrief, spectate own squad or return to camp while teammates continue. | Next session; escape does not end other squads’ runs. |

### Universal rescue actions

Every character can perform a baseline revive. A helper starts an 8-second hold interaction from a valid position; completion returns 25 health. A consumed med-kit charge reduces the interaction to 6 seconds. These are game balance values, not medical procedure.

A second helper can watch, distract or carry gear, but does not stack unlimited revive speed. Moving away, taking a major hit or cancellation stops progress. Resource consumption occurs on successful completion, and duplicate requests cannot spend two charges.

### Bleeding and transport

Initial downed window: 90 seconds. One stabilization action may add 60 seconds, capped at 150 seconds from that downing event. Dragging and carrying do not repeatedly pause or reset the deadline. Display the action and expected benefit before the helper commits.

> Lethal outcomes must be readable. Avoid surprise one-hit executions during ordinary travel, invisible water kills or a creature striking through an unbroken wall. A rescue can fail, but players should understand why.


---

## 05 / Bait encounters & rescue tuning

*THE THREAT KNOWS YOU WILL RETURN*

### Capture rules

The Forest Stalker can seize a downed survivor after a visible approach and grab wind-up. A teammate can interrupt the grab with a correctly timed stagger or distraction. Captured players are carried to nearby authored root bindings or a sheltered bait site, never across the entire map.

On the first successful capture of a downed episode, replace bleeding with a 180-second rescue clock starting at the grab. Travel, rebinding and animation changes do not reset it. Freeing the target returns them to Downed with a 30-second rescue period. A player cannot be captured again in that episode until revived. All timings are prototype targets.

Bindings are environment props around clothing and equipment; avoid requiring graphic torture imagery. The captive can rotate the camera, choose whether to call out and attempt one slow, clearly signposted escape interaction when the creature leaves. Accessibility alternatives replace rapid button mashing.

### The bait loop

An enemy may deliberately stop attacking a downed player, retreat behind cover and wait for a rescuer. The scene must include fair evidence: fresh drag marks, unusually deliberate silence, broken branches or a partial silhouette. Different predators have distinct tells; “every injured person is a trap” would make helping irrational.

| EXAMPLE BEAT | EXPECTED PLAYER DECISION |
| --- | --- |
| A cry comes from a root hollow beside a ford. | Identify the voice, check the approach and decide whether another squad is worth the risk. |
| A moving branch silhouette crosses the tree line. | One player watches high ground; another checks the captive. |
| The predator follows a thrown noise lure. | Choose between freeing the survivor immediately or waiting for a longer opening. |
| The captive is freed but cannot stand. | One player revives or carries while others light the exit and control pursuit. |
| A nearby squad offers a med kit. | Accept cooperation without requiring a permanent alliance or giving away inventory access. |

### Pacing limits

Prototype rule: one active capture per squad at a time. Do not start a second bait setup inside the same rescue space. After a successful rescue, give the encounter director a short recovery cooldown; nearby existing threats remain visible and obey their own rules. Log capture time, agency time, rescue attempts and abandonment reasons.


---

## 06 / World layout & traversal

*BLACKWATER REACH*

The first location is a fictional forest reserve called Blackwater Reach within Hollow Pines. It combines enormous redwood-like trunks, thick fern beds, mossy rock, shallow braided rivers and connected caves. Redwood scale is the visual reference, not a claim that every plant or geological feature reproduces one real reserve.

### World structure

Use an authored surface network with three travel loops: a readable river route, an obscured upper-forest route and a short but dangerous cave route. Routes reconnect often enough to allow rescues without turning every journey into a long backtrack. Large landmarks provide direction when electronic navigation is unreliable.

| SPACE | FUNCTION | HORROR OPPORTUNITY |
| --- | --- | --- |
| Giant-trunk groves | Navigation landmarks and moments of concealment. | A silhouette can be mistaken for a trunk until it moves. |
| Shallow river and fords | Readable travel corridor with several crossings. | Splash noise and exposed crossing positions reveal movement. |
| Ravines and fallen trees | Choices between safe detours and faster traversal. | A group can lose sight of a slower carrier without an artificial teleport. |
| Root caves and sinkholes | Surface-to-cave transitions and rescue sites. | Light from outside stops abruptly; sound continues beyond view. |
| Service buildings | Concentrated supplies and objective work. | Power restoration creates noise, shadows and an obvious destination. |
| Underground chambers | Alternative routes and predator territory. | A high ceiling lets something move above the flashlight beam. |

### Traversal requirements

Prototype main trails: approximately 3–5 m of usable width. Main cave passages: roughly 3 m wide and 3–4 m high, widening to 8–12 m at encounter chambers. A carried body and camera must fit through every mandatory escape route. These are blockout targets to validate with the actual character capsule.

Shallow crossings begin at 0.15–0.6 m depth; deep-water swimming and diving are out of scope for the first test. Water speed, splashes and exposure are explicit gameplay data, not inferred from visual ripples. Caves include at least two exits per major encounter loop.

> Fear should not come from unreadable geometry. Reserve narrow squeezes for optional routes and authored transitions; never make rescuers discover that a mandatory doorway cannot pass a downed teammate.


---

## 06 / First playable test map

*BUILD A SMALL, COMPLETE NIGHT*

Build one approximately 600 × 600 m test area for two squads, not the entire release forest. Include a continuous surface-to-cave loop, one ford and one extraction route. Increase playable area only after travel time, encounter cadence and cross-squad contact are measured.

| ZONE | CONTENT | TEST PURPOSE |
| --- | --- | --- |
| 1 / North trailhead | Squad A arrival, map board, small shelter and starter supplies. | Orientation without a tutorial pop-up overload. |
| 2 / South service path | Squad B arrival, damaged vehicle and an alternate map fragment. | Independent start that still leads toward a shared goal. |
| 3 / Blackwater ford | Shallow river, fallen log, visible ridge and two approaches. | First contact, wading noise and a carried-player crossing. |
| 4 / Root hollow | Root binding prop, watch position and an escape path. | Forest Stalker downing, bait and rescue. |
| 5 / Limestone loop | Entrance, bend, 10 m chamber, short upper ledge and exit. | Quadruped pursuit, flashlight readability and streaming transition. |
| 6 / Relay and road gate | Replaceable relay module, power switch and departure corridor. | Shared objective completion followed by multi-squad extraction. |

### Route sequence

Trailhead A → ford → root hollow → relay. Service path B → cave entrance → cave chamber → relay. The ford and cave loop reconnect, allowing either squad to reach the same rescue site from a different direction. Place objective components in more than one valid container so one looter cannot halt the session.

### Scripted first test

Players establish radio contact, investigate the ford, witness a downing and attempt a rescue, meet the other squad, recover the relay component, then choose whether to use the cave shortcut or escort a weakened survivor along the river. The final gate stays usable for both squads after the first departure.

### What to measure

Time to understand the goal; frequency of wrong turns; successful and abandoned rescues; percentage of cross-squad meetings that produce help; light usage; camera obstructions; extraction failures; and time spent with no meaningful control. Capture causes and player feedback should be reviewed together rather than treating survival rate alone as success.

### Scaling plan

Run the same rescue test with 4, 8, 16 and 32 connected clients. The later full forest can begin around 1.5 × 1.5 km as a planning hypothesis, but map size is not committed until contact frequency and server cost justify it. More acreage is not a substitute for interesting routes.


---

## 07 / Enemy ecology

*TWO CORE THREATS; ONE RESERVE CONCEPT*

Enemies are designed around different rescue problems rather than increasing health bars. The prototype uses the Forest Stalker and the four-legged Cave Stalker. The earlier biped Cave Dweller sheet remains a reserve concept so it does not silently add a third rig and AI package to the first milestone.

| CREATURE | PRIMARY BEHAVIOR | READABLE RESPONSE |
| --- | --- | --- |
| Forest Stalker / core | Camouflages among trunks, follows exposed groups, downs and captures a survivor, then uses the survivor as bait. | Look for branch movement and amber eye points. Break line of sight, draw it away and rescue from another approach. |
| Cave Stalker / core | Four-legged ambush predator. Responds to movement and sharp sound, pounces and drags downed targets toward a den. | Watch scrape trails and low silhouettes. Interrupt a wind-up or use a timed light/noise distraction, then change route. |
| Cave Dweller / reserve | Tall, long-armed climber for vertical cave routes; listens from ledges and threatens blocked paths. | Ceiling movement, stone clicks and visible grip points. Not required for the first playable. |

### Shared AI contract

Use the states Idle → Observe → Investigate → Stalk → Commit → Recover → Disengage. Only an enemy with the capture capability enters Seize → Transport → Bait. Attack decisions depend on valid perception, reach and navigation; animations alone do not decide damage.

Sight considers character visibility, illumination state, distance and occlusion. Hearing consumes explicit gameplay noise events such as running, splashing, tools and generators. Do not record or imitate live player voices. Authored distress sounds can suggest mimicry while remaining distinguishable from actual squad radio.

### Fair threat placement

Spawn or activate enemies only at valid authored approach points outside all nearby players’ view, with sufficient approach time. No spawning inside occupied shelter, behind a closed door without an entry route, or immediately on the back of a camera. When streaming unloads visual cells, authoritative enemy and captive state persists.

### Combat boundaries

The Forest Stalker is repelled, not farmed, in the prototype. The Cave Stalker may be defeated with coordinated tools at substantial cost, but does not drop an equipment jackpot. Resist repeated stun loops through visible recovery behavior rather than unexplained invulnerability.

> Do not infer lore, abilities or physical measurements from decorative concept-sheet slogans. The tree creature is roughly 5–6 m tall as an art target—not taller than mature redwoods.


---

## 07 / Forest Stalker

*ENEMY REFERENCE / CORE*

![Forest Stalker: full-body hero, front, back and side studies. Original ROOTBOUND branding is superseded by HOLLOW PINES. [Concept art; not a production turnaround.]](hollow_pines_assets/03_forest_stalker_reference.png)

*A03 | Forest Stalker: full-body hero, front, back and side studies. Original ROOTBOUND branding is superseded by HOLLOW PINES. [Concept art; not a production turnaround.]*

### Silhouette and materials

A 5–6 m upright predator made visually from wet bark plates, root-like fibers and moss. Long arms and an irregular crown let it read as a tree before movement exposes it. Sparse amber eye points should remain unsettling, not become an always-visible navigation marker.

### Gameplay brief

Territory: surface groves and wide cave mouths. Signature encounter: down one survivor, bind them near a root hollow and watch the rescue approach. Counterplay requires a readable distraction window and a second route, not sustained weapon damage.

Animation priorities: stillness with tiny settling motion; trunk-like lean; deliberate step; long reach; interrupted grab; controlled transport; release; retreat. Model the bindings as separate environment assets. Hands, branch silhouette and root feet must remain readable across distance tiers.


---

## 07 / Cave Dweller

*ENEMY REFERENCE / RESERVE EXPLORATION*

![Earlier biped Cave Dweller exploration. Retain as a reserve visual direction; the first playable uses the four-legged cave predator on the following page.](hollow_pines_assets/04_cave_dweller_exploration.png)

*A04 | Earlier biped Cave Dweller exploration. Retain as a reserve visual direction; the first playable uses the four-legged cave predator on the following page.*

### Use of this reference

The long arms, low-set head, pale mottled hide and bony back can inform subterranean material language. This concept is not permission to replace the quadruped with a humanoid enemy or expand the initial AI scope.

### Potential later role

A ledge-dwelling listener that forces the group to check high ground and coordinate quiet movement. Its design would require its own climbing routes, animation set, camera tests and counterplay validation before entering production.

Art cleanup: maintain skin continuity rather than relying on graphic exposed anatomy. Verify finger count, mouth structure, front/back correspondence and true opposing side views. Do not reuse decorative dimensions or misspelled labels as asset requirements.


---

## 07 / Four-legged Cave Stalker

*ENEMY REFERENCE / CORE*

![Quadruped Cave Stalker: the primary cave predator. Hero and orthographic studies remain separated. HOLLOW PINES replaces the legacy ROOTBOUND title.](hollow_pines_assets/05_quadruped_cave_stalker_reference.png)

*A05 | Quadruped Cave Stalker: the primary cave predator. Hero and orthographic studies remain separated. HOLLOW PINES replaces the legacy ROOTBOUND title.*

### Silhouette and locomotion

Low, powerful quadruped with enlarged forelimbs, a compact rear drive and a jagged back silhouette. Approximate art target: 2.5 m long. All four limbs must support believable weight and turning; the final rig must not be a humanoid animation bent onto its hands.

### Gameplay brief

Use cave bends, shallow rock shelves and dark river-edge openings. Telegraph a pounce with a lowered body and scrape sound. It can knock a survivor down, drag the target a short distance and guard the approach. A committed pounce has recovery time that teammates can use.

Required animations: slow stalk, trot, burst, tight turn, slope adjustment, pounce, hit reaction, drag, interrupted drag, retreat and death. Use authored traversal links for ledges; free climbing on any surface is out of scope. Test all attacks with two survivors and a carried body in the same chamber.


---

## 08 / Modern survival equipment

*GEAR REFERENCE*

![Modern camping and rescue gear study: lights, radio, navigation, medical supplies and hand tools. Treat product-like claims and legacy slogans as exploratory artwork, not final UI copy.](hollow_pines_assets/06_survival_gear_reference.png)

*A06 | Modern camping and rescue gear study: lights, radio, navigation, medical supplies and hand tools. Treat product-like claims and legacy slogans as exploratory artwork, not final UI copy.*

### Equipment language

Weathered, practical equipment that a hiker, volunteer rescuer or city visitor could plausibly carry. Rubber grips, woven straps, scratched metal, damp fabric and readable controls. Avoid science-fiction scanners, military armor and oversized tactical loadouts.

### Inventory philosophy

Each survivor has one hand-tool slot, one light slot, four quick-access slots and a small backpack inventory. A bulky quest item occupies visible carrying space but cannot permanently block essential rescue actions. Supplies are found during the session; lobby loadouts select equivalent starter kits, not accumulated power.

All equipment needs a pickup view, held view and world-drop mesh. Batteries, charges, noise and usable conditions are data-driven. Descriptions communicate gameplay benefits without implying real-world medical or water-purification guarantees.


---

## 08 / Gear functions & limits

*ITEMS MUST CHANGE A DECISION*

| ITEM | GAMEPLAY JOB | COST OR LIMIT |
| --- | --- | --- |
| Flashlight | Aimable narrow/wide beam; inspect routes and signal locally. | Finite charge; visible to threats and strangers. |
| Headlamp | Hands-free illumination while reviving or carrying. | Lower effective reach; player direction exposes the group. |
| Handheld radio | Squad and opt-in alliance communication. | Cave attenuation is signposted; no unexplained arbitrary failure. |
| Compass + paper map | Reliable direction and annotated landmarks. | No automatic cave layout or moving-player radar. |
| GPS / offline device | Surface waypoints and previously shared locations. | Underground position is unavailable or explicitly last-known. |
| Med kit | Faster revive and a defined health-restoration use. | Limited charges; never required for the basic revive. |
| Bandage | One-time stabilization of a downed deadline. | Cannot repeatedly extend the same downing event. |
| Water / food | Recover a portion of stamina reserve or exposure penalty. | Limited consumables; not required every few minutes. |
| Road flare | Illumination, signaling and creature-specific distraction. | Bright, finite duration and not a universal repellent. |
| Noise lure / alarm | Thrown noise or a local trip-warning device. | Limited uses; cannot detect enemies through arbitrary terrain. |
| Rope kit | Authored lowering or haul interaction at marked anchors. | No free-form grappling hook, arbitrary tether physics or climbing anywhere. |
| Hatchet / multitool | Utility interactions and desperate close defense. | Stamina cost, attack recovery and noisy use. |

### Starter kit balance

Proposed universal starter gear: small flashlight, radio, map/compass and one bandage. Choose one equivalent kit focus: extra light charge, one med-kit charge, one utility tool or two signaling consumables. Equipment roles are not locked to appearance or character ethnicity.

### Scavenging and item safety

Use a mixture of shared public caches and individual container draws for basic necessities. Never duplicate unique objective rewards. Inventory capacity, swaps and transfers are server-validated. Dropped quest objects return to a reachable recovery point if they fall outside the world or become trapped in non-navigable geometry.

First test: approximately 8–12 meaningful loot sites across the small map. Tune from actual shortages and route decisions. Keep the number of item types small enough that a new player can understand every pickup without a long crafting tree.


---

## 08 / Survival hatchet

*PROP REFERENCE / UTILITY AND DEFENSE*

![Hatchet study with separated hero and orthographic views, material details and a suggested 310 mm scale. Legacy branding is not part of the final prop texture.](hollow_pines_assets/07_survival_hatchet_reference.png)

*A07 | Hatchet study with separated hero and orthographic views, material details and a suggested 310 mm scale. Legacy branding is not part of the final prop texture.*

### Production target

A compact one-handed camping hatchet with a worn wooden handle and steel head. The pictured 310 mm overall length is a starting reference; validate grip, reach and belt storage against the survivor rig before locking dimensions.

### Required game representations

World pickup, equipped hand pose, belt-stowed mesh and inventory icon. Avoid embedding decorative ROOTBOUND marks in the production texture. Supply separate material controls for clean, wet, dirty and damaged states.

Actions: equip, stow, light swing, committed heavy swing, shove transition, valid utility strike, miss, hit and exhausted recovery. Utility chopping is limited to authored obstacles and resource props; this does not imply destructible redwoods or a full forestry simulation. It is a game asset brief, not a tool-manufacturing specification.


---

## 09 / In-game HUD

*GAMEPLAY SCREEN REFERENCE*

![Over-the-shoulder rescue composition: a shallow river, a downed teammate, a cave predator and a distant forest threat. Original title, live survivor count and shrinking-mist timer are superseded.](hollow_pines_assets/01_gameplay_reference.png)

*A01 | Over-the-shoulder rescue composition: a shallow river, a downed teammate, a cave predator and a distant forest threat. Original title, live survivor count and shrinking-mist timer are superseded.*

### Approved HUD placement

| REGION | CONTENT |
| --- | --- |
| Upper left | Four own-squad rows: name, portrait, health/state and radio activity. Include the local player only once. |
| Top center | Compact compass with player-placed pins. No enemy radar and no always-on minimap. |
| Upper right | One current objective and, only when relevant, an escape-window timer. |
| Lower left | Health, contextual stamina and a compact exposure indicator. |
| Lower right | Four quick slots; active tool, charge or quantity; device battery when relevant. |
| Center / world | Small interaction prompt and progress; local nameplates, rescue state and shared markers only when allowed. |

> Keep the scene—not the interface—as the visual focus. Do not ship the large in-game title logo, “8 teams / 32 survivors” live counter or “mist shrinks” mechanic shown in this early image.


---

## 09 / HUD states & accessibility

*INFORMATION WITHOUT BREAKING FEAR*

### Information hierarchy

Critical survival state comes first, then immediate interaction, then squad status, then route guidance. Routine notifications collapse during an attack. Every dangerous state uses a word or symbol as well as color; a red bar alone is not an adequate downed-player indicator.

| STATE | EXAMPLE UI COPY | RULE |
| --- | --- | --- |
| Downed teammate | Kell · DOWNED · 01:12 | Show to own squad; strangers see it only after observation or a deliberate help signal. |
| Revive | Hold E · Revive · 8 s | Replace E with the active binding. Display progress and interruption feedback. |
| Captured teammate | Mara · CAPTURED · last signal 35 m | Do not display exact real-time underground coordinates without a valid signal. |
| Free captive | Hold E · Cut bindings | Show whether the rescuer has a valid interaction angle. |
| Battery warning | LIGHT LOW · 15% | Warn before failure; never conceal a sudden rules-driven shutdown. |
| Escape active | Road exit open · 07:30 remaining | Only display a timer tied to an announced opportunity, not a shrinking arena. |

### Layout and implementation targets

Design on a 1920 × 1080 reference canvas with a configurable safe area; keep essential controls inside a 5% inset by default. Support 16:9, 16:10 and ultrawide without pushing squad status to the far edge. Target a 20–24 px base reading size at 1080p and expose a UI-scale setting. Test at the actual play distance.

Use a consistent 32/48/64 px icon family. Avoid tiny decorative labels from the concept sheets. A held flashlight battery appears beside its slot; med-kit quantity appears on that slot; the interface never shows a made-up value while waiting for replication.

### Accessibility and comfort

Provide remappable inputs, toggle/hold alternatives, reduced camera shake, adjustable motion blur, subtitle scaling, speaker identification, high-contrast prompts and color-independent squad identification. Provide a reduced-flash storm mode without changing the server’s danger timing.

Offer a directional sound visualization that describes audible events at their real effective range without revealing unseen exact enemy positions. Lower storm loudness must not erase attack tells. Brightness calibration preserves navigable ground and interactables without turning the forest into daylight.

Inventory, map and pause screens do not pause an online match. A persistent “ONLINE GAME CONTINUES” reminder appears when appropriate. Accessibility preferences persist outside the match.


---

## 10 / Main menu & campfire lobby

*FOUR EMPTY SEATS; ONE SHARED FIRE*

![Campfire main-menu mockup: dark storm, enormous trees, wet ground, distant glowing eyes and four empty positions. The displayed ROOTBOUND title must be replaced with HOLLOW PINES in production.](hollow_pines_assets/02_campfire_lobby_reference.png)

*A02 | Campfire main-menu mockup: dark storm, enormous trees, wet ground, distant glowing eyes and four empty positions. The displayed ROOTBOUND title must be replaced with HOLLOW PINES in production.*

### Scene direction

A fixed cinematic view of a sheltered fire in a deep, nearly black forest. Heavy rain, wind and intermittent lightning reveal distant trunks. Several subtle eye points move beyond the clearing; no creature attacks inside the menu. Logs or stumps define exactly four player positions.

### Player arrival

The initial presentation has four empty seats. A connected player remains an unselected slot until choosing a survivor. The selected character then enters the clearing and sits in that slot, warming hands or checking gear. Ready state appears next to the seat without replacing the character with a static portrait.

### Menu layout

Left: HOLLOW PINES, Play, Survivors, Loadout, Settings and Quit. Right: party roster, privacy, invite controls and readiness. Bottom: input hints and network status. Keep the fire and seated silhouettes visible between the panels.

> This camp is the four-person party lobby, not a 32-person waiting room. The eight squads meet after matchmaking. The empty-seat mockup is the existing visual reference; seated, partial-party and ready states are specified next, not claimed as finished artwork.


---

## 10 / Menu flow & lobby states

*SELECT → SIT → READY → ENTER*

| SCREEN | PRIMARY TASK | NEXT STATE |
| --- | --- | --- |
| Camp / main menu | Choose Play or edit the local survivor, gear and settings. | Character selection, loadout or ready check. |
| Survivor selection | Preview a character, rotate the model and confirm outfit. | Selected model appears at the assigned camp seat. |
| Loadout | Choose equivalent kit focus and inspect tool functions. | Return to camp; readiness resets after a material kit change. |
| Ready / matchmaking | Confirm party and squad-fill settings; find a suitable session. | Loading with map-neutral tips and connection progress. |
| In-game pause | Settings, squad/voice, report, reconnect info or leave confirmation. | Return to active match; online game never pauses. |
| Debrief | Show escaped, rescued, lost and useful contributions. | Keep party together and return to camp. |

### Seat occupancy reference

| SCENE STATE | SEAT 1 | SEAT 2 | SEAT 3 | SEAT 4 |
| --- | --- | --- | --- | --- |
| 0 / 4 selected | Empty | Empty | Empty | Empty |
| 2 / 4 selected | Mara / seated | Grant / seated | Empty / invite | Empty / invite |
| 4 / 4 selected | Mara / ready | Grant / ready | Kai / not ready | Ellis / ready |

The slot state machine is Empty → Connected / selecting → Selected / seated → Ready → Loading. A player changing character stands, exits or crossfades at a controlled transition, then the replacement sits. Avoid instant body swapping in the middle of the firelight.

### Network and input behavior

The party service owns membership; each player owns their selection; the lobby replicates approved selections, seat assignments and ready state. Cosmetic idle timing can be local with a shared seed. A leader leaving transfers leadership without destroying the other players’ camp. A disconnect removes or reserves the seat with a clear reconnect message.

Matchmaking begins after every connected player confirms a character and is ready, with the leader confirming squad fill. A party may enter with fewer than four if the selected mode allows it. Character duplicates between players are allowed initially; personal names and squad marks identify players.

### Animation requirements

Walk in, approach seat, sit, seated idle, warm hands, adjust backpack, look toward distant noise, stand and leave. Blend all four players independently. Offer reduced movement and reduced flash menu settings. Controller focus must never disappear behind the 3D scene.


---

## 11 / Playable survivors

*ROSTER AND ART ACCEPTANCE RULES*

Seven visual directions exist. Names below are working character names; player account names remain separate. Existing inconsistent “Character 3 / 4 / 6” labels are retired. No character is selected for a role because of race, gender or appearance; kits remain interchangeable.

| SURVIVOR | VISUAL / PERSONAL DIRECTION | SUGGESTED STARTER FOCUS |
| --- | --- | --- |
| Mara | Dark-haired modern hiker; cautious and observant. Proposed name for the first unnamed sheet. | General utility |
| Riley | Field-guide influence, rolled sleeves, compact trail kit. | Navigation |
| Grant | Rescue-volunteer influence, radio and medical access. | Rescue |
| Marcus | Cap, workwear and mechanic influence; practical repair kit. | Tools |
| Kai | Urban visitor / delivery-rider influence; lighter silhouette. | Mobility and scavenging |
| Ellis | Black female survivor; calm, capable rescue-support direction. | Medical |
| Brock | Blond male backcountry-guide influence. | Trail support |

### Prototype selection

Start with Mara, Grant, Kai and Ellis to populate the four-seat lobby. Use a common animation-compatible body system where it preserves silhouette and identity. Riley, Marcus and Brock remain documented follow-on options. The wardrobe must read as modern civilian survival clothing rather than seven nearly identical soldiers.

### Required character sheet

Provide a full-body hero, front, back, true left profile and true right profile in separate non-overlapping panels. Match scale, floor height, clothing, equipment placement and proportions across all orthographic views. Opposite sides must face opposite directions and show genuinely different surfaces.

Provide a separate genuine T-pose with arms horizontal, unobstructed hands and no held weapon for rigging. Several existing sheets label lowered arms “T-pose” or repeat the same side view; those errors are not accepted. Keep turnarounds neutrally lit even when the hero shot uses dramatic lighting.

### Production deliverables

Body, outfit, hair and backpack sources; clean rig and skinning; material instances; collision and sockets; distance variants; wet/dirt controls; facial blend shapes; and a playable animation test. Model turnarounds are references, not automatically usable meshes. Visible carried equipment must not clip through revival or seated poses.


---

## 11 / Mara

*SURVIVOR REFERENCE / PROTOTYPE*

![First survivor visual direction, assigned the working name Mara in this document. Legacy branding and the inaccurate lowered-arm “T-pose” label are superseded.](hollow_pines_assets/08_mara_survivor_reference.png)

*A08 | First survivor visual direction, assigned the working name Mara in this document. Legacy branding and the inaccurate lowered-arm “T-pose” label are superseded.*

### Character direction

A practical modern hiker whose silhouette reads through the backpack, tied hair and short weatherproof jacket. She should feel like a person making difficult decisions, not a heavily armored combat specialist. Preserve a distinct face and natural proportions.

### Artist handoff

Separate the hero, turnarounds and rigging pose. Reduce redundant tactical pouches in the civilian pass while preserving the useful flashlight and tool attachments. Confirm hatchet storage, backpack thickness and hands in the actual third-person camera.

Priority animation tests: walking through shallow water, looking behind while moving, helping a downed player and sitting at the campfire. Match wetness and grime across body, clothing and gear rather than applying a uniform gloss to every material.


---

## 11 / Riley

*SURVIVOR REFERENCE / FOLLOW-ON*

![Riley visual direction: field guide and scout. Treat duplicated side orientation, character numbers and decorative role labels as provisional.](hollow_pines_assets/09_riley_survivor_reference.png)

*A09 | Riley visual direction: field guide and scout. Treat duplicated side orientation, character numbers and decorative role labels as provisional.*

### Character direction

An observant guide with a compact trail pack, lighter outer layer and a quietly confident posture. Differentiate Riley from Mara through silhouette, outfit construction, hair and face—not only a jacket recolor.

### Artist handoff

Supply a separate full-body hero shot; the existing portrait is not a substitute. Correct the side views and create a true horizontal-arm T-pose. Tools must remain in the same sockets across the model views and color variants.

Her navigation identity is flavor and a suggested starting kit, not exclusive access to a map mechanic. Any survivor may carry navigation equipment. Additional wardrobe colors must remain legible in rain and low light without glowing or breaking the grounded setting.


---

## 11 / Grant

*SURVIVOR REFERENCE / PROTOTYPE*

![Grant, rescue-volunteer visual direction. Use the separated reference layout, but replace repeated side-facing views with true left and right orthographics.](hollow_pines_assets/10_grant_survivor_reference.png)

*A10 | Grant, rescue-volunteer visual direction. Use the separated reference layout, but replace repeated side-facing views with true left and right orthographics.*

### Character direction

A dependable survivor whose equipment is organized for helping others. Keep the radio and accessible med pouch, but prioritize contemporary search-and-rescue workwear over military body armor.

### Artist handoff

Hands must reach the med pouch, shoulder light and carry grip without stretching. Test his backpack and jacket during knee-down revives and a two-character lift. Provide a separate T-pose and readable head front, three-quarter and profile views.

Animation tone: deliberate, tired but capable. Grant can support the rescue fantasy without receiving an exclusive revive ability. Background and personality are narrative direction; gameplay statistics are defined by the same baseline and selectable kit system as everyone else.


---

## 11 / Marcus

*SURVIVOR REFERENCE / FOLLOW-ON*

![Marcus, cap-and-workwear visual direction. The legacy “Character 3” label conflicts with Grant and is retired; use survivor names or stable internal IDs.](hollow_pines_assets/11_marcus_survivor_reference.png)

*A11 | Marcus, cap-and-workwear visual direction. The legacy “Character 3” label conflicts with Grant and is retired; use survivor names or stable internal IDs.*

### Character direction

A practical mechanic or maintenance-worker influence. Cap, reinforced work trousers and a tool-oriented bag create recognition. Keep him visually distinct from Grant by changing jacket shape and backpack organization, not merely facial hair.

### Artist handoff

Create separate true left and right profiles and a rigging pose. Verify cap/hair intersections at every distance tier. Ensure carried tools have safe stowed silhouettes that do not pierce another player during a rescue or the seat during lobby idles.

A repair-oriented kit can shorten one authored utility interaction at the cost of fewer medical or light supplies. It does not turn Marcus into a mandatory objective key. Every squad must be capable of completing the match without a specific survivor appearance.


---

## 11 / Kai

*SURVIVOR REFERENCE / PROTOTYPE*

![Kai, urban survivor direction with separate pose panels. Rework the repeated side view and lowered-arm rigging pose before production.](hollow_pines_assets/12_kai_survivor_reference.png)

*A12 | Kai, urban survivor direction with separate pose panels. Rework the repeated side view and lowered-arm rigging pose before production.*

### Character direction

Bring the requested urban influence forward: a contemporary hoodie or rain shell, worn everyday layers and a smaller practical bag. The current sheet is overly close to the other tactical hikers; the next wardrobe pass should establish a clearer city-to-wilderness contrast.

### Artist handoff

Retain credible footwear for wet ground without making Kai look like a soldier. Prioritize a clear profile, believable wet hair and lighter gear distribution. Maintain realistic body proportions; no acrobatic superhero styling.

Animation tone: quick decisions, checking the phone or radio, then adapting to the forest. Mobility is a starting-kit emphasis, not a requirement for stunt mechanics. Vaults, carries and revives must use the same traversable spaces and rescue rules as the rest of the roster.


---

## 11 / Ellis

*SURVIVOR REFERENCE / PROTOTYPE*

![Ellis, the Black survivor concept created for the roster, with a medical-support visual direction. Keep the separated panel layout; validate true opposing sides.](hollow_pines_assets/13_ellis_survivor_reference.png)

*A13 | Ellis, the Black survivor concept created for the roster, with a medical-support visual direction. Keep the separated panel layout; validate true opposing sides.*

### Character direction

Calm, capable and attentive under pressure. Preserve her distinct facial features, hair silhouette and grounded posture. Skin shading must remain readable in cool moonlight, warm campfire light and a neutral studio test without flattening the material response.

### Artist handoff

The med pouch needs an accessible placement that does not interfere with climbing or seated poses. Hair should remain stable through running and revival animations. Provide neutral expressions as well as stress states; the injured portrait is optional content intensity, not the only face reference.

Ellis’s kit can emphasize medical supplies, but every survivor can rescue and heal. A separate outfit pass should use recognizable civilian rescue cues and avoid copying the exact same jacket and cargo layout as all other characters.


---

## 11 / Brock

*SURVIVOR REFERENCE / FOLLOW-ON*

![Brock, blond male survivor direction. Normalize the title to HOLLOW PINES and replace exploratory numbering with a stable survivor identifier.](hollow_pines_assets/14_brock_survivor_reference.png)

*A14 | Brock, blond male survivor direction. Normalize the title to HOLLOW PINES and replace exploratory numbering with a stable survivor identifier.*

### Character direction

A weathered backcountry-guide influence with a recognizable blond hair silhouette. Build confidence through posture and practical equipment rather than a heroic combat stance. Use a distinct jacket cut or trail layer to separate him from Grant.

### Artist handoff

Confirm hair readability against light fog and dark forest backgrounds. Test backpack depth, side attachments and scarf movement while turning, looking back and carrying a downed survivor. Orthographic side views must be genuine opposite sides, not duplicate poses.

The visible firearm in exploratory reference is not a starter-loadout approval. Remove it from the initial playable wardrobe and use the approved tool/light loadout. Hunting or tracking flavor does not grant wall-vision or a magical monster-detection ability.


---

## 12 / Animation, sound & atmosphere

*MAKE THE FOREST FEEL PRESENT*

### Animation priorities

Author responsive locomotion before cinematic flourishes. Separate movement intent from pose presentation so network correction does not yank the player out of a revive. Prioritize starts, stops, turns, slopes, wading, exhaustion, hit reaction, downing, crawling, carrying, capture and recovery.

Use foot placement and restrained upper-body adjustment to keep survivors grounded. Backpacks and straps need limited secondary movement, not uncontrolled physics. Two-character actions use tested alignment points, reach limits and an interruption exit for both participants. Blender source animations must include believable weight shifts and breathing rather than rigid looping poses.

### Audio hierarchy

| LAYER | FUNCTION |
| --- | --- |
| Immediate danger | Distinct pounce preparation, grab approach, nearby movement and injury feedback. Always intelligible over weather. |
| Team information | Radio intelligibility, proximity voices, rescue calls and quick acknowledgments. Mute controls never mute essential game cues. |
| Environment | Wind through high branches, rain by material, moving water, debris and cave reflections. |
| Uncertainty | Rare distant calls, branch settling and unexplained movement. Do not play a fake imminent attack cue every minute. |
| Music | Sparse tension beds and low-frequency pressure; silence carries encounters. Rescue success can release tension without a victory fanfare. |

### Storm and darkness

Use cold ambient light and warm player-made pools. Rain and wind vary through shared weather states; local effects sell the transition. Lightning reveals the scene briefly but is never the sole way to see a required obstacle. Fire, lamps and readable reflective surfaces guide travel.

A menu fire is staged under canopy or a protective rock lip so the storm and visible flame feel coherent. In gameplay, shelter and fire placement follow explicit rules; rain cannot extinguish a flame arbitrarily just because an effect plays near it.

### Environment art language

Build giant trunk bases, fallen logs, fern clusters, moss, exposed roots, river stones, cliff modules, cave arches, shelves, stalactites, binding props and a small ranger-service kit. Use repeated materials with controlled wetness; not every surface should have the same glossy finish.

> Concept art is a visual target. A packaged build must prove the target with controllable camera exposure, stable animation, readable audio and repeatable performance—not only a still render.


---

## 13 / Unreal Engine 5.8.3 plan

*RENDERING AND TERRAIN*

Pin the project to the requested Unreal Engine 5.8.3 branch and record plugin versions. Epic published the 5.8.3 hotfix announcement on 22 September 2026. That verifies availability; it does not guarantee project compatibility or performance. [T1]

| SYSTEM | DOCUMENTED CAPABILITY / STATUS | HOLLOW PINES PLAN |
| --- | --- | --- |
| Mesh Terrain | Experimental; supports 3D terrain shapes including tunnels, overhangs and cliffs. [T2] | Prototype one surface-to-cave route. Keep conventional Landscape plus modular cave meshes as the fallback. |
| Lumen | Dynamic global illumination and reflections. [T3] | Use for shifting outdoor/cave light and warm rescue scenes. Budget and test exposure changes. |
| MegaLights | Production-ready in UE 5.8; platform and feature limitations remain. [T4, T5] | Evaluate many player lights on the deferred renderer; keep a tested lower-cost lighting profile. |
| PCG / vegetation | 5.8 adds worldbuilding improvements; Procedural Vegetation Editor remains Experimental. [T4] | Scatter dressing around authored navigation and encounter masks. Do not procedurally block mandatory paths. |
| Fog scattering | Fog Screen Space Scattering is Experimental in 5.8. [T4] | Optional visual experiment, not a shipping dependency or a source of authoritative visibility. |
| World Partition | Grid-based world management and streaming with streaming sources. [T6] | Partition the forest; explicitly test remote squads, caves, captives and critical objective actors. |

### Important lighting limitation

Epic’s MegaLights documentation lists unsupported Water, Clouds, Heterogenous Volumes and Local Volumetrics, and states that MegaLights is incompatible with the Forward Renderer. Therefore the river, storm and local fog cannot be assumed to receive every MegaLights effect. Validate them separately and retain an appropriate supported rendering path. [T5]

### Terrain release gate

Approve Mesh Terrain only after collision, navigation, cave lighting, packaging, streaming and multiplayer traversal pass on target hardware. An editor-only screenshot is not a pass. Keep an authored, non-destructive source workflow and a reversible fallback; runtime terrain excavation is not in scope.

### Do not couple gameplay to rendering

AI visibility uses explicit light states, occlusion and authored visibility rules. Particle rain, ray tracing quality and foliage density settings must not decide whether a player is detectable. Preserve equivalent gameplay blockers and critical cue visibility across visual quality tiers.


---

## 14 / Multiplayer & data architecture

*SERVER-AUTHORITATIVE FROM DAY ONE*

Use dedicated authoritative game servers for the 32-player target. Epic recommends planning for multiplayer from the beginning rather than retrofitting network state later. The component layout below is a project proposal, not a requirement imposed by the engine. [T7]

| RESPONSIBILITY | PROPOSED OWNER |
| --- | --- |
| Session and weather | Game mode / game state: session seed, objectives, escape windows, shared weather timing and global encounter budget. |
| Identity and squads | Player state: survivor ID, squad ID, alliance permissions, ready state, life state and persistent session result. |
| Survivor actions | Replicated character components: health, stamina, inventory, light, interaction, rescue and capture. |
| Enemies | Server AI controller and behavior state; replicated transform, animation intent and attack/capture events. |
| Public objectives | Persistent objective actors or lightweight state records with recovery rules for quest items. |
| HUD and menu | Client presentation models driven by replicated state; approved selection and ready requests sent to server/service. |

### Interaction contract

The client requests an action with a target ID. The server checks distance, line of reach, life state, item availability and an exclusive interaction lock. It then issues an action ID and server timestamps. Clients display progress from that state, while success and resource consumption commit once on the server.

Revive, capture release, extraction and loot transfers are idempotent: a repeated message cannot create a second reward or consume extra charges. Cancellation releases reservations cleanly. Losing visual relevance does not cancel a captive’s deadline or respawn an objective.

### Replication approach

Prioritize nearby movement, attacks and rescue state; reduce frequency for distant environmental props. Always retain lightweight own-squad status even when a teammate is far away. Evaluate the engine’s current replication options in a small benchmark before committing; do not promise that one plugin solves scaling automatically.

Replicate light activation, charge and aim intent, not per-frame lighting output. Weather replicates state and timing, while rain particles are local. Captures use constrained authored attachment/transport behavior instead of fully networked ragdoll chains.

### Data assets

Define survivor presentation, starter kits, item functions, enemy senses/attacks, objective routes, capture sites and weather profiles as separate data. Store stable IDs rather than decorative sheet character numbers. Keep test overrides out of release balance assets.


---

## 14 / Reliability & performance gates

*MEASURE THE WORST CASE*

### Connection and failure behavior

| CASE | REQUIRED BEHAVIOR |
| --- | --- |
| Disconnect in danger | Keep the survivor authoritative and vulnerable for a short reconnect reservation. No disappearing to cancel damage or captivity. |
| Reconnect | Restore the same survivor, inventory, life state and remaining deadline. Never grant a fresh starter kit. |
| Leader leaves | Transfer party leadership without ending the server session or ejecting other squads. |
| Carrier disconnects | Set the carried survivor down at a validated nearby position; preserve rescue state and deadline. |
| Critical item lost | Recover to a reachable public point according to an auditable timeout rule. |
| Server failure | Report an incomplete session; do not falsely award escape or penalize players as if they intentionally abandoned. |

### Initial engineering targets—not measured results

Client target: 60 frames per second on a named PC test configuration to be selected before the performance milestone. Use a 16.7 ms frame budget; do not publish minimum hardware until a packaged build is measured. Target a 30 Hz server simulation, keeping p95 simulation time below 25 ms and p99 below the 33.3 ms tick interval under the test workload.

Stress cases: all 32 survivors converge with active lights; two simultaneous captures in separate regions; eight squads stream distinct cells; heavy rain and river reflections; a cave doorway with multiple carried bodies; and repeated objective interactions under latency. Test at 50/100/150 ms simulated round-trip latency and a controlled packet-loss profile.

### Budgets and observability

Begin the small test with two core enemy actors and expand through measured encounter budgets. Separate perception updates, navigation, animation, VFX and shadow work. Set distance tiers for hair, cloth, foliage, sound and lights. Preserve mechanics and cue visibility when reducing presentation cost.

Log frame and server tick times, network traffic, replication stalls, capture state changes, revive cancellations, quest recovery, disconnected bodies and streaming faults. Use a reproducible route with the same session seed for before/after comparisons.

### Security baseline

Validate movement-dependent interactions, item counts, cooldowns and objective completion on the server. Rate-limit spam actions. Do not trust the client’s claim that an enemy is stunned, a target is in reach or an extraction is complete. Formal anti-cheat, platform account integration and reporting storage remain separate production work.


---

## 15 / Prototype milestones & tests

*A COMPLETE LOOP BEFORE A LARGE WORLD*

| GATE | DELIVERABLE | PASS CONDITION |
| --- | --- | --- |
| M0 / foundation | Pinned engine, source control, automated client/server packaging and a 4-client map. | Two machines connect; state survives movement, damage and a reconnect. |
| M1 / rescue | Health, downing, revive, drag/carry, bindings and one predator graybox. | All recoverable states work under latency without duplicate inventory use or stuck bodies. |
| M2 / first night | 600 m test map, 2 squads, 2 predators, river/cave loop and one shared escape route. | Both squads can rescue and extract; losing one component cannot deadlock the match. |
| M3 / presentation | Four survivors, storm lighting, campfire menu and readable HUD. | Selection fills exactly four seats; gameplay prompts remain legible in dark and bright conditions. |
| M4 / scale | 16-client and 32-client dedicated-server scenarios. | Performance, relevance, remote capture and objective persistence meet measured budgets. |
| M5 / external test | Small invited playtest with instrumentation and a debrief. | Players understand threat tells, rescue tradeoffs and the shared survival goal. |

### Acceptance scenarios

RES-01: two helpers request the same revive; one valid action completes and one charge is consumed. RES-02: a carrier disconnects in the river; the target remains reachable. CAP-01: the predator crosses a streaming boundary while carrying a player; the timer continues. CAP-02: freeing a captive does not immediately allow infinite recapture.

COOP-01: an unallied stranger revives a survivor without inventory access. OBJ-01: one squad extracts while another remains; the route stays functional. UI-01: changing survivor updates the seated model without overlapping bodies. UI-02: all four seats begin empty, then fill only after selection. ART-01: every production turnaround has non-overlapping, genuinely opposite side views.

NET-01: repeat revive, pickup and extraction messages; no duplication. PERF-01: converge 32 lit survivors during a storm at a cave entrance. ACC-01: complete a rescue using hold/toggle alternatives, scaled UI and reduced-flash mode.

### Playtest success hypotheses

Initial targets: most new players can identify their first objective within three minutes, understand why they were downed after one encounter, and make at least one meaningful rescue choice. Track rescue completion and abandonment, but tune from interviews as well as percentages. Do not force a specific death rate simply to label the game “horror.”


---

## 16 / Scope, backlog & open decisions

*WHAT TO BUILD NEXT*

### First-playable scope

One compact map; four playable survivor presentations; two enemy types; one capture/bait interaction; shared extraction; approximately a dozen meaningful item types; campfire lobby; HUD; 8-player human test; and an early path to 32-client engineering tests.

### Initial asset backlog

| PACKAGE | REQUIRED CONTENT |
| --- | --- |
| Environment | Giant trunk kit, roots, fallen trees, ferns, moss, river rocks, cave arch/wall/floor kit, relay shed, road gate, camp seats and fire. |
| Characters | Mara, Grant, Kai and Ellis; shared rescue-compatible animation baseline; separate face/outfit identity; lobby seated poses. |
| Creatures | Forest Stalker and quadruped Cave Stalker; complete attack, interruption, capture and locomotion sets. |
| Props / UI | Lights, radio, map/compass, med kit, bandage, food/water, flare, lure, rope and hatchet; state icons and four-slot interface. |
| Audio / effects | Weather layers, wet movement, cave acoustics, creature tells, rescue actions, radio feedback, flashlight/fire effects and accessibility variants. |

### Explicitly deferred

Persistent base building, freely destructible terrain, free-form rope physics, vehicles, deep-water swimming, PvP progression, live voice imitation, a broad gun arsenal, procedural caves, the biped Cave Dweller, additional playable characters and console certification. None is required to prove the core rescue loop.

### Decisions for the next review

Confirm the proposed PvE-first / player-damage-off baseline; preferred match length; whether solo or duo public entry is supported; launch hardware and store targets; desired injury intensity; final survivor names; and whether cosmetic progression should exist at all. The current document keeps progress cosmetic or informational, with no permanent combat advantage.

### Risks and responses

If 32 players dilute tension, change route density and encounter timing before increasing monster health. If capture removes too much agency, shorten transport and add clearer self-escape opportunities. If Mesh Terrain or lighting fails performance gates, use the documented fallback rather than delaying the rescue prototype.

> Next production priority: build the two-squad river-to-cave rescue test and the four-seat lobby state machine. Additional concept sheets should answer specific implementation questions, not replace playtesting.


---

## 17 / Technical references

*PRIMARY SOURCES / VERIFIED 08 OCTOBER 2026*

The sources below support engine facts only. Game rules, timings, dimensions, architecture and milestone thresholds are original design proposals. Availability of an engine feature does not establish suitability for this project.

**[T1] [Epic Developer Community — 5.8.3 Hotfix Released](https://forums.unrealengine.com/t/5-8-3-hotfix-released/2833315)**

Published 22 September 2026. Confirms the requested engine patch exists.

**[T2] [Epic Games — Mesh Terrain](https://dev.epicgames.com/documentation/unreal-engine/mesh-terrain-in-unreal-engine)**

Documents the Experimental 3D terrain system and tunnel/overhang capability.

**[T3] [Epic Games — Lumen Global Illumination and Reflections](https://dev.epicgames.com/documentation/unreal-engine/lumen-global-illumination-and-reflections-in-unreal-engine)**

Documents dynamic GI and reflections; does not imply a project-specific frame rate.

**[T4] [Epic Games — Unreal Engine 5.8 is now available](https://www.unrealengine.com/news/unreal-engine-5-8-is-now-available)**

Release overview: MegaLights production readiness, worldbuilding updates and Experimental features.

**[T5] [Epic Games — MegaLights](https://dev.epicgames.com/documentation/unreal-engine/megalights-in-unreal-engine)**

Documents rendering, platform support and current limitations, including water and local volumetrics.

**[T6] [Epic Games — World Partition](https://dev.epicgames.com/documentation/unreal-engine/world-partition-in-unreal-engine)**

Documents grid-based world streaming and streaming-source behavior.

**[T7] [Epic Games — Networking Overview](https://dev.epicgames.com/documentation/unreal-engine/networking-overview-for-unreal-engine)**

Explains multiplayer concepts and the importance of designing for networking early.

Re-check feature status and limitations before an engine upgrade. Pin the project to a tested version rather than automatically adopting the newest release. No external asset purchase, engine plugin license or platform entitlement is assumed by this document.


---

## 17 / Visual reference register

*ARTWORK PROVENANCE AND CORRECTIONS*

All A-series plates were generated earlier in this conversation for this forest-survival project. They are embedded unchanged except for the explicitly identified cover crop. Original files are retained in the portable asset folder; none of the artwork is presented as an actual Unreal Engine screenshot or a finished mesh.

| ID | REFERENCE | DESIGN STATUS |
| --- | --- | --- |
| A01 | River rescue gameplay screenshot | Atmosphere and framing; HUD text is superseded. |
| A02 | Stormy campfire menu | Empty four-seat layout; production branding is HOLLOW PINES. |
| A03 | Forest Stalker | Core enemy reference; correct decorative scale claims. |
| A04 | Biped Cave Dweller | Reserve exploration; not first-playable scope. |
| A05 | Quadruped Cave Stalker | Core cave enemy; validate four-legged locomotion. |
| A06 | Survival equipment | Modern gear direction; fictional item copy requires rewriting. |
| A07 | Hatchet | Game prop reference; validate scale on rig. |
| A08 | First female survivor / Mara | Proposed working name; correct pose and branding. |
| A09 | Riley | Follow-on survivor; correct repeated side view. |
| A10 | Grant | Prototype survivor; correct repeated side view. |
| A11 | Marcus | Follow-on survivor; retire conflicting numbering. |
| A12 | Kai | Prototype survivor; strengthen urban wardrobe identity. |
| A13 | Ellis | Prototype survivor; validate skin, hair and rescue equipment. |
| A14 | Brock | Follow-on survivor; remove unapproved starter firearm. |

### Superseded visual details

ROOTBOUND and THE HOLLOW PINES are legacy treatments; final title is HOLLOW PINES. The “mist shrinks” mechanic, exact live stranger count, decorative character statistics, inconsistent character numbers, repeated same-facing profiles and incorrectly labeled T-poses are not approved specifications.

### Portable files

Hollow_Pines_GDD.md uses relative image links to hollow_pines_assets/. Keep the folder beside the Markdown file, or extract the complete package. The PDF and Word versions embed their images. The full package includes all three document formats, the referenced PNGs and an asset manifest.

Revision discipline: change the written rule first, update its test case, then revise the relevant mockup. Preserve the original concept separately so artists and programmers can distinguish exploration from the current implementation target.
