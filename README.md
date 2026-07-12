# ISRO - BAH2026
## Detection and Characterization of Subsurface Ice in Lunar South Polar Regions
### Using Chandrayaan-2 DFSAR Radar and LOLA DEM Data

---

## Bharatiya Antariksh Hackathon 2026 — National Level

**Problem Statement:** PS8 — Lunar South Polar Ice Detection
**Target Crater:** Faustini F2 (87.39 deg S, 82.31 deg E)

---

## Project Overview

A complete end-to-end pipeline for detecting, characterizing, and planning a rover
mission to subsurface water ice deposits in the lunar south polar region, using actual
Chandrayaan-2 DFSAR Level-2 radar products from ISRO PRADAN portal.

Our ice detection independently reproduces results from Sinha et al. 2026:
- Published ice area : 0.564 km2
- Our detected area  : 0.534 km2
- Match accuracy     : 94.6% (5.4% deviation — excellent match)

---

## Key Results

| Metric | Value |
|--------|-------|
| Ice-bearing area (CPR>1 AND DOP<0.13) | 0.534 km2 |
| Published paper value (Sinha 2026) | 0.564 km2 |
| Match accuracy | 94.6% |
| F2 crater diameter | 1,100 m |
| F2 crater depth | 137-151 m |
| Ice volume (conservative, radar-detected) | ~1.07 million m3 |
| Ice volume (geological upper-bound) | ~46.1 million m3 |
| Average ice volume estimate | ~23.6 million m3 |
| Rover path length to ice deposit | 27.9 km |
| Elevation drop along rover path | 171 m |
| Max slope on rover path | 21.2 deg |

---

## Pipeline Phases

### Phase 1 — Data Download & Verification
- Verifies all required Chandrayaan-2 DFSAR and LOLA DEM files are present
- Provides download instructions if files are missing
- Script: `phase1_data_download.py`

### Phase 2 — PSR Shadow Mapping
- Simulates solar illumination from 36 azimuth directions at 1.54 deg sun elevation
- Identifies Permanently Shadowed Regions (PSRs) — never-illuminated areas
- PSRs are critical: temperatures as low as 40K preserve water ice for billions of years
- F2 crater confirmed as PSR (consistent with Hayne et al. 2015 PSR catalog)
- Script: `phase2_shadow_psr_mapping.py`
- Output: `outputs/psr_maps/phase2_psr_mapping.png`

### Phase 3 — CPR/DOP Ice Detection
- Read Chandrayaan-2 DFSAR derived CPR and SRD (DOP) GeoTIFF products
- Applied dual-criterion ice detection: CPR > 1.0 AND DOP < 0.13
- Detected 854 ice pixels = 0.534 km2 ice area
- Script: `phase3_cpr_dop.py`
- Output: `outputs/cpr_maps/phase3_ice_detection.png`

### Phase 4 — Terrain Analysis
- Read LOLA DEM (LDEM_875S_20M.IMG) at 20m/pixel resolution
- Generated slope map using Sobel gradient filter
- Identified safe landing zones (slope less than 10 deg)
- Script: `phase4_terrain.py`
- Output: `outputs/final_maps/phase4_terrain.png`

### Phase 5 — Faustini F2 Crop and Analysis
- Fixed NaN values in CPR/DOP data
- Cropped 10x10 km window around F2 ice cluster centroid
- Generated 4-panel scientific figure: CPR map, DOP map, ice overlay, CPR vs DOP scatter
- Saved georeferenced GeoTIFFs for QGIS visualization
- Script: `phase5_cpr_crop_analysis.py`
- Output: `outputs/cpr_maps/phase5_faustini_F2_analysis.png`

### Phase 6 — A* Rover Path Planning
- A* pathfinding algorithm on LOLA DEM-derived slope and cost grid
- Landing zone: flattest point on crater rim (slope < 0.5 deg)
- Goal: Phase 5 ice mask centroid in real-world coordinates (59m offset verified)
- Path: 27.9 km, 171m elevation drop, max slope 21.2 deg
- Script: `phase6_rover_path_v2.py` (final version targeting ice centroid)
- Output: `outputs/rover_path/phase6_rover_path_v2.png`

### Phase 7 — Ice Volume Estimation
- Scenario A (Conservative): radar penetration depth 5m, 40% ice fraction = 1.07M m3
- Scenario B (Geological upper-bound): full crater depth 144m, 60% ice fraction = 46.1M m3
- Average estimate: 23.6M m3 (~21.6M tonnes)
- Script: `phase7_ice_volume.py`
- Output: `outputs/final_maps/phase7_ice_volume.png`

### Phase 8 — QGIS Visualization
- Loaded F2_cpr_crop.tif with Inferno pseudocolor ramp (CPR 0-2)
- Overlaid F2_ice_mask.tif as cyan transparent layer (ice pixels only)
- Added rover waypoints from rover_waypoints_v2.csv in CRS ESRI:103878
- Map shows CPR heatmap with cyan ice pixels and rover path overlay

---

## Repository Structure

```
BAH2026-lunar-ice/
|
|-- phase1_data_download.py        <- Data verification and download guide
|-- phase2_shadow_psr_mapping.py   <- PSR shadow mapping from DEM
|-- phase3_cpr_dop.py              <- Ice detection (CPR>1 AND DOP<0.13)
|-- phase4_terrain.py              <- LOLA DEM terrain and slope analysis
|-- phase5_cpr_crop_analysis.py    <- NaN fix, F2 crop, 4-panel figure
|-- phase6_rover_path_v1.py        <- A* rover path v1
|-- phase6_rover_path_v2.py        <- A* rover path v2 (targets ice centroid)
|-- phase7_ice_volume.py           <- Dual-scenario ice volume estimation
|
|-- outputs/
|   |-- psr_maps/
|   |   `-- phase2_psr_mapping.png
|   |-- cpr_maps/
|   |   |-- phase3_ice_detection.png
|   |   `-- phase5_faustini_F2_analysis.png
|   |-- final_maps/
|   |   |-- phase4_terrain.png
|   |   `-- phase7_ice_volume.png
|   `-- rover_path/
|       |-- phase6_rover_path.png
|       |-- phase6_rover_path_v2.png
|       |-- rover_waypoints.csv
|       |-- rover_waypoints_geo.csv
|       `-- rover_waypoints_v2.csv
```

---

## Data Sources

| Dataset | Source | Description |
|---------|--------|-------------|
| Chandrayaan-2 DFSAR CPR | ISRO PRADAN (pradan.issdc.gov.in) | Circular Polarization Ratio |
| Chandrayaan-2 DFSAR SRD | ISRO PRADAN (pradan.issdc.gov.in) | Degree of Polarization |
| OHRC Image | ISRO PRADAN (pradan.issdc.gov.in) | Optical High Resolution Camera |
| LOLA DEM | NASA (imbrium.mit.edu) | LDEM_875S_20M — 20m/pixel south pole DEM |

Note: Raw data files are not included in this repository due to size (several GB).
Download from ISRO PRADAN portal and NASA LOLA repository using instructions
provided in phase1_data_download.py

---

## Setup and Installation

```bash
conda create -n lunar_ice python=3.10
conda activate lunar_ice
pip install numpy scipy matplotlib rasterio pyproj python-docx pandas
```

Run scripts from C:\hackathon_lunar (or your project root):

```bash
python phase1_data_download.py
python phase2_shadow_psr_mapping.py
python phase3_cpr_dop.py
python phase4_terrain.py
python phase5_cpr_crop_analysis.py
python phase6_rover_path_v2.py
python phase7_ice_volume.py
```

---

## Ice Detection Criterion

The dual-criterion approach from Sinha et al. 2026:

```
ICE PIXEL = (CPR > 1.0) AND (DOP < 0.13)
```

- CPR > 1.0 : Anomalously high circular polarization ratio indicates
  multiple scattering from subsurface ice (Hapke criterion)
- DOP < 0.13 : Low degree of polarization indicates volume scattering
  consistent with water ice in regolith

---

## PSR Science Background

Permanently Shadowed Regions (PSRs) are critical for lunar ice:
- Sun never rises above crater walls at the south pole (max elevation 1.54 deg)
- Temperatures inside PSRs reach as low as 40 K
- Water ice deposited by comets and asteroids over billions of years is preserved
- Faustini F2 is a sub-crater within the larger Faustini PSR
- Ice confirmed by CPR anomaly (lobate rim morphology = strongest evidence)

---

## Tools Used

- Python  : numpy, scipy, rasterio, matplotlib, pyproj, heapq
- QGIS    : GIS visualization and georeferenced map export
- Data    : ISRO PRADAN portal, NASA LOLA
- Algorithm: A* pathfinding for rover traverse planning

---

## Reference

Sinha, R. K., et al. (2026). Detection and characterization of subsurface ice
in lunar south polar regions using Chandrayaan-2 DFSAR data.
npj Space Exploration.
