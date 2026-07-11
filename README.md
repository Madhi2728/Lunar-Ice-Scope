**Hackathon:** Bharatiya Antariksh Hackathon 2026 — National Level  
**Problem Statement:** PS8 — Lunar South Polar Ice Detection

## 🌕 Project Overview

A complete end-to-end pipeline for detecting, characterizing, and planning a rover
mission to subsurface water ice deposits in the lunar south polar region, using actual
Chandrayaan-2 DFSAR Level-2 radar products from ISRO's PRADAN portal.

Our ice detection independently reproduces results from:
> Sinha et al. 2026, *npj Space Exploration* — Faustini F2 ice area: **0.564 km²**
> Our result: **0.534 km²** (5.4% deviation — excellent match)

---

## 📊 Key Results

| Metric | Value |
|--------|-------|
| Ice-bearing area (CPR>1 AND DOP<0.13) | 0.534 km² |
| Published paper value (Sinha 2026) | 0.564 km² |
| Match accuracy | 94.6% |
| F2 crater diameter | 1,100 m |
| F2 crater depth | 137–151 m |
| Ice volume (conservative, radar-detected) | ~1.07 million m³ |
| Ice volume (geological upper-bound) | ~46.1 million m³ |
| Average ice volume estimate | ~23.6 million m³ |
| Rover path length to ice deposit | 27.9 km |
| Elevation drop along rover path | 171 m |
| Max slope on rover path | 21.2° |

---

## 🛠️ Pipeline Phases

### Phase 3 — CPR/DOP Ice Detection
- Read Chandrayaan-2 DFSAR derived CPR and SRD (DOP) GeoTIFF products
- Applied dual-criterion ice detection: **CPR > 1.0 AND DOP < 0.13**
- Detected 854 ice pixels → 0.534 km² ice area
- Script: `phase3_cpr_dop.py`

### Phase 4 — Terrain Analysis
- Read LOLA DEM (LDEM_875S_20M.IMG) at 20m/pixel
- Generated slope map using Sobel gradient filter
- Identified safe landing zones (slope < 10°)
- Script: `phase4_terrain.py`

### Phase 5 — Faustini F2 Crop & Analysis
- Fixed NaN values in CPR/DOP data
- Cropped 10×10 km window around F2 ice cluster centroid
- Generated 4-panel scientific figure: CPR map, DOP map, ice overlay, CPR vs DOP scatter
- Saved georeferenced GeoTIFFs for QGIS visualization
- Script: `phase5_fix_cpr_crop.py`

### Phase 6 — A* Rover Path Planning
- A* pathfinding algorithm on LOLA DEM-derived slope/cost grid
- Landing zone: flattest point on crater rim (slope < 0.5°)
- Goal: Phase 5 ice mask centroid (real-world coordinates, 59m offset verified)
- Path: 27.9 km, 171m elevation drop, max slope 21.2°
- Script: `phase6_astar_rover_v2.py`

### Phase 7 — Ice Volume Estimation
- Scenario A (Conservative): radar penetration depth 5m, 40% ice fraction → 1.07M m³
- Scenario B (Geological upper-bound): full crater depth 144m, 60% ice fraction → 46.1M m³
- Average estimate: 23.6M m³ (~21.6M tonnes)
- Script: `phase7_ice_volume.py`

### Phase 8 — QGIS Visualization
- Loaded F2_cpr_crop.tif with Inferno pseudocolor ramp (CPR 0–2)
- Overlaid F2_ice_mask.tif as cyan transparent layer (ice pixels only)
- Added rover waypoints from rover_waypoints_v2.csv in matching CRS (ESRI:103878)
- Exported final map at 300 DPI

---

## 📁 Repository Structure