# Browser MCP Skill

## Description
Browser automation using Edge or Chrome

## Configuration
\`\`\`json
{
  "command": "npx",
  "args": ["-y", "@liangshanli/mcp-server-browser"],
  "env": {
    "CHROME_PATH": "C:\\Program Files (x86)\\Microsoft\\Edge\\Application\\msedge.exe",
    "TOOL_PREFIX": "browser"
  }
}
\`\`\`

## Tools
- browser_get_content - Get rendered HTML
- get_saved_files - List cached pages
- read_saved_file - Read cached content

## Usage
1. Configure CHROME_PATH to Edge location
2. Run: npx @liangshanli/mcp-server-browser
3. Use tools to fetch JavaScript-rendered pages

## Edge Path
\`C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe\`
