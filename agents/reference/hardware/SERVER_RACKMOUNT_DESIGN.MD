# Rack & GPU Integration Context Summary  
_Last updated: 2025-11-08_

---

## 🧭 Context Overview

User (Shua) operates a **12U wall-mounted rack**, mounted roughly **3 feet above the floor**.  
The rack houses a **Sliger CX3701** 3U chassis configured with:

- **Motherboard:** B550I AORUS Pro AX (Mini-ITX)  
- **CPU:** Ryzen AM4 platform  
- **PSU:** Corsair SF750 80+ Platinum SFX  
- **Storage:** 10× trayless 3.5" HDDs (hot-swap/direct-wired SATA)  
- **Cooling:** AC Infinity controllers and fans (top & bottom zones)  

The goal was to **mount an NVIDIA RTX 3070 GPU externally** within the rack while **maintaining ideal airflow**, ensuring the GPU cooperates with the CX3701’s cooling pattern and the rack’s chimney flow.

---

## 🧱 Current Rack (Before GPU Upgrade)

### Rack Layout (Pre-Upgrade)
| U-slot | Component | Function | Airflow Role | Notes |
|:------:|:-----------|:----------|:--------------|:------|
| **U1–U2** | Patch panel + switch | Networking | Passive zone | Minimal airflow impact. |
| **U3–U5** | CX3701 Server | Compute + storage | **Right→Left airflow**; exhausts at **U3** | 3U chassis; internal side-to-side cooling. |
| **U6–U7** | AC Infinity fan/controller modules | Exhaust assist | **Top exhaust zone** | Controlled exhaust path for chimney flow. |
| **U8** | (Empty space) | Open clearance | Neutral | Provides unobstructed vertical flow. |
| **U9** | Front-mount PDU | Power distribution | Neutral | Easy access to outlets. |
| **U10–U11** | Utility shelf | Pi, NUC, misc devices | Slightly warm | Rear open for convection. |
| **U12** | UPS | Power backup | **Intake region** | Draws cool ambient air into rack base. |

### Airflow Behavior (Pre-Upgrade)

Room air (~22 °C)
↑ drawn in through UPS (U12)
↑ passes through utility shelf (U10–U11)
↑ feeds CX3701 intake (right side)
→ inside CX3701: air moves RIGHT → LEFT → rear exhaust (U3)
↑ AC Infinity fans pull that hot air upward & out top (U6–U7)

- Air enters **low/front**, moves **rearward**, then **rises** behind chassis.  
- The CX3701 adds **lateral (R→L)** exhaust into that same vertical column.  
- Combined result: **cross-flow + vertical convection synergy**.

---

## 🧩 Objective of the GPU Upgrade

Add an **RTX 3070** (2.5-slot card, 10.5" length, ~220–250 W) to the rack in a **thermally coherent** way:
- Must **not** disrupt CX3701 exhaust pattern.  
- Must **use ambient intake air**, not recirculated heat.  
- Must fit physically in limited rack depth (Sliger 15" chassis, 12U frame).  
- Must allow future serviceability (server removable without unbolting GPU).

---

## 🔧 GPU Integration Decision Process

### Options Considered
| Mount Location | Pros | Cons | Verdict |
|:--|:--|:--|:--|
| **Above server (U3 zone)** | Shortest cables | Pulls in 40 °C exhaust, airflow conflict, service difficulty | ❌ Rejected |
| **Below server (U7–U8)** | Coolest intake, cable reach fine, airflow aligned | Uses 2 U vertical clearance | ✅ Chosen |
| **Side-mounted (rack wall)** | Clean thermal separation | Complicated bracket, riser tension | ⚙️ Optional future mod |

**Key insight:**  
The **air above the server (U3)** is *exhaust air*—it’s turbulent, 10–20 °C warmer than ambient, and moving upward.  
The GPU must **breathe cold air**, not re-ingest the CX3701’s output.

---

## 🧱 Final Rack Layout (Post-GPU Integration)

| U-slot | Component | Function | Airflow Role | Notes |
|:------:|:-----------|:----------|:--------------|:------|
| **U1–U2** | Patch panel + switch | Networking | Passive warm zone | Above exhaust. |
| **U3** | CX3701 exhaust zone | Hot air exits here | Primary exhaust (rear/left). |
| **U4–U6** | CX3701 chassis | Compute + storage | **Right→Left internal airflow**, exhausts into U3/rear plenum. |
| **U7** | Open air gap | Clearance + airflow buffer | GPU height extends upward into this space. |
| **U8** | **1U GPU shelf (RTX 3070 on top)** | Mounted flat, **fan side up**, **R→L orientation** | Intake reinforcement; 120 mm fan assists airflow. |
| **U9** | Front-mount PDU | Power & cable management | Neutral; short leads to PSU & GPU. |
| **U10–U11** | Utility shelf (NUC, Pi, controllers) | Light gear | Slightly warm. |
| **U12** | UPS | Power backup | **Cool intake region**; base of chimney. |

---

## 🎯 GPU Mount Details

- **Shelf:** StarTech.com 1U vented metal cantilever shelf (16″ depth, model CABSHELF116V).  
- **GPU:** RTX 3070 (~10.5″ long, 2.5-slot, ~4.4″ tall).  
  - Rests flat on shelf.  
  - Fan side faces **up**.  
  - Fans pull from **right** (cool side) → blow **left** (toward exhaust).  
  - Extends physically through **U7 + U8** space.  
- **PCIe Riser:**  
  - LINKUP Ultra PCIe 4.0 x16 (300–500 mm, 270° or 180° orientation).  
  - Routes from CX3701 rear I/O downward into GPU socket (gentle bend).  
- **Power:**  
  - 2× Corsair Type-4 8-pin cables, direct from SF750 (no daisy-chain).  
- **Fans:**  
  - (1) 120 mm right-rail fan (RIGHT → LEFT) across GPU face.  
  - (1 optional) 120 mm front-to-rear fan into rear plenum to boost chimney flow.  
- **Grounding:**  
  - Short 16 AWG wire from GPU bracket to rack frame.  
- **Air sealing:**  
  - Foam weather-strip along rear rails to contain chimney airflow.

---

## 🌬️ Combined Airflow (Post-Upgrade)

[Ambient room air (~22 °C)]
↑ drawn in low/front around UPS (U12)
↑ rises past utility shelf (U10–U11)
↑ enters GPU zone (U8) – fans pull RIGHT → LEFT
↑ GPU exhaust joins CX3701 intake stream
↑ CX3701 (U4–U6) pulls air RIGHT → LEFT, exhausts rear/left into U3
↑ Rear plenum carries mixed air upward
↑ AC Infinity exhaust fans (U6–U7) pull air up & out top
[Exhaust air (~38–42 °C) leaves rack top]

**Airflow coherence:**  
- GPU and server share the **same horizontal (R→L)** pattern.  
- Rack maintains **vertical convection (Front→Rear→Up)** behind them.  
- Cool intake air always originates from right/bottom side.

---

## 🧰 Supporting Hardware Summary

| Component | Model / Notes |
|:--|:--|
| **GPU Shelf** | StarTech.com 1U vented cantilever shelf (16″ depth, CABSHELF116V) |
| **PCIe Riser** | LINKUP Ultra Gen4 x16 270°/180° (300–500 mm) |
| **Fans** | Arctic P12 / Noctua P12 (pressure-optimized, PWM) |
| **Controllers** | AC Infinity dual-zone (top = exhaust, bottom = intake) |
| **Power Supply** | Corsair SF750 Platinum SFX |
| **Grounding** | 16 AWG copper wire GPU bracket → rack |
| **Sealing** | Foam tape on rear rails (directs vertical plenum airflow) |

---

## 🧠 Design Principles Recap

| Principle | Description |
|:--|:--|
| **Cold air path** | Always enters low/right side. |
| **Hot air path** | Always exits rear/top (U3). |
| **GPU alignment** | Follows server R→L direction. |
| **Serviceability** | GPU shelf removable without unbolting CX3701. |
| **Noise & heat** | Managed via AC Infinity dual controllers. |
| **Center of gravity** | Balanced; GPU mounted below center, not above. |

---

## 🧩 System Diagrams

### Top View

RIGHT (cold aisle)                                   LEFT (hot aisle)
┌────────────────────────────────────────────────────────────────────────┐
│ ←←← 120 mm assist fan (R→L) on U8 shelf                                │
│ ┌─────────────── RTX 3070 GPU ────────────────┐                        │
│ │ ↑↑↑ axial fans pull from RIGHT → blow LEFT │ →→→ warm exhaust       │
│ └────────────────────────────────────────────┘                        │
│        ↑ riser from CX3701 rear I/O (gentle radius)                   │
│ ┌────────────────── CX3701 (U4–U6) ────────────────────────────────┐  │
│ │ Intake RIGHT → exhaust LEFT/REAR → joins rear plenum → upward     │  │
│ └──────────────────────────────────────────────────────────────────┘  │
│ Rear plenum: FRONT→REAR push (from bottom) → upward to exhaust      │
└────────────────────────────────────────────────────────────────────────┘

### Side View

FRONT of rack                                             REAR wall
┌─────────────────────────────────────────────────────────────────────┐
│ U1–U2  Patch/Switch (passive)                                       │
│ U3     CX3701 EXHAUST ZONE  ← hot air exits here                   ↑│
│ U4–U6  CX3701 main body  (R→L exhaust joins rear plenum)             │
│ U7     Open gap / GPU height clearance                              │
│ U8     GPU shelf (flat mount, fan side up, assist fan R→L)          │
│ U9     Front PDU (neutral)                                          │
│ U10–U11 Utility shelf                                               │
│ U12    UPS (intake, cool air source)                                │
└─────────────────────────────────────────────────────────────────────┘
↑ cool air intake low/front → rear → up (vertical chimney)

---

## ✅ Final Deliverables

- **Rack_GPU_Layout_Final.pdf** — diagram + 12U summary  
- **Rack_GPU_Conversation_Summary.md** — this full context document  
- Airflow logic validated for **sideflow (R→L)** and **vertical (Front→Rear→Up)** coherence  
- GPU location: **U8 (shelf mount)**, spanning **U7–U8**  
- Exhaust zone: **U3**  
- Rack verified for **thermal separation**, **serviceability**, and **balanced power**

---

## 🔁 Handoff Notes (for Next Agent)

- Treat this layout and airflow design as **canonical**.  
- If integrating a new GPU:  
  1. Confirm card fits 10.5″ × 4.5″ × 2.5 slot dimensions.  
  2. Verify total power < 300 W (SF750 headroom).  
- Any change in chassis or rack height should **re-model airflow** using same dual-vector principles (R→L internal, F→R→Up plenum).  
- AC Infinity thresholds currently assumed:  
  - **Intake fans:** start 30 °C, max 45 °C.  
  - **Exhaust fans:** start 35 °C, max 50 °C.  
- Keep right side clear (cold aisle), left side vented (hot exhaust).  
- Top 1–2 U always remain unobstructed to maintain vertical exhaust column.

---

_This markdown captures the **complete context, technical reasoning, airflow modeling, and physical layout** of Shua’s 12U wall-mounted rack before and after the RTX 3070 integration.  
All subsequent modifications should reference this file as the system baseline._