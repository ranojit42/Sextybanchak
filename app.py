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
        task = progress.add_task("[cyan]Fetching player data...", total=100)

        # -------- DUMMY COOKIES & HEADERS --------
        cookies = {
            '_ga': 'GA1.1.2123120599.1674510784',
            '_fbp': 'fb.1.1674510785537.363500115',
            '_ga_7JZFJ14B0B': 'GS1.1.1674510784.1.1.1674510789.0.0.0',
            'source': 'mb',
            'region': 'MA',
            'language': 'ar',
            '_ga_TVZ1LG7BEB': 'GS1.1.1674930050.3.1.1674930171.0.0.0',
            'datadome': 'dummy_value',
            'session_key': 'dummy_key',
        }

        headers = {
            'Accept-Language': 'en-US,en;q=0.9',
            'Connection': 'keep-alive',
            'Origin': 'https://shop2game.com',
            'Referer': 'https://shop2game.com/app/100067/idlogin',
            'User-Agent': 'Mozilla/5.0 (Linux; Android 11; Redmi Note 8) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/107.0.0.0 Mobile Safari/537.36',
            'accept': 'application/json',
            'content-type': 'application/json',
        }

        json_data = {
            'app_id': 100067,
            'login_id': target_id,
            'app_server_id': 0,
        }

        try:
            progress.update(task, advance=30)

            # -------- GET PLAYER DATA --------
            res = requests.post(
                'https://shop2game.com/api/auth/player_id_login',
                cookies=cookies,
                headers=headers,
                json=json_data
            )

            if res.status_code != 200 or not res.json().get('nickname'):
                return {"error": "ID NOT FOUND"}

            player_data = res.json()
            nickname = player_data.get('nickname', 'N/A')
            region = player_data.get('region', 'N/A')

            progress.update(task, advance=10)

            # -------- LAST LOGIN --------
            last_login = convert_time(get_last_login(target_id))
            progress.update(task, advance=20)

            # -------- BAN STATUS --------
            ban_url = f'https://ff.garena.com/api/antihack/check_banned?lang=en&uid={target_id}'
            ban_response = requests.get(ban_url, headers={
                'User-Agent': 'Mozilla/5.0 (Linux; Android 10; K) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Mobile Safari/537.36',
                'Accept': 'application/json, text/plain, */*',
            })
            progress.update(task, advance=20)
            ban_data = ban_response.json()

            if ban_data.get("status") == "success" and "data" in ban_data:
                is_banned = ban_data["data"].get("is_banned", 0)
                period = ban_data["data"].get("period", 0)

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

                return {
                    "ban_period": ban_period,
                    "ban_status": ban_status,
                    "ban_reason": reason,
                    "last_login": last_login,
                    "nickname": nickname,
                    "region": region
                }

            else:
                return {"error": "Failed to retrieve ban status"}

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
