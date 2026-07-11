import rasterio
import numpy as np
import matplotlib.pyplot as plt
import os

print("=== Phase 3: CPR Analysis - Derived Product ===")

# Find the CPR tif file
cpr_file = None
for r,d,files in os.walk('data/dfsar'):
    for f in files:
        if '_cpr_' in f and f.endswith('.tif'):
            cpr_file = os.path.join(r,f)
            print('Found CPR file:', cpr_file)

# Also find SRD file (Stokes/DOP related)
srd_file = None
for r,d,files in os.walk('data/dfsar'):
    for f in files:
        if '_srd_' in f and f.endswith('.tif'):
            srd_file = os.path.join(r,f)
            print('Found SRD file:', srd_file)

# Read CPR file
print('\nReading CPR map...')
with rasterio.open(cpr_file) as src:
    print('CRS:', src.crs)
    print('Shape:', src.shape)
    print('Bounds:', src.bounds)
    print('Bands:', src.count)
    print('Resolution:', src.res)
    
    # Read full image
    CPR = src.read(1).astype(float)
    cpr_transform = src.transform
    cpr_crs = src.crs

print('CPR min:', round(CPR.min(), 3))
print('CPR max:', round(CPR.max(), 3))
print('CPR mean:', round(CPR.mean(), 3))
print('Pixels CPR > 1:', np.sum(CPR > 1))
print('CPR > 1 percentage:', round(100*np.sum(CPR > 1)/CPR.size, 2), '%')

# Read SRD file if available
if srd_file:
    print('\nReading SRD map...')
    with rasterio.open(srd_file) as src:
        SRD = src.read(1).astype(float)
    print('SRD min:', round(SRD.min(), 3))
    print('SRD max:', round(SRD.max(), 3))
    print('SRD mean:', round(SRD.mean(), 3))
    
    # DOP from SRD
    DOP = np.clip(SRD, 0, 1)
    ice_mask = (CPR > 1) & (DOP < 0.13)
    print('\nIce pixels (CPR>1 AND DOP<0.13):', np.sum(ice_mask))
    print('Ice %:', round(100*np.sum(ice_mask)/ice_mask.size, 2))
else:
    # Use CPR only
    ice_mask = CPR > 1
    DOP = np.zeros_like(CPR)

# Plot
fig, axes = plt.subplots(1, 3, figsize=(18, 6))

im0 = axes[0].imshow(np.clip(CPR, 0, 2), cmap='hot', aspect='auto')
axes[0].set_title('CPR Map - Lunar South Polar\n(Red/Yellow = CPR>1, ice candidate)')
plt.colorbar(im0, ax=axes[0], label='CPR')

im1 = axes[1].imshow(np.clip(DOP, 0, 1), cmap='coolwarm_r', aspect='auto')
axes[1].set_title('DOP/SRD Map\n(Blue = volume scattering)')
plt.colorbar(im1, ax=axes[1])

axes[2].imshow(ice_mask, cmap='Blues', aspect='auto')
axes[2].set_title('Ice Detection Map\n(CPR>1 AND DOP<0.13)')

plt.suptitle('Phase 3: Subsurface Ice Detection\nChandrayaan-2 DFSAR Derived Product - South Polar Mosaic',
             fontsize=12, fontweight='bold')
plt.tight_layout()
plt.savefig('outputs/cpr_maps/phase3_ice_detection.png', dpi=150)
plt.show()
print('\nSaved to outputs/cpr_maps/phase3_ice_detection.png')