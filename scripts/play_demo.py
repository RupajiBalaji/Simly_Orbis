#!/usr/bin/env python3
"""
Orbis Lab Live Demo Player (scripts/play_demo.py)

Plays both interactive experiments ('pk_ward' and 'titration_bench')
end-to-end against a running Orbis Lab backend server.

Demonstrates:
  1. Experiment initialization & protocol steps
  2. Stateful action execution & visual directive logging
  3. Safety rules engine validation & PPE enforcement
  4. Simulation solvers (PK oral superposition & acid-base charge balance)
  5. Final multi-factor report cards and leaderboard ranking
"""

import json
import os
import sys
import time
import urllib.error
import urllib.request

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

BASE_URL = os.getenv("ORBIS_URL", "http://127.0.0.1:8000")


def api_request(method: str, path: str, data: dict | None = None) -> dict:
    url = f"{BASE_URL}{path}"
    headers = {"Content-Type": "application/json"}
    body = json.dumps(data).encode("utf-8") if data is not None else None
    req = urllib.request.Request(url, data=body, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req, timeout=10) as response:
            return json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        err_msg = exc.read().decode("utf-8")
        print(f"\n[HTTP Error {exc.code} on {path}]: {err_msg}", file=sys.stderr)
        raise
    except Exception as exc:
        print(f"\n[Connection Error on {url}]: {exc}", file=sys.stderr)
        raise


def run_action(session_id: str, action: str, params: dict | None = None, target: str | None = None) -> dict:
    resolved_target = target or (params.get("target") if params else None)
    payload = {"action": action, "target": resolved_target, "params": params or {}}
    res = api_request("POST", f"/api/lab/sessions/{session_id}/actions", payload)
    
    status_icon = "OK" if res["accepted"] else "REJECT"
    print(f"  [{status_icon}] Action '{action}': {res['message']}")
    
    if res.get("violations"):
        for v in res["violations"]:
            expl = v.get("explanation") or v.get("title") or "Safety breach"
            print(f"      [VIOLATION] [{v['severity'].upper()}] {v['rule_id']} - {expl}")
            
    if res.get("visuals"):
        for vis in res["visuals"]:
            vtype = vis.get("type")
            target = vis.get("target") or vis.get("patient") or "scene"
            detail = ""
            if vtype == "liquid":
                detail = f"vol={vis.get('volume_ml')}mL, hex={vis.get('hex')}"
            elif vtype == "effect":
                detail = f"effect='{vis.get('name')}', dur={vis.get('duration_ms')}ms"
            elif vtype == "readout":
                detail = f"{vis.get('label')} = {vis.get('value')} {vis.get('unit') or ''}"
            elif vtype == "vitals":
                detail = f"HR={vis.get('hr')} bpm, SpO2={vis.get('spo2')}%, status={vis.get('status')}"
            elif vtype == "label":
                detail = f"text='{vis.get('text')}'"
            print(f"      [DIRECTIVE:{vtype}] -> target: '{target}' ({detail})")

    if res.get("character_animation"):
        anim = res["character_animation"]
        print(f"      [ANIMATION]: {anim.get('name')} (target: {anim.get('target')})")

    return res


def play_pk_ward():
    print("\n" + "=" * 70)
    print("  EXPERIMENT 1: Pharmacokinetics Ward (pk_ward)")
    print("=" * 70)

    # 1. Start Session
    session = api_request("POST", "/api/lab/sessions", {
        "experiment_id": "pk_ward",
        "nickname": "Dr_Alex_Demo"
    })
    session_id = session["session_id"]
    print(f"Started session: {session_id} for '{session['experiment_id']}' (Player: {session['nickname']})")

    # 2. Sequential Protocol Actions
    run_action(session_id, "wear_ppe", {"item": "goggles"})
    run_action(session_id, "wear_ppe", {"item": "gloves"})
    run_action(session_id, "wear_ppe", {"item": "coat"})
    run_action(session_id, "tare_balance")
    run_action(session_id, "weigh", {"amount_g": 0.5, "substance": "paracetamol"})
    run_action(session_id, "dissolve", {"substance": "paracetamol", "solvent": "water", "target": "dosing_cup"})
    run_action(session_id, "label", {"target": "dosing_cup", "text": "Pt: Alex | Paracetamol 500mg"})
    run_action(session_id, "administer_oral", {"target": "patient_bed"})

    # Advance time and draw blood at 1h
    run_action(session_id, "advance_time", {"hours": 1.0})
    run_action(session_id, "label", {"target": "tube_1", "text": "Pt: Alex | t=1.0h"})
    run_action(session_id, "draw_blood", {"target": "tube_1"})
    run_action(session_id, "run_assay", {"target": "tube_1"})

    # Advance time and draw blood at 3h
    run_action(session_id, "advance_time", {"hours": 2.0})
    run_action(session_id, "label", {"target": "tube_2", "text": "Pt: Alex | t=3.0h"})
    run_action(session_id, "draw_blood", {"target": "tube_2"})
    run_action(session_id, "run_assay", {"target": "tube_2"})

    # Advance time and draw blood at 6h
    run_action(session_id, "advance_time", {"hours": 3.0})
    run_action(session_id, "label", {"target": "tube_3", "text": "Pt: Alex | t=6.0h"})
    run_action(session_id, "draw_blood", {"target": "tube_3"})
    run_action(session_id, "run_assay", {"target": "tube_3"})

    # Cleanup & Finish
    run_action(session_id, "dispose_waste", {"item": "dosing_cup", "bin": "biohazard"})
    run_action(session_id, "wash_hands")
    
    print("\n--- Submitting Final Report ---")
    report = api_request("POST", f"/api/lab/sessions/{session_id}/finish")
    print(f"Final Report Grade: {report['grade']}")
    print(f"Overall Score: {report['score']} / 100")
    print(f"Score Breakdown: {report['score_breakdown']}")
    print(f"Lessons Learned: {report.get('lessons_learned', [])}")


def play_titration_bench():
    print("\n" + "=" * 70)
    print("  EXPERIMENT 2: Acid-Base Titration Bench (titration_bench)")
    print("=" * 70)

    # 1. Start Session
    session = api_request("POST", "/api/lab/sessions", {
        "experiment_id": "titration_bench",
        "nickname": "Chem_Prof_Demo"
    })
    session_id = session["session_id"]
    print(f"Started session: {session_id} for '{session['experiment_id']}' (Player: {session['nickname']})")

    # 2. Sequential Protocol Actions
    run_action(session_id, "wear_ppe", {"item": "goggles"})
    run_action(session_id, "wear_ppe", {"item": "gloves"})
    run_action(session_id, "wear_ppe", {"item": "coat"})
    run_action(session_id, "rinse_burette", {"solvent": "naoh"})
    run_action(session_id, "fill_burette", {"titrant": "naoh", "volume_ml": 50.0})
    run_action(session_id, "pipette_analyte", {"analyte": "hcl", "volume_ml": 25.0, "target": "conical_flask"})
    run_action(session_id, "add_indicator", {"indicator": "phenolphthalein", "drops": 3, "target": "conical_flask"})
    run_action(session_id, "read_ph_meter")

    # Titration progression (20 mL fast -> swirl -> 4.5 mL -> swirl -> 0.5 mL endpoint -> swirl)
    run_action(session_id, "titrate", {"volume_ml": 20.0})
    run_action(session_id, "swirl")
    run_action(session_id, "titrate", {"volume_ml": 4.5})
    run_action(session_id, "swirl")
    run_action(session_id, "titrate", {"volume_ml": 0.5})  # Exactly reaches 25.0 mL
    run_action(session_id, "swirl")
    run_action(session_id, "read_ph_meter")
    run_action(session_id, "record_endpoint", {"volume_ml": 25.0})

    # Cleanup & Finish
    run_action(session_id, "dispose_waste", {"item": "conical_flask", "bin": "chemical"})
    run_action(session_id, "wash_hands")

    print("\n--- Submitting Final Report ---")
    report = api_request("POST", f"/api/lab/sessions/{session_id}/finish")
    print(f"Final Report Grade: {report['grade']}")
    print(f"Overall Score: {report['score']} / 100")
    print(f"Score Breakdown: {report['score_breakdown']}")
    print(f"Lessons Learned: {report.get('lessons_learned', [])}")


def show_leaderboards():
    print("\n" + "=" * 70)
    print("  ORBIS LAB LEADERBOARDS")
    print("=" * 70)
    for exp_id in ["pk_ward", "titration_bench"]:
        entries = api_request("GET", f"/api/lab/leaderboard?experiment_id={exp_id}")
        print(f"\nTop Reports for [{exp_id}]:")
        for entry in entries[:5]:
            nick = entry.get("nickname", "Anonymous")
            score = entry.get("score", 0)
            grade = entry.get("grade", "-")
            rank = entry.get("rank", 1)
            created = entry.get("created_at", "")[:19]
            print(f"  #{rank} {nick:18} | Score: {score:3d} (Grade: {grade}) | Date: {created}")


def main():
    print("Checking Orbis Lab server health at", BASE_URL)
    try:
        health = api_request("GET", "/api/health")
        print(f"Server online. Storage mode: {health.get('storage')}, Lab sessions: {health.get('counts', {}).get('lab_sessions', 0)}")
    except Exception:
        print(f"Error: Could not connect to {BASE_URL}. Ensure uvicorn is running.")
        sys.exit(1)

    play_pk_ward()
    play_titration_bench()
    show_leaderboards()
    print("\n[SUCCESS] Both experiments played successfully!")


if __name__ == "__main__":
    main()
