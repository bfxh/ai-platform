#!/bin/bash
# MCP Core 启动脚本 (Linux/Mac)

echo "MCP Core 启动脚本"
echo "================================"
echo

# 检查 Python
if ! command -v python3 &> /dev/null; then
    echo "[错误] 未找到 Python3"
    exit 1
fi

# 切换到工作目录
cd "$(dirname "$0")" || exit

# 显示菜单
echo "请选择操作:"
echo "  1. 启动 MCP Server"
echo "  2. 列出技能"
echo "  3. 列出工作流"
echo "  4. 查看状态"
echo "  5. 运行测试"
echo "  6. 安装新技能"
echo "  7. 退出"
echo

read -rp "输入选项 (1-7): " choice

case $choice in
    1)
        echo "启动 MCP Server..."
        python3 server.py
        ;;
    2)
        echo "列出技能..."
        python3 cli.py skill list -v
        ;;
    3)
        echo "列出工作流..."
        python3 cli.py workflow list
        ;;
    4)
        echo "查看状态..."
        python3 cli.py status
        ;;
    5)
        echo "运行测试..."
        cd tests && python3 run_tests.py -v && cd ..
        ;;
    6)
        echo "安装新技能..."
        read -rp "技能名称: " skill_name
        read -rp "技能描述: " skill_desc
        python3 skill_installer.py create "$skill_name" --description "$skill_desc"
        echo
        read -rp "是否立即注册？(y/n): " register
        if [[ $register =~ ^[Yy]$ ]]; then
            python3 skill_installer.py register "$skill_name"
        fi
        ;;
    7)
        echo "再见!"
        exit 0
        ;;
    *)
        echo "[错误] 无效选项"
        ;;
esac
