from flask import Flask, jsonify, request
import requests
from typing import Dict, Optional

app = Flask(__name__)

# ---------------- CORS Handling ----------------
def add_cors_headers(response):
    response.headers['Access-Control-Allow-Origin'] = 'https://flamexhub.vercel.app'
    response.headers['Access-Control-Allow-Methods'] = 'GET, POST, OPTIONS'
    response.headers['Access-Control-Allow-Headers'] = 'Content-Type, Authorization'
    response.headers['Access-Control-Max-Age'] = '86400'
    return response

@app.after_request
def after_request(response):
    return add_cors_headers(response)

@app.before_request
def handle_preflight():
    if request.method == "OPTIONS":
        response = jsonify({'status': 'ok'})
        response = add_cors_headers(response)
        return response

# ---------------- Garena API Call ----------------
def check_ban_garena(uid: str, lang: str = "en") -> Optional[Dict]:
    api_url = "https://ff.garena.com/api/antihack/check_banned"
    
    # Browser-style headers (like Chrome)
    headers = {'Accept': 'application/json, text/plain, */*', 'Accept-Encoding': 'gzip, deflate, br, zstd', 'Accept-Language': 'en-US,en;q=0.9', 'Referer': 'https://ff.garena.com/en/support/', 'Sec-Ch-Ua': '"Chromium";v="140", "Not=A?Brand";v="24", "Google Chrome";v="140"', 'Sec-Ch-Ua-Mobile': '?0', 'Sec-Ch-Ua-Platform': '"Windows"', 'Sec-Fetch-Dest': 'empty', 'Sec-Fetch-Mode': 'cors', 'Sec-Fetch-Site': 'same-origin', 'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/140.0.0.0 Safari/537.36', 'X-Requested-With': 'B6FksShzIgjfrYImLpTsadjS86sddhFH' }
    
    params = {"lang": lang, "uid": uid}
    
    try:
        response = requests.get(api_url, params=params, headers=headers, timeout=15)
        if response.status_code != 200:
            return {"error": True, "message": f"API returned status {response.status_code}"}
        
        try:
            return response.json()
        except ValueError:
            return {"error": True, "message": "Invalid JSON response from Garena"}
    except Exception as e:
        return {"error": True, "message": f"Request failed: {str(e)}"}

# ---------------- Routes ----------------
@app.route('/')
def health_check():
    return jsonify({
        "status": "success",
        "message": "Free Fire Ban Check API is running",
        "version": "2.0.1",
        "api_source": "Official Garena API"
    })

@app.route('/api/check-ban/<uid>')
def check_ban_status(uid):
    try:
        if not uid or not uid.isdigit():
            return jsonify({
                "status": "error",
                "message": "Invalid UID. Please provide a valid numeric user ID.",
                "data": None
            }), 400
        
        lang = request.args.get('lang', 'en')
        ban_data = check_ban_garena(uid, lang)
        
        if ban_data is None:
            return jsonify({
                "status": "error",
                "message": "Could not retrieve ban information. Please try again later.",
                "data": None
            }), 503
        
        if ban_data.get("error"):
            return jsonify({
                "status": "error",
                "message": ban_data.get("message", "API returned an error"),
                "data": None
            }), 400
        
        response_data = {
            "uid": uid,
            "language": lang,
            "garena_response": ban_data,
            "api_source": "Official Garena API"
        }
        
        return jsonify({
            "status": "success",
            "message": "Ban check completed successfully",
            "data": response_data
        })
        
    except Exception as e:
        return jsonify({
            "status": "error",
            "message": f"An unexpected error occurred: {str(e)}",
            "data": None
        }), 500

@app.route('/api/check-ban', methods=['POST'])
def check_ban_post():
    try:
        data = request.get_json()
        
        if not data or 'uid' not in data:
            return jsonify({
                "status": "error",
                "message": "Missing 'uid' in request body",
                "data": None
            }), 400
        
        uid = str(data['uid'])
        lang = data.get('lang', 'en')
        
        if not uid.isdigit():
            return jsonify({
                "status": "error",
                "message": "Invalid UID. Please provide a valid numeric user ID.",
                "data": None
            }), 400
        
        ban_data = check_ban_garena(uid, lang)
        
        if ban_data is None:
            return jsonify({
                "status": "error",
                "message": "Could not retrieve ban information. Please try again later.",
                "data": None
            }), 503
        
        if ban_data.get("error"):
            return jsonify({
                "status": "error",
                "message": ban_data.get("message", "API returned an error"),
                "data": None
            }), 400
        
        response_data = {
            "uid": uid,
            "language": lang,
            "garena_response": ban_data,
            "api_source": "Official Garena API"
        }
        
        return jsonify({
            "status": "success",
            "message": "Ban check completed successfully",
            "data": response_data
        })
        
    except Exception as e:
        return jsonify({
            "status": "error",
            "message": f"Invalid request: {str(e)}",
            "data": None
        }), 400

# ---------------- Error Handlers ----------------
@app.errorhandler(404)
def not_found(error):
    return jsonify({
        "status": "error",
        "message": "Endpoint not found",
        "available_endpoints": [
            "GET /",
            "GET /api/check-ban/<uid>?lang=<lang>",
            "POST /api/check-ban"
        ]
    }), 404

@app.errorhandler(500)
def internal_error(error):
    return jsonify({
        "status": "error",
        "message": "Internal server error",
        "data": None
    }), 500

# For local dev only
if __name__ == "__main__":
    app.run(debug=True)

