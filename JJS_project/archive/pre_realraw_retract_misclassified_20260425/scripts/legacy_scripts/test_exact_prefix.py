# %% [markdown]
r"""
## Raw Data Ingestion

The raw data are Bruker NanoScope Analysis `.txt` files exported from PeakForce QNM mode. Each file contains:
- **512 data points** (standard PeakForce acquisition)
- **2 Chinese header lines** describing experiment parameters
- **2 numeric columns**: piezo position $Z$ (nm) and cantilever deflection force $F$ (nN)
"""
