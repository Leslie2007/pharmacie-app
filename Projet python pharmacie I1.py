#!/usr/bin/env python
# coding: utf-8

# In[150]:


# IMPORTATION DE NUMPY ET PANDAS
import numpy as np
import pandas as pd
import streamlit as st


# In[151]:


#donnée entrées par le gérant
donnees_de_la_semaine= pd.DataFrame(
    [
        { 
            "produit": "DOLIPRANE 500mg",
            "prix_achat": 700,
            "prix_vente": 1130,
            "stock_depart": 700,
            "ventes": 210,
            "stock_reel":480,
        },
        {
            "produit": "DOLIPRANE 1000mg",
            "prix_achat": 800,
            "prix_vente": 1180,
            "stock_depart": 500,
            "ventes": 100,
            "stock_reel":390,
        },
        {
            "produit": "C-CAL",
            "prix_achat": 1200,
            "prix_vente": 1800,
            "stock_depart": 700,
            "ventes":20,
            "stock_reel":679,
        },
        {
            "produit": "MAG2",
            "prix_achat": 3500,
            "prix_vente": 4600,
            "stock_depart": 200,
            "ventes": 93,
            "stock_reel": 107,
        },
        {
            "produit": "RAPIDEX",
            "prix_achat": 3000,
            "prix_vente": 3200,
            "stock_depart": 56,
            "ventes": 23,
            "stock_reel": 33,
        },
        {
            "produit": "SPASFON",
            "prix_achat": 2100,
            "prix_vente": 2250,
            "stock_depart": 63,
            "ventes": 15,
            "stock_reel": 10,
        },
    ]
)
            


# In[154]:


def calcule_marge(df):
    #cette fonction permet de determiner le benefice de la pharmacie sur chaque produit et calcule l'ecart

    df_traite= df.copy()
    #calcule du stock qu'on aurait dû avoir
    df_traite["stock_theorique"]=(df_traite["stock_depart"]-df_traite["ventes"])
    df_traite["ecart_inventaire"]=(df_traite["stock_theorique"]-df_traite["stock_reel"])
    #calcule la marge obtenue
    df_traite["marge"]=((df_traite["prix_vente"]-df_traite["prix_achat"])/df_traite["prix_vente"])*100
    #retourne la marge et le stock theorique
    return df_traite


# In[156]:


def mettre_a_jour_stocks(df_donnees):
    #fais une copie des données
    df=df_donnees.copy()
    #calcule du stock théorique ainsi que de l'ecart de l'inventaire
    df["stock_theorique"]=df["stock_depart"]-df["ventes"]
    df["ecart_inventaire"]=df["stock_theorique"]-df["stock_reel"]
    return df


# In[158]:


class DetecteurAnomalies:
    def __init__( self, seuil_zscore=1.0, seuil_reapprovisionnement=50.0):
        #initialise le zscore, le seuil de reapprovisionnement et les statistiques d'une semaine normale
        self.seuil_zscore=seuil_zscore
        self.seuil_reapprovisionnement=seuil_reapprovisionnement
        self.stats_normales={}
        
    def entrainer(self, df_historique):
        # attribuer à la liste metrique la marge faite, les ventes et l'ecart type de chaque produit
        metrique=["marge", "ventes", "ecart_inventaire"]
        # determiner la moyenne et l'ecart type historique
        for colonne in metrique:
            self.stats_normales[colonne]={
                "moyenne":df_historique[colonne].mean(),
                "ecart_type": df_historique[colonne].std(),
            }

    def analyser_donnees(self,df_donnees):
        # initialiser les differents types d'alertes
         alertes_stock=[]
         alertes_marge=[]
         alertes_ventes=[]
         alertes_inventaire=[]
        # ALERTES EN CAS DE FAIBLES STOCK
         for index,row in df_donnees.iterrows():
             produit=row["produit"]
             stock_restant=row["stock_reel"]
             if stock_restant<self.seuil_reapprovisionnement:
                 alertes_stock.append(f"[{produit}]:plus que {stock_restant} unité en réserve! Passer commande.")
                 
          # ALERTES EN CAS DE MARGE TROP FAIBLE       
             std_marge=self.stats_normales["marge"]["ecart_type"]
             if std_marge>0:
                 zmarge=(row["marge"]-self.stats_normales["marge"]["moyenne"])/std_marge
             else:
                 if row["marge"]>=self.stats_normales["marge"]["moyenne"]:
                     zmarge=0
                 else:
                     zmarge=0.99
             if row["marge"]<25:
                alertes_marge.append(f"[{produit}] Marge anormalement  basse ({row['marge']:.1f}%). Erreur de prix possible ?")
                 
           # ALERTES EN CAS DE MAUVAIS INVENTAIRE      
             std_inv=self.stats_normales["ecart_inventaire"]["ecart_type"]
             if std_inv>0:
                 z_inventaire=( row["ecart_inventaire"]-self.stats_normales["ecart_inventaire"]["moyenne"])/self.stats_normales["ecart_inventaire"]["ecart_type"]
             else:
                 z_inventaire=0
             if z_inventaire> self.seuil_zscore:
                alertes_inventaire.append(f"[{produit}] Ecart d'inventaire important (Théorique: {row['stock_theorique']}, Réel:{row['stock_reel']}). Vol, casse ou erreur de saisie ?")
             
             #ALERTES EN CAS DE VENTES PLUS ELEVEE QUE LA NORMALE    
             std_ventes=self.stats_normales["ventes"]["ecart_type"]
             if std_ventes>0:
                 z_ventes= ( row["ventes"]-self.stats_normales["ventes"]["moyenne"])/self.stats_normales["ventes"]["ecart_type"]
             else:
                 z_ventes=0
             if z_ventes> self.seuil_zscore:
                alertes_ventes.append(f"[{produit}] Ventes très élevées ({row['ventes']} unités). Le médicament sort plus que d'ordinaire!")
                 
               #RETOUR DES DIFFERENTS ALERTES  
         return {"STOCK FAIBLE": alertes_stock,
                 "MARGE BASSE": alertes_marge,
                 "ANOMALIES INVENTAIRE": alertes_inventaire,
                 "ANOMALIES VENTES": alertes_ventes,}


# In[166]:


if __name__=="__main__":

    # DONNEES HABITUELLES
    np.random.seed(42)
    historique=pd.DataFrame(
         {
            "prix_achat":[6.5]*100,
            "prix_vente":[10.0]*100,
            "stock_depart":[70]*100,
            "ventes": np.random.normal(loc=20, scale=3, size=100),
            "stock_reel": [ 70-v-np.random.normal(1,0.5) for v in range(100)],})
    
    # DETERMINATION DES DONNEES HABITUELLES
    historique=mettre_a_jour_stocks(historique)
    historique_calcule=calcule_marge(historique)
    detecteur=DetecteurAnomalies(seuil_zscore=2.0)
    detecteur.entrainer(historique_calcule)
    
    # DETERMINATION DES DONNEES DE LA SEMAINES
    donnees_de_la_semaine=mettre_a_jour_stocks(donnees_de_la_semaine)
    donnees_de_la_semaine_calculee=calcule_marge(donnees_de_la_semaine)
    alertes_de_la_semaine=detecteur.analyser_donnees(donnees_de_la_semaine_calculee)
    st.title(" =========RAPPORT DE LA SEMAINE==========")
    st.subheader("Données analysées")
    st.dataframe(donnees_de_la_semaine)

    #COMPARAISONS DES DONNEES HABITUELLES ET DE LA SEMAINES ET MISE EN PLACE DES ALERTES
    if alertes_de_la_semaine:
        st.subheader("ALERTES DETECTEES")
        for categorie, liste_alertes in alertes_de_la_semaine.items():
            if liste_alertes:
                st.markdown(f"### {categorie}")
                for alerte in liste_alertes:
                    st.warning(alerte)
    else:
        st.success(f"{categorie}:Rien à signaler, tout est normal!")
    
    


# In[ ]:





# In[ ]:




