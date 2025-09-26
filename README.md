# OSR Hex Labeler

A single-page hex-map labeling tool for tabletop campaigns. The app lives in
`index.html` and can be hosted as plain static content. It ships with a blank
Dolmenwood map but can be pointed at any accessible image and keeps labels in
sync across browsers through Firebase.

## Highlights

* **Client-side UI only.** One HTML file contains the UI, styling, and
  JavaScript required to run the editor.
* **Grid-aware labels.** Drag the “Drag to add label” chip onto the map to spawn
  a new marker. The tool analyses the underlying image, snaps labels to the
  detected hex centres, and lets you fine-tune the overlay scale and offsets.
* **Persistent map IDs.** Pick a `mapId` to group labels. Data is stored in the
  browser’s `localStorage` and, when configured, mirrored to Firebase so other
  devices see the same state.
* **Import/export.** Back up or migrate maps as JSON and re-import them later to
  restore labels, settings, and the image reference.
* **Keyboard- and mouse-friendly.** Drag to pan, scroll to zoom, and edit or
  delete labels through the modal editor or the `Delete` key.

## Repository layout

| Path | Description |
| --- | --- |
| `index.html` | The complete Hex Labeler application. |
| `Dolmenwood_Blank_Hex_Map.png` | Default map bundled with the app. Replace it or change the default source in the script to use your own art. |
| `firebase_db.py` | Helper routines for integrating a Python backend with Firebase if you prefer server-side access. |
| `data/` | Reserved for future data exports/imports. Empty by default. |

## Quick start

1. Serve the repository folder as static files (for example with
   `python -m http.server 8000`).
2. Open `http://localhost:8000/index.html` in your browser.
3. Enter a `mapId` or keep the default (`dolmenwood`). The app will load saved
   state for that ID from your browser (and Firebase, if enabled).

> Opening the file with the `file://` scheme is supported but some browsers may
> block features like JSON downloads or cross-origin map images. A local HTTP
> server is recommended.

## Using your own map art

* Replace `Dolmenwood_Blank_Hex_Map.png` with another image and keep the same
  filename, **or** edit the initialization call near the bottom of
  `index.html` to point to a different path/URL.
* Export a map (`Export JSON`), update the `img.src` field in the JSON to any
  reachable image, then import it again. The app will load that image and store
  it with the map record.
* Align the detected grid using the **Advanced tools** panel: toggle the grid,
  adjust the scale and offsets, and click **Reset grid adjustments** if you need
  to revert.

## Firebase synchronisation

The app speaks to Firebase Realtime Database via its REST API. By default it
points to the shared **osr-hex** project
(`https://osr-hex-default-rtdb.europe-west1.firebasedatabase.app/`). Data for a
map lives under `maps/<mapId>` with this shape:

```json
{
  "mapId": "dolmenwood",
  "labels": [
    { "id": "...", "x": 123.4, "y": 456.7, "hex": "0805", "text": "Label" }
  ],
  "options": {
    "showGrid": true,
    "gridAdjust": { "scale": 90, "offsetX": 214, "offsetY": 120 }
  },
  "imgMeta": {
    "src": "Dolmenwood_Blank_Hex_Map.png",
    "naturalWidth": 1700,
    "naturalHeight": 1200
  },
  "updatedAt": "2024-01-01T00:00:00.000Z"
}
```

To use your own Firebase project, declare a configuration object before the
inline script runs:

```html
<script>
  window.HEX_LABELER_FIREBASE_CONFIG = {
    databaseURL: "https://<project-id>-default-rtdb.firebaseio.com",
    // Optional: include an auth token when your database rules require it.
    // authToken: "<database-secret-or-custom-token>"
  };
</script>
```

Ensure the database rules allow the desired access. A permissive development
setup might look like:

```json
{
  "rules": {
    "maps": {
      ".read": true,
      ".write": true
    }
  }
}
```

> ⚠️ Public read/write rules mean anyone with the URL can edit your maps. Use an
> auth token or tighter rules for production use.

## Tips and troubleshooting

| Issue | Suggested fix |
| --- | --- |
| Firebase calls fail with `Permission denied`. | Check your Realtime Database rules or provide an `authToken` in `HEX_LABELER_FIREBASE_CONFIG`. |
| The map never loads. | Confirm the image path/URL is reachable from the browser and serve the app over HTTP(S) rather than `file://`. |
| Labels stop syncing between devices. | Verify the devices use the same `mapId`, have network access to Firebase, and that no conflicting JSON imports overwrote data. |
| Grid overlay is misaligned. | Use the advanced controls to tweak scale and offsets or reset them to the defaults. |

## Extending the project

The `firebase_db.py` module contains thin wrappers around the Firebase REST API
for Python. You can build a proxy service with it when you prefer to hide your
Firebase credentials from the browser or need to enforce server-side policies.
