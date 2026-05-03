import re

DEFAULT_USER_ID = "8b50fa2c-a393-4a20-83fc-34580c43f85d"
DEFAULT_EMAIL = "default@multica.local"

ws_client_path = r"\packages\core\api\ws-client.ts"
with open(ws_client_path, "r", encoding="utf-8") as f:
    content = f.read()

if "auto-login-dev" in content:
    print("ws-client.ts already patched, skipping")
else:
    old_ws_auth = """    this.ws.onopen = () => {
      if (!this.cookieAuth && this.token) {
        this.ws!.send(
          JSON.stringify({ type: "auth", payload: { token: this.token } }),
        );
        return;
      }

      this.onAuthenticated();
    };"""
    new_ws_auth = f"""    this.ws.onopen = () => {{
      if (!this.cookieAuth && this.token) {{
        if (this.token === "auto-login-dev") {{
          this.ws!.send(
            JSON.stringify({{ type: "auth", payload: {{ user_id: "{DEFAULT_USER_ID}", user_email: "{DEFAULT_EMAIL}" }} }}),
          );
        }} else {{
          this.ws!.send(
            JSON.stringify({{ type: "auth", payload: {{ token: this.token }} }}),
          );
        }}
        return;
      }}

      this.onAuthenticated();
    }};"""
    content = content.replace(old_ws_auth, new_ws_auth, 1)
    with open(ws_client_path, "w", encoding="utf-8") as f:
        f.write(content)
    print("ws-client.ts patched successfully")

app_tsx_path = r"\apps\desktop\src\renderer\src\App.tsx"
with open(app_tsx_path, "r", encoding="utf-8") as f:
    content = f.read()

if "auto-login-dev" in content:
    print("App.tsx already patched, skipping")
else:
    old_daemon_sync = """  useEffect(() => {
    if (!user) return;
    const token = localStorage.getItem("multica_token");
    if (!token) return;
    const userId = user.id;
    (async () => {
      try {
        await window.daemonAPI.syncToken(token, userId);
        await window.daemonAPI.autoStart();
      } catch (err) {
        console.error("Failed to sync daemon on login", err);
      }
    })();
  }, [user]);"""
    new_daemon_sync = """  useEffect(() => {
    if (!user) return;
    const token = localStorage.getItem("multica_token");
    if (!token) return;
    if (token === "auto-login-dev") return;
    const userId = user.id;
    (async () => {
      try {
        await window.daemonAPI.syncToken(token, userId);
        await window.daemonAPI.autoStart();
      } catch (err) {
        console.error("Failed to sync daemon on login", err);
      }
    })();
  }, [user]);"""
    content = content.replace(old_daemon_sync, new_daemon_sync, 1)
    with open(app_tsx_path, "w", encoding="utf-8") as f:
        f.write(content)
    print("App.tsx patched successfully")

print("\nAll patches applied!")
