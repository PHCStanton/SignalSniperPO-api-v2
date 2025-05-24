# check_ec2_directory.ps1
# This script checks if the EC2 directory exists and creates it if needed

Write-Host "Checking for EC2 directory..." -ForegroundColor Cyan

# Check if EC2 directory exists
if (-not (Test-Path "EC2")) {
    Write-Host "EC2 directory not found. Creating it..." -ForegroundColor Yellow
    
    try {
        New-Item -ItemType Directory -Path "EC2" -Force | Out-Null
        Write-Host "EC2 directory created successfully." -ForegroundColor Green
    }
    catch {
        Write-Host "Error creating EC2 directory: $_" -ForegroundColor Red
        exit 1
    }
} else {
    Write-Host "EC2 directory already exists." -ForegroundColor Green
}

# Check if key file exists
if (-not (Test-Path "EC2\whoami-in-Frankfurt.pem")) {
    Write-Host "`nWARNING: SSH key file 'EC2\whoami-in-Frankfurt.pem' not found!" -ForegroundColor Yellow
    Write-Host "You need to place your AWS key file in the EC2 directory." -ForegroundColor Yellow
    Write-Host "Please ensure you have downloaded the key file from AWS and placed it at:" -ForegroundColor Yellow
    Write-Host "  c:\www\Pocket-Option-API\PocketOptionAPI\EC2\whoami-in-Frankfurt.pem" -ForegroundColor Cyan
} else {
    Write-Host "`nSSH key file found at 'EC2\whoami-in-Frankfurt.pem'" -ForegroundColor Green
    Write-Host "You can now run the fix_ssh_key_permissions.ps1 script to fix permissions." -ForegroundColor Green
}

Write-Host "`nNext steps:" -ForegroundColor Cyan
Write-Host "1. Ensure your key file is in the EC2 directory" -ForegroundColor White
Write-Host "2. Run .\fix_ssh_key_permissions.ps1 to fix permissions" -ForegroundColor White
Write-Host "3. Try connecting with: ssh -i EC2/whoami-in-Frankfurt.pem ubuntu@3.126.128.227" -ForegroundColor White
