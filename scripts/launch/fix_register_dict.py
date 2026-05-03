import os

core_index = r"\packages\core\index.ts"
with open(core_index, "r", encoding="utf-8") as f:
    content = f.read()

content = content.replace(
    'export { t, tn, I18nProvider, useI18n } from "./i18n";',
    'export { t, tn, I18nProvider, useI18n, registerDictionary } from "./i18n";'
)

with open(core_index, "w", encoding="utf-8") as f:
    f.write(content)
print("Added registerDictionary to core/index.ts exports")
