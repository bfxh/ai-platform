# System Tools Installation Guide

## Python Packages
\`\`\`bash
pip install playwright pyppeteer selenium
playwright install
\`\`\`

## Node.js Packages
\`\`\`bash
npm install -g @playwright/mcp
npm install -g @liangshanli/mcp-server-browser
npm install -g mcpbrowser
\`\`\`

## Browser Drivers
\`\`\`bash
# Playwright browsers
npx playwright install chromium
npx playwright install firefox
npx playwright install webkit

# Chrome/Edge
# Already installed at:
# C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe
\`\`\`

## Verification
\`\`\`bash
# Check installed browsers
npx playwright show-browsers

# Test browser automation
npx playwright test --browser=chromium
\`\`\`
