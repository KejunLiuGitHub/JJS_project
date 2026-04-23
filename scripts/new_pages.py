# 新增页面函数（将插入 generate_jjs_report.py）
# 模块 1-4 的深度分析页面

def page_asymmetry_analysis(pdf, curves):
    fig, axes = plt.subplots(2, 2, figsize=(A4_W, A4_H))
    
    labels_short = [c['file'].replace('JJS-50nm-', '').replace(' - NanoScope Analysis.txt', '') for c in curves]
    drops = [c['max_drop_slope'] for c in curves]
    rises = [c['max_rise_slope'] for c in curves]
    asymms = [abs(r/d) if d != 0 else 0 for r, d in zip(rises, drops)]
    disps = [c['disp'] for c in curves]
    
    # 左上：下降斜率
    ax = axes[0, 0]
    x = np.arange(len(labels_short))
    colors = ['red' if d < -80 else 'orange' if d < -40 else 'steelblue' for d in drops]
    bars = ax.bar(x, np.abs(drops), color=colors, edgecolor='black')
    ax.set_xticks(x)
    ax.set_xticklabels(labels_short, rotation=45, ha='right', fontsize=6)
    ax.set_ylabel('|Drop Slope| (N/m)', fontsize=10)
    ax.set_title('下降段最大斜率（Snap-in 过程）', fontsize=12, fontweight='bold')
    ax.grid(axis='y', alpha=0.3)
    ax.axhline(5, color='green', linestyle='--', linewidth=1, label='k_c = 5 N/m')
    ax.legend()
    
    # 右上：上升斜率
    ax = axes[0, 1]
    bars = ax.bar(x, rises, color='coral', edgecolor='black')
    ax.set_xticks(x)
    ax.set_xticklabels(labels_short, rotation=45, ha='right', fontsize=6)
    ax.set_ylabel('Rise Slope (N/m)', fontsize=10)
    ax.set_title('上升段最大斜率（恢复过程）', fontsize=12, fontweight='bold')
    ax.grid(axis='y', alpha=0.3)
    ax.axhline(5, color='green', linestyle='--', linewidth=1, label='k_c = 5 N/m')
    ax.legend()
    
    # 左下：不对称比
    ax = axes[1, 0]
    bars = ax.bar(x, asymms, color='mediumpurple', edgecolor='black')
    ax.set_xticks(x)
    ax.set_xticklabels(labels_short, rotation=45, ha='right', fontsize=6)
    ax.set_ylabel('Asymmetry Ratio (|rise|/|drop|)', fontsize=10)
    ax.set_title('不对称比', fontsize=12, fontweight='bold')
    ax.grid(axis='y', alpha=0.3)
    
    # 右下：不对称比 vs 位移
    ax = axes[1, 1]
    ax.scatter(disps, asymms, s=100, color='mediumpurple', edgecolors='black', zorder=5)
    for c in curves:
        ax.annotate(f"{c['disp']:.0f}nm", (c['disp'], abs(c['max_rise_slope']/c['max_drop_slope']) if c['max_drop_slope'] != 0 else 0),
                   fontsize=8, ha='center', va='bottom')
    ax.set_xlabel('Displacement (nm)', fontsize=10)
    ax.set_ylabel('Asymmetry Ratio', fontsize=10)
    ax.set_title('不对称比 vs 位移', fontsize=12, fontweight='bold')
    ax.grid(True, alpha=0.3)
    
    fig.suptitle('模块1：不对称性定量分析', fontsize=16, fontweight='bold', y=0.98)
    pdf.savefig(fig, dpi=200)
    plt.close(fig)


def page_vdw_fitting(pdf, curves):
    fig, axes = plt.subplots(1, 2, figsize=(A4_W, A4_H))
    
    # 找到有 vdW 拟合的曲线
    fit_curves = [c for c in curves if c.get('vdw_fit')]
    
    for ax, c in zip(axes, fit_curves):
        fit = c['vdw_fit']
        drop_z = np.array(c['drop_z'])
        drop_f = np.array(c['drop_f'])
        
        # 选取吸引区 f < -2
        valid = drop_f < -2.0
        if np.sum(valid) < 5:
            continue
        
        vd_z = drop_z[valid]
        vd_f = np.abs(drop_f[valid])
        contact_z = c['contact_z_nm']
        d_est = contact_z - vd_z
        
        # 过滤
        mask = d_est > 0.5
        d_est = d_est[mask]
        vd_f = vd_f[mask]
        
        # log-log 图
        ax.scatter(d_est, vd_f, s=30, color='steelblue', edgecolors='black', zorder=5, label='Data')
        
        # 拟合线
        if len(d_est) >= 3:
            log_d = np.log(d_est)
            log_f = np.log(vd_f)
            coeffs = np.polyfit(log_d, log_f, 1)
            d_fit = np.linspace(np.min(d_est), np.max(d_est), 100)
            f_fit = np.exp(coeffs[1]) * d_fit**coeffs[0]
            ax.plot(d_fit, f_fit, 'r--', linewidth=2, 
                    label=f"Fit: |F|={np.exp(coeffs[1]):.1f}*d^{coeffs[0]:.2f}\nR2={fit['R2']:.2f}")
        
        # 理论线
        d_theory = np.linspace(0.5, np.max(d_est), 100)
        A = 4e-19  # J
        R = 8e-9  # m
        F_vdw = A * R / (6 * (d_theory * 1e-9)**2) * 1e9  # nN
        ax.plot(d_theory, F_vdw, 'g:', linewidth=2, label='Non-retarded vdW (A=4e-19J)')
        
        ax.set_xlabel('Distance d (nm)', fontsize=11)
        ax.set_ylabel('|Force| (nN)', fontsize=11)
        ax.set_title(f"{c['file'].replace('JJS-50nm-', '').replace(' - NanoScope Analysis.txt', '')}\n"
                     f"Snap-in 前 vdW 距离依赖性", fontsize=12, fontweight='bold')
        ax.set_xscale('log')
        ax.set_yscale('log')
        ax.legend(loc='best', fontsize=9)
        ax.grid(True, alpha=0.3, which='both')
    
    fig.suptitle('模块2：Snap-in 前 vdW 距离依赖性拟合', fontsize=16, fontweight='bold', y=0.98)
    pdf.savefig(fig, dpi=200)
    plt.close(fig)


def page_recovery_behavior(pdf, curves):
    fig, axes = plt.subplots(2, 2, figsize=(A4_W, A4_H))
    
    # 左上图：局部斜率分布（选 4 条代表性曲线）
    ax = axes[0, 0]
    selected = [c for c in curves if c['disp'] in (454.0, 500.0, 1000.0, 1500.0)]
    colors = ['red', 'orange', 'blue', 'green']
    for c, color in zip(selected, colors):
        if len(c.get('rise_z', [])) >= 3:
            rise_z = np.array(c['rise_z'])
            rise_f = np.array(c['rise_f'])
            local_slopes = np.diff(rise_f) / np.diff(rise_z)
            local_z = (rise_z[:-1] + rise_z[1:]) / 2 - c['snap_z_nm']
            ax.plot(local_z, local_slopes, color=color, linewidth=1.5, 
                    label=f"{c['disp']:.0f}nm")
    ax.axhline(0, color='black', linestyle='--', linewidth=0.8)
    ax.axhline(5, color='green', linestyle='--', linewidth=1, label='k_c = 5 N/m')
    ax.set_xlabel('Relative Z (nm, 0 = snap-in)', fontsize=10)
    ax.set_ylabel('Local Slope (N/m)', fontsize=10)
    ax.set_title('恢复段局部斜率分布', fontsize=12, fontweight='bold')
    ax.legend(loc='best', fontsize=9)
    ax.grid(True, alpha=0.3)
    
    # 右上图：plateau 检测
    ax = axes[0, 1]
    labels = [c['file'].replace('JJS-50nm-', '').replace(' - NanoScope Analysis.txt', '') for c in curves]
    plateau_fracs = [c.get('recovery', {}).get('plateau_fraction', 0) for c in curves]
    x = np.arange(len(labels))
    ax.bar(x, plateau_fracs, color='lightcoral', edgecolor='black')
    ax.set_xticks(x)
    ax.set_xticklabels(labels, rotation=45, ha='right', fontsize=6)
    ax.set_ylabel('Plateau Fraction', fontsize=10)
    ax.set_title('毛细桥 Plateau 检测（|slope|<0.5 N/m）', fontsize=12, fontweight='bold')
    ax.grid(axis='y', alpha=0.3)
    
    # 左下图：理论毛细力 vs 实测
    ax = axes[1, 0]
    f_caps = [c['vdW_check']['F_capillary_theory_nN'] for c in curves]
    f_measured = [c['vdW_check']['F_measured_nN'] for c in curves]
    ax.scatter(f_caps, f_measured, s=100, color='steelblue', edgecolors='black', zorder=5)
    ax.plot([0, 10], [0, 10], 'k--', linewidth=1, label='1:1 line')
    ax.set_xlabel('Theoretical Capillary Force (nN)', fontsize=10)
    ax.set_ylabel('Measured Snap-in Force (nN)', fontsize=10)
    ax.set_title('实测力 vs 理论毛细力', fontsize=12, fontweight='bold')
    ax.set_xlim(0, 10)
    ax.set_ylim(0, 160)
    ax.legend()
    ax.grid(True, alpha=0.3)
    
    # 右下图：能量耗散
    ax = axes[1, 1]
    disps = [c['disp'] for c in curves]
    energies = [c['energy_dissipated_nN_nm'] for c in curves]
    ax.scatter(disps, energies, s=100, c=[abs(c['snap_f']) for c in curves], 
               cmap='Reds', edgecolors='black', zorder=5)
    ax.set_xlabel('Displacement (nm)', fontsize=10)
    ax.set_ylabel('Energy Dissipated (nN·nm)', fontsize=10)
    ax.set_title('过渡区能量耗散', fontsize=12, fontweight='bold')
    ax.grid(True, alpha=0.3)
    
    fig.suptitle('模块3：恢复行为与毛细桥判断', fontsize=16, fontweight='bold', y=0.98)
    pdf.savefig(fig, dpi=200)
    plt.close(fig)


def page_retarded_vdw(pdf, curves):
    fig = plt.figure(figsize=(A4_W, A4_H))
    fig.clf()
    
    fig.text(0.5, 0.95, '模块4：延迟 vdW 检验与水分子限域效应', 
             ha='center', va='top', fontsize=18, fontweight='bold')
    
    # 左侧：理论值 vs 实测值对比表
    fig.text(0.25, 0.88, '理论力 vs 实测力对比', 
             ha='center', va='top', fontsize=14, fontweight='bold', color='darkblue')
    
    table_text = (
        "理论模型预测（d0 = 0.3 nm）：\n\n"
        "  非延迟 vdW (DMT):\n"
        "    F = A*R/(12*d0^2)\n"
        "    A = 4e-19 J (典型聚合物)\n"
        "    F_vdw = 2.96 nN\n\n"
        "  延迟 vdW (Casimir-Polder):\n"
        "    F = pi^3*hbar*c*R/(360*d0^3)*eta\n"
        "    eta = 0.4 (聚合物/氮化硅)\n"
        "    F_CP = 0.037 nN\n\n"
        "  毛细力 (Kelvin方程):\n"
        "    F = 4*pi*R*gamma\n"
        "    gamma = 72 mN/m (水)\n"
        "    F_cap = 7.24 nN\n\n"
        "  vdW + 毛细力总和:\n"
        "    F_total = 10.2 nN\n\n"
        "实测 Snap-in 力:\n"
        "  最小: 99.0 nN (1500nm-10nN)\n"
        "  最大: 150.6 nN (454nm-8.862nN)\n"
        "  均值: 120.7 nN\n\n"
        "结论:\n"
        "  实测力 = 10-15 x 理论总和\n"
        "  单一机制无法解释\n"
        "  必须引入几何增强因子 10-15x"
    )
    fig.text(0.03, 0.83, table_text, ha='left', va='top', fontsize=10,
             bbox=dict(boxstyle='round', facecolor='lightblue', alpha=0.3))
    
    # 右侧：水分子限域效应分析
    fig.text(0.75, 0.88, '水分子限域效应分析（湿度 >60%）', 
             ha='center', va='top', fontsize=14, fontweight='bold', color='darkgreen')
    
    water_text = (
        "高湿度下的纳米间隙水行为：\n\n"
        "1. 吸附层形成:\n"
        "   探针和薄膜表面均吸附水分子层\n"
        "   厚度 ~0.3-1 nm（取决于湿度）\n"
        "   吸附层降低有效 Hamaker 常数?\n"
        "   → 实测表明有效 A 反而增大 30-50x\n\n"
        "2. 毛细桥成核:\n"
        "   探针接近时，水分子在间隙中凝聚\n"
        "   形成纳米级液桥（ neck radius < 10 nm）\n"
        "   但恢复段未观察到力 plateau\n"
        "   → 毛细桥维持时间极短或不稳定\n\n"
        "3. 受限水的粘度增大:\n"
        "   纳米间隙 (< 5 nm) 中水的粘度\n"
        "   可能比体相高 10-1000 倍\n"
        "   可能导致探针接近时的能量耗散\n"
        "   过渡区能量耗散: 800-1800 nN·nm\n\n"
        "4. 综合图像:\n"
        "   • 远距离 (> 10 nm): 延迟 vdW（微弱）\n"
        "   • 中距离 (1-10 nm): 非延迟 vdW + 水吸附层\n"
        "   • 近距离 (< 1 nm): 毛细桥快速成核\n"
        "   • 接触后: 粘着接触 + 悬臂弹性恢复\n\n"
        "关键问题:\n"
        "   为什么有效 A 增大 30-50 倍?\n"
        "   → 薄膜局部曲率增强（几何因子）\n"
        "   → 多体相互作用（水分子介导）\n"
        "   → 薄膜机械不稳定性（下凹放大吸引力）"
    )
    fig.text(0.53, 0.83, water_text, ha='left', va='top', fontsize=10,
             bbox=dict(boxstyle='round', facecolor='lightgreen', alpha=0.3))
    
    # 底部：关键数值
    fig.text(0.5, 0.08, 
             '核心矛盾：DMT/Casimir 预测 ~3-10 nN，实测 100-150 nN，差距 10-50 倍。'
             ' 高湿度下水分子限域效应和薄膜几何增强是主要增强机制。',
             ha='center', fontsize=11, color='darkred', fontweight='bold',
             bbox=dict(boxstyle='round', facecolor='yellow', alpha=0.3))
    
    pdf.savefig(fig, dpi=200)
    plt.close(fig)
