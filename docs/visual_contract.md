# Orbis Lab – 3D Visual Directives Contract

This document specifies the exact visual directives and character animation contract returned by the **Orbis Lab** backend engine (`POST /api/lab/sessions/{id}/actions`).

The backend acts as the authoritative **"World Brain"**, validating player intent against laboratory safety rules and physical/chemical simulations. The Three.js frontend client is a **pure renderer**: it interprets these directives to update 3D scene meshes, shaders, particle systems, and character skeletal rigs.

---

## 1. Directive Types

Every action result returns a `visuals` array containing zero or more directives conforming to the following schemas:

### A. Liquid Volume & Shader Color (`"liquid"`)
Directs the 3D client to update the liquid mesh inside volumetric glassware or containers (e.g. burette meniscus, conical flask solution, blood collection tubes, dosing cups).

```json
{
  "type": "liquid",
  "target": "conical_flask",
  "hex": "#ec4899",
  "volume_ml": 26.0,
  "opacity": 0.90
}
```
* **`target`** (string): Unique apparatus identifier (e.g., `"dosing_cup"`, `"tube_1"`, `"burette"`, `"conical_flask"`).
* **`hex`** (string): Standard hex RGB color code representing solution color or indicator absorption spectrum.
* **`volume_ml`** (float): Total liquid volume in mL to drive geometric liquid level / height displacement in the mesh.
* **`opacity`** (float, 0.0–1.0): Material transmission / alpha transparency (e.g. 0.8 for clear aqueous buffer, 0.95 for opaque whole blood).

---

### B. Dynamic Particle & Visual Effects (`"effect"`)
Triggers temporary particle systems, shader flashes, or alarms anchored to an apparatus or character bone.

```json
{
  "type": "effect",
  "target": "dosing_cup",
  "name": "bubbles",
  "duration_ms": 1500
}
```
* **`target`** (string): Apparatus or coordinate target for effect emitter.
* **`name`** (enum):
  * `"splash"`: Fast droplet burst when pouring too quickly or violating the acid dilution sequence.
  * `"bubbles"`: Effervescence particle system inside liquid when dissolving powder or swirling.
  * `"smoke"`: Vapor plume from exothermic chemical contact.
  * `"spark"`: Electrical or static discharge.
  * `"alarm"`: Flashing red ambient light and strobe when critical safety limits are breached.
  * `"glow"`: Subtle cyan/teal bioluminescent or UV fluorescence pulse.
  * `"fume_puff"`: Toxic chemical fume plume (red/yellow particle puff) + 5s camera blur and shake (Rules R1 / R2: handling chemicals/blood without goggles/gloves).
  * `"contamination"`: Cross-contamination visual effect turning solution muddy brown/grey `#6b5b45` (Rule R5).
  * `"spill_puddle"`: Chemical spill puddle decal spreading on benchtop/floor with falling drip particles (Rule R6: hazardous acid/water pouring).
  * `"runaway_reaction"`: Vigorous boiling effervescence + dense rising steam plume (Rule R8: dose limit exceeded).
  * `"foam_eruption"`: Violent foaming eruption and smoke from waste receptacle (Rules R9 / R10: incompatible waste mixture).
  * `"camera_shake"`: 8px high-frequency camera shake for 300ms on critical violations.
  * `"alarm_flash"`: Vivid red peripheral HUD border flash on critical safety breaches.
  * `"sparkles"`: Gentle green celebratory sparkle particle burst above apparatus on protocol step completion.
  * `"confetti"`: Celebratory multi-color confetti particle shower on Grade A report completion.
* **`duration_ms`** (integer): Lifetime of the effect in milliseconds before auto-culling.

---

### C. Digital Instrument Readout (`"readout"`)
Updates 2D/3D screen canvases, LED segment displays, or floating tooltips on analytical laboratory equipment.

```json
{
  "type": "readout",
  "target": "digital_balance",
  "label": "Weight",
  "value": 0.500,
  "unit": "g"
}
```
* **`target`** (string): Apparatus with digital display (e.g., `"digital_balance"`, `"ph_meter"`, `"ward_clock"`, `"assay_analyzer"`).
* **`label`** (string): Displayed measurement title (e.g., `"Tare"`, `"pH"`, `"Weight"`, `"Plasma Assay"`).
* **`value`** (float | string): Scalar reading value formatted for instrument display.
* **`unit`** (string): Unit abbreviation (`"g"`, `"mL"`, `"mg/L"`, `"pH"`, `"h"`).

---

### D. Patient Physiological Vitals (`"vitals"`)
Updates the bedside hospital cardiac monitor and clinical HUD during pharmacokinetics ward simulations.

```json
{
  "type": "vitals",
  "patient": "Alex (70 kg)",
  "hr": 70,
  "spo2": 99,
  "status": "stable_therapeutic (illustrative)"
}
```
* **`patient`** (string): Patient profile label.
* **`hr`** (integer): Heart rate in beats per minute (BPM).
* **`spo2`** (integer): Peripheral blood oxygen saturation percentage.
* **`status`** (string): Clinical state classification (`"stable_therapeutic"`, `"subtherapeutic"`, `"toxic_tachycardia"`).
> *Note: Physiological vitals are illustrative and educational only.*

---

### E. Physical Container Identification Label (`"label"`)
Renders printed or handwritten barcode/text decals directly onto 3D glassware and sample tubes.

```json
{
  "type": "label",
  "target": "tube_1",
  "text": "Pt: Alex | Paracetamol | t=1.0h"
}
```
* **`target`** (string): Target object receiving label (e.g., `"dosing_cup"`, `"tube_1"`).
* **`text`** (string): Exact alphanumeric text string projected onto the container texture.

---

### F. Interactive Object Highlight (`"highlight"`)
Outlines interactive meshes with a luminous Fresnel edge glow to draw player focus during protocol progression.

```json
{
  "type": "highlight",
  "target": "conical_flask"
}
```

---

## 2. Character Animation Contract

Every action result may optionally specify a `character_animation` directive driving the 3D humanoid avatar's skeletal state machine:

```json
{
  "character_animation": {
    "name": "draw_blood",
    "target": "patient_bed",
    "duration_ms": 2500
  }
}
```

### Supported Avatar Animation Clips
| Animation Name | Description | Typical Target |
|---|---|---|
| `"idle"` | Default standing breathing posture | `"avatar"` |
| `"wear_ppe"` | Avatar dons goggles/gloves/coat gesture | `"avatar"` |
| `"weigh"` | Leans over balance, uses laboratory spatula | `"digital_balance"` |
| `"pour"` | Tilts beaker/jug with fluid streaming | `"dosing_cup"` / `"conical_flask"` |
| `"write_label"` | Writes with laboratory marker pen | Container or sample tube |
| `"administer"` | Hands oral medication to patient | `"patient_bed"` |
| `"draw_blood"` | Applies tourniquet, swab, and vacuum tube draw | `"patient_bed"` |
| `"swirl"` | Holds neck of conical flask and rotates wrist smoothly | `"conical_flask"` |
| `"turn_stopcock"` | Finely rotates burette PTFE stopcock with left hand | `"burette"` |
| `"read"` | Leans in to inspect meniscus or digital display | Apparatus sensor |
| `"dispose"` | Drops item into designated waste receptacle | Waste bin |
| `"wash_hands"` | Lathers and rinses hands under running water | `"sink"` |

---

## 3. End-to-End Action Result Payload Example

Here is a complete JSON response returned by `POST /api/lab/sessions/{id}/actions` when dispensing titrant:

```json
{
  "accepted": true,
  "message": "Dispensed +1.00 mL NaOH titrant (Total added: 25.00 mL).",
  "events": [
    {
      "timestamp_h": 0.0,
      "action": "titrate",
      "message": "Dispensed +1.00 mL NaOH titrant (Total added: 25.00 mL).",
      "severity": "normal"
    }
  ],
  "violations": [],
  "visuals": [
    {
      "type": "liquid",
      "target": "burette",
      "hex": "#f8fafc",
      "volume_ml": 25.0,
      "opacity": 0.8
    },
    {
      "type": "liquid",
      "target": "conical_flask",
      "hex": "#ec4899",
      "volume_ml": 50.0,
      "opacity": 0.9
    },
    {
      "type": "readout",
      "target": "burette",
      "label": "Remaining",
      "value": 25.0,
      "unit": "mL"
    }
  ],
  "character_animation": {
    "name": "turn_stopcock",
    "target": "burette",
    "duration_ms": 1600
  },
  "score_delta": 0,
  "hints": [],
  "status": "active"
}
```
