@echo off
REM ============================================================
REM SEXTA-FEIRA — Build do Satélite PC (.exe)
REM ============================================================
REM Gera um executável standalone usando PyInstaller.
REM O .exe pode ser instalado em qualquer PC Windows sem
REM precisar do Python instalado.
REM
REM Pré-requisitos:
REM   pip install pyinstaller
REM
REM Uso:
REM   build.bat
REM ============================================================

echo.
echo ========================================
echo  SEXTA-FEIRA - Build do Satelite PC
echo ========================================
echo.

REM Instala dependências se necessário
pip install -r requirements.txt
pip install pyinstaller

echo.
echo [*] Gerando executavel...
echo.

REM Gera o .exe com ícone (se disponível)
REM --onefile    = Tudo em um arquivo
REM --noconsole  = Sem janela do terminal (roda em background)
REM --name       = Nome do executável
pyinstaller ^
    --onefile ^
    --noconsole ^
    --name "SextaFeira_Satelite" ^
    --add-data ".env;." ^
    main_satelite.py

echo.
echo ========================================
echo  Build concluido!
echo  Executavel em: dist\SextaFeira_Satelite.exe
echo ========================================
echo.

pause
