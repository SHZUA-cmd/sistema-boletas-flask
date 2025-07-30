@echo off
echo.
echo ==================================================
echo    Script de Limpieza y Reseteo de Base de Datos
echo ==================================================
echo.

REM Verifica y elimina la carpeta de la base de datos
IF EXIST "instance" (
    echo Eliminando la base de datos y la carpeta 'instance'...
    rmdir /s /q "instance"
    echo Carpeta 'instance' eliminada.
) ELSE (
    echo No se encontro la carpeta 'instance'. No hay nada que borrar.
)

echo.

REM Verifica y elimina la cache de Python
IF EXIST "project\__pycache__" (
    echo Limpiando la cache de Python ('__pycache__')...
    rmdir /s /q "project\__pycache__"
    echo Cache eliminada.
)

echo.
echo Limpieza completada.
echo.
echo Ahora puedes ejecutar 'iniciar_servidor.bat' o 'flask run'.
echo La base de datos se creara de nuevo, completamente limpia.
echo.
pause