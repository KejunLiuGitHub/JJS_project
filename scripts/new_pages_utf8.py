# 鏂板椤甸潰鍑芥暟锛堝皢鎻掑叆 generate_jjs_report.py锛?# 妯″潡 1-4 鐨勬繁搴﹀垎鏋愰〉闈?
def page_asymmetry_analysis(pdf, curves):
    fig, axes = plt.subplots(2, 2, figsize=(A4_W, A4_H))
    
    labels_short = [c['file'].replace('JJS-50nm-', '').replace(' - NanoScope Analysis.txt', '') for c in curves]
    drops = [c['max_drop_slope'] for c in curves]
    rises = [c['max_rise_slope'] for c in curves]
    asymms = [abs(r/d) if d != 0 else 0 for r, d in zip(rises, drops)]
    disps = [c['disp'] for c in curves]
    
    # 宸︿笂锛氫笅闄嶆枩鐜?    ax = axes[0, 0]
    x = np.arange(len(labels_short))
    colors = ['red' if d < -80 else 'orange' if d < -40 else 'steelblue' for d in drops]
    bars = ax.bar(x, np.abs(drops), color=colors, edgecolor='black')
    ax.set_xticks(x)
    ax.set_xticklabels(labels_short, rotation=45, ha='right', fontsize=6)
    ax.set_ylabel('|Drop Slope| (N/m)', fontsize=10)
    ax.set_title('涓嬮檷娈垫渶澶ф枩鐜囷紙Snap-in 杩囩▼锛?, fontsize=12, fontweight='bold')
    ax.grid(axis='y', alpha=0.3)
    ax.axhline(5, color='green', linestyle='--', linewidth=1, label='k_c = 5 N/m')
    ax.legend()
    
    # 鍙充笂锛氫笂鍗囨枩鐜?    ax = axes[0, 1]
    bars = ax.bar(x, rises, color='coral', edgecolor='black')
    ax.set_xticks(x)
    ax.set_xticklabels(labels_short, rotation=45, ha='right', fontsize=6)
    ax.set_ylabel('Rise Slope (N/m)', fontsize=10)
    ax.set_title('涓婂崌娈垫渶澶ф枩鐜囷紙鎭㈠杩囩▼锛?, fontsize=12, fontweight='bold')
    ax.grid(axis='y', alpha=0.3)
    ax.axhline(5, color='green', linestyle='--', linewidth=1, label='k_c = 5 N/m')
    ax.legend()
    
    # 宸︿笅锛氫笉瀵圭О姣?    ax = axes[1, 0]
    bars = ax.bar(x, asymms, color='mediumpurple', edgecolor='black')
    ax.set_xticks(x)
    ax.set_xticklabels(labels_short, rotation=45, ha='right', fontsize=6)
    ax.set_ylabel('Asymmetry Ratio (|rise|/|drop|)', fontsize=10)
    ax.set_title('涓嶅绉版瘮', fontsize=12, fontweight='bold')
    ax.grid(axis='y', alpha=0.3)
    
    # 鍙充笅锛氫笉瀵圭О姣?vs 浣嶇Щ
    ax = axes[1, 1]
    ax.scatter(disps, asymms, s=100, color='mediumpurple', edgecolors='black', zorder=5)
    for c in curves:
        ax.annotate(f"{c['disp']:.0f}nm", (c['disp'], abs(c['max_rise_slope']/c['max_drop_slope']) if c['max_drop_slope'] != 0 else 0),
                   fontsize=8, ha='center', va='bottom')
    ax.set_xlabel('Displacement (nm)', fontsize=10)
    ax.set_ylabel('Asymmetry Ratio', fontsize=10)
    ax.set_title('涓嶅绉版瘮 vs 浣嶇Щ', fontsize=12, fontweight='bold')
    ax.grid(True, alpha=0.3)
    
    fig.suptitle('妯″潡1锛氫笉瀵圭О鎬у畾閲忓垎鏋?, fontsize=16, fontweight='bold', y=0.98)
    pdf.savefig(fig, dpi=200)
    plt.close(fig)


def page_vdw_fitting(pdf, curves):
    fig, axes = plt.subplots(1, 2, figsize=(A4_W, A4_H))
    
    # 鎵惧埌鏈?vdW 鎷熷悎鐨勬洸绾?    fit_curves = [c for c in curves if c.get('vdw_fit')]
    
    for ax, c in zip(axes, fit_curves):
        fit = c['vdw_fit']
        drop_z = np.array(c['drop_z'])
        drop_f = np.array(c['drop_f'])
        
        # 閫夊彇鍚稿紩鍖?f < -2
        valid = drop_f < -2.0
        if np.sum(valid) < 5:
            continue
        
        vd_z = drop_z[valid]
        vd_f = np.abs(drop_f[valid])
        contact_z = c['contact_z_nm']
        d_est = contact_z - vd_z
        
        # 杩囨护
        mask = d_est > 0.5
        d_est = d_est[mask]
        vd_f = vd_f[mask]
        
        # log-log 鍥?        ax.scatter(d_est, vd_f, s=30, color='steelblue', edgecolors='black', zorder=5, label='Data')
        
        # 鎷熷悎绾?        if len(d_est) >= 3:
            log_d = np.log(d_est)
            log_f = np.log(vd_f)
            coeffs = np.polyfit(log_d, log_f, 1)
            d_fit = np.linspace(np.min(d_est), np.max(d_est), 100)
            f_fit = np.exp(coeffs[1]) * d_fit**coeffs[0]
            ax.plot(d_fit, f_fit, 'r--', linewidth=2, 
                    label=f"Fit: |F|={np.exp(coeffs[1]):.1f}*d^{coeffs[0]:.2f}\nR2={fit['R2']:.2f}")
        
        # 鐞嗚绾?        d_theory = np.linspace(0.5, np.max(d_est), 100)
        A = 4e-19  # J
        R = 8e-9  # m
        F_vdw = A * R / (6 * (d_theory * 1e-9)**2) * 1e9  # nN
        ax.plot(d_theory, F_vdw, 'g:', linewidth=2, label='Non-retarded vdW (A=4e-19J)')
        
        ax.set_xlabel('Distance d (nm)', fontsize=11)
        ax.set_ylabel('|Force| (nN)', fontsize=11)
        ax.set_title(f"{c['file'].replace('JJS-50nm-', '').replace(' - NanoScope Analysis.txt', '')}\n"
                     f"Snap-in 鍓?vdW 璺濈渚濊禆鎬?, fontsize=12, fontweight='bold')
        ax.set_xscale('log')
        ax.set_yscale('log')
        ax.legend(loc='best', fontsize=9)
        ax.grid(True, alpha=0.3, which='both')
    
    fig.suptitle('妯″潡2锛歋nap-in 鍓?vdW 璺濈渚濊禆鎬ф嫙鍚?, fontsize=16, fontweight='bold', y=0.98)
    pdf.savefig(fig, dpi=200)
    plt.close(fig)


def page_recovery_behavior(pdf, curves):
    fig, axes = plt.subplots(2, 2, figsize=(A4_W, A4_H))
    
    # 宸︿笂鍥撅細灞€閮ㄦ枩鐜囧垎甯冿紙閫?4 鏉′唬琛ㄦ€ф洸绾匡級
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
    ax.set_title('鎭㈠娈靛眬閮ㄦ枩鐜囧垎甯?, fontsize=12, fontweight='bold')
    ax.legend(loc='best', fontsize=9)
    ax.grid(True, alpha=0.3)
    
    # 鍙充笂鍥撅細plateau 妫€娴?    ax = axes[0, 1]
    labels = [c['file'].replace('JJS-50nm-', '').replace(' - NanoScope Analysis.txt', '') for c in curves]
    plateau_fracs = [c.get('recovery', {}).get('plateau_fraction', 0) for c in curves]
    x = np.arange(len(labels))
    ax.bar(x, plateau_fracs, color='lightcoral', edgecolor='black')
    ax.set_xticks(x)
    ax.set_xticklabels(labels, rotation=45, ha='right', fontsize=6)
    ax.set_ylabel('Plateau Fraction', fontsize=10)
    ax.set_title('姣涚粏妗?Plateau 妫€娴嬶紙|slope|<0.5 N/m锛?, fontsize=12, fontweight='bold')
    ax.grid(axis='y', alpha=0.3)
    
    # 宸︿笅鍥撅細鐞嗚姣涚粏鍔?vs 瀹炴祴
    ax = axes[1, 0]
    f_caps = [c['vdW_check']['F_capillary_theory_nN'] for c in curves]
    f_measured = [c['vdW_check']['F_measured_nN'] for c in curves]
    ax.scatter(f_caps, f_measured, s=100, color='steelblue', edgecolors='black', zorder=5)
    ax.plot([0, 10], [0, 10], 'k--', linewidth=1, label='1:1 line')
    ax.set_xlabel('Theoretical Capillary Force (nN)', fontsize=10)
    ax.set_ylabel('Measured Snap-in Force (nN)', fontsize=10)
    ax.set_title('瀹炴祴鍔?vs 鐞嗚姣涚粏鍔?, fontsize=12, fontweight='bold')
    ax.set_xlim(0, 10)
    ax.set_ylim(0, 160)
    ax.legend()
    ax.grid(True, alpha=0.3)
    
    # 鍙充笅鍥撅細鑳介噺鑰楁暎
    ax = axes[1, 1]
    disps = [c['disp'] for c in curves]
    energies = [c['energy_dissipated_nN_nm'] for c in curves]
    ax.scatter(disps, energies, s=100, c=[abs(c['snap_f']) for c in curves], 
               cmap='Reds', edgecolors='black', zorder=5)
    ax.set_xlabel('Displacement (nm)', fontsize=10)
    ax.set_ylabel('Energy Dissipated (nN路nm)', fontsize=10)
    ax.set_title('杩囨浮鍖鸿兘閲忚€楁暎', fontsize=12, fontweight='bold')
    ax.grid(True, alpha=0.3)
    
    fig.suptitle('妯″潡3锛氭仮澶嶈涓轰笌姣涚粏妗ュ垽鏂?, fontsize=16, fontweight='bold', y=0.98)
    pdf.savefig(fig, dpi=200)
    plt.close(fig)


def page_retarded_vdw(pdf, curves):
    fig = plt.figure(figsize=(A4_W, A4_H))
    fig.clf()
    
    fig.text(0.5, 0.95, '妯″潡4锛氬欢杩?vdW 妫€楠屼笌姘村垎瀛愰檺鍩熸晥搴?, 
             ha='center', va='top', fontsize=18, fontweight='bold')
    
    # 宸︿晶锛氱悊璁哄€?vs 瀹炴祴鍊煎姣旇〃
    fig.text(0.25, 0.88, '鐞嗚鍔?vs 瀹炴祴鍔涘姣?, 
             ha='center', va='top', fontsize=14, fontweight='bold', color='darkblue')
    
    table_text = (
        "鐞嗚妯″瀷棰勬祴锛坉0 = 0.3 nm锛夛細\n\n"
        "  闈炲欢杩?vdW (DMT):\n"
        "    F = A*R/(12*d0^2)\n"
        "    A = 4e-19 J (鍏稿瀷鑱氬悎鐗?\n"
        "    F_vdw = 2.96 nN\n\n"
        "  寤惰繜 vdW (Casimir-Polder):\n"
        "    F = pi^3*hbar*c*R/(360*d0^3)*eta\n"
        "    eta = 0.4 (鑱氬悎鐗?姘寲纭?\n"
        "    F_CP = 0.037 nN\n\n"
        "  姣涚粏鍔?(Kelvin鏂圭▼):\n"
        "    F = 4*pi*R*gamma\n"
        "    gamma = 72 mN/m (姘?\n"
        "    F_cap = 7.24 nN\n\n"
        "  vdW + 姣涚粏鍔涙€诲拰:\n"
        "    F_total = 10.2 nN\n\n"
        "瀹炴祴 Snap-in 鍔?\n"
        "  鏈€灏? 99.0 nN (1500nm-10nN)\n"
        "  鏈€澶? 150.6 nN (454nm-8.862nN)\n"
        "  鍧囧€? 120.7 nN\n\n"
        "缁撹:\n"
        "  瀹炴祴鍔?= 10-15 x 鐞嗚鎬诲拰\n"
        "  鍗曚竴鏈哄埗鏃犳硶瑙ｉ噴\n"
        "  蹇呴』寮曞叆鍑犱綍澧炲己鍥犲瓙 10-15x"
    )
    fig.text(0.03, 0.83, table_text, ha='left', va='top', fontsize=10,
             bbox=dict(boxstyle='round', facecolor='lightblue', alpha=0.3))
    
    # 鍙充晶锛氭按鍒嗗瓙闄愬煙鏁堝簲鍒嗘瀽
    fig.text(0.75, 0.88, '姘村垎瀛愰檺鍩熸晥搴斿垎鏋愶紙婀垮害 >60%锛?, 
             ha='center', va='top', fontsize=14, fontweight='bold', color='darkgreen')
    
    water_text = (
        "楂樻箍搴︿笅鐨勭撼绫抽棿闅欐按琛屼负锛歕n\n"
        "1. 鍚搁檮灞傚舰鎴?\n"
        "   鎺㈤拡鍜岃杽鑶滆〃闈㈠潎鍚搁檮姘村垎瀛愬眰\n"
        "   鍘氬害 ~0.3-1 nm锛堝彇鍐充簬婀垮害锛塡n"
        "   鍚搁檮灞傞檷浣庢湁鏁?Hamaker 甯告暟?\n"
        "   鈫?瀹炴祴琛ㄦ槑鏈夋晥 A 鍙嶈€屽澶?30-50x\n\n"
        "2. 姣涚粏妗ユ垚鏍?\n"
        "   鎺㈤拡鎺ヨ繎鏃讹紝姘村垎瀛愬湪闂撮殭涓嚌鑱歕n"
        "   褰㈡垚绾崇背绾ф恫妗ワ紙 neck radius < 10 nm锛塡n"
        "   浣嗘仮澶嶆鏈瀵熷埌鍔?plateau\n"
        "   鈫?姣涚粏妗ョ淮鎸佹椂闂存瀬鐭垨涓嶇ǔ瀹歕n\n"
        "3. 鍙楅檺姘寸殑绮樺害澧炲ぇ:\n"
        "   绾崇背闂撮殭 (< 5 nm) 涓按鐨勭矘搴n"
        "   鍙兘姣斾綋鐩搁珮 10-1000 鍊峔n"
        "   鍙兘瀵艰嚧鎺㈤拡鎺ヨ繎鏃剁殑鑳介噺鑰楁暎\n"
        "   杩囨浮鍖鸿兘閲忚€楁暎: 800-1800 nN路nm\n\n"
        "4. 缁煎悎鍥惧儚:\n"
        "   鈥?杩滆窛绂?(> 10 nm): 寤惰繜 vdW锛堝井寮憋級\n"
        "   鈥?涓窛绂?(1-10 nm): 闈炲欢杩?vdW + 姘村惛闄勫眰\n"
        "   鈥?杩戣窛绂?(< 1 nm): 姣涚粏妗ュ揩閫熸垚鏍竆n"
        "   鈥?鎺ヨЕ鍚? 绮樼潃鎺ヨЕ + 鎮噦寮规€ф仮澶峔n\n"
        "鍏抽敭闂:\n"
        "   涓轰粈涔堟湁鏁?A 澧炲ぇ 30-50 鍊?\n"
        "   鈫?钖勮啘灞€閮ㄦ洸鐜囧寮猴紙鍑犱綍鍥犲瓙锛塡n"
        "   鈫?澶氫綋鐩镐簰浣滅敤锛堟按鍒嗗瓙浠嬪锛塡n"
        "   鈫?钖勮啘鏈烘涓嶇ǔ瀹氭€э紙涓嬪嚬鏀惧ぇ鍚稿紩鍔涳級"
    )
    fig.text(0.53, 0.83, water_text, ha='left', va='top', fontsize=10,
             bbox=dict(boxstyle='round', facecolor='lightgreen', alpha=0.3))
    
    # 搴曢儴锛氬叧閿暟鍊?    fig.text(0.5, 0.08, 
             '鏍稿績鐭涚浘锛欴MT/Casimir 棰勬祴 ~3-10 nN锛屽疄娴?100-150 nN锛屽樊璺?10-50 鍊嶃€?
             ' 楂樻箍搴︿笅姘村垎瀛愰檺鍩熸晥搴斿拰钖勮啘鍑犱綍澧炲己鏄富瑕佸寮烘満鍒躲€?,
             ha='center', fontsize=11, color='darkred', fontweight='bold',
             bbox=dict(boxstyle='round', facecolor='yellow', alpha=0.3))
    
    pdf.savefig(fig, dpi=200)
    plt.close(fig)
