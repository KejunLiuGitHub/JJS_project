---
title: "Intermolecular and Surface Forces, 3rd Edition"
authors: "Israelachvili, J. N."
journal: "Academic Press, 2011"
doi: "N/A (book)"
tags: [surface-forces, van-der-Waals, capillary-force, adhesion, textbook]
citation_key: "Israelachvili2011"
cited_in: [progress.md, afm_scientific_report.md]
---

# 分子间力与表面力（第三版）

> 引用格式: `[Israelachvili2011](Israelachvili_2011_IntermolecularForces.md#Lxxx-Lxxx)`
> 分子间力和表面力领域的标准参考书。

---

L001 # 概述
L002 本书是分子间力和表面力物理学的权威教科书，涵盖从基础理论到实验技术的完整体系。
L003 第三版增加了生物相互作用、聚合物力和纳米尺度的最新进展。
L004 > EN: Standard textbook on intermolecular and surface forces, covering theory and experiment.

L005 # 第5章: 范德华力 (van der Waals Forces)
L006 两个宏观物体间的范德华相互作用可以从 Lifshitz 理论导出。
L007 球-平面几何（适合 AFM）的简化公式:
L008 F_vdW = A R / (12 d₀²)
L009 其中 A 为 Hamaker 常数 (~10⁻¹⁹–10⁻²⁰ J)，R 为球半径，d₀ 为最小间距。
L010 大多数凝聚相材料的 Hamaker 常数在 4×10⁻²⁰ 到 1×10⁻¹⁹ J 之间。
L011 > EN: For sphere-flat geometry: F_vdW = A R / (12 d₀²).
L012 > EN: Hamaker constants for most condensed phases are 4×10⁻²⁰ to 1×10⁻¹⁹ J.

L013 # 第15章: 毛细力与液桥 (Capillary Forces and Liquid Bridges)
L014 在空气或蒸气压条件下，两个表面之间可自发形成弯月形液桥。
L015 液桥产生的毛细力由 Laplace 压力项和表面张力项组成。
L016 对于球-平面几何，完全润湿时的最大毛细力:
L017 F_cap = 4π R γ cosθ
L018 对于水 (γ = 72 mN/m)，R = 8 nm 时 F_cap ~ 7.2 nN (θ = 0°)。
L019 实际毛细力受 Kirkwood 有效润湿半径和接触线钉扎影响，通常偏离理想公式。
L020 > EN: Capillary force for sphere-flat in complete wetting: F_cap = 4π R γ cosθ.
L021 > EN: For water (γ = 72 mN/m) with R = 8 nm: F_cap ≈ 7.2 nN.
L022 > EN: Real capillary forces deviate from ideal due to effective wetting radius and contact-line pinning.

L023 # 第17章: 粘附与界面能 (Adhesion and Interfacial Energy)
L024 粘附力受界面能、接触面积、弹性变形和表面粗糙度共同影响。
L025 粘附滞后是指分离力大于接触力的现象。
L026 滞后原因包括: 接触线钉扎、塑性变形、粘弹性耗散、化学键重组。
L027 在 AFM 测量中，pull-off 几乎总是大于 snap-in（对亲水表面在空气中）。
L028 > EN: Adhesion hysteresis means pull-off force > contact force.
L029 > EN: Causes: contact-line pinning, plastic deformation, viscoelastic dissipation, chemical bond reformation.

L030 # 与项目的关联
L031 我们的项目使用 Israrelachvili 的以下内容:
L032 - 范德华力公式估算 F_vdW (L008)
L033 - 毛细力公式估算 F_cap (L017)
L034 - 粘附滞后的物理机制解释 pull-off >> snap-in (L025-L029)
L035 - Hamaker 常数的合理取值范围 (L010)
