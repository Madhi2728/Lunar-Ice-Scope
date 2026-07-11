import rasterio
import csv

# Get the transform from the cropped CPR tif (same georeference as ice mask)
with rasterio.open("outputs/cropped/F2_cpr_crop.tif") as src:
    transform = src.transform
    crs = src.crs
    print("CRS:", crs)

rows_out = []
with open("outputs/rover_path/rover_waypoints.csv") as f:
    reader = csv.DictReader(f)
    for r in reader:
        row = int(r['row'])
        col = int(r['col'])
        # Convert pixel row/col to real-world X/Y using the crop's transform
        x, y = transform * (col, row)
        rows_out.append({**r, 'X': x, 'Y': y})

with open("outputs/rover_path/rover_waypoints_geo.csv", "w", newline='') as f:
    fieldnames = list(rows_out[0].keys())
    writer = csv.DictWriter(f, fieldnames=fieldnames)
    writer.writeheader()
    writer.writerows(rows_out)

print("Saved: outputs/rover_path/rover_waypoints_geo.csv")
print("Sample row:", rows_out[0])