import os

app_tsx = r"\apps\desktop\src\renderer\src\App.tsx"
with open(app_tsx, "r", encoding="utf-8") as f:
    content = f.read()

if 'I18nProvider' not in content:
    content = content.replace(
        'import { useEffect, useLayoutEffect, useMemo, useRef, useState } from "react";',
        'import { useEffect, useLayoutEffect, useMemo, useRef, useState } from "react";\nimport { I18nProvider } from "@multica/core/i18n";\nimport "@multica/core/i18n/zh";'
    )
    content = content.replace(
        '    <ThemeProvider>\n      <CoreProvider',
        '    <I18nProvider defaultLocale="zh">\n    <ThemeProvider>\n      <CoreProvider'
    )
    content = content.replace(
        '      </CoreProvider>\n      <Toaster />',
        '      </CoreProvider>\n      <Toaster />\n    </ThemeProvider>\n    </I18nProvider>'
    )
    content = content.replace(
        '    </ThemeProvider>\n    </I18nProvider>',
        '    </I18nProvider>'
    )
    with open(app_tsx, "w", encoding="utf-8") as f:
        f.write(content)
    print("App.tsx patched with I18nProvider")
else:
    print("App.tsx already has I18nProvider")

print("Done!")
