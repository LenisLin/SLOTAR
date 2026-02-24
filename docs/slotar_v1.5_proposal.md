# SLOTAR Proposal V1.5

## Selection-aware longitudinal change atlas for multi-ROI IMC

### Community prototypes + (Density/Shape/Scale) + Unbalanced OT + Uncertainty + Remapping

---

## 0) 摘要（1 段落）

在 multi-ROI、pre/post 选择机制不对称且不可控的 IMC 纵向数据中，我们用“局部社区实例 → 全局原型字典（prototype dictionary）”建立统一语义坐标系；在患者-时间点-分层组（区室或 ROI-state）上，将原型密度聚合成经验测度，通过 **Unbalanced Optimal Transport (UOT)** 将 pre→post 变化分解为 **retention / remodeling / creation / destruction**，并同时输出 **scale（总密度）变化**与 **shape（归一化结构形状）变化**以解耦“总量/覆盖”与“结构形状”。不确定性采用 ROI bootstrap；当某组仅 1 个 ROI 时，采用 **自适应网格 block bootstrap（带有效面积与 composition-stratified 约束）**。所有关键事件可回映射到 ROI 原图以便病理复核。UOT 目标函数在广义 KL + 熵正则下有显式下界，数值求解默认启用 **log-domain + clamp + (\varepsilon)-scaling** 退火以保证在稀疏高维分布上可收敛。

---

## 1) 问题定义（严格边界）

### 1.1 数据现实约束

* 层级结构：cell → ROI → timepoint → patient
* pre/post 组织状态集合不对称（如 post 出现 RTB，pre 不存在；pCR post 可能没有 CT）
* post ROI 来自更大母体组织抽样，选择机制不对称且不可控
* ROI 面积近似一致（(\approx 1,\mathrm{mm}^2)），可计算细胞密度（cells/mm²）

### 1.2 我们要解决的“蓝海输出”

对每位患者、每个分层组 (g)（区室或 ROI-state），输出：

1. **可归因变化分解**（retention/remodeling/creation/destruction）
2. **可置信**（bootstrap 区间、事件复现概率、敏感性、批次漂移风险标记、单 ROI 降级声明）
3. **可回映射**（事件→原型→ROI→空间区域→细胞集合）

> 关键解释边界（必须写进 proposal 与工具文档）：
> creation/destruction = 在给定表示、代价、超参、ROI 覆盖与分层条件下的 **unmatched mass**；它不是“真实生物学生成/消亡”的必然同义词。我们通过 shape/scale 解耦、组内 (\lambda) 校准、UQ 与 batch drift 风险标记提供证据等级。

---

## 2) 输入与输出（明确到字段级）

### 2.1 输入

对患者 (p)，时间 (t\in{0,1})，ROI (r)，细胞 (c)：

* 坐标 (\mathbf{s}_{p,t,r,c}=(x,y))
* marker (\mathbf{m}_{p,t,r,c}\in\mathbb{R}^M)（(M\approx 30)）
* ROI 有效面积 (Area_{p,t,r})（优先 tissue mask；否则近似 1mm²）
* 可选：ROI 标签 (\ell_{p,t,r}\in\mathcal{L})（CT/PT/RTB/AB 或自定义）
* 可选：批次信息 batch_id、临床协变量 (\mathbf{v}_p)、结局 (y_p)

### 2.2 输出（核心对象）

对每个 ((p,g))：

* **Scale**：(S_{p,1,g}/S_{p,0,g})（总密度/覆盖变化）
* **Density-level UOT**：((R^{dens},M^{dens},B^{dens},D^{dens})) + 事件表 + UQ
* **Shape-level UOT**：((R^{shape},M^{shape},B^{shape},D^{shape})) + 事件表 + UQ
* **Batch drift 风险标记**：每条 remodeling edge 的 drift-alignment 分数与标记
* **Remapping package**：事件→ROI→细胞坐标/邻域集合→marker/组成摘要→可信度标签
* **审计字段**：`lambda_dens[g]`, `lambda_shape[g]`, `s_C`, `UQ_mode`, `area_mode`, `G_used`, `n_blocks_valid`

---

## 3) 表示层：社区实例与原型字典（统一语义坐标系）

### 3.1 community instance (u_c)（在完整 ROI 上计算）

默认用 kNN（降低边缘效应）：
[
\mathbf{p}*c=\frac{1}{k}\sum*{c'\in\mathcal{N}*k(c)}\mathbf{e}*{c'},\quad
\bar{\mathbf{m}}*c=\frac{1}{k}\sum*{c'\in\mathcal{N}*k(c)}\mathbf{m}*{c'},\quad
\delta_c=\frac{k}{\pi r_k(c)^2}
]
[
u_c=[\mathbf{p}_c,\bar{\mathbf{m}}_c,\mathbf{m}_c,\delta_c]
]
对四个块做 block-wise robust scaling 得 (\tilde u_c)。

### 3.2 全局原型字典（分层均匀下采样 + k-means）

从每个 ((p,t)) 抽同数量 (N_{bal}) 的 (\tilde u_c) 构成 (\mathcal{U}_{bal})，在其上 k-means 学得原型中心 (\mathbf{z}_1,\dots,\mathbf{z}*K)。对全量细胞硬分配：
[
a(c)=\arg\min*{k}|\tilde u_c-\mathbf{z}_k|_2
]

---

## 4) 分层组 (g)：区室优先，缺失退化为 ROI-state

* 若有 (\ell_{p,t,r})：(g=\ell)
* 否则对 ROI 的原型密度/比例向量聚类得到 ROI-state：(g=\hat\ell)
* 或用户指定不分层：(g=all)

> 组内校准与组内 UOT 都按 (g) 执行，避免“真实空间异质性污染 (\lambda) 校准”。

---

## 5) 三件套聚合：Density / Shape / Scale（核心）

ROI 原型计数：
[
n_{p,t,r,k}=#{c\in ROI_{p,t,r}:a(c)=k}
]
ROI 原型密度：
[
\rho_{p,t,r,k}=\frac{n_{p,t,r,k}}{Area_{p,t,r}}
]
聚合（默认 ROI 均匀权重 (\omega)）：
[
a_{p,t,g,k}=\sum_{r:g(r)=g}\omega_{p,t,r}\rho_{p,t,r,k},\qquad \sum_r\omega_{p,t,r}=1
]
Scale：
[
S_{p,t,g}=\sum_k a_{p,t,g,k}
]
Shape：
[
\bar{\mathbf{a}}*{p,t,g}=\mathbf{a}*{p,t,g}/S_{p,t,g}\quad (S_{p,t,g}>0)
]

---

## 6) UOT：目标函数、全局 cost scaling、(\lambda) 双校准、数值求解

### 6.1 全局静态 cost scaling（V1.5 固化为强制）

原型学习后一次性计算：
[
s_C=\mathrm{median}\left(|\mathbf{z}_i-\mathbf{z}_j|*2^2:i\neq j\right)
]
任何 UOT 子问题（校准/推断、任何 active set）都用：
[
C*{ij}=|\mathbf{z}_i-\mathbf{z}_j|_2^2/s_C
]
这保证 (\lambda) 的量纲语义在校准与推断之间不漂移。

### 6.2 支持集裁剪（强制，保证 KL 合法与稳定）

[
\mathcal{K}*{p,g}={k: a*{p,0,g,k}+a_{p,1,g,k}>\eta}
]
只在 (\mathcal{K}_{p,g}) 上求解。

### 6.3 UOT 目标函数（density-level 或 shape-level 仅输入向量不同）

对 (a,b\in\mathbb{R}*+^{|\mathcal{K}|})：
[
\Pi^*=\arg\min*{\Pi\ge 0}\ \langle C,\Pi\rangle
+\lambda,\mathrm{KL}(\Pi\mathbf{1}|a)
+\lambda,\mathrm{KL}(\Pi^\top\mathbf{1}|b)
+\varepsilon \sum_{ij}\Pi_{ij}(\log\Pi_{ij}-1)
]
广义 KL：
[
\mathrm{KL}(x|a)=\sum_i\left[x_i\log\frac{x_i}{a_i}-x_i+a_i\right]\ge 0
]

### 6.4 有界性（可证明下界）

令 (|\mathcal{K}|=K')。因：

* (\langle C,\Pi\rangle\ge 0)
* 两个 KL 项 (\ge 0)
* 熵项中 (h(x)=x(\log x-1)) 在 (x\ge 0) 的全局最小值为 (-1)（在 (x=1) 处），故
  [
  \sum_{ij} h(\Pi_{ij}) \ge -K'^2
  ]
  因此目标函数下界为：
  [
  \mathcal{L}(\Pi)\ge -\varepsilon K'^2
  ]
  即 **有界**（不会 (-\infty)），且在常见 UOT 条件下最小解存在并可数值求解。

### 6.5 (\lambda) 校准（V1.5：density 与 shape 分别校准）

在同组 (g) 内，用 pre 的 ROI–ROI 配对构造 unmatched ratio 曲线，在候选网格 (\Lambda) 上选择使队列中位数匹配容忍度 (\alpha) 的 (\lambda)。

* 得到 (\lambda^{dens}_g)：输入为 density 向量（(\rho) 或聚合后的 (a)）
* 得到 (\lambda^{shape}_g)：输入为归一化 shape 向量（(\bar\rho) 或 (\bar a)）

> 这避免 shape-level 因复用 density-level (\lambda) 而退化为 balanced OT。

### 6.6 数值求解（V1.5：默认启用 (\varepsilon)-scaling）

**强制**：

* log-domain stabilized Sinkhorn
* clamp（例如 ([-50,50])）
* warm-start 对偶变量（跨 (\varepsilon) 层）

**默认启用 (\varepsilon)-scaling**（高维稀疏下实用上必需）：

* (\varepsilon_{init}>\cdots>\varepsilon_{target})，例如 (10.0\to 0.1)，每层乘 0.5
* 每层迭代到 marginal residual 达标或 objective 稳定，再降 (\varepsilon)
* 优先调用成熟库（如 POT 的稳定实现）；若自写必须严格遵循上述策略

---

## 7) 变化分解指标与事件（输出层）

对每个 ((p,g))（density-level 与 shape-level 分别计算）：

* (T=\sum_{ij}\Pi_{ij})
* (D=|a-\Pi\mathbf{1}|_1)（destruction）
* (B=|b-\Pi^\top\mathbf{1}|_1)（creation）
* (M=\frac{1}{T}\sum_{ij} C_{ij}\Pi_{ij})（remodeling 强度）
* (R(\tau)=\frac{1}{T}\sum_{C_{ij}\le\tau}\Pi_{ij})（retention）

事件提取：

* retention edges：(\Pi_{ij}) 大且 (C_{ij}) 小
* remodeling edges：(C_{ij}\Pi_{ij}) 大
* create/destroy prototypes：由残差向量 (a-\Pi\mathbf{1})、(b-\Pi^\top\mathbf{1}) 的大分量给出
  每个事件附：质量、成本、UQ 复现概率、敏感性标签、drift 风险标记、可回映射索引。

---

## 8) 不确定性（UQ）：ROI bootstrap + 单 ROI 自适应网格 block bootstrap（V1.5 工程固化）

### 8.1 多 ROI（默认）

((p,t,g)) 至少 2 个 ROI：ROI bootstrap（有放回）重采样，重算 (a,\bar a)、UOT、指标与事件；输出区间与复现概率。

### 8.2 单 ROI（V1.5：工程规范的三条必需细节）

**(i) 特征预计算冻结（必须）**
在完整 ROI 上一次性计算并冻结：

* kNN 邻域与 (\tilde u_c)
* 原型标签 (a(c))
  单 ROI block bootstrap **只重采样带标签细胞集合**，不重算 kNN/密度/原型。

**(ii) 自适应 (G\times G) 网格与 Edge-cell Assignment（必须）**

* 使用确定性的半开区间/`floor` 规则给每个细胞唯一 block id，保证落在网格线上的细胞归属可复现。
* 选择 (G) 使有效 blocks 数达到目标（如 16 或 25）且每块细胞数足够（阈值 (n_{\min})）；不足则降低 (G)。

**(iii) 空网格/低细胞块过滤 + pseudo-area（必须）**

* 每个 block (b) 预计算：细胞集合、原型计数向量 (n_{b,k})、以及 (Area_b)（优先 tissue mask；否则 nominal area）
* 丢弃 (|Cells(b)|<n_{\min}/3) 或 (Area_b<Area_{\min}) 的 block
* bootstrap 只在有效 block 集合上进行
* 组装 pseudo-ROI 时：
  [
  n^{pseudo}*k=\sum*{b\in sample} n_{b,k},\quad Area_{pseudo}=\sum_{b\in sample} Area_b,\quad
  \rho^{pseudo}_k=n^{pseudo}*k/Area*{pseudo}
  ]
  并输出 `area_mode={mask,nominal}` 与 `n_blocks_valid` 用于审计。

---

## 9) 批次漂移风险标记（不做黑盒校正，但可审计）

选 anchor 细胞群（如内皮/成纤维），计算漂移向量：
[
\Delta_{batch}=\bar{\mathbf{m}}*{anchor,post}-\bar{\mathbf{m}}*{anchor,pre}
]
对每条 remodeling edge (i\to j)：
[
S_{i\to j}=\cos(\mathbf{z}_j-\mathbf{z}*i,\Delta*{batch})
]
若 (S>0.85) 标记 drift-aligned，并提供“包含/排除 drift-aligned edges”的敏感性版本。

---

## 10) 回映射（审计与病例展示）

事件 (\to) 原型集合 (\to) ROI 内细胞集合（按 (a(c))）(\to) 细胞坐标/邻域集合 (\to) 可视化高亮。输出同时附：

* 原型的 marker/identity 摘要
* 事件质量与 UQ 复现概率
* drift 风险标记

---

## 11) 胃癌队列模拟推演（你们队列的“预期输出形态”）

### 11.1 队列结构（已知事实）

* (P\approx 50)，pre/post 配对；标签 (y_p\in{pCR,NR})
* pre：2–3 ROI（多见 CT/PT）
* post：3–5 ROI（NR 多见 CT；pCR 多见 RTB；可有 AB/PT）
* ROI 面积近似 1mm²，可用密度

### 11.2 运行后你们会得到的“典型模式”

**pCR 患者（典型）**

* RTB 组：density-level (B^{dens}) 高；shape-level 若也高 → 更支持“结构形状新生/重塑”而非纯 coverage
* CT 组：density-level (D^{dens}) 可能高；结合 scale ratio 判断是覆盖减少还是形状变化
* remodeling edges：pre 某原型 (\to) post RTB-like 原型，质量大、成本中高、bootstrap 高复现，可回映射到退缩床区域

**NR 患者（典型）**

* CT 组：retention 高（低成本大质量边多）；(D) 相对低
* “抗性生态位候选”：高复现 retention edges，对应原型可回映射到 post CT 中稳定残存区域
* 若 remodeling edges 与 (\Delta_{batch}) 高对齐 → 标记为 drift 风险，需要敏感性版本复核

---

# 12) 生物有效性与算法优雅性评估（客观）

## 12.1 生物有效性（强项）

* **结构变化可归因**：UOT 自然给出 matched 与 unmatched，并通过 density/shape/scale 三件套提高解释可信度
* **跨患者可比性更强**：全局 cost scaling + 组内双 (\lambda) 校准
* **UQ 可审计**：多 ROI bootstrap 与单 ROI 自适应 blocks，明确区分“降级模式”
* **可回映射**：事件直接落到组织空间，有利于病理复核与机制叙述
* **技术漂移风险可见**：不黑盒纠正，但提供诊断维度与敏感性结果

## 12.2 生物有效性（必须写入 limitation 的点）

* unmatched mass 无法仅凭 IMC 数据完全识别“真生物生成/消亡 vs 选择偏差”，只能提供证据等级
* 单 ROI block bootstrap 量化的是“ROI 内部重采样不确定性”，不是“术后母体组织 ROI 选择机制不确定性”
* 若缺乏 tissue mask，只能用 nominal area，会降低 density-level UQ 的物理严格性（需在输出与 limitation 明示）

## 12.3 算法优雅性（强项）

* 模块少、解耦清晰：原型字典 → 聚合 → UOT → UQ → remap
* 主要计算是可复现的确定性迭代（给定随机种子）
* 新增复杂度都属于“必要且最小”：

  * 全局 (s_C) 是常数
  * (\lambda^{shape}) 校准复用同一流程
  * 自适应 blocks 与 pseudo-area 是密度合法性的必要工程条款
  * (\varepsilon)-scaling 是数值稳定的默认策略，不改变理论目标

---

# 13) V1.5 伪代码（可直接作为实现蓝图）

下面三段：**Algorithm 1（端到端）**、**Algorithm 2（组内双 (\lambda) 校准）**、**Algorithm 3（UOT 求解：默认 eps-scaling + log-domain）**。关键点都已固化（全局 (s_C)、预计算冻结、自适应 blocks、pseudo-area、双 (\lambda)、eps-scaling）。

```python
# Algorithm 1: End-to-end V1.5
def run_pipeline(patients, params):
    # 1) Preprocess markers & coarse identities e(c)
    preprocess_markers(patients)                # arcsinh/normalization/batch pipeline
    assign_coarse_identities(patients)          # gating or pooled clustering

    # 2) Compute community instances u_c on FULL ROI (once), then robust scale -> u_tilde
    for roi in all_rois(patients):
        roi.knn_graph = build_knn(roi.coords, k=params.k)
        roi.u_tilde = compute_and_block_scale_u(roi, params)  # includes density delta_c

    # 3) Learn global prototypes with balanced sampling
    U_bal = []
    for (p,t) in all_patient_timepoints(patients):
        U_bal += uniform_sample(patients[p].timepoint[t].all_u_tilde, n=params.N_bal)
    z = kmeans(U_bal, K=params.K)               # prototype centers z_k

    # 4) Assign prototype id a(c) for all cells; cache (freeze)
    for roi in all_rois(patients):
        roi.proto_id = assign_prototype(roi.u_tilde, z)  # a(c), frozen for all downstream
        roi.proto_counts = count_by_prototype(roi.proto_id, K=params.K)

    # 5) Global static cost scale s_C (once)
    s_C = global_median_pairwise_dist2(z)       # median(||z_i-z_j||^2, i!=j)
    
    # 6) Define group g: compartment label if provided else ROI-state clustering
    define_groups(patients, params)             # g(r)

    # 7) Calibrate lambda for density and shape (group-wise)
    lambda_dens, lambda_shape = calibrate_lambdas_groupwise(patients, z, s_C, params)

    # 8) Batch drift vector (optional but recommended)
    delta_batch = estimate_batch_drift(patients, anchor_types=params.anchor_types)

    # 9) Per patient inference (dens + shape)
    outputs = {}
    for p in patients:
        outputs[p] = {}
        for g in groups_for_patient(patients[p]):
            a0 = aggregate_density_vector(patients[p], t=0, g=g, params=params)  # a_{p,0,g}
            a1 = aggregate_density_vector(patients[p], t=1, g=g, params=params)  # a_{p,1,g}
            S0, S1 = a0.sum(), a1.sum()
            outputs[p][g] = {"scale_ratio": safe_div(S1, S0), "S0": S0, "S1": S1}

            # Density-level UOT
            Pi_d, metrics_d, events_d = solve_and_decompose_uot(
                a0, a1, z, s_C, lambda_dens[g], params
            )
            # Shape-level UOT (if S0,S1 > 0)
            if S0 > 0 and S1 > 0:
                a0s, a1s = a0/S0, a1/S1
                Pi_s, metrics_s, events_s = solve_and_decompose_uot(
                    a0s, a1s, z, s_C, lambda_shape[g], params
                )
            else:
                Pi_s, metrics_s, events_s = None, None, None

            # Drift alignment flags for remodeling edges
            flag_drift(events_d, z, delta_batch, thr=params.drift_thr)
            if events_s is not None:
                flag_drift(events_s, z, delta_batch, thr=params.drift_thr)

            outputs[p][g].update({
                "density": {"Pi": Pi_d, "metrics": metrics_d, "events": events_d},
                "shape":   {"Pi": Pi_s, "metrics": metrics_s, "events": events_s},
                "lambda_dens": lambda_dens[g], "lambda_shape": lambda_shape[g],
                "s_C": s_C
            })

    # 10) Uncertainty quantification (ROI bootstrap; single-ROI adaptive blocks)
    for p in patients:
        for g in outputs[p]:
            uq = bootstrap_uq(patients[p], g, z, s_C, lambda_dens[g], lambda_shape[g], params)
            outputs[p][g]["UQ"] = uq

    # 11) Remapping package
    for p in patients:
        outputs[p]["remap"] = build_remap_package(patients[p], outputs[p], params)

    return outputs
```

```python
# Algorithm 2: Group-wise calibration of lambda_dens and lambda_shape
def calibrate_lambdas_groupwise(patients, z, s_C, params):
    lambda_dens, lambda_shape = {}, {}
    for g in all_groups(patients):
        # Collect ROI-ROI pairs within pre (t=0) and within group g
        pairs = collect_within_time_pairs(patients, t=0, g=g, max_pairs_per_patient=params.max_pairs)
        if len(pairs) < params.min_pairs_for_calibration:
            continue  # fall back later

        # For each candidate lambda, compute cohort median unmatched ratio
        U_dens = []
        U_shape = []
        for lam in params.lambda_grid:
            uvals_d, uvals_s = [], []
            for (roiA, roiB) in pairs:
                a = roi_density_vector(roiA, params)   # rho_{roiA,k} using proto_id counts / Area
                b = roi_density_vector(roiB, params)
                # density unmatched ratio
                Pi, met, _ = solve_and_decompose_uot(a, b, z, s_C, lam, params, return_events=False)
                uvals_d.append((met["B"] + met["D"]) / (met["T"] + met["B"] + met["D"] + 1e-12))

                # shape unmatched ratio
                if a.sum() > 0 and b.sum() > 0:
                    as_, bs_ = a/a.sum(), b/b.sum()
                    Pi, met, _ = solve_and_decompose_uot(as_, bs_, z, s_C, lam, params, return_events=False)
                    uvals_s.append((met["B"] + met["D"]) / (met["T"] + met["B"] + met["D"] + 1e-12))

            U_dens.append((lam, median(uvals_d)))
            U_shape.append((lam, median(uvals_s) if len(uvals_s)>0 else None))

        # Choose lambda to match tolerance alpha (separately)
        lambda_dens[g]  = argmin_abs(U_dens,  target=params.alpha)
        lambda_shape[g] = argmin_abs([x for x in U_shape if x[1] is not None], target=params.alpha)

    # Fallback if some groups missing (pooling / global)
    fill_missing_with_global_defaults(lambda_dens, lambda_shape, patients, params)
    return lambda_dens, lambda_shape
```

```python
# Algorithm 3: SolveUOT + Decompose (default eps-scaling + log-domain)
def solve_and_decompose_uot(a, b, z, s_C, lam, params, return_events=True):
    # 1) Active set pruning
    active = (a + b) > params.eta
    aA, bA = a[active], b[active]
    zA = z[active_indices(active)]

    # 2) Cost matrix with GLOBAL static scaling
    C = pairwise_dist2(zA) / s_C  # C_ij >= 0

    # 3) UOT solve: log-domain + clamp + eps-scaling (default enabled)
    Pi = uot_sinkhorn_log_eps_scaling(
        aA, bA, C, lam, eps_target=params.eps_target,
        eps_init=params.eps_init, eps_factor=params.eps_factor,
        max_iter=params.max_iter, tol=params.tol, clamp=params.clamp_range
    )

    # 4) Metrics
    T = Pi.sum()
    pre_marg = Pi.sum(axis=1)
    post_marg = Pi.sum(axis=0)
    D = l1_norm(aA - pre_marg)
    B = l1_norm(bA - post_marg)
    M = (C * Pi).sum() / max(T, 1e-12)

    tau = quantile(C.flatten(), params.retention_cost_q)
    R = Pi[C <= tau].sum() / max(T, 1e-12)

    metrics = {"T": T, "B": B, "D": D, "M": M, "R": R, "tau": tau}

    # 5) Events (optional)
    events = None
    if return_events:
        events = extract_events(Pi, C, aA, bA, params)

    return Pi, metrics, events
```

