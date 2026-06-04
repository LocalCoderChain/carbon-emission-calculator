@echo off
echo Installing required packages...
pip install streamlit pandas mysql-connector-python openpyxl psutil --quiet
echo.
echo Setup complete! Double-click CarbonCalculator StartTheApp.bat to launch(start the app).
pause