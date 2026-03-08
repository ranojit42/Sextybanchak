from flask import Flask, request, jsonify
import requests
from rich.progress import Progress

app = Flask(__name__)

def check_player_info(target_id):
    with Progress() as progress:
        task = progress.add_task("[cyan]Fetching player data...", total=100)
        
        cookies = {
            '_ga': 'GA1.1.2123120599.1674510784',
            '_fbp': 'fb.1.1674510785537.363500115',
            '_ga_7JZFJ14B0B': 'GS1.1.1674510784.1.1.1674510789.0.0.0',
            'source': 'mb',
            'region': 'MA',
            'language': 'ar',
            '_ga_TVZ1LG7BEB': 'GS1.1.1674930050.3.1.1674930171.0.0.0',
            'datadome': '6h5F5cx_GpbuNtAkftMpDjsbLcL3op_5W5Z-npxeT_qcEe_7pvil2EuJ6l~JlYDxEALeyvKTz3~LyC1opQgdP~7~UDJ0jYcP5p20IQlT3aBEIKDYLH~cqdfXnnR6FAL0',
            'session_key': 'efwfzwesi9ui8drux4pmqix4cosane0y',
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
            res = requests.post(
                'https://shop2game.com/api/auth/player_id_login', 
                cookies=cookies, headers=headers, json=json_data
            )

            if res.status_code != 200 or not res.json().get('nickname'):
                return {"error": "ID NOT FOUND"}

            player_data = res.json()
            nickname = player_data.get('nickname', 'N/A')
            region = player_data.get('region', 'N/A')

            progress.update(task, advance=35)

            # Ban check
            ban_url = f'https://ff.garena.com/api/antihack/check_banned?lang=en&uid={target_id}'
            ban_response = requests.get(ban_url, headers={
                'User-Agent': 'Mozilla/5.0 (Linux; Android 10; K) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Mobile Safari/537.36',
                'Accept': 'application/json, text/plain, */*',
                'referer': 'https://ff.garena.com/en/support/',
                'x-requested-with': 'B6FksShzIgjfrYImLpTsadjS86sddhFH',
            })

            progress.update(task, advance=35)
            ban_data = ban_response.json()

            # Default values
            is_banned = 0
            period = 0
            ban_reason = None

            if ban_data.get("status") == "success" and "data" in ban_data:
                is_banned = ban_data["data"].get("is_banned", 0)
                period = ban_data["data"].get("period", 0)
                api_reason = ban_data["data"].get("reason", "").strip()

                if is_banned:
                    # ✅ Fix: fallback reason if API empty
                    ban_reason = api_reason if api_reason else "use chet"
                else:
                    ban_reason = None

            return {
                "nickname": nickname,
                "region": region,
                "ban_status": "Banned" if is_banned else "Not banned",
                "ban_period": f"{period} months" if is_banned and period > 0 else None,
                "ban_reason": ban_reason
            }

        except requests.exceptions.RequestException as e:
            return {"error": str(e)}

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
