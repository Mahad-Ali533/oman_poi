import json
import csv

with open("C:/Users/san/Desktop/converter/hotosm_omn_points_of_interest_points_geojson.geojson", "r", encoding="utf-8") as f:
    data = json.load(f)

extracted_data = []
for feature in data["features"]:
    properties = feature["properties"]
    geometry = feature["geometry"]

    name_en = (properties.get("name") or "")
    name_ar = (properties.get("name:ar") or "")

    # Use name_en if available, otherwise fallback to name_ar
    name = name_en if name_en else name_ar

    if name:  # Only add if we have at least one name
        addr_full = properties.get("addr:full", "")
        coordinates = geometry.get("coordinates", [])
        extracted_data.append([name, addr_full, coordinates])



# Workaround: write BOM manually
with open("output.csv", "w", newline="", encoding="utf-8") as f:
    f.write('\ufeff')  # Write BOM manually
    writer = csv.writer(f)
    writer.writerow(["Name", "Address", "Coordinates"])
    writer.writerows(extracted_data)

print("File written with BOM manually.")



import pandas as pd
import geopandas as gpd
from shapely.geometry import Point

# Step 1: Read the original CSV
df = pd.read_csv("output.csv", encoding="utf-8-sig")

# Step 2: Create geometry from lat/lon
df["Latitude"] = df["Coordinates"].apply(lambda x: float(x.strip("[]").split(",")[1]))
df["Longitude"] = df["Coordinates"].apply(lambda x: float(x.strip("[]").split(",")[0]))

# Step 3: Convert to GeoDataFrame with Point geometry
geometry = [Point(lon, lat) for lon, lat in zip(df["Longitude"], df["Latitude"])]
gdf = gpd.GeoDataFrame(df, geometry=geometry, crs="EPSG:4326")

# Step 4: Reproject to meters for accurate buffering
gdf = gdf.to_crs(epsg=3857)

# Step 5: Buffer each point by 1000 meters (1 km)
gdf["Polygon"] = gdf.buffer(1000)

# Step 6: Reproject back to WGS84 (lat/lon)
gdf = gdf.set_geometry("Polygon").to_crs(epsg=4326)

# Step 7: Add WKT polygon column
gdf["Polygon_WKT"] = gdf["Polygon"].apply(lambda geom: geom.wkt)

# Step 8: Save to new CSV
gdf[["Name", "Address", "Latitude", "Longitude", "Polygon_WKT"]].to_csv(
    "oman_POI.csv", index=False, encoding="utf-8-sig"
)

print("✅ New CSV created: output_with_polygons.csv")
