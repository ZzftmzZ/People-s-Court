# Auto commit script - adds a dummy line to README.md and pushes to GitHub

# Change to project directory
Set-Location "C:\Users\caue.mgil\Downloads\curriculo-web-completo\People-s-Court"

# Pull latest changes to avoid conflicts
git pull

# Decide randomly whether to commit (70% chance)
if ((Get-Random -Minimum 1 -Maximum 101) -le 70) {
    # Random delay between 0 and 24 hours (in seconds)
    $delay = Get-Random -Minimum 0 -Maximum 86400
    Start-Sleep -Seconds $delay

    # Get current timestamp in ISO format
    $timestamp = (Get-Date).ToString('yyyy-MM-ddTHH:mm:ssZ')

    # Append dummy line to README.md
    Add-Content -Path README.md -Value "`n<!-- Auto activity commit $timestamp -->"

    # Stage, commit, and push
    git add README.md
    git commit -m "Auto activity commit $timestamp"
    git push
} else {
    # Skip this run
    Write-Output "Skipping auto commit this cycle."
}
