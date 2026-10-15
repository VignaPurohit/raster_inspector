# Raster Inspector (QGIS plugin)

Sketch polygons on the map, inspect raster statistics inside them, and save the
ones you keep as sample features. Built from the final checkpoint of the
FOSS4G *Advanced PyQGIS Scripting and Automation* workshop.

Works with **QGIS 3.40+ (Qt5)** and **QGIS 4.x (Qt6)**.

## Install

**From ZIP:** *Plugins → Manage and Install Plugins → Install from ZIP* → pick `raster_inspector.zip`.

**Or copy the folder** `raster_inspector/` into your profile's plugin directory, then
enable it in *Plugins → Manage and Install Plugins → Installed*:

| OS | Path |
|---|---|
| macOS | `~/Library/Application Support/QGIS/QGIS3/profiles/default/python/plugins/` |
| Windows | `%APPDATA%\QGIS\QGIS3\profiles\default\python\plugins\` |
| Linux | `~/.local/share/QGIS/QGIS3/profiles/default/python/plugins/` |

QGIS 4 uses the same layout under a `QGIS4` folder instead of `QGIS3`. If you're
not sure, use *Settings → User Profiles → Open Active Profile Folder*.

## Use

1. Load a raster and click the **Raster Inspector** toolbar button (or *Raster → Raster Inspector*).
2. In the panel, choose the **layer** and **band**.
3. On the map: **left-click** to add vertices, **right-click** to finish.
4. The polygon turns green and the panel shows **mean / min / max / pixels**.
5. Edit the **Sample ID** / **Note** if you like, then press **S** (or *Save*) to keep it,
   or **Esc** (or *Discard*) to drop it.

Saved polygons go to a memory layer (default `inspection_samples`) with the fields
`sample_id, note, raster, band, mean, min, max, pixel_count, created`.
Memory layers are temporary, so use *Export → Save Features As…* to keep them.

## Sample data

`sample_data/denali_dem_30m.tif` is a small test raster: a digital elevation model
of the Denali area, Alaska. It is resampled to 30 m (766 × 734 pixels) in an Albers
equal-area projection, with elevations from about 1,070 m to 6,165 m. Drag it into
QGIS and try sketching polygons over the summit and the surrounding glaciers.

## Differences from the workshop script

- It has a dock panel UI, and messages appear in the message bar instead of `print()`.
- Stats are computed **inside the polygon** (`QgsZonalStatistics`) rather than over its bounding box.
- The polygon is reprojected to the raster CRS before stats are computed, so the results are correct when the project CRS differs from the raster's.
- You can choose the raster and band explicitly instead of relying on the active layer.
- The code is Qt6-ready: it imports through `qgis.PyQt`, uses scoped enums and `QMetaType` field types.

## Build the upload zip

```bash
git archive --format=zip --prefix=raster_inspector/ -o raster_inspector.zip HEAD
```

This produces a clean zip (no `.git`, `__pycache__` or hidden files) whose contents
match the repository exactly, as plugins.qgis.org expects.
