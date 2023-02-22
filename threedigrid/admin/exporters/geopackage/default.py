from copy import deepcopy

import numpy as np

from threedigrid.admin.exporters.geopackage.exporter import GpkgExporter

# Obstacle export field definitions/mapping
OBSTACLES_FIELD_DEFINITIONS = {
    "id": "line_id",
    "dpumax": "exchange_level",
    # special field, not part of the model data but given as extra kwargs
    "cross_pix_coords__transformed": "the_geom",
}


class GeopackageExporter:
    def __init__(self, gridadmin_filename, gpkg_filename):
        """
        Usage:
            class Progress:
                def __init__(self):
                    self.percentage = 0

                def update(self, count, total):
                    if (count * 100) // total > self.percentage:
                        self.percentage = (count * 100) // total
                        print("Percentage done: %s" % self.percentage)

            progress = Progress()
            exporter = GeopackageExporter("/tmp/gridadmin.h5", "/tmp/bergermeer.gpkg")
            exporter.export(progress.update)
        """
        self.gridadmin_filename = gridadmin_filename
        self.gpkg_filename = gpkg_filename

        # Keep track of progress
        self.start = 0
        self.total_items = 0

    def export(self, progress_func=None):
        """
        progress_func should be in format:

            def progress_func(count, total):
                # count = current processed features
                # total = total feature
                pass
        """
        from threedigrid.admin.gridadmin import GridH5Admin

        with GridH5Admin(self.gridadmin_filename) as ga:
            # Replace 'coordinates' with 'node_coordinates'
            PUMPS_LINESTRING_FIELD_DEFINITIONS = deepcopy(
                ga.pumps.GPKG_DEFAULT_FIELD_MAP
            )
            del PUMPS_LINESTRING_FIELD_DEFINITIONS["coordinates"]
            PUMPS_LINESTRING_FIELD_DEFINITIONS.update({"node_coordinates": "the_geom"})

            cells = ga.cells.subset("2D_OPEN_WATER")
            pumps = ga.pumps.filter(id__gte=1)
            lines = ga.lines.filter(id__gte=1)
            nodes = ga.nodes.filter(id__gte=1)
            obstacles = ga.lines.filter(kcu=101)

            # Linestring geometry for pumps
            pumps_linestring = pumps.filter(node1_id__ne=-9999, node2_id__ne=-9999)
            obstacles_count = (
                obstacles.count if np.any(obstacles.cross_pix_coords) else 0
            )

            if progress_func:
                self.total_items = (
                    cells.count
                    + pumps.count
                    + lines.count
                    + nodes.count
                    + obstacles_count
                    + pumps_linestring.count
                )
                self.start = 0

            self.calculated_items = 0

            def internal_progress_func(item_count, item_total):
                progress_func(self.start + item_count, self.total_items)
                if item_count == item_total:
                    self.start += item_total
                    self.calculated_items += item_total

            internal_func = internal_progress_func if progress_func else None

            # pumps and pumps_linestring layers
            pumps.to_gpkg(self.gpkg_filename, progress_func=internal_func)
            pumps_linestring.to_gpkg(
                self.gpkg_filename,
                "pump_linestring",
                PUMPS_LINESTRING_FIELD_DEFINITIONS,
                progress_func=internal_func,
            )

            # Other layers
            lines.to_gpkg(
                self.gpkg_filename, layer_name="flowline", progress_func=internal_func
            )
            nodes.to_gpkg(self.gpkg_filename, progress_func=internal_func)
            cells.to_gpkg(self.gpkg_filename, progress_func=internal_func)

            if obstacles_count > 0:
                # override the value for 'cross_pixel_coords'
                cross_pix_coords__transformed = obstacles.cross_pix_coords_transformed(
                    ga.grid.transform
                )

                obstacles.to_gpkg(
                    self.gpkg_filename,
                    "obstacle",
                    OBSTACLES_FIELD_DEFINITIONS,
                    progress_func=internal_func,
                    cross_pix_coords__transformed=cross_pix_coords__transformed,
                )

            # Write meta info
            exporter = GpkgExporter(ga)
            exporter.add_meta_data(self.gpkg_filename, "meta")

            assert self.total_items == self.calculated_items
