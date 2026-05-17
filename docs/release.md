# LearnKit Windows Release

The auto-updater MVP is Windows-only and requires a packaged PyInstaller build.
Running with `python -m app.main` stays in development mode: update checks can open
GitHub Releases, but automatic download/install is disabled.

## Version Sources

Keep these values aligned before publishing:

- `app/version.py`
- `pyproject.toml`
- Git tag, for example `v0.3.0`
- GitHub release asset name, for example `LearnKit-0.3.0-win.zip`

## Build

From the repository root:

```powershell
.\scripts\build_windows.ps1 -Version 0.3.0 -ReleaseUrl https://github.com/GlxV/learnkit/releases/tag/v0.3.0
```

The script creates:

- `dist/LearnKit-<version>-win.zip`
- `dist/latest.json`

The app build is PyInstaller `onedir`. The updater executable is copied beside
`LearnKit.exe` as `LearnKitUpdater.exe` so the running app can copy it to `%TEMP%`
before closing.
The zip also includes a lightweight `manifest.json`; the separate `latest.json`
asset is the authoritative manifest used by the updater because it contains the
SHA-256 of the zip.

## GitHub Release Assets

Upload both files to the GitHub Release:

- `LearnKit-<version>-win.zip`
- `latest.json`

The manifest has this shape:

```json
{
  "version": "0.3.0",
  "platform": "windows",
  "asset_name": "LearnKit-0.3.0-win.zip",
  "sha256": "...",
  "release_url": "https://github.com/GlxV/learnkit/releases/tag/v0.3.0",
  "notes": "..."
}
```

Without `latest.json` or `manifest.json` containing a SHA-256, LearnKit treats the
release as manual-only and disables `Update now`.

## Protected User Data

The updater never replaces these paths inside the install directory:

- `data/`
- `backups/`
- `logs/`
- `app/logs/`
- `.learnkit_update_backup/`

`data/learnkit.db` must not be included in the release zip.

## Manual End-to-End Check

1. Build version `0.1.0` and run it from a temporary install directory.
2. Put a fake `data/learnkit.db` in that directory.
3. Publish or simulate a release for `0.1.1` with `latest.json`.
4. Click `Verificar atualizacoes` in Configuracoes.
5. Confirm the dialog, download, SHA-256 validation, app close, updater launch and restart.
6. Confirm `data/learnkit.db`, `backups/` and `logs/` are still intact.
