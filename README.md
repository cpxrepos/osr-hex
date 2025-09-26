# Hex Labeler with Firebase Sync Backend

This project packages a single-page hex-map labeler that persists map labels
directly to a Firebase Realtime Database. Multiple users can connect to the
same map ID and keep their labels synchronized across devices in near real
time, even when the HTML file is hosted as static content.

## Prerequisites

* Python 3.9 or newer.
* A Google Cloud project with the Firebase Realtime Database enabled (the
  default configuration in this repository points to the shared **osr-hex**
  project).

## Firebase setup

The web client communicates with Firebase using the public REST API. By default
it targets the shared **osr-hex** Firebase project:

* **Database URL:** `https://osr-hex-default-rtdb.europe-west1.firebasedatabase.app/`

To point the client at your own Firebase project, define a global configuration
object before the main script executes. When self-hosting, add the following
snippet above the inline script block in
`hex_labeler_webapp_single_file_html_js.html` or inject it from your hosting
platform:

```html
<script>
  window.HEX_LABELER_FIREBASE_CONFIG = {
    databaseURL: "https://<project-id>-default-rtdb.firebaseio.com",
    // Optional: supply an auth token when your database rules require it
    // authToken: "<database-secret-or-custom-token>"
  };
</script>
```

Ensure your Realtime Database rules allow unauthenticated read/write access (or
provide a token through `authToken`) for the paths you plan to use, for example:

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

> ⚠️ Opening your database to the public means anyone with the URL can read and
> modify your data. Consider restricting access to specific map IDs, using
> Firebase Authentication, or serving the app behind your own backend if you
> need stronger guarantees.

If you prefer to keep the database secret out of the browser, you can still run
the bundled Python backend described below.

## Running the optional Python proxy

Install dependencies and start the backend if you do not want to expose a
database secret to the browser or prefer server-side access control:

```bash
python server.py
```

The server listens on port 8000 by default. Once it is running, load the web
client through the backend so that API calls are proxied correctly:

```
http://localhost:8000/hex_labeler_webapp_single_file_html_js.html
```

## Usage tips

* Each map is identified by a `mapId`. Share the same ID with your group to
  collaborate.
* Labels are stored locally in `localStorage` and synchronized to Firebase when
  the database is reachable. The latest server state is fetched when the map is
  loaded, falling back to the local cache if necessary.
* When using open database rules, consider choosing opaque map IDs to avoid
  collisions with other users.
* Keep your database secret private and rotate it regularly if you rely on an
  `authToken` or the Python proxy.

## Troubleshooting

| Symptom | Possible fix |
| --- | --- |
| `Permission denied` responses from Firebase | Verify your Realtime Database rules allow the requested operation or supply a valid `authToken` in `HEX_LABELER_FIREBASE_CONFIG`. |
| Updates are not syncing | Confirm that the page is served over `http(s)` (not from the `file://` scheme) so the map image is not treated as cross-origin, and that your Firebase database is reachable. |
| Prefer not to expose a database secret | Use the bundled Python proxy and keep the secret server-side instead of adding it to `HEX_LABELER_FIREBASE_CONFIG`. |

