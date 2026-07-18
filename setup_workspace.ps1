# SSCG Workspace Auto-Setup & Launcher Script
Write-Host "=============================================" -ForegroundColor Cyan
Write-Host "   SSCG Workspace Setup & Launcher script    " -ForegroundColor Cyan
Write-Host "=============================================" -ForegroundColor Cyan

# 1. Check Python installation
if (Get-Command python -ErrorAction SilentlyContinue) {
    Write-Host "[√] Python is installed." -ForegroundColor Green
} else {
    Write-Host "[X] Python was not found in your PATH! Please install Python first." -ForegroundColor Red
    Exit
}

# 2. Setup and Activate Virtual Environment to avoid permission issues
if (-not (Test-Path ".\.venv")) {
    Write-Host "Creating Python virtual environment (.venv)..." -ForegroundColor Yellow
    python -m venv .venv
    if ($LASTEXITCODE -ne 0) {
        Write-Host "[X] Failed to create virtual environment. Falling back to global user-install." -ForegroundColor Red
        $UseVenv = $false
    } else {
        $UseVenv = $true
    }
} else {
    $UseVenv = $true
}

if ($UseVenv) {
    Write-Host "Activating virtual environment..." -ForegroundColor Yellow
    # Set execution policy for the session to allow activating venv if needed
    Set-ExecutionPolicy -ExecutionPolicy Bypass -Scope Process -Force
    .\.venv\Scripts\Activate.ps1
}

# 3. Check/Install required libraries
Write-Host "Checking and installing required dependencies (plotly, numpy, scipy, pandas, jupyter)..." -ForegroundColor Yellow
if ($UseVenv) {
    python -m pip install --upgrade pip
    python -m pip install plotly numpy scipy pandas jupyter
} else {
    # Fallback to user-install if venv creation failed
    python -m pip install --upgrade pip --user
    python -m pip install plotly numpy scipy pandas jupyter --user
}

if ($LASTEXITCODE -eq 0) {
    Write-Host "[√] Dependencies installed successfully!" -ForegroundColor Green
} else {
    Write-Host "[X] Dependency installation failed." -ForegroundColor Red
    Exit
}

# 4. Ask user if they want to run the standalone HTML generator
$run_gen = Read-Host "Would you like to run the standalone generator now to generate the interactive HTML reports? (Y/N)"
if ($run_gen -eq 'Y' -or $run_gen -eq 'y') {
    Write-Host "Running sscg_generator.py..." -ForegroundColor Yellow
    python sscg_generator.py
}

# 5. Launch Jupyter Notebook
Write-Host "Launching Jupyter Notebook. The browser will open automatically..." -ForegroundColor Cyan
if ($UseVenv) {
    # Run jupyter within the venv
    .\.venv\Scripts\jupyter-notebook.exe SSCG_Modelling.ipynb
} else {
    jupyter notebook SSCG_Modelling.ipynb
}

