# RealRaw Branch-Aware Scientific Reinterpretation

Generated from `results/realraw/pair_features.csv` and `results/realraw/curve_features.csv`.

## Executive Summary

The previous JJS narrative treated the large `~121 nN` negative force as an approach snap-in anomaly. The RealRaw branch separation changes the scientific interpretation. In the actual `extend` branch, JJS approach attraction is `17.3 nN` median with an IQR of `14.0` to `20.7 nN`. This is close to the classic RTESPA-150 `R=8 nm` estimate: `F_vdW = 3.0 nN`, `F_cap = 7.2 nN`, and `F_vdW + F_cap = 10.2 nN`.

The large force is instead a retract phenomenon: JJS pull-off is `115.9 nN` median with IQR `108.2` to `131.0 nN`. The median retract/extend force ratio is `7.0`. The robust physical picture is therefore water-bridge/contact hysteresis: the approach branch forms contact or a capillary bridge at a near-classical force scale, while the retract branch stretches and pins a confined water/adhesion junction until delayed rupture.

## Revised Physical Interpretation

### 1. van der Waals and capillary force scale

For the sharp RTESPA-150 probe (`R=8 nm`), the nominal sphere-plane estimates are:

- `F_vdW = AR/(12 d0^2) = 3.0 nN`
- `F_cap = 4 pi R gamma = 7.2 nN`
- `F_vdW + F_cap = 10.2 nN`

JJS extend median `17.3 nN` is only `1.69x` the nominal sum. It does not require a 40x Hamaker enhancement. If mapped onto vdW alone, the effective Hamaker constant is `2.33e-18 J`, about `5.8x` the nominal value; if mapped onto capillarity alone, the effective capillary radius is `19.1 nm`. These are diagnostic scales, not unique fitted microscopic parameters.

By contrast, mapping the retract median `115.9 nN` onto the same simple formulas gives `A_eff = 1.56e-17 J` or `R_cap,eff = 128.1 nm`, which is physically a pull-off/contact-line hysteresis signature rather than a pre-contact vdW fit.

### 2. Confined water and adhesion hysteresis

The RealRaw result supports a capillary-confined-water hysteresis model:

- approach attraction is moderate and near the classic vdW + capillary scale;
- after contact/bridge formation, the retract branch has much larger negative force;
- the pull-off/extend ratio is several-fold for JJS and many linker/PAA cases;
- the large negative force should be interpreted as bridge stretching, contact-line pinning, delayed rupture, and possible confined-water structuring.

The data are consistent with confined water contributing to high dissipation and strong adhesion, but they do not independently isolate a solvation-force term. A separate humidity/dry-N2/KPFM/probe-radius series would be needed to separate capillary, electrostatic, and solvation components.

### 3. Sample comparison

The `20260415` linker series has much weaker extend attraction, typically sub-nN to a few nN, while retract pull-off rises to several nN or tens of nN. PAA-containing samples rank higher in adhesion than PFPE-OH/NLS, especially `linker2-PAA`.

The `20260416` k80 series uses a much larger and stiffer DDESP-V2 probe (`R≈100 nm`, `k=89 N/m`). The nominal force scale is correspondingly larger: `F_vdW + F_cap ≈ 127.5 nN`. However, baseline QC flags are frequent in this dataset, so k80 should be treated as deep-indentation/tip-geometry evidence rather than clean pre-contact force fitting.

### 4. Film mechanics

JJS intrinsic Young's modulus, membrane tension, and stress cannot be reliably extracted from these snap/pull-off branches. The post-contact segment is too short and the indentation depth is too shallow. The old `N/m`-scale apparent tension and hundreds-MPa apparent stress should be reinterpreted as a coupled capillary-water-film apparent stiffness, not as intrinsic film pre-tension.

For membrane mechanics, use only curves with sufficient deep post-contact indentation and analyze them separately from adhesion. This is most plausible for selected 20260415/20260416 curves after QC, cantilever correction, and a model appropriate to the probe radius.

## Group Statistics

|     date | group            |   n_pairs |   extend_snap_median_nN |   retract_pull_off_median_nN |   pull_to_snap_ratio_median |   hysteresis_work_median_nN_nm |
|---------:|:-----------------|----------:|------------------------:|-----------------------------:|----------------------------:|-------------------------------:|
| 20260409 | JJS              |        11 |                   17.29 |                       115.92 |                        7.02 |                       -1616.55 |
| 20260415 | linker1-PFPE-OH  |        32 |                    0.28 |                         4.06 |                        3.13 |                         637.24 |
| 20260415 | linker1-nls      |         8 |                    0.49 |                         5.94 |                        8.07 |                         645.36 |
| 20260415 | linker1-paa      |         5 |                    2.43 |                        13.57 |                        7.87 |                        -173.72 |
| 20260415 | linker2-paa      |        24 |                    0.96 |                        16.06 |                       14.82 |                        1030.10 |
| 20260416 | k80-linker1-PFNA |        12 |                    8.64 |                       117.85 |                        4.08 |                     6062304.70 |
| 20260416 | k80-linker1-SDBS |        12 |                    4.00 |                       130.87 |                       14.43 |                     2539723.32 |
| 20260416 | k80-linker1-paa  |        17 |                   14.38 |                        59.88 |                        2.20 |                     5372994.68 |
| 20260416 | k80-linker2-paa  |         8 |                    7.55 |                         9.09 |                        1.19 |                       24892.78 |

## QC Context

|     date | branch   |   curves |   valid |   warnings | directions            |
|---------:|:---------|---------:|--------:|-----------:|:----------------------|
| 20260409 | extend   |       11 |      11 |          1 | {"inc": 11}           |
| 20260409 | retract  |       11 |      11 |          2 | {"dec": 10, "inc": 1} |
| 20260415 | extend   |       69 |      69 |         69 | {"inc": 69}           |
| 20260415 | retract  |       69 |      69 |         69 | {"dec": 69}           |
| 20260416 | extend   |       49 |      26 |         23 | {"inc": 49}           |
| 20260416 | retract  |       49 |      18 |         31 | {"dec": 49}           |
| 20260409 | pairs    |       11 |      11 |          2 | {"paired": 11}        |
| 20260415 | pairs    |       69 |      69 |         69 | {"paired": 69}        |
| 20260416 | pairs    |       49 |      49 |         31 | {"paired": 49}        |

## What Can and Cannot Be Extracted

| category                            | quantity                                          | evidence                                                           | interpretation                                                                              |
|:------------------------------------|:--------------------------------------------------|:-------------------------------------------------------------------|:--------------------------------------------------------------------------------------------|
| Can extract robustly                | Approach attraction scale                         | extend branch minimum force after branch-aware baseline correction | vdW + capillary + modest dynamic/interface enhancement                                      |
| Can extract robustly                | Pull-off adhesion                                 | retract branch minimum force                                       | water bridge/contact-line pinning/adhesion hysteresis                                       |
| Can extract robustly                | Hysteresis and sample ranking                     | paired extend/retract work and pull-off ratios                     | relative confined-water/adhesion strength across chemistries                                |
| Semi-quantitative                   | Effective capillary radius or Hamaker upper bound | force magnitude mapped onto simple sphere-plane models             | diagnostic scale only, not unique microscopic geometry                                      |
| Not reliable from JJS snap/pull-off | Intrinsic Young's modulus, tension, or stress     | too few post-contact points and shallow indentation                | old N/m-scale apparent tension is capillary-water-film coupling, not intrinsic film tension |
| Not independently separable         | Solvation force or true water bridge geometry     | no humidity, dry-N2, KPFM, or probe-radius control series          | confined water is a plausible mechanism, not a uniquely fitted component                    |

## Figures

- `extend_vs_retract_pull_off.pdf`: approach attraction versus retract adhesion.
- `extend_vs_theory.pdf`: extend force compared with classic vdW + capillary scale.
- `hysteresis_ratio_work.pdf`: retract/extend ratio and paired work difference.
- `adhesion_ranking.pdf`: sample-level adhesion ranking.
