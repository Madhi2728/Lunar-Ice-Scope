"""
Phase 6 v2 - A* Rover Path Planning - TARGETS ACTUAL ICE MASK CENTROID
BAH2026 | Rover path now explicitly targets the Phase 5 detected ice pixels
Landing zone OUTSIDE crater rim -> descent to actual ice deposit location
"""
import numpy as np
import heapq, math
import rasterio
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from scipy.ndimage import sobel, gaussian_filter, center_of_mass
import os

os.makedirs("outputs/rover_path", exist_ok=True)

# ── 1. Load the ice mask from Phase 5 to find its REAL geo-coordinates ───────
print("Loading ice mask from Phase 5...")
with rasterio.open("outputs/cropped/F2_ice_mask.tif") as src:
    ice_mask = src.read(1).astype(bool)
    ice_transform = src.transform
    ice_crs = src.crs

ice_rows, ice_cols = np.where(ice_mask)
if len(ice_rows) == 0:
    raise ValueError("No ice pixels found in mask!")

# Centroid of ice pixels in the CROPPED ice mask's own pixel space
centroid_row = ice_rows.mean()
centroid_col = ice_cols.mean()

# Convert that centroid to REAL WORLD coordinates using ice mask's transform
ice_target_x, ice_target_y = ice_transform * (centroid_col, centroid_row)
print(f"Ice centroid (pixel space): row={centroid_row:.1f}, col={centroid_col:.1f}")
print(f"Ice centroid (real-world coords): X={ice_target_x:.1f}, Y={ice_target_y:.1f}")
print(f"Ice mask CRS: {ice_crs}")

# ── 2. Load DEM exactly like phase4/phase6 v1 ────────────────────────────────
dem_file = 'data/dem/LDEM_875S_20M.IMG'
print('\nReading DEM...')
dem = np.fromfile(dem_file, dtype=np.int16)
total = len(dem)
side = int(math.sqrt(total))
dem = dem[:side*side].reshape(side, side).astype(float)
print(f'DEM shape: {dem.shape}, range: {dem.min():.0f} to {dem.max():.0f} m')
pixel_m = 20.0

# ── 3. Slope (corrected Sobel normalization) ─────────────────────────────────
dx = sobel(dem, axis=1)
dy = sobel(dem, axis=0)
slope = np.degrees(np.arctan(np.sqrt(dx**2 + dy**2) / (8.0 * pixel_m)))
print(f'Slope range: {slope.min():.1f} to {slope.max():.1f} deg')

# ── 4. CRITICAL STEP: Convert ice target real-world coords -> DEM pixel coords
# The DEM is centered on the south pole (90S at image center), 20m/pixel.
# We need the DEM's own affine transform. Since np.fromfile has no georeference,
# we reconstruct it the same way as the official LOLA south-pole product:
# image center = (-90, 0) i.e. the pole, at pixel (side/2, side/2)
H, W = dem.shape
dem_center_row, dem_center_col = H/2, W/2

# The CPR/ice products use Moon_2000_South_Pole_Stereographic with the SAME
# pole-centered convention. So real-world (X,Y) in meters from the pole maps
# directly to DEM pixel offsets at 20m/pixel:
#   col = center_col + X/pixel_m
#   row = center_row - Y/pixel_m   (Y increases northward = row decreases)
target_col = dem_center_col + (ice_target_x / pixel_m)
target_row = dem_center_row - (ice_target_y / pixel_m)
print(f"\nIce target mapped to DEM pixel coords: row={target_row:.0f}, col={target_col:.0f}")

floor_abs = (int(round(target_row)), int(round(target_col)))
floor_abs = (max(0, min(H-1, floor_abs[0])), max(0, min(W-1, floor_abs[1])))
floor_elev = dem[floor_abs]
print(f"DEM elevation at ice target: {floor_elev:.0f} m")

# ── 5. Crop 800x800px (16x16 km) centred on the ICE TARGET (not DEM minimum) ─
HALF = 400
r0 = max(0, floor_abs[0]-HALF)
r1 = min(H, floor_abs[0]+HALF)
c0 = max(0, floor_abs[1]-HALF)
c1 = min(W, floor_abs[1]+HALF)
dem_s   = dem[r0:r1, c0:c1]
slope_s = slope[r0:r1, c0:c1]
sH, sW  = dem_s.shape
print(f'Crop: {dem_s.shape} = {sH*pixel_m/1000:.1f}x{sW*pixel_m/1000:.1f} km')
print(f'Crop elev: {dem_s.min():.0f} to {dem_s.max():.0f} m')

# Goal in cropped coords = the ice target itself
goal = (floor_abs[0]-r0, floor_abs[1]-c0)
print(f'Goal (ice target): row={goal[0]}, col={goal[1]}, elev={dem_s[goal]:.0f}m, '
      f'slope={slope_s[goal]:.1f}deg')

# If the exact ice pixel has bad slope/elev data, snap to nearest low-slope cell nearby
if slope_s[goal] > 30 or np.isnan(dem_s[goal]):
    print("Ice target cell has poor terrain data, snapping to nearest safe cell...")
    search_r = 15
    best = None
    best_d = 1e9
    gr, gc = goal
    for dr in range(-search_r, search_r+1):
        for dc in range(-search_r, search_r+1):
            rr, cc = gr+dr, gc+dc
            if 0 <= rr < sH and 0 <= cc < sW:
                if slope_s[rr,cc] < 20 and not np.isnan(dem_s[rr,cc]):
                    d = dr*dr+dc*dc
                    if d < best_d:
                        best_d = d
                        best = (rr,cc)
    if best:
        goal = best
        print(f"Snapped goal to: {goal}, elev={dem_s[goal]:.0f}m, slope={slope_s[goal]:.1f}deg")

# ── 6. Start = safest point on crater RIM around this goal ───────────────────
floor_elev = dem_s[goal]
rim_mask = np.zeros_like(dem_s, dtype=bool)
for r in range(sH):
    for c in range(sW):
        dist = math.hypot(r-goal[0], c-goal[1])
        if 60 <= dist <= 150:
            if dem_s[r,c] > floor_elev + 300 and slope_s[r,c] < 15:
                rim_mask[r,c] = True

if rim_mask.sum() == 0:
    print("No rim candidates found, relaxing criteria...")
    for r in range(sH):
        for c in range(sW):
            dist = math.hypot(r-goal[0], c-goal[1])
            if 40 <= dist <= 200 and dem_s[r,c] > floor_elev+100:
                rim_mask[r,c] = True

slope_rim = slope_s.copy()
slope_rim[~rim_mask] = 9999
start = np.unravel_index(np.argmin(slope_rim), slope_rim.shape)
print(f'Start (rim landing): {start}, elev={dem_s[start]:.0f}m, slope={slope_s[start]:.1f}deg')

# ── 7. Cost grid ─────────────────────────────────────────────────────────────
cost = np.ones_like(slope_s)
cost[slope_s >  8]  = 3.0
cost[slope_s > 12]  = 8.0
cost[slope_s > 18]  = 30.0
cost[slope_s > 22]  = 200.0
cost[slope_s > 28]  = 9999.0
cost[np.isnan(dem_s)] = 9999.0

# ── 8. A* ────────────────────────────────────────────────────────────────────
def astar(cg, s, g):
    H,W = cg.shape
    dirs  = [(-1,0),(1,0),(0,-1),(0,1),(-1,-1),(-1,1),(1,-1),(1,1)]
    mults = [1,1,1,1,1.414,1.414,1.414,1.414]
    heap  = [(0.0, s)]
    gscore= {s:0.0}
    came  = {}
    seen  = set()
    while heap:
        _,cur = heapq.heappop(heap)
        if cur in seen: continue
        seen.add(cur)
        if cur==g:
            path=[]
            while cur in came: path.append(cur); cur=came[cur]
            path.append(s); return path[::-1]
        for (dr,dc),m in zip(dirs,mults):
            nr,nc = cur[0]+dr, cur[1]+dc
            if 0<=nr<H and 0<=nc<W and (nr,nc) not in seen:
                sc = cg[nr,nc]*m
                if sc>=990: continue
                ng = gscore[cur]+sc
                if ng < gscore.get((nr,nc),1e18):
                    came[(nr,nc)]=cur
                    gscore[(nr,nc)]=ng
                    heapq.heappush(heap,(ng+math.hypot(nr-g[0],nc-g[1]),(nr,nc)))
    return None

print('\nRunning A*...')
path = astar(cost, start, goal)
if path is None:
    print('A* blocked, using gradient-descent fallback')
    path = [start]
    cur = start
    visited = {start}
    dirs = [(-1,0),(1,0),(0,-1),(0,1),(-1,-1),(-1,1),(1,-1),(1,1)]
    for _ in range(10000):
        if cur == goal: break
        best_next, best_score = None, 1e18
        for dr,dc in dirs:
            nr,nc = cur[0]+dr, cur[1]+dc
            if 0<=nr<sH and 0<=nc<sW and (nr,nc) not in visited:
                if slope_s[nr,nc] < 25:
                    score = math.hypot(nr-goal[0],nc-goal[1]) + slope_s[nr,nc]*2
                    if score < best_score:
                        best_score=score; best_next=(nr,nc)
        if best_next is None: break
        path.append(best_next); visited.add(best_next); cur = best_next
    print(f'Gradient descent path: {len(path)} nodes')
else:
    print(f'A* path: {len(path)} nodes')

pa = np.array(path)
dists   = np.hypot(np.diff(pa[:,0]), np.diff(pa[:,1])) * pixel_m/1000
path_km = float(np.sum(dists))
cum_d   = np.concatenate([[0], np.cumsum(dists)])
pslopes = [float(slope_s[p[0],p[1]]) for p in path]
elevs   = [float(dem_s[p[0],p[1]])   for p in path]
elev_drop = elevs[0]-elevs[-1]

print(f'\nPath: {path_km:.2f} km | Drop: {elev_drop:.0f}m | MaxSlope: {max(pslopes):.1f}deg')
print(f'Traverse: ~{path_km/0.1:.0f} hrs @ 0.1 km/h')

# ── 9. Save CSV with BOTH pixel coords AND real-world X/Y (matching ice CRS) ──
def pix_to_world(row, col):
    # local crop pixel -> DEM absolute pixel -> real world (same convention as ice mask)
    abs_row = row + r0
    abs_col = col + c0
    x = (abs_col - dem_center_col) * pixel_m
    y = (dem_center_row - abs_row) * pixel_m
    return x, y

step = max(1,len(path)//50)
with open("outputs/rover_path/rover_waypoints_v2.csv","w") as f:
    f.write("wp,row,col,X,Y,cum_km,slope_deg,elev_m\n")
    for i,p in enumerate(path[::step]):
        x,y = pix_to_world(p[0], p[1])
        f.write(f"{i},{p[0]},{p[1]},{x:.2f},{y:.2f},"
                f"{cum_d[min(i*step,len(cum_d)-1)]:.3f},"
                f"{slope_s[p[0],p[1]]:.2f},{dem_s[p[0],p[1]]:.1f}\n")
print("Saved: outputs/rover_path/rover_waypoints_v2.csv")

# Verify alignment with ice mask bounds
gx, gy = pix_to_world(goal[0], goal[1])
print(f"\nVerification - Goal real-world coords: X={gx:.1f}, Y={gy:.1f}")
print(f"Original ice centroid coords        : X={ice_target_x:.1f}, Y={ice_target_y:.1f}")
print(f"Offset: {math.hypot(gx-ice_target_x, gy-ice_target_y):.1f} m (should be small)")

# ── 10. Plot ──────────────────────────────────────────────────────────────────
km = pixel_m/1000
ext = [0, sW*km, sH*km, 0]
fig, axes = plt.subplots(1,3,figsize=(18,6),facecolor='#0a0a1a')
fig.suptitle(f"Rover Path to Detected Ice Zone — Faustini F2 Crater | BAH2026\n"
             f"A* on LOLA DEM | Target = Phase 5 Ice Mask Centroid | {path_km:.1f} km | Drop {elev_drop:.0f}m",
             color='white', fontsize=12.5, fontweight='bold')

ax=axes[0]; ax.set_facecolor('#0a0a1a')
im=ax.imshow(dem_s, cmap='terrain', origin='upper', extent=ext, aspect='equal')
cb=fig.colorbar(im,ax=ax,fraction=0.046,pad=0.04)
cb.set_label('Elevation (m)',color='white',fontsize=8)
cb.ax.yaxis.set_tick_params(color='white')
plt.setp(cb.ax.yaxis.get_ticklabels(),color='white')
ax.plot(pa[:,1]*km, pa[:,0]*km,'y-',lw=2.5,alpha=0.95,label='Rover path',zorder=4)
ax.plot(start[1]*km,start[0]*km,'g^',ms=14,zorder=5,
        label=f'Landing (slope={slope_s[start]:.1f}°)')
ax.plot(goal[1]*km, goal[0]*km, 'c*',ms=18,zorder=5,
        label='Ice deposit (Phase 5 target)')
ax.set_title(f'DEM + Rover Path ({path_km:.1f} km)', color='white', fontsize=10)
ax.set_xlabel('km', color='white', fontsize=9)
ax.set_ylabel('km', color='white', fontsize=9)
ax.tick_params(colors='white')
for sp in ax.spines.values(): sp.set_edgecolor('white')
ax.legend(fontsize=7,facecolor='#1a1a2e',edgecolor='white',labelcolor='white')

ax=axes[1]; ax.set_facecolor('#0a0a1a')
im2=ax.imshow(slope_s,cmap='RdYlGn_r',vmin=0,vmax=25,
              origin='upper',extent=ext,aspect='equal')
cb2=fig.colorbar(im2,ax=ax,fraction=0.046,pad=0.04)
cb2.set_label('Slope (°)',color='white',fontsize=8)
cb2.ax.yaxis.set_tick_params(color='white')
plt.setp(cb2.ax.yaxis.get_ticklabels(),color='white')
safe_ov=np.ma.masked_where(slope_s>=10,np.ones_like(slope_s))
ax.imshow(safe_ov,cmap='cool',alpha=0.5,origin='upper',extent=ext,aspect='equal')
ax.plot(pa[:,1]*km,pa[:,0]*km,'w-',lw=2.5,alpha=0.9,label='Path')
ax.plot(start[1]*km,start[0]*km,'g^',ms=14,zorder=5,label='Landing')
ax.plot(goal[1]*km, goal[0]*km, 'c*',ms=18,zorder=5,label='Ice target')
ax.set_title('Slope Map (blue=safe <10°)', color='white', fontsize=10)
ax.set_xlabel('km',color='white',fontsize=9)
ax.set_ylabel('km',color='white',fontsize=9)
ax.tick_params(colors='white')
for sp in ax.spines.values(): sp.set_edgecolor('white')
ax.legend(fontsize=7,facecolor='#1a1a2e',edgecolor='white',labelcolor='white')

ax=axes[2]; ax.set_facecolor('#0d0d1f')
ax.fill_between(cum_d,elevs,min(elevs),color='saddlebrown',alpha=0.6)
ax.plot(cum_d,elevs,'w-',lw=2)
ax.axhline(elevs[0], color='lime',ls='--',lw=1.5,label=f'Start {elevs[0]:.0f}m')
ax.axhline(elevs[-1],color='cyan', ls='--',lw=1.5,label=f'Ice target {elevs[-1]:.0f}m')
max_slope_idx = int(np.argmax(pslopes))
ax.axvline(cum_d[max_slope_idx],color='orange',ls=':',lw=1.2,
           label=f'Max slope {max(pslopes):.1f}°')
ax.set_xlabel('Distance (km)',color='white',fontsize=9)
ax.set_ylabel('Elevation (m)',color='white',fontsize=9)
ax.set_title(f'Elevation Profile\nDrop {elev_drop:.0f}m | {path_km:.1f}km | ~{path_km/0.1:.0f}h',
             color='white',fontsize=10)
ax.tick_params(colors='white')
for sp in ax.spines.values(): sp.set_edgecolor('#444')
ax.legend(fontsize=8,facecolor='#1a1a2e',edgecolor='white',labelcolor='white')

plt.tight_layout()
plt.savefig("outputs/rover_path/phase6_rover_path_v2.png",
            dpi=150,bbox_inches='tight',facecolor='#0a0a1a')
plt.close()
print("\nSaved: outputs/rover_path/phase6_rover_path_v2.png")
print("="*55)
print("PHASE 6 v2 COMPLETE — Path now targets actual ice mask centroid")
print(f"  Path     : {path_km:.2f} km")
print(f"  Elev drop: {elev_drop:.0f} m")
print(f"  Max slope: {max(pslopes):.1f}°")
print("="*55)