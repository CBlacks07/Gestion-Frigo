@echo off
echo ========================================
echo Construction de Gestion-Frigo
echo ========================================
echo.

REM Installer PyInstaller si nécessaire
echo Installation de PyInstaller...
pip install pyinstaller

echo.
echo Construction de l'executable...
pyinstaller build_installer.spec --clean

echo.
echo ========================================
echo Construction terminée !
echo L'exécutable se trouve dans : dist\Gestion-Frigo.exe
echo ========================================
pause
