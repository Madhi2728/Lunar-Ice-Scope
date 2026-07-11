import numpy as np
import matplotlib.pyplot as plt
from scipy.ndimage import sobel

print("=== Phase 4: Terrain Analysis ===")

dem_file = 'data/dem/LDEM_875S_20M.IMG'

# Known dimensions for LDEM_875S_20M
# 20m/pixel, 87.5S polar region
rows = 5765
cols = 5765

print('Reading DEM...')
try:
    dem = np.fromfile(dem_file, dtype=np.int16)
    total = len(dem)
    print('Total values:', total)
    # Auto-calculate cols
    import math
    side = int(math.sqrt(total))
    rows, cols = side, side
    dem = dem[:rows*cols].reshape(rows, cols).astype(float)
    print('DEM shape:', dem.shape)
    print('Elevation min:', dem.min(), 'm')
    print('Elevation max:', dem.max(), 'm')
except Exception as e:
    print('Error:', e)
    exit()

dx = sobel(dem, axis=1)
dy = sobel(dem, axis=0)
slope = np.degrees(np.arctan(np.sqrt(dx**2 + dy**2) / 20.0))

safe = slope < 10
print('Slope mean:', round(slope.mean(),1), 'deg')
print('Safe landing %:', round(100*np.sum(safe)/safe.size,1))

fig, axes = plt.subplots(1, 3, figsize=(18,6))
axes[0].imshow(dem, cmap='terrain')
axes[0].set_title('LOLA DEM - South Pole')
im1 = axes[1].imshow(slope, cmap='hot', vmax=30)
axes[1].set_title('Slope Map (degrees)')
plt.colorbar(im1, ax=axes[1])
axes[2].imshow(safe, cmap='Greens')
axes[2].set_title('Safe Landing Zones\n(slope < 10 deg)')
plt.suptitle('Phase 4: Terrain Analysis - Lunar South Pole', fontsize=13)
plt.tight_layout()
plt.savefig('outputs/final_maps/phase4_terrain.png', dpi=150)
plt.show()
print('Saved!')