# Hex Labeler with Firebase Sync Backend

This project packages a single-page hex-map labeler together with a lightweight
Python backend that persists map labels to a Firebase Realtime Database. By
serving the HTML client through the backend, multiple users can connect to the
same map ID and keep their labels synchronized across devices in near real time.

## Prerequisites

* Python 3.9 or newer.
* The `firebase-admin` Python package (`pip install firebase-admin`).
* A Google Cloud project with the Firebase Realtime Database enabled.

## Firebase setup

1. **Create or select a Firebase project.**
   * Visit [https://console.firebase.google.com](https://console.firebase.google.com) and create a new project (or reuse an existing one).
   * Make sure the project is upgraded to the Blaze plan if you expect the Realtime Database to be accessed from outside the United States or need production-grade throughput.
2. **Enable the Realtime Database.**
   * In the Firebase console, open *Build → Realtime Database* and click **Create database**.
   * Choose the region closest to your users and start in **Locked mode** (recommended) so only authenticated requests are allowed.
3. **Set up database rules.**
   * Adjust the security rules to match your needs. For a quick test you can temporarily allow read/write for authenticated users:
     ```json
     {
       "rules": {
         ".read": "auth != null",
         ".write": "auth != null"
       }
     }
     ```
   * For production, narrow these rules to the specific data paths that the app requires.
4. **Create a service account key for the backend.**
   * In the Firebase project settings, open the **Service Accounts** tab.
   * Click **Generate new private key** to download the JSON credentials file.
   * Store the file securely and do not commit it to version control.
5. **Collect the database URL.**
   * From the Realtime Database page, copy the instance URL. It looks like `https://<project-id>-default-rtdb.firebaseio.com/`.
6. **Configure environment variables.**
   * Export the following variables before running the server:
     ```bash
     export FIREBASE_CREDENTIALS="/absolute/path/to/service-account.json"
     export FIREBASE_DATABASE_URL="https://<project-id>-default-rtdb.firebaseio.com"
     ```
   * If `FIREBASE_CREDENTIALS` is omitted, the backend falls back to Application Default Credentials (ADC).

## Running the server locally

Install dependencies and start the backend:

```bash
pip install firebase-admin
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
* Keep your service account key private and rotate it regularly according to your
  organization's security policies.

## Troubleshooting

| Symptom | Possible fix |
| --- | --- |
| `Permission denied` responses from Firebase | Verify your Realtime Database rules allow access for the authenticated service account and that `FIREBASE_DATABASE_URL` is correct. |
| Backend fails with credential errors | Confirm the path in `FIREBASE_CREDENTIALS` points to an existing JSON key file and that the service account has the *Firebase Realtime Database Admin* role. |
| Web client cannot load data | Ensure you open the HTML file through the backend URL rather than directly from disk, and check that the server process is still running. |

