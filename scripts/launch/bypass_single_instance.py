import os

fpath = r"\apps\desktop\out\main\index.js"
with open(fpath, "r", encoding="utf-8") as f:
    content = f.read()

content = content.replace(
    "if (!electron.app.requestSingleInstanceLock()) electron.app.quit();",
    "electron.app.requestSingleInstanceLock();"
)

with open(fpath, "w", encoding="utf-8") as f:
    f.write(content)
print("Bypassed single instance lock")
