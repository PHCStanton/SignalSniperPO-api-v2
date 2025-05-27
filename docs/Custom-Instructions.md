## Read Instructions Carefully:

You are a state of the art Coding Agent in the world. There is no Task or Project you can not  solve. With your Superior Knoledge Base and skill you only come up with the best robust and effective solutions possible. No time wasting only Robust most logical Solutions every time.
!! ALWAYS REMEMBER YOU ARE WORKING ON POWERSHELL ENVIRONMENT!! SO ; NOT &&

###Main Objectives:

1. Performing real trade executions Pocket Option.
2. Running the Telegram monitoring successfully with correct API integrations, Signal identifying and Parsing.
3. Running the Self_Bot_v.1.5 in a real session executing real automation. With the correct parsing format for pocket option to interpret @docs\parsing-Telegram-signals\signal-parsing-analysis.mdown
@docs\parsing-Telegram-signals\listening-parsing-trading-GPT-script.mdown
**Relative Documentation:**
@docs\🎯SelfBot.v1.5_Specs_Info_improvements\v.1.5.1-Improvement_Plan.md
@self_bot.py
Also see other relateSd documents not mentioned here.

## Previous Task completion Message:

Project Status Summary:

The self_bot.py enhancements (JSON storage and percentage-based amount calculator) are documented as completed.
The EC2 instance setup and deployment is the current focus, with the next steps to be performed by you (the user) via RDP on the Windows EC2 instance. These steps are detailed in Custom-Instructions.md and include connecting via RDP, installing necessary software (Git, Python), cloning the repository, installing dependencies, configuring NTP, performing latency checks, and running the bot.
Suggested Next Steps (after you complete the EC2 setup):

Verify the bot's operation and stability on the EC2 instance.
Test real trade execution capabilities.
Confirm the functionality of Telegram signal monitoring and parsing.
Update Custom-Instructions.md to reflect the new status.
The review of Custom-Instructions.md is complete. The next phase of EC2 deployment requires your direct action on the server.

## Important
Please keep the the solution concise and goal focused without any unnecessary documents created in Repository to reduce clutter..Be specific, focusing on the goal to get the bot real Trading Ready. If we test we test with real trading scripts. Do not use Testing Scripts to update code or any other real trading implementation. If it deems absolutely necessary. you will inform the user for permission, before running any Testing Script. with a logical explanation why it is  important. Keep in mind that the bigger the context in a chat the more the user pays for the solution. Have a precise and Clinical approach to solving problems effectively.

---
## EC2 Instance Setup and Deployment (Task from 2025-05-27)

**IMPORTANT NOTE:** The EC2 instance (i-0bbfba4a4b1e39cf5, Public IP: can change) is a **Windows System**. The following plan and actions are adjusted accordingly. The previous script `utils/deploy_to_ec2_with_ntp_and_latency.ps1` was designed for a Linux target and is not suitable for direct remote execution against a Windows EC2 in its previous form.

### Objective:
Connect to the Windows EC2 instance, deploy the repository, perform latency checks, and set up NTP.

### Revised Plan for Windows EC2:

1.  **[X] Prerequisites on Local Machine**
    *   Ensure you have an RDP client (e.g., Remote Desktop Connection on Windows).
    *   The PEM key (`EC2/eXP-BinaryBot.pem`) is used to retrieve the Administrator password for RDP via the AWS EC2 console.
    *   Git installed locally (for managing the repo before any potential manual transfer or if cloning directly on EC2).
2.  **[-] Connect to Windows EC2 Instance via RDP**
    *   Use the Public IPv4 address: `18.184.67.51`.
    *   Retrieve the Administrator password using your `EC2/eXP-BinaryBot.pem` file through the AWS Management Console (EC2 -> Instances -> Connect -> RDP client -> Get password).
    *   Connect using Remote Desktop Connection with username `Administrator` and the retrieved password.
3.  **[-] Prepare the Windows EC2 Instance (Manual Steps via RDP)**
    *   **Install Git:** If not already installed, download and install Git for Windows from [https://git-scm.com/download/win](https://git-scm.com/download/win).
    *   **Install Python:** If not already installed, download and install Python for Windows from [https://www.python.org/downloads/windows/](https://www.python.org/downloads/windows/). Ensure "Add Python to PATH" is checked during installation.
4.  **[-] Clone the Repository on Windows EC2**
    *   Open Command Prompt or PowerShell on the EC2 instance.
    *   Navigate to a suitable directory (e.g., `C:\Users\Administrator\Documents`).
    *   Clone the repository: `git clone -b SignalBot_v.1.5.2 https://github.com/PHCStanton/TradingBot.git`
    *   `cd TradingBot`
    *   Ensure `.gitignore` is present in the repository or create/update it as needed (e.g., to ignore `*.pem`, `*.env`, `local_data/`, `*.log`).
5.  **[-] Install Python Dependencies on Windows EC2**
    *   In the repository directory on EC2 (e.g., `C:\Users\Administrator\Documents\TradingBot`):
        `pip install -r requirements.txt`
6.  **[-] Set Up NTP (Windows Time Service) on Windows EC2**
    *   Open Command Prompt as Administrator on the EC2 instance.
    *   Check status: `w32tm /query /status`
    *   Force sync: `w32tm /resync /rediscover` (may require a few tries or waiting)
    *   Ensure the service is running: `sc query w32time` (should show RUNNING)
7.  **[-] Run an Effective Latency Check on Windows EC2**
    *   From Command Prompt on EC2: `ping 8.8.8.8 -n 10`
    *   If `utils/check_latency.py` is compatible and you want to run it: `python utils/check_latency.py` (from the repo directory).
8.  **[-] Deploy and Run the Bot/Service on Windows EC2**
    *   Navigate to the repository directory.
    *   Run the bot: `python self_bot.py` (or `python Self_bot.py` if that's the exact filename).
9.  **[X] Update @Custom_Instructions.md** (This step, reflecting Windows EC2).

### Actions Taken (Revised):

1.  **Clarified EC2 OS**: Confirmed the EC2 instance is a Windows System.
2.  **Previous Script Invalidated for Remote Windows Ops**: The script `utils/deploy_to_ec2_with_ntp_and_latency.ps1` (created earlier based on Linux assumption) is not suitable for direct remote command execution on the Windows EC2 instance as it was written. Local PEM permission settings in that script are still relevant if using WSL for local Git operations.
3.  **Updated Custom Instructions**: This section of `Custom-Instructions.md` has been updated to reflect the Windows EC2 environment and provide a manual RDP-based setup guide.

### Next Steps (User - To be performed on Windows EC2 via RDP):
*   **Connect to your Windows EC2 instance (18.184.67.51) using RDP.** Use your `EC2/eXP-BinaryBot.pem` key to get the Administrator password from the AWS console.
*   **Install Git and Python** on the EC2 instance if they are not already present.
*   **Clone the repository**: `git clone -b SignalBot_v.1.5.2 https://github.com/PHCStanton/TradingBot.git` into a suitable directory.
*   **Install Python dependencies**: `pip install -r requirements.txt` in the cloned repository directory.
*   **Configure Windows Time Service (NTP)**:
    *   `w32tm /query /status`
    *   `w32tm /resync /rediscover`
*   **Perform Latency Check**: `ping 8.8.8.8 -n 10` and optionally `python utils/check_latency.py`.
*   **Run your bot**: `python self_bot.py` from the repository directory.
*   **Manage `.gitignore`**: Ensure your repository's `.gitignore` file is adequate or create/update it on the EC2 instance before committing any local changes specific to the EC2 environment.
