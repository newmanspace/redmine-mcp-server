#!/bin/bash
# 测试订阅功能脚本

MCP_URL="http://localhost:8000/mcp"
HEADERS="-H 'Content-Type: application/json' -H 'Accept: application/json, text/event-stream'"

call_mcp() {
    local tool=$1
    local args=$2
    curl -s -X POST "$MCP_URL" \
        -H "Content-Type: application/json" \
        -H "Accept: application/json, text/event-stream" \
        -d "{\"jsonrpc\":\"2.0\",\"id\":1,\"method\":\"tools/call\",\"params\":{\"name\":\"$tool\",\"arguments\":$args}}"
}

echo "======================================"
echo "  Redmine MCP 订阅功能测试"
echo "======================================"
echo ""

# 1. 订阅项目
echo "1️⃣  订阅项目 341 (每日简要报告)..."
result=$(call_mcp "subscribe_project" '{"project_id":341,"frequency":"daily","level":"brief","push_time":"09:00"}')
echo "$result" | grep -o '"message":"[^"]*"' | head -1
echo ""

# 2. 订阅另一个项目
echo "2️⃣  订阅项目 372 (每周详细报告)..."
result=$(call_mcp "subscribe_project" '{"project_id":372,"frequency":"weekly","level":"detailed","push_time":"Mon 09:00"}')
echo "$result" | grep -o '"message":"[^"]*"' | head -1
echo ""

# 3. 查看订阅列表
echo "3️⃣  查看我的订阅..."
result=$(call_mcp "list_my_subscriptions" '{}')
echo "$result" | grep -o '"subscription_id":"[^"]*"' | while read line; do
    echo "   - $line"
done
echo ""

# 4. 查看订阅统计
echo "4️⃣  订阅统计..."
result=$(call_mcp "get_subscription_stats" '{}')
total=$(echo "$result" | grep -o '"total_subscriptions":[0-9]*' | cut -d: -f2)
echo "   总订阅数：$total"
echo ""

# 5. 生成简要报告
echo "5️⃣  生成项目 341 简要报告..."
result=$(call_mcp "generate_subscription_report" '{"project_id":341,"level":"brief"}')
total=$(echo "$result" | grep -o '"total_issues":[0-9]*' | head -1 | cut -d: -f2)
new=$(echo "$result" | grep -o '"new_today":[0-9]*' | head -1 | cut -d: -f2)
echo "   Issue 总数：$total"
echo "   今日新建：$new"
echo ""

# 6. 生成详细报告
echo "6️⃣  生成项目 341 详细报告..."
result=$(call_mcp "generate_subscription_report" '{"project_id":341,"level":"detailed"}')
total=$(echo "$result" | grep -o '"total_issues":[0-9]*' | head -1 | cut -d: -f2)
echo "   Issue 总数：$total"
# 检查是否有逾期风险
overdue=$(echo "$result" | grep -o '"overdue_risks":\[' | wc -l)
if [ "$overdue" -gt 0 ]; then
    echo "   ⚠️ 包含逾期风险识别"
fi
echo ""

# 7. 取消订阅
echo "7️⃣  取消项目 372 订阅..."
result=$(call_mcp "unsubscribe_project" '{"project_id":372}')
echo "$result" | grep -o '"message":"[^"]*"' | head -1
echo ""

echo "======================================"
echo "  ✅ 测试完成!"
echo "======================================"
