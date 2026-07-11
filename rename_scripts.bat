@echo off
:: BAH2026 - Rename all phase scripts to consistent naming convention
:: Run from C:\hackathon_lunar in Command Prompt or Anaconda Prompt

echo Renaming phase scripts to consistent names...

:: Phase 5 - already correct
:: phase5_fix_cpr_crop.py -> phase5_cpr_crop_analysis.py
ren phase5_fix_cpr_crop.py phase5_cpr_crop_analysis.py
echo Renamed: phase5_fix_cpr_crop.py -> phase5_cpr_crop_analysis.py

:: Phase 6 v1
:: phase6_astar_rover.py -> phase6_rover_path_v1.py
ren phase6_astar_rover.py phase6_rover_path_v1.py
echo Renamed: phase6_astar_rover.py -> phase6_rover_path_v1.py

:: Phase 6 v2 (final version - targets ice centroid)
:: phase6_astar_rover_v2.py -> phase6_rover_path_v2.py
ren phase6_astar_rover_v2.py phase6_rover_path_v2.py
echo Renamed: phase6_astar_rover_v2.py -> phase6_rover_path_v2.py

:: Phase 2 (if old name exists)
if exist phase2_shadow_mapping.py (
    ren phase2_shadow_mapping.py phase2_shadow_mapping_old.py
    echo Renamed: phase2_shadow_mapping.py -> phase2_shadow_mapping_old.py
)

echo.
echo Done! New file listing:
dir *.py /b

echo.
echo Now run:
echo   git add .
echo   git commit -m "Rename scripts to consistent naming convention"
echo   git push
