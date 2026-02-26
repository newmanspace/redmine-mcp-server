#!/bin/bash
# Redmine 项目日报生成脚本
# 生成时间维度对比和人员任务量统计

REDMINE_URL="http://redmine.fa-software.com"
API_KEY="adabb6a1089a5ac90e5649f505029d28e1cc9bc7"

# 项目配置
declare -A PROJECTS=(
    ["341"]="新顺 CIM"
    ["372"]="上海工研院 MES"
)

# 获取项目 Issue 统计
get_project_stats() {
    local project_id=$1
    local limit=500
    
    curl -s "${REDMINE_URL}/issues.json?project_id=${project_id}&limit=${limit}&status_id=*" \
        -H "X-Redmine-API-Key: ${API_KEY}" | jq '
    {
        total: .total_count,
        by_status: (.issues | group_by(.status.name) | map({key: .[0].status.name, value: length}) | from_entries),
        by_priority: (.issues | group_by(.priority.name) | map({key: .[0].priority.name, value: length}) | from_entries),
        by_assignee: (.issues | map(select(.assigned_to != null)) | group_by(.assigned_to.name) | map({
            key: .[0].assigned_to.name,
            value: {
                total: length,
                open: [.[] | select(.status.name == "新建" or .status.name == "进行中")] | length,
                high_priority: [.[] | select(.priority.name == "立刻" or .priority.name == "紧急" or .priority.name == "高")] | length
            }
        }) | from_entries),
        today_new: ([.issues[] | select(.created_on >= (now - 86400) | strftime("%Y-%m-%d") == (now | strftime("%Y-%m-%d")))] | length),
        today_closed: ([.issues[] | select(.status.name == "已关闭" and .updated_on >= (now - 86400) | strftime("%Y-%m-%d") == (now | strftime("%Y-%m-%d")))] | length)
    }'
}

# 生成报告
generate_report() {
    echo "📊 **项目日报**"
    echo "📅 $(date +%Y-%m-%d) $(date +%H:%M)"
    echo ""
    
    for project_id in "${!PROJECTS[@]}"; do
        project_name="${PROJECTS[$project_id]}"
        echo "━━━━━━━━━━━━━━━━━━━"
        echo "## 📁 ${project_name}"
        echo ""
        
        stats=$(get_project_stats $project_id)
        
        # 总数
        total=$(echo "$stats" | jq -r '.total')
        echo "### 📈 状态快照"
        echo "| 指标 | 数值 |"
        echo "|------|------|"
        echo "| Issue 总数 | ${total} |"
        
        # 状态分布
        echo ""
        echo "**状态分布:**"
        echo "$stats" | jq -r '.by_status | to_entries | map("| \(.key) | \(.value) |") | .[]'
        
        # 优先级分布
        echo ""
        echo "**优先级分布:**"
        echo "$stats" | jq -r '.by_priority | to_entries | map("| \(.key) | \(.value) |") | .[]'
        
        # 人员任务量
        echo ""
        echo "### 👥 人员任务量"
        echo "| 负责人 | 总任务 | 进行中/待处理 | 高优先级 |"
        echo "|--------|--------|---------------|----------|"
        echo "$stats" | jq -r '.by_assignee | to_entries | sort_by(.value.total) | reverse | .[:10] | map("| \(.key) | \(.value.total) | \(.value.open) | \(.value.high_priority) |") | .[]'
        
        echo ""
    done
    
    echo "━━━━━━━━━━━━━━━━━━━"
    echo "📌 下次报告：明天 09:00"
}

generate_report
