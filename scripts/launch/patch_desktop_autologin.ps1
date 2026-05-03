$envPath = "\apps\desktop\.env.development"
$envContent = @"
VITE_API_URL=http://localhost:8080
VITE_WS_URL=ws://localhost:8080/ws
VITE_APP_URL=http://localhost:8080
"@
Set-Content -Path $envPath -Value $envContent -Encoding UTF8 -NoNewline
Write-Host "Updated .env.development to point to localhost:8080"

$authStorePath = "\packages\core\auth\store.ts"
$content = Get-Content $authStorePath -Raw

if ($content -match "DEFAULT_USER_AUTO_LOGIN") {
    Write-Host "Auth store already patched for auto-login"
} else {
    $oldCode = @'
    initialize: async () => {
      if (cookieAuth) {
'@
    $newCode = @'
    initialize: async () => {
      const DEFAULT_USER_ID = "8b50fa2c-a393-4a20-83fc-34580c43f85d";
      const AUTO_LOGIN = true;
      if (AUTO_LOGIN && !cookieAuth) {
        try {
          const resp = await fetch(`${api.getBaseUrl()}/api/me`, {
            headers: { "X-User-ID": DEFAULT_USER_ID, "X-User-Email": "default@multica.local" }
          });
          if (resp.ok) {
            const user = await resp.json();
            storage.setItem("multica_token", "auto-login-dev");
            api.setToken("auto-login-dev");
            set({ user, isLoading: false });
            onLogin?.();
            identifyAnalytics(user.id, { email: user.email, name: user.name });
            return;
          }
        } catch {}
      }
      if (cookieAuth) {
'@
    $content = $content.Replace($oldCode, $newCode)
    Set-Content -Path $authStorePath -Value $content -Encoding UTF8 -NoNewline
    Write-Host "Patched auth store for auto-login"
}

$apiClientPath = "\packages\core\api\client.ts"
$apiContent = Get-Content $apiClientPath -Raw

if ($apiContent -match "X-User-ID.*DEFAULT") {
    Write-Host "API client already patched"
} else {
    $oldAuth = @'
  private authHeaders(): Record<string, string> {
    const headers: Record<string, string> = {};
    if (this.token) headers["Authorization"] = `Bearer ${this.token}`;
'@
    $newAuth = @'
  private authHeaders(): Record<string, string> {
    const headers: Record<string, string> = {};
    if (this.token === "auto-login-dev") {
      headers["X-User-ID"] = "8b50fa2c-a393-4a20-83fc-34580c43f85d";
      headers["X-User-Email"] = "default@multica.local";
    } else if (this.token) {
      headers["Authorization"] = `Bearer ${this.token}`;
    }
'@
    $apiContent = $apiContent.Replace($oldAuth, $newAuth)
    Set-Content -Path $apiClientPath -Value $apiContent -Encoding UTF8 -NoNewline
    Write-Host "Patched API client for auto-login headers"
}

Write-Host "`nAll patches applied successfully!"
