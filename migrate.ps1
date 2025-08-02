# Create migrations and versions folders if missing
if (-not (Test-Path -Path "./migrations")) {
    mkdir migrations
    Write-Host "Created 'migrations' folder."
}

if (-not (Test-Path -Path "./migrations/versions")) {
    mkdir migrations\versions
    Write-Host "Created 'migrations/versions' folder."
}

# Set FLASK_APP environment variable for this session
$env:FLASK_APP = "run.py"
Write-Host "Set FLASK_APP=run.py"

# Run Alembic migration commands
Write-Host "Running flask db migrate..."
flask db migrate -m "Initial migration"

Write-Host "Running flask db upgrade..."
flask db upgrade

Write-Host "Migration complete!"
