import json

pkg_path = r"\packages\core\package.json"
with open(pkg_path, "r", encoding="utf-8") as f:
    data = json.load(f)

if "./i18n" not in data.get("exports", {}):
    data["exports"]["./i18n"] = "./i18n/index.ts"
    data["exports"]["./i18n/zh"] = "./i18n/zh.ts"
    with open(pkg_path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
        f.write("\n")
    print("Added ./i18n and ./i18n/zh exports to package.json")
else:
    print("exports already exist")

print("Done!")
