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

$content = Get-Content $py -Raw
$regex = [regex] 'version\s*=\s*"(?<major>\d+)\.(?<minor>\d+)\.(?<patch>\d+)"'
if ($regex.IsMatch($content)) {
    $newContent = $regex.Replace($content, { param($m) "version = \"$($m.Groups['major'].Value).$($m.Groups['minor'].Value).$([int]$m.Groups['patch'].Value + 1)\"" })
    Set-Content -Path $py -Value $newContent -Encoding UTF8
    $match = $regex.Match($content)
    $old = "$($match.Groups['major'].Value).$($match.Groups['minor'].Value).$($match.Groups['patch'].Value)"
    $new = $regex.Match($newContent).Groups['major'].Value + "." + $regex.Match($newContent).Groups['minor'].Value + "." + $regex.Match($newContent).Groups['patch'].Value
    Write-Host "Bumped version: $old -> $new"
} else {
    Write-Error "No semantic version found in pyproject.toml"
    exit 1
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
