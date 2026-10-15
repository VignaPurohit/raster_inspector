"""Dock panel: pick the raster, start drawing, review stats, save or discard."""

from qgis.core import Qgis
from qgis.gui import QgsDockWidget, QgsMapLayerComboBox, QgsRasterBandComboBox
from qgis.PyQt.QtCore import pyqtSignal
from qgis.PyQt.QtWidgets import (
    QFormLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

HINT = (
    "<b>Left-click</b> add vertex · <b>Right-click</b> finish<br>"
    "<b>S</b> save · <b>Esc</b> discard"
)


class RasterInspectorDock(QgsDockWidget):
    drawToggled = pyqtSignal(bool)
    saveClicked = pyqtSignal()
    discardClicked = pyqtSignal()
    zoomClicked = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__("RasterSample", parent)
        self.setObjectName("RasterInspectorDock")

        root = QWidget()
        layout = QVBoxLayout(root)

        # --- Input -------------------------------------------------------
        input_box = QGroupBox("Input raster")
        input_form = QFormLayout(input_box)
        self.layer_combo = QgsMapLayerComboBox()
        self.layer_combo.setFilters(Qgis.LayerFilter.RasterLayer)
        self.band_combo = QgsRasterBandComboBox()
        self.band_combo.setLayer(self.layer_combo.currentLayer())
        self.layer_combo.layerChanged.connect(self.band_combo.setLayer)
        input_form.addRow("Layer", self.layer_combo)
        input_form.addRow("Band", self.band_combo)
        layout.addWidget(input_box)

        # --- Tool --------------------------------------------------------
        self.draw_button = QPushButton("Start drawing")
        self.draw_button.setCheckable(True)
        self.draw_button.toggled.connect(self._on_draw_toggled)
        layout.addWidget(self.draw_button)

        hint = QLabel(HINT)
        hint.setWordWrap(True)
        layout.addWidget(hint)

        # --- Pending result ---------------------------------------------
        self.result_box = QGroupBox("Pending polygon")
        result_form = QFormLayout(self.result_box)
        self.mean_label = QLabel("–")
        self.min_label = QLabel("–")
        self.max_label = QLabel("–")
        self.count_label = QLabel("–")
        result_form.addRow("Mean", self.mean_label)
        result_form.addRow("Min", self.min_label)
        result_form.addRow("Max", self.max_label)
        result_form.addRow("Pixels", self.count_label)

        self.sample_id_edit = QLineEdit()
        self.note_edit = QLineEdit()
        self.note_edit.setPlaceholderText("Optional")
        result_form.addRow("Sample ID", self.sample_id_edit)
        result_form.addRow("Note", self.note_edit)

        buttons = QHBoxLayout()
        self.save_button = QPushButton("Save (S)")
        self.discard_button = QPushButton("Discard (Esc)")
        self.save_button.clicked.connect(self.saveClicked)
        self.discard_button.clicked.connect(self.discardClicked)
        self.sample_id_edit.returnPressed.connect(self.saveClicked)
        self.note_edit.returnPressed.connect(self.saveClicked)
        buttons.addWidget(self.save_button)
        buttons.addWidget(self.discard_button)
        result_form.addRow(buttons)
        layout.addWidget(self.result_box)

        # --- Output ------------------------------------------------------
        output_box = QGroupBox("Output")
        output_form = QFormLayout(output_box)
        self.output_name_edit = QLineEdit("inspection_samples")
        self.saved_label = QLabel("0 samples saved")
        self.zoom_button = QPushButton("Zoom to samples")
        self.zoom_button.clicked.connect(self.zoomClicked)
        output_form.addRow("Layer name", self.output_name_edit)
        output_form.addRow(self.saved_label, self.zoom_button)
        layout.addWidget(output_box)

        layout.addStretch()
        self.setWidget(root)

        self.next_sample_number = 1
        self.clear_pending()

    # -- tool button ------------------------------------------------------
    def _on_draw_toggled(self, checked):
        self.draw_button.setText("Stop drawing" if checked else "Start drawing")
        self.drawToggled.emit(checked)

    def set_drawing(self, checked):
        """Sync the button with the tool state without re-emitting."""
        self.draw_button.blockSignals(True)
        self.draw_button.setChecked(checked)
        self.draw_button.setText("Stop drawing" if checked else "Start drawing")
        self.draw_button.blockSignals(False)

    # -- pending result ---------------------------------------------------
    def show_pending(self, stats):
        self.mean_label.setText(_fmt(stats["mean"]))
        self.min_label.setText(_fmt(stats["min"]))
        self.max_label.setText(_fmt(stats["max"]))
        count = _fmt(stats["count"])
        if stats.get("method") == "bbox":
            count += " (bounding box)"
        self.count_label.setText(count)

        if not self.sample_id_edit.text():
            self.sample_id_edit.setText(f"S{self.next_sample_number:03d}")
        self.result_box.setEnabled(True)

    def clear_pending(self):
        for label in (self.mean_label, self.min_label, self.max_label, self.count_label):
            label.setText("–")
        self.sample_id_edit.clear()
        self.note_edit.clear()
        self.result_box.setEnabled(False)

    def sample_saved(self, total):
        self.next_sample_number += 1
        self.saved_label.setText(f"{total} sample{'s' if total != 1 else ''} saved")


def _fmt(value):
    if value is None:
        return "–"
    return f"{value:.4g}" if abs(value) < 1e6 else f"{value:.6g}"
