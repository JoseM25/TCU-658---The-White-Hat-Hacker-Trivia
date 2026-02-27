# TCU-658 - The White Hat Hacker Trivia

Desktop trivia app built with `customtkinter`.

## Run in development

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
python .\main.py
```

## Build a single EXE (Windows)

```powershell
.\build_exe.ps1
```

Output:

- `dist\WhiteHatTrivia.exe`

The EXE is one-file and embeds:

- `recursos`
- `datos`
- `docs`

When running the frozen EXE, assets are copied on first launch to:

- `%LOCALAPPDATA%\The White Hat Hacker Trivia`

This keeps the game executable standalone while runtime files live in LocalAppData.
