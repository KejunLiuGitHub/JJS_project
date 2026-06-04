import sys, numpy as np
sys.path.insert(0, 'scripts')
from parser import AFMForceCurve, load_all_curves

curves = load_all_curves('.')
print("=== JJS repulsive segment analysis ===\n")
for rel, c in sorted(curves.items()):
    if 'JJS' not in rel:
        continue
    z = np.array(c.z)
    f = np.array(c.force)
    if c.z_unit in ('um','μm'):
        z = z * 1000
    # baseline correction (same logic as extract_features.py)
    mask = (z >= 0) & (z <= 100)
    count = int(np.sum(mask))
    if count >= 5:
        coeffs = np.polyfit(z[mask], f[mask], 1)
        a, b = coeffs[0], coeffs[1]
        f_corr = f - (a * z + b)
    elif count >= 3:
        f_corr = f - np.mean(f[mask])
    else:
        f_corr = f
    
    # repulsive segment
    rep = f_corr > 0
    rep_z = z[rep]
    rep_f = f_corr[rep]
    
    # snap-in point
    snap_idx = np.argmin(f_corr)
    snap_z = z[snap_idx]
    
    # find contact point (first F>0 after snap-in)
    contact_candidates = np.where((z > snap_z) & (f_corr > 0))[0]
    if len(contact_candidates) > 0:
        contact_z = z[contact_candidates[0]]
    else:
        contact_z = snap_z
    
    print(f"{rel.split('\\')[-1]}")
    print(f"  snap_in_z={snap_z:.1f} nm, contact_z={contact_z:.1f} nm")
    print(f"  repulsive points: {np.sum(rep)}")
    print(f"  repulsive F range: {rep_f.min():.2f} to {rep_f.max():.2f} nN")
    print(f"  repulsive z range: {rep_z.min():.1f} to {rep_z.max():.1f} nm")
    if len(rep_f) >= 3:
        # slope of F vs z in repulsive region
        slope = np.polyfit(rep_z, rep_f, 1)[0]
        print(f"  repulsive slope dF/dz: {slope:.4f} nN/nm")
    print()
