Param(
    [string]$Python = "py -3.11",
    [string]$Keywords = "report,excel",
    [int]$Interval = 60
)

Write-Host "Creating virtual environment..."
& $Python -m venv .venv

Write-Host "Activating virtual environment..."
& .\.venv\Scripts\Activate

Write-Host "Installing requirements..."
& pip install -r buddy_mvp\requirements.txt

Write-Host "Running pywin32 post-install..."
& python .\.venv\Scripts\pywin32_postinstall.py -install

Write-Host "Setup complete. Launching the app..."
& $Python buddy_mvp\mvp.py --keywords $Keywords --interval $Interval