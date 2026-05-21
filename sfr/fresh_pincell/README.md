# Testing Results

## 11th Gen Intel Core™ i7-11800H (16 threads)

Hash: 42ce34d5b0233b7503fd38890f62729a2aaa844e

- Particles: 1,000
- Active batches: 1,000
- Inactive batches: 100

| QOI                     | Delta Tracking       | Surface Tracking     |
| ----------------------- | -------------------- | -------------------- |
| k-eff  (Collision)      | 0.98686 +/- 0.00078  | 0.98964 +/- 0.00082  |
| Leakage Fraction        | 0.13896 +/- 0.00037  | 0.14056 +/- 0.00037  |
| Active Tracking Rate    | 71907.3              | 31811.6              |
| Inactive Tracking Rate  | 82926.3              | 39973.9              |

- Particles: 10,000
- Active batches: 1,000
- Inactive batches: 100

| QOI                     | Delta Tracking       | Surface Tracking     |
| ----------------------- | -------------------- | -------------------- |
| k-eff  (Collision)      | 0.98602 +/- 0.00025  | 0.98811 +/- 0.00026  |
| Leakage Fraction        | 0.13937 +/- 0.00011  | 0.14028 +/- 0.00012  |
| Active Tracking Rate    | 67741.6              | 32679                |
| Inactive Tracking Rate  | 90030.2              | 42711.1              |

- Particles: 100,000
- Active batches: 1,000
- Inactive batches: 100

| QOI                     | Delta Tracking       | Surface Tracking     |
| ----------------------- | -------------------- | -------------------- |
| k-eff  (Collision)      | 0.98578 +/- 0.00008  | 0.98839 +/- 0.00008  |
| Leakage Fraction        | 0.13925 +/- 0.00004  | 0.14026 +/- 0.00004  |
| Active Tracking Rate    | 72843.5              | 34555.7              |
| Inactive Tracking Rate  | 83335.3              | 38022.8              |

### Flux Spectra

<p align="center">
  <img src="figures/spectrum_comp_p1000_ab1000_ib100.png" width="300" />
  <img src="figures/spectrum_comp_p10000_ab1000_ib100.png" width="300" />
  <img src="figures/spectrum_comp_p100000_ab1000_ib100.png" width="300" />
</p>
<p align="center">
Spectrum comparisons for 1000, 10000, and 100000 particles per batch (left to right).
</p>

### Flux Distributions

<p align="center">
  <img src="figures/flux_dis_p1000_ab1000_ib100.png" />
</p>
<p align="center">
1000 particles per batch.
</p>
<p align="center">
  <img src="figures/flux_dis_p10000_ab1000_ib100.png" />
</p>
<p align="center">
10000 particles per batch.
</p>
<p align="center">
  <img src="figures/flux_dis_p100000_ab1000_ib100.png" />
</p>
<p align="center">
100000 particles per batch.
</p>

### Flux Statistical Error Distributions

<p align="center">
  <img src="figures/flux_rel_dis_p1000_ab1000_ib100.png" />
</p>
<p align="center">
1000 particles per batch.
</p>
<p align="center">
  <img src="figures/flux_rel_dis_p10000_ab1000_ib100.png" />
</p>
<p align="center">
10000 particles per batch.
</p>
<p align="center">
  <img src="figures/flux_rel_dis_p100000_ab1000_ib100.png" />
</p>
<p align="center">
100000 particles per batch.
</p>

### Flux Relative Error Distributions

<p align="center">
  <img src="figures/flux_spatial_comp_p1000_ab1000_ib100.png" width="300" />
  <img src="figures/flux_spatial_comp_p10000_ab1000_ib100.png" width="300" />
  <img src="figures/flux_spatial_comp_p100000_ab1000_ib100.png" width="300" />
</p>
<p align="center">
1000, 10000, and 100000 particles per batch (left to right).
</p>

### Total Reaction Rate Distributions

<p align="center">
  <img src="figures/total_dis_p1000_ab1000_ib100.png" />
</p>
<p align="center">
1000 particles per batch.
</p>
<p align="center">
  <img src="figures/total_dis_p10000_ab1000_ib100.png" />
</p>
<p align="center">
10000 particles per batch.
</p>
<p align="center">
  <img src="figures/total_dis_p100000_ab1000_ib100.png" />
</p>
<p align="center">
100000 particles per batch.
</p>

### Total Reaction Rate Statistical Error Distributions

<p align="center">
  <img src="figures/total_rel_dis_p1000_ab1000_ib100.png" />
</p>
<p align="center">
1000 particles per batch.
</p>
<p align="center">
  <img src="figures/total_rel_dis_p10000_ab1000_ib100.png" />
</p>
<p align="center">
10000 particles per batch.
</p>
<p align="center">
  <img src="figures/total_rel_dis_p100000_ab1000_ib100.png" />
</p>
<p align="center">
100000 particles per batch.
</p>

### Total Reaction Rate Relative Error Distributions

<p align="center">
  <img src="figures/total_spatial_comp_p1000_ab1000_ib100.png" width="300" />
  <img src="figures/total_spatial_comp_p10000_ab1000_ib100.png" width="300" />
  <img src="figures/total_spatial_comp_p100000_ab1000_ib100.png" width="300" />
</p>
<p align="center">
1000, 10000, and 100000 particles per batch (left to right).
</p>
