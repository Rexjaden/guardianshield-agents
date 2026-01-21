# Google Cloud Deployment Guide for GuardianShield

## Phase 1: Preparation (What YOU need to do in the Browser)

I cannot click these buttons for you, so please follow these steps to prepare the cloud environment:

1.  **Create an Account**: Go to [cloud.google.com](https://cloud.google.com) and sign in.
2.  **Create a Project**: Name it `guardianshield-production`.
    *   *Note: You may need to enable "Billing" to use Compute Engine.*
3.  **Create a Virtual Machine (VM)**:
    *   Go to **Compute Engine** > **VM Instances**.
    *   Click **Create Instance**.
    *   **Name**: `guardianshield-server-1`
    *   **Region**: Choose `us-east1` (South Carolina) since that is your HQ location.
    *   **Machine Type**: `e2-medium` (2 vCPUs, 4GB RAM) is a good starting point.
    *   **Boot Disk**: Change to **Ubuntu 22.04 LTS**. Increase size to **50GB**.
    *   **Firewall**: Check both boxes: `Allow HTTP traffic` and `Allow HTTPS traffic`.
    *   Click **Create**.

## Phase 2: Connecting the Repository (I handle the code, You handle the keys)

You asked about moving the repo. You usually **do not need to move** the repo. Instead, the Cloud VM simply downloads a copy of it from GitHub.

1.  **SSH into your new VM**:
    *   In the Google Cloud Console list of VMs, click the **SSH** button next to your new instance.
    *   A black terminal window will pop up.

2.  **Run the Setup Script**:
    *   Copy the command below and paste it into that SSH window:

```bash
# Download the setup script I wrote for you
wget https://raw.githubusercontent.com/Rexjaden/guardianshield-agents/main/cloud-setup.sh

# Make it executable
chmod +x cloud-setup.sh

# Run it
./cloud-setup.sh
```

*(Note: If your repo is currently set to Private on GitHub, the script will ask for a username/password. You would use your GitHub username and a Personal Access Token).*

## Phase 3: Finalizing

Once the script finishes:
1.  Copy the **External IP** address shown in the Google Cloud Console.
2.  Paste it into your browser.
3.  You should see your Professional Landing Page running live from Google Cloud!
