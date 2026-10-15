"""Persist inspected polygons to a memory vector layer."""

from qgis.core import (
    QgsFeature,
    QgsField,
    QgsProject,
    QgsVectorLayer,
)
from qgis.PyQt.QtCore import QDateTime, QMetaType

FIELDS = [
    ("sample_id", QMetaType.Type.QString),
    ("note", QMetaType.Type.QString),
    ("raster", QMetaType.Type.QString),
    ("band", QMetaType.Type.Int),
    ("mean", QMetaType.Type.Double),
    ("min", QMetaType.Type.Double),
    ("max", QMetaType.Type.Double),
    ("pixel_count", QMetaType.Type.Double),
    ("created", QMetaType.Type.QDateTime),
]


def get_or_create_output_layer(name, crs):
    """Return the project's layer called ``name``, creating it if needed."""
    project = QgsProject.instance()
    for layer in project.mapLayersByName(name):
        if isinstance(layer, QgsVectorLayer) and layer.fields().indexOf("sample_id") >= 0:
            return layer

    vlayer = QgsVectorLayer(f"Polygon?crs={crs.authid()}", name, "memory")
    if not crs.authid():
        vlayer.setCrs(crs)
    vlayer.dataProvider().addAttributes([QgsField(n, t) for n, t in FIELDS])
    vlayer.updateFields()
    project.addMapLayer(vlayer)
    return vlayer


def save_sample(vlayer, geom, stats, sample_id, note):
    feat = QgsFeature(vlayer.fields())
    feat.setGeometry(geom)
    values = {
        "sample_id": sample_id,
        "note": note,
        "raster": stats["raster"],
        "band": stats["band"],
        "mean": stats["mean"],
        "min": stats["min"],
        "max": stats["max"],
        "pixel_count": stats["count"],
        "created": QDateTime.currentDateTime(),
    }
    for field_name, value in values.items():
        idx = vlayer.fields().indexOf(field_name)
        if idx >= 0:
            feat.setAttribute(idx, value)

    ok, _ = vlayer.dataProvider().addFeatures([feat])
    vlayer.updateExtents()
    vlayer.triggerRepaint()
    return ok
