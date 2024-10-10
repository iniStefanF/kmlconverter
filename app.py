import os
import geopandas as gpd
import warnings
import zipfile
from shapely.geometry import Polygon, MultiPolygon
from io import BytesIO
import streamlit as st
import tempfile
import shutil
import matplotlib.pyplot as plt
import contextily as ctx  # For basemap tiles

# Suppress warnings
warnings.filterwarnings("ignore")

# Streamlit app setup
st.title("KML to Shapefile Converter")

# Upload KML file
uploaded_file = st.file_uploader("Upload a KML file", type="kml")

# Proceed if a file has been uploaded
if uploaded_file is not None:
    try:
        # Read the KML file into a GeoDataFrame
        with tempfile.NamedTemporaryFile(suffix=".kml", delete=False) as tmp_kml:
            tmp_kml.write(uploaded_file.read())
            tmp_kml.flush()
            gdf = gpd.read_file(tmp_kml.name, driver='KML')
        
        # Filter out geometries that are not polygons or multipolygons
        def ensure_polygon(geometry):
            if isinstance(geometry, (Polygon, MultiPolygon)):
                return geometry
            else:
                return None

        gdf['geometry'] = gdf['geometry'].apply(ensure_polygon)
        gdf = gdf[gdf['geometry'].notnull()]

        # Display preview of the polygons with a basemap
        st.subheader("Polygon Preview with Basemap")
        fig, ax = plt.subplots(figsize=(10, 10))
        
        # Plot polygons
        gdf.plot(ax=ax, alpha=0.5, edgecolor='k')
        
        # Add basemap (contextily uses OpenStreetMap tiles by default)
        ctx.add_basemap(ax, crs=gdf.crs.to_string(), source=ctx.providers.OpenStreetMap.Mapnik)

        plt.axis("off")
        st.pyplot(fig)

        # Temporary directory to store output files
        with tempfile.TemporaryDirectory() as tmp_output_dir:
            # Save shapefile to the temporary directory
            shp_filename = "converted_shapefile"
            shp_path = os.path.join(tmp_output_dir, shp_filename)
            gdf.to_file(shp_path, driver='ESRI Shapefile')

            # Create a zip file containing the shapefile components
            zip_buffer = BytesIO()
            with zipfile.ZipFile(zip_buffer, 'w') as zip_file:
                for root, _, files in os.walk(tmp_output_dir):
                    for file in files:
                        zip_file.write(os.path.join(root, file), arcname=file)

            # Enable download of the zipped shapefile
            st.download_button(
                label="Download Zipped Shapefile",
                data=zip_buffer.getvalue(),
                file_name="shapefile.zip",
                mime="application/zip"
            )
            
        st.success("Shapefile successfully generated!")
    except Exception as e:
        st.error(f"There was an error processing the KML file: {e}")
else:
    st.info("Please upload a KML file to convert.")