"""
Phase 7 - Ice Volume Estimation - Simplified, Realistic Lunar Surface
BAH2026 | Faustini F2 Crater | Chandrayaan-2 DFSAR
Reference: Sinha et al. 2026, npj Space Exploration
"""
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.colors import LinearSegmentedColormap
from scipy.ndimage import gaussian_filter
import os

os.makedirs("outputs/final_maps", exist_ok=True)
np.random.seed(42)

print("="*60)
print("PHASE 7 - ICE VOLUME ESTIMATION (SIMPLIFIED)")
print("Target: Faustini F2 Crater, Lunar South Pole")
print("="*60)

ICE_AREA_KM2  = 0.534
ICE_AREA_M2   = ICE_AREA_KM2 * 1e6
DENSITY_ICE   = 917.0
CRATER_DIAM_M = 1100
CRATER_RAD_M  = CRATER_DIAM_M/2
DEPTH_FULL    = 144

RADAR_DEPTH   = 5
FRAC_LOW      = 0.4
FRAC_HIGH     = 0.6

def vol_mass(depth, frac):
    vol_m3 = ICE_AREA_M2 * depth * frac
    mass_t = vol_m3 * DENSITY_ICE / 1000.0
    return vol_m3, mass_t

A = vol_mass(RADAR_DEPTH, FRAC_LOW)     # conservative
B = vol_mass(DEPTH_FULL, FRAC_HIGH)     # upper-bound
avg_vol  = (A[0] + B[0]) / 2
avg_mass = (A[1] + B[1]) / 2

print(f"Scenario A (Radar-Detected, 5m, 40%) : {A[0]:>14,.0f} m3   {A[1]:>14,.0f} t")
print(f"Scenario B (Upper-Bound, 144m, 60%)  : {B[0]:>14,.0f} m3   {B[1]:>14,.0f} t")
print(f"Average                              : {avg_vol:>14,.0f} m3   {avg_mass:>14,.0f} t")
print("="*60)

# ─────────────────────────────────────────────────────────────────────────
# STYLING
# ─────────────────────────────────────────────────────────────────────────
plt.rcParams['font.family'] = 'DejaVu Sans'
BG       = '#070912'
PANEL_BG = '#0d1120'
GRID_CLR = '#262c4a'
TEXT_CLR = '#eef0f7'
ACCENT_BLUE  = '#4dc8ff'
ACCENT_RED   = '#ff6b6b'
ACCENT_GOLD  = '#ffc857'

fig = plt.figure(figsize=(16, 11), facecolor=BG)
gs = fig.add_gridspec(2, 1, height_ratios=[0.8, 1.3], hspace=0.30,
                       left=0.07, right=0.95, top=0.89, bottom=0.07)

fig.suptitle("Ice Volume Estimation — Faustini F2 Crater",
             color='white', fontsize=20, fontweight='bold', y=0.965)
fig.text(0.5, 0.925,
         "BAH2026 National Hackathon  |  Chandrayaan-2 DFSAR",
         color='#9aa3c7', fontsize=11, ha='center', style='italic')

# ── TOP: Simple 2-bar comparison + average ───────────────────────────────
ax1 = fig.add_subplot(gs[0])
ax1.set_facecolor(PANEL_BG)

labels = ['Average\nEstimate\n(Best Guess)',
          'Scenario B\nGeological Bound\n(Speculative)\n144m depth, 60% ice',
          'Scenario A\nRadar-Detected\n(Conservative)\n5m depth, 40% ice']
values = [avg_vol, B[0], A[0]]
masses = [avg_mass, B[1], A[1]]
colors = [ACCENT_GOLD, ACCENT_RED, ACCENT_BLUE]

bars = ax1.barh(labels, values, color=colors, edgecolor='white',
                linewidth=1.2, height=0.55, zorder=3)
ax1.set_xscale('log')
ax1.set_xlim(5e5, 1.3e8)

for b, v, m in zip(bars, values, masses):
    ax1.text(v*1.3, b.get_y()+b.get_height()/2,
             f'{v:,.0f} m³\n≈ {m:,.0f} tonnes',
             va='center', ha='left', color='white', fontsize=10.5, fontweight='bold')

ax1.set_xlabel('Estimated Ice Volume (m³, logarithmic scale)', color=TEXT_CLR, fontsize=11)
ax1.tick_params(colors=TEXT_CLR, labelsize=10.5)
ax1.grid(axis='x', which='both', color=GRID_CLR, linewidth=0.5, alpha=0.5)
for sp in ax1.spines.values():
    sp.set_edgecolor(GRID_CLR)
ax1.set_title('How Much Ice? — Three Estimates Side by Side',
              color='white', fontsize=13, fontweight='bold', pad=14)

# ── BOTTOM: Crater cross-section with realistic textured regolith ───────
ax2 = fig.add_subplot(gs[1])
ax2.set_facecolor(PANEL_BG)

crater_r   = CRATER_RAD_M
rim_height = 30
x = np.linspace(-700, 700, 1400)
crater_profile = np.where(
    np.abs(x) <= crater_r,
    -DEPTH_FULL * (1 - (x/crater_r)**2),
    np.where(np.abs(x) <= crater_r*1.1,
             rim_height * (1 - (np.abs(x)-crater_r)/(crater_r*0.1)),
             0)
)

# Build a 2D textured "regolith" patch using fractal-like noise for realism
ny, nx = 300, len(x)
noise = np.random.normal(0, 1, (ny, nx))
noise = gaussian_filter(noise, sigma=[1.5, 6])
noise2 = np.random.normal(0, 1, (ny, nx))
noise2 = gaussian_filter(noise2, sigma=[4, 12])
texture = 0.65*noise + 0.35*noise2
texture = (texture - texture.min()) / (texture.max() - texture.min())

# Greyscale lunar regolith colormap (white/grey, like real regolith)
regolith_cmap = LinearSegmentedColormap.from_list(
    'regolith', ['#5a5a5e', '#8d8d92', '#bcbcc0', '#e8e8ec', '#ffffff']
)

y_bottom = -DEPTH_FULL - 60
y_top    = 200
yy = np.linspace(y_bottom, y_top, ny)
extent = [x.min(), x.max(), y_bottom, y_top]

# Mask texture to only show below the crater profile surface line (the solid ground)
Y2D = np.tile(yy.reshape(-1,1), (1, nx))
surf2D = np.tile(crater_profile.reshape(1,-1), (ny,1))
mask = Y2D <= surf2D

masked_tex = np.ma.masked_where(~mask, texture)
ax2.imshow(masked_tex, extent=extent, origin='lower', cmap=regolith_cmap,
           aspect='auto', alpha=0.95, zorder=2, vmin=0, vmax=1)

# Ice layers on top of textured ground
radar_depth = 5
iceA_top    = np.where(np.abs(x) <= crater_r*0.85, crater_profile, np.nan)
iceA_bottom = np.where(np.abs(x) <= crater_r*0.85, crater_profile - radar_depth*3, np.nan)
ax2.fill_between(x, iceA_bottom, iceA_top, color=ACCENT_BLUE, alpha=0.95, zorder=4,
                 label=f'Scenario A — Radar-detected ice ({A[0]:,.0f} m³)')

iceB_top    = np.where(np.abs(x) <= crater_r*0.85, -DEPTH_FULL*0.15, np.nan)
iceB_bottom = np.where(np.abs(x) <= crater_r*0.85, -DEPTH_FULL, np.nan)
ax2.fill_between(x, iceB_bottom, iceB_top, color=ACCENT_RED, alpha=0.28,
                 hatch='////', edgecolor=ACCENT_RED, linewidth=0.6, zorder=3,
                 label=f'Scenario B — Speculative deep ice sheet ({B[0]/1e6:.1f}M m³)')

# Surface outline
ax2.plot(x, crater_profile, color='white', lw=2.4, zorder=5)

# Sky/space above surface — solid dark fill for contrast
ax2.fill_between(x, crater_profile, y_top, color=BG, zorder=1)

# Simple labelled arrows
ax2.annotate('', xy=(crater_r, -10), xytext=(-crater_r, -10),
             arrowprops=dict(arrowstyle='<->', color=ACCENT_GOLD, lw=1.8))
ax2.text(0, 18, f'{CRATER_DIAM_M} m crater diameter', color=ACCENT_GOLD,
         fontsize=10, ha='center', fontweight='bold')

ax2.annotate('', xy=(crater_r+40, 0), xytext=(crater_r+40, -DEPTH_FULL),
             arrowprops=dict(arrowstyle='<->', color='white', lw=1.6))
ax2.text(crater_r+60, -DEPTH_FULL/2, f'{DEPTH_FULL} m\ndeep',
         color='white', fontsize=9.5, va='center')

ax2.set_xlim(-720, 720)
ax2.set_ylim(y_bottom, y_top)
ax2.set_xlabel('Distance from Crater Center (m)', color=TEXT_CLR, fontsize=11)
ax2.set_ylabel('Elevation (m)', color=TEXT_CLR, fontsize=11)
ax2.set_title('F2 Crater Cross-Section',
              color='white', fontsize=13, fontweight='bold', pad=12)
ax2.tick_params(colors=TEXT_CLR, labelsize=9.5)
ax2.legend(fontsize=10, facecolor=PANEL_BG, edgecolor=GRID_CLR,
           labelcolor='white', loc='lower right', framealpha=0.95)
for sp in ax2.spines.values():
    sp.set_edgecolor(GRID_CLR)

fig.text(0.5, 0.015,
         "Scenario A = what radar can actually detect (2-10 m penetration).  "
         "Scenario B = upper-bound hypothesis from crater lobate-rim shape, not a direct measurement.",
         color='#8a92b8', fontsize=9, style='italic', ha='center')

plt.savefig("outputs/final_maps/phase7_ice_volume.png",
            dpi=160, bbox_inches='tight', facecolor=BG)
plt.close()
print("\nSaved: outputs/final_maps/phase7_ice_volume.png")
print("PHASE 7 COMPLETE")