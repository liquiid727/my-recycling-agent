# Over Cycling Design Docs

## 文档结构

### 核心产品文档
- `01-product-vision.md` - 产品愿景和定位
- `02-prd.md` - 产品需求文档

### 领域模型
- `03-domain-model.md` - CIM (Cycling Intelligence Model) 领域模型
- `04-decision-tree.md` - 决策规则树

### Agent 系统
- `05-agent-catalog.md` - Agent 目录
- `06-agent-runtime.md` - Agent 运行时架构
- `07-prompt-spec.md` - Prompt 规范

### 评估与任务
- `08-eval-dataset.md` - 评估数据集
- `09-eval-cases.yaml` - 评估用例
- `10-task-backlog.md` - 任务待办

## 整体思路

### 01. CIM（Cycling Intelligence Model）
- 用户模型
- 目标模型
- 骑行状态模型
- 习惯模型
- 决策模型

这会成为你的 Agent 大脑。

### 02. Agent PRD
- 首页
- 今日建议
- 路线规划
- 骑后总结
- 月报
- Agent 聊天

对应小程序 / App。

### 03. Agent Eval Dataset
- Case001
- Case002
- ...
- Case100

专门用于验证：
- 今天适合骑吗？
- 推荐的距离合理吗？
- 是否符合用户习惯？

这部分其实是未来 Agent 质量的护城河。

按照这个思路，Over Cycling 最有价值的方向不是骑行训练，而是"程序员骑行生活方式 Agent"。
