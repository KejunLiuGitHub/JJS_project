---
title: "Force measurements with the atomic force microscope: Technique, interpretation and applications"
authors: "Butt, H.-J.; Cappella, B.; Kappl, M."
journal: "Surface Science Reports 2005, 59 (1–6), 1–152"
doi: "10.1016/j.surfrep.2005.08.003"
tags: [AFM, force-distance-curve, surface-forces, review, capillary-force, adhesion]
citation_key: "Butt2005"
cited_in: [progress.md, afm_scientific_report.md]
---

# AFM 力测量：技术、解释与应用

> 引用格式: `[Butt2005](Butt_2005_SurfSciRep.md#Lxxx-Lxxx)`

---

L001 # 摘要
L002 本文全面综述了 AFM 力-距离曲线的测量技术、数据解释和应用。
L003 力曲线提供关于局部材料性质的信息，包括弹性、硬度、Hamaker 常数、粘附力和表面电荷密度。
L004 综述涵盖了表面力测量、单分子力谱、受限液体结构以及力曲线分析的技术细节。
L005 还讨论了关键实验问题：弹簧常数的测定、针尖半径的校准。
L006 截至 2005 年，力曲线已从专家工具转变为常规 AFM 表征手段。
L007 > EN: The review describes force-distance curves, their measurement, interpretation, and applications
L008 > EN: in surface science, materials engineering, and biology. Key experimental issues such as
L009 > EN: spring constant determination and tip radius characterization are discussed in detail.

L010 # 1. Introduction
L011 力-距离曲线是 AFM 最基本的测量模式之一。
L012 通过记录探针接近和离开表面时悬臂的挠度，可以提取针尖-样品相互作用的定量信息。
L013 关键可测量量包括: snap-in force（跳入力）、pull-off force（拉脱力）、
L014 接触刚度、能量耗散和长程力的距离依赖性。
L015 > EN: Force-distance curves record cantilever deflection versus piezo displacement during approach and retraction.
L016 > EN: They provide quantitative information about tip-sample interactions.

L017 # 2. 表面力基础
L018 在 AFM 力测量中，需要考虑的主要表面力包括:
L019 - 范德华力 (van der Waals): 普遍存在的远程吸引力
L020 - 静电力 (electrostatic): 受表面电荷和溶液条件影响
L021 - 毛细力 (capillary): 在空气中由于表面水膜凝结形成的液桥力
L022 - 溶剂化力 (solvation): 在液体中由于溶剂分子层化产生的振荡力
L023 - 疏水力 (hydrophobic): 水中疏水表面间的长程吸引力
L024 - 空间位阻力 (steric): 吸附聚合物层或生物分子产生的排斥力
L025 > EN: The main surface forces include van der Waals, electrostatic double-layer, capillary (in air),
L026 > EN: solvation (in liquids), hydrophobic, and steric/polymer-induced forces.

L027 # 3. 毛细力与液桥 (Capillary Forces and Liquid Bridges)
L028 在空气环境中，亲水表面常被薄水膜覆盖。当 AFM 针尖接近样品时，
L029 水膜凝聚形成弯月形液桥，产生强烈的毛细吸引力。
L030 完全润湿条件下的毛细桥力: F_cap = 4πR γ cosθ
L031 其中 R 为针尖半径，γ 为液体表面张力，θ 为有效接触角。
L032 毛细力依赖于湿度、表面亲水性和粗糙度。
L033 液桥形成后，探针回撤时由于接触线钉扎 (contact line pinning)，
L034 pull-off force 通常远大于 snap-in force，产生显著的粘附滞后。
L035 > EN: In ambient conditions, water layers on hydrophilic surfaces condense into capillary bridges.
L036 > EN: The capillary force in the complete wetting limit is F_cap = 4πR γ cosθ.
L037 > EN: Contact line pinning during retraction leads to adhesion hysteresis — pull-off >> snap-in.

L038 # 4. 接触力学模型
L039 力曲线中接触区的分析依赖于接触力学模型。常用模型包括:
L040 - Hertz 模型: 纯弹性接触，无粘附
L041 - JKR (Johnson-Kendall-Roberts): 含粘附的弹性接触，适用于大半径软材料
L042 - DMT (Derjaguin-Muller-Toporov): 含粘附的弹性接触，适用于小半径硬材料
L043 选择模型时需要根据 Tabor 参数 μ 判断。
L044 > EN: Contact mechanics models for interpreting AFM force curves include Hertz (pure elastic),
L045 > EN: JKR (adhesive, large soft contacts), and DMT (adhesive, small stiff contacts).

L046 # 5. 实验技术要点
L047 - 弹簧常数校准: thermal noise method, Sader method, reference cantilever method
L048 - 针尖半径表征: SEM imaging, blind tip reconstruction, tip characterizer samples
L049 - 压电位移的灵敏度校准: 在硬表面上做力曲线获取 deflection sensitivity
L050 - 零距离定义: contact point 的准确判定是定量分析的前提
L051 > EN: Critical calibrations: spring constant, tip radius, deflection sensitivity, and zero-distance definition.

L052 # 6. 粘附力与滞后 (Adhesion and Hysteresis)
L053 pull-off force 代表拉开接触所需的最大力，受以下因素影响:
L054 - 实际接触面积 (接触几何和变形)
L055 - 界面能 (表面化学和液体环境)
L056 - 接触时间和加载速率 (动态效应)
L057 - 表面粗糙度 (多粗糙峰接触 vs 单粗糙峰)
L058 加载-卸载曲线之间的面积差代表能量耗散 (hysteresis work)。
L059 > EN: Pull-off force depends on contact area, interfacial energy, contact time, loading rate, and roughness.
L060 > EN: The area between loading and unloading curves represents dissipated energy.
