# Woodcock Tracking Test Models

This repository houses models used to test the correctness and performance of Woodcock (delta) tracking in OpenMC. We benchmark delta tracking against
surface tracking in OpenMC as a "reference" with several different cases:

1. A simple sphere of weapons-grade plutonium (Jezebel)
2. Fresh and depleted Sodium Fast Reactor (SFR) models
   - Pincell
   - Assembly
   - Partial core
3. Fresh and depleted Light Water Reactor (LWR) models
   - Pincell
   - Assembly
   - Partial core
4. A Helium Cooled Pebble Bed (HCPB) fusion breeder module
5. Fresh and depleted High Temperature Gas Reactor (HTGR) models
   - Compact
   - Assembly
   - Partial core

These problems are chosen to represent many different neutron spectra, nuclide compositions, and levels of geometric complexity.
