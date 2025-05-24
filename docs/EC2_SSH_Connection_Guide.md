# EC2 SSH Connection Troubleshooting Guide

This document provides a comprehensive guide to troubleshoot and fix SSH connection issues to your EC2 instance.

## Understanding the Issue

Based on the analysis of your deployment scripts and documentation, the most likely cause of your SSH connection issue is **incorrect permissions on the SSH key file**. Windows is particularly strict about SSH private key permissions, and if they're not set correctly, the SSH connection will be rejected without a clear error message.

## Solution: Fix SSH Key Permissions

I've created a PowerShell script (`fix_ssh_key_permissions.ps1`) that will automatically fix the permissions on your SSH key file. Here's how to use it:

1. **Run PowerShell as Administrator**:
   - Right-click on PowerShell in the Start menu
   - Select "Run as Administrator"

2. **Navigate to your project directory**:
   ```powershell
   cd c:/www/Pocket-Option-API/PocketOptionAPI
   ```

3. **Run the fix permissions script**:
   ```powershell
   .\fix_ssh_key_permissions.ps1
   ```

4. **Try connecting again**:
   ```powershell
   ssh -i EC2/whoami-in-Frankfurt.pem ubuntu@3.126.128.227
   ```

## Additional Troubleshooting Steps

If fixing the permissions doesn't resolve the issue, try these additional troubleshooting steps:

### 1. Verify the EC2 Instance is Running

Check that your EC2 instance is actually running in the AWS Management Console:
- Log in to the AWS Management Console
- Navigate to EC2 > Instances
- Verify that instance with IP 3.126.128.227 is in the "running" state
- Check that the instance's security group allows inbound SSH (port 22)

### 2. Check Network Connectivity

Verify that you can reach the EC2 instance:
```powershell
Test-NetConnection -ComputerName 3.126.128.227 -Port 22
```

### 3. Verify the Key File Path

Ensure the key file exists at the specified path:
```powershell
Test-Path EC2/whoami-in-Frankfurt.pem
```

If the file doesn't exist, you may need to:
- Check if the file is in a different location
- Download a new copy of the key file from AWS
- Create the EC2 directory if it doesn't exist: `mkdir -p EC2`

### 4. Check for SSH Client Installation

Verify that SSH is installed and available in your PATH:
```powershell
Get-Command ssh
```

If not found, you may need to:
- Install OpenSSH Client from Windows Features
- Or install Git for Windows which includes SSH

### 5. Try Verbose Mode

Run SSH with verbose output to get more information about the connection issue:
```powershell
ssh -v -i EC2/whoami-in-Frankfurt.pem ubuntu@3.126.128.227
```

### 6. Check AWS Security Groups

Ensure that the EC2 instance's security group allows inbound SSH connections from your IP address:
- In AWS Console, go to EC2 > Security Groups
- Find the security group associated with your instance
- Verify that there's an inbound rule allowing TCP port 22 from your IP address or from anywhere (0.0.0.0/0)

## Common SSH Error Messages and Solutions

### "Permission denied (publickey)"
- This usually means the key file permissions are incorrect or the key doesn't match what's configured on the EC2 instance
- Solution: Fix key permissions and verify the key pair is correct

### "Connection timed out"
- This usually means the EC2 instance is not reachable due to network issues or security group restrictions
- Solution: Check security groups and network connectivity

### "Host key verification failed"
- This means the host key has changed since your last connection
- Solution: Remove the old host key with `ssh-keygen -R 3.126.128.227`

## Next Steps After Connecting

Once you've successfully connected to the EC2 instance, you can:

1. **Check the status of the Self Bot service**:
   ```bash
   sudo systemctl status selfbot.service
   ```

2. **View the logs**:
   ```bash
   sudo journalctl -u selfbot.service -f
   ```

3. **Update the SSID in the configuration**:
   ```bash
   nano ~/selfbot/config/pocket_option_config.json
   ```

4. **Restart the service after making changes**:
   ```bash
   sudo systemctl restart selfbot.service
   ```

## Conclusion

SSH connection issues are often related to key file permissions, especially on Windows. The provided PowerShell script should fix the most common permission issues. If you continue to experience problems, follow the additional troubleshooting steps or consider using an alternative SSH client like PuTTY.
