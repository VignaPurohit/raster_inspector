"""Raster statistics for a polygon drawn on the map canvas."""

from qgis.analysis import QgsZonalStatistics
from qgis.core import (
    Qgis,
    QgsCoordinateTransform,
    QgsGeometry,
    QgsProject,
)


def compute_stats(layer, band, geom, canvas_crs):
    """Return mean/min/max/count of ``band`` of ``layer`` inside ``geom``.

    ``geom`` is in ``canvas_crs`` and is transformed to the raster CRS first.
    Pixels are counted when their centre falls inside the polygon; for
    polygons smaller than a pixel QGIS weights pixels by coverage, so the
    count can be fractional. Returns None if there is no overlap.
    """
    geom = QgsGeometry(geom)
    if canvas_crs != layer.crs():
        xform = QgsCoordinateTransform(canvas_crs, layer.crs(), QgsProject.instance())
        geom.transform(xform)

    wanted = (
        Qgis.ZonalStatistic.Mean
        | Qgis.ZonalStatistic.Min
        | Qgis.ZonalStatistic.Max
        | Qgis.ZonalStatistic.Count
    )
    result = QgsZonalStatistics.calculateStatistics(
        layer.dataProvider(),
        geom,
        layer.rasterUnitsPerPixelX(),
        layer.rasterUnitsPerPixelY(),
        band,
        wanted,
    )

    def value(stat):
        # Keys are ints under Qt5 and may be enum members under Qt6.
        if stat in result:
            return result[stat]
        return result.get(int(stat))

    count = value(Qgis.ZonalStatistic.Count)
    if count:
        return {
            "raster": layer.name(),
            "band": band,
            "mean": value(Qgis.ZonalStatistic.Mean),
            "min": value(Qgis.ZonalStatistic.Min),
            "max": value(Qgis.ZonalStatistic.Max),
            "count": round(float(count), 2),
            "method": "polygon",
        }

    # Zonal statistics found nothing: fall back to the workshop's
    # bounding-box statistics so the user still gets the values underneath.
    if not geom.boundingBox().intersects(layer.extent()):
        return None
    bbox_stats = layer.dataProvider().bandStatistics(
        band,
        Qgis.RasterBandStatistic.Mean
        | Qgis.RasterBandStatistic.Min
        | Qgis.RasterBandStatistic.Max,
        geom.boundingBox(),
        0,
    )
    if not bbox_stats.elementCount:
        return None
    return {
        "raster": layer.name(),
        "band": band,
        "mean": bbox_stats.mean,
        "min": bbox_stats.minimumValue,
        "max": bbox_stats.maximumValue,
        "count": int(bbox_stats.elementCount),
        "method": "bbox",
    }
