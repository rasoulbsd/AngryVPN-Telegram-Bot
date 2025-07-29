import base64
import json
import os
import subprocess
import tempfile
import time
import sys
import signal

# -------- USER CONFIG --------
V2RAY_BIN = "/usr/local/bin/v2ray"
TEST_URL = "https://api.ip.sb"
# -----------------------------


def decode_vmess(vmess_url):
    if not vmess_url.startswith("vmess://"):
        raise ValueError("Invalid VMess URL format.")
    b64 = vmess_url.replace("vmess://", "")
    padded = b64 + "=" * (-len(b64) % 4)
    decoded = base64.b64decode(padded).decode("utf-8")
    return json.loads(decoded)


def write_config(vmess_conf, config_path):
    outbound = {
        "protocol": "vmess",
        "settings": {
            "vnext": [{
                "address": vmess_conf["add"],
                "port": int(vmess_conf["port"]),
                "users": [{
                    "id": vmess_conf["id"],
                    "alterId": 0,
                    "security": "auto"
                }]
            }]
        },
        "streamSettings": {
            "network": vmess_conf["net"],
            "security": vmess_conf["tls"],
            "wsSettings": {
                "path": vmess_conf.get("path", "")
            }
        }
    }

    full_conf = {
        "inbounds": [{
            "port": 10808,
            "listen": "127.0.0.1",
            "protocol": "socks",
            "settings": {"auth": "noauth"}
        }],
        "outbounds": [outbound]
    }

    with open(config_path, "w") as f:
        json.dump(full_conf, f, indent=2)


def check_proxy():
    try:
        result = subprocess.run(
            ["curl", "--socks5-hostname", "127.0.0.1:10808", TEST_URL, "--max-time", "10"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )
        return result.returncode == 0
    except Exception:
        return False


def run_v2ray(config_path):
    return subprocess.Popen([V2RAY_BIN, "-config", config_path],
                            stdout=subprocess.DEVNULL,
                            stderr=subprocess.DEVNULL)


def main(vmess_url):
    with tempfile.TemporaryDirectory() as tmpdir:
        config_path = os.path.join(tmpdir, "config.json")
        try:
            conf = decode_vmess(vmess_url)
        except Exception as e:
            print(f"❌ Error decoding VMess URL: {e}")
            return

        write_config(conf, config_path)

        print(f"🟡 Checking: {conf.get('ps', conf['add'])}:{conf['port']} ...")

        v2ray_proc = run_v2ray(config_path)
        time.sleep(3)  # give v2ray time to start

        try:
            if check_proxy():
                print(f"✅ VMess WORKS: {conf['add']}:{conf['port']}")
            else:
                print(f"❌ VMess FAILED: {conf['add']}:{conf['port']}")
        finally:
            os.kill(v2ray_proc.pid, signal.SIGTERM)


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python check_vmess.py 'vmess://<base64>'")
        sys.exit(1)

    vmess_url = sys.argv[1]
    main(vmess_url)
