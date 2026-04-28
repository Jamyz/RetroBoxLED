@ECHO off
setlocal enabledelayedexpansion
chcp 1252 >nul
title Recalbox Mirror SD
color 0A

set "config=%~dp0config.txt"

:main
cls
echo.
echo  ╔════════════════════════════════════════╗
echo  ║       RECALBOX MIRROR SD v2.0          ║
echo  ╚════════════════════════════════════════╝
echo.

if exist "%config%" (
    set i=0
    for /f "usebackq delims=" %%a in ("%config%") do (
        set /a i+=1
        if !i!==1 set "saved_roms=%%a"
        if !i!==2 set "saved_user=%%a"
    )
    echo  [√] Config: !saved_user!@!saved_roms!
) else (
    echo  [!] Aucune configuration sauvegardee
)
echo.
echo  [1] Lancer le mirror
echo  [2] Verifier la carte SD
echo  [3] Configurer les identifiants NAS
echo  [4] Quitter
echo.
set /p choix="  Choix: "

if "%choix%"=="1" goto :mirror
if "%choix%"=="2" goto :show
if "%choix%"=="3" goto :config
if "%choix%"=="4" goto :quit
goto :main

:config
cls
echo.
echo  ═══ CONFIGURATION NAS ═══
echo.
set /p roms="  Chemin reseau (ex: \\192.168.1.10\roms): "
set /p user="  Utilisateur: "
set /p pass="  Mot de passe: "
echo.
echo  Test de connexion...
net use "%roms%" /user:%user% %pass% >nul 2>&1
if errorlevel 1 (
    color 0C
    echo  [X] ECHEC - Verifiez vos identifiants
    net use "%roms%" /delete >nul 2>&1
    pause
    color 0A
    goto :main
)
net use "%roms%" /delete >nul 2>&1
(
echo %roms%
echo %user%
echo %pass%
) > "%config%"
color 0B
echo  [√] Configuration sauvegardee avec succes
timeout /t 2 >nul
color 0A
goto :main

:mirror
cls
echo.
echo  ═══ MIRROR SD ═══
echo.
set /p drive="  Lettre SD (ex: E): "
set "drive=%drive::=%"

if not exist "%drive%:\" (
    color 0C
    echo  [X] Lecteur %drive%: introuvable
    pause
    color 0A
    goto :main
)

if not exist "%config%" (
    color 0E
    echo  [!] Configuration manquante - Utilisez option [3]
    pause
    color 0A
    goto :main
)

set i=0
for /f "usebackq delims=" %%a in ("%config%") do (
    set /a i+=1
    if !i!==1 set "roms=%%a"
    if !i!==2 set "user=%%a"
    if !i!==3 set "pass=%%a"
)

echo  Connexion a %roms%...
net use "%roms%" /user:%user% %pass% >nul 2>&1
if errorlevel 1 (
    color 0C
    echo  [X] Connexion impossible - Verifiez la config
    pause
    color 0A
    goto :main
)

set "sys=%drive%:\systems"
echo  [√] Connecte
echo.
echo  Creation des dossiers...

mkdir "%sys%\default" 2>nul
mkdir "%sys%\favorites" 2>nul 
echo   [+] default
echo   [+] favorites

set c=2
for /f %%d in ('dir "%roms%" /ad /b 2^>nul') do (
    mkdir "%sys%\%%d" 2>nul
    echo   [+] %%d
    set /a c+=1
)

net use "%roms%" /delete >nul 2>&1
echo.
color 0B
echo  ════════════════════════════════════
echo   TERMINE - !c! dossiers crees
echo  ════════════════════════════════════
timeout /t 3 >nul
color 0A
goto :main

:show
cls
echo.
echo  ═══ VERIFICATION SD ═══
echo.
set /p drive="  Lettre SD (ex: E): "
set "drive=%drive::=%"

if not exist "%drive%:\systems" (
    color 0E
    echo  [!] Dossier systems introuvable sur %drive%:
    pause
    color 0A
    goto :main
)

echo.
echo  Contenu de %drive%:\systems:
echo  ────────────────────────────────
for /f %%d in ('dir "%drive%:\systems" /ad /b /on') do echo   • %%d
echo  ────────────────────────────────
echo.
pause
goto :main

:quit
cls
echo.
echo  Au revoir!
timeout /t 1 >nul
exit