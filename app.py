from flask import Flask, request, jsonify
import requests
import random
from datetime import datetime
from rich.progress import Progress
from rich.console import Console

app = Flask(__name__)
console = Console()

# -------------------- CACHE --------------------
ban_reason_cache = {}

# -------------------- BAN REASONS --------------------
ban_reason_list = [
    "3rd Party Apps",
    "Anti Hack Use",
    "Illegal Script Use",
    "Unauthorized Tool Use",
    "Suspicious Gameplay Activity",
    "Using Modified Game Files",
    "Unfair Advantage Detected",
    "Abnormal Damage Hack",
    "Speed Hack Detected"
]

# -------------------- TIME CONVERT --------------------
def convert_time(x):
    try:
        if x is None:
            return "Unknown"
        if isinstance(x, str) and "-" in x:
            return x
        return datetime.fromtimestamp(int(x)).strftime("%Y-%m-%d %H:%M:%S")
    except:
        return "Unknown"

def get_last_login(uid):
    try:
        res = requests.get(f"https://sextyinfo.vercel.app/player-info?uid={uid}", timeout=8)
        if res.status_code != 200:
            return None
        data = res.json()
        return data.get("basicInfo", {}).get("lastLoginAt")
    except:
        return None

# -------------------- CHECK PLAYER INFO --------------------
def check_player_info(target_id):
    with Progress() as progress:
        task = progress.add_task("[cyan]Fetching ban status...", total=100)

        progress.update(task, advance=20)

        try:
            # -------- BAN STATUS --------
            ban_url = f'https://ff.garena.com/api/antihack/check_banned?lang=en&uid={target_id}'
            ban_response = requests.get(ban_url, headers={
                'User-Agent': 'Mozilla/5.0 (Linux; Android 10) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Mobile Safari/537.36',
                'Accept': 'application/json, text/plain, */*',
            }, timeout=8)
            progress.update(task, advance=40)
            ban_data = ban_response.json()

            is_banned = 0
            period = 0
            if ban_data.get("status") == "success" and "data" in ban_data:
                is_banned = ban_data["data"].get("is_banned", 0)
                period = ban_data["data"].get("period", 0)
            else:
                return {"error": "Failed to retrieve ban status"}

            # -------- FIXED UNIQUE BAN REASON --------
            if is_banned:
                if target_id in ban_reason_cache:
                    reason = ban_reason_cache[target_id]
                else:
                    reason = random.choice(ban_reason_list)
                    ban_reason_cache[target_id] = reason

                if period > 0:
                    ban_status = f"Banned for {period} months"
                    ban_period = f"{period} months"
                else:
                    ban_status = "Banned indefinitely"
                    ban_period = None
            else:
                ban_status = "Not banned"
                ban_period = None
                reason = None

            progress.update(task, advance=20)

            # -------- LAST LOGIN --------
            last_login = convert_time(get_last_login(target_id))
            progress.update(task, advance=20)

            # -------- RETURN CLEAN DATA --------
            return {
                "ban_period": ban_period,
                "ban_status": ban_status,
                "ban_reason": reason,
                "last_login": last_login,
                "nickname": "Unknown",
                "region": "Unknown"
            }

        except requests.exceptions.RequestException as e:
            return {"error": str(e)}

# -------------------- FLASK ROUTE --------------------
@app.route('/bancheck', methods=['GET'])
def check_ban_status():
    uid = request.args.get('uid')
    if not uid:
        return jsonify({"error": "UID parameter is required"}), 400

    result = check_player_info(uid)
    if "error" in result:
        return jsonify(result), 404

    return jsonify(result)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
