@echo off
cmd /k "cd /d C:\Nidec-tester\virtualenv\Scripts & activate & cd C:\Nidec-tester & pyinstaller --distpath "C:\Nidec-tester-release\deploy" --hidden-import=pyvisa --hidden-import=pyvisa_py --onedir --noconfirm --noconsole --icon="C:\Nidec-tester\resources\app_icon.ico" application.py --name Nidec-tester & pause & exit"
