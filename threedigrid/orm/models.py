# (c) Nelen & Schuurmans.  GPL licensed, see LICENSE.rst.

from threedigrid.admin.exporter_constants import DEFAULT_EXPORT_FIELDS
from threedigrid.admin.exporters.geopackage.exporter import GpkgExporter
from threedigrid.admin.serializers import GeoJsonSerializer
from threedigrid.orm.base.models import Model as BaseModel
from threedigrid.orm.fields import GeomArrayField, LineArrayField
from threedigrid.orm.filters import FILTER_MAP

from .constants import GEOJSON_DRIVER_NAME, SHP_DRIVER_NAME


class Model(BaseModel):
    _filter_map = FILTER_MAP

    def to_centroid(self):
        """
        Returns: the filtered values with geometries
                 transformed to centroids
        """
        selection = self.data
        for field_name in self._field_names:
            field = self._get_field(field_name)
            if isinstance(field, LineArrayField) and field_name in selection:
                # Use the to_centroid function of the GeomArrayField
                # to allow different geometry to be "centroided"
                selection[field_name] = field.to_centroid(selection[field_name])
        return selection

    def _is_coords(self, field_name):
        return isinstance(self._get_field(field_name), GeomArrayField)

    def _includes_coords(self, selection):
        """
        Returns: true if selection contains any data that
                 has coordinates.
        """
        found = False
        for field_name in self._field_names:
            if isinstance(self._get_field(field_name), GeomArrayField):
                found = True
                break
        return found

    def reproject_to(self, target_epsg_code):
        """
        Returns: a new class including the reprojection.

        Note: the last reproject_to is used:
            reproject_to('28992').reproject_to('4326') == reproject_to('4326')
        """
        new_class_kwargs = dict(self.class_kwargs)
        new_class_kwargs.update({"reproject_to_epsg": target_epsg_code})

        return self.__init_class(self.__class__, **new_class_kwargs)

    def _do_reproject_value(self, value, field_name, target_epsg_code):
        if target_epsg_code == self.epsg_code:
            # Already done
            return value

        field = self._get_field(field_name)

        return field.reproject(value, self.epsg_code, target_epsg_code)

    def __do_reproject(self, selection, target_epsg_code):
        """
        Reproject coordinate fields in selection to the
        target_epsg_code
        """
        if target_epsg_code == self.epsg_code:
            # Already done
            return selection

        # Reproject all GeomDataField's
        for field_name in self._field_names:
            field = self._get_field(field_name)
            if isinstance(field, GeomArrayField) and field_name in selection:
                # Use the reproject function of the GeomDataField
                # to allow different geometry to be reprojected
                selection[field_name] = field.reproject(
                    selection[field_name], self.epsg_code, target_epsg_code
                )
        return selection

    def to_shape(self, file_name, **kwargs):
        self._to_ogr(SHP_DRIVER_NAME, file_name, **kwargs)

    def to_gpkg(
        self,
        file_name,
        layer_name=None,
        field_definitions=None,
        progress_func=None,
        **kwargs
    ):
        # By default use class name in lowercase as layer_name
        if layer_name is None:
            layer_name = self.__class__.__name__.lower()
            if layer_name.endswith("s"):
                layer_name = layer_name[:-1]

        if field_definitions is None:
            if not hasattr(self, "GPKG_DEFAULT_FIELD_MAP"):
                raise Exception(
                    "field_definitions is not defined and no default field map present"
                )

            field_definitions = self.GPKG_DEFAULT_FIELD_MAP
        exporter = GpkgExporter(self)
        exporter.save(
            file_name,
            layer_name=layer_name,
            field_definitions=field_definitions,
            progress_func=progress_func,
            **kwargs
        )

    def to_geojson(self, file_name, **kwargs):
        if kwargs.get("use_ogr", False):
            self._to_ogr(GEOJSON_DRIVER_NAME, file_name, **kwargs)
        else:
            fields = kwargs.get(
                "fields", DEFAULT_EXPORT_FIELDS[self.__class__.__name__]
            )
            if fields == "ALL":
                fields = self._field_names

            indent = kwargs.get("indent", None)
            serializer = GeoJsonSerializer(fields, self, indent)
            serializer.save(file_name)

    def _to_ogr(self, driver_name, file_name, **kwargs):
        exporter = self._get_exporter(driver_name)
        if not exporter:
            raise AttributeError(
                "Instance {} has no {} exporter".format(self, driver_name)
            )
        exporter.set_driver(driver_name=driver_name)
        epsg_code = self.epsg_code
        if self.reproject_to_epsg:
            epsg_code = self.reproject_to_epsg

        exporter.save(file_name, self.data, epsg_code, **kwargs)

    def _get_exporter(self, driver_name):
        for exporter in self._exporters:
            if driver_name in exporter.supported_drivers:
                return exporter
        return None
