import re
import streamlit as st
import matplotlib.pyplot as plt

# -------------------------------------------------
# Base de données matériaux
# -------------------------------------------------
materiaux = {
    "Gravier": {"densite": 1500, "impact": 0.01761},
    "Béton": {"densite": 2300, "impact": 0.1088},
    "Enrobé bitumineux": {"densite": 2400, "impact": 0.1154},
    "Pavé béton préfabriquée": {"densite": 2300, "impact": 0.2087},
    "Grille béton préfabriquée": {"densite": 2300, "impact": 0.2087},
    "Pavé en Grès": {"densite": 2500, "impact": 0.0957},
    "Dalle en pierre": {"densite": 1000, "impact": 0.83},
    "Dalle en pierre polie": {"densite": 1000, "impact": 1.307},
    "Géotextile": {"densite": 1, "impact": 1.3},
    "Béton maigre": {"densite": 2150, "impact": 0.0628},
    "Granulés de béton": {"densite": 1550, "impact": 0.01392},
    "Grave": {"densite": 1500, "impact": 0.01761},
    "Indéfini": {"densite": None, "impact": None},
}

impact_excavation = 0.43      # kg CO₂e / m³
impact_sable     = 1500 * 0.01565
impact_ciment    = 1550 * 0.26

pavements = {
    "Revêtement bitumineux": [
        {"materiau": "Enrobé bitumineux", "epaisseur_cm": 10},
        {"materiau": "Gravier",            "epaisseur_cm": 5},
        {"materiau": "Grave",              "epaisseur_cm": 20},
    ],
    "Revêtement béton": [
        {"materiau": "Béton",  "epaisseur_cm": 15},
        {"materiau": "Gravier","epaisseur_cm": 5},
        {"materiau": "Grave",  "epaisseur_cm": 25},
    ],
    "Revêtement gravier": [
        {"materiau": "Gravier","epaisseur_cm": 5},
        {"materiau": "Gravier","epaisseur_cm": 10},
        {"materiau": "Grave",  "epaisseur_cm": 25},
    ],
    "Revêtement pavé en pierre naturelle": [
        {"materiau": "Pavé en Grès","epaisseur_cm": 8},
        {"materiau": "Gravier",     "epaisseur_cm": 3},
        {"materiau": "Grave",       "epaisseur_cm": 25},
    ],
    "Revêtement dalle en pierre naturelle": [
        {"materiau": "Dalle en pierre polie","epaisseur_cm": 4},
        {"materiau": "Gravier",              "epaisseur_cm": 3},
        {"materiau": "Grave",                "epaisseur_cm": 25},
    ],
    "Revêtement béton préfabriquée": [
        {"materiau": "Pavé béton préfabriquée","epaisseur_cm": 8},
        {"materiau": "Gravier",               "epaisseur_cm": 3},
        {"materiau": "Grave",                 "epaisseur_cm": 25},
    ],
    "Revêtement grille de béton préfabriquée": [
        {"materiau": "Grille béton préfabriquée","epaisseur_cm": 4},
        {"materiau": "Gravier",                 "epaisseur_cm": 3},
        {"materiau": "Grave",                   "epaisseur_cm": 25},
    ],
}

liste_lie = (
    "Pavé béton préfabriquée",
    "Pavé en Grès",
    "Dalle en pierre",
    "Dalle en pierre polie",
)

# -------------------------------------------------
# Session state & helpers
# -------------------------------------------------
if "pavement_type" not in st.session_state:
    st.session_state.pavement_type = list(pavements.keys())[0]
if "couches" not in st.session_state:
    st.session_state.couches = [c.copy() for c in pavements[st.session_state.pavement_type]]

def clear_layer_widget_keys():
    """Supprime les clés des widgets de couches pour forcer la recréation."""
    pattern = re.compile(r"^(mat_|ep_|joint_|imp_|del_)")
    for key in list(st.session_state.keys()):
        if pattern.match(key):
            del st.session_state[key]

def reset_couches():
    """Réinitialise les couches au changement de revêtement."""
    choix = st.session_state.pavement_type
    st.session_state.couches = [c.copy() for c in pavements[choix]]
    clear_layer_widget_keys()
    st.rerun()

# -------------------------------------------------
# Fonctions de calcul
# -------------------------------------------------
def empreinte_couche(couche, surface_m2):
    """Impact carbone d'une couche en kg CO₂e pour la surface donnée."""
    mat = couche["materiau"]
    ep_cm = 0 if mat == "Géotextile" else couche.get("epaisseur_cm", 0)

    if mat == "Indéfini":
        impact_vol = couche.get("impact", 0)  # kg CO₂e / m³ saisi par l’utilisateur
    else:
        impact_vol = materiaux[mat]["impact"] * materiaux[mat]["densite"]  # kg CO₂e / m³
        if mat in liste_lie:
            joint = couche.get("joint", "Sable")
            add = impact_sable if joint == "Sable" else impact_ciment
            impact_vol += add * 0.05  # ex. +5 % lié au joint

    return impact_vol * (ep_cm / 100.0) * surface_m2

def empreinte_totale(surface_m2):
    total = sum(empreinte_couche(c, surface_m2) for c in st.session_state.couches)
    profondeur = sum(
        c.get("epaisseur_cm", 0)
        for c in st.session_state.couches
        if c.get("materiau") != "Géotextile"
    ) / 100.0
    total += profondeur * impact_excavation * surface_m2
    return total

# -------------------------------------------------
# Interface
# -------------------------------------------------
st.title("🌍 Calculateur d'empreinte carbone de revêtement")

surface_revetue = st.number_input("Surface revêtue (m²)", min_value=1.0, value=100.0)
surface_batiment = st.number_input("Surface du bâtiment (m²)", min_value=1.0, value=50.0)

st.markdown("---")

# Choix du revêtement
st.selectbox(
    "Type de revêtement",
    list(pavements.keys()),
    index=list(pavements.keys()).index(st.session_state.pavement_type),
    on_change=reset_couches,
    key="pavement_type",
)

st.subheader("⚙️ Couches du revêtement")

# Couches dynamiques
for i, couche in enumerate(st.session_state.couches):
    c1, c2, c3, c4 = st.columns([3, 1.5, 2, 0.5])

    mat = c1.selectbox(
        "Matériau",
        list(materiaux.keys()),
        index=list(materiaux.keys()).index(couche["materiau"]),
        key=f"mat_{i}",
    )
    st.session_state.couches[i]["materiau"] = mat

    ep_disabled = mat == "Géotextile"
    ep = c2.number_input(
        "Épaisseur (cm)",
        min_value=0,
        value=couche.get("epaisseur_cm", 0),
        key=f"ep_{i}",
        disabled=ep_disabled,
    )
    st.session_state.couches[i]["epaisseur_cm"] = 0 if ep_disabled else ep

    if mat in liste_lie:
        joint = c3.radio("Joint", ["Sable", "Ciment"], key=f"joint_{i}", horizontal=True)
        st.session_state.couches[i]["joint"] = joint
    elif mat == "Indéfini":
        impact = c3.number_input(
            "Impact (kg CO₂e/m³)",
            min_value=0.0,
            value=couche.get("impact", 100.0),
            key=f"imp_{i}",
        )
        st.session_state.couches[i]["impact"] = impact

    if c4.button("🗑️", key=f"del_{i}"):
        st.session_state.couches.pop(i)
        st.rerun()

# Bouton d’ajout
if st.button("➕ Ajouter une couche"):
    st.session_state.couches.append({"materiau": "Indéfini", "epaisseur_cm": 5})
    st.rerun()

st.markdown("---")

# -------------------------------------------------
# Calculs
# -------------------------------------------------
total = empreinte_totale(surface_revetue)
par_m2 = total / surface_batiment
st.success(f"Empreinte totale : **{total:,.1f} kg CO₂e**")
st.success(f"Empreinte par m² de SRE : **{par_m2:,.2f} kg CO₂e/m²**")

# -------------------------------------------------
# Histogramme empilé : gauche = kg CO₂e/m², droite = total
# -------------------------------------------------
fig, ax1 = plt.subplots(figsize=(7, 4))
cumul = 0.0
for couche in st.session_state.couches:
    imp_m2 = empreinte_couche(couche, 1.0)  # impact par m²
    ax1.bar(
        ["Revêtement total"],
        [imp_m2],
        bottom=[cumul],
        label=couche["materiau"]
    )
    cumul += imp_m2

ax1.set_ylabel("kg CO₂e / m²")
ax1.set_title("Impact carbone du revêtement")
ax1.legend(title="Couches", bbox_to_anchor=(1.05, 1), loc="upper left")

# Axe droit : total
ax2 = ax1.twinx()
total_kg = cumul * surface_revetue
ax2.set_ylabel("kg CO₂e")
ax2.set_ylim(0, total_kg)
ax2.yaxis.set_label_position("right")
ax2.yaxis.tick_right()

st.pyplot(fig)
