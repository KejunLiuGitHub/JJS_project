# AFM 限域水桥文献扫描与 JJS 新颖性判断

更新时间：2026-04-25  
项目：`JJS_project` branch-aware RealRaw AFM force-curve analysis

## 1. 一句话结论

单独宣称“AFM 空气中存在水桥/毛细桥”“湿度影响 pull-off”“纳米限域水被压缩后出现黏弹、层化或 pinning”新颖性较低。这些已经是成熟文献区域。JJS 数据更有希望的主线是：

> branch-resolved AFM reveals water-bridge-amplified adhesion hysteresis coupled to a compliant suspended 2D COF nanomembrane.

也就是说，新颖性应落在“悬浮二维 COF 薄膜几何/顺应性/表面化学如何放大回撤水桥拉伸、接触线钉扎和耗散”上，而不是落在“发现了限域水”本身。

## 2. 现有研究版图

| 方向 | 已有共识 | 对 JJS 的含义 | 代表文献 |
|---|---|---|---|
| AFM 毛细力/水桥 | 空气中亲水 tip-surface 接触常有水 meniscus，capillary force 是 AFM adhesion 的主要来源之一；RH、粗糙度、亲疏水性、tip 半径和动力学都会改变测得力值。 | “水桥导致 pull-off/snap-in”不能单独作为创新点。 | Harrison et al. 2015；Jang et al. 2004 |
| 湿度依赖 pull-off | SiO2 tip/SiO2 surface 的水桥 pull-off 可随 tip 半径近似线性变化，随 RH 呈非单调关系；Kelvin/Young-Laplace 模型能解释一部分趋势。 | 需要湿度序列才能把 JJS 的大回撤力和水桥机制绑定起来。 | Bartosik et al. 2017 |
| 液桥形成、断裂、滞后 | 形成/断裂能垒和 metastable bridge 可自然给出 approach/retract hysteresis。 | JJS 的分支不对称不是概念上全新，但分支分离数据可以成为强证据。 | Men et al. 2009 |
| 水桥动力学 | 水纳米桥凝结时间、横向滑动界面中的成核/生长/黏附仍是活跃问题，速率会影响桥形成和体积。 | 做 approach/retract rate、dwell time、lateral scan 控制可以把 JJS 连接到前沿问题。 | Vitorino et al. 2018；Cassin et al. 2023 |
| 压缩水/限域水层 | 动态 AFM 已显示纳米限域水有非线性黏弹、dynamic solidification、squeeze-out、临界速率和 pinning。 | 现有 JJS 数据可说“consistent with confined-water contribution”，但不能强 claim “solvation force resolved”。 | Li and Riedo 2008；Khan et al. 2010；Khan and Hoffmann 2015 |
| 水桥内界面水结构 | 3D-AFM 已能在纳米水桥内原子尺度成像界面水层，水化层间距约 0.28-0.30 nm。 | “水桥内结构化水”已有强先例，JJS 需要避免把普通结构化水当作主创新。 | Uhlig and Garcia 2021 |
| COF freestanding film mechanics | freestanding 2D COF nanofilm 的拉伸、AFM point-load/nanoindentation、buckling 等力学表征已有报道。 | COF 薄膜力学不是空白；JJS 的机会在 adhesion/water-bridge hysteresis 和膜顺应性耦合，而非单纯模量。 | Pantano et al. 2022；Gazzato et al. 2025 |

## 3. 与当前 JJS 数据的对接

本地 branch-aware 分析已经把原先“约 121 nN approach snap-in”的叙述修正为：

| 指标 | JJS 数值 | 解释 |
|---|---:|---|
| extend branch attraction median | 17.3 nN | 接近经典 RTESPA-150 `R=8 nm` 的 vdW + capillary 量级，理论合计约 10.2 nN。 |
| retract pull-off median | 115.9 nN | 远大于 extend，适合解释为水桥/接触线拉伸、pinning、延迟断裂和界面耗散。 |
| pull-off / extend ratio median | 7.0 | 支持 branch-resolved adhesion hysteresis，而不是单分支 snap-in 异常。 |

数据出处：`reports/realraw/scientific_reinterpretation/realraw_scientific_reinterpretation.md` 和 `results/realraw/scientific_reinterpretation_metrics.json`。

### 新颖性分级

| 等级 | 可写内容 | 判断 |
|---|---|---|
| 低 | AFM 空气中有水桥；水桥影响 pull-off；湿度改变 adhesion。 | 已成熟，不建议作为核心 claim。 |
| 中 | JJS 的 extend/retract 分支分离显示 approach moderate、retract giant 的强滞后。 | 可作为当前数据的稳健结果。 |
| 高潜力 | 悬浮 COF 膜相对支撑膜/空白基底/铜网样品显著放大水桥拉伸和耗散，且受 RH、速率、tip 半径、表面化学系统调控。 | 需要下一轮控制实验验证。 |

### 当前不应强 claim

- 不应说已经直接测到了 solvation force 或单水层振荡力；现有曲线没有湿度、干氮、KPFM、tip-radius 和高分辨 separation calibration 控制。
- 不应从 JJS snap/pull-off 段直接提取 COF 本征 Young's modulus、膜张力或应力；现有局部 post-contact 段过短，adhesion/水桥耦合太强。
- 不应把 retract 的 115.9 nN 映射为单一 Hamaker 常数或单一水桥半径；这些只能作为 diagnostic effective scale。

## 4. 下一步实验矩阵

| 实验轴 | 建议水平 | 固定条件 | 读出量 | 判据 |
|---|---|---|---|---|
| 湿度 RH | 干 N2 或 <5%、20%、40%、60%、80% | 同一 tip、同一点位附近、同一 setpoint、同一速度 | extend minimum、retract pull-off、rupture distance、hysteresis work | 干燥下 retract giant adhesion 显著消失，随 RH 系统变化，则水桥机制坐实。 |
| 速率 | approach/retract velocity 至少 4 档，覆盖当前速度上下一个数量级 | RH 固定，tip 不换 | pull-off、rupture distance、耗散功、断裂概率 | 速率依赖或临界速率行为可连接水桥成核/生长和 squeeze-out 文献。 |
| dwell time | 0、0.1、1、5、10 s | RH 和速度固定 | pull-off 随停留时间增长或饱和 | 若停留时间增强 adhesion，说明桥增长/接触线 aging 重要。 |
| 基底/膜状态 | 悬浮 COF、支撑 COF、空白 SiN/Si、铜网样品 | 同一 RH、tip、速度 | JJS 与控制组的 pull-off/extend ratio | 若只有悬浮 COF 强放大，创新点转向膜顺应性耦合。 |
| tip 半径 | RTESPA-150 小半径、DDESP-V2 大半径、可选 colloidal probe | RH 和样品固定 | force 是否近似随 `R_tip` 放大 | 偏离经典 `F_cap ~ R_tip` 可提示膜变形、接触线钉扎或多接触几何。 |
| 表面化学 | 原始 tip、疏水化 tip、亲水化/清洗基底 | 几何和 RH 固定 | adhesion ranking | 化学依赖可证明 COF 表面/水亲和性参与。 |
| 电荷排除 | KPFM 或接地/偏压控制 | 干燥和湿润条件各做一组 | force-offset、long-range attraction | 避免把静电吸引误判为限域水。 |

## 5. 推荐文章主线

### 标题草案

Branch-resolved AFM reveals water-bridge-amplified adhesion hysteresis in suspended 2D COF nanomembranes

### 核心图

1. Branch-aware force curves：extend vs retract overlay，突出 17.3 nN vs 115.9 nN。
2. Existing theory scale：RTESPA-150 classical vdW + capillary force 与 extend median 对比。
3. Hysteresis map：不同样品/基底/化学的 pull-off ratio 和 hysteresis work ranking。
4. RH/velocity follow-up：把 water bridge mechanism 从 plausible 推到 mechanistic。
5. Control geometry：悬浮 COF vs 支撑 COF vs blank substrate。

### 稳健措辞

- 可用：capillary-confined-water adhesion hysteresis；water-bridge/contact-line pinning；compliant suspended membrane coupling；branch-resolved AFM evidence。
- 慎用：solvation force、hydration-layer force、intrinsic membrane tension、true nanoscale meniscus geometry。
- 避免：we discovered confined water；the 115.9 nN force is purely vdW；JJS snap-in gives Young's modulus。

## 6. Semantic Scholar 检索执行建议

用户提供的 S2 API key 不应明文写入脚本、报告或 shell 历史。建议轮换 key 后只通过环境变量注入：

```bash
export S2_API_KEY="..."
python3 scripts/semantic_scholar_scan.py --outdir results/literature/semantic_scholar
```

脚本默认使用 1.25 s/query 的节流，低于 1 request/s 限制，输出 JSON 和 CSV，便于后续用 citation count、year、DOI 和 title 做去重筛选。

## References

[1] Aaron J. Harrison, David S. Corti, and Stephen P. Beaudoin. (2015). Capillary Forces in Nanoparticle Adhesion: A Review of AFM Methods. *Particulate Science and Technology*, 33(5), 526-538. https://doi.org/10.1080/02726351.2015.1045641

[2] Joonkyung Jang, George C. Schatz, and Mark A. Ratner. (2004). Capillary force in atomic force microscopy. *Journal of Chemical Physics*, 120(3), 1157-1160. https://doi.org/10.1063/1.1640332

[3] Miroslav Bartosik, Lukáš Kormoš, Lukáš Flajšman, Radek Kalousek, Jindřich Mach, Zuzana Lišková, David Nezval, Vojtěch Švarc, Tomáš Šamořil, and Tomáš Šikola. (2017). Nanometer-Sized Water Bridge and Pull-Off Force in AFM at Different Relative Humidities: Reproducibility Measurement and Model Based on Surface Tension Change. *Journal of Physical Chemistry B*, 121(3), 610-619. https://doi.org/10.1021/acs.jpcb.6b11108

[4] Yumei Men, Xianren Zhang, and Wenchuan Wang. (2009). Capillary liquid bridges in atomic force microscopy: Formation, rupture, and hysteresis. *Journal of Chemical Physics*, 131(18), 184702. https://doi.org/10.1063/1.3257624

[5] Miguel V. Vitorino, Arthur Vieira, Carolina A. Marques, and Mario S. Rodrigues. (2018). Direct measurement of the capillary condensation time of a water nanobridge. *Scientific Reports*, 8, 13848. https://doi.org/10.1038/s41598-018-32021-0

[6] Felix Cassin, Rachid Hahury, Thibault Lançon, Steve Franklin, and Bart Weber. (2023). The nucleation, growth, and adhesion of water bridges in sliding nano-contacts. *Journal of Chemical Physics*, 158, 224703. https://doi.org/10.1063/5.0150276

[7] Tai-De Li and Elisa Riedo. (2008). Nonlinear Viscoelastic Dynamics of Nanoconfined Wetting Liquids. *Physical Review Letters*, 100, 106102. https://doi.org/10.1103/PhysRevLett.100.106102

[8] Shah H. Khan, George Matei, Shivprasad Patil, and Peter M. Hoffmann. (2010). Dynamic Solidification in Nanoconfined Water Films. *Physical Review Letters*, 105, 106101. https://doi.org/10.1103/PhysRevLett.105.106101

[9] Shah H. Khan and Peter M. Hoffmann. (2015). Squeeze-out dynamics of nanoconfined water: A detailed nanomechanical study. *Physical Review E*, 92, 042403. https://doi.org/10.1103/PhysRevE.92.042403

[10] Manuel R. Uhlig and Ricardo Garcia. (2021). In Situ Atomic-Scale Imaging of Interfacial Water under 3D Nanoscale Confinement. *Nano Letters*, 21(13), 5593-5598. https://doi.org/10.1021/acs.nanolett.1c01092

[11] Maria F. Pantano, Elena Missale, Luana Gazzato, Roberto Pilot, Francesco Sedona, Giorgio Speranza, and Marco Frasconi. (2022). Large freestanding 2D covalent organic framework nanofilms exhibiting high strength and stiffness. *Materials Today Chemistry*, 26, 101007. https://doi.org/10.1016/j.mtchem.2022.101007

[12] Luana Gazzato, Elena Missale, Daniele Asnicar, Francesco Sedona, Giorgio Speranza, Alessandra Del Giudice, Luciano Galantini, Alberta Ferrarini, Marco Frasconi, and Maria F. Pantano. (2025). Structural Insights into the Mechanical Behavior of Large-Area 2D Covalent Organic Framework Nanofilms. *ACS Applied Materials & Interfaces*, 17(17), 25819-25827. https://doi.org/10.1021/acsami.5c03512
