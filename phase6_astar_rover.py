"""
Phase 6 - A* Rover Path Planning - ACCURATE VERSION
Finds real landing zone on crater rim → F2 crater floor
BAH2026 | LOLA DEM
"""
import numpy as np
import heapq, math
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from scipy.ndimage import sobel, gaussian_filter
import os

os.makedirs("outputs/rover_path", exist_ok=True)

# 1. Load DEM exactly like phase4
dem_file = 'data/dem/LDEM_875S_20M.IMG'
print('Reading DEM...')
dem = np.fromfile(dem_file, dtype=np.int16)
total = len(dem)
side = int(math.sqrt(total))
dem = dem[:side*side].reshape(side, side).astype(float)
print(f'DEM shape: {dem.shape}, range: {dem.min():.0f} to {dem.max():.0f} m')
pixel_m = 20.0

# 2. Slope
dx = sobel(dem, axis=1)
dy = sobel(dem, axis=0)
slope = np.degrees(np.arctan(np.sqrt(dx**2 + dy**2) / (8.0 * 20.0)))
print(f'Slope: {slope.min():.1f} to {slope.max():.1f} deg')

# 3. Find the deepest crater (Faustini) in the DEM
# Smooth DEM to find crater bowl center reliably
dem_smooth = gaussian_filter(dem, sigma=30)
# The crater floor is the global minimum in the south pole region
# Work on centre 2000x2000 to stay near pole
H, W = dem.shape
rC, cC = H//2, W//2
SEARCH = 1000
rs, re = rC-SEARCH, rC+SEARCH
cs, ce = cC-SEARCH, cC+SEARCH
dem_search = dem_smooth[rs:re, cs:ce]

# Find crater floor = deepest point
floor_local = np.unravel_index(np.argmin(dem_search), dem_search.shape)
floor_abs = (floor_local[0]+rs, floor_local[1]+cs)
print(f'Crater floor at pixel: {floor_abs}, elev={dem[floor_abs]:.0f}m')

# 4. Crop 600x600 px (12x12 km) around crater
HALF = 300
r0 = max(0, floor_abs[0]-HALF)
r1 = min(H, floor_abs[0]+HALF)
c0 = max(0, floor_abs[1]-HALF)
c1 = min(W, floor_abs[1]+HALF)
dem_s   = dem[r0:r1, c0:c1]
slope_s = slope[r0:r1, c0:c1]
sH, sW  = dem_s.shape
print(f'Crop: {dem_s.shape} = {sH*pixel_m/1000:.1f}x{sW*pixel_m/1000:.1f} km')
print(f'Crop elev: {dem_s.min():.0f} to {dem_s.max():.0f} m')

# 5. Goal = crater floor center in cropped image
goal = (floor_abs[0]-r0, floor_abs[1]-c0)
print(f'Goal (crater floor): {goal}, elev={dem_s[goal]:.0f}m, slope={slope_s[goal]:.1f}deg')

# 6. Start = safest point on crater RIM
# Rim = within 50-120px of floor, elevation > floor+500m, slope < 15deg
floor_elev = dem_s[goal]
rim_mask = np.zeros_like(dem_s, dtype=bool)
for r in range(sH):
    for c in range(sW):
        dist = math.hypot(r-goal[0], c-goal[1])
        if 60 <= dist <= 150:
            if dem_s[r,c] > floor_elev + 300:
                if slope_s[r,c] < 15:
                    rim_mask[r,c] = True

if rim_mask.sum() == 0:
    print("No rim candidates found, relaxing criteria...")
    for r in range(sH):
        for c in range(sW):
            dist = math.hypot(r-goal[0], c-goal[1])
            if 40 <= dist <= 200 and dem_s[r,c] > floor_elev+100:
                rim_mask[r,c] = True

# Pick flattest point on rim
slope_rim = slope_s.copy()
slope_rim[~rim_mask] = 9999
start_local = np.unravel_index(np.argmin(slope_rim), slope_rim.shape)
start = start_local
print(f'Start (rim landing): {start}, elev={dem_s[start]:.0f}m, slope={slope_s[start]:.1f}deg')

# 7. Cost grid
cost = np.ones_like(slope_s)
cost[slope_s >  8]  = 3.0
cost[slope_s > 12]  = 8.0
cost[slope_s > 18]  = 30.0
cost[slope_s > 22]  = 200.0
cost[slope_s > 28]  = 9999.0

# 8. A*
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

print('Running A*...')
path = astar(cost, start, goal)
if path is None:
    print('A* blocked — using gradient descent path')
    # Walk downhill avoiding steep slopes
    path = [start]
    cur = start
    visited = {start}
    dirs = [(-1,0),(1,0),(0,-1),(0,1),(-1,-1),(-1,1),(1,-1),(1,1)]
    for _ in range(10000):
        if cur == goal: break
        best_next = None
        best_score = 1e18
        for dr,dc in dirs:
            nr,nc = cur[0]+dr, cur[1]+dc
            if 0<=nr<sH and 0<=nc<sW and (nr,nc) not in visited:
                if slope_s[nr,nc] < 25:
                    score = dem_s[nr,nc] + slope_s[nr,nc]*10
                    if score < best_score:
                        best_score=score; best_next=(nr,nc)
        if best_next is None: break
        path.append(best_next)
        visited.add(best_next)
        cur = best_next
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

print(f'Path: {path_km:.2f} km | Drop: {elev_drop:.0f}m | MaxSlope: {max(pslopes):.1f}deg')

# Save CSV
step = max(1,len(path)//50)
with open("outputs/rover_path/rover_waypoints.csv","w") as f:
    f.write("wp,row,col,cum_km,slope_deg,elev_m\n")
    for i,p in enumerate(path[::step]):
        f.write(f"{i},{p[0]},{p[1]},{cum_d[min(i*step,len(cum_d)-1)]:.3f},"
                f"{slope_s[p[0],p[1]]:.2f},{dem_s[p[0],p[1]]:.1f}\n")
print("Saved: outputs/rover_path/rover_waypoints.csv")

# 9. Plot
km = pixel_m/1000
ext = [0, sW*km, sH*km, 0]
fig, axes = plt.subplots(1,3,figsize=(18,6),facecolor='#0a0a1a')
fig.suptitle(f"Rover Path — Faustini F2 Crater  |  BAH2026\n"
             f"A* on LOLA DEM | {path_km:.1f} km | Drop {elev_drop:.0f}m",
             color='white', fontsize=13, fontweight='bold')

# Panel 1: DEM + path
ax=axes[0]; ax.set_facecolor('#0a0a1a')
im=ax.imshow(dem_s, cmap='terrain', origin='upper', extent=ext, aspect='equal')
cb=fig.colorbar(im,ax=ax,fraction=0.046,pad=0.04)
cb.set_label('Elevation (m)',color='white',fontsize=8)
cb.ax.yaxis.set_tick_params(color='white')
plt.setp(cb.ax.yaxis.get_ticklabels(),color='white')
ax.plot(pa[:,1]*km, pa[:,0]*km,'y-',lw=2.5,alpha=0.95,label='Rover path',zorder=4)
ax.plot(start[1]*km,start[0]*km,'g^',ms=14,zorder=5,
        label=f'Landing (slope={slope_s[start]:.1f}°, {dem_s[start]:.0f}m)')
ax.plot(goal[1]*km, goal[0]*km, 'r*',ms=16,zorder=5,
        label=f'F2 floor ({dem_s[goal]:.0f}m)')
# Draw crater rim circle
theta = np.linspace(0,2*np.pi,200)
rim_r_km = 80*km  # ~1100m diameter / 2 = 550m = ~27px * km
ax.plot(goal[1]*km + rim_r_km*np.cos(theta),
        goal[0]*km + rim_r_km*np.sin(theta),
        'w--', lw=1, alpha=0.5, label='F2 crater rim (~1.1km)')
ax.set_title(f'DEM + Rover Path ({path_km:.1f} km)', color='white', fontsize=10)
ax.set_xlabel('km', color='white', fontsize=9)
ax.set_ylabel('km', color='white', fontsize=9)
ax.tick_params(colors='white')
for sp in ax.spines.values(): sp.set_edgecolor('white')
ax.legend(fontsize=7,facecolor='#1a1a2e',edgecolor='white',labelcolor='white')

# Panel 2: Slope + safe zones
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
ax.plot(goal[1]*km, goal[0]*km, 'r*',ms=16,zorder=5,label='F2 target')
ax.set_title('Slope Map  (blue=safe <10°)', color='white', fontsize=10)
ax.set_xlabel('km',color='white',fontsize=9)
ax.set_ylabel('km',color='white',fontsize=9)
ax.tick_params(colors='white')
for sp in ax.spines.values(): sp.set_edgecolor('white')
ax.legend(fontsize=7,facecolor='#1a1a2e',edgecolor='white',labelcolor='white')

# Panel 3: Elevation profile
ax=axes[2]; ax.set_facecolor('#0d0d1f')
ax.fill_between(cum_d,elevs,min(elevs),color='saddlebrown',alpha=0.6)
ax.plot(cum_d,elevs,'w-',lw=2)
ax.axhline(elevs[0], color='lime',ls='--',lw=1.5,label=f'Start {elevs[0]:.0f}m')
ax.axhline(elevs[-1],color='red', ls='--',lw=1.5,label=f'End   {elevs[-1]:.0f}m')
# Mark max slope point
max_slope_idx = np.argmax(pslopes)
ax.axvline(cum_d[max_slope_idx],color='orange',ls=':',lw=1.2,
           label=f'Max slope {max(pslopes):.1f}°')
ax.set_xlabel('Distance (km)',color='white',fontsize=9)
ax.set_ylabel('Elevation (m)',color='white',fontsize=9)
ax.set_title(f'Elevation Profile\nDrop {elev_drop:.0f}m  |  {path_km:.1f}km  |  '
             f'~{path_km/0.1:.0f}h traverse',
             color='white',fontsize=10)
ax.tick_params(colors='white')
for sp in ax.spines.values(): sp.set_edgecolor('#444')
ax.legend(fontsize=8,facecolor='#1a1a2e',edgecolor='white',labelcolor='white')

plt.tight_layout()
plt.savefig("outputs/rover_path/phase6_rover_path.png",
            dpi=150,bbox_inches='tight',facecolor='#0a0a1a')
plt.close()
print("Saved: outputs/rover_path/phase6_rover_path.png")
print("="*50)
print("PHASE 6 COMPLETE")
print(f"  Path     : {path_km:.2f} km")
print(f"  Elev drop: {elev_drop:.0f} m")
print(f"  Max slope: {max(pslopes):.1f}°")
print(f"  Avg slope: {np.mean(pslopes):.1f}°")
print(f"  Time est : ~{path_km/0.1:.0f} hrs @ 0.1 km/h")
print("="*50)