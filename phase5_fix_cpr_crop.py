"""
Phase 5 - Fix NaN + Crop to Faustini F2
BAH2026 | Chandrayaan-2 DFSAR Ice Detection
"""
import numpy as np
import rasterio
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.colors import LinearSegmentedColormap
import os
import glob

os.makedirs("outputs/cpr_maps", exist_ok=True)
os.makedirs("outputs/cropped", exist_ok=True)

# 1. Find TIF files
cpr_files = glob.glob("data/dfsar/**/*_cpr_*.tif", recursive=True) + \
            glob.glob("data/dfsar/**/*cpr*.tif", recursive=True)
srd_files = glob.glob("data/dfsar/**/*_srd_*.tif", recursive=True) + \
            glob.glob("data/dfsar/**/*srd*.tif", recursive=True)

if not cpr_files: raise FileNotFoundError("No CPR TIF found under data/dfsar/")
if not srd_files: raise FileNotFoundError("No SRD/DOP TIF found under data/dfsar/")

cpr_path = cpr_files[0]
dop_path = srd_files[0]
print(f"CPR file: {cpr_path}")
print(f"DOP file: {dop_path}")

# 2. Read CPR
with rasterio.open(cpr_path) as src:
    cpr_data = src.read(1).astype(np.float32)
    cpr_nodata = src.nodata
    cpr_transform = src.transform
    cpr_crs = src.crs
    cpr_meta = src.meta.copy()
    cpr_bounds = src.bounds
    print(f"CPR shape: {cpr_data.shape}")

if cpr_nodata is not None:
    cpr_data[cpr_data == cpr_nodata] = np.nan
cpr_data[cpr_data <= 0] = np.nan
cpr_data[cpr_data > 10] = np.nan
print(f"CPR valid pixels: {np.sum(~np.isnan(cpr_data)):,}")
print(f"CPR range: {np.nanmin(cpr_data):.4f} to {np.nanmax(cpr_data):.4f}")
print(f"CPR > 1.0: {np.sum(cpr_data > 1.0):,}")

# 3. Read DOP
with rasterio.open(dop_path) as src:
    dop_data = src.read(1).astype(np.float32)
    dop_nodata = src.nodata

if dop_nodata is not None:
    dop_data[dop_data == dop_nodata] = np.nan
dop_data[dop_data < 0] = np.nan
dop_data[dop_data > 1] = np.nan
print(f"DOP valid pixels: {np.sum(~np.isnan(dop_data)):,}")

# 4. Ice detection (full scene)
ice_mask_full = (cpr_data > 1.0) & (dop_data < 0.13) & \
                ~np.isnan(cpr_data) & ~np.isnan(dop_data)
n_ice_full = np.sum(ice_mask_full)
area_full_km2 = n_ice_full * (25 * 25) / 1e6
print(f"\nIce pixels: {n_ice_full:,}  |  Ice area: {area_full_km2:.3f} km2  (paper: 0.564)")

# 5. Crop to Faustini F2 using direct pixel coordinates
# The CPR image covers the lunar south pole in stereographic projection
# F2 is near image center — use the image center as F2 proxy
# OR compute from transform directly without pyproj

# Get image center in projected coords
img_rows, img_cols = cpr_data.shape
center_x = cpr_transform.c + (img_cols / 2) * cpr_transform.a
center_y = cpr_transform.f + (img_rows / 2) * cpr_transform.e
print(f"\nImage projected center: X={center_x:.1f}, Y={center_y:.1f}")
print(f"Image pixel size: {cpr_transform.a:.1f} m")

# Find highest CPR density region (where ice pixels cluster) as F2 proxy
# Smooth ice mask and find centroid
from scipy.ndimage import label, center_of_mass, uniform_filter
ice_smooth = uniform_filter(ice_mask_full.astype(float), size=20)
max_pos = np.unravel_index(np.argmax(ice_smooth), ice_smooth.shape)
row_center, col_center = max_pos
print(f"Highest ice density at pixel: row={row_center}, col={col_center}")

# Buffer = 5km = 200 pixels at 25m/px
BUFFER_M = 5000
buf_px = int(BUFFER_M / abs(cpr_transform.a))

r0 = max(0, row_center - buf_px)
r1 = min(cpr_data.shape[0], row_center + buf_px)
c0 = max(0, col_center - buf_px)
c1 = min(cpr_data.shape[1], col_center + buf_px)

cpr_crop = cpr_data[r0:r1, c0:c1]
dop_crop = dop_data[r0:r1, c0:c1]
ice_crop  = ice_mask_full[r0:r1, c0:c1]

n_ice_crop = np.sum(ice_crop)
area_crop_km2 = n_ice_crop * (25 * 25) / 1e6
print(f"Crop shape: {cpr_crop.shape}")
print(f"F2 region ice: {n_ice_crop:,} px  |  {area_crop_km2:.3f} km2")

# 6. Save cropped GeoTIFFs
new_transform = rasterio.transform.from_bounds(
    cpr_bounds.left + c0 * cpr_transform.a,
    cpr_bounds.top  + r1 * cpr_transform.e,
    cpr_bounds.left + c1 * cpr_transform.a,
    cpr_bounds.top  + r0 * cpr_transform.e,
    cpr_crop.shape[1], cpr_crop.shape[0]
)
out_meta = cpr_meta.copy()
out_meta.update({"height": cpr_crop.shape[0], "width": cpr_crop.shape[1],
                 "transform": new_transform, "nodata": -9999.0, "dtype": "float32"})

with rasterio.open("outputs/cropped/F2_cpr_crop.tif", "w", **out_meta) as dst:
    dst.write(np.nan_to_num(cpr_crop, nan=-9999.0).astype(np.float32), 1)
print("Saved: outputs/cropped/F2_cpr_crop.tif")

with rasterio.open("outputs/cropped/F2_dop_crop.tif", "w", **out_meta) as dst:
    dst.write(np.nan_to_num(dop_crop, nan=-9999.0).astype(np.float32), 1)
print("Saved: outputs/cropped/F2_dop_crop.tif")

ice_meta = out_meta.copy()
ice_meta.update({"dtype": "uint8", "nodata": 255})
with rasterio.open("outputs/cropped/F2_ice_mask.tif", "w", **ice_meta) as dst:
    dst.write(ice_crop.astype(np.uint8), 1)
print("Saved: outputs/cropped/F2_ice_mask.tif")

# 7. 4-panel figure
fig, axes = plt.subplots(2, 2, figsize=(14, 12), facecolor='#0a0a1a')
fig.suptitle("Faustini F2 Crater - Ice Detection\nBAH2026 | Chandrayaan-2 DFSAR",
             color='white', fontsize=14, fontweight='bold', y=0.98)
ext = [-BUFFER_M/1000, BUFFER_M/1000, -BUFFER_M/1000, BUFFER_M/1000]

# Panel 1: CPR
ax = axes[0,0]
ax.set_facecolor('#0a0a1a')
im = ax.imshow(cpr_crop, cmap='inferno', vmin=0, vmax=2.0, extent=ext, origin='upper')
cb = fig.colorbar(im, ax=ax, fraction=0.046, pad=0.04)
cb.set_label('CPR', color='white', fontsize=9)
cb.ax.yaxis.set_tick_params(color='white')
plt.setp(cb.ax.yaxis.get_ticklabels(), color='white')
if not np.all(np.isnan(cpr_crop)):
    ax.contour(cpr_crop, levels=[1.0], colors='lime', linewidths=1.5, extent=ext, origin='upper')
ax.set_title('CPR Map  (lime = CPR > 1.0)', color='white', fontsize=10)
ax.set_xlabel('km from F2 center', color='white', fontsize=8)
ax.set_ylabel('km from F2 center', color='white', fontsize=8)
ax.tick_params(colors='white')
for sp in ax.spines.values(): sp.set_edgecolor('white')

# Panel 2: DOP
ax = axes[0,1]
ax.set_facecolor('#0a0a1a')
im = ax.imshow(dop_crop, cmap='coolwarm_r', vmin=0, vmax=0.3, extent=ext, origin='upper')
cb = fig.colorbar(im, ax=ax, fraction=0.046, pad=0.04)
cb.set_label('DOP', color='white', fontsize=9)
cb.ax.yaxis.set_tick_params(color='white')
plt.setp(cb.ax.yaxis.get_ticklabels(), color='white')
if not np.all(np.isnan(dop_crop)):
    ax.contour(dop_crop, levels=[0.13], colors='yellow', linewidths=1.5, extent=ext, origin='upper')
ax.set_title('DOP Map  (yellow = DOP < 0.13)', color='white', fontsize=10)
ax.set_xlabel('km from F2 center', color='white', fontsize=8)
ax.set_ylabel('km from F2 center', color='white', fontsize=8)
ax.tick_params(colors='white')
for sp in ax.spines.values(): sp.set_edgecolor('white')

# Panel 3: Ice overlay
ax = axes[1,0]
ax.set_facecolor('#0a0a1a')
ax.imshow(cpr_crop, cmap='gray', vmin=0, vmax=2.0, alpha=0.7, extent=ext, origin='upper')
ice_ov = np.ma.masked_where(~ice_crop, np.ones_like(ice_crop, dtype=float))
ax.imshow(ice_ov, cmap=LinearSegmentedColormap.from_list('ic', ['cyan','white']),
          alpha=0.85, extent=ext, origin='upper')
ax.set_title(f'Ice Pixels: CPR>1 AND DOP<0.13\nArea = {area_crop_km2:.3f} km2  (Paper: 0.564 km2)',
             color='white', fontsize=9)
ax.set_xlabel('km from F2 center', color='white', fontsize=8)
ax.set_ylabel('km from F2 center', color='white', fontsize=8)
ax.tick_params(colors='white')
for sp in ax.spines.values(): sp.set_edgecolor('white')
ax.legend(handles=[mpatches.Patch(color='cyan', label=f'Ice n={n_ice_crop:,}'),
                   mpatches.Patch(color='gray', alpha=0.7, label='Non-ice')],
          loc='lower right', fontsize=8, facecolor='#1a1a2e',
          edgecolor='white', labelcolor='white')

# Panel 4: CPR vs DOP scatter
ax = axes[1,1]
ax.set_facecolor('#0d0d1f')
valid = ~np.isnan(cpr_crop) & ~np.isnan(dop_crop)
cv = cpr_crop[valid].ravel()
dv = dop_crop[valid].ravel()
iv = ice_crop[valid].ravel()
idx = np.random.choice(len(cv), size=min(30000, len(cv)), replace=False)
ax.scatter(cv[idx][~iv[idx]], dv[idx][~iv[idx]], s=0.3, c='steelblue', alpha=0.3, label='Non-ice')
ax.scatter(cv[idx][iv[idx]], dv[idx][iv[idx]], s=5, c='cyan', alpha=0.9, label=f'Ice n={n_ice_crop:,}')
ax.axvline(1.0, color='lime', lw=1.5, ls='--', label='CPR=1.0')
ax.axhline(0.13, color='yellow', lw=1.5, ls='--', label='DOP=0.13')
ax.set_xlim(0, 2.5); ax.set_ylim(0, 0.5)
ax.set_xlabel('CPR', color='white', fontsize=9)
ax.set_ylabel('DOP', color='white', fontsize=9)
ax.set_title('CPR vs DOP  (ice = upper-left zone)', color='white', fontsize=10)
ax.tick_params(colors='white')
ax.legend(loc='upper right', fontsize=8, facecolor='#1a1a2e',
          edgecolor='white', labelcolor='white', markerscale=5)
for sp in ax.spines.values(): sp.set_edgecolor('#444')

plt.tight_layout(rect=[0,0,1,0.96])
plt.savefig("outputs/cpr_maps/phase5_faustini_F2_analysis.png",
            dpi=150, bbox_inches='tight', facecolor='#0a0a1a')
plt.close()
print("Saved: outputs/cpr_maps/phase5_faustini_F2_analysis.png")
print("="*55)
print("PHASE 5 COMPLETE")
print(f"  Full-scene ice area : {area_full_km2:.3f} km2")
print(f"  F2-crop ice area    : {area_crop_km2:.3f} km2")
print(f"  Paper (Sinha 2026)  : 0.564 km2")
print(f"  Deviation           : {abs(area_full_km2-0.564)/0.564*100:.1f}%")
print("="*55)