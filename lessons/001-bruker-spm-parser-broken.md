# Lesson 001 — Bruker SPM 二进制解析器三处致命错误

## 问题

`1umSquare/bruker_parser.py` 解析 Bruker PeakForce QNM 原始二进制（.spm）文件时，输出与 NanoScope Analysis 导出的 txt 文件严重不一致。用 `comparison/` 文件夹中同一测量的三种格式对比：

| 格式 | Z 范围 | F max | F min | 点数 |
|------|--------|-------|-------|------|
| Binary (parser trace) | 987→11 nm ↘ | 3019 nN | **-2150 nN** ✗ | 512 |
| TXT extend (真值) | 0→996 nm ↗ | 7614 nN | 679 nN | 256 |
| TXT retract (真值) | 0→996 nm ↗ | 7709 nN | 602 nN | 256 |

## 根因：三处耦合错误

### 1. trace/retrace 互换

`_read_trace_retrace()` 用 `vals[::2]` / `vals[1::2]` 拆分奇偶，假设偶数下标=trace(approach)、奇数下标=retrace(withdraw)。但实际 binary 文件中数据存储顺序是 retrace 在前、trace 在后。

证据：parser "trace" 的 Z 从 987→11 nm（递减 = 探针缩回），而 txt extend（真·approach）Z 从 0→996 nm（递增）。

### 2. 力值校准错误（小了 ~2.5×）

Parser 对 bpp=4（int32）的 DeflectionError 块使用了 int16 的 ADC 转换系数：
```python
defl_z_scale_v = 0.5
v_per_count = defl_z_scale_v / 32768.0  # ← 这是 int16 的公式，int32 不对
```
int32 的 ADC 范围是 ±10V（不是 ±0.5V），且满量程对应 ±2^31 = ±2147483648 counts。

### 3. 基线减法用错数据段

```python
baseline_trace = np.median(defl_trace_raw[:10])  # ← 前 10 个点不是 far-field
```
前 10 个点可能已在接触区（探针受力），减完后产生假负力（-2150 nN）。

## 教训

1. **永远用 NanoScope Analysis 导出的 txt 做权威数据源**，不要自己解析 binary。NanoScope 的导出已经做了基线校正、单位转换、branch 分离，这些都是 parser 容易出错的地方。
2. **解析 binary 格式前，先用同一测量的 txt 导出做对照**。`comparison/` 文件夹里有同一文件的三版格式，这种对照应该在做 parser 的第一天就做。
3. **Parser 能读出数据，但读出的值不能用于科学分析**。数据块定位、Z/Deflection 通道识别是能工作的——读出来的值数量级也合理（Z ~1000nm, F ~3000nN）。问题全在校准层面（trace/retrace 顺序、ADC 系数、基线减法），不是读不出数据。如果只是想"从 binary 里看到点什么"，parser 能做到；但别用于拟合模量或发论文。
4. **要修这三个错基本等于逆向工程重写一遍**。Bruker binary 格式没有公开文档，`*Ciao force image list` 的 bpp=2 vs bpp=4 变体、trace/retrace 存储顺序、ADC 转换系数都是靠猜的。而 NanoScope Analysis 导出 txt 时已经做了所有这些校准（基线校正、单位转换、branch 分离），直接用 txt 就行。
5. **不要修这个 parser**。三个错误互相耦合（trace/retrace 顺序 + ADC 系数 + 基线减法），修好一个另外两个还在。直接放弃，用 txt 导出 + JJS pipeline（`compute_apparent_modulus.py`）。
