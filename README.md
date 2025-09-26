# Hex Labeler with Firebase Sync Backend

This project packages a single-page hex-map labeler together with a lightweight
Python backend that persists map labels to a Firebase Realtime Database. By
serving the HTML client through the backend, multiple users can connect to the
same map ID and keep their labels synchronized across devices in near real time.

## Prerequisites

* Python 3.9 or newer.
* A Google Cloud project with the Firebase Realtime Database enabled (the
  default configuration in this repository points to the shared **osr-hex**
  project).

## Firebase setup

The backend communicates with Firebase using the public REST API and a database
secret, so no service account file or `firebase-admin` dependency is required.
The server ships with defaults that connect to the **osr-hex** Firebase project:

* **Database URL:** `https://osr-hex-default-rtdb.europe-west1.firebasedatabase.app/`
* **Database secret:** `jbk2dB7RupFXJitRNlfKST2a2KetiNrwHaIfD77O`

To point the backend at a different Firebase project, override the following
environment variables before starting the server:

```bash
export FIREBASE_DATABASE_URL="https://<project-id>-default-rtdb.firebaseio.com"
export FIREBASE_DATABASE_SECRET="<database-secret>"
```

You can obtain the database secret from the Firebase console by navigating to
*Project Settings → Service accounts* and expanding the **Database secrets**
section.

## Running the server locally

Install dependencies and start the backend:

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
  the backend is reachable. The latest server state is fetched when the map is
  loaded, falling back to the local cache if necessary.
* Keep your database secret private and rotate it regularly according to your
  organization's security policies.

## Troubleshooting

| Symptom | Possible fix |
| --- | --- |
| `Permission denied` responses from Firebase | Verify your Realtime Database rules allow access for requests authenticated with the configured database secret and that `FIREBASE_DATABASE_URL` is correct. |
| Backend fails with credential errors | Ensure the `FIREBASE_DATABASE_SECRET` environment variable is set correctly or that the default secret is still valid. |
| Web client cannot load data | Ensure you open the HTML file through the backend URL rather than directly from disk, and check that the server process is still running. |

