# Deep Indentation Apparent Modulus Report

## Scope

This analysis excludes JJS, snap-in, pull-off, adhesion, and confined-water interpretation. It uses only stitched deep-indentation extend/loading curves from `20260415` and `20260416`.

The reported modulus is a model-dependent apparent Young's modulus for relative comparison, not an intrinsic material constant.

## Model

The loading branch is fitted as:

```text
F = k1 * delta + k3 * delta^3
E_app = k3 * a^2 / (q^3 * t)
q = 1 / (1.05 - 0.15 nu - 0.16 nu^2)
```

Defaults: pore diameter = 20 um, pore radius `a` = 10 um, `nu` = 0.30, main thickness `t` = 50 nm. The 80 nm column shows the thickness sensitivity; because `E_app` scales as `1/t`, the 80 nm value is 0.625x the 50 nm value.

## Main k80 Ranking

Within the same `20260416` DDESP-V2/k80 probe set, `k80-linker1-paa` has the highest median apparent modulus. Its median `E_app` is `55.1 MPa`, about `36.3x` the next strongest valid k80 group.

| group | N valid | E_app 50 nm MPa | E_app 80 nm MPa | high-k N/m | power n | fit R2 | QC |
| --- | --- | --- | --- | --- | --- | --- | --- |
| k80-linker1-paa | 11 | 55.1 | 34.4 | 1.01 | 1.16 | 0.994 | invalid_models=1|contains_stitched_slip|compare_within_k80_only |
| k80-linker1-PFNA | 6 | 1.52 | 0.948 | 0.276 | 1.15 | 0.972 | invalid_models=1|contains_stitched_slip|compare_within_k80_only |
| k80-linker1-SDBS | 3 | 0.463 | 0.289 | 0.161 | 1.19 | 0.976 | invalid_models=2|compare_within_k80_only |


## 20260415 Reference

The `20260415` RTESPA-150 data are kept as a same-workflow reference, but they should not be ranked directly against k80 because probe radius and force range differ.

| group | N valid | E_app 50 nm MPa | E_app 80 nm MPa | high-k N/m | power n | fit R2 | QC |
| --- | --- | --- | --- | --- | --- | --- | --- |
| linker2-paa | 15 | 1299 | 812 | 0.17 | 1.56 | 0.988 |  |
| linker1-paa | 0 | NA | NA | NA | NA | NA | low_N|invalid_models=1 |


## Interpretation

- Use the k80 ranking as the strongest surfactant comparison because probe, cantilever, and force range are internally consistent.
- `E_app`, `T_app`, and `sigma_app` are comparative quantities. Their absolute values depend on assumed film thickness, pore radius, boundary condition, and the stitched loading reconstruction.
- Groups with `low_N` or invalid model fits should be treated as screening-level evidence only.
