import os

fpath = r"\apps\desktop\out\main\index.js"
with open(fpath, "r", encoding="utf-8") as f:
    content = f.read()

debug_code = """
// DEBUG: log startup
const fs = require('fs');
const debugLog = (msg) => {
  try { fs.appendFileSync('D:\\\\AI\\\\logs\\\\electron_debug.log', new Date().toISOString() + ' ' + msg + '\\n'); } catch(e) {}
};
debugLog('Main process starting...');
debugLog('platform: ' + process.platform);
debugLog('argv: ' + JSON.stringify(process.argv));
debugLog('cwd: ' + process.cwd());
"""

content = debug_code + content

content = content.replace(
    "electron.app.requestSingleInstanceLock();",
    """electron.app.requestSingleInstanceLock();
debugLog('Single instance lock requested');"""
)

content = content.replace(
    "electron.app.whenReady().then(() => {",
    """electron.app.whenReady().then(() => {
debugLog('App ready!');"""
)

content = content.replace(
    "electron.app.on('window-all-closed'",
    """debugLog('Setting up window-all-closed handler');
electron.app.on('window-all-closed'"""
)

with open(fpath, "w", encoding="utf-8") as f:
    f.write(content)
print("Added debug logging to main process")
