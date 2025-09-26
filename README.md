# Hex Labeler with Sync Backend

This project provides the single-page hex map labeler along with a lightweight
Python backend that persists map labels to an SQLite database. Running the
server allows multiple clients to share the same map ID and automatically keep
their labels synchronized.

## Running the server

```bash
python server.py
```

The server listens on port 8000 by default. Once it is running, open the
`hex_labeler_webapp_single_file_html_js.html` file through the server:

```
http://localhost:8000/hex_labeler_webapp_single_file_html_js.html
```

Labels are stored in `data/labels.db`. Every change in the UI is saved locally
(in `localStorage`) and also queued for synchronization with the backend. When
you load a map ID, the application first tries to fetch the latest copy from
the server and falls back to the local cache if the server is unavailable.
