@echo off
call "C:\Program Files\QGIS 3.30.2\bin\o4w_env.bat"
call "C:\Program Files\QGIS 3.30.2\qt5_env.bat"
call "C:\Program Files\QGIS 3.30.2\py3_env.bat"

@echo on
pyrcc5 -o resources.py resources.qrc