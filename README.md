# Nudge

A liquid-glass desktop task widget for Windows. Always-on-top, draggable,
and out of the way, but right there when you need it.

![Nudge](icon.ico)

## Features

- **Liquid-glass UI** with frosted acrylic panels, dark and light themes.
- **Task list** with inline add / edit / delete, reordering, and groups.
- **History panel** for archived and completed tasks, with restore.
- **Export** to `.txt`, `.md`, or `.csv`, optionally with full history.
- **Keyboard shortcuts** for every common action.
- **Persistent state** under `%APPDATA%\Nudge\`, survives reinstalls
  and upgrades.
- **Portable mode** — drop a `portable.flag` file next to the EXE to keep
  state beside it (USB sticks, no-install setups).

## Download

Grab the latest Windows installer from the
[Releases](https://github.com/your-org/Nudge/releases) page. Download
`Nudge-version-.exe` and run it — it will install Nudge to
`%LOCALAPPDATA%\Programs\Nudge\` and create a Start Menu entry.

A portable `Nudge-version-windows.zip` is also provided for users who
want to run Nudge without installing.

### Windows SmartScreen

Because the installer is not yet code-signed, Windows may show a
**"Windows protected your PC"** prompt on first launch. This is
expected for any newly released app. To proceed:

1. Click **More info** in the dialog.
2. Click **Run anyway**.

If you'd like the warning to go away permanently, vote on
[issue #1](#) (tracking code-signing acquisition) or grab the
**portable zip** instead, which is also unsigned but smaller and
faster to verify.

## Keyboard Shortcuts

| Shortcut | Action                |
| -------- | --------------------- |
| `Ctrl+H` | Open History          |
| `Ctrl+,` | Open Settings         |
| `Ctrl+P` | Pin / unpin window    |
| `Alt+T`  | Always on top toggle  |
| `Ctrl+E` | Export tasks          |

All shortcuts are rebindable from **Settings → Shortcuts**.

## Data Location

By default Nudge stores its state in:

```
%APPDATA%\Nudge\
  ├── appstate.json   # theme, opacity, shortcuts, window position
  ├── tasks.json      # active tasks
  ├── groups.json     # task groups
  └── history.json    # archived / completed tasks
```

On first launch, Nudge will automatically migrate any state files it
finds next to the executable, as well as data from the previous
`%APPDATA%\RemindTaskWidget\` folder (rebrand migration).

### Portable mode

Create an empty file named `portable.flag` in the same folder as
`Nudge.exe`. Nudge will then store its state in a `data/` subfolder next
to the EXE.

## Building from source

```powershell
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
pyinstaller --noconfirm --clean Nudge.spec
```

The build output is `dist/Nudge/`. Run `Nudge.exe` from there.

## Releasing

1. Bump `__version__` in `src/__init__.py`.
2. Add a new section to `CHANGELOG.md`.
3. Commit and tag: `git tag v1.2.3`.
4. Push the tag: `git push origin v1.2.3`.
5. The GitHub Actions workflow will build, zip, and publish the release.

Manual dispatch from the Actions tab is also supported for dry runs.

## License

[MIT](LICENSE)
