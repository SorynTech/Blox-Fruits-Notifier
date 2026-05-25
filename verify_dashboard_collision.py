import html
import secrets
import base64
from unittest.mock import MagicMock

# Mocking parts of main.py
STATS_USER = "admin"
STATS_PASS = "password"
HEALTH_PAGE = "Health {uptime}"
STATS_PAGE = "Stats {uptime}"
SUSPENDED_PAGE = "Suspended {suspended_count}"
stats = {'bot_start_time': None, 'total_rolls': 0, 'active_users': 0, 'guilds_count': 0}

class WebResponse:
    def __init__(self, text, content_type=None, status=200):
        self.text = text
        self.content_type = content_type
        self.status = status

class Web:
    Response = WebResponse
web = Web()

def get_all_users(): return []
def get_rarity_distribution(): return {}
def get_suspended_users(): return []
def get_auth_response(): return WebResponse("Unauthorized", status=401)
def check_auth(request):
    auth_header = request.headers.get('Authorization')
    if not auth_header or not auth_header.startswith('Basic '): return False
    try:
        credentials = base64.b64decode(auth_header[6:]).decode('utf-8')
        username, password = credentials.split(':', 1)
        return secrets.compare_digest(username, STATS_USER) and secrets.compare_digest(password, STATS_PASS)
    except: return False

# The logic from main.py
async def handle_health(request):
    uptime = "Not started"
    response_html = HEALTH_PAGE.format(uptime=uptime)
    return web.Response(text=response_html, content_type='text/html')

async def handle_stats(request):
    if not check_auth(request): return get_auth_response()
    uptime = "Not started"
    users_html = "<div>User</div>"
    # Testing that html.escape still works
    safe_user = html.escape("<script>")
    response_html = STATS_PAGE.format(uptime=uptime)
    return web.Response(text=response_html, content_type='text/html')

import asyncio

async def test():
    try:
        r1 = await handle_health(None)
        print(f"Handle health: {r1.text}")

        req = MagicMock()
        req.headers = {'Authorization': 'Basic YWRtaW46cGFzc3dvcmQ='}
        r2 = await handle_stats(req)
        print(f"Handle stats: {r2.text}")
        print("✅ No shadowing crash detected")
    except Exception as e:
        print(f"❌ Shadowing crash detected: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test())
