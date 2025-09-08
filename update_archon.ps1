# Stop on errors
$ErrorActionPreference = "Stop"

# Path to the submodule
$submodulePath = "Archon"

# Check if the submodule has local changes
Set-Location -Path $submodulePath
$localChanges = git status --porcelain
if ($localChanges) {
    Write-Host "Warning: Local changes exist in submodule '$submodulePath'. Aborting update."
    exit 1
}

# Fetch and update submodule
git fetch origin 2>&1 | Write-Host
git checkout main 2>&1 | Write-Host
git pull origin main 2>&1 | Write-Host

# Go back to the main project root
Set-Location -Path ".."

# Stage the submodule pointer
git add $submodulePath

# Commit only if there are changes
if ((git status --porcelain) -ne "") {
    git commit -m "Update $submodulePath submodule to latest main" 2>&1 | Write-Host
} else {
    Write-Host "No changes to commit"
}

# Push main repo to its remote
git push 2>&1 | Write-Host
