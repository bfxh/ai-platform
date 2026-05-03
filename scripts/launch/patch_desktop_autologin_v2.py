import re

DEFAULT_USER_ID = "8b50fa2c-a393-4a20-83fc-34580c43f85d"
DEFAULT_EMAIL = "default@multica.local"

auth_init_path = r"\packages\core\platform\auth-initializer.tsx"
with open(auth_init_path, "r", encoding="utf-8") as f:
    content = f.read()

if "AUTO_LOGIN_ENABLED" in content:
    print("auth-initializer.tsx already patched, skipping")
else:
    old_code = """    // Token mode: read from localStorage (Electron / legacy).
    const token = storage.getItem("multica_token");
    if (!token) {
      onLogout?.();
      useAuthStore.setState({ isLoading: false });
      return;
    }"""
    new_code = f"""    // Token mode: read from localStorage (Electron / legacy).
    // AUTO-LOGIN: if no token exists, create a dev token and auto-login
    const AUTO_LOGIN_ENABLED = true;
    let token = storage.getItem("multica_token");
    if (!token && AUTO_LOGIN_ENABLED) {{
      storage.setItem("multica_token", "auto-login-dev");
      token = "auto-login-dev";
    }}
    if (!token) {{
      onLogout?.();
      useAuthStore.setState({{ isLoading: false }});
      return;
    }}"""
    content = content.replace(old_code, new_code, 1)
    with open(auth_init_path, "w", encoding="utf-8") as f:
        f.write(content)
    print("auth-initializer.tsx patched successfully")

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
        patterns = [
            ('if (this.token) {\n      url.searchParams.set("token", this.token);',
             f'''if (this.token === "auto-login-dev") {{
      url.searchParams.set("user_id", "{DEFAULT_USER_ID}");
      url.searchParams.set("user_email", "{DEFAULT_EMAIL}");
    }} else if (this.token) {{
      url.searchParams.set("token", this.token);'''),
            ('if (token) {\n      url.searchParams.set("token", token);',
             f'''if (token === "auto-login-dev") {{
      url.searchParams.set("user_id", "{DEFAULT_USER_ID}");
      url.searchParams.set("user_email", "{DEFAULT_EMAIL}");
    }} else if (token) {{
      url.searchParams.set("token", token);'''),
        ]
        patched = False
        for old_ws, new_ws in patterns:
            if old_ws in content:
                content = content.replace(old_ws, new_ws, 1)
                with open(ws_client_path, "w", encoding="utf-8") as f:
                    f.write(content)
                print("api/ws-client.ts patched successfully")
                patched = True
                break
        if not patched:
            print("api/ws-client.ts: no matching pattern found, skipping WS patch")
except FileNotFoundError:
    print("api/ws-client.ts not found, skipping")

print("\nAll patches applied!")
