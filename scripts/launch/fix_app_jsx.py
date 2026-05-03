import os

app_tsx = r"\apps\desktop\src\renderer\src\App.tsx"
with open(app_tsx, "r", encoding="utf-8") as f:
    content = f.read()

old_return = """  return (
    <I18nProvider defaultLocale="zh">
    <ThemeProvider>
      <CoreProvider
        apiBaseUrl={import.meta.env.VITE_API_URL || "http://localhost:8080"}
        wsUrl={import.meta.env.VITE_WS_URL || "ws://localhost:8080/ws"}
        onLogout={handleDaemonLogout}
        identity={identity}
      >
        <AppContent />
      </CoreProvider>
      <Toaster />
    </I18nProvider>
      <UpdateNotification />
    </ThemeProvider>
  );"""

new_return = """  return (
    <I18nProvider defaultLocale="zh">
      <ThemeProvider>
        <CoreProvider
          apiBaseUrl={import.meta.env.VITE_API_URL || "http://localhost:8080"}
          wsUrl={import.meta.env.VITE_WS_URL || "ws://localhost:8080/ws"}
          onLogout={handleDaemonLogout}
          identity={identity}
        >
          <AppContent />
        </CoreProvider>
        <Toaster />
        <UpdateNotification />
      </ThemeProvider>
    </I18nProvider>
  );"""

content = content.replace(old_return, new_return)
with open(app_tsx, "w", encoding="utf-8") as f:
    f.write(content)
print("Fixed App.tsx JSX nesting")
