# -*- coding: utf-8 -*-
"""
Created on Tue Sep 23 08:47:28 2025

@author: lucile.schulthe
"""

import streamlit as st
import matplotlib.pyplot as plt
import copy
import uuid



# -------------------------------------------------
# Base de données matériaux
# -------------------------------------------------
materiaux = {
    "Gravier": {"densite": 1500, "impact": 0.01761},
    "Béton": {"densite": 2350, "impact": 0.1088},
    "Enrobé bitumineux": {"densite": 2400, "impact": 0.1154},  
    "Pavé béton préfabriquée": {"densite": 2300, "impact": 0.2087},
    "Grille béton préfabriquée": {"densite": 2300, "impact": 0.2087},
    "Pavé en pierre": {"densite": 2500, "impact": 0.0957+0.0848},
    "Dalle en pierre": {"densite": 2750, "impact": 0.407},
    "Dalle en pierre polie": {"densite": 2750, "impact": 0.475},
    "Géotextile": {"densite": 1, "impact": 1.3},
    "Béton maigre": {"densite": 2150, "impact": 0.0628},
    "Granulés de béton": {"densite": 1550, "impact": 0.01392},
    "Grave": {"densite": 1500, "impact": 0.01761},
    "Indéfini": {"densite": 1, "impact": 0},
}

impact_excavation = 0.43      # kg CO₂e / m³
impact_sable     = 1500 * 0.01565  # kg CO₂e / m³
impact_ciment    = 1550 * 0.26  # kg CO₂e / m³
impact_asphalt=0.8375 # kg CO₂e / kg
impact_granulat=0.003012
impact_transport_fin=0.046+0.019



pavements = {
    "Revêtement bitumineux": [
        {"materiau": "Enrobé bitumineux", "epaisseur_cm": 7},
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
        {"materiau": "Pavé en pierre","epaisseur_cm": 8},
        {"materiau": "Gravier",     "epaisseur_cm": 3},
        {"materiau": "Grave",       "epaisseur_cm": 25},
    ],
    "Revêtement dalle en pierre naturelle": [
        {"materiau": "Dalle en pierre polie","epaisseur_cm": 4},
        {"materiau": "Gravier",              "epaisseur_cm": 3},
        {"materiau": "Grave",                "epaisseur_cm": 25},
    ],
    "Revêtement dalle en pierre naturelle, mixte": [
        {"materiau": "Dalle en pierre polie","epaisseur_cm": 4},
        {"materiau": "Granulés de béton",    "epaisseur_cm": 6},
        {"materiau": "Béton maigre",         "epaisseur_cm": 12},
        {"materiau": "Grave",                "epaisseur_cm": 10},
    ],
    "Revêtement béton préfabriqué": [
        {"materiau": "Pavé béton préfabriquée","epaisseur_cm": 8},
        {"materiau": "Gravier",               "epaisseur_cm": 3},
        {"materiau": "Grave",                 "epaisseur_cm": 25},
    ],
    "Revêtement grille de béton préfabriquée": [
        {"materiau": "Grille béton préfabriquée","epaisseur_cm": 4},
        {"materiau": "Gravier",                 "epaisseur_cm": 3},
        {"materiau": "Grave",                   "epaisseur_cm": 25},
    ],
    "Indéfini": [
        {"materiau": "Indéfini","epaisseur_cm": 30},
    ],
}

liste_lie = (
    "Pavé béton préfabriqué",
    "Pavé en pierre",
    "Dalle en pierre",
    "Dalle en pierre polie",
)

liste_pierre = (
    "Pavé en pierre",
    "Dalle en pierre",
    "Dalle en pierre polie",
)

liste_beton = {
    "Standard": {"densite": 2350, "impact": 0.1088},    
    "Portland": {"densite": 2350, "impact": 0.118},
    "CEM II/B": {"densite": 2350, "impact": 0.101},  
    "CEM II/A": {"densite": 2350, "impact": 0.105},
    "CEM ZN/D": {"densite": 2350, "impact": 0.089},  
    "CEM III/A": {"densite": 2350, "impact": 0.080},   
    }

origin_pierre = {
    "Mix": {"imp_trans": 0},
    "Suisse": {"imp_trans": -0.0848},
    "Europe": {"imp_trans": -0.0048},
    "Outre-mer": {"imp_trans": 0.0267},
    
}
# -------------------------------------------------
# Fonctions de calcul
# -------------------------------------------------

def empreinte_couche(couche):     #"""Impact carbone d'une couche en kg CO₂e pour la surface donnée."""
    mat = couche["materiau"]    
        
    impact = couche.get("impact", 0) * materiaux[mat]["densite"]*couche.get("epaisseur_cm", 0)/100
    
    if mat == "Géotextile":
        impact = materiaux[mat]["impact"]
        
        
    if mat in liste_lie:
        joint = couche.get("joint", "Sable")
        impact_joint = impact_sable if joint == "Sable" else impact_ciment
        impact += impact_joint * 0.05*couche.get("epaisseur_cm", 0)/100  # ex. +5 % lié au joint
    
    return impact # kg CO₂e / m²

def empreinte_totale(couches):
    total = sum(empreinte_couche(c) for c in couches)
    profondeur = sum(c.get("epaisseur_cm", 0) for c in couches if c.get("materiau") != "Géotextile") / 100.0
    total += profondeur * impact_excavation
    return total

# -----------------------
# Session state
# -----------------------
if "instances" not in st.session_state:
    # {id: {"nom": str, "surface": float, "couches": list}}
    st.session_state.instances = {}


# -------------------------------------------------
# Interface
# -------------------------------------------------
st.title("Calculateur d'empreinte carbone de surface extérieure")


# Ajouter un nouveau revêtement

type_choisi = st.selectbox("Type de composition de base:", list(pavements.keys()))
if st.button("➕ Ajouter cette composition"):
    new_id = str(uuid.uuid4())
    st.session_state.instances[new_id] = {
        "nom": type_choisi,
        "surface": 1.0,  # valeur initiale
        "couches": copy.deepcopy(pavements[type_choisi]),
    }



# Affichage des instances
st.markdown("---")
if not st.session_state.instances:
    st.info("Ajoutez cette composition")

else:
    tabs = st.tabs([f"{v['nom']}" for i, v in st.session_state.instances.items()])

    for tab, (inst_id, inst) in zip(tabs, st.session_state.instances.items()):
        with tab:
            # Champ texte pour changer le nom
            new_name = st.text_input(
                "Nom du revêtement",
                value=inst["nom"],
                key=f"name_{inst_id}"   # clé unique
            )
            # Met à jour la session si modifié
            st.session_state.instances[inst_id]["nom"] = new_name

            # Surface propre à ce revêtement
            inst["surface"] = st.number_input(
                "Surface de ce revêtement (m²)",
                min_value=0.0,
                value=inst["surface"],
                key=f"{inst_id}_surf",
            )
            st.markdown("---")
            
            # Ajouter ou supprimer
            if st.button("➕ Ajouter une couche", key=f"add2_{inst_id}"):
                inst["couches"].insert(0, {"materiau": "Indéfini", "epaisseur_cm": 5})

            # Edition des couches
            for idx, couche in enumerate(inst["couches"]):
                c1, c2, c3, c4, c5= st.columns([3, 1.3, 2.4, 1.5,0.5])
                mat = c1.selectbox(
                    "Matériau",
                    list(materiaux.keys()),
                    index=list(materiaux.keys()).index(couche["materiau"]),
                    key=f"{inst_id}_mat_{idx}",
                )
                couche["materiau"] = mat
                
                ep_disabled = mat == "Géotextile"
                ep = c2.number_input(
                    "Épaisseur (cm)",
                    min_value=0,
                    value=couche.get("epaisseur_cm", 0),
                    key=f"{inst_id}_ep_{idx}",
                    disabled=ep_disabled,
                )
                couche["epaisseur_cm"] = 0 if ep_disabled else ep
                
                couche["impact"]=materiaux[mat]["impact"]
                
                if mat in liste_lie:
                    joint = c3.radio("Joint", ["Sable", "Ciment"], key=f"{inst_id}_joint_{idx}", horizontal=True)
                    couche["joint"] = joint
                    

                    if mat !="Pavé béton préfabriqué":
                        
                        origin = c4.selectbox("Origine", 
                        list(origin_pierre.keys()),
                        key=f"{inst_id}_cim_{idx}",
                    )                    
                    couche["impact"]+=origin_pierre[origin]["imp_trans"]
                        
                        
                    
                elif mat == "Indéfini":
                    val_imp = c3.number_input(
                        "Impact (kgCO₂e/m³)",
                        min_value=0.0,
                        value=couche.get("val_impact", 100.0),
                        key=f"{inst_id}_imp_{idx}",
                    )
                    couche["impact"] = val_imp
                    
                elif mat=="Enrobé bitumineux":
                    taux_recycle=c3.number_input(
                        "Taux Gran. recyclés (%)",
                        min_value=0,
                        value=couche.get("taux", 0),
                        key=f"{inst_id}_recycle_{idx}",
                    )

                    taux_asphalt=c4.number_input(
                        "Taux d'asphalt (%)",
                        min_value=1.0,
                        value=couche.get("taux", 5.6),
                        key=f"{inst_id}_taux_{idx}",
                    )
                    couche["impact"]=(impact_asphalt*taux_asphalt/100+(1-taux_asphalt/100)*impact_granulat)*(1-taux_recycle/100)+impact_transport_fin
                
                elif mat=="Béton":
                    cim= c3.selectbox(
                        "Type ciment",
                        list(liste_beton.keys()),
                        key=f"{inst_id}_cim_{idx}",
                    )                    
                    couche["impact"]=liste_beton[cim]["impact"]
                    
                elif mat=="Grille béton préfabriquée":
                    taux_empty=c3.number_input(
                        "Vide (%)",
                        min_value=0,
                        value=couche.get("taux", 40),
                        key=f"{inst_id}_recycle_{idx}",
                    )              
                    couche["impact"]=(1-taux_empty/100)*materiaux[mat]["impact"]
                
                
   

                
                if c5.button("➖", key=f"{inst_id}_del_{idx}"):
                    inst["couches"].pop(idx)




            # Ajouter ou supprimer
            if st.button("➕ Ajouter une couche", key=f"add_{inst_id}"):
                inst["couches"].append({"materiau": "Indéfini", "epaisseur_cm": 5})
                
           
            st.markdown("---")
            k1, k2= st.columns([5, 5])     
            if k1.button("➖ Supprimer cette composition", key=f"del_{inst_id}"):
                del st.session_state.instances[inst_id]

    # Bouton de duplication
            if k2.button("➕Dupliquer cette composition", key=f"dup_{inst_id}"):
                # Crée un nouvel identifiant unique
                new_id = str(uuid.uuid4())
                # Copie profonde de l'instance
                st.session_state.instances[new_id] = {
                    "nom": inst["nom"] + " (copie)",
                    "surface": inst["surface"],
                    # on copie aussi les couches pour pouvoir les modifier indépendamment
                    "couches": [c.copy() for c in inst["couches"]],
                }

# -----------------------
# Résultats comparatifs
# -----------------------
st.markdown("---")
st.header("Comparaison")

# -------------------------------------------------
# Calculs
# -------------------------------------------------
data = []
sumtotal=0
sumsurface=0
for inst_id, inst in st.session_state.instances.items():
    par_m2 = empreinte_totale(inst["couches"])
    total =par_m2*inst["surface"], 
    data.append((f"{inst['nom']}", inst["surface"], total[0], par_m2))
    sumtotal+=total[0]
    sumsurface+=inst["surface"]

   
data.append(("Total", sumsurface, sumtotal, sumtotal/sumsurface))    



if data:
    st.table(
        [
            {
                "Composition": n,
                "Surface (m²)": f"{s:,.0f}",
                "Total (kg CO₂e)": f"{t:,.0f}",
                "Par m²": f"{pm:,.0f}",
            }
            for n, s, t, pm in data
        ]
    )



# --------------------------------------------
# Histogramme empilé multi-revêtements
# --------------------------------------------
fig1, ax1 = plt.subplots(figsize=(8, 5))

rev_labels   = []        # noms sur l’axe X
totaux_m2    = []        # total par m² pour axe droit
max_total    = 0         # pour l’échelle de l’axe droit
couleurs     = {}        # une couleur par matériau

# pour affecter une couleur unique à chaque matériau
import itertools
palette = itertools.cycle(plt.cm.tab20.colors)

for inst_id, inst in st.session_state.instances.items():
    rev_labels.append(f"{inst['nom']}")
    couches = inst["couches"]
    surface = inst.get("surface", 1.0)
    cumul_m2 = 0.0

    # pour chaque couche on empile
    for couche in reversed(couches):
        mat = couche["materiau"]
        # impact par m² de la couche
        imp_m2 = empreinte_couche(couche)   # on normalise sur 1 m²
        if mat not in couleurs:
            couleurs[mat] = next(palette)
        ax1.bar(
            rev_labels[-1],
            imp_m2,
            bottom=cumul_m2,
            color=couleurs[mat],
            label=mat
        )
        cumul_m2 += imp_m2

    # total absolu (kg) pour l’axe droit
    total_abs = cumul_m2 * surface
    totaux_m2.append(total_abs)
    max_total = max(max_total, total_abs)

# axe gauche : kg CO₂e / m²
ax1.set_ylabel("kg CO₂e / m²")
ax1.set_title("Impact carbone par composition")


ax1.set_xticklabels(rev_labels, rotation=30, ha="right", fontsize=9)

# légende unique
handles, labels = ax1.get_legend_handles_labels()
by_label = dict(zip(labels, handles))
ax1.legend(by_label.values(), by_label.keys(), bbox_to_anchor=(1.05, 1), loc="upper left")



st.pyplot(fig1)
