# Scheduling Execution Report

**Date Generated:** 2026-08-07 02:33:58

**Clingo Profile:** `parallel4` (arguments=['--parallel-mode=4'])

## Execution Summary
- Total runs: **136**
- VALID: **132**
- INVALID: **4**
- UNCHECKED: **0**
- Validation pass rate: **97.06%** (132/136)
- Optimization cost range (successful runs): **0 .. 13655**

## Week Configurations (Mid-Year Simulation)
- **Forced Closed (FC) Weeks (8 weeks):** Weeks 22 to 29
- **Preferably Closed (PC) Weeks (2 weeks):** Weeks 32 to 33

## Base Runs
| Year | TL | Run Type | Cost | Validation | Validation Summary |
|---|---|---|---|---|---|
| 2024 | 5 | Base_2024 | 11444 | VALID | CSV schedule adheres to all ASP rules! |
| 2024 | 15 | Base_2024 | 11630 | VALID | CSV schedule adheres to all ASP rules! |
| 2024 | 30 | Base_2024 | 11450 | VALID | CSV schedule adheres to all ASP rules! |
| 2024 | 60 | Base_2024 | 11384 | VALID | CSV schedule adheres to all ASP rules! |
| 2025 | 5 | Base_2025 | 11510 | VALID | CSV schedule adheres to all ASP rules! |
| 2025 | 15 | Base_2025 | 11516 | VALID | CSV schedule adheres to all ASP rules! |
| 2025 | 30 | Base_2025 | 11324 | VALID | CSV schedule adheres to all ASP rules! |
| 2025 | 60 | Base_2025 | 11450 | VALID | CSV schedule adheres to all ASP rules! |
| 2026 | 5 | Base_2026 | 12592 | VALID | CSV schedule adheres to all ASP rules! |
| 2026 | 15 | Base_2026 | 12112 | VALID | CSV schedule adheres to all ASP rules! |
| 2026 | 30 | Base_2026 | 12052 | VALID | CSV schedule adheres to all ASP rules! |
| 2026 | 60 | Base_2026 | 12046 | VALID | CSV schedule adheres to all ASP rules! |
| 2027 | 5 | Base_2027 | 11690 | VALID | CSV schedule adheres to all ASP rules! |
| 2027 | 15 | Base_2027 | 11570 | VALID | CSV schedule adheres to all ASP rules! |
| 2027 | 30 | Base_2027 | 11510 | VALID | CSV schedule adheres to all ASP rules! |
| 2027 | 60 | Base_2027 | 11444 | VALID | CSV schedule adheres to all ASP rules! |

## Reschedule Runs
| Year | TL | Run Type | Cost | Validation | Validation Summary |
|---|---|---|---|---|---|
| 2026 | 5 | Reschedule_2026 | 13655 | INVALID | Found 1 validation errors: -- [ERROR] Consecutive Year Festivity Violation: Pharmacy F6 covered festivity 'Festa della repubblica' in both years. |
| 2026 | 15 | Reschedule_2026 | 13560 | INVALID | Found 1 validation errors: -- [ERROR] Consecutive Year Festivity Violation: Pharmacy F6 covered festivity 'Festa della repubblica' in both years. |
| 2026 | 30 | Reschedule_2026 | 13158 | INVALID | Found 1 validation errors: -- [ERROR] Consecutive Year Festivity Violation: Pharmacy F6 covered festivity 'Festa della repubblica' in both years. |
| 2026 | 60 | Reschedule_2026 | 13013 | INVALID | Found 1 validation errors: -- [ERROR] Consecutive Year Festivity Violation: Pharmacy F6 covered festivity 'Festa della repubblica' in both years. |

## Corrected Runs
| Year | TL | Run Type | Cost | Validation | Validation Summary |
|---|---|---|---|---|---|
| 2026 | 5 | Corrected_2026 | 12316 | VALID | CSV schedule adheres to all ASP rules! |
| 2026 | 15 | Corrected_2026 | 12046 | VALID | CSV schedule adheres to all ASP rules! |
| 2026 | 30 | Corrected_2026 | 12052 | VALID | CSV schedule adheres to all ASP rules! |
| 2026 | 60 | Corrected_2026 | 12046 | VALID | CSV schedule adheres to all ASP rules! |

## Constraint Runs
| Year | TL | Run Type | Cost | Validation | Validation Summary | All PC Respected | PC Respect Rate | PC Target Count | PC Respected Count |
|---|---|---|---|---|---|---|---|---|---|
| 2026 | 5 | Constraint_Comb_1FC_1PC_C | 0 | VALID | CSV schedule adheres to all ASP rules! | True | 100.00% | 2 | 2 |
| 2026 | 5 | Constraint_Comb_1FC_1PC_M | 0 | VALID | CSV schedule adheres to all ASP rules! | True | 100.00% | 2 | 2 |
| 2026 | 5 | Constraint_Comb_1FC_2PC_C | 0 | VALID | CSV schedule adheres to all ASP rules! | True | 100.00% | 4 | 4 |
| 2026 | 5 | Constraint_Comb_1F_1M_1P_1PM | 0 | VALID | CSV schedule adheres to all ASP rules! | True | 100.00% | 4 | 4 |
| 2026 | 5 | Constraint_Comb_1F_1M_2P_1PM | 0 | VALID | CSV schedule adheres to all ASP rules! | True | 100.00% | 6 | 6 |
| 2026 | 5 | Constraint_Comb_2FC_1PC_C | 0 | VALID | CSV schedule adheres to all ASP rules! | True | 100.00% | 2 | 2 |
| 2026 | 5 | Constraint_Comb_2FC_2PC_C | 0 | VALID | CSV schedule adheres to all ASP rules! | True | 100.00% | 4 | 4 |
| 2026 | 5 | Constraint_Comb_2F_1M_1P_1PM | 0 | VALID | CSV schedule adheres to all ASP rules! | True | 100.00% | 4 | 4 |
| 2026 | 5 | Constraint_Comb_2F_1M_2P_1PM | 0 | VALID | CSV schedule adheres to all ASP rules! | True | 100.00% | 6 | 6 |
| 2026 | 5 | Constraint_FC_1C | 12868 | VALID | CSV schedule adheres to all ASP rules! | N/A | N/A | N/A | N/A |
| 2026 | 5 | Constraint_FC_1C_1M | 12052 | VALID | CSV schedule adheres to all ASP rules! | N/A | N/A | N/A | N/A |
| 2026 | 5 | Constraint_FC_1M | 12352 | VALID | CSV schedule adheres to all ASP rules! | N/A | N/A | N/A | N/A |
| 2026 | 5 | Constraint_FC_2C | 12292 | VALID | CSV schedule adheres to all ASP rules! | N/A | N/A | N/A | N/A |
| 2026 | 5 | Constraint_FC_2C_1M | 12244 | VALID | CSV schedule adheres to all ASP rules! | N/A | N/A | N/A | N/A |
| 2026 | 5 | Constraint_FC_2M | 12376 | VALID | CSV schedule adheres to all ASP rules! | N/A | N/A | N/A | N/A |
| 2026 | 5 | Constraint_FC_3C | 12382 | VALID | CSV schedule adheres to all ASP rules! | N/A | N/A | N/A | N/A |
| 2026 | 5 | Constraint_PC_1C | 0 | VALID | CSV schedule adheres to all ASP rules! | True | 100.00% | 2 | 2 |
| 2026 | 5 | Constraint_PC_1C_1M | 0 | VALID | CSV schedule adheres to all ASP rules! | True | 100.00% | 4 | 4 |
| 2026 | 5 | Constraint_PC_1C_2M | 0 | VALID | CSV schedule adheres to all ASP rules! | True | 100.00% | 6 | 6 |
| 2026 | 5 | Constraint_PC_1M | 0 | VALID | CSV schedule adheres to all ASP rules! | True | 100.00% | 2 | 2 |
| 2026 | 5 | Constraint_PC_2C | 0 | VALID | CSV schedule adheres to all ASP rules! | True | 100.00% | 4 | 4 |
| 2026 | 5 | Constraint_PC_2C_1M | 0 | VALID | CSV schedule adheres to all ASP rules! | True | 100.00% | 6 | 6 |
| 2026 | 5 | Constraint_PC_2C_2M | 0 | VALID | CSV schedule adheres to all ASP rules! | True | 100.00% | 8 | 8 |
| 2026 | 5 | Constraint_PC_2M | 0 | VALID | CSV schedule adheres to all ASP rules! | True | 100.00% | 4 | 4 |
| 2026 | 5 | Constraint_PC_3C | 0 | VALID | CSV schedule adheres to all ASP rules! | True | 100.00% | 6 | 6 |
| 2026 | 5 | Constraint_PC_3C_1M | 0 | VALID | CSV schedule adheres to all ASP rules! | True | 100.00% | 8 | 8 |
| 2026 | 5 | Constraint_PC_3C_2M | 0 | VALID | CSV schedule adheres to all ASP rules! | True | 100.00% | 10 | 10 |
| 2026 | 5 | Constraint_PC_4C | 0 | VALID | CSV schedule adheres to all ASP rules! | True | 100.00% | 8 | 8 |
| 2026 | 15 | Constraint_Comb_1FC_1PC_C | 0 | VALID | CSV schedule adheres to all ASP rules! | True | 100.00% | 2 | 2 |
| 2026 | 15 | Constraint_Comb_1FC_1PC_M | 0 | VALID | CSV schedule adheres to all ASP rules! | True | 100.00% | 2 | 2 |
| 2026 | 15 | Constraint_Comb_1FC_2PC_C | 0 | VALID | CSV schedule adheres to all ASP rules! | True | 100.00% | 4 | 4 |
| 2026 | 15 | Constraint_Comb_1F_1M_1P_1PM | 0 | VALID | CSV schedule adheres to all ASP rules! | True | 100.00% | 4 | 4 |
| 2026 | 15 | Constraint_Comb_1F_1M_2P_1PM | 0 | VALID | CSV schedule adheres to all ASP rules! | True | 100.00% | 6 | 6 |
| 2026 | 15 | Constraint_Comb_2FC_1PC_C | 0 | VALID | CSV schedule adheres to all ASP rules! | True | 100.00% | 2 | 2 |
| 2026 | 15 | Constraint_Comb_2FC_2PC_C | 0 | VALID | CSV schedule adheres to all ASP rules! | True | 100.00% | 4 | 4 |
| 2026 | 15 | Constraint_Comb_2F_1M_1P_1PM | 0 | VALID | CSV schedule adheres to all ASP rules! | True | 100.00% | 4 | 4 |
| 2026 | 15 | Constraint_Comb_2F_1M_2P_1PM | 0 | VALID | CSV schedule adheres to all ASP rules! | True | 100.00% | 6 | 6 |
| 2026 | 15 | Constraint_FC_1C | 12118 | VALID | CSV schedule adheres to all ASP rules! | N/A | N/A | N/A | N/A |
| 2026 | 15 | Constraint_FC_1C_1M | 12112 | VALID | CSV schedule adheres to all ASP rules! | N/A | N/A | N/A | N/A |
| 2026 | 15 | Constraint_FC_1M | 12052 | VALID | CSV schedule adheres to all ASP rules! | N/A | N/A | N/A | N/A |
| 2026 | 15 | Constraint_FC_2C | 12178 | VALID | CSV schedule adheres to all ASP rules! | N/A | N/A | N/A | N/A |
| 2026 | 15 | Constraint_FC_2C_1M | 12172 | VALID | CSV schedule adheres to all ASP rules! | N/A | N/A | N/A | N/A |
| 2026 | 15 | Constraint_FC_2M | 12178 | VALID | CSV schedule adheres to all ASP rules! | N/A | N/A | N/A | N/A |
| 2026 | 15 | Constraint_FC_3C | 11986 | VALID | CSV schedule adheres to all ASP rules! | N/A | N/A | N/A | N/A |
| 2026 | 15 | Constraint_PC_1C | 0 | VALID | CSV schedule adheres to all ASP rules! | True | 100.00% | 2 | 2 |
| 2026 | 15 | Constraint_PC_1C_1M | 0 | VALID | CSV schedule adheres to all ASP rules! | True | 100.00% | 4 | 4 |
| 2026 | 15 | Constraint_PC_1C_2M | 0 | VALID | CSV schedule adheres to all ASP rules! | True | 100.00% | 6 | 6 |
| 2026 | 15 | Constraint_PC_1M | 0 | VALID | CSV schedule adheres to all ASP rules! | True | 100.00% | 2 | 2 |
| 2026 | 15 | Constraint_PC_2C | 0 | VALID | CSV schedule adheres to all ASP rules! | True | 100.00% | 4 | 4 |
| 2026 | 15 | Constraint_PC_2C_1M | 0 | VALID | CSV schedule adheres to all ASP rules! | True | 100.00% | 6 | 6 |
| 2026 | 15 | Constraint_PC_2C_2M | 0 | VALID | CSV schedule adheres to all ASP rules! | True | 100.00% | 8 | 8 |
| 2026 | 15 | Constraint_PC_2M | 0 | VALID | CSV schedule adheres to all ASP rules! | True | 100.00% | 4 | 4 |
| 2026 | 15 | Constraint_PC_3C | 0 | VALID | CSV schedule adheres to all ASP rules! | True | 100.00% | 6 | 6 |
| 2026 | 15 | Constraint_PC_3C_1M | 0 | VALID | CSV schedule adheres to all ASP rules! | True | 100.00% | 8 | 8 |
| 2026 | 15 | Constraint_PC_3C_2M | 0 | VALID | CSV schedule adheres to all ASP rules! | True | 100.00% | 10 | 10 |
| 2026 | 15 | Constraint_PC_4C | 0 | VALID | CSV schedule adheres to all ASP rules! | True | 100.00% | 8 | 8 |
| 2026 | 30 | Constraint_Comb_1FC_1PC_C | 0 | VALID | CSV schedule adheres to all ASP rules! | True | 100.00% | 2 | 2 |
| 2026 | 30 | Constraint_Comb_1FC_1PC_M | 0 | VALID | CSV schedule adheres to all ASP rules! | True | 100.00% | 2 | 2 |
| 2026 | 30 | Constraint_Comb_1FC_2PC_C | 0 | VALID | CSV schedule adheres to all ASP rules! | True | 100.00% | 4 | 4 |
| 2026 | 30 | Constraint_Comb_1F_1M_1P_1PM | 0 | VALID | CSV schedule adheres to all ASP rules! | True | 100.00% | 4 | 4 |
| 2026 | 30 | Constraint_Comb_1F_1M_2P_1PM | 0 | VALID | CSV schedule adheres to all ASP rules! | True | 100.00% | 6 | 6 |
| 2026 | 30 | Constraint_Comb_2FC_1PC_C | 0 | VALID | CSV schedule adheres to all ASP rules! | True | 100.00% | 2 | 2 |
| 2026 | 30 | Constraint_Comb_2FC_2PC_C | 0 | VALID | CSV schedule adheres to all ASP rules! | True | 100.00% | 4 | 4 |
| 2026 | 30 | Constraint_Comb_2F_1M_1P_1PM | 0 | VALID | CSV schedule adheres to all ASP rules! | True | 100.00% | 4 | 4 |
| 2026 | 30 | Constraint_Comb_2F_1M_2P_1PM | 0 | VALID | CSV schedule adheres to all ASP rules! | True | 100.00% | 6 | 6 |
| 2026 | 30 | Constraint_FC_1C | 12112 | VALID | CSV schedule adheres to all ASP rules! | N/A | N/A | N/A | N/A |
| 2026 | 30 | Constraint_FC_1C_1M | 12118 | VALID | CSV schedule adheres to all ASP rules! | N/A | N/A | N/A | N/A |
| 2026 | 30 | Constraint_FC_1M | 12052 | VALID | CSV schedule adheres to all ASP rules! | N/A | N/A | N/A | N/A |
| 2026 | 30 | Constraint_FC_2C | 12112 | VALID | CSV schedule adheres to all ASP rules! | N/A | N/A | N/A | N/A |
| 2026 | 30 | Constraint_FC_2C_1M | 11986 | VALID | CSV schedule adheres to all ASP rules! | N/A | N/A | N/A | N/A |
| 2026 | 30 | Constraint_FC_2M | 12106 | VALID | CSV schedule adheres to all ASP rules! | N/A | N/A | N/A | N/A |
| 2026 | 30 | Constraint_FC_3C | 12118 | VALID | CSV schedule adheres to all ASP rules! | N/A | N/A | N/A | N/A |
| 2026 | 30 | Constraint_PC_1C | 0 | VALID | CSV schedule adheres to all ASP rules! | True | 100.00% | 2 | 2 |
| 2026 | 30 | Constraint_PC_1C_1M | 0 | VALID | CSV schedule adheres to all ASP rules! | True | 100.00% | 4 | 4 |
| 2026 | 30 | Constraint_PC_1C_2M | 0 | VALID | CSV schedule adheres to all ASP rules! | True | 100.00% | 6 | 6 |
| 2026 | 30 | Constraint_PC_1M | 0 | VALID | CSV schedule adheres to all ASP rules! | True | 100.00% | 2 | 2 |
| 2026 | 30 | Constraint_PC_2C | 0 | VALID | CSV schedule adheres to all ASP rules! | True | 100.00% | 4 | 4 |
| 2026 | 30 | Constraint_PC_2C_1M | 0 | VALID | CSV schedule adheres to all ASP rules! | True | 100.00% | 6 | 6 |
| 2026 | 30 | Constraint_PC_2C_2M | 0 | VALID | CSV schedule adheres to all ASP rules! | True | 100.00% | 8 | 8 |
| 2026 | 30 | Constraint_PC_2M | 0 | VALID | CSV schedule adheres to all ASP rules! | True | 100.00% | 4 | 4 |
| 2026 | 30 | Constraint_PC_3C | 0 | VALID | CSV schedule adheres to all ASP rules! | True | 100.00% | 6 | 6 |
| 2026 | 30 | Constraint_PC_3C_1M | 0 | VALID | CSV schedule adheres to all ASP rules! | True | 100.00% | 8 | 8 |
| 2026 | 30 | Constraint_PC_3C_2M | 0 | VALID | CSV schedule adheres to all ASP rules! | True | 100.00% | 10 | 10 |
| 2026 | 30 | Constraint_PC_4C | 0 | VALID | CSV schedule adheres to all ASP rules! | True | 100.00% | 8 | 8 |
| 2026 | 60 | Constraint_Comb_1FC_1PC_C | 0 | VALID | CSV schedule adheres to all ASP rules! | True | 100.00% | 2 | 2 |
| 2026 | 60 | Constraint_Comb_1FC_1PC_M | 0 | VALID | CSV schedule adheres to all ASP rules! | True | 100.00% | 2 | 2 |
| 2026 | 60 | Constraint_Comb_1FC_2PC_C | 0 | VALID | CSV schedule adheres to all ASP rules! | True | 100.00% | 4 | 4 |
| 2026 | 60 | Constraint_Comb_1F_1M_1P_1PM | 0 | VALID | CSV schedule adheres to all ASP rules! | True | 100.00% | 4 | 4 |
| 2026 | 60 | Constraint_Comb_1F_1M_2P_1PM | 0 | VALID | CSV schedule adheres to all ASP rules! | True | 100.00% | 6 | 6 |
| 2026 | 60 | Constraint_Comb_2FC_1PC_C | 0 | VALID | CSV schedule adheres to all ASP rules! | True | 100.00% | 2 | 2 |
| 2026 | 60 | Constraint_Comb_2FC_2PC_C | 0 | VALID | CSV schedule adheres to all ASP rules! | True | 100.00% | 4 | 4 |
| 2026 | 60 | Constraint_Comb_2F_1M_1P_1PM | 0 | VALID | CSV schedule adheres to all ASP rules! | True | 100.00% | 4 | 4 |
| 2026 | 60 | Constraint_Comb_2F_1M_2P_1PM | 0 | VALID | CSV schedule adheres to all ASP rules! | True | 100.00% | 6 | 6 |
| 2026 | 60 | Constraint_FC_1C | 11986 | VALID | CSV schedule adheres to all ASP rules! | N/A | N/A | N/A | N/A |
| 2026 | 60 | Constraint_FC_1C_1M | 12052 | VALID | CSV schedule adheres to all ASP rules! | N/A | N/A | N/A | N/A |
| 2026 | 60 | Constraint_FC_1M | 12052 | VALID | CSV schedule adheres to all ASP rules! | N/A | N/A | N/A | N/A |
| 2026 | 60 | Constraint_FC_2C | 11986 | VALID | CSV schedule adheres to all ASP rules! | N/A | N/A | N/A | N/A |
| 2026 | 60 | Constraint_FC_2C_1M | 12052 | VALID | CSV schedule adheres to all ASP rules! | N/A | N/A | N/A | N/A |
| 2026 | 60 | Constraint_FC_2M | 12046 | VALID | CSV schedule adheres to all ASP rules! | N/A | N/A | N/A | N/A |
| 2026 | 60 | Constraint_FC_3C | 12052 | VALID | CSV schedule adheres to all ASP rules! | N/A | N/A | N/A | N/A |
| 2026 | 60 | Constraint_PC_1C | 0 | VALID | CSV schedule adheres to all ASP rules! | True | 100.00% | 2 | 2 |
| 2026 | 60 | Constraint_PC_1C_1M | 0 | VALID | CSV schedule adheres to all ASP rules! | True | 100.00% | 4 | 4 |
| 2026 | 60 | Constraint_PC_1C_2M | 0 | VALID | CSV schedule adheres to all ASP rules! | True | 100.00% | 6 | 6 |
| 2026 | 60 | Constraint_PC_1M | 0 | VALID | CSV schedule adheres to all ASP rules! | True | 100.00% | 2 | 2 |
| 2026 | 60 | Constraint_PC_2C | 0 | VALID | CSV schedule adheres to all ASP rules! | True | 100.00% | 4 | 4 |
| 2026 | 60 | Constraint_PC_2C_1M | 0 | VALID | CSV schedule adheres to all ASP rules! | True | 100.00% | 6 | 6 |
| 2026 | 60 | Constraint_PC_2C_2M | 0 | VALID | CSV schedule adheres to all ASP rules! | True | 100.00% | 8 | 8 |
| 2026 | 60 | Constraint_PC_2M | 0 | VALID | CSV schedule adheres to all ASP rules! | True | 100.00% | 4 | 4 |
| 2026 | 60 | Constraint_PC_3C | 0 | VALID | CSV schedule adheres to all ASP rules! | True | 100.00% | 6 | 6 |
| 2026 | 60 | Constraint_PC_3C_1M | 0 | VALID | CSV schedule adheres to all ASP rules! | True | 100.00% | 8 | 8 |
| 2026 | 60 | Constraint_PC_3C_2M | 0 | VALID | CSV schedule adheres to all ASP rules! | True | 100.00% | 10 | 10 |
| 2026 | 60 | Constraint_PC_4C | 0 | VALID | CSV schedule adheres to all ASP rules! | True | 100.00% | 8 | 8 |

## Constraint Scenario Definitions
| Scenario Name | Description | FC Pharmacies | PC Pharmacies |
|---|---|---|---|
| FC_1C | 1 FC Center (8w) | 1 | None |
| FC_2C | 2 FC Center (8w) | 1, 2 | None |
| FC_3C | 3 FC Center (8w) | 1, 2, 3 | None |
| FC_1M | 1 FC Marina (8w) | 7 | None |
| FC_2M | 2 FC Marina (8w) | 7, 8 | None |
| FC_1C_1M | 1 FC Center, 1 FC Marina (8w) | 1, 7 | None |
| FC_2C_1M | 2 FC Center, 1 FC Marina (8w) | 1, 2, 7 | None |
| PC_1C | 1 PC Center (2w) | None | 4 |
| PC_2C | 2 PC Center (2w) | None | 4, 5 |
| PC_3C | 3 PC Center (2w) | None | 4, 5, 6 |
| PC_4C | 4 PC Center (2w) | None | 1, 2, 3, 4 |
| PC_1M | 1 PC Marina (2w) | None | 9 |
| PC_2M | 2 PC Marina (2w) | None | 9, 10 |
| PC_1C_1M | 1 PC Center, 1 PC Marina (2w) | None | 4, 9 |
| PC_2C_1M | 2 PC Center, 1 PC Marina (2w) | None | 4, 5, 9 |
| PC_3C_1M | 3 PC Center, 1 PC Marina (2w) | None | 4, 5, 6, 9 |
| PC_1C_2M | 1 PC Center, 2 PC Marina (2w) | None | 4, 9, 10 |
| PC_2C_2M | 2 PC Center, 2 PC Marina (2w) | None | 4, 5, 9, 10 |
| PC_3C_2M | 3 PC Center, 2 PC Marina (2w) | None | 4, 5, 6, 9, 10 |
| Comb_1FC_1PC_C | 1 FC C + 1 PC C | 1 | 4 |
| Comb_2FC_1PC_C | 2 FC C + 1 PC C | 1, 2 | 4 |
| Comb_1FC_2PC_C | 1 FC C + 2 PC C | 1 | 4, 5 |
| Comb_2FC_2PC_C | 2 FC C + 2 PC C | 1, 2 | 4, 5 |
| Comb_1FC_1PC_M | 1 FC M + 1 PC M | 7 | 9 |
| Comb_1F_1M_1P_1PM | 1 FC C + 1 FC M + 1 PC C + 1 PC M | 1, 7 | 4, 9 |
| Comb_2F_1M_1P_1PM | 2 FC C + 1 FC M + 1 PC C + 1 PC M | 1, 2, 7 | 4, 9 |
| Comb_1F_1M_2P_1PM | 1 FC C + 1 FC M + 2 PC C + 1 PC M | 1, 7 | 4, 5, 9 |
| Comb_2F_1M_2P_1PM | 2 FC C + 1 FC M + 2 PC C + 1 PC M | 1, 2, 7 | 4, 5, 9 |
