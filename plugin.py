"""Raster Inspector plugin: wires the map tool, dock panel and storage."""

import os

from qgis.core import Qgis, QgsCoordinateTransform, QgsGeometry, QgsProject
from qgis.PyQt.QtCore import Qt
from qgis.PyQt.QtGui import QIcon
from qgis.PyQt.QtWidgets import QAction

from .dock import RasterInspectorDock
from .map_tool import RasterInspectorTool
from .stats import compute_stats
from .storage import get_or_create_output_layer, save_sample

MENU = "&Raster Inspector"


class RasterInspectorPlugin:
    def __init__(self, iface):
        self.iface = iface
        self.canvas = iface.mapCanvas()
        self.action = None
        self.dock = None
        self.tool = None
        self.pending_geom = None
        self.pending_stats = None
        self.pending_crs = None

    # ------------------------------------------------------------------ setup
    def initGui(self):
        icon = QIcon(os.path.join(os.path.dirname(__file__), "icon.svg"))
        self.action = QAction(icon, "Raster Inspector", self.iface.mainWindow())
        self.action.setCheckable(True)
        self.action.setToolTip("Sketch polygons and inspect raster statistics")
        self.action.toggled.connect(self.set_active)
        self.iface.addToolBarIcon(self.action)
        self.iface.addPluginToRasterMenu(MENU, self.action)

        self.tool = RasterInspectorTool(self.canvas)
        self.tool.polygonFinished.connect(self.on_polygon_finished)
        self.tool.saveRequested.connect(self.save_pending)
        self.tool.discardRequested.connect(self.discard_pending)
        self.tool.message.connect(lambda text: self.notify(text, Qgis.MessageLevel.Info))
        self.tool.deactivated.connect(self.on_tool_deactivated)

        self.dock = RasterInspectorDock(self.iface.mainWindow())
        self.dock.drawToggled.connect(self.action.setChecked)
        self.dock.saveClicked.connect(self.save_pending)
        self.dock.discardClicked.connect(self.discard_pending)
        self.dock.zoomClicked.connect(self.zoom_to_samples)
        self.iface.addDockWidget(Qt.DockWidgetArea.RightDockWidgetArea, self.dock)
        self.dock.hide()

    def unload(self):
        if self.canvas.mapTool() is self.tool:
            self.canvas.unsetMapTool(self.tool)
        if self.tool:
            self.tool.cleanup()
            self.tool.deleteLater()
            self.tool = None

        if self.dock:
            self.iface.removeDockWidget(self.dock)
            self.dock.deleteLater()
            self.dock = None

        if self.action:
            self.iface.removePluginRasterMenu(MENU, self.action)
            self.iface.removeToolBarIcon(self.action)
            self.action.deleteLater()
            self.action = None

    # ------------------------------------------------------------ tool state
    def set_active(self, checked):
        if checked:
            self.dock.show()
            self.dock.raise_()
            if self.canvas.mapTool() is not self.tool:
                self.canvas.setMapTool(self.tool)
        elif self.canvas.mapTool() is self.tool:
            self.canvas.unsetMapTool(self.tool)
        self.dock.set_drawing(checked)

    def on_tool_deactivated(self):
        # Another map tool (pan, identify...) took over.
        self.action.blockSignals(True)
        self.action.setChecked(False)
        self.action.blockSignals(False)
        self.dock.set_drawing(False)

    # --------------------------------------------------------- inspection
    def on_polygon_finished(self, geom):
        layer = self.dock.layer_combo.currentLayer()
        if layer is None:
            self.notify("Add or select a raster layer in the Raster Inspector panel.",
                        Qgis.MessageLevel.Warning)
            self.tool.reset()
            return

        band = self.dock.band_combo.currentBand()
        if band < 1:
            band = 1

        canvas_crs = self.canvas.mapSettings().destinationCrs()
        stats = compute_stats(layer, band, geom, canvas_crs)
        if stats is None:
            self.notify("The polygon does not overlap the raster.", Qgis.MessageLevel.Warning)
            self.tool.reset()
            return

        self.pending_geom = geom
        self.pending_stats = stats
        self.pending_crs = canvas_crs
        self.tool.set_pending()
        self.dock.show()
        self.dock.show_pending(stats)

    def save_pending(self):
        if self.pending_geom is None:
            self.notify("Nothing to save.", Qgis.MessageLevel.Info)
            return

        sample_id = self.dock.sample_id_edit.text().strip()
        if not sample_id:
            self.notify("Enter a sample ID before saving.", Qgis.MessageLevel.Warning)
            self.dock.sample_id_edit.setFocus()
            return

        name = self.dock.output_name_edit.text().strip() or "inspection_samples"
        vlayer = get_or_create_output_layer(name, self.pending_crs)
        geom = self.pending_geom
        if vlayer.crs() != self.pending_crs:
            geom = QgsGeometry(geom)
            geom.transform(QgsCoordinateTransform(self.pending_crs, vlayer.crs(),
                                                  QgsProject.instance()))

        if save_sample(vlayer, geom, self.pending_stats, sample_id,
                       self.dock.note_edit.text().strip()):
            self.dock.sample_saved(vlayer.featureCount())
            self.notify(f"Saved sample {sample_id} to '{vlayer.name()}'.",
                        Qgis.MessageLevel.Success)
            self._clear_pending()
        else:
            self.notify("Could not save the sample.", Qgis.MessageLevel.Critical)

    def discard_pending(self):
        if self.pending_geom is not None:
            self.notify("Pending polygon discarded.", Qgis.MessageLevel.Info)
        self._clear_pending()

    def _clear_pending(self):
        self.pending_geom = None
        self.pending_stats = None
        self.pending_crs = None
        self.tool.reset()
        self.dock.clear_pending()
        if self.canvas.mapTool() is self.tool:
            self.canvas.setFocus()

    def zoom_to_samples(self):
        name = self.dock.output_name_edit.text().strip() or "inspection_samples"
        layers = QgsProject.instance().mapLayersByName(name)
        if not layers or layers[0].featureCount() == 0:
            self.notify("No saved samples yet.", Qgis.MessageLevel.Info)
            return
        self.iface.setActiveLayer(layers[0])
        self.iface.zoomToActiveLayer()

    # ---------------------------------------------------------------- utils
    def notify(self, text, level):
        self.iface.messageBar().pushMessage("Raster Inspector", text, level, 4)
