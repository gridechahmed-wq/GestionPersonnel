import sqlite3
import tkinter as tk


# =====================================================================
# ÉTAPE 1 : MODÈLES MÉTIER (héritage, composition, agrégation)
# =====================================================================
class Contrat:
    """COMPOSITION : le contrat n'existe que pour un employé."""

    def __init__(self, type_contrat, montant, jours_travailles=0):
        self.type_contrat = type_contrat
        self.montant = montant
        self.jours_travailles = jours_travailles


class Adresse:
    """COMPOSITION : l'adresse est créée par l'employé et disparaît avec lui."""

    def __init__(self, rue="", ville=""):
        self.rue = rue
        self.ville = ville


class Departement:
    """AGRÉGATION : regroupe des employés qui existent sans lui."""

    def __init__(self, id_dept, nom):
        self.id_dept = id_dept
        self.nom = nom
        self.employes = []

    def ajouter_employe(self, employe):
        self.employes.append(employe)
        employe.departement = self


class Projet:
    """AGRÉGATION : un projet existe sans ses employés (et inversement)."""

    def __init__(self, id_projet, nom):
        self.id_projet = id_projet
        self.nom = nom
        self.employes = []

    def ajouter_employe(self, employe):
        self.employes.append(employe)
        employe.projets.append(self)


class Employe:
    """Classe de base : les sous-classes définissent calculer_revenu()."""

    def __init__(self, id_emp, nom, prenom, email, contrat, departement=None,
                 rue="", ville=""):
        self.id_emp = id_emp
        self.nom = nom
        self.prenom = prenom
        self.email = email
        self.contrat = contrat  # composition
        self.adresse = Adresse(rue, ville)  # composition : créée par l'employé lui-même
        self.departement = departement  # agrégation
        self.projets = []  # agrégation : liste d'objets Projet

    def calculer_revenu(self):
        raise NotImplementedError("À implémenter dans la sous-classe.")

    @property
    def revenu_mensuel(self):
        """Revenu du mois : s'utilise comme un attribut (emp.revenu_mensuel)."""
        return self.calculer_revenu()

    @property
    def revenu_affiche(self):
        """Texte affiché dans la liste (les sous-classes peuvent le changer)."""
        return f"{self.revenu_mensuel:,.2f} €"


class Salarie(Employe):
    """HÉRITAGE : revenu = salaire mensuel."""

    def calculer_revenu(self):
        return self.contrat.montant


class Freelance(Employe):
    """HÉRITAGE : revenu = TJM x jours travaillés."""

    def calculer_revenu(self):
        return round(self.contrat.montant * self.contrat.jours_travailles, 2)


class Stagiaire(Employe):
    """HÉRITAGE : revenu = gratification mensuelle (0 = stage non rémunéré)."""

    def calculer_revenu(self):
        return self.contrat.montant

    @property
    def revenu_affiche(self):
        if self.revenu_mensuel == 0:
            return "Stage non rémunéré"
        return super().revenu_affiche


TYPES_EMPLOYES = {"Salarié": Salarie, "Freelance": Freelance, "Stagiaire": Stagiaire}


def creer_employe(statut, id_emp, nom, prenom, email, montant, jours, departement=None,
                  rue="", ville=""):
    contrat = Contrat(statut, montant, jours)
    return TYPES_EMPLOYES[statut](id_emp, nom, prenom, email, contrat, departement,
                                  rue, ville)


# =====================================================================
# ÉTAPE 2 : VALIDATION
# =====================================================================
def email_valide(email):
    if " " in email or email.count("@") != 1:
        return False
    local, domaine = email.split("@")
    return (bool(local)
            and "." in domaine
            and not domaine.startswith(".")
            and not domaine.endswith("."))


def valider_saisie(nom, prenom, email, statut, montant_txt, jours_txt):
    """Retourne (montant, jours) ou lève ValueError."""
    if not nom or not prenom or not email or not montant_txt:
        raise ValueError("Tous les champs obligatoires doivent être remplis.")
    if not email_valide(email):
        raise ValueError("L'adresse email n'est pas valide.")
    try:
        montant = float(montant_txt.replace(",", "."))
    except ValueError:
        raise ValueError("Le montant doit être un nombre.")
    if not 0 <= montant <= 100000000:
        raise ValueError("Le montant doit être compris entre 0 et 100 000 000 €.")
    if round(montant, 2) != montant:
        raise ValueError("Le montant ne peut pas avoir plus de 2 décimales.")

    jours = 0
    if statut == "Freelance":
        try:
            jours = int(jours_txt)
        except ValueError:
            raise ValueError("Les jours travaillés doivent être un entier.")
        if not 1 <= jours <= 31:
            raise ValueError("Les jours travaillés doivent être entre 1 et 31.")
    return montant, jours


# =====================================================================
# ÉTAPE 3 : BASE DE DONNÉES
# =====================================================================
# Tri SQL : clé de colonne -> expressions ORDER BY (liste blanche)
TRIS_SQL = {
    "id": ("e.id",),
    "nom": ("e.nom COLLATE NOCASE", "e.prenom COLLATE NOCASE"),
    "prenom": ("e.prenom COLLATE NOCASE", "e.nom COLLATE NOCASE"),
    "email": ("e.email COLLATE NOCASE",),
    "statut": ("c.type_contrat",),
    "dept": ("d.nom COLLATE NOCASE",),
    "ville": ("a.ville COLLATE NOCASE",),
    "projets": ("(SELECT COUNT(*) FROM affectations x WHERE x.employe_id = e.id)",),
    "revenu": ("c.revenu_mensuel",),
}


SCHEMA = """
CREATE TABLE IF NOT EXISTS departements
(
    id  INTEGER PRIMARY KEY AUTOINCREMENT,
    nom TEXT NOT NULL UNIQUE
);
CREATE TABLE IF NOT EXISTS projets
(
    id  INTEGER PRIMARY KEY AUTOINCREMENT,
    nom TEXT NOT NULL UNIQUE
);
CREATE TABLE IF NOT EXISTS employes
(
    id             INTEGER PRIMARY KEY AUTOINCREMENT,
    nom            TEXT NOT NULL,
    prenom         TEXT NOT NULL,
    email          TEXT NOT NULL UNIQUE,
    departement_id INTEGER,
    FOREIGN KEY (departement_id) REFERENCES departements (id)
        ON DELETE SET NULL
);
CREATE TABLE IF NOT EXISTS contrats
(
    id               INTEGER PRIMARY KEY AUTOINCREMENT,
    employe_id       INTEGER NOT NULL UNIQUE,
    type_contrat     TEXT    NOT NULL,
    montant          REAL    NOT NULL CHECK (montant >= 0),
    revenu_mensuel   REAL    NOT NULL,
    jours_travailles INTEGER NOT NULL DEFAULT 0,
    FOREIGN KEY (employe_id) REFERENCES employes (id)
        ON DELETE CASCADE
);
CREATE TABLE IF NOT EXISTS adresses
(
    id         INTEGER PRIMARY KEY AUTOINCREMENT,
    employe_id INTEGER NOT NULL UNIQUE,
    rue        TEXT    NOT NULL DEFAULT '',
    ville      TEXT    NOT NULL DEFAULT '',
    FOREIGN KEY (employe_id) REFERENCES employes (id)
        ON DELETE CASCADE
);
CREATE TABLE IF NOT EXISTS affectations
(
    employe_id INTEGER NOT NULL,
    projet_id  INTEGER NOT NULL,
    PRIMARY KEY (employe_id, projet_id),
    FOREIGN KEY (employe_id) REFERENCES employes (id)
        ON DELETE CASCADE,
    FOREIGN KEY (projet_id) REFERENCES projets (id)
        ON DELETE CASCADE
);
"""


class Depot:
    def __init__(self, fichier="entreprise.db"):
        self.fichier = fichier
        self._creer_tables()

    def _connexion(self):
        conn = sqlite3.connect(self.fichier)
        conn.execute("PRAGMA foreign_keys = ON")  # sinon SQLite ignore les clés étrangères
        return conn

    def _creer_tables(self):
        conn = None
        try:
            conn = self._connexion()
            conn.executescript(SCHEMA)
            conn.commit()
        finally:
            if conn:
                conn.close()


    def _ecrire(self, sql, params=(), message_doublon="Valeur déjà existante."):
        conn = None
        try:
            conn = self._connexion()
            conn.execute(sql, params)
            conn.commit()
        except sqlite3.IntegrityError:
            raise ValueError(message_doublon)
        finally:
            if conn:
                conn.close()

    # ----- départements -----
    def lister_departements(self):
        conn = None
        try:
            conn = self._connexion()
            lignes = conn.execute("SELECT id, nom FROM departements ORDER BY nom").fetchall()
            return [Departement(i, n) for i, n in lignes]
        finally:
            if conn:
                conn.close()

    def ajouter_departement(self, nom):
        self._ecrire("INSERT INTO departements (nom) VALUES (?)", (nom,),
                     "Ce département existe déjà.")

    def supprimer_departement(self, id_dept):
        # Les employés restent : departement_id passe à NULL (agrégation).
        self._ecrire("DELETE FROM departements WHERE id = ?", (id_dept,))

    # ----- projets -----
    def lister_projets(self):
        conn = None
        try:
            conn = self._connexion()
            lignes = conn.execute("SELECT id, nom FROM projets ORDER BY nom").fetchall()
            return [Projet(i, n) for i, n in lignes]
        finally:
            if conn:
                conn.close()

    def ajouter_projet(self, nom):
        self._ecrire("INSERT INTO projets (nom) VALUES (?)", (nom,),
                     "Ce projet existe déjà.")

    def supprimer_projet(self, id_projet):
        # Seules les affectations disparaissent (CASCADE) : les employés restent.
        self._ecrire("DELETE FROM projets WHERE id = ?", (id_projet,))

    # ----- employés -----
    @staticmethod
    def _erreur_integrite(e):
        if "email" in str(e):
            return ValueError("Cet email est déjà utilisé.")
        return ValueError(f"Donnée refusée par la base : {e}")

    def ajouter_employe(self, employe, id_dept):
        conn = None
        try:
            conn = self._connexion()
            curseur = conn.execute(
                "INSERT INTO employes (nom, prenom, email, departement_id) VALUES (?, ?, ?, ?)",
                (employe.nom, employe.prenom, employe.email, id_dept))
            id_emp = curseur.lastrowid
            contrat = employe.contrat
            conn.execute(
                "INSERT INTO contrats (employe_id, type_contrat, montant, "
                "jours_travailles, revenu_mensuel) VALUES (?, ?, ?, ?, ?)",
                (id_emp, contrat.type_contrat, contrat.montant,
                 contrat.jours_travailles, employe.revenu_mensuel))
            conn.execute(
                "INSERT INTO adresses (employe_id, rue, ville) VALUES (?, ?, ?)",
                (id_emp, employe.adresse.rue, employe.adresse.ville))
            conn.executemany(
                "INSERT INTO affectations (employe_id, projet_id) VALUES (?, ?)",
                [(id_emp, p.id_projet) for p in employe.projets])
            conn.commit()  # tout réussit ensemble ou rien n'est écrit
        except sqlite3.IntegrityError as e:
            raise self._erreur_integrite(e)
        finally:
            if conn:
                conn.close()

    def modifier_employe(self, employe, id_dept):
        conn = None
        try:
            conn = self._connexion()
            curseur = conn.execute(
                "UPDATE employes SET nom = ?, prenom = ?, email = ?, departement_id = ? "
                "WHERE id = ?",
                (employe.nom, employe.prenom, employe.email, id_dept, employe.id_emp))
            if curseur.rowcount == 0:
                raise ValueError("Cet employé n'existe plus.")
            contrat = employe.contrat
            conn.execute(
                "UPDATE contrats SET type_contrat = ?, montant = ?, jours_travailles = ?, revenu_mensuel = ? WHERE employe_id = ?",
                (contrat.type_contrat, contrat.montant, contrat.jours_travailles,
                 employe.revenu_mensuel, employe.id_emp))
            conn.execute(
                "INSERT OR REPLACE INTO adresses (employe_id, rue, ville) VALUES (?, ?, ?)",
                (employe.id_emp, employe.adresse.rue, employe.adresse.ville))
            conn.execute("DELETE FROM affectations WHERE employe_id = ?", (employe.id_emp,))
            conn.executemany(
                "INSERT INTO affectations (employe_id, projet_id) VALUES (?, ?)",
                [(employe.id_emp, p.id_projet) for p in employe.projets])
            conn.commit()
        except sqlite3.IntegrityError as e:
            raise self._erreur_integrite(e)
        finally:
            if conn:
                conn.close()

    def supprimer_employe(self, id_emp):
        # Contrat, adresse (composition) et affectations disparaissent en CASCADE ;
        # les projets, eux, restent (agrégation).
        self._ecrire("DELETE FROM employes WHERE id = ?", (id_emp,))

    def lister_employes(self, recherche="", dept_filtre=None, statut=None,
                        tri="nom", decroissant=False):
        if tri not in TRIS_SQL:
            raise ValueError("Colonne de tri inconnue.")
        sens = "DESC" if decroissant else "ASC"
        ordre = ", ".join(f"{colonne} {sens}" for colonne in TRIS_SQL[tri]) + ", e.id"

        motif = f"%{recherche}%"
        conditions = ["(e.nom LIKE ? OR e.prenom LIKE ? OR e.email LIKE ?)"]
        params = [motif, motif, motif]
        if dept_filtre is not None:
            if dept_filtre == 0:
                conditions.append("e.departement_id IS NULL")
            else:
                conditions.append("e.departement_id = ?")
                params.append(dept_filtre)
        if statut is not None:
            conditions.append("c.type_contrat = ?")
            params.append(statut)

        sql = f"""
            SELECT e.id, e.nom, e.prenom, e.email,
                   c.type_contrat, c.montant, c.jours_travailles,
                   d.id, d.nom, a.rue, a.ville
            FROM employes e
            JOIN contrats c ON c.employe_id = e.id
            LEFT JOIN adresses a ON a.employe_id = e.id
            LEFT JOIN departements d ON d.id = e.departement_id
            WHERE {" AND ".join(conditions)}
            ORDER BY {ordre}
        """
        conn = None
        try:
            conn = self._connexion()
            lignes = conn.execute(sql, params).fetchall()
            affectations = conn.execute(
                "SELECT af.employe_id, p.id, p.nom FROM affectations af "
                "JOIN projets p ON p.id = af.projet_id ORDER BY p.nom").fetchall()
        finally:
            if conn:
                conn.close()

        projets = {}
        projets_par_employe = {}
        for id_e, id_p, nom_p in affectations:
            if id_p not in projets:
                projets[id_p] = Projet(id_p, nom_p)
            projets_par_employe.setdefault(id_e, []).append(projets[id_p])

        departements = {}
        resultat = []
        for id_e, nom, prenom, email, st, montant, jours, id_d, nom_d, rue, ville in lignes:
            employe = creer_employe(st, id_e, nom, prenom, email, montant, jours,
                                    rue=rue or "", ville=ville or "")
            if id_d is not None:
                if id_d not in departements:
                    departements[id_d] = Departement(id_d, nom_d)
                departements[id_d].ajouter_employe(employe)
            for projet in projets_par_employe.get(id_e, []):
                projet.ajouter_employe(employe)
            resultat.append(employe)
        return resultat


# =====================================================================
# ÉTAPE 4 : INTERFACE TKINTER
# =====================================================================
TOUS = "Tous"
AUCUN = "(aucun)"

# (clé de tri, titre affiché, largeur en caractères)
COLONNES = (
    ("id", "ID", 4),
    ("nom", "Nom", 12),
    ("prenom", "Prénom", 10),
    ("email", "Email", 22),
    ("statut", "Statut", 10),
    ("dept", "Département", 12),
    ("ville", "Ville", 10),
    ("projets", "Projets", 14),
    ("revenu", "Revenu", 20),
)


def formater_ligne(valeurs):
    morceaux = []
    derniere = len(COLONNES) - 1
    for i, (valeur, (_, _, largeur)) in enumerate(zip(valeurs, COLONNES)):
        texte = str(valeur)[:largeur - 1]
        morceaux.append(texte.rjust(largeur) if i == derniere else texte.ljust(largeur))
    return "".join(morceaux)


class Application(tk.Tk):
    def __init__(self, depot):
        super().__init__()
        self.title("Gestion du personnel")
        self.depot = depot
        self.employes_affiches = []
        self.departements = []
        self.projets = []
        self.employe_en_edition = None
        self.fenetre_confirmation = None
        self.tri_col = 1
        self.tri_desc = False

        self.var_statut = tk.StringVar(value="Salarié")
        self.var_dept = tk.StringVar()
        self.var_recherche = tk.StringVar()
        self.var_filtre_dept = tk.StringVar(value=TOUS)
        self.var_filtre_statut = tk.StringVar(value=TOUS)

        self._construire_formulaire()
        self._construire_liste()
        self.lbl_message = tk.Label(self, text="", anchor="w")
        self.lbl_message.pack(fill="x", padx=12, pady=(0, 8))

        self.var_statut.trace_add("write", lambda *a: self._maj_formulaire())
        for var in (self.var_recherche, self.var_filtre_dept, self.var_filtre_statut):
            var.trace_add("write", lambda *a: self.rafraichir_liste())

        self._maj_formulaire()
        self.rafraichir_departements()
        self.rafraichir_projets()
        self.rafraichir_liste()

    # ----- construction -----
    def _construire_formulaire(self):
        self.cadre_form = tk.LabelFrame(self, padx=10, pady=8)
        cadre = self.cadre_form
        cadre.pack(fill="x", padx=12, pady=8)

        self.ent_nom = self._champ(cadre, "Nom :", 0, 0)
        self.ent_prenom = self._champ(cadre, "Prénom :", 0, 2)
        self.ent_email = self._champ(cadre, "Email :", 1, 0)

        tk.Label(cadre, text="Département :").grid(row=1, column=2, sticky="w")
        self.menu_dept = tk.OptionMenu(cadre, self.var_dept, "")
        self.menu_dept.grid(row=1, column=3, sticky="ew", padx=5, pady=2)

        tk.Label(cadre, text="Statut :").grid(row=2, column=0, sticky="w")
        tk.OptionMenu(cadre, self.var_statut, *TYPES_EMPLOYES.keys()).grid(
            row=2, column=1, sticky="ew", padx=5, pady=2)

        self.lbl_montant = tk.Label(cadre, text="Salaire mensuel (€) :")
        self.lbl_montant.grid(row=2, column=2, sticky="w")
        self.ent_montant = tk.Entry(cadre)
        self.ent_montant.grid(row=2, column=3, padx=5, pady=2)

        self.ent_rue = self._champ(cadre, "Rue :", 3, 0)
        tk.Label(cadre, text="Jours travaillés :").grid(row=3, column=2, sticky="w")
        self.ent_jours = tk.Entry(cadre)
        self.ent_jours.grid(row=3, column=3, padx=5, pady=2)

        self.ent_ville = self._champ(cadre, "Ville :", 4, 0)
        tk.Label(cadre, text="Projets :").grid(row=4, column=2, sticky="nw")
        self.liste_projets = tk.Listbox(cadre, selectmode=tk.MULTIPLE, height=3,
                                        exportselection=False)
        self.liste_projets.grid(row=4, column=3, sticky="ew", padx=5, pady=2)

        boutons = tk.Frame(cadre)
        boutons.grid(row=5, column=0, columnspan=4, sticky="ew", pady=(8, 0))
        self.btn_valider = tk.Button(boutons, fg="white", command=self.action_valider)
        self.btn_valider.pack(side="left", fill="x", expand=True)
        self.btn_annuler = tk.Button(boutons, text="Annuler", command=self._mode_ajout)

        # Gestion des départements
        cadre_d = tk.LabelFrame(self, text=" Départements ", padx=10, pady=6)
        cadre_d.pack(fill="x", padx=12, pady=4)
        self.ent_nouveau_dept = tk.Entry(cadre_d)
        self.ent_nouveau_dept.pack(side="left", padx=(0, 5))
        tk.Button(cadre_d, text="Créer", command=self.action_creer_dept).pack(side="left")
        tk.Button(cadre_d, text="Supprimer le département choisi ci-dessus", fg="#B71C1C",
                  command=self.action_supprimer_dept).pack(side="right")

        # Gestion des projets
        cadre_p = tk.LabelFrame(self, text=" Projets ", padx=10, pady=6)
        cadre_p.pack(fill="x", padx=12, pady=4)
        self.ent_nouveau_projet = tk.Entry(cadre_p)
        self.ent_nouveau_projet.pack(side="left", padx=(0, 5))
        tk.Button(cadre_p, text="Créer", command=self.action_creer_projet).pack(side="left")
        tk.Button(cadre_p, text="Supprimer le projet sélectionné ci-dessus", fg="#B71C1C",
                  command=self.action_supprimer_projet).pack(side="right")

        self._mode_ajout()

    def _champ(self, parent, texte, ligne, colonne):
        tk.Label(parent, text=texte).grid(row=ligne, column=colonne, sticky="w")
        entree = tk.Entry(parent)
        entree.grid(row=ligne, column=colonne + 1, padx=5, pady=2)
        return entree

    def _construire_liste(self):
        self.cadre_liste = tk.LabelFrame(self, padx=10, pady=8)
        cadre = self.cadre_liste
        cadre.pack(fill="both", expand=True, padx=12, pady=8)

        # Ligne de recherche et de filtres
        haut = tk.Frame(cadre)
        haut.pack(fill="x")
        tk.Label(haut, text="Recherche :").pack(side="left")
        tk.Entry(haut, textvariable=self.var_recherche, width=16).pack(side="left", padx=5)
        tk.Label(haut, text="Dép. :").pack(side="left")
        self.menu_filtre_dept = tk.OptionMenu(haut, self.var_filtre_dept, TOUS)
        self.menu_filtre_dept.pack(side="left", padx=5)
        tk.Label(haut, text="Statut :").pack(side="left")
        tk.OptionMenu(haut, self.var_filtre_statut, TOUS, *TYPES_EMPLOYES.keys()).pack(
            side="left", padx=5)
        tk.Button(haut, text="Supprimer la sélection", fg="#B71C1C",
                  command=self.action_supprimer).pack(side="right")

        # En-têtes cliquables = tri par colonne
        entete = tk.Frame(cadre)
        entete.pack(fill="x", pady=(8, 0))
        self.boutons_tri = []
        for i, (cle, titre, largeur) in enumerate(COLONNES):
            bouton = tk.Button(entete, width=largeur, anchor="w", relief="flat", bd=0,
                               padx=0, pady=0, highlightthickness=0,
                               font=("Courier", 10, "bold"),
                               command=lambda i=i: self.action_trier(i))
            bouton.pack(side="left")
            self.boutons_tri.append(bouton)
        self._maj_entetes()

        corps = tk.Frame(cadre)
        corps.pack(fill="both", expand=True)
        barre = tk.Scrollbar(corps)
        barre.pack(side="right", fill="y")
        self.liste = tk.Listbox(corps, font=("Courier", 10), height=10, exportselection=False,
                                width=sum(c[2] for c in COLONNES), yscrollcommand=barre.set)
        self.liste.pack(side="left", fill="both", expand=True)
        barre.config(command=self.liste.yview)
        self.liste.bind("<Double-Button-1>", self.action_charger)

        tk.Label(cadre, text="Double-clic sur une ligne pour la modifier. "
                             "Clic sur un titre de colonne pour trier.",
                 fg="#666666").pack(anchor="w", pady=(4, 0))

    # ----- affichage -----
    def message(self, texte, erreur=False):
        self.lbl_message.config(text=texte, fg="#B71C1C" if erreur else "#2E7D32")

    def _maj_formulaire(self):
        """Adapte le formulaire au statut choisi."""
        statut = self.var_statut.get()
        if statut == "Freelance":
            self.lbl_montant.config(text="Tarif journalier (TJM €) :")
            self.ent_jours.config(state="normal")
            if not self.ent_jours.get():
                self.ent_jours.insert(0, "20")
        else:
            if statut == "Stagiaire":
                self.lbl_montant.config(text="Gratification (€) :")
            else:
                self.lbl_montant.config(text="Salaire mensuel (€) :")
            self.ent_jours.delete(0, tk.END)
            self.ent_jours.config(state="disabled")

    def _maj_entetes(self):
        for i, (cle, titre, _) in enumerate(COLONNES):
            fleche = ""
            if i == self.tri_col:
                fleche = "▼" if self.tri_desc else "▲"
            self.boutons_tri[i].config(text=titre + fleche)

    @staticmethod
    def _reconstruire_menu(menu_widget, variable, choix):
        menu = menu_widget["menu"]
        menu.delete(0, "end")
        for texte in choix:
            menu.add_command(label=texte, command=lambda t=texte: variable.set(t))

    def rafraichir_departements(self):
        try:
            self.departements = self.depot.lister_departements()
        except (ValueError, sqlite3.Error) as e:
            self.message(str(e), erreur=True)
            return
        noms = [d.nom for d in self.departements]

        self._reconstruire_menu(self.menu_dept, self.var_dept, [AUCUN] + noms)
        if self.var_dept.get() not in noms + [AUCUN]:
            self.var_dept.set(noms[0] if noms else AUCUN)

        self._reconstruire_menu(self.menu_filtre_dept, self.var_filtre_dept,
                                [TOUS, AUCUN] + noms)
        if self.var_filtre_dept.get() not in noms + [TOUS, AUCUN]:
            self.var_filtre_dept.set(TOUS)

    def _projets_choisis(self):
        """Objets Projet sélectionnés dans le Listbox du formulaire."""
        return [self.projets[i] for i in self.liste_projets.curselection()]

    def rafraichir_projets(self):
        noms_choisis = {p.nom for p in self._projets_choisis()}  # garder la sélection
        try:
            self.projets = self.depot.lister_projets()
        except (ValueError, sqlite3.Error) as e:
            self.message(str(e), erreur=True)
            return
        self.liste_projets.delete(0, tk.END)
        for i, projet in enumerate(self.projets):
            self.liste_projets.insert(tk.END, projet.nom)
            if projet.nom in noms_choisis:
                self.liste_projets.selection_set(i)

    def _id_dept_par_nom(self, nom):
        return next((d.id_dept for d in self.departements if d.nom == nom), None)

    def _dept_filtre(self):
        valeur = self.var_filtre_dept.get()
        if valeur == TOUS:
            return None
        if valeur == AUCUN:
            return 0
        return self._id_dept_par_nom(valeur)

    def rafraichir_liste(self):
        statut = self.var_filtre_statut.get()
        try:
            employes = self.depot.lister_employes(
                self.var_recherche.get().strip(),
                self._dept_filtre(),
                None if statut == TOUS else statut,
                COLONNES[self.tri_col][0],
                self.tri_desc)
        except (ValueError, sqlite3.Error) as e:
            self.message(str(e), erreur=True)
            return
        self.employes_affiches = employes

        self.liste.delete(0, tk.END)
        for emp in employes:
            dept = emp.departement.nom if emp.departement else AUCUN
            projets = ", ".join(p.nom for p in emp.projets)
            self.liste.insert(tk.END, formater_ligne((
                emp.id_emp, emp.nom, emp.prenom, emp.email, emp.contrat.type_contrat,
                dept, emp.adresse.ville, projets, emp.revenu_affiche)))
        self.cadre_liste.config(text=f" Personnel ({len(self.employes_affiches)}) ")

    # ----- mode ajout / mode modification -----
    def _vider_formulaire(self):
        for champ in (self.ent_nom, self.ent_prenom, self.ent_email, self.ent_montant,
                      self.ent_rue, self.ent_ville):
            champ.delete(0, tk.END)
        self.liste_projets.selection_clear(0, tk.END)
        if self.var_statut.get() == "Freelance":
            self.ent_jours.delete(0, tk.END)
            self.ent_jours.insert(0, "20")

    def _mode_ajout(self):
        self.employe_en_edition = None
        self.cadre_form.config(text=" Nouveau collaborateur ")
        self.btn_valider.config(text="Ajouter le collaborateur", bg="#4CAF50")
        self.btn_annuler.pack_forget()
        self._vider_formulaire()

    def action_charger(self, event):
        """Double-clic : charge l'employé dans le formulaire."""
        i = self.liste.nearest(event.y)
        boite = self.liste.bbox(i)
        if not (0 <= i < len(self.employes_affiches)) or boite is None \
                or not (boite[1] <= event.y < boite[1] + boite[3]):
            return
        emp = self.employes_affiches[i]
        self.employe_en_edition = emp
        self.cadre_form.config(text=f" Modifier : {emp.prenom} {emp.nom} ")
        self.btn_valider.config(text="Enregistrer les modifications", bg="#1976D2")
        self.btn_annuler.pack(side="right", padx=(8, 0))

        for champ, valeur in ((self.ent_nom, emp.nom), (self.ent_prenom, emp.prenom),
                              (self.ent_email, emp.email),
                              (self.ent_montant, f"{emp.contrat.montant:.2f}"),
                              (self.ent_rue, emp.adresse.rue),
                              (self.ent_ville, emp.adresse.ville)):
            champ.delete(0, tk.END)
            champ.insert(0, valeur)
        self.var_statut.set(emp.contrat.type_contrat)  # déclenche _maj_formulaire
        if emp.contrat.type_contrat == "Freelance":
            self.ent_jours.delete(0, tk.END)
            self.ent_jours.insert(0, str(emp.contrat.jours_travailles))
        self.var_dept.set(emp.departement.nom if emp.departement else AUCUN)

        ids_projets = {p.id_projet for p in emp.projets}
        self.liste_projets.selection_clear(0, tk.END)
        for k, projet in enumerate(self.projets):
            if projet.id_projet in ids_projets:
                self.liste_projets.selection_set(k)
        self.message("Modifiez les champs puis enregistrez (ou Annuler).")

    # ----- actions -----
    def action_valider(self):
        try:
            nom = self.ent_nom.get().strip()
            prenom = self.ent_prenom.get().strip()
            email = self.ent_email.get().strip()
            statut = self.var_statut.get()
            montant, jours = valider_saisie(nom, prenom, email, statut,
                                            self.ent_montant.get().strip(),
                                            self.ent_jours.get().strip())
            rue = self.ent_rue.get().strip()
            ville = self.ent_ville.get().strip()
            id_dept = self._id_dept_par_nom(self.var_dept.get())  # None si "(aucun)"
            id_emp = None if self.employe_en_edition is None else self.employe_en_edition.id_emp
            employe = creer_employe(statut, id_emp, nom, prenom, email, montant, jours,
                                    rue=rue, ville=ville)
            employe.projets = self._projets_choisis()
            if id_emp is None:
                self.depot.ajouter_employe(employe, id_dept)
                texte = f"{prenom} {nom} ajouté."
            else:
                self.depot.modifier_employe(employe, id_dept)
                texte = f"{prenom} {nom} modifié."
        except ValueError as e:
            self.message(str(e), erreur=True)
        except sqlite3.Error as e:
            self.message(f"Erreur base de données : {e}", erreur=True)
        else:
            self._mode_ajout()
            self.rafraichir_liste()
            self.message(texte)

    def action_trier(self, colonne):
        if colonne == self.tri_col:
            self.tri_desc = not self.tri_desc
        else:
            self.tri_col, self.tri_desc = colonne, False
        self._maj_entetes()
        self.rafraichir_liste()

    def confirmer(self, titre, texte, action):
        """Petite fenêtre Oui / Non. 'action' n'est appelée que si l'on clique sur Oui."""
        if self.fenetre_confirmation is not None:
            self.fenetre_confirmation.lift()
            return
        fen = tk.Toplevel(self)
        self.fenetre_confirmation = fen
        fen.title(titre)
        fen.resizable(False, False)
        fen.transient(self)  # reste au-dessus de la fenêtre principale

        def fermer():
            fen.grab_release()
            fen.destroy()
            self.fenetre_confirmation = None

        def oui():
            fermer()
            action()

        tk.Label(fen, text=texte, justify="left", padx=20, pady=15).pack()
        boutons = tk.Frame(fen)
        boutons.pack(pady=(0, 12))
        tk.Button(boutons, text="Oui, supprimer", bg="#B71C1C", fg="white",
                  command=oui).pack(side="left", padx=6)
        bouton_non = tk.Button(boutons, text="Non", width=10, command=fermer)
        bouton_non.pack(side="left", padx=6)
        bouton_non.focus_set()  # par sécurité, « Non » est le choix par défaut
        fen.bind("<Escape>", lambda e: fermer())
        fen.protocol("WM_DELETE_WINDOW", fermer)

        fen.update_idletasks()  # centrer sur la fenêtre principale
        x = self.winfo_rootx() + (self.winfo_width() - fen.winfo_reqwidth()) // 2
        y = self.winfo_rooty() + (self.winfo_height() - fen.winfo_reqheight()) // 2
        fen.geometry(f"+{max(x, 0)}+{max(y, 0)}")
        fen.wait_visibility()
        fen.grab_set()  # modale : bloque la fenêtre principale

    def action_supprimer(self):
        selection = self.liste.curselection()
        if not selection:
            self.message("Sélectionnez d'abord un employé.", erreur=True)
            return
        emp = self.employes_affiches[selection[0]]
        self.confirmer(
            "Confirmer la suppression",
            f"Supprimer {emp.prenom} {emp.nom} ?\n\n"
            "Son contrat et son adresse seront aussi supprimés.\n"
            "Cette action est définitive.",
            lambda: self._supprimer_employe(emp))

    def _supprimer_employe(self, emp):
        try:
            self.depot.supprimer_employe(emp.id_emp)
        except (ValueError, sqlite3.Error) as e:
            self.message(str(e), erreur=True)
        else:
            if self.employe_en_edition and self.employe_en_edition.id_emp == emp.id_emp:
                self._mode_ajout()
            self.rafraichir_liste()
            self.message(f"{emp.prenom} {emp.nom}, son contrat et son adresse "
                         "ont été supprimés.")

    def action_creer_dept(self):
        nom = self.ent_nouveau_dept.get().strip()
        if not nom or nom in (TOUS, AUCUN):
            self.message("Saisissez un nom de département valide.", erreur=True)
            return
        try:
            self.depot.ajouter_departement(nom)
        except (ValueError, sqlite3.Error) as e:
            self.message(str(e), erreur=True)
        else:
            self.ent_nouveau_dept.delete(0, tk.END)
            self.rafraichir_departements()
            self.message(f"Département « {nom} » créé.")

    def action_supprimer_dept(self):
        nom = self.var_dept.get()
        id_dept = self._id_dept_par_nom(nom)
        if id_dept is None:
            self.message("Choisissez d'abord un département dans le formulaire.", erreur=True)
            return
        self.confirmer(
            "Confirmer la suppression",
            f"Supprimer le département « {nom} » ?\n\n"
            "Ses employés seront conservés (sans département).",
            lambda: self._supprimer_departement(id_dept, nom))

    def _supprimer_departement(self, id_dept, nom):
        try:
            self.depot.supprimer_departement(id_dept)
        except (ValueError, sqlite3.Error) as e:
            self.message(str(e), erreur=True)
        else:
            self.rafraichir_departements()
            self.rafraichir_liste()
            self.message(f"Département « {nom} » supprimé ; ses employés sont conservés.")

    def action_creer_projet(self):
        nom = self.ent_nouveau_projet.get().strip()
        if not nom:
            self.message("Saisissez un nom de projet.", erreur=True)
            return
        try:
            self.depot.ajouter_projet(nom)
        except (ValueError, sqlite3.Error) as e:
            self.message(str(e), erreur=True)
        else:
            self.ent_nouveau_projet.delete(0, tk.END)
            self.rafraichir_projets()
            self.message(f"Projet « {nom} » créé.")

    def action_supprimer_projet(self):
        choisis = self._projets_choisis()
        if len(choisis) != 1:
            self.message("Sélectionnez un seul projet dans la liste « Projets » du "
                         "formulaire.", erreur=True)
            return
        projet = choisis[0]
        self.confirmer(
            "Confirmer la suppression",
            f"Supprimer le projet « {projet.nom} » ?\n\n"
            "Les employés affectés seront conservés.",
            lambda: self._supprimer_projet(projet))

    def _supprimer_projet(self, projet):
        try:
            self.depot.supprimer_projet(projet.id_projet)
        except (ValueError, sqlite3.Error) as e:
            self.message(str(e), erreur=True)
        else:
            self.rafraichir_projets()
            self.rafraichir_liste()
            self.message(f"Projet « {projet.nom} » supprimé ; ses employés sont conservés.")


if __name__ == "__main__":
    Application(Depot()).mainloop()