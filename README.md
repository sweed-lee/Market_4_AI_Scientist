## market4science
### 运行系统（入口：`main_10_founders.py`）

运行：

```bash
python main_10_founders.py
```

#### 默认配置与输出

`main_10_founders.py` 当前默认导入：
- `config/config_25_founders_6groups_investor_counts.py` 中的 `CONFIG_25_FOUNDERS_6GROUPS_INVESTOR_COUNTS`

默认输出（写到项目根目录）：
- `results_25_founders_6groups_investor_counts.json`
- `dialogs_25_founders_6groups_investor_counts.json`

如需修改 LLM 服务地址或 key，编辑入口脚本所使用的 config 中：
- `CONFIG_...["system"]["base_url"]`
- `CONFIG_...["system"]["api_key"]`

### 配置字段说明（config dict）

入口脚本最终传入 orchestrator 的 config 是一个 Python dict，核心结构如下（示意）：
- `system`: 系统级超参数与 LLM 连接信息
- `founders`: founder 列表（每个 founder 一个 dict）
- `investor_groups`: investor group 列表（每个 group 一个 dict，内部包含 investors 列表）
- `interaction_graphs`: 多种可选的“可见性图”（谁能看到谁）
- `graph_mode`: 选择使用 `interaction_graphs` 中的哪一种图

#### `system`（系统级参数）

- **`num_rounds`**：major round 数量（创始人提交一次 + 投资方若干 investment round）循环多少次。
- **`temperature`**：LLM 采样温度（由入口脚本注入到 `llm_callback` 的每次调用里）。
- **`budget_tolerance_percent`**：预算容忍区间比例，用于把 founder 的 `BUDGET` 转成 \([lower\_bound, upper\_bound]\)：
  - \(lower = budget \times (1 - tol)\)
  - \(upper = budget \times (1 + tol)\)
  - 投资累计达到 `lower` 视为成功退出；达到/超过 `upper` 会按比例接受到 `upper` 并退款超额部分。
- **`max_investment_rounds`**：每个 major round 内，最多执行多少次 investment round（资金分配循环）。
- **`max_allocation_retries`**：当某个 investor 的 step-2 分配不合法（例如总和不等于其预算）时的最大重试次数。
- **`enable_checkpoints`**：是否写 checkpoint（两类：`founder_submitted` / `investor_evaluated`）。
- **`checkpoint_dir`**：checkpoint 输出目录名（相对项目根目录）。
- **`verbose`**（可选）：是否输出更详细的日志；不配则默认较安静（主要靠 tqdm 进度条）。
- **`base_url` / `api_key`**：OpenAI-compatible 接口地址与 key（由 `utils/llm_client.py` 使用）。
- **`max_investor_points`**：评分上限/尺度参数（默认 100）。当前两步制里 step-1 评分是 0-100；该字段也会被 orchestrator 读取为 `max_points`（兼容旧逻辑）。

#### `founders`（创始人列表）

每个 founder 配置项包含：
- **`name`**：节点名（必须与 `interaction_graphs` 里使用的名字一致，例如 `Founder_1`）。
- **`specialization`**：领域/专长描述（主要用于提示词与日志标识）。
- **`model`**：该 founder 调用 LLM 时使用的模型名（入口脚本会把它透传给 `llm_callback(..., model=...)`）。
- **`instruction`**：该 founder 的任务/需求文本（未显式传 `requirement` 时会用它作为 prompt 的 `requirement`）。

#### `investor_groups`（投资组列表）

每个 investor group 配置项包含：
- **`name`**：节点名（必须与 `interaction_graphs` 里一致，例如 `InvestorGroup_1`）。
- **`total_capital`**：该组在一个 major round 内可使用的总资金（tokens）。在每个 investment round，会在组内 investors 之间均分预算份额用于分配。
- **`k_selection`**：组内 top-k 选择开关（可为空）：
  - 若设为 \(k\)，则先按 step-1 的组内聚合评分对 founders 排序，只对 top-k 候选进行 step-2 分配；
  - 若不设，则候选为该 group 可见的全部 founders。
- **`round1_max_workers`**（可选）：step-1 评审阶段并行线程数上限；不设则自动按任务量估计一个值。
- **`investors`**：组内 investor 列表（每个 investor 一个 dict）：
  - **`name`**：investor 名字（例如 `Investor_1_G3`）
  - **`criteria`**：评审维度（用于 prompt）
  - **`philosophy`**：投资理念（用于 prompt）
  - **`model`**：该 investor 使用的模型名

#### `interaction_graphs` 与 `graph_mode`（可见性/交互图）

- **`interaction_graphs`**：一个 dict，键是模式名（如 `sparse`），值是“邻接表”：
  - `interaction_graphs[mode][node_name] = [visible_node_name, ...]`
  - node 可以是 founder 或 investor group（名字直接用 `founders[i]["name"]` / `investor_groups[j]["name"]`）
- **`graph_mode`**：选择使用哪个模式的邻接表（例如 `"sparse"`）。

可见性图会影响：
- investor group 在 step-1 / step-2 中“能看到并投资哪些 founders”
- founder 在迭代阶段“能看到哪些其他 founder 的信息”（如果 orchestrator 有使用这部分可见性）

### 系统工作流（更详细）

系统由三类核心对象协作完成：
- **Founder**（`agents/founder.py`）：生成/迭代提案
- **InvestorGroup**（`agents/investor.py`）：由多个 Investor 组成，组内并行评估与分配资金
- **SystemOrchestrator**（`system/orchestrator.py`）：驱动 major round / investment round 循环，处理接受/退款/退出市场，并记录结果

#### 1) 从配置创建 agents

入口脚本会把 config 里的字典转换成对象：
- **Founders**：读取 `name / specialization / model / instruction`
- **Investor groups**：读取 `name / total_capital / k_selection / investors[]`
  - 每个 investor 读取 `name / criteria / philosophy / model`

然后构造 `LLMClient`，并注入一个 `llm_callback(prompt, model=...)`，使得：
- **每个 agent 可以使用自己的 model**
- **temperature 使用 system 全局值**

#### 2) major round（大轮次）循环

`SystemOrchestrator.run()` 会执行 `system.num_rounds` 个 **major round**。每个 major round 的高层流程是：

- **Founder 阶段（提交）**
  - 第 1 轮：每个 founder 调用 `Founder.generate_strategy()` 生成提交
  - 第 2..N 轮：每个 founder 调用 `Founder.iterate_strategy()`，结合上一轮的投资/反馈进行迭代
  - Founder 提交内容会从 LLM 输出中解析出结构化字段（典型为）：
    - `TITLE`
    - `BUDGET`（整数 tokens）
    - `PROPOSAL`
    - `PROTOTYPE`（可选）

- **Checkpoint（可选）**
  - 如果 config 中 `system.enable_checkpoints=True`，在“founder 提交完成、投资评估开始之前”，会写一份 checkpoint：
    - kind = `founder_submitted`

- **Investor 阶段（评估 + 多次投资轮）**
  - 调用 orchestrator 内部 `_run_investment_rounds(...)`，它包含：
    - **Step 1（每个 major round 只做一次，缓存）**：proposal evaluation
    - **Step 2（循环多次 investment_round）**：allocation + 接受/退款 + 退出市场

- **Checkpoint（可选）**
  - Investor 阶段结束后，会写一份 checkpoint：
    - kind = `investor_evaluated`

> 术语说明：**major round** 是“创始人提交一次、投资方可能进行多轮投资直到停止”的一个大周期；**investment round** 是 major round 内部的第 1..K 次资金分配循环（由 `system.max_investment_rounds` 控制）。

#### 3) Investor 阶段的 Step 1：提案评分（缓存）

在一个 major round 的投资开始前（investment_round 循环外），每个 investor group 会对自己“可见”的 founders 做一次 step-1 评估并缓存（`InvestorGroup.run_step1_evaluations()`）：
- 对每个 `(investor, founder)` 组合调用 `Investor.evaluate_single_proposal(...)`
- 产出并缓存：
  - `per_investor_scores[inv][founder]`：0-100
  - `per_investor_advices[inv][founder]`：短评/建议
  - `aggregated_scores[founder]`：组内 investor 分数求和（用于 top-k）

这一步的结果 **在本 major round 的所有 investment_round 中复用**，避免重复评审提案。

#### 4) Investor 阶段的 Step 2：多次 investment round 分配资金

接下来进入 `investment_round = 1..system.max_investment_rounds` 循环。每一轮的关键步骤：

- **4.1 选股（top-k，可选）**
  - 如果 group 配了 `k_selection`，则按 step-1 的 `aggregated_scores` 取 top-k founders 作为候选池；
  - 未配置则候选池为该 group 可见的全部 founders。

- **4.2 每个 investor 分配自己份额（LLM 调用）**
  - group 的当轮可用资金会均分到各 investor：`budget_per_investor = group.total_capital // num_investors`
  - 对每个 investor 调用 `Investor.allocate_step2(...)`，要求：
    - 只在候选池里分配
    - 分配总和必须 **精确等于** `budget_per_investor`
    - 如不满足，会按 `system.max_allocation_retries` 重试

- **4.3 组内汇总为 planned investments（先扣款）**
  - group 把所有 investor 的分配结果相加，得到当轮对每个 founder 的 **planned 投资额**
  - 这一步会先从 `group.total_capital` 扣除 planned 总额（后续退款会加回）

- **4.4 按 founder 的预算区间做“接受/退款”并处理退出市场**
  - 每个 founder 有 `budget`，系统会用 `system.budget_tolerance_percent` 计算区间：
    - `lower_bound = budget * (1 - tol)`
    - `upper_bound = budget * (1 + tol)`
  - 设该 founder 在本轮收到的 planned 总额为 `round_total`，本轮前累计已接受为 `current_accumulated`：
    - 若 `current_accumulated + round_total >= upper_bound`：
      - 只按比例接受到刚好 `upper_bound`
      - 超出部分对各 group **按比例退款**
      - founder 退出市场
    - 若 `current_accumulated + round_total >= lower_bound`：
      - 本轮 planned 全部接受，不退款
      - founder 退出市场（达到成功下限）
    - 否则：
      - 本轮 planned 全部先接受，不退款
      - founder 继续留在市场，等待下一轮加注

> “退出市场”意味着该 founder 不会再出现在后续 investment_round 的可投资集合中。

- **4.5 记录投资历史（用于结果与出图）**
  - orchestrator 会在每个 investment_round 记录：
    - group 维度：planned / accepted / refunded / capital_before / capital_after
    - founder 维度：budget、bounds、accumulated、planned/accepted/refunded、per-group 明细
    - investor 维度：把 LLM 的浮点分配按比例离散成整数 planned，并按 accepted 比例拆分 accepted/refunded

#### 5) major round 的结果结构（写入 results / checkpoint）

每个 major round 产生一段 `round_data`，典型字段包括：
- `round`（major round 编号）
- `strategies / titles / budgets / proposals / prototypes`（founder 提交）
- `all_scores`：`{group_name: {founder_name: accepted_total_so_far_in_this_major_round}}`
- `investor_feedback`：每个 group 对每个 founder 的 step-1 分数、摘要、细节等（用于 founder 下一轮迭代）
- `investment_history`：`investment_round_1..K` 的详细流水

### 从 checkpoint 出图分析（`analyze/plot_investment_results_from_checkpoint.py`）

该脚本用于把某个 `investor_evaluated_*.json` checkpoint 里的 `orchestrator.history`（以及当前 round 的 `payload.round_data`）拼成 `results["all_rounds"]`，然后调用绘图函数批量出图。

#### 用法

```bash
python analyze/plot_investment_results_from_checkpoint.py /path/to/investor_evaluated_major_round_10_xxx.json
```

指定输出目录（可选）：

```bash
python analyze/plot_investment_results_from_checkpoint.py /path/to/investor_evaluated_major_round_10_xxx.json -o out_plots/
```

#### 输出图（当前脚本会生成）

- **Plot1**：各 investor group 的成功投资总量（随 major round 变化）
- **Plot2**：各 founder budget（随 major round 变化）
- **Plot3**：每个 major round 内，accumulated investment 随 investment round 的变化
- **Plot4**：成功率随 major round 变化（success = 最终融资 \(\ge 0.8 \times budget\)）
- **Plot5**：每个 major round 内，各 founder budget vs 最终融资额（并列柱状）
- **Plot6+7（group-only，按 group 分开）**
  - `plot6_7_major_round_{R}_{InvestorGroup_X}_group_accepted_per_founder.png`（按 accepted 降序）
  - `plot6_7_major_round_{R}_{InvestorGroup_X}_group_accepted_per_founder_ordered.png`（按 Founder 序号）

> 备注：**Plot8（score bars）** 是否生成取决于 `analyze/plot_investment_results.py` 里的 `TARGET_INVESTOR_GROUP` 与 `TARGET_INVESTOR` 是否配置。
