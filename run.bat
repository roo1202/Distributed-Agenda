@echo off
title Ejecutando servidor y cliente
color 0a

echo Iniciando servidor backend...
start "Servidor Backend" python server/backend/app/main.py

echo Iniciando cliente backend...
start "Cliente Backend" cmd /k "python client/backend/main.py"

echo Iniciando cliente frontend...
cd client/frontend
start "Cliente Frontend" npm run dev

echo Todos los procesos han sido iniciados.
pause