@echo off
IF "%1"=="-gui" (
start py -3 GUI.py
console /c py -3 Server.py
) ELSE (
console /c  py -3 Server.py
)
