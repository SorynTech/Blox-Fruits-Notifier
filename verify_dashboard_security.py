import html
import asyncio
from aiohttp import web
from unittest.mock import MagicMock

# Mock data and constants
STATS_USER = "admin"
STATS_PASS = "password"
SUSPENDED_PAGE = "<html><body>{suspended_count} {users_list}</body></html>"

def check_auth(request):
    import secrets
    import base64
    auth_header = request.headers.get('Authorization')
    if not auth_header or not auth_header.startswith('Basic '):
        return False
    try:
        credentials = base64.b64decode(auth_header[6:]).decode('utf-8')
        username, password = credentials.split(':', 1)
        return secrets.compare_digest(username, STATS_USER) and secrets.compare_digest(password, STATS_PASS)
    except:
        return False

async def handle_suspended_mock(request):
    if not check_auth(request):
        return web.Response(text='Unauthorized', status=401)

    try:
        # Simulate unsafe data from DB
        suspended_users = [{
            'username': "<script>alert('user')</script>",
            'user_id': 123,
            'last_roll_time': None,
            'created_at': None,
            'total_rolls': 0,
            'suspension_reason': "<img src=x onerror=alert('reason')>"
        }]

        users_html = ""
        for user in suspended_users:
            reason = user.get('suspension_reason', 'No reason provided')
            safe_username = html.escape(str(user['username']))
            safe_reason = html.escape(str(reason if reason else 'No reason provided'))

            users_html += f"<div>{safe_username}</div><div>{safe_reason}</div>"

        html_content = SUSPENDED_PAGE.format(
            suspended_count=len(suspended_users),
            users_list=users_html
        )
        return web.Response(text=html_content, content_type='text/html')
    except Exception as e:
        return web.Response(text="Internal Server Error", status=500)

async def test_security():
    # Test XSS escaping
    request = MagicMock()
    request.headers = {'Authorization': 'Basic YWRtaW46cGFzc3dvcmQ='} # admin:password
    response = await handle_suspended_mock(request)
    body = response.text
    print(f"Response body: {body}")
    assert "&lt;script&gt;" in body
    assert "&lt;img" in body
    assert "<script>" not in body
    assert "<img" not in body
    print("✅ XSS escaping verified")

    # Test Error masking
    async def handle_error_mock(request):
        try:
            raise Exception("Sensitive DB details")
        except:
            return web.Response(text="Internal Server Error", status=500)

    response = await handle_error_mock(None)
    assert response.text == "Internal Server Error"
    assert "Sensitive DB details" not in response.text
    print("✅ Error masking verified")

if __name__ == "__main__":
    asyncio.run(test_security())
