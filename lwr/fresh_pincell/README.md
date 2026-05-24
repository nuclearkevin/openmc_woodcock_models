# Testing Results

## 11th Gen Intel Core™ i7-11800H (16 threads)

Hash: 17fee0db263a492ea66758854e2c16ffd036b225

- Particles: 1,000
- Active batches: 1,000
- Inactive batches: 100

| QOI                     | Delta Tracking (old majorant) | Delta Tracking (manual majorant) | Surface Tracking     |
| ----------------------- | ----------------------------- | -------------------------------- | -------------------- |
| k-eff  (Collision)      | 1.14756 +/- 0.00118           | 1.14774 +/- 0.00120              | 1.14874 +/- 0.00114  |
| Leakage Fraction        | 0.01228 +/- 0.00014           | 0.01197 +/- 0.00013              | 0.01176 +/- 0.00013  |
| Active Tracking Rate    | 21224.3                       | 91015.3                          | 64222.8              |
| Inactive Tracking Rate  | 22681.8                       | 112619                           | 81047.3              |

- Particles: 10,000
- Active batches: 1,000
- Inactive batches: 100

| QOI                     | Delta Tracking (old majorant) | Delta Tracking (manual majorant) | Surface Tracking     |
| ----------------------- | ----------------------------- | -------------------------------- | -------------------- |
| k-eff  (Collision)      | 1.14910 +/- 0.00037           | 1.14861 +/- 0.00039              | 1.14810 +/- 0.00038  |
| Leakage Fraction        | 0.01205 +/- 0.00004           | 0.01212 +/- 0.00004              | 0.01217 +/- 0.00004  |
| Active Tracking Rate    | 21555.2                       | 106448                           | 69051.9              |
| Inactive Tracking Rate  | 23500.5                       | 156191                           | 88820.7              |

- Particles: 100,000
- Active batches: 1,000
- Inactive batches: 100

| QOI                     | Delta Tracking (old majorant) | Delta Tracking (manual majorant) | Surface Tracking     |
| ----------------------- | ----------------------------- | -------------------------------- | -------------------- |
| k-eff  (Collision)      | 1.14891 +/- 0.00012           | 1.14896 +/- 0.00012              | 1.14886 +/- 0.00012  |
| Leakage Fraction        | 0.01200 +/- 0.00001           | 0.01203 +/- 0.00001              | 0.01206 +/- 0.00001  |
| Active Tracking Rate    | 19810.1                       | 117132                           | 67889.2              |
| Inactive Tracking Rate  | 21721.2                       | 138045                           | 71035.3              |

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
