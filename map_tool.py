"""Polygon sketching map tool with a pending (inspect before save) state.

This is the workshop's RasterInspectorCommit tool (checkpoint 6), reworked so
that it only handles drawing and keyboard input and reports everything else
through signals. The plugin decides what to do with the polygon.
"""

from qgis.core import Qgis, QgsGeometry
from qgis.gui import QgsMapTool, QgsRubberBand
from qgis.PyQt.QtCore import Qt, pyqtSignal
from qgis.PyQt.QtGui import QColor

DRAW_COLOR = QColor(255, 0, 0, 120)      # red = drawing
PENDING_COLOR = QColor(0, 180, 0, 120)   # green = pending decision


class RasterInspectorTool(QgsMapTool):
    polygonFinished = pyqtSignal(QgsGeometry)
    saveRequested = pyqtSignal()
    discardRequested = pyqtSignal()
    message = pyqtSignal(str)

    def __init__(self, canvas):
        super().__init__(canvas)
        self.canvas = canvas

        # drawing state
        self.points = []

        # pending state
        self.is_pending = False

        self.rb = QgsRubberBand(canvas, Qgis.GeometryType.Polygon)
        self.rb.setColor(DRAW_COLOR)
        self.rb.setWidth(2)

    def activate(self):
        self.canvas.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        self.canvas.setFocus()
        super().activate()

    def deactivate(self):
        # Keep a pending polygon visible so it can still be saved from the
        # dock, but drop a half-drawn sketch.
        if not self.is_pending:
            self.reset()
        super().deactivate()

    def canvasPressEvent(self, event):
        if self.is_pending:
            self.message.emit("Decision pending. Press S to save or Esc to discard.")
            return

        if event.button() == Qt.MouseButton.LeftButton:
            pt = self.toMapCoordinates(event.pos())
            # Drop the rubber band's trailing "stretch" vertex before adding
            # the real one.
            if self.rb.numberOfVertices() > len(self.points):
                self.rb.removeLastPoint()
            self.points.append(pt)
            self.rb.addPoint(pt, True)

        elif event.button() == Qt.MouseButton.RightButton:
            if len(self.points) < 3:
                self.message.emit("Need at least 3 points to finish a polygon.")
                return

            geom = QgsGeometry.fromPolygonXY([self.points])
            self.points = []
            self.rb.setToGeometry(geom, None)
            self.polygonFinished.emit(geom)

    def canvasMoveEvent(self, event):
        if not self.points or self.is_pending:
            return

        pt = self.toMapCoordinates(event.pos())
        if self.rb.numberOfVertices() > len(self.points):
            self.rb.removeLastPoint()
        self.rb.addPoint(pt, True)

    def keyPressEvent(self, event):
        if event.key() == Qt.Key.Key_Escape:
            if self.is_pending:
                self.discardRequested.emit()
            else:
                self.reset()
            event.accept()

        elif event.key() == Qt.Key.Key_S:
            if not self.is_pending:
                self.message.emit("Nothing to save.")
            else:
                self.saveRequested.emit()
            event.accept()

        else:
            event.ignore()

    def set_pending(self):
        self.is_pending = True
        self.rb.setColor(PENDING_COLOR)

    def reset(self):
        self.points = []
        self.is_pending = False
        self.rb.reset(Qgis.GeometryType.Polygon)
        self.rb.setColor(DRAW_COLOR)

    def cleanup(self):
        """Remove the rubber band from the canvas (called on plugin unload)."""
        self.reset()
        self.canvas.scene().removeItem(self.rb)
        self.rb = None
