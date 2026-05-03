#!/bin/bash
# ============================================================
# AI 能力包 安装/同步脚本 install.sh
# 将 \ai-plugin 的规则和配置同步到所有 AI 工具
# ============================================================
set -e

PLUGIN_DIR="/ai-plugin"
BACKUP_DIR="/backups/ai-plugin-$(date +%Y%m%d_%H%M%S)"

echo "=========================================="
echo "  AI Plugin Installer v1.0"
echo "  Centralized AI Capability Pack"
echo "=========================================="
echo ""

# --- Git 同步 (如果配置了远程仓库) ---
if grep -q "url:" "$PLUGIN_DIR/plugin.yaml" 2>/dev/null; then
    REPO_URL=$(grep "url:" "$PLUGIN_DIR/plugin.yaml" | head -1 | sed 's/.*url: *"//' | sed 's/"//')
    if [ -n "$REPO_URL" ]; then
        echo "[1/4] Git 同步..."
        if [ -d "$PLUGIN_DIR/.git" ]; then
            cd "$PLUGIN_DIR" && git pull --ff-only && echo "  Updated via git pull" || echo "  [!] git pull failed, continuing..."
        else
            echo "  Remote URL configured but no .git found. Skipping git sync."
            echo "  To enable: rm -rf \"$PLUGIN_DIR\" && git clone $REPO_URL \"$PLUGIN_DIR\""
        fi
    else
        echo "[1/4] Git 同步: 未配置远程仓库，跳过"
    fi
else
    echo "[1/4] Git 同步: plugin.yaml 无 repository.url，跳过"
fi

# --- 备份现有配置 ---
echo "[2/4] 备份现有配置到: $BACKUP_DIR"
mkdir -p "$BACKUP_DIR"

# 备份 .trae/
if [ -d "/.trae" ]; then
    cp -r "/.trae" "$BACKUP_DIR/" 2>/dev/null || true
    echo "  Backed up .trae/"
fi

# 备份 .qoder/
if [ -d "/.qoder" ]; then
    cp -r "/.qoder" "$BACKUP_DIR/" 2>/dev/null || true
    echo "  Backed up .qoder/"
fi

# --- 创建符号链接 ---
echo "[3/4] 创建配置链接..."
SYMLINK_METHOD=""

# 检测符号链接支持
if [ "$OS" = "Windows_NT" ]; then
    # Git Bash on Windows: 尝试 ln -s
    if ln -s --help >/dev/null 2>&1; then
        SYMLINK_METHOD="ln"
    fi
else
    SYMLINK_METHOD="ln"
fi

create_link() {
    local SOURCE="$1"
    local TARGET="$2"
    local DESC="$3"

    echo "  $DESC"

    # 移除旧的目标 (文件或链接)
    if [ -f "$TARGET" ] || [ -L "$TARGET" ]; then
        rm -f "$TARGET"
    fi

    # 确保目标目录存在
    mkdir -p "$(dirname "$TARGET")"

    if [ "$SYMLINK_METHOD" = "ln" ]; then
        ln -s "$SOURCE" "$TARGET" && echo "    -> linked: $(basename "$TARGET")" || {
            echo "    [!] symlink failed, falling back to cp"
            cp "$SOURCE" "$TARGET"
        }
    else
        # Windows 无 ln 支持: 退化为复制
        cp "$SOURCE" "$TARGET"
        echo "    -> copied (symlink not available)"
    fi
}

# TRAE 规则
create_link \
    "$PLUGIN_DIR/rules/trae-project-rules.md" \
    "/.trae/project_rules.md" \
    "TRAE: project_rules.md -> ai-plugin/rules/trae-project-rules.md"

# TRAE 通用规则 (自动加载)
create_link \
    "$PLUGIN_DIR/rules/workflow.md" \
    "/.trae/ai-plugin-workflow.md" \
    "TRAE: workflow.md (extra)"

create_link \
    "$PLUGIN_DIR/rules/security.md" \
    "/.trae/ai-plugin-security.md" \
    "TRAE: security.md (extra)"

# Qoder Agent 规则
create_link \
    "$PLUGIN_DIR/rules/qoder-agent.md" \
    "/.qoder/agents/default.md" \
    "Qoder: default.md -> ai-plugin/rules/qoder-agent.md"

# Qoder 额外规则
create_link \
    "$PLUGIN_DIR/rules/workflow.md" \
    "/.qoder/ai-plugin-workflow.md" \
    "Qoder: workflow.md (extra)"

create_link \
    "$PLUGIN_DIR/rules/coding-style.md" \
    "/.qoder/ai-plugin-coding-style.md" \
    "Qoder: coding-style.md (extra)"

create_link \
    "$PLUGIN_DIR/rules/security.md" \
    "/.qoder/ai-plugin-security.md" \
    "Qoder: security.md (extra)"

# --- 验证 ---
echo "[4/4] 验证安装..."

verify_file() {
    local FILE="$1"
    local NAME="$2"
    if [ -f "$FILE" ]; then
        echo "  [OK] $NAME"
    else
        echo "  [FAIL] $NAME — missing: $FILE"
    fi
}

verify_file "/.trae/project_rules.md" "TRAE rules"
verify_file "/.qoder/agents/default.md" "Qoder agent"
verify_file "/ai-plugin/plugin.yaml" "Plugin config"
verify_file "/ai-plugin/rules/workflow.md" "Workflow rules"
verify_file "/ai-plugin/rules/communication.md" "Communication rules"
verify_file "/ai-plugin/rules/coding-style.md" "Coding style rules"
verify_file "/ai-plugin/rules/security.md" "Security rules"

echo ""
echo "=========================================="
echo "  Install Complete!"
echo "=========================================="
echo ""
echo "  Updated configs:"
echo "    TRAE:  /.trae/project_rules.md"
echo "    Qoder: /.qoder/agents/default.md"
echo ""
echo "  What changed:"
echo "    - All AI tools now inherit from ai-plugin/rules/"
echo "    - Single source of truth: /ai-plugin/"
echo "    - Old configs backed up to: $BACKUP_DIR"
echo ""
echo "  Next steps:"
echo "    1. Restart TRAE IDE to pick up new config"
echo "    2. Restart Qoder to apply new agent rules"
echo "    3. To enable git auto-update, configure repository.url in plugin.yaml"
echo ""
