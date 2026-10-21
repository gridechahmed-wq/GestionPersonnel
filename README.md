# 👥 Application de Gestion du Personnel

Application de bureau développée en **Python**, avec **Tkinter** pour l'interface graphique et **SQLite** pour la gestion des données. Elle permet de gérer les employés, leurs contrats, leurs départements et leurs affectations aux projets au sein d'une entreprise.

Le projet met en pratique la programmation orientée objet (POO), la gestion d'une base de données relationnelle et la création d'une interface graphique interactive.

## ✨ Fonctionnalités

### 👤 Gestion des employés
- Ajouter, modifier et supprimer des employés.
- Gérer les informations personnelles : nom, prénom, email et adresse.
- Prendre en charge différents statuts professionnels :
  - **Salarié** : salaire mensuel.
  - **Freelance** : tarif journalier moyen (TJM) et nombre de jours travaillés.
  - **Stagiaire** : gratification mensuelle, avec prise en charge des stages non rémunérés.
- Calculer automatiquement le revenu mensuel selon le type de contrat.
- Vérifier la validité des données saisies.

### 🏢 Gestion des départements
- Créer et supprimer des départements.
- Affecter un employé à un département.
- Conserver les employés lorsqu'un département est supprimé.

### 📂 Gestion des projets
- Créer et supprimer des projets.
- Affecter plusieurs projets à un même employé.
- Gérer les relations entre employés et projets.

### 🔎 Recherche et filtrage
- Rechercher des employés par nom, prénom ou email.
- Filtrer par département, statut professionnel ou projet.
- Trier les résultats par différentes colonnes, en ordre croissant ou décroissant.

### 🗄️ Gestion des données
- Stocker les informations dans une base SQLite persistante.
- Garantir l'unicité des adresses email.
- Utiliser des clés étrangères pour préserver l'intégrité des relations.
- Gérer les erreurs liées aux contraintes de la base de données.
- Prévoir une migration des anciennes structures de tables.

### 🎨 Interface graphique
- Interface construite avec Tkinter et ttk.
- Formulaire dynamique adapté au statut professionnel.
- Tableau interactif avec tri des colonnes.
- Fenêtres de confirmation avant les suppressions.
- Raccourcis clavier pour faciliter l'utilisation.

## 🛠️ Technologies utilisées

| Technologie | Utilisation |
|---|---|
| Python | Logique métier et programmation orientée objet |
| Tkinter | Interface graphique |
| ttk | Composants graphiques et styles |
| SQLite | Stockage des données relationnelles |
| SQL | Requêtes CRUD, jointures et contraintes |

Toutes les bibliothèques utilisées dans le code sont incluses dans la bibliothèque standard de Python.

## 🧠 Concepts de programmation démontrés

Ce projet illustre plusieurs concepts fondamentaux de la programmation orientée objet :

- **Encapsulation et séparation des responsabilités** : distinction entre les modèles métier, l'accès aux données et l'interface graphique.
- **Héritage** : les classes `Salarie`, `Freelance` et `Stagiaire` héritent de la classe `Employe`.
- **Polymorphisme** : chaque type d'employé implémente sa propre méthode `calculer_revenu()`.
- **Composition** : un employé possède un objet `Contrat` et un objet `Adresse`.
- **Agrégation** : les employés peuvent être associés à des départements et à des projets.
- **Abstraction métier** : les règles de calcul et de validation sont séparées de l'interface.

Le projet met également en pratique les requêtes SQL paramétrées, les transactions, la gestion des exceptions et les contraintes d'intégrité.

## 🗃️ Structure de la base de données

La base de données `entreprise.db` comprend quatre tables principales :

| Table | Rôle |
|---|---|
| `employes` | Informations personnelles et professionnelles des employés |
| `departements` | Départements de l'entreprise |
| `projets` | Projets de l'entreprise |
| `affectations` | Relations entre employés et projets |

### Relations entre les tables

- Un département peut regrouper plusieurs employés.
- Un employé peut être associé à plusieurs projets.
- Un projet peut regrouper plusieurs employés.
- La table `affectations` assure la relation plusieurs-à-plusieurs entre les employés et les projets.

## 🎯 Objectif du projet

Ce projet a pour objectif de concevoir une application de gestion du personnel fonctionnelle tout en mettant en pratique Python, la programmation orientée objet, les bases de données relationnelles et le développement d'interfaces graphiques.

Il constitue un projet pratique pour démontrer des compétences en développement Python, en conception logicielle et en gestion des données.

---

**Technologies :** Python · Tkinter · SQLite · SQL · Programmation orientée objet

