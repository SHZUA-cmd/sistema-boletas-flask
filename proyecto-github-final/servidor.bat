@echo off
echo Activando entorno virtual e iniciando servidor...
echo.

:: Activa el entorno virtual
call venv\Scripts\activate

:: Inicia la aplicacion Flask
flask run

:: Mantiene la ventana abierta al cerrar el servidor
pause