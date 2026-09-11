# Workbench backend

This Slice 1 API is unauthenticated and intended only for local use. Bind it to
the loopback interface; do not expose it on a LAN or public address.

```sh
uv run --extra dev uvicorn app.main:create_app --factory --host 127.0.0.1 --port 8000
```

The default SQLite database is `instance/workbench.db`. The backend creates the
directory and database with private permissions. Override the path with
`WORKBENCH_DATABASE_URL` when needed.

Apply the persisted schema explicitly with:

```sh
uv run alembic upgrade head
```

Optional Zotero import/export reads `ZOTERO_API_KEY`, `ZOTERO_USER_ID`, and
`ZOTERO_LIBRARY_TYPE` from the backend environment. The key is never returned
to the browser or included in project exports. Use the integration endpoints
`/projects/{project_id}/integrations/zotero/import` and
`/projects/{project_id}/integrations/zotero/export`.
