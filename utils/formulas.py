"""
formulas.py - Carbon Emission Calculator
=========================================
EXACT replication of Excel sheet: "Carbon_Emission_Calculator__Packaging___Transport_.xlsx"

Excel Cell Mapping:
-------------------
CORRUGATED BOX:
  E16 = adjusted length  (=IF($M$12=TRUE,($E$12+40),...))
  G16 = adjusted width   (=IF($M$12=TRUE,($G$12+40),...))
  H16 = adjusted height  (=IF($M$12=TRUE,($H$12+40),...))
  M16 = box area (m2)    (ply-adjusted surface area / 1,000,000)
  N16 = box weight (kg)  (ply weight adjustment on M16)

WOODEN BOX:
  E19 = adjusted length  (=IF($M$13=TRUE,($E$12+40),...))
  G19 = adjusted width
  H19 = adjusted height
  M19 = box volume (m3)  (=(E19*G19*H19-(E19-B19)*(G19-B19)*(H19-B19))/1e9)
  N19 = box weight (kg)  (=M19*600)

PALLET:
  E22 = pallet L         (=E12+40)
  G22 = pallet W         (=G12+40)
  H23 = deck H = 36      (fixed)
  E24,G24,H24 = runner   (125, 110, 90 fixed)
  I24 = runner count = 9
  E25=G22, G25=90, H25=20, I25=3
  M22 = pallet volume    (=((E23*G23*H23)+(E24*G24*H24)*I24+(E25*G25*H25)*I25)/1e9)
  N22 = pallet weight    (=M22*500)

CARBON EMISSIONS (Backup calculations sheet):
  C15 = 0.491  (corrugation emission factor kgCO2/kg)
  C18 = 0.31   (solidwood emission factor)
  C19 = 0.68   (plywood emission factor)
  E15 = 2.792  (LDPE)
  E16 = 2.506  (HDPE)
  E17 = 3.576  (PP)
  E18 = 2.587  (LLDPE)
  E19 = 2.982  (PS)

TRANSPORT EMISSION FACTORS (kgCO2/tonne-km):
  H15 = 62/1000 = 0.062  (Road)
  H16 = 22/1000 = 0.022  (Rail)
  H17 = 16/1000 = 0.016  (Sea/Ocean)
  H18 = 0.61             (Air)

DESIGN CALC TRANSPORT (Backup H32):
  =IF(G32=G15, H30*I30*H15, IF(G32=G16,...))
  Where H30=distance, I30=total_weight_kg/1000 (tonnes)

PHYSICAL INPUT TRANSPORT (Backup H38):
  =IF(G38=G15, H36*I36*H15, ...)
  Where H36=distance, I36=U34/1000
"""

# ─── EMISSION FACTORS (from Backup calculations sheet) ───────────────────────

# Packaging material emission factors (kgCO2/kg)  — Backup!C15, C18, C19
EMISSION_FACTORS = {
    "Corrugation": 0.491,      # Backup!C15
    "Solidwood":   0.31,       # Backup!C18
    "Plywood":     0.68,       # Backup!C19
}

# Plastic subcategory emission factors (kgCO2/kg) — Backup!D15:E19
PLASTIC_EMISSION_FACTORS = {
    "LDPE":  2.792,   # Backup!E15
    "HDPE":  2.506,   # Backup!E16
    "PP":    3.576,   # Backup!E17
    "LLDPE": 2.587,   # Backup!E18
    "PS":    2.982,   # Backup!E19
}

# Transport emission factors (kgCO2/tonne-km) — Backup!H15:H18
TRANSPORT_FACTORS = {
    "Road":       62 / 1000,   # Backup!H15 =62/1000 = 0.062
    "Rail":       22 / 1000,   # Backup!H16 =22/1000 = 0.022
    "Sea (Ocean)": 16 / 1000,  # Backup!H17 =16/1000 = 0.016
    "Air":        0.61,        # Backup!H18
}

# Pallet fixed constants
PALLET_DECK_H        = 36    # mm — Calculator!H23
PALLET_RUNNER_L      = 125   # mm — Calculator!E24
PALLET_RUNNER_W      = 110   # mm — Calculator!G24
PALLET_RUNNER_H      = 90    # mm — Calculator!H24
PALLET_RUNNER_COUNT  = 9     # — Calculator!I24
PALLET_PLANK_W       = 90    # mm — Calculator!G25
PALLET_PLANK_H       = 20    # mm — Calculator!H25
PALLET_PLANK_COUNT   = 3     # — Calculator!I25
PALLET_DENSITY       = 500   # kg/m3 — Calculator!N22 uses *500

# Box size clearance — Calculator!E16 adds 40 mm
BOX_CLEARANCE = 40           # mm


# ─── 2.1  CORRUGATED BOX ─────────────────────────────────────────────────────

def corrugated_adjusted_dims(length_mm: float, width_mm: float, height_mm: float,
                              enabled: bool = True) -> tuple:
    """
    Excel: E16=IF($M$12=TRUE,($E$12+40),IF($M$12=FALSE,($E$12*0),0))
    Returns (adj_L, adj_W, adj_H)
    """
    if enabled:
        return (length_mm + BOX_CLEARANCE,
                width_mm + BOX_CLEARANCE,
                height_mm + BOX_CLEARANCE)
    else:
        return (0.0, 0.0, 0.0)


def corrugated_box_area(length_mm: float, width_mm: float, height_mm: float,
                        ply: int, enabled: bool = True) -> float:
    """
    Excel M16:
    =IF(B16=7,
        (2*(E16*G16+E16*H16+G16*H16) + 2*(E16*G16+E16*H16+G16*H16)*105/100)/1000000,
     IF(B16=5,
        (2*(E16*G16+E16*H16+G16*H16) + 2*(E16*G16+E16*H16+G16*H16)*110/100)/1000000,
     IF(B16=3,
        (2*(E16*G16+E16*H16+G16*H16) + 2*(E16*G16+E16*H16+G16*H16)*170/100)/1000000,
     0)))

    Ply adjustments (additional corrugation layers factor):
      7 ply → +105%  (multiply base by 105/100)
      5 ply → +110%
      3 ply → +170%
    Returns area in m²
    """
    adj_L, adj_W, adj_H = corrugated_adjusted_dims(length_mm, width_mm, height_mm, enabled)
    base_sa = 2 * (adj_L * adj_W + adj_L * adj_H + adj_W * adj_H)  # mm²

    ply_factors = {7: 105 / 100, 5: 110 / 100, 3: 170 / 100}
    factor = ply_factors.get(ply, 0)

    area_m2 = (base_sa + base_sa * factor) / 1_000_000
    return area_m2


def corrugated_box_weight(area_m2: float, ply: int) -> float:
    """
    Excel N16:
    =IF(B16=3, M16 - M16*25/100,
     IF(B16=5, M16 + M16*5/100,
     IF(B16=7, M16 + M16*45/100)))

    Ply weight adjustment (applied on area in m2 to give kg):
      3 ply → area * (1 - 0.25)
      5 ply → area * (1 + 0.05)
      7 ply → area * (1 + 0.45)
    Returns weight in kg
    """
    if ply == 3:
        return area_m2 - area_m2 * 25 / 100
    elif ply == 5:
        return area_m2 + area_m2 * 5 / 100
    elif ply == 7:
        return area_m2 + area_m2 * 45 / 100
    return 0.0


# ─── 2.2  WOODEN BOX (HOLLOW) ────────────────────────────────────────────────

def wooden_box_adjusted_dims(length_mm: float, width_mm: float, height_mm: float,
                              enabled: bool = True) -> tuple:
    """
    Excel E19=IF($M$13=TRUE,($E$12+40),IF($M$13=FALSE,($E$12*0),0))
    """
    if enabled:
        return (length_mm + BOX_CLEARANCE,
                width_mm + BOX_CLEARANCE,
                height_mm + BOX_CLEARANCE)
    else:
        return (0.0, 0.0, 0.0)


def wooden_box_volume(length_mm: float, width_mm: float, height_mm: float,
                      thickness_mm: float, enabled: bool = True) -> float:
    """
    Excel M19:
    =((E19*G19*H19) - ((E19-B19)*(G19-B19)*(H19-B19))) / 1000000000

    Outer volume - Inner volume, converted mm³ → m³
    """
    adj_L, adj_W, adj_H = wooden_box_adjusted_dims(length_mm, width_mm, height_mm, enabled)
    t = thickness_mm
    outer = adj_L * adj_W * adj_H
    inner = (adj_L - t) * (adj_W - t) * (adj_H - t)
    volume_m3 = (outer - inner) / 1_000_000_000
    return volume_m3


def wooden_box_weight(volume_m3: float) -> float:
    """
    Excel N19: =M19*600
    Density of solidwood = 600 kg/m³
    """
    return volume_m3 * 600


# ─── 2.3  WOODEN PALLET ──────────────────────────────────────────────────────

def pallet_volume(length_mm: float, width_mm: float) -> float:
    """
    Excel M22:
    =((E23*G23*H23) + (E24*G24*H24)*I24 + (E25*G25*H25)*I25) / 1000000000

    Pallet L = E12+40, Pallet W = G12+40 (same clearance as box)
    E23=E22=pallet_L, G23=G22=pallet_W, H23=36 (deck height, fixed)
    E24=125, G24=110, H24=90, I24=9  (runner - fixed)
    E25=G22=pallet_W, G25=90, H25=20, I25=3  (planks - fixed)
    """
    pallet_L = length_mm + BOX_CLEARANCE   # Excel E22 = E12+40
    pallet_W = width_mm + BOX_CLEARANCE    # Excel G22 = G12+40

    # Deck — Excel row 23
    deck_vol = pallet_L * pallet_W * PALLET_DECK_H * 1   # I23=1

    # Runner/Block — Excel row 24 (fixed dims)
    runner_vol = (PALLET_RUNNER_L * PALLET_RUNNER_W *
                  PALLET_RUNNER_H * PALLET_RUNNER_COUNT)

    # Plank/Runner — Excel row 25 (E25=G22=pallet_W)
    plank_vol = pallet_W * PALLET_PLANK_W * PALLET_PLANK_H * PALLET_PLANK_COUNT

    total_vol_m3 = (deck_vol + runner_vol + plank_vol) / 1_000_000_000
    return total_vol_m3


def pallet_weight(volume_m3: float) -> float:
    """
    Excel N22: =M22*500
    Pallet density = 500 kg/m³
    """
    return volume_m3 * PALLET_DENSITY


# ─── 2.4  TRANSPORT PACKAGING WEIGHT (for Physical Input path) ───────────────

def physical_packaging_weight_corr_pallet(
        corrugated_weight_kg: float, pallet_weight_kg: float,
        use_corr: bool) -> float:
    """
    Excel U18: =IF($S$18=TRUE,$U$12+$U$14,0)
    When corrugated box selected, weight = corr_physical_kg + pallet_physical_kg
    """
    if use_corr:
        return corrugated_weight_kg + pallet_weight_kg
    return 0.0


def physical_packaging_weight_wood_pallet(
        wooden_weight_kg: float, pallet_weight_kg: float,
        use_wood: bool) -> float:
    """
    Excel U19: =IF($S$19=TRUE,$U$13+$U$14,0)
    """
    if use_wood:
        return wooden_weight_kg + pallet_weight_kg
    return 0.0


# ─── 2.5  CARBON EMISSIONS ───────────────────────────────────────────────────

def material_co2_corrugated(box_weight_kg: float) -> float:
    """
    Excel E30: =N16 * 'Backup calculations'!C15
    = box_weight_kg * 0.491
    """
    return box_weight_kg * EMISSION_FACTORS["Corrugation"]


def material_co2_wooden_box(box_weight_kg: float, wood_type: str) -> float:
    """
    Excel H30:
    =IF(I19='Backup calculations'!$B$18, Calculator!N19*'Backup calculations'!$C$18,
     IF(Calculator!I19='Backup calculations'!$B$19, Calculator!N19*'Backup calculations'!$C$19))
    I19 = wood_type; B18='Solidwood'; B19='Plywood'
    """
    factor = EMISSION_FACTORS.get(wood_type, 0.0)
    return box_weight_kg * factor


def material_co2_pallet(pallet_weight_kg: float, wood_type: str) -> float:
    """
    Excel K30:
    =IF(K22='Backup calculations'!B18, Calculator!N22*'Backup calculations'!C18,
     IF(Calculator!K22='Backup calculations'!B19, Calculator!N22*'Backup calculations'!C19))
    K22 = pallet wood type
    """
    factor = EMISSION_FACTORS.get(wood_type, 0.0)
    return pallet_weight_kg * factor


def material_co2_plastic(plastic_weight_kg: float, plastic_type: str) -> float:
    """
    Excel X30:
    =IF(T25='Backup calculations'!D15, 'Backup calculations'!E15*Calculator!W25, ...)
    T25 = plastic subcategory
    """
    factor = PLASTIC_EMISSION_FACTORS.get(plastic_type, 0.0)
    return plastic_weight_kg * factor


def transport_co2_design(transport_type: str, total_weight_kg: float,
                         distance_km: float) -> float:
    """
    Excel Backup!H32:
    =IF($G$32=$G$15, $H$30*$I$30*$H$15,
     IF($G$32=$G$16, $H$30*$I$30*$H$16,
     IF($G$32=$G$17, $H$30*$I$30*$H$17,
     IF($G$32=$G$18, $H$30*$I$30*$H$18))))

    H30 = distance_km  (Calculator!I34)
    I30 = Calculator!H34/1000  (total_weight_kg / 1000 = tonnes)
    H15..H18 = transport emission factors
    Returns CO2 in kg
    """
    factor = TRANSPORT_FACTORS.get(transport_type, 0.0)
    weight_tonnes = total_weight_kg / 1000
    return distance_km * weight_tonnes * factor


def transport_co2_physical(transport_type: str, total_weight_kg: float,
                            distance_km: float) -> float:
    """
    Excel Backup!H38 (same formula as H32 but for physical input path):
    H36 = Calculator!W34 = distance
    I36 = Calculator!U34/1000 = total weight in tonnes
    """
    factor = TRANSPORT_FACTORS.get(transport_type, 0.0)
    weight_tonnes = total_weight_kg / 1000
    return distance_km * weight_tonnes * factor


# ─── MASTER CALCULATION FUNCTION ─────────────────────────────────────────────

def calculate_all(
    # Product dimensions
    length_mm: float, width_mm: float, height_mm: float,
    # Box settings
    ply: int,
    box_thickness_mm: float,
    phys_wood_type_box: str, 
    wood_type_box: str,      # 'Solidwood' or 'Plywood'
    wood_type_pallet: str,   # 'Plywood' or 'Solidwood'
    # Enable flags (which packaging is used)
    use_corrugated: bool,
    use_wooden: bool,
    # Transport - Design path
    transport_type_design: str,
    product_weight_kg: float,
    distance_design_km: float,
    # Physical inputs (if user knows actual weights)
    phys_corrugated_kg: float,
    phys_wooden_kg: float,
    phys_pallet_kg: float,
    phys_plastic_kg: float,
    phys_plastic_type: str,
    phys_packaging_combo: str,  # 'corrugated+pallet' or 'wooden+pallet'
    transport_type_physical: str,
    phys_product_weight_kg: float,
    distance_physical_km: float,
) -> dict:
    """
    Master calculation matching the full Excel sheet.
    Returns a dict with all intermediate and final values.
    """
    results = {}

    # ── CORRUGATED BOX (Design) ──────────────────────────────
    corr_area_m2 = corrugated_box_area(length_mm, width_mm, height_mm,
                                       ply, enabled=use_corrugated)
    corr_weight_kg = corrugated_box_weight(corr_area_m2, ply) if use_corrugated else 0.0

    results["corr_area_m2"]   = corr_area_m2
    results["corr_weight_kg"] = corr_weight_kg

    # ── WOODEN BOX (Design) ──────────────────────────────────
    wood_vol_m3   = wooden_box_volume(length_mm, width_mm, height_mm,
                                      box_thickness_mm, enabled=use_wooden)
    wood_weight_kg = wooden_box_weight(wood_vol_m3) if use_wooden else 0.0

    results["wood_vol_m3"]    = wood_vol_m3
    results["wood_weight_kg"] = wood_weight_kg

    # ── PALLET (Design) ──────────────────────────────────────
    pallet_vol_m3  = pallet_volume(length_mm, width_mm)
    pallet_wt_kg   = pallet_weight(pallet_vol_m3)

    results["pallet_vol_m3"]  = pallet_vol_m3
    results["pallet_wt_kg"]   = pallet_wt_kg

    # Pallet dims for display
    results["pallet_L_mm"] = length_mm + BOX_CLEARANCE
    results["pallet_W_mm"] = width_mm  + BOX_CLEARANCE
    results["pallet_H_mm"] = PALLET_DECK_H + PALLET_RUNNER_H + PALLET_PLANK_H

    # ── DESIGN PACKAGING WEIGHT (for transport) ──────────────
    # Excel E34: =IF(M12=TRUE, N16+N22, IF(M12=FALSE, N19+N22))
    if use_corrugated:
        design_pkg_weight_kg = corr_weight_kg + pallet_wt_kg
    else:
        design_pkg_weight_kg = wood_weight_kg + pallet_wt_kg

    design_total_weight_kg = design_pkg_weight_kg + product_weight_kg  # Excel H34

    results["design_pkg_weight_kg"]   = design_pkg_weight_kg
    results["design_total_weight_kg"] = design_total_weight_kg

    # ── DESIGN CARBON EMISSIONS ──────────────────────────────
    # Excel logic: corrugated and wooden box are ALTERNATIVES (one OR the other)
    # Excel E34: =IF(M12=TRUE, N16+N22, IF(M12=FALSE, N19+N22))
    # M12=corrugated checkbox, M13=wooden checkbox — only ONE active at a time
    # Material CO2 only includes the ACTIVE box type + pallet
    if use_corrugated:
        co2_corr_design  = material_co2_corrugated(corr_weight_kg)
        co2_wood_design  = 0.0  # wooden box not the active choice
    else:
        co2_corr_design  = 0.0  # corrugated not the active choice
        co2_wood_design  = material_co2_wooden_box(wood_weight_kg, wood_type_box)

    co2_pallet_design  = material_co2_pallet(pallet_wt_kg, wood_type_pallet)
    co2_transport_design = transport_co2_design(
        transport_type_design, design_total_weight_kg, distance_design_km
    )
    co2_material_design = co2_corr_design + co2_wood_design + co2_pallet_design
    co2_total_design    = co2_material_design + co2_transport_design

    results["co2_corr_design"]       = co2_corr_design
    results["co2_wood_design"]       = co2_wood_design
    results["co2_pallet_design"]     = co2_pallet_design
    results["co2_transport_design"]  = co2_transport_design
    results["co2_material_design"]   = co2_material_design
    results["co2_total_design"]      = co2_total_design

    # ── PHYSICAL INPUT PATH ──────────────────────────────────
    # Excel U18: =IF($S$18=TRUE,$U$12+$U$14,0)
    # Excel U19: =IF($S$19=TRUE,$U$13+$U$14,0)
    use_corr_phys  = (phys_packaging_combo == "corrugated+pallet")
    use_wood_phys  = (phys_packaging_combo == "wooden+pallet")
    phys_pkg_wt    = physical_packaging_weight_corr_pallet(
        phys_corrugated_kg, phys_pallet_kg, use_corr_phys
    ) + physical_packaging_weight_wood_pallet(
        phys_wooden_kg, phys_pallet_kg, use_wood_phys
    )

    # Excel U34: =R34+T34  (phys_pkg_weight + phys_product_weight)
    phys_total_weight_kg = phys_pkg_wt + phys_product_weight_kg

    results["phys_pkg_wt"]          = phys_pkg_wt
    results["phys_total_weight_kg"] = phys_total_weight_kg

    # Physical material CO2
    # Excel W23 = U12 (corrugated physical weight)
    co2_corr_phys    = material_co2_corrugated(phys_corrugated_kg)
    # Excel W24 = U13+U14 (wood + pallet)
    wood_phys_total  = phys_wooden_kg + phys_pallet_kg
    co2_wood_phys    = material_co2_wooden_box(wood_phys_total, phys_wood_type_box)
    co2_plastic_phys = material_co2_plastic(phys_plastic_kg, phys_plastic_type)
    co2_transport_phys = transport_co2_physical(
        transport_type_physical, phys_total_weight_kg, distance_physical_km
    )
    co2_material_phys = co2_corr_phys + co2_wood_phys + co2_plastic_phys
    co2_total_phys    = co2_material_phys + co2_transport_phys

    results["co2_corr_phys"]       = co2_corr_phys
    results["co2_wood_phys"]       = co2_wood_phys
    results["co2_plastic_phys"]    = co2_plastic_phys
    results["co2_transport_phys"]  = co2_transport_phys
    results["co2_material_phys"]   = co2_material_phys
    results["co2_total_phys"]      = co2_total_phys

    return results
