"""RasterSample - QGIS plugin entry point."""


def classFactory(iface):
    from .plugin import RasterInspectorPlugin
    return RasterInspectorPlugin(iface)
