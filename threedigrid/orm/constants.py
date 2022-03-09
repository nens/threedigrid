# (c) Nelen & Schuurmans.  GPL licensed, see LICENSE.rst.

SHP_DRIVER_NAME = "ESRI Shapefile"
GEO_PACKAGE_DRIVER_NAME = "GPKG"
GEOJSON_DRIVER_NAME = "GeoJSON"

EXPORT_SHAPEFILE = "to_shape"
EXPORT_GEOPACKAGE = "to_gpkg"
EXPORT_GEOJSON = "to_geojson"

SHP_EXTENSION = ".shp"
GEO_PACKAGE_EXTENSION = ".gpkg"
GEOJSON_EXTENSION = ".json"
GEOJSON_EXTENSION2 = ".geojson"

EXTENSION_TO_DRIVER_MAP = {
    SHP_EXTENSION: SHP_DRIVER_NAME,
    GEO_PACKAGE_EXTENSION: GEO_PACKAGE_DRIVER_NAME,
    GEOJSON_EXTENSION: GEOJSON_DRIVER_NAME,
    GEOJSON_EXTENSION2: GEOJSON_DRIVER_NAME,
}

EXPORT_METHOD_TO_EXTENSION_MAP = {
    EXPORT_SHAPEFILE: SHP_EXTENSION,
    EXPORT_GEOPACKAGE: GEO_PACKAGE_EXTENSION,
    EXPORT_GEOJSON: GEOJSON_EXTENSION,
}

###############################################################################
# White list of variables and aggregation variables
AGGREGATION_OPTIONS = {
    "min",
    "max",
    "avg",
    "med",
    "cum",
    "cum_positive",
    "cum_negative",
}

###############################################################################
# result netCDF variables


# pumpstations
PUMPS_VARIABLES = ["Mesh1D_q_pump"]

# breaches
BREACH_VARIABLES = ["Mesh1D_breach_depth", "Mesh1D_breach_width"]
LEVEES_VARIABLES = []
