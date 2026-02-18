Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

$root = Split-Path -Parent $MyInvocation.MyCommand.Path

# Remove dist directory if it exists
$dist = Join-Path $root 'dist'
if (Test-Path $dist) {
    Write-Host "Removing $dist"
    Remove-Item $dist -Recurse -Force
} else {
    Write-Host "No dist directory to remove."
}

# Bump semantic version (patch) in pyproject.toml
$py = Join-Path $root 'pyproject.toml'
if (-not (Test-Path $py)) {
    Write-Error "pyproject.toml not found at $py"
    exit 1
}

if (-not (Get-Command uv -ErrorAction SilentlyContinue)) {
    Write-Error "uv command not found in PATH"
    exit 1
}

# Prefer uv-native version bump when available
$versionBumped = $false
Write-Host "Running: uv version --bump patch"
& uv version --bump patch
if ($LASTEXITCODE -eq 0) {
    $versionBumped = $true
    Write-Host "Version bumped with uv."
} else {
    Write-Host "uv version --bump patch not available or failed; falling back to pyproject.toml edit."
}

if (-not $versionBumped) {
    $content = Get-Content $py -Raw
    $regex = [regex] 'version\s*=\s*"(?<major>\d+)\.(?<minor>\d+)\.(?<patch>\d+)"'
    if ($regex.IsMatch($content)) {
        $match = $regex.Match($content)
        $major = [int]$match.Groups['major'].Value
        $minor = [int]$match.Groups['minor'].Value
        $patch = [int]$match.Groups['patch'].Value
        $newPatch = $patch + 1
        $newVersion = "$major.$minor.$newPatch"
        $newContent = $regex.Replace($content, "version = `"$newVersion`"", 1)
        Set-Content -Path $py -Value $newContent -Encoding UTF8
        $old = "$major.$minor.$patch"
        Write-Host "Bumped version: $old -> $newVersion"
    } else {
        Write-Error "No semantic version found in pyproject.toml"
        exit 1
    }
}

# Run uv build
Write-Host "Running: uv build"
& uv build
if ($LASTEXITCODE -ne 0) {
    Write-Error "uv build failed with exit code $LASTEXITCODE"
    exit $LASTEXITCODE
}

# Run uv publish
Write-Host "Running: uv publish"
& uv publish
if ($LASTEXITCODE -ne 0) {
    Write-Error "uv publish failed with exit code $LASTEXITCODE"
    exit $LASTEXITCODE
}

Write-Host "All done."
