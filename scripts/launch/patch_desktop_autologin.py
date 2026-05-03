import re

DEFAULT_USER_ID = "8b50fa2c-a393-4a20-83fc-34580c43f85d"
DEFAULT_EMAIL = "default@multica.local"

auth_store_path = r"\packages\core\auth\store.ts"
with open(auth_store_path, "r", encoding="utf-8") as f:
    content = f.read()

if "AUTO_LOGIN_ENABLED" in content:
    print("auth/store.ts already patched, skipping")
else:
    old_init = """    initialize: async () => {
      if (cookieAuth) {"""
    new_init = f"""    initialize: async () => {{
      const AUTO_LOGIN_ENABLED = true;
      const DEFAULT_USER_ID = "{DEFAULT_USER_ID}";
      const DEFAULT_USER_EMAIL = "{DEFAULT_EMAIL}";
      if (AUTO_LOGIN_ENABLED && !cookieAuth) {{
        try {{
          const resp = await fetch(`${{api.getBaseUrl()}}/api/me`, {{
            headers: {{ "X-User-ID": DEFAULT_USER_ID, "X-User-Email": DEFAULT_USER_EMAIL }}
          }});
          if (resp.ok) {{
            const user = await resp.json();
            storage.setItem("multica_token", "auto-login-dev");
            api.setToken("auto-login-dev");
            set({{ user, isLoading: false }});
            onLogin?.();
            identifyAnalytics(user.id, {{ email: user.email, name: user.name }});
            return;
          }}
        }} catch {{}}
      }}
      if (cookieAuth) {{"""
    content = content.replace(old_init, new_init, 1)
    with open(auth_store_path, "w", encoding="utf-8") as f:
        f.write(content)
    print("auth/store.ts patched successfully")

api_client_path = r"\packages\core\api\client.ts"
with open(api_client_path, "r", encoding="utf-8") as f:
    content = f.read()

if "auto-login-dev" in content:
    print("api/client.ts already patched, skipping")
else:
    old_auth = """  private authHeaders(): Record<string, string> {
    const headers: Record<string, string> = {};
    if (this.token) headers["Authorization"] = `Bearer ${this.token}`;"""
    new_auth = f"""  private authHeaders(): Record<string, string> {{
    const headers: Record<string, string> = {{}};
    if (this.token === "auto-login-dev") {{
      headers["X-User-ID"] = "{DEFAULT_USER_ID}";
      headers["X-User-Email"] = "{DEFAULT_EMAIL}";
    }} else if (this.token) {{
      headers["Authorization"] = `Bearer ${{this.token}}`;
    }}"""
    content = content.replace(old_auth, new_auth, 1)
    with open(api_client_path, "w", encoding="utf-8") as f:
        f.write(content)
    print("api/client.ts patched successfully")

ws_client_path = r"\packages\core\api\ws-client.ts"
try:
    with open(ws_client_path, "r", encoding="utf-8") as f:
        content = f.read()
    if "auto-login-dev" in content:
        print("api/ws-client.ts already patched, skipping")
    else:
        old_ws = 'if (this.token) {\n      url.searchParams.set("token", this.token);'
        new_ws = f'''if (this.token === "auto-login-dev") {{
      url.searchParams.set("user_id", "{DEFAULT_USER_ID}");
      url.searchParams.set("user_email", "{DEFAULT_EMAIL}");
    }} else if (this.token) {{
      url.searchParams.set("token", this.token);'''
        if old_ws in content:
            content = content.replace(old_ws, new_ws, 1)
            with open(ws_client_path, "w", encoding="utf-8") as f:
                f.write(content)
            print("api/ws-client.ts patched successfully")
        else:
            print("api/ws-client.ts: token pattern not found, checking alternative")
            old_ws2 = 'if (token) {\n      url.searchParams.set("token", token);'
            if old_ws2 in content:
                new_ws2 = f'''if (token === "auto-login-dev") {{
      url.searchParams.set("user_id", "{DEFAULT_USER_ID}");
      url.searchParams.set("user_email", "{DEFAULT_EMAIL}");
    }} else if (token) {{
      url.searchParams.set("token", token);'''
                content = content.replace(old_ws2, new_ws2, 1)
                with open(ws_client_path, "w", encoding="utf-8") as f:
                    f.write(content)
                print("api/ws-client.ts patched successfully (alt pattern)")
            else:
                print("api/ws-client.ts: no matching pattern found, skipping WS patch")
except FileNotFoundError:
    print("api/ws-client.ts not found, skipping")

print("\nAll patches applied!")
