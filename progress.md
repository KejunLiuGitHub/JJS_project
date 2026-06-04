# AFM 二维聚合物薄膜力学分析 — 进度记录

> 自动生成的分析日志。每次运行追加新章节。

## 项目概览

- **样品**: JJS (<10nm 非晶COF薄膜, SiN孔), linker系列 (50-80nm 结晶COF, 铜网), k80系列 (50-80nm, 铜网)
- **探针**: RTESPA-150 (R=8nm, k=7N/m), DDESP-V2 (R=100nm, k=89N/m)
- **关键修正**: extend=approach/loading, retract=unloading/pull-off (2026-04-25 RealRaw 分支分离)
- **核心发现**: JJS retract pull-off ~115.9 nN >> extend snap-in ~17.3 nN (~7.0x), 液桥-膜顺应性耦合放大

---

## 运行记录

### 2026-06-04 09:21 — 自动分析 #20260604-0921

**数据**: RealRaw/20260409 (JJS, 11 pairs), RealRaw/20260415 (linker, 69 pairs), RealRaw/20260416 (k80, 49 pairs)

**关键结果**:

- JJS extend snap-in: **17.3 nN** [14.0--20.7 nN]
- JJS retract pull-off: **115.9 nN** [108.2--131.0 nN]
- pull-off/snap-in ratio: **7.0x**
- 理论参考 vdW+capillary (R=8nm): **10.2 nN**
- extend/理论比值: **1.7x** — 同量级

**apparent modulus ranking (k80 系列)**: PAA > PFNA > SDBS

**讨论**:

- JJS 接近段吸引力 (~17 nN) 只需略大的有效润湿半径或亲水界面即可解释，不需要 40x Hamaker 增强
- 真正的强信号是 retract pull-off (~116 nN)，属于接触后液桥拉伸/接触线钉扎导致的粘附滞后
- 当前数据支持限域水桥作为候选机制，但不能独立分离 solvation force 和静电力
- 缺少湿度控制和悬浮/支撑对比实验，无法证伪替代解释
- k80 系列的 SDBS 组 N=3，统计意义极弱，只能做趋势讨论

**文献参考**:

- Butt, Cappella, Kappl. *Surface Science Reports* 2005 — AFM 力测量综述
- Israelachvili. *Intermolecular and Surface Forces* 2011 — 毛细力/液桥经典
- Lee et al. *Science* 2008 — 石墨烯 AFM 压入力学
- Xiong et al. *Chemical Science* 2025 — 2D COF 本征力学性能

**完整报告**: [afm_scientific_report.md](JJS_project/reports/realraw/scientific_report/afm_scientific_report.md)

**关键图表**:

![approach_theory](JJS_project/reports/realraw/scientific_report/approach_theory_comparison.png)
![branch_comparison](JJS_project/reports/realraw/scientific_report/branch_force_comparison.png)
![hysteresis](JJS_project/reports/realraw/scientific_report/hysteresis_ratio_work.png)
![modulus_ranking](JJS_project/reports/realraw/scientific_report/apparent_modulus_ranking.png)

### 2026-06-04 09:23 — 自动分析 #20260604-0923

**数据**: RealRaw/20260409 (JJS, 11 pairs), RealRaw/20260415 (linker, 69 pairs), RealRaw/20260416 (k80, 49 pairs)

**关键结果**:

- JJS extend snap-in: **17.3 nN** [14.0--20.7 nN]
- JJS retract pull-off: **115.9 nN** [108.2--131.0 nN]
- pull-off/snap-in ratio: **7.0x**
- 理论参考 vdW+capillary (R=8nm): **10.2 nN**
- extend/理论比值: **1.7x** — 同量级

**apparent modulus ranking (k80 系列)**: PAA > PFNA > SDBS

**讨论**:

- JJS 接近段吸引力 (~17 nN) 只需略大的有效润湿半径或亲水界面即可解释，不需要 40x Hamaker 增强
- 真正的强信号是 retract pull-off (~116 nN)，属于接触后液桥拉伸/接触线钉扎导致的粘附滞后
- 当前数据支持限域水桥作为候选机制，但不能独立分离 solvation force 和静电力
- 缺少湿度控制和悬浮/支撑对比实验，无法证伪替代解释
- k80 系列的 SDBS 组 N=3，统计意义极弱，只能做趋势讨论

**文献参考**:

- Butt, Cappella, Kappl. *Surface Science Reports* 2005 — AFM 力测量综述
- Israelachvili. *Intermolecular and Surface Forces* 2011 — 毛细力/液桥经典
- Lee et al. *Science* 2008 — 石墨烯 AFM 压入力学
- Xiong et al. *Chemical Science* 2025 — 2D COF 本征力学性能

**完整报告**: [afm_scientific_report.md](JJS_project/reports/realraw/scientific_report/afm_scientific_report.md)

**关键图表**:

![approach_theory](JJS_project/reports/realraw/scientific_report/approach_theory_comparison.png)
![branch_comparison](JJS_project/reports/realraw/scientific_report/branch_force_comparison.png)
![hysteresis](JJS_project/reports/realraw/scientific_report/hysteresis_ratio_work.png)
![modulus_ranking](JJS_project/reports/realraw/scientific_report/apparent_modulus_ranking.png)

