import rasterio
import pandas as pd

with rasterio.open("outputs/cropped/F2_cpr_crop.tif") as src:
    print("=== CPR CROP BOUNDS ===")
    print(src.bounds)
    print("Center:", (src.bounds.left+src.bounds.right)/2, (src.bounds.top+src.bounds.bottom)/2)

df = pd.read_csv("outputs/rover_path/rover_waypoints_geo.csv")
print("\n=== ROVER WAYPOINTS RANGE ===")
print("X range:", df['X'].min(), "to", df['X'].max())
print("Y range:", df['Y'].min(), "to", df['Y'].max())
print("X center:", df['X'].mean())
print("Y center:", df['Y'].mean())