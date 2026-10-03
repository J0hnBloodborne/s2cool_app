# Oracle A1 demo setup

Use an **Ubuntu 24.04 ARM64** image and the **VM.Standard.A1.Flex** shape.
Choose a size marked Always Free in your account. Oracle currently lists
2 OCPUs and 12 GB RAM in total for an Always Free account, plus up to 200 GB
of block storage. Confirm the allowance shown in your account before
creating the VM. [Oracle's resource limits](https://docs.oracle.com/en-us/iaas/Content/FreeTier/freetier_topic-Always_Free_Resources.htm)

Use a public IP and allow SSH from your own IP. The first demo uses an SSH
tunnel, so the app needs no public web port or domain.

## 1. Upload the app

On this Windows PC, build the bundle:

```powershell
.\.venv\Scripts\python.exe scripts\build_bundle.py
scp -i "C:\path\oracle.key" build\s2cool-oracle-demo.zip ubuntu@VM_PUBLIC_IP:~/
ssh -i "C:\path\oracle.key" ubuntu@VM_PUBLIC_IP
```

Replace the key path and `VM_PUBLIC_IP` with your connection details.

On the VM:

```bash
sudo apt-get update
sudo apt-get install -y unzip
sudo mkdir -p /opt/s2cool/app
sudo unzip -o ~/s2cool-oracle-demo.zip -d /opt/s2cool/app
cd /opt/s2cool/app
sudo bash deployment/install-ubuntu.sh
```

The script installs the app and all six model options, including CPU-only
PyTorch for LSTMs. It asks you to set a demo username and password. It saves
the password as a hash. It then starts the app and enables automatic restart.

If a model package fails to install, stop and inspect that error before
continuing. The selected packages have ARM64 wheels; the actual server still
needs the check below. [PyTorch CPU install](https://pytorch.org/get-started/locally/),
[CatBoost ARM support](https://catboost.ai/docs/en/installation/python-installation-method-pip-install)

## 2. Check the server

```bash
sudo systemctl status s2cool --no-pager
curl --fail http://127.0.0.1:8050/healthz
sudo -u s2cool /opt/s2cool/app/.venv/bin/python /opt/s2cool/app/scripts/smoke_demo.py --full --report /var/lib/s2cool/arm-check.json
```

For memory readings too, first run:

```bash
sudo /opt/s2cool/app/.venv/bin/python -m pip install psutil
```

The model check uses a temporary copy of the sample data. It does not change
saved work. It prints the time for each check. Compare the report on this
actual A1 server before choosing longer training settings.

## 3. Open the demo

Keep this command running on your Windows PC:

```powershell
ssh -i "C:\path\oracle.key" -N -L 8051:127.0.0.1:8050 ubuntu@VM_PUBLIC_IP
```

Open <http://127.0.0.1:8051> and enter the demo login. SSH encrypts the link
to the server. Each person who uses this method needs SSH access to the VM.

For a public browser link, point a domain at the VM and use HTTPS. The app
already requires the demo login. Ubuntu can run Caddy as the HTTPS front end:

```bash
sudo apt-get install -y caddy
sudo nano /etc/caddy/Caddyfile
```

Put your real domain in this file:

```caddyfile
demo.example.com {
    encode gzip
    reverse_proxy 127.0.0.1:8050
}
```

Validate the file and restart Caddy:

```bash
sudo caddy validate --config /etc/caddy/Caddyfile
sudo systemctl restart caddy
```

Allow TCP 80 and 443 in the Oracle network rules and the VM firewall. Keep
8050 bound to localhost. Caddy handles the HTTPS certificate.
[Caddy HTTPS setup](https://caddyserver.com/docs/automatic-https)

## Updates and saved work

The code is in `/opt/s2cool/app`. Saved work is in `/var/lib/s2cool`.
Upload a new bundle, unzip it over the code, then run the install script again.
Existing profiles and models stay in the data folder. Keep the package
versions used to create trained models; retrain them after an incompatible
model-library update.

```bash
sudo systemctl restart s2cool
sudo journalctl -u s2cool -n 50 --no-pager
sudo /opt/s2cool/app/.venv/bin/python /opt/s2cool/app/scripts/configure_demo_access.py /etc/s2cool/demo.env
```

The last command changes the demo login. Restart the service after it.

## Backup

```bash
sudo bash /opt/s2cool/app/deployment/backup.sh
```

This briefly stops the app, saves the data folder under
`/var/backups/s2cool`, and starts the app again. Copy that archive off the VM
through SSH. For example, first copy it to the Ubuntu user's home folder
with mode 600, then use `scp` from your PC. Delete that temporary home copy
after the transfer.

To test a restore, unpack the archive into a separate empty folder first.
Check that it contains `config/`, both data trees, and `models/`. Restore
into `/var/lib/s2cool` only while the service is stopped, then set its owner
back to `s2cool:s2cool` and start the service.

Oracle can reclaim an idle free VM. Keep the off-server copy of saved work.
The app uses no paid cloud service in this demo setup.
