---

## Demo

Three real scenarios — run them yourself with the included sample data.

---

### Scenario 1 — Conveyor motor overheat

**Input:** `data/samples/conveyor_motor_overheat.csv`

```
timestamp             tag           value    unit   status
2026-03-18 11:00:00   motor_temp    65.2     °C     ok
2026-03-18 11:12:00   motor_temp    71.4     °C     ok
2026-03-18 11:24:00   motor_temp    78.8     °C     warn
2026-03-18 11:35:00   motor_temp    87.3     °C     warn
2026-03-18 11:47:00   motor_temp    96.1     °C     warn
```

**Command:**
```bash
python main.py --file data/samples/conveyor_motor_overheat.csv --asset ConveyorMotorA
```

**Output:**
```
━━━  PHASE 1 · PARSE  ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Asset:                ConveyorMotorA
Rows loaded:          144
Columns valid:        ✓  timestamp  tag  value  unit  asset  status

━━━  PHASE 2 · DETECT  (tool calls)  ━━━━━━━━━━━━━━━━━━━━━━━
  [tool] run_spike_detector           OK     no spikes detected
  [tool] run_flatline_detector        OK     no flatline detected
  [tool] run_missing_data_detector    OK     no gaps found
  [tool] run_out_of_range_detector    WARN   3 readings above 90°C
  [tool] run_drift_detector           FAULT  47.3% upward drift over 47 min

━━━  PHASE 3 · FINDINGS  ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  [CRITICAL] Upward drift
             motor_temp rose 65.2→96.1°C over 47 min
             Risk score: 0.91

  [WARNING]  Out-of-range
             3 readings exceeded safe bound of 90°C
             Risk score: 0.74

━━━  PHASE 4 · MEMORY  ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  [tool] get_asset_history    2 prior sessions — drift flagged
                              on 2026-02-14 (resolved: bearing re-lubricated)

━━━  PHASE 5 · REPORT  (LLM)  ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

  Fault:          Motor overheating — progressive thermal buildup
  Root cause:     Bearing friction due to inadequate lubrication cycle
  Confidence:     0.91
  Asset risk:     0.91  [CRITICAL]

  Recommendations:
  1. Shut down ConveyorMotorA and allow cooling to ambient temperature
  2. Inspect and re-lubricate bearings — last service was 33 days ago
  3. Check alignment and belt tension — misalignment accelerates heat buildup
  4. Schedule full motor inspection before restart
  5. Set alert threshold to 85°C to catch recurrence earlier

━━━  PHASE 6 · SAVE  ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  Session saved → data/memory/conveyormotora.json

Run time: 4.3s   |   Performance score: 9,180 / 10,000  [Grade S]
```

---

### Scenario 2 — Cooling line flow blockage

**Input:** `data/samples/flow_sensor_blockage.csv`

```
timestamp             tag             value    unit     status
2026-03-18 08:00:00   coolant_flow    45.0     L/min    ok
2026-03-18 08:28:00   coolant_flow    38.6     L/min    ok
2026-03-18 09:04:00   coolant_flow    29.1     L/min    warn
2026-03-18 09:52:00   coolant_flow    18.3     L/min    warn
```

**Command:**
```bash
python main.py --file data/samples/flow_sensor_blockage.csv --asset CoolingLineA
```

**Output:**
```
━━━  PHASE 2 · DETECT  (tool calls)  ━━━━━━━━━━━━━━━━━━━━━━━
  [tool] run_drift_detector           FAULT  59.3% downward drift over 112 min
  [tool] run_out_of_range_detector    WARN   flow dropped below 20 L/min (2 readings)

━━━  PHASE 5 · REPORT  (LLM)  ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

  Fault:          Partial flow blockage — progressive restriction in coolant line
  Root cause:     Particulate buildup or partial valve closure restricting flow
  Confidence:     0.88
  Asset risk:     0.88  [HIGH]

  Recommendations:
  1. Reduce system load immediately to prevent downstream thermal damage
  2. Inspect inline filter and strainer — likely source of restriction
  3. Check isolation valve positions — partial closure may be undetected
  4. Flush coolant line section A-3 through A-7 to clear particulate
  5. Install differential pressure sensor across filter for early detection

Run time: 3.8s   |   Performance score: 8,640 / 10,000  [Grade A]
```

---

### Scenario 3 — Furnace sensor flatline (hardware fault)

**Input:** `data/samples/sensor_spike.csv`

```
timestamp             tag             value    unit   status
2026-03-18 14:00:00   furnace_temp    180.0    °C     ok
2026-03-18 14:02:00   furnace_temp    180.0    °C     ok
  ...  (12 consecutive identical readings over 18 minutes)
2026-03-18 14:18:00   furnace_temp    180.0    °C     ok
```

**Command:**
```bash
python main.py --file data/samples/sensor_spike.csv --asset FurnaceSensorA
```

**Output:**
```
━━━  PHASE 2 · DETECT  (tool calls)  ━━━━━━━━━━━━━━━━━━━━━━━
  [tool] run_flatline_detector        FAULT  12 consecutive identical readings (180.0°C)

━━━  PHASE 4 · MEMORY  ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  [tool] get_asset_history    1 prior session — sensor replaced 2026-01-09
                              (same fault pattern)

━━━  PHASE 5 · REPORT  (LLM)  ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

  Fault:          Sensor failure — stuck reading / frozen output
  Root cause:     Thermocouple or transmitter hardware fault producing frozen output
  Confidence:     0.85
  Asset risk:     0.85  [HIGH]

  Recommendations:
  1. Do not trust current furnace temperature readings — sensor is unreliable
  2. Cross-check against backup thermocouple TC-02B immediately
  3. Replace primary thermocouple on FurnaceSensorA — prior failure on record
  4. Check transmitter wiring and signal conditioning card for faults
  5. Increase flatline detection sensitivity threshold from 5 to 3 readings

Run time: 2.9s   |   Performance score: 7,820 / 10,000  [Grade A]
```

---

### Interactive Q&A mode

After any diagnosis, run with `--interactive` to ask follow-up questions:

```bash
python main.py --file data/samples/conveyor_motor_overheat.csv \
               --asset ConveyorMotorA --interactive
```

```
[IndusDiag] Diagnosis complete. Ask a follow-up question (or 'exit'):

> What is the most likely cause of the temperature rise?

  Based on the 47-minute drift pattern and memory of the prior bearing
  failure on 2026-02-14, the most probable cause is insufficient lubrication
  on the main drive bearing. The progressive (non-spike) temperature increase
  rules out electrical faults and points to mechanical friction buildup.

> How urgent is this compared to the last incident?

  The current risk score (0.91) exceeds the prior incident (0.76). The rate
  of temperature increase is also steeper — 31°C in 47 min vs 24°C in 63 min
  last time. Immediate shutdown is recommended.

> exit
```
