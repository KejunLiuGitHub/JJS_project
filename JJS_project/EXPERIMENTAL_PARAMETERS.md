# AFM 实验参数汇总与修正记录

> **最后更新**: 2026-04-23
> **修正原因**: 各数据集目录下新增 readme.md 文件，揭示了之前脚本中的探针参数错误

> **2026-04-25 RealRaw 修正**: 新数据明确分出 `extend` 与 `retract`。
> 旧分析中的 JJS `~120 nN` 大负力主要来自 `retract` pull-off/粘附脱离，
> 不是 approach/extend snap-in。新的分支分析显示 JJS extend 吸引力中位数约
> `17 nN`，接近 RTESPA-150 `R=8 nm` 下的经典 `vdW + capillary ~10 nN`；
> JJS retract pull-off 中位数约 `116 nN`，应解释为水桥/限域水/接触线钉扎导致的强粘附滞后。
> 详见 `reports/realraw/scientific_reinterpretation/realraw_scientific_reinterpretation.md`。

---

## 一、三批次实验参数对照表

| 参数 | 20260409 (JJS) | 20260415 (linker1/linker2) | 20260416 (k80) |
|------|----------------|---------------------------|----------------|
| **样品类型** | 超晶格非晶薄膜 | 高度结晶厚膜 | 高度结晶厚膜 |
| **膜厚** | **< 10 nm** | **50–80 nm** | **50–80 nm** |
| **化学成分** | 酒石酸 (表面活性剂) | linker1/linker2-PAA/NLS/PFPE-OH | PFNA/SDBS/PAA (氟化链) |
| **基底** | **氮化硅带孔** (SiN pore) | **铜网** (copper mesh) | **铜网** (copper mesh) |
| **探针型号** | RTESPA-150 | RTESPA-150 | DDESP-V2 |
| **探针材料** | 单晶硅 (Sb掺杂) | 单晶硅 (Sb掺杂) | 金刚石涂层硅 |
| **悬臂梁刚度 k_lever** | **7.0 N/m** (校准后) | **7.0 N/m** (校准后) | **89.0 N/m** (校准后) |
| **尖端半径 R** | **8 nm** | **8 nm** | **~100 nm** |
| **悬臂梁尺寸** | T:1.75μm L:125μm W:35μm | T:1.75μm L:125μm W:35μm | T:3.8μm L:125μm W:35μm |
| **共振频率** | 150 kHz | 150 kHz | 400 kHz |
| **setpoint 范围** | 8–50 nN | 100 nN | 3–10 μN |
| **压电陶瓷位移** | 454–1500 nm | 150–2500 nm | 500–12410 nm |
| **文件数** | 11 | 56 | 49 |

---

## 二、关键物理差异

### 2.1 薄膜结构差异

| 特性 | JJS (<10nm 非晶) | linker/k80 (50-80nm 结晶) |
|------|------------------|---------------------------|
| 晶体结构 | **非晶** (amorphous) | **高度结晶** (highly crystalline) |
| 厚度 | **< 10 nm** (超薄) | **50–80 nm** (厚膜) |
| 柔韧性 | 极易变形，张力主导 | 有一定弯曲刚度 |
| 预应力 | 较高（桥拱效应显著）| 相对较低 |
| extend snap-in 力 | **~17 nN** (中位数，9–22 nN 范围) | 多数 ~0.3–2 nN |
| retract pull-off 粘附 | **~116 nN** (中位数，强滞后) | 数 nN到十几 nN，PAA/linker2-PAA 更强 |

### 2.2 探针差异对测量的影响

| 参数 | RTESPA-150 (20260409/15) | DDESP-V2 (20260416) |
|------|--------------------------|---------------------|
| 刚度 | 7 N/m (软) | 89 N/m (硬) |
| 尖端半径 | 8 nm (超尖) | ~100 nm (钝) |
| 适用场景 | 软样品，高分辨率 | 硬样品，深压入 |
| 对薄膜的影响 | 易刺穿超薄非晶膜 | 适合压入厚结晶膜 |
| 接触力学模型 | 点载荷近似较好 | 需考虑钝探头接触区 |

---

## 三、参数修正记录

### 修正前（错误）

| 脚本 | 错误参数 | 错误值 |
|------|---------|--------|
| JJS_analysis.py | CANTILEVER_STIFFNESS_N_M | 5.0 N/m |
| k80_linker1_paa_analysis.py | CANTILEVER_STIFFNESS_N_M | 5.0 N/m |
| k80_linker1_paa_analysis.py | PROBE_RADIUS_NM | 8.0 nm |
| dataset_registry.py (全部) | cantilever_stiffness_N_m | 5.0 N/m |
| membrane_mechanics.py | K_CANTILEVER | 5.0 N/m |

### 修正后（正确）

| 脚本 | 正确参数 | 正确值 | 数据集 |
|------|---------|--------|--------|
| JJS_analysis.py | CANTILEVER_STIFFNESS_N_M | **7.0 N/m** | 20260409 |
| linker1_*.py | CANTILEVER_STIFFNESS_N_M | **7.0 N/m** | 20260415 |
| k80_*.py | CANTILEVER_STIFFNESS_N_M | **89.0 N/m** | 20260416 |
| k80_*.py | PROBE_RADIUS_NM | **100.0 nm** | 20260416 |
| dataset_registry.py | 全部已更新 | 见上表 | 全部 |
| membrane_mechanics.py | K_CANTILEVER | **7.0 N/m** | JJS专用 |

---

## 四、Snap-in / Pull-off 力差异的物理解释

### 4.1 JJS 强 retract pull-off (~116 nN) 的来源

RealRaw 分支修正后，JJS 的 `extend` snap-in 不是 ~120 nN，而是约 **17 nN** 中位数。
这与 `R=8 nm` 探针的经典 `vdW + capillary ~10 nN` 同量级，只需要毛细桥、亲水界面、
动态效应或有效接触半径略增即可解释。真正大的信号是 `retract` pull-off，约 **116 nN**
中位数，比 extend 大约 **7 倍**，主要原因更可能是：

1. **薄膜厚度效应** (<10nm vs 50-80nm):
   - 超薄非晶膜容易与液桥/探针接触区耦合变形
   - 回撤时水桥和软膜共同被拉伸，导致 pull-off 延迟

2. **结构差异** (非晶 vs 结晶):
   - 非晶膜表面更"软"，探针-膜接触更紧密
   - 可能形成更稳定的毛细桥（表面活性剂亲水）

3. **基底差异** (氮化硅 vs 铜网):
   - 氮化硅表面亲水，易吸附水膜
   - 铜网为金属，表面性质和电荷屏蔽不同

4. **接触线钉扎与限域水滞后**:
   - approach 阶段只需要形成/触发水桥
   - retract 阶段水桥颈部被拉伸并延迟断裂，因此力远大于 approach snap-in

### 4.2 毛细伪刚度 (Capillary Pseudo-stiffness)

毛细伪刚度仍是有价值的概念，但应主要用于解释 **retract pull-off 和滞后段的表观刚度**，
而不是把 `~120 nN` 当作 approach snap-in 反推本征薄膜张力。负力区斜率陡峭的可能来源
不是薄膜本身变硬，而是**液桥颈部曲率急剧变小导致的拉普拉斯负压飙升**。

拉普拉斯方程：$\Delta P = \gamma(1/R_1 + 1/R_2)$

当探针-薄膜间隙 $d$ 减小时，液桥颈部半径 $r_{neck}$ 迅速减小，负压 $|\Delta P|$ 急剧增大，产生表观上的"大刚度"。

**定量评估**：
- 简单圆柱液桥模型：$k_{cap} \sim 0.16$ N/m（太小）
- 实际观测：$k_{cap} \sim 22$ N/m
- **差距原因**：纳米尺度液桥几何远比圆柱复杂，可能涉及动态效应、表面电荷、膜变形耦合等

**结论**："毛细伪刚度"是**有价值的定性概念**，但定量模型仍需完善。它与软膜变形、
限域水和接触线钉扎共同解释 JJS 的强 retract pull-off/粘附滞后。

### 4.3 限域水 (Confined Water) 的可能贡献

在纳米级间隙 (d < 5 nm) 中，水分子可能形成有序层状结构，产生额外的**溶剂化力** (solvation force)：

$$F_{sol}(d) = F_0 \exp(-d/\lambda) \cos(2\pi d / \sigma)$$

对于 JJS (氮化硅+酒石酸，亲水表面)：
- 水膜厚度可能更大
- 限域水有序化程度更高
- 可能贡献额外的 10–50 nN 吸引力

**但**：现有数据不能把限域水、毛细桥和静电效应独立分离。限域水应表述为强粘附滞后的
候选机制，而不是已经被单独定量证明的力项。

---

## 五、分析建议

### 5.1 各数据集适用的分析模型

| 数据集 | 推荐模型 | 注意事项 |
|--------|---------|----------|
| JJS (20260409) | extend/retract 粘附滞后 + 毛细/限域水模型 | intrinsic E/T/σ 不能从 snap/pull-off 可靠提取 |
| linker1 (20260415) | 线性膜力学 (F = k₁D) | 浅压入，数据线性，k₃ 不可靠 |
| k80 (20260416) | 非线性膜力学 (F = k₁D + k₃D³) | 深压入，但探针太钝 (R=100nm)，需修正接触模型 |

### 5.2 DDESP-V2 探针的特殊处理

DDESP-V2 的 R ≈ 100 nm，远大于 RTESPA-150 的 8 nm：
- **不能直接使用点载荷模型** (F ∝ E₂D·D³/R²)
- 应改用 **Hertzian 接触模型** 或 **钝探头膜压入模型**
- 接触区半径 a = √(R·D) 可能达到数十 nm，与膜厚可比拟

---

## 六、数据来源

- `20260409/readme.md` — JJS 实验参数
- `20260415原始数据/readme.md` — linker1/linker2 实验参数
- `20260416原始数据/readme.md` — k80 实验参数
- `scripts/dataset_registry.py` — 修正后的中央配置
