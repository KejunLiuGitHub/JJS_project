"""Parser for Bruker PeakForce QNM raw binary force curve files."""
import struct, re, numpy as np
from pathlib import Path


def parse_bruker_force_curve(filepath):
    """Parse a Bruker PeakForce QNM force curve from raw binary format.

    Returns dict with trace (approach) and retrace (withdraw) curves
    in physical units (nm, nN).
    """
    with open(filepath, 'rb') as f:
        raw = f.read()

    header_end = raw.find(b'\\*File list end')
    header = raw[:header_end].decode('latin-1', errors='replace')

    # Extract calibrations
    sc_match = re.search(r'\\Spring Constant:\s*([\d.]+)', header)
    spring_constant = float(sc_match.group(1)) if sc_match else 80.0

    ds_match = re.search(r'\\@Sens\. DeflSens:\s*V\s*([\d.]+)\s*nm/V', header)
    defl_sens = float(ds_match.group(1)) if ds_match else 64.64787

    zs_match = re.search(r'\\@Sens\. Zsens:\s*V\s*([\d.]+)\s*nm/V', header)
    z_sens = float(zs_match.group(1)) if zs_match else 34.861

    # Parse data blocks via Ciao markers
    lines = header.split('\n')
    current_channel = None
    ciao_blocks = []

    for i, line in enumerate(lines):
        if '@4:Image Data:' in line:
            if 'ZSensor' in line:
                current_channel = 'ZSensor'
            elif 'DeflectionError' in line:
                current_channel = 'DeflectionError'
        if '*Ciao force image list' in line:
            block = {'channel': current_channel}
            for j in range(i + 1, min(i + 20, len(lines))):
                ll = lines[j]
                dm = re.search(r'Data offset:\s*(\d+)', ll)
                lm = re.search(r'Data length:\s*(\d+)', ll)
                bm = re.search(r'Bytes/pixel:\s*(\d+)', ll)
                if dm:
                    block['offset'] = int(dm.group(1))
                if lm:
                    block['length'] = int(lm.group(1))
                if bm:
                    block['bpp'] = int(bm.group(1))
                if ll.startswith('\\') and 'Ciao' not in ll and 'Data' not in ll and 'Bytes' not in ll:
                    break
            if 'offset' in block and 'length' in block:
                ciao_blocks.append(block)

    def _read_trace_retrace(block):
        start = block['offset']
        data = raw[start:start + block['length']]
        vals = np.frombuffer(data, dtype=np.int16).astype(np.float64)
        return vals[::2].copy(), vals[1::2].copy()

    # Select correct blocks
    z_block = None
    defl_block = None
    for cb in ciao_blocks:
        if cb.get('channel') == 'ZSensor' and z_block is None:
            z_block = cb
        elif cb.get('channel') == 'DeflectionError' and cb.get('bpp') == 4 and defl_block is None:
            defl_block = cb

    if z_block is None or defl_block is None:
        raise ValueError(f"Missing data blocks in {filepath}")

    z_trace, z_retrace = _read_trace_retrace(z_block)
    defl_trace_raw, defl_retrace_raw = _read_trace_retrace(defl_block)

    # Convert Z ADC → nm
    z_adc = z_trace.astype(np.float64)
    z_min, z_max = z_adc.min(), z_adc.max()

    zs_pos = header.find('@4:Image Data: S [ZSensor]')
    ramp_size_v = 28.68535
    if zs_pos > 0:
        zs_section = header[zs_pos:zs_pos + 2000]
        rs_m = re.search(
            r'Ramp Size:.*\([\d.]+\s*V/LSB\)\s*([\d.]+)\s*V',
            zs_section
        )
        if rs_m:
            ramp_size_v = float(rs_m.group(1))
    ramp_size_nm = ramp_size_v * z_sens

    z_nm = (z_adc - z_min) / (z_max - z_min) * ramp_size_nm

    # Retrace Z (may be all zeros; if so, use reversed trace)
    z_retrace_adc = z_retrace.astype(np.float64)
    if z_retrace_adc.max() <= 0:
        z_nm_retrace = z_nm[::-1].copy()
    else:
        z_nm_retrace = (z_retrace_adc - z_min) / (z_max - z_min) * ramp_size_nm

    # Convert deflection ADC → nN
    # DeflSens Z-scale: ±0.5 V maps to ±32768 int16 counts
    defl_z_scale_v = 0.5
    v_per_count = defl_z_scale_v / 32768.0

    baseline_trace = np.median(defl_trace_raw[:10])
    defl_v_trace = (defl_trace_raw - baseline_trace) * v_per_count
    defl_nm_trace = defl_v_trace * defl_sens
    force_nn_trace = defl_nm_trace * spring_constant

    baseline_retrace = np.median(defl_retrace_raw[:10])
    defl_v_retrace = (defl_retrace_raw - baseline_retrace) * v_per_count
    defl_nm_retrace = defl_v_retrace * defl_sens
    force_nn_retrace = defl_nm_retrace * spring_constant

    return {
        'filename': Path(filepath).name,
        'z_nm': z_nm,
        'force_nn': force_nn_trace,
        'z_nm_retract': z_nm_retrace,
        'force_retract_nn': force_nn_retrace,
        'spring_constant': spring_constant,
        'defl_sens': defl_sens,
        'z_sens': z_sens,
        'ramp_size_nm': ramp_size_nm,
    }
