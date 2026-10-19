# 👥 Gestion du personnel

Application de bureau en **Python** avec interface **Tkinter** et base de données **SQLite** pour gérer les employés, leurs contrats, leurs adresses, leurs départements et leurs projets.

Ce projet met en pratique les concepts fondamentaux de la **programmation orientée objet** : héritage, composition et agrégation.

## ✨ Fonctionnalités

- **CRUD complet** sur les employés : ajout, modification (double-clic), suppression
- **Trois types de collaborateurs**, chacun avec son propre calcul de revenu :
  - *Salarié* : salaire mensuel
  - *Freelance* : TJM × jours travaillés
  - *Stagiaire* : gratification mensuelle (ou « Stage non rémunéré »)
- **Gestion des départements et des projets** (création, suppression)
- **Affectation multiple** d'un employé à plusieurs projets
- **Recherche** par nom, prénom ou email
- **Filtres** par département et par statut
- **Tri** par colonne en cliquant sur les en-têtes (ascendant / descendant)
- **Validation de la saisie** (email, montant, jours travaillés)
- **Confirmation** avant toute suppression
- **Intégrité des données** : transactions atomiques et clés étrangères activées

## 🧱 Concepts POO illustrés

| Concept | Où ? |
|---|---|
| **Héritage** | `Salarie`, `Freelance`, `Stagiaire` héritent de `Employe` et redéfinissent `calculer_revenu()` |
| **Polymorphisme** | `revenu_affiche` est surchargé dans `Stagiaire` |
| **Composition** | `Contrat` et `Adresse` n'existent que pour un employé (`ON DELETE CASCADE`) |
| **Agrégation** | `Departement` et `Projet` existent indépendamment des employés (`ON DELETE SET NULL` / table d'association) |
| **Propriétés** | `revenu_mensuel`, `revenu_affiche` |

## 🗄️ Schéma de la base de données
