@echo off
echo Installing Merchant Pipeline dependencies...

REM Create and activate virtual environment
python -m venv .venv
call .venv\Scripts\activate

REM Upgrade pip
python -m pip install --upgrade pip

REM Install required dependencies
pip install -r requirements.txt

REM Optional: Install GPU dependencies if available
REM pip install torch torchvision cuda-python

echo.
echo Installation complete! You can now run:
echo python main.py
echo.
pause
