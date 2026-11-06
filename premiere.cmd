@echo off
rem LOCAL (so nesta maquina, fora do git): o kit com o Premiere Pro no lugar do FilmCraft. Ver CLAUDE.local.md
"%LOCALAPPDATA%\STLFLIX_EDITOR\venv\Scripts\python.exe" -m stlflix.premiere %*
