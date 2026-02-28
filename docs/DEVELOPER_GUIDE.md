# Developer Guide / 开发者指南

**Version**: 1.0  
**Last Updated**: 2026-02-28  
**Status**: Active

---

## 📋 Development Requirements / 开发要求

### 1. Code Comments / 代码注释

**Requirement / 要求**: **English Only / 仅英文**

All code comments, docstrings, and inline comments MUST be in English.

所有代码注释、文档字符串和行内注释必须使用英文。

#### Examples / 示例

```python
# ✅ GOOD / 正确
"""
Get project statistics from database
"""
def get_project_stats(project_id: int):
    """Retrieve project statistics"""
    # Calculate total issues
    total = len(issues)
    return stats

# ❌ BAD / 错误
"""
获取项目统计数据
"""
def get_project_stats(project_id: int):
    """检索项目统计"""
    # 计算总 issue 数
    total = len(issues)
    return stats
```

#### Why / 为什么

- ✅ International team collaboration / 国际团队协作
- ✅ Consistent codebase / 一致的代码库
- ✅ Easier maintenance / 更易维护
- ✅ Better tooling support / 更好的工具支持

---

### 2. Documentation / 文档

**Requirement / 要求**: **Bilingual Support (EN/ZH) / 双语支持（英文/中文）**

All user-facing documentation MUST provide both English and Chinese versions.

所有面向用户的文档必须提供英文和中文版本。

#### Documentation Structure / 文档结构

```
docs/
├── README.md                    # Main README (English with language switch)
├── README_BILINGUAL.md          # Bilingual documentation (EN/ZH)
├── DEPLOYMENT_REPORT.md         # Deployment guide (English)
├── contributing.md              # Contribution guide (English)
├── troubleshooting.md           # Troubleshooting (English)
└── tool-reference.md            # Tool reference (English)
```

#### README Format / README 格式

```markdown
## 🌐 Language / 语言

- **[🇨🇳 中文文档](README_BILINGUAL.md#中文)** - 中英文双语文档
- **[🇺🇸 English Documentation](README_BILINGUAL.md#english)** - Bilingual Documentation (EN/ZH)
```

#### Bilingual Section Format / 双语章节格式

```markdown
### Installation / 安装

#### English / 英文

```bash
pip install redmine-mcp-server
```

#### 中文 / Chinese

```bash
pip install redmine-mcp-server
```
```

---

### 3. i18n Configuration / 国际化配置

**Requirement / 要求**: **Preserve i18n Files / 保留 i18n 文件**

The i18n configuration files MUST be preserved and contain both language translations.

国际化配置文件必须保留并包含两种语言的翻译。

#### File Structure / 文件结构

```
src/redmine_mcp_server/i18n/
├── __init__.py              # i18n module initialization
├── zh_CN.py                 # Chinese translations (PRESERVE / 保留)
└── en_US.py                 # English translations (PRESERVE / 保留)
```

#### Example / 示例

```python
# i18n/zh_CN.py
REPORT_TYPES = {
    'daily': '日报',
    'weekly': '周报',
    'monthly': '月报'
}

# i18n/en_US.py
REPORT_TYPES = {
    'daily': 'Daily Report',
    'weekly': 'Weekly Report',
    'monthly': 'Monthly Report'
}
```

#### Usage / 使用

```python
from redmine_mcp_server.i18n import get_report_type_name

# Get translated report type
report_type_zh = get_report_type_name('daily', 'zh_CN')  # '日报'
report_type_en = get_report_type_name('daily', 'en_US')  # 'Daily Report'
```

---

### 4. Git Commit Messages / Git 提交信息

**Requirement / 要求**: **English / 英文**

All Git commit messages MUST be in English.

所有 Git 提交信息必须使用英文。

#### Format / 格式

```
<type>: <subject>

<body>

<footer>
```

#### Types / 类型

- `feat`: New feature / 新功能
- `fix`: Bug fix / 修复
- `docs`: Documentation changes / 文档变更
- `style`: Code style changes (formatting) / 代码格式
- `refactor`: Code refactoring / 代码重构
- `test`: Test changes / 测试变更
- `chore`: Build/config changes / 构建/配置变更

#### Examples / 示例

```bash
# ✅ GOOD / 正确
git commit -m "feat: add email subscription support"
git commit -m "fix: resolve database connection issue"
git commit -m "docs: update installation guide"
git commit -m "refactor: translate code comments to English"

# ❌ BAD / 错误
git commit -m "添加邮件订阅功能"
git commit -m "修复数据库连接问题"
git commit -m "更新安装指南"
```

---

### 5. Code Review Checklist / 代码审查清单

#### Before Submitting PR / 提交 PR 前

- [ ] All code comments in English / 所有代码注释为英文
- [ ] All docstrings in English / 所有文档字符串为英文
- [ ] No Chinese in code (except i18n) / 代码中无中文（i18n 除外）
- [ ] Documentation updated (if needed) / 文档已更新（如需要）
- [ ] Bilingual docs provided (if user-facing) / 提供双语文档（如面向用户）
- [ ] Git commit message in English / Git 提交信息为英文
- [ ] Tests pass / 测试通过
- [ ] No temporary files committed / 无临时文件提交

---

### 6. Project Structure / 项目结构

```
redmine-mcp-server/
├── src/redmine_mcp_server/      # Source code / 源代码
│   ├── i18n/                    # i18n configuration (PRESERVE / 保留)
│   ├── mcp/                     # MCP tools
│   ├── dws/                     # Data warehouse services
│   ├── scheduler/               # Schedulers
│   └── main.py                  # Entry point
├── docs/                        # Documentation / 文档
│   ├── README_BILINGUAL.md      # Bilingual docs / 双语文档
│   ├── DEPLOYMENT_REPORT.md     # Deployment guide / 部署指南
│   └── ...                      # Other docs / 其他文档
├── README.md                    # Main README (with language switch)
├── README_BILINGUAL.md          # Bilingual README / 双语 README
└── tests/                       # Tests / 测试
```

---

### 7. Translation Guidelines / 翻译指南

#### Technical Terms / 技术术语

| English | Chinese | Usage / 使用场景 |
|---------|---------|----------------|
| Subscription | 订阅 | User feature / 用户功能 |
| Report | 报告 | Generated content / 生成内容 |
| Push | 推送 | Send notification / 发送通知 |
| Email | 邮件 | Communication channel / 通信渠道 |
| Project | 项目 | Redmine project / Redmine 项目 |
| User | 用户 | System user / 系统用户 |
| Configuration | 配置 | System settings / 系统设置 |
| Service | 服务 | Backend service / 后端服务 |

#### Translation Best Practices / 翻译最佳实践

1. **Keep technical terms in English when appropriate / 适当保留英文技术术语**
   - ✅ "API", "MCP", "SMTP", "PostgreSQL"
   - ❌ "应用程序接口", "邮件传输协议"

2. **Be consistent / 保持一致性**
   - Use the same translation throughout / 全文使用相同翻译
   - Create a glossary for common terms / 为常用术语创建词汇表

3. **Context matters / 注意上下文**
   - Code comments: English only / 代码注释：仅英文
   - User docs: Bilingual / 用户文档：双语
   - i18n files: Both languages / i18n 文件：两种语言

---

### 8. Quality Assurance / 质量保证

#### Automated Checks / 自动检查

```bash
# Check for Chinese in code (should return 0)
grep -r "订阅\|报告\|推送" src/ --include="*.py" | grep -v i18n | wc -l

# Expected output: 0
```

#### Manual Review / 手动审查

- Review all new code comments / 审查所有新代码注释
- Verify documentation is bilingual / 验证文档是双语的
- Check i18n files are preserved / 检查 i18n 文件已保留

---

### 9. Onboarding New Developers / 新开发者入职

#### Step 1: Read This Guide / 阅读本指南

Read and understand all requirements in this document.

阅读并理解本文档中的所有要求。

#### Step 2: Review Code Style / 审查代码风格

Review existing code to understand the comment style.

审查现有代码以了解注释风格。

#### Step 3: Setup Development Environment / 设置开发环境

```bash
# Clone repository
git clone https://github.com/jztan/redmine-mcp-server.git
cd redmine-mcp-server

# Install dependencies
pip install -e .[dev]

# Run tests
pytest tests/
```

#### Step 4: First Commit / 首次提交

Make a small change to practice the workflow:

1. Make code change with English comments
2. Write commit message in English
3. Submit PR
4. Wait for review

---

### 10. Enforcement / 执行

#### CI/CD Checks / CI/CD 检查

- [ ] Code comment language check (future)
- [ ] Documentation completeness check
- [ ] i18n file preservation check

#### Code Review / 代码审查

All PRs will be reviewed for:
- English code comments
- Bilingual documentation (if applicable)
- i18n file preservation

#### Non-Compliance / 不合规处理

- First offense: Gentle reminder / 首次：温和提醒
- Repeated: PR will be rejected / 多次：PR 将被拒绝
- Pattern: Team discussion / 模式：团队讨论

---

## Quick Reference Card / 快速参考卡

```
┌─────────────────────────────────────────────┐
│  DEVELOPMENT REQUIREMENTS / 开发要求        │
├─────────────────────────────────────────────┤
│  Code Comments:    English ONLY / 仅英文    │
│  Documentation:    Bilingual / 双语         │
│  i18n Files:       Preserve / 保留          │
│  Git Messages:     English ONLY / 仅英文    │
│  PR Reviews:       Check all above          │
└─────────────────────────────────────────────┘
```

---

**Maintainer / 维护者**: OpenJaw  
**Contact / 联系**: jingzheng.tan@gmail.com  
**License / 许可证**: MIT
