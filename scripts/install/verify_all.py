import sys, os
sys.path.insert(0, r'\python\turix-cua\TuriX-CUA')

print('=' * 55)
print('  AI Desktop Automation Suite - Configuration Check')
print('=' * 55)

# 1. TuriX CUA + OCR + Browser
try:
    from src.agent.service import TuriXAgent, OCRReader, BrowserController, WindowsActions, AppLauncher
    agent = TuriXAgent(r'\python\turix-cua\TuriX-CUA\examples\config.json')
    apps = agent.app.list_applications()
    print(f'[OK] TuriX CUA: {len(apps)} apps, OCR+Browser integrated')
except Exception as e:
    print(f'[FAIL] TuriX CUA: {e}')

# 2. Agent S3
try:
    from gui_agents.s3.agents.agent_s import UIAgent
    print('[OK] Agent S3: UIAgent ready')
except Exception as e:
    print(f'[WARN] Agent S3: {e}')

# 3. Playwright
try:
    from playwright.sync_api import sync_playwright
    print('[OK] Playwright: browser automation ready')
except Exception as e:
    print(f'[FAIL] Playwright: {e}')

# 4. Tesseract OCR
try:
    import pytesseract
    tess_path = r'C:\Program Files\Tesseract-OCR\tesseract.exe'
    if os.path.exists(tess_path):
        pytesseract.pytesseract.tesseract_cmd = tess_path
        ver = pytesseract.get_tesseract_version()
        print(f'[OK] Tesseract OCR: v{ver}')
    else:
        print('[WARN] Tesseract OCR: engine not installed (run install_tesseract_admin.bat)')
except Exception as e:
    print(f'[WARN] Tesseract OCR: {e}')

# 5. UFO2
try:
    ufo_cfg = r'\python\UFO\config\ufo\agents.yaml'
    if os.path.exists(ufo_cfg):
        with open(ufo_cfg, 'r', encoding='utf-8') as f:
            content = f.read()
        has_ollama = 'localhost:11434' in content
        print(f'[OK] UFO2: config ready (Ollama={has_ollama})')
    else:
        print('[WARN] UFO2: config not found')
except Exception as e:
    print(f'[WARN] UFO2: {e}')

# 6. Security Tools
try:
    sys.path.insert(0, r'\python\security-tools')
    from tools.vuln_scanner import VulnScanner
    from tools.web_security import WebSecurityTester
    print('[OK] Security Tools: VulnScanner + WebSecTester ready')
except Exception as e:
    print(f'[FAIL] Security Tools: {e}')

# 7. Config files
print()
configs = {
    'TuriX CUA': r'\python\turix-cua\TuriX-CUA\examples\config.json',
    'UFO2 agents': r'\python\UFO\config\ufo\agents.yaml',
    'UFO2 system': r'\python\UFO\config\ufo\system.yaml',
    'Suite launcher': r'\python\start_suite.bat',
}
for name, path in configs.items():
    exists = os.path.exists(path)
    status = 'OK' if exists else 'MISSING'
    print(f'  [{status}] {name}: {path}')

print()
print('=' * 55)
print('  Configuration Complete!')
print('=' * 55)
