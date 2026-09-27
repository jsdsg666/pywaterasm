# Unified symbol mapping of the eight pywaterasm models

Sources: input/ASM1_Class.inwt, ASM2d_Class.inwt, ASM2d_IC.inwt, ASM3_Class.inwt
(WaterTAP activated_sludge family) and input/ASM1_2N.inwt, ASM3_N2O.inwt,
ASM2d_EBPR.inwt, ASM2d_3.inwt (langgraph-en family, modelcomplex names: SimplifiedCODN / CompleteNRN2O / EBPRCODN / IntegratedNPR).

Three columns, identical to the `#note# 6. Mapping` section of every .inwt:
name in code | name in chemical | name in regular expression (symbol_sub_<sub>_sep_<sub>_sup_<sup>).

Note: `S_NO` is used by ASM1 for nitrate + nitrite nitrogen and by the langgraph-en
models for nitric oxide (two different quantities sharing one symbol).

## Components

| code    | name in chemical                               | regular expression | models |
|---------|------------------------------------------------|----------------------|------------------------------------------------------------|
| S_A     | Fermentation products, considered acetate      | S_sub_A | ASM2d, ASM2d_IC |
| S_ALK   | Alkalinity                                     | S_sub_ALK | ASM1, ASM2d, ASM3, ASM1_2N, ASM3_N2O, ASM2d_EBPR, ASM2d_3 |
| S_F     | Fermentable, readily biodegradable substrates  | S_sub_F | ASM2d, ASM2d_IC |
| S_I     | Inert soluble organic material                 | S_sub_I | ASM1, ASM2d, ASM2d_IC, ASM3, ASM1_2N, ASM3_N2O, ASM2d_EBPR, ASM2d_3 |
| S_IC    | Inorganic carbon                               | S_sub_IC | ASM2d_IC |
| S_K     | Potassium                                      | S_sub_K | ASM2d_IC |
| S_Mg    | Magnesium                                      | S_sub_Mg | ASM2d_IC |
| S_N2    | Dinitrogen                                     | S_sub_N_sub_2 | ASM2d, ASM2d_IC, ASM3, ASM1_2N, ASM3_N2O, ASM2d_EBPR, ASM2d_3 |
| S_N2O   | Nitrous oxide nitrogen                         | S_sub_N_sub_2O | ASM3_N2O, ASM2d_3 |
| S_ND    | Soluble biodegradable organic nitrogen         | S_sub_ND | ASM1 |
| S_NH    | Ammonium nitrogen                              | S_sub_NH | ASM1 |
| S_NH2OH | Hydroxylamine nitrogen                         | S_sub_NH_sub_2OH | ASM3_N2O, ASM2d_3 |
| S_NH4   | Ammonium plus ammonia nitrogen                 | S_sub_NH_sub_4 | ASM2d, ASM2d_IC, ASM3, ASM1_2N, ASM3_N2O, ASM2d_EBPR, ASM2d_3 |
| S_NO    | Nitrate and nitrite nitrogen                   | S_sub_NO | ASM1 |
| S_NO    | Nitric oxide nitrogen                          | S_sub_NO | ASM3_N2O, ASM2d_3 |
| S_NO2   | Nitrite nitrogen                               | S_sub_NO_sub_2 | ASM1_2N, ASM3_N2O, ASM2d_EBPR, ASM2d_3 |
| S_NO3   | Nitrate nitrogen                               | S_sub_NO_sub_3 | ASM2d, ASM2d_IC, ASM1_2N, ASM3_N2O, ASM2d_EBPR, ASM2d_3 |
| S_NOX   | Nitrate and nitrite nitrogen                   | S_sub_NOX | ASM3 |
| S_O     | Dissolved oxygen                               | S_sub_O | ASM1, ASM3 |
| S_O2    | Dissolved oxygen                               | S_sub_O_sub_2 | ASM2d, ASM2d_IC, ASM1_2N, ASM3_N2O, ASM2d_EBPR, ASM2d_3 |
| S_PO4   | Inorganic soluble phosphorus (ortho-phosphate) | S_sub_PO_sub_4 | ASM2d, ASM2d_IC, ASM2d_EBPR, ASM2d_3 |
| S_S     | Readily biodegradable substrate                | S_sub_S | ASM1, ASM3, ASM1_2N, ASM3_N2O, ASM2d_EBPR, ASM2d_3 |
| X_A     | Autotrophic (nitrifying) biomass               | X_sub_A | ASM3 |
| X_AOB   | Ammonia-oxidizing organisms                    | X_sub_AOB | ASM1_2N, ASM3_N2O, ASM2d_EBPR, ASM2d_3 |
| X_AUT   | Autotrophic nitrifying organisms               | X_sub_AUT | ASM2d, ASM2d_IC |
| X_BA    | Active autotrophic biomass                     | X_sub_BA | ASM1 |
| X_BH    | Active heterotrophic biomass                   | X_sub_BH | ASM1 |
| X_H     | Heterotrophic organisms                        | X_sub_H | ASM2d, ASM2d_IC, ASM3, ASM1_2N, ASM3_N2O, ASM2d_EBPR, ASM2d_3 |
| X_I     | Inert particulate organic material             | X_sub_I | ASM1, ASM2d, ASM2d_IC, ASM3, ASM1_2N, ASM3_N2O, ASM2d_EBPR, ASM2d_3 |
| X_MeOH  | Metal-hydroxides                               | X_sub_MeOH | ASM2d |
| X_MeP   | Metal-phosphate                                | X_sub_MeP | ASM2d |
| X_ND    | Particulate biodegradable organic N            | X_sub_ND | ASM1 |
| X_NOB   | Nitrite-oxidizing organisms                    | X_sub_NOB | ASM1_2N, ASM3_N2O, ASM2d_EBPR, ASM2d_3 |
| X_P     | Particulate products from biomass decay        | X_sub_P | ASM1 |
| X_PAO   | Phosphate-accumulating organisms               | X_sub_PAO | ASM2d, ASM2d_IC, ASM2d_EBPR, ASM2d_3 |
| X_PHA   | Cell-internal storage product of PAOs          | X_sub_PHA | ASM2d, ASM2d_IC, ASM2d_EBPR, ASM2d_3 |
| X_PP    | Poly-phosphate                                 | X_sub_PP | ASM2d, ASM2d_IC, ASM2d_EBPR, ASM2d_3 |
| X_S     | Slowly biodegradable substrates                | X_sub_S | ASM1, ASM2d, ASM2d_IC, ASM3, ASM1_2N, ASM3_N2O, ASM2d_EBPR, ASM2d_3 |
| X_STO   | Organics stored by heterotrophs                | X_sub_STO | ASM3, ASM3_N2O, ASM2d_3 |
| X_TSS   | Total suspended solids                         | X_sub_TSS | ASM3 |

## Parameters

| code           | name in chemical                                                                   | regular expression | models |
|----------------|------------------------------------------------------------------------------------|----------------------|------------------------------------------------------------|
| KA_NH4         | Half-saturation coefficient for ammonium, autotrophs (mg N/L)                      | KA_sub_NH_sub_4 | ASM2d_IC |
| KA_NO3         | Half-saturation coefficient for nitrate, autotrophs (mg N/L)                       | KA_sub_NO_sub_3 | ASM2d_IC |
| KA_O2          | Half-saturation coefficient for oxygen, autotrophs (mg O2/L)                       | KA_sub_O_sub_2 | ASM2d_IC |
| KA_PO4         | Half-saturation coefficient for phosphate, autotrophs (mg P/L)                     | KA_sub_PO_sub_4 | ASM2d_IC |
| KH_A           | Half-saturation coefficient for S_A, heterotrophs (mg COD/L)                       | KH_sub_A | ASM2d_IC |
| KH_NH4         | Half-saturation coefficient for ammonium, heterotrophs (mg N/L)                    | KH_sub_NH_sub_4 | ASM2d_IC |
| KH_NO3         | Half-saturation coefficient for nitrate, heterotrophs (mg N/L)                     | KH_sub_NO_sub_3 | ASM2d_IC |
| KH_O2          | Half-saturation coefficient for oxygen, heterotrophs (mg O2/L)                     | KH_sub_O_sub_2 | ASM2d_IC |
| KH_PO4         | Half-saturation coefficient for phosphate, heterotrophs (mg P/L)                   | KH_sub_PO_sub_4 | ASM2d_IC |
| KI_PP          | Inhibition coefficient for additional poly-P storage (g PP / g PAO)                | KI_sub_PP | ASM2d_IC |
| KL_NO3         | Half-saturation coefficient for nitrate in hydrolysis (mg N/L)                     | KL_sub_NO_sub_3 | ASM2d_IC |
| KL_O2          | Half-saturation coefficient for oxygen in hydrolysis (mg O2/L)                     | KL_sub_O_sub_2 | ASM2d_IC |
| KL_X           | Hydrolysis saturation coefficient (g X_S / g X_H)                                  | KL_sub_X | ASM2d_IC |
| KP_A           | Half-saturation coefficient for S_A in PHA storage (mg COD/L)                      | KP_sub_A | ASM2d_IC |
| KP_NH4         | Half-saturation coefficient for ammonium, PAO (mg N/L)                             | KP_sub_NH_sub_4 | ASM2d_IC |
| KP_NO3         | Half-saturation coefficient for nitrate, PAO (mg N/L)                              | KP_sub_NO_sub_3 | ASM2d_IC |
| KP_O2          | Half-saturation coefficient for oxygen, PAO (mg O2/L)                              | KP_sub_O_sub_2 | ASM2d_IC |
| KP_P           | Half-saturation coefficient for phosphate in PP storage (mg P/L)                   | KP_sub_P | ASM2d_IC |
| KP_PHA         | Half-saturation coefficient for PHA in PP storage and PAO growth (g PHA / g PAO)   | KP_sub_PHA | ASM2d_IC |
| KP_PO4         | Half-saturation coefficient for phosphate, PAO (mg P/L)                            | KP_sub_PO_sub_4 | ASM2d_IC |
| KP_PP          | Half-saturation coefficient for poly-P in PHA storage (g PP / g PAO)               | KP_sub_PP | ASM2d_IC |
| K_A            | Half-saturation coefficient for volatile fatty acids S_A (mg COD/L)                | K_sub_A | ASM2d |
| K_ALK          | Half-saturation coefficient for alkalinity, heterotrophs (mol/m3)                  | K_sub_ALK | ASM2d, ASM3 |
| K_AOB_NH2OH    | Half-saturation coefficient for hydroxylamine, AOB                                 | K_sub_AOB_sep_NH_sub_2OH | ASM3_N2O, ASM2d_3 |
| K_AOB_NH4      | Half-saturation coefficient for ammonium, AOB                                      | K_sub_AOB_sep_NH_sub_4 | ASM1_2N, ASM3_N2O, ASM2d_EBPR, ASM2d_3 |
| K_AOB_NO       | Half-saturation coefficient for NO, AOB                                            | K_sub_AOB_sep_NO | ASM3_N2O, ASM2d_3 |
| K_AOB_NO2      | Half-saturation coefficient for nitrite, AOB                                       | K_sub_AOB_sep_NO_sub_2 | ASM3_N2O, ASM2d_3 |
| K_AOB_O2_AMO   | Half-saturation coefficient for oxygen, AMO step                                   | K_sub_AOB_sep_O_sub_2_sup_AMO | ASM1_2N, ASM3_N2O, ASM2d_EBPR, ASM2d_3 |
| K_AOB_O2_HAO   | Half-saturation coefficient for oxygen, AOB HAO steps                              | K_sub_AOB_sep_O_sub_2_sup_HAO | ASM3_N2O, ASM2d_3 |
| K_AOB_O2_I     | Oxygen inhibition coefficient, AOB N2O pathway                                     | K_sub_AOB_sep_O_sub_2_sup_I | ASM3_N2O, ASM2d_3 |
| K_AOB_O2_I_P27 | Oxygen inhibition coefficient, AOB reaction P27                                    | K_sub_AOB_sep_O_sub_2_sup_I_sep_P27 | ASM3_N2O, ASM2d_3 |
| K_A_ALK        | Half-saturation coefficient for alkalinity, autotrophs (mol/m3)                    | K_sub_A_sep_ALK | ASM3 |
| K_A_NH4        | Half-saturation coefficient for ammonium, autotrophs (mg N/L)                      | K_sub_A_sep_NH_sub_4 | ASM3 |
| K_A_O2         | Half-saturation coefficient for oxygen, autotrophs (mg O2/L)                       | K_sub_A_sep_O_sub_2 | ASM3 |
| K_F            | Half-saturation coefficient for fermentable substrate S_F (mg COD/L)               | K_sub_F | ASM2d, ASM2d_IC |
| K_H            | Hydrolysis rate constant (1/d)                                                     | K_sub_H | ASM2d, ASM2d_IC |
| K_H_ALK        | Half-saturation coefficient for alkalinity, heterotrophs                           | K_sub_H_sep_ALK | ASM1_2N, ASM3_N2O, ASM2d_EBPR, ASM2d_3 |
| K_H_N2O        | Half-saturation coefficient for N2O, heterotrophs                                  | K_sub_H_sep_N_sub_2O | ASM3_N2O, ASM2d_3 |
| K_H_NH4        | Half-saturation coefficient for ammonium, heterotrophs                             | K_sub_H_sep_NH_sub_4 | ASM1_2N, ASM3_N2O, ASM2d_EBPR, ASM2d_3 |
| K_H_NO         | Inhibition coefficient for NO (Haldane term), heterotrophs                         | K_sub_H_sep_NO | ASM3_N2O, ASM2d_3 |
| K_H_NO2        | Half-saturation coefficient for nitrite, heterotrophs                              | K_sub_H_sep_NO_sub_2 | ASM3_N2O, ASM2d_3 |
| K_H_NO3        | Half-saturation coefficient for nitrate, heterotrophs                              | K_sub_H_sep_NO_sub_3 | ASM1_2N, ASM3_N2O, ASM2d_EBPR, ASM2d_3 |
| K_H_NOS        | Half-saturation coefficient for NO, heterotrophs                                   | K_sub_H_sep_NO_sub_S | ASM3_N2O, ASM2d_3 |
| K_H_NO_I1      | Inhibition coefficient for NO, heterotroph storage pathway I1                      | K_sub_H_sep_NO_sup_I1 | ASM3_N2O, ASM2d_3 |
| K_H_NO_I3      | Inhibition coefficient for NO, heterotroph storage pathway I3                      | K_sub_H_sep_NO_sup_I3 | ASM3_N2O, ASM2d_3 |
| K_H_O2         | Half-saturation coefficient for oxygen, heterotrophs                               | K_sub_H_sep_O_sub_2 | ASM1_2N, ASM3_N2O, ASM2d_EBPR, ASM2d_3 |
| K_H_O2inh      | Oxygen inhibition coefficient, heterotrophs                                        | K_sub_H_sep_O_sub_2_inh | ASM1_2N, ASM3_N2O, ASM2d_EBPR, ASM2d_3 |
| K_H_SS         | Half-saturation coefficient for readily biodegradable substrate                    | K_sub_H_sep_SS | ASM1_2N, ASM3_N2O, ASM2d_EBPR, ASM2d_3 |
| K_H_STO        | Half-saturation coefficient for stored organics (X_STO/X_H ratio)                  | K_sub_H_sep_STO | ASM3_N2O, ASM2d_3 |
| K_IPP          | Inhibition coefficient for additional poly-P storage                               | K_sub_IPP | ASM2d, ASM2d_EBPR, ASM2d_3 |
| K_MAX          | Maximum poly-P storage capacity per PAO (g PP / g PAO)                             | K_sub_MAX | ASM2d, ASM2d_IC |
| K_NH           | Half-saturation coefficient for ammonium, autotrophs (mg N/L)                      | K_sub_NH | ASM1 |
| K_NH4          | Half-saturation coefficient for ammonium, heterotrophs (mg N/L)                    | K_sub_NH_sub_4 | ASM2d, ASM3 |
| K_NO           | Half-saturation coefficient for nitrate, heterotrophs (mg N/L)                     | K_sub_NO | ASM1 |
| K_NO3          | Half-saturation coefficient for nitrate (mg N/L)                                   | K_sub_NO_sub_3 | ASM2d |
| K_NOB_NO2      | Half-saturation coefficient for nitrite, NOB                                       | K_sub_NOB_sep_NO_sub_2 | ASM1_2N, ASM3_N2O, ASM2d_EBPR, ASM2d_3 |
| K_NOB_O2       | Half-saturation coefficient for oxygen, NOB                                        | K_sub_NOB_sep_O_sub_2 | ASM1_2N, ASM3_N2O, ASM2d_EBPR, ASM2d_3 |
| K_NOX          | Half-saturation coefficient for nitrate/nitrite nitrogen (mg N/L)                  | K_sub_NOX | ASM3 |
| K_N_ALK        | Half-saturation coefficient for alkalinity, nitrifiers                             | K_sub_N_sep_ALK | ASM1_2N, ASM3_N2O, ASM2d_EBPR, ASM2d_3 |
| K_O2           | Half-saturation coefficient for oxygen, heterotrophs (mg O2/L)                     | K_sub_O_sub_2 | ASM2d, ASM3 |
| K_OA           | Half-saturation coefficient for oxygen, autotrophs (mg O2/L)                       | K_sub_OA | ASM1 |
| K_OH           | Half-saturation coefficient for oxygen, heterotrophs (mg O2/L)                     | K_sub_OH | ASM1 |
| K_P            | Half-saturation coefficient for phosphate (mg P/L)                                 | K_sub_P | ASM2d |
| K_PAO_ALK      | Half-saturation coefficient for alkalinity, PAO                                    | K_sub_PAO_sep_ALK | ASM2d_EBPR, ASM2d_3 |
| K_PAO_NH4      | Half-saturation coefficient for ammonium, PAO                                      | K_sub_PAO_sep_NH_sub_4 | ASM2d_EBPR, ASM2d_3 |
| K_PAO_NO3      | Half-saturation coefficient for nitrate, PAO                                       | K_sub_PAO_sep_NO_sub_3 | ASM2d_EBPR, ASM2d_3 |
| K_PAO_NO3inh   | Nitrate inhibition coefficient, PAO                                                | K_sub_PAO_sep_NO_sub_3_inh | ASM2d_EBPR, ASM2d_3 |
| K_PAO_O2       | Half-saturation coefficient for oxygen, PAO                                        | K_sub_PAO_sep_O_sub_2 | ASM2d_EBPR, ASM2d_3 |
| K_PAO_PHA      | Half-saturation coefficient for PHA (X_PHA/X_PAO ratio)                            | K_sub_PAO_sep_PHA | ASM2d_EBPR, ASM2d_3 |
| K_PAO_PO4      | Half-saturation coefficient for phosphate, PAO                                     | K_sub_PAO_sep_PO_sub_4 | ASM2d_EBPR, ASM2d_3 |
| K_PAO_PP       | Half-saturation coefficient for poly-P (X_PP/X_PAO ratio)                          | K_sub_PAO_sep_PP | ASM2d_EBPR, ASM2d_3 |
| K_PAO_PS       | Half-saturation coefficient for phosphorus uptake, PAO                             | K_sub_PAO_sep_PS | ASM2d_EBPR, ASM2d_3 |
| K_PAO_S        | Half-saturation coefficient for substrate, PAO                                     | K_sub_PAO_sep_S | ASM2d_EBPR, ASM2d_3 |
| K_PHA          | Half-saturation coefficient for PHA in PP storage and PAO growth (g PHA / g PAO)   | K_sub_PHA | ASM2d |
| K_PP           | Half-saturation coefficient for poly-P in PHA storage (g PP / g PAO)               | K_sub_PP | ASM2d |
| K_PP_MAX       | Maximum poly-P storage per PAO biomass                                             | K_sub_PP_sep_MAX | ASM2d_EBPR, ASM2d_3 |
| K_PS           | Half-saturation coefficient for phosphate in PP storage (mg P/L)                   | K_sub_PS | ASM2d |
| K_S            | Half-saturation coefficient for readily biodegradable substrate (mg COD/L)         | K_sub_S | ASM1, ASM3 |
| K_STO          | Half-saturation coefficient for stored organics (g X_STO / g X_H)                  | K_sub_STO | ASM3 |
| K_X            | Hydrolysis saturation coefficient (g X_S / g X_H)                                  | K_sub_X | ASM1, ASM2d, ASM3, ASM1_2N, ASM3_N2O, ASM2d_EBPR, ASM2d_3 |
| K_fe           | Half-saturation coefficient for fermentation of S_F (mg COD/L)                     | K_sub_fe | ASM2d, ASM2d_IC |
| Y_A            | Autotrophic (nitrifier) yield (g COD biomass / g N oxidized)                       | Y_sub_A | ASM1, ASM2d, ASM2d_IC, ASM3 |
| Y_AOB          | AOB yield                                                                          | Y_sub_AOB | ASM1_2N, ASM3_N2O, ASM2d_EBPR, ASM2d_3 |
| Y_H            | Heterotrophic yield (g COD biomass / g COD substrate)                              | Y_sub_H | ASM1, ASM2d, ASM2d_IC |
| Y_H_N2O        | Anoxic heterotrophic yield with N2O                                                | Y_sub_H_sep_N_sub_2O | ASM3_N2O, ASM2d_3 |
| Y_H_NO         | Anoxic heterotrophic yield with NO                                                 | Y_sub_H_sep_NO | ASM3_N2O, ASM2d_3 |
| Y_H_NO2        | Anoxic heterotrophic yield with nitrite                                            | Y_sub_H_sep_NO_sub_2 | ASM3_N2O, ASM2d_3 |
| Y_H_NO3        | Anoxic heterotrophic yield with nitrate                                            | Y_sub_H_sep_NO_sub_3 | ASM1_2N, ASM3_N2O, ASM2d_EBPR, ASM2d_3 |
| Y_H_NOX        | Heterotrophic yield on stored organics, anoxic growth (g COD / g COD)              | Y_sub_H_sep_NOX | ASM3 |
| Y_H_O2         | Aerobic heterotrophic yield (g COD / g COD)                                        | Y_sub_H_sep_O_sub_2 | ASM3, ASM1_2N, ASM3_N2O, ASM2d_EBPR, ASM2d_3 |
| Y_NOB          | NOB yield                                                                          | Y_sub_NOB | ASM1_2N, ASM3_N2O, ASM2d_EBPR, ASM2d_3 |
| Y_PAO          | PAO yield on stored PHA, aerobic growth (g COD / g COD)                            | Y_sub_PAO | ASM2d, ASM2d_IC |
| Y_PAO_NO3      | Anoxic PAO yield on PHA                                                            | Y_sub_PAO_sep_NO_sub_3 | ASM2d_EBPR, ASM2d_3 |
| Y_PAO_O2       | Aerobic PAO yield on PHA                                                           | Y_sub_PAO_sep_O_sub_2 | ASM2d_EBPR, ASM2d_3 |
| Y_PHA          | PHA stored per S_A taken up, anaerobic PHA storage (g COD / g COD)                 | Y_sub_PHA | ASM2d, ASM2d_IC |
| Y_PHA_PP_NO3   | PHA consumed per poly-P stored, anoxic                                             | Y_sub_PHA_sep_PP_sep_NO_sub_3 | ASM2d_EBPR, ASM2d_3 |
| Y_PHA_PP_O2    | PHA consumed per poly-P stored, aerobic                                            | Y_sub_PHA_sep_PP_sep_O_sub_2 | ASM2d_EBPR, ASM2d_3 |
| Y_PO4          | Phosphorus release per PHA consumed, anaerobic P release (g P / g COD)             | Y_sub_PO_sub_4 | ASM2d, ASM2d_IC |
| Y_PO4_PP       | Phosphate release per PHA stored, anaerobic                                        | Y_sub_PO_sub_4_sep_PP | ASM2d_EBPR, ASM2d_3 |
| Y_STO_N2O      | Yield of stored organics with N2O                                                  | Y_sub_STO_sep_N_sub_2O | ASM3_N2O, ASM2d_3 |
| Y_STO_NO       | Yield of stored organics with NO                                                   | Y_sub_STO_sep_NO | ASM3_N2O, ASM2d_3 |
| Y_STO_NO2      | Yield of stored organics with nitrite                                              | Y_sub_STO_sep_NO_sub_2 | ASM3_N2O, ASM2d_3 |
| Y_STO_NO3      | Yield of stored organics with nitrate                                              | Y_sub_STO_sep_NO_sub_3 | ASM3_N2O, ASM2d_3 |
| Y_STO_NOX      | Anoxic storage yield of X_STO on S_S (g COD / g COD)                               | Y_sub_STO_sep_NOX | ASM3 |
| Y_STO_O2       | Aerobic storage yield of X_STO on S_S (g COD / g COD)                              | Y_sub_STO_sep_O_sub_2 | ASM3, ASM3_N2O, ASM2d_3 |
| b_A            | Autotrophic decay rate (1/d)                                                       | b_sub_A | ASM1 |
| b_AOB          | AOB decay rate                                                                     | b_sub_AOB | ASM1_2N, ASM3_N2O, ASM2d_EBPR, ASM2d_3 |
| b_AUT          | Autotrophic lysis rate (1/d)                                                       | b_sub_AUT | ASM2d, ASM2d_IC |
| b_A_NOX        | Anoxic endogenous respiration rate of autotrophs (1/d)                             | b_sub_A_sep_NOX | ASM3 |
| b_A_O2         | Aerobic endogenous respiration rate of autotrophs (1/d)                            | b_sub_A_sep_O_sub_2 | ASM3 |
| b_H            | Heterotrophic lysis rate (1/d)                                                     | b_sub_H | ASM1, ASM2d, ASM2d_IC |
| b_H_NOX        | Anoxic endogenous respiration rate of heterotrophs (1/d)                           | b_sub_H_sep_NOX | ASM3 |
| b_H_O2         | Aerobic endogenous respiration rate of heterotrophs (1/d)                          | b_sub_H_sep_O_sub_2 | ASM3, ASM1_2N, ASM3_N2O, ASM2d_EBPR, ASM2d_3 |
| b_NOB          | NOB decay rate                                                                     | b_sub_NOB | ASM1_2N, ASM3_N2O, ASM2d_EBPR, ASM2d_3 |
| b_PAO          | PAO lysis rate (1/d)                                                               | b_sub_PAO | ASM2d, ASM2d_IC, ASM2d_EBPR, ASM2d_3 |
| b_PHA          | PHA lysis rate (1/d)                                                               | b_sub_PHA | ASM2d, ASM2d_IC, ASM2d_EBPR, ASM2d_3 |
| b_PP           | Polyphosphate lysis rate (1/d)                                                     | b_sub_PP | ASM2d, ASM2d_IC, ASM2d_EBPR, ASM2d_3 |
| b_STO_NOX      | Anoxic respiration rate of stored organics (1/d)                                   | b_sub_STO_sep_NOX | ASM3 |
| b_STO_O2       | Aerobic respiration rate of stored organics (1/d)                                  | b_sub_STO_sep_O_sub_2 | ASM3, ASM3_N2O, ASM2d_3 |
| eps            | Small-denominator guard for saturation terms (numerical)                           | eps | ASM1, ASM2d, ASM2d_IC |
| eta_AOB_1      | Reduction factor for AOB HAO step 3                                                | eta_sub_AOB_sep_1 | ASM3_N2O, ASM2d_3 |
| eta_AOB_2      | Fraction of chemical hydroxylamine oxidation                                       | eta_sub_AOB_sep_2 | ASM3_N2O, ASM2d_3 |
| eta_H_N2O      | Reduction factor for storage with N2O                                              | eta_sub_H_sep_N_sub_2O | ASM3_N2O, ASM2d_3 |
| eta_H_NO       | Reduction factor for storage with NO                                               | eta_sub_H_sep_NO | ASM3_N2O, ASM2d_3 |
| eta_H_NO2      | Reduction factor for storage with nitrite                                          | eta_sub_H_sep_NO_sub_2 | ASM3_N2O, ASM2d_3 |
| eta_H_NO3      | Anoxic reduction factor for storage with nitrate                                   | eta_sub_H_sep_NO_sub_3 | ASM1_2N, ASM3_N2O, ASM2d_EBPR, ASM2d_3 |
| eta_H_endN2O   | Anoxic reduction factor for endogenous respiration with N2O                        | eta_sub_H_sep_end_N_sub_2O | ASM3_N2O, ASM2d_3 |
| eta_H_endNO    | Anoxic reduction factor for endogenous respiration with NO                         | eta_sub_H_sep_end_NO | ASM3_N2O, ASM2d_3 |
| eta_H_endNO2   | Anoxic reduction factor for endogenous respiration with nitrite                    | eta_sub_H_sep_end_NO_sub_2 | ASM3_N2O, ASM2d_3 |
| eta_H_endNO3   | Anoxic reduction factor for endogenous respiration with nitrate                    | eta_sub_H_sep_end_NO_sub_3 | ASM1_2N, ASM3_N2O, ASM2d_EBPR, ASM2d_3 |
| eta_NO3        | Anoxic reduction factor for heterotrophic growth / hydrolysis (-)                  | eta_sub_NO_sub_3 | ASM2d |
| eta_NOX        | Anoxic reduction factor for storage / growth (-)                                   | eta_sub_NOX | ASM3 |
| eta_N_end      | Anoxic reduction factor for endogenous respiration of nitrifiers                   | eta_sub_N_sep_end | ASM3_N2O, ASM2d_3 |
| eta_PAO_NO3    | Anoxic reduction factor for poly-P storage with nitrate                            | eta_sub_PAO_sep_NO_sub_3 | ASM2d_EBPR, ASM2d_3 |
| eta_PAO_end    | Anoxic reduction factor for PAO decay                                              | eta_sub_PAO_sep_end | ASM2d_EBPR, ASM2d_3 |
| eta_fe         | Anoxic reduction factor for fermentation (-)                                       | eta_sub_fe | ASM2d |
| eta_g          | Anoxic growth reduction factor for heterotrophs (-)                                | eta_sub_g | ASM1 |
| eta_h          | Anoxic hydrolysis reduction factor for heterotrophs (-)                            | eta_sub_h | ASM1 |
| f_ND           | Soluble fraction of influent organic N                                             | f_sub_ND | ASM2d_IC |
| f_SI           | Fraction of hydrolysis products that are soluble inert organic matter (-)          | f_sub_SI | ASM2d, ASM2d_IC, ASM3, ASM1_2N, ASM3_N2O, ASM2d_EBPR, ASM2d_3 |
| f_XI           | Fraction of lysis / endogenous-respiration products that are particulate inert (-) | f_sub_XI | ASM2d, ASM2d_IC, ASM3, ASM1_2N, ASM3_N2O, ASM2d_EBPR, ASM2d_3 |
| f_in_SA        | Influent COD fraction to S_A                                                       | f_sub_SA | ASM2d_IC |
| f_in_SF        | Influent COD fraction to S_F                                                       | f_sub_SF | ASM2d_IC |
| f_in_SI        | Influent COD fraction to S_I                                                       | f_sub_SI | ASM2d_IC |
| f_in_XI        | Influent COD fraction to X_I                                                       | f_sub_XI | ASM2d_IC |
| f_p            | Fraction of biomass decay products that are particulate inert (-)                  | f_sub_p | ASM1 |
| hAUT_NO3_end   | Anoxic reduction factor for autotrophic lysis (-)                                  | hAUT_sub_NO_sub_3_sep_end | ASM2d_IC |
| hH_NO3         | Anoxic reduction factor for heterotrophic growth (-)                               | hH_sub_NO_sub_3 | ASM2d_IC |
| hH_NO3_end     | Anoxic reduction factor for heterotrophic lysis (-)                                | hH_sub_NO_sub_3_sep_end | ASM2d_IC |
| hL_NO3         | Anoxic reduction factor for hydrolysis (-)                                         | hL_sub_NO_sub_3 | ASM2d_IC |
| hL_fe          | Anoxic reduction factor for fermentation (-)                                       | hL_sub_fe | ASM2d_IC |
| hPHA_NO3_end   | Anoxic reduction factor for PHA lysis (-)                                          | hPHA_sub_NO_sub_3_sep_end | ASM2d_IC |
| hPP_NO3_end    | Anoxic reduction factor for poly-P lysis (-)                                       | hPP_sub_NO_sub_3_sep_end | ASM2d_IC |
| hP_NO3         | Anoxic reduction factor for PAO growth (-)                                         | hP_sub_NO_sub_3 | ASM2d_IC |
| hP_NO3_end     | Anoxic reduction factor for PAO lysis (-)                                          | hP_sub_NO_sub_3_sep_end | ASM2d_IC |
| i_CSA          | Carbon content of volatile fatty acids S_A (g C / g COD)                           | i_sub_CSA | ASM2d_IC |
| i_CSF          | Carbon content of fermentable substrate (g C / g COD)                              | i_sub_CSF | ASM2d_IC |
| i_CSI          | Carbon content of soluble inert organic matter (g C / g COD)                       | i_sub_CSI | ASM2d_IC |
| i_CXB          | Carbon content of biomass (g C / g COD)                                            | i_sub_CXB | ASM2d_IC |
| i_CXI          | Carbon content of particulate inert organic matter (g C / g COD)                   | i_sub_CXI | ASM2d_IC |
| i_CXS          | Carbon content of slowly biodegradable substrate (g C / g COD)                     | i_sub_CXS | ASM2d_IC |
| i_KXPP         | Potassium content of polyphosphate (g K / g PP)                                    | i_sub_KXPP | ASM2d_IC |
| i_MgXPP        | Magnesium content of polyphosphate (g Mg / g PP)                                   | i_sub_MgXPP | ASM2d_IC |
| i_NBM          | Nitrogen content of biomass (g N / g COD)                                          | i_sub_NBM | ASM2d, ASM2d_IC, ASM3, ASM1_2N, ASM3_N2O, ASM2d_EBPR, ASM2d_3 |
| i_NOx_N2       | Electron-acceptor mass ratio, nitrate vs dinitrogen (g N / g N)                    | i_sub_NOx_sep_N_sub_2 | ASM2d_IC |
| i_NSF          | Nitrogen content of fermentable substrate (g N / g COD)                            | i_sub_NSF | ASM2d, ASM2d_IC |
| i_NSI          | Nitrogen content of soluble inert organic matter (g N / g COD)                     | i_sub_NSI | ASM2d, ASM2d_IC, ASM3, ASM1_2N, ASM3_N2O, ASM2d_EBPR, ASM2d_3 |
| i_NSS          | Nitrogen content of readily biodegradable substrate (g N / g COD)                  | i_sub_NSS | ASM3, ASM1_2N, ASM3_N2O, ASM2d_EBPR, ASM2d_3 |
| i_NXI          | Nitrogen content of particulate inert organic matter (g N / g COD)                 | i_sub_NXI | ASM2d, ASM2d_IC, ASM3, ASM1_2N, ASM3_N2O, ASM2d_EBPR, ASM2d_3 |
| i_NXS          | Nitrogen content of slowly biodegradable substrate (g N / g COD)                   | i_sub_NXS | ASM2d, ASM2d_IC, ASM3, ASM1_2N, ASM3_N2O, ASM2d_EBPR, ASM2d_3 |
| i_PBM          | Phosphorus content of biomass (g P / g COD)                                        | i_sub_PBM | ASM2d, ASM2d_IC, ASM2d_EBPR, ASM2d_3 |
| i_PSF          | Phosphorus content of fermentable substrate (g P / g COD)                          | i_sub_PSF | ASM2d, ASM2d_IC |
| i_PSI          | Phosphorus content of soluble inert organic matter (g P / g COD)                   | i_sub_PSI | ASM2d |
| i_PXI          | Phosphorus content of particulate inert organic matter (g P / g COD)               | i_sub_PXI | ASM2d, ASM2d_IC, ASM2d_EBPR, ASM2d_3 |
| i_PXS          | Phosphorus content of slowly biodegradable substrate (g P / g COD)                 | i_sub_PXS | ASM2d, ASM2d_IC |
| i_SSBM         | TSS content of active biomass (g TSS / g COD)                                      | i_sub_SSBM | ASM3 |
| i_SSSTO        | TSS content of stored organics (g TSS / g COD)                                     | i_sub_SSSTO | ASM3 |
| i_SSXI         | TSS content of particulate inert organic matter (g TSS / g COD)                    | i_sub_SSXI | ASM3 |
| i_SSXS         | TSS content of slowly biodegradable substrate (g TSS / g COD)                      | i_sub_SSXS | ASM3 |
| i_xb           | Nitrogen content of biomass (g N / g COD)                                          | i_sub_xb | ASM1 |
| i_xp           | Nitrogen content of particulate decay products (g N / g COD)                       | i_sub_xp | ASM1 |
| k_H            | Hydrolysis rate constant (1/d)                                                     | k_sub_H | ASM3, ASM1_2N, ASM3_N2O, ASM2d_EBPR, ASM2d_3 |
| k_STO          | Storage rate constant (1/d)                                                        | k_sub_STO | ASM3, ASM3_N2O, ASM2d_3 |
| k_a            | Ammonification rate constant (L/(mg N d))                                          | k_sub_a | ASM1 |
| k_h            | Hydrolysis rate constant (1/d)                                                     | k_sub_h | ASM1 |
| k_pre          | Phosphate precipitation rate constant (L/(mg MeOH d))                              | k_sub_pre | ASM2d |
| k_red          | Re-dissolution rate constant of metal phosphate (1/d)                              | k_sub_red | ASM2d |
| mu_A           | Maximum autotrophic growth rate (1/d)                                              | mu_sub_A | ASM1, ASM3 |
| mu_AOB_1_HAO   | Maximum rate of AOB HAO step 1 (hydroxylamine oxidation to NO)                     | mu_sub_AOB_sep_1_sup_HAO | ASM3_N2O, ASM2d_3 |
| mu_AOB_2_HAO   | Maximum rate of AOB HAO step 2 (NO oxidation to nitrite)                           | mu_sub_AOB_sep_2_sup_HAO | ASM3_N2O, ASM2d_3 |
| mu_AOB_3_HAO   | Maximum rate of AOB HAO step 3                                                     | mu_sub_AOB_sep_3_sup_HAO | ASM3_N2O, ASM2d_3 |
| mu_AOB_AMO     | Maximum rate of ammonia oxidation to hydroxylamine (AMO)                           | mu_sub_AOB_sup_AMO | ASM1_2N, ASM3_N2O, ASM2d_EBPR, ASM2d_3 |
| mu_AUT         | Maximum autotrophic growth rate (1/d)                                              | mu_sub_AUT | ASM2d, ASM2d_IC |
| mu_H           | Maximum heterotrophic growth rate (1/d)                                            | mu_sub_H | ASM1, ASM2d, ASM2d_IC, ASM3, ASM1_2N, ASM3_N2O, ASM2d_EBPR, ASM2d_3 |
| mu_NOB         | Maximum NOB growth rate (1/d)                                                      | mu_sub_NOB | ASM1_2N, ASM3_N2O, ASM2d_EBPR, ASM2d_3 |
| mu_PAO         | Maximum PAO growth rate (1/d)                                                      | mu_sub_PAO | ASM2d, ASM2d_IC, ASM2d_EBPR, ASM2d_3 |
| mw_N           | Molar mass of nitrogen (g/mol)                                                     | mw_sub_N | ASM2d |
| mw_P           | Molar mass of phosphorus (g/mol)                                                   | mw_sub_P | ASM2d |
| mw_alk         | Molecular weight of alkalinity                                                     | mw_sub_alk | ASM1, ASM2d |
| mw_n           | Molecular weight of nitrogen                                                       | mw_sub_n | ASM1 |
| q_AOB_1_HAO    | Rate constant for chemical hydroxylamine oxidation                                 | q_sub_AOB_sep_1_sup_HAO | ASM3_N2O, ASM2d_3 |
| q_PHA          | PHA storage rate constant (1/d)                                                    | q_sub_PHA | ASM2d, ASM2d_IC, ASM2d_EBPR, ASM2d_3 |
| q_PP           | Polyphosphate (PP) storage rate constant (1/d)                                     | q_sub_PP | ASM2d, ASM2d_IC, ASM2d_EBPR, ASM2d_3 |
| q_fe           | Fermentation rate constant (1/d)                                                   | q_sub_fe | ASM2d, ASM2d_IC |

