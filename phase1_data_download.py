"""
Phase 1 - Data Download Guide & Verification
BAH2026 Problem Statement 8 - Lunar South Polar Ice Detection
Chandrayaan-2 DFSAR + LOLA DEM Data Acquisition

This script verifies that all required data files are present.
Download instructions are provided for each dataset.

Data Sources:
- ISRO PRADAN portal: https://pradan.issdc.gov.in
- NASA LOLA: https://imbrium.mit.edu
"""

import os
import glob

print("="*65)
print("PHASE 1 - DATA VERIFICATION")
print("BAH2026 PS8 | Lunar South Polar Ice Detection")
print("="*65)

# ── Expected file structure ───────────────────────────────────────────────────
EXPECTED = {
    "SAR FP (.dat)": "data/dfsar/data/raw/**/*_fp_*.dat",
    "SAR CP (.dat)": "data/dfsar/data/raw/**/*_cp_*.dat",
    "CPR TIF":       "data/dfsar/**/*_cpr_*.tif",
    "SRD/DOP TIF":   "data/dfsar/**/*_srd_*.tif",
    "OHRC image":    "data/ohrc/**/*.img",
    "LOLA DEM":      "data/dem/LDEM_875S_20M.IMG",
}

print("\nChecking data files...\n")
all_ok = True
for name, pattern in EXPECTED.items():
    files = glob.glob(pattern, recursive=True)
    if files:
        size_mb = sum(os.path.getsize(f) for f in files) / 1024 / 1024
        print(f"  [FOUND] {name}")
        for f in files:
            print(f"          {f}  ({os.path.getsize(f)/1024/1024:.1f} MB)")
    else:
        print(f"  [MISSING] {name}  <- Download required")
        all_ok = False

print()
if all_ok:
    print("All data files present. Ready for Phase 2+")
else:
    print("DOWNLOAD INSTRUCTIONS:")
    print()
    print("1. ISRO PRADAN Portal (Chandrayaan-2 DFSAR):")
    print("   URL    : https://pradan.issdc.gov.in")
    print("   Login  : Register with your email")
    print("   Search : 'ch2_sar_nrxl' → select DFSAR products")
    print("   Select : SAR FP (Full Polarimetry) and SAR CP (Compact Polarimetry)")
    print("   Also   : Download pre-processed Derived Products (CPR, SRD TIFs)")
    print("   Save to: data/dfsar/")
    print()
    print("2. OHRC Image (Chandrayaan-2 Optical):")
    print("   URL    : https://pradan.issdc.gov.in")
    print("   Search : 'ch2_ohr' → select OHRC products")
    print("   Save to: data/ohrc/")
    print()
    print("3. LOLA DEM (NASA Lunar Orbiter Laser Altimeter):")
    print("   URL    : https://imbrium.mit.edu/DATA/LOLA_GDR/POLAR/IMG/")
    print("   File   : LDEM_875S_20M.IMG  (south pole, 20m/pixel)")
    print("   Save to: data/dem/")
    print()
    print("Target coordinates: Faustini F2 Crater")
    print("  Latitude : -87.39 deg S")
    print("  Longitude: 82.31 deg E")
    print("  Diameter : ~1100 m")

print("\n" + "="*65)
print("DATA SUMMARY")
total_size = 0
for root, dirs, files in os.walk("data"):
    for f in files:
        fp = os.path.join(root, f)
        try:
            total_size += os.path.getsize(fp)
        except:
            pass
print(f"  Total data size: {total_size/1024/1024/1024:.2f} GB")
print("="*65)
