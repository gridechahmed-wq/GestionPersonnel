import sqlite3
import tkinter as tk
import tkinter.font as tkfont
from tkinter import ttk


# =====================================================================
# ÉTAPE 1 : MODÈLES MÉTIER (héritage, composition, agrégation)
# =====================================================================
class Contrat:
    """COMPOSITION : le contrat n'existe que pour un employé"""

    def __init__(self, type_contrat, montant, jours_travailles=0):
        self.type_contrat = type_contrat
        self.montant = montant
        self.jours_travailles = jours_travailles


class Adresse:
    """COMPOSITION : l'adresse est créée par l'employé et disparaît avec lui """

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
    "statut": ("e.type_contrat",),
    "dept": ("d.nom COLLATE NOCASE",),
    "rue": ("e.rue COLLATE NOCASE",),
    "ville": ("e.ville COLLATE NOCASE",),
    "projets": ("(SELECT COUNT(*) FROM affectations x WHERE x.employe_id = e.id)",),
    "revenu": ("e.revenu_mensuel",),
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
    rue            TEXT NOT NULL DEFAULT '',
    ville          TEXT NOT NULL DEFAULT '',
    type_contrat   TEXT NOT NULL DEFAULT 'Salarié',
    montant        REAL NOT NULL DEFAULT 0 CHECK (montant >= 0),
    jours_travailles INTEGER NOT NULL DEFAULT 0,
    revenu_mensuel REAL NOT NULL DEFAULT 0,
    departement_id INTEGER,
    FOREIGN KEY (departement_id) REFERENCES departements (id)
        ON DELETE SET NULL
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
            self._migrer_anciennes_tables(conn)
            conn.commit()
        finally:
            if conn:
                conn.close()

    @staticmethod
    def _migrer_anciennes_tables(conn):

        colonnes = {c[1] for c in conn.execute("PRAGMA table_info(employes)")}
        ajouts = {
            "rue": "TEXT NOT NULL DEFAULT ''",
            "ville": "TEXT NOT NULL DEFAULT ''",
            "type_contrat": "TEXT NOT NULL DEFAULT 'Salarié'",
            "montant": "REAL NOT NULL DEFAULT 0",
            "jours_travailles": "INTEGER NOT NULL DEFAULT 0",
            "revenu_mensuel": "REAL NOT NULL DEFAULT 0",
        }
        for col, definition in ajouts.items():
            if col not in colonnes:
                conn.execute(f"ALTER TABLE employes ADD COLUMN {col} {definition}")

        def existe(table):
            return conn.execute("SELECT 1 FROM sqlite_master WHERE type = 'table' "
                                "AND name = ?", (table,)).fetchone() is not None

        def copier(table, champs):
            affectations = ", ".join(
                f"{c} = COALESCE((SELECT t.{c} FROM {table} t "
                f"WHERE t.employe_id = employes.id), {c})" for c in champs)
            conn.execute(f"UPDATE employes SET {affectations}")
            conn.execute(f"DROP TABLE {table}")

        if existe("adresses"):
            copier("adresses", ("rue", "ville"))
        if existe("contrats"):
            copier("contrats", ("type_contrat", "montant", "jours_travailles","revenu_mensuel"))

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
        contrat = employe.contrat
        conn = None
        try:
            conn = self._connexion()
            curseur = conn.execute(
                "INSERT INTO employes (nom, prenom, email, rue, ville, type_contrat, "
                "montant, jours_travailles, revenu_mensuel, departement_id) "
                "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                (employe.nom, employe.prenom, employe.email,
                 employe.adresse.rue, employe.adresse.ville, contrat.type_contrat,
                 contrat.montant, contrat.jours_travailles, employe.revenu_mensuel,
                 id_dept))
            id_emp = curseur.lastrowid
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
        contrat = employe.contrat
        conn = None
        try:
            conn = self._connexion()
            curseur = conn.execute(
                "UPDATE employes SET nom = ?, prenom = ?, email = ?, rue = ?, ville = ?, "
                "type_contrat = ?, montant = ?, jours_travailles = ?, revenu_mensuel = ?, "
                "departement_id = ? WHERE id = ?",
                (employe.nom, employe.prenom, employe.email, employe.adresse.rue,
                 employe.adresse.ville, contrat.type_contrat, contrat.montant,
                 contrat.jours_travailles, employe.revenu_mensuel, id_dept,
                 employe.id_emp))
            if curseur.rowcount == 0:
                raise ValueError("Cet employé n'existe plus.")
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
        # Les affectations disparaissent en CASCADE ;
        # les projets, eux, restent (agrégation).
        self._ecrire("DELETE FROM employes WHERE id = ?", (id_emp,))

    def lister_employes(self, recherche="", dept_filtre=None, statut=None,
                        projet_filtre=None, tri="nom", decroissant=False):
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
            conditions.append("e.type_contrat = ?")
            params.append(statut)
        if projet_filtre is not None:
            if projet_filtre == 0:
                conditions.append("NOT EXISTS (SELECT 1 FROM affectations x "
                                  "WHERE x.employe_id = e.id)")
            else:
                conditions.append("EXISTS (SELECT 1 FROM affectations x "
                                  "WHERE x.employe_id = e.id AND x.projet_id = ?)")
                params.append(projet_filtre)

        sql = f"""
            SELECT e.id, e.nom, e.prenom, e.email,
                   e.type_contrat, e.montant, e.jours_travailles,
                   d.id, d.nom, e.rue, e.ville
            FROM employes e
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

# Palette
FOND = "#F3F4F6"
TEXTE = "#1F2937"
GRIS = "#6B7280"
BORDURE = "#D1D5DB"
VERT, VERT_FONCE = "#2E7D32", "#256628"
BLEU, BLEU_FONCE = "#1976D2", "#1565C0"
ROUGE, ROUGE_FONCE = "#B71C1C", "#8E1515"

# (clé de tri, titre affiché, largeur en pixels, alignement)
COLONNES = (
    ("id", "ID", 45, "center"),
    ("nom", "Nom", 120, "w"),
    ("prenom", "Prénom", 110, "w"),
    ("email", "Email", 210, "w"),
    ("statut", "Statut", 90, "w"),
    ("dept", "Département", 130, "w"),
    ("rue", "Rue", 150, "w"),
    ("ville", "Ville", 110, "w"),
    ("projets", "Projets", 200, "w"),
    ("revenu", "Revenu", 150, "e"),
)

# Couleur du texte de la ligne selon le statut (Salarié = couleur normale)
TAGS_STATUT = {"Freelance": "freelance", "Stagiaire": "stagiaire"}


class Application(tk.Tk):
    def __init__(self, depot):
        super().__init__()
        self.title("Gestion du personnel")
        self.minsize(1350, 760)
        self.configure(background=FOND)
        self._plein_ecran()
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
        self.var_supp_dept = tk.StringVar()
        self.var_supp_projet = tk.StringVar()
        self.var_recherche = tk.StringVar()
        self.var_filtre_dept = tk.StringVar(value=TOUS)
        self.var_filtre_statut = tk.StringVar(value=TOUS)
        self.var_filtre_projet = tk.StringVar(value=TOUS)

        self._appliquer_style()
        self.columnconfigure(0, weight=1)
        self.rowconfigure(1, weight=1)
        self._construire_haut()
        self._construire_liste()
        self._construire_barre_etat()
        self._raccourcis()

        self.var_statut.trace_add("write", lambda *a: self._maj_formulaire())
        for var in (self.var_recherche, self.var_filtre_dept, self.var_filtre_statut,
                    self.var_filtre_projet):
            var.trace_add("write", lambda *a: self.rafraichir_liste())

        self._maj_formulaire()
        self.rafraichir_departements()
        self.rafraichir_projets()
        self.rafraichir_liste()

    def _plein_ecran(self):
        try:
            self.state("zoomed")  # Windows (et certains macOS)
        except tk.TclError:
            try:
                self.attributes("-zoomed", True)  # Linux
            except tk.TclError:
                self.geometry(f"{self.winfo_screenwidth()}x{self.winfo_screenheight()}+0+0")

    # ----- style -----
    def _appliquer_style(self):
        familles = set(tkfont.families(self))
        police = next((f for f in ("Segoe UI", "Helvetica Neue", "Ubuntu", "DejaVu Sans")
                       if f in familles), None)
        if police:
            for nom in ("TkDefaultFont", "TkTextFont", "TkMenuFont", "TkHeadingFont"):
                tkfont.nametofont(nom).configure(family=police, size=10)
        else:
            police = tkfont.nametofont("TkDefaultFont").actual("family")
        self.police = police

        s = ttk.Style(self)
        s.theme_use("clam")
        s.configure(".", background=FOND, foreground=TEXTE, font=(police, 10))

        # Champs de saisie
        s.configure("TEntry", fieldbackground="white", padding=4, bordercolor=BORDURE)
        s.map("TEntry", fieldbackground=[("disabled", "#E5E7EB")],
              foreground=[("disabled", GRIS)])
        s.configure("TCombobox", fieldbackground="white", padding=4, bordercolor=BORDURE,
                    arrowsize=14)
        s.map("TCombobox", fieldbackground=[("readonly", "white")],
              selectbackground=[("readonly", "white")],
              selectforeground=[("readonly", TEXTE)])

        # Cadres
        s.configure("TLabelframe", background=FOND, bordercolor=BORDURE)
        s.configure("TLabelframe.Label", background=FOND, foreground=TEXTE,
                    font=(police, 10, "bold"))

        # Boutons
        s.configure("TButton", padding=(12, 5), background="#E5E7EB", bordercolor=BORDURE)
        s.map("TButton", background=[("active", BORDURE)])

        def bouton(nom, fond, actif):
            s.configure(nom, background=fond, foreground="white", bordercolor=fond,
                        padding=(16, 6))
            s.map(nom, background=[("active", actif), ("pressed", actif)],
                  foreground=[("active", "white")])

        bouton("Accent.TButton", VERT, VERT_FONCE)      # action principale
        bouton("Edit.TButton", BLEU, BLEU_FONCE)        # mode modification
        bouton("DangerSolid.TButton", ROUGE, ROUGE_FONCE)
        s.configure("Danger.TButton", background="white", foreground=ROUGE,
                    bordercolor=ROUGE)
        s.map("Danger.TButton", background=[("active", "#FDE8E8")],
              foreground=[("active", ROUGE)])

        # Tableau
        s.configure("Treeview", rowheight=28, background="white", fieldbackground="white",
                    borderwidth=0, font=(police, 10))
        s.map("Treeview", background=[("selected", BLEU)], foreground=[("selected", "white")])
        s.configure("Treeview.Heading", background="#E5E7EB", foreground=TEXTE,
                    font=(police, 10, "bold"), padding=(6, 6), relief="flat")
        s.map("Treeview.Heading", background=[("active", BORDURE)])

    # ----- construction -----
    def _construire_haut(self):
        haut = ttk.Frame(self)
        haut.grid(row=0, column=0, sticky="ew", padx=12, pady=(12, 6))
        haut.columnconfigure(0, weight=3)
        haut.columnconfigure(1, weight=2, minsize=400)
        self._construire_formulaire(haut)

        # Colonne de droite : gestion des départements et des projets
        droite = ttk.Frame(haut)
        droite.grid(row=0, column=1, sticky="nsew", padx=(12, 0))
        droite.columnconfigure(0, weight=1)
        droite.rowconfigure(0, weight=1)
        droite.rowconfigure(1, weight=1)
        self.ent_nouveau_dept, self.menu_supp_dept = self._bloc_gestion(
            droite, 0, "Départements", self.var_supp_dept,
            self.action_creer_dept, self.action_supprimer_dept)
        self.ent_nouveau_projet, self.menu_supp_projet = self._bloc_gestion(
            droite, 1, "Projets", self.var_supp_projet,
            self.action_creer_projet, self.action_supprimer_projet)

    def _bloc_gestion(self, parent, ligne, titre, var_choix, creer, supprimer):
        """Bloc « Créer / Supprimer » : retourne (champ de saisie, liste déroulante)."""
        bloc = ttk.LabelFrame(parent, text=f" {titre} ", padding=10)
        bloc.grid(row=ligne, column=0, sticky="nsew", pady=(0, 6) if ligne == 0 else 0)
        bloc.columnconfigure(1, weight=1)

        ttk.Label(bloc, text="Nouveau").grid(row=0, column=0, sticky="w", padx=(0, 10))
        entree = ttk.Entry(bloc)
        entree.grid(row=0, column=1, sticky="ew", pady=4)
        entree.bind("<Return>", lambda e: creer())
        ttk.Button(bloc, text="Créer", command=creer).grid(
            row=0, column=2, sticky="ew", padx=(8, 0))

        ttk.Label(bloc, text="Existant").grid(row=1, column=0, sticky="w", padx=(0, 10))
        choix = self._combo(bloc, var_choix, ())
        choix.grid(row=1, column=1, sticky="ew", pady=4)
        ttk.Button(bloc, text="Supprimer", style="Danger.TButton", command=supprimer).grid(
            row=1, column=2, sticky="ew", padx=(8, 0))
        return entree, choix

    def _construire_formulaire(self, parent):
        self.cadre_form = ttk.LabelFrame(parent, padding=12)
        cadre = self.cadre_form
        cadre.grid(row=0, column=0, sticky="nsew")
        # colonnes de champs de même largeur ; colonne des libellés à largeur fixe
        cadre.columnconfigure(0, minsize=60)
        cadre.columnconfigure(1, weight=1, uniform="champ")
        cadre.columnconfigure(2, minsize=220)
        cadre.columnconfigure(3, weight=1, uniform="champ")

        self.ent_nom = self._champ(cadre, "Nom *", 0, 0)
        self.ent_prenom = self._champ(cadre, "Prénom *", 0, 2)
        self.ent_email = self._champ(cadre, "Email *", 1, 0)

        self._etiquette(cadre, "Département", 1, 2)
        self.menu_dept = self._combo(cadre, self.var_dept, ())
        self.menu_dept.grid(row=1, column=3, sticky="ew", pady=4)

        self._etiquette(cadre, "Statut", 2, 0)
        self._combo(cadre, self.var_statut, list(TYPES_EMPLOYES)).grid(
            row=2, column=1, sticky="ew", pady=4)

        self.lbl_montant = self._etiquette(cadre, "Salaire mensuel (€) *", 2, 2)
        self.ent_montant = ttk.Entry(cadre)
        self.ent_montant.grid(row=2, column=3, sticky="ew", pady=4)

        self.ent_rue = self._champ(cadre, "Rue", 3, 0)
        self.lbl_jours = self._etiquette(cadre, "Jours travaillés", 3, 2)
        self.ent_jours = ttk.Entry(cadre)
        self.ent_jours.grid(row=3, column=3, sticky="ew", pady=4)

        self.ent_ville = self._champ(cadre, "Ville", 4, 0)
        self._etiquette(cadre, "Projets", 4, 2, sticky="nw", pady=8)
        cadre_proj = ttk.Frame(cadre)
        cadre_proj.grid(row=4, column=3, rowspan=2, sticky="ew", pady=4)
        cadre_proj.columnconfigure(0, weight=1)
        self.liste_projets = tk.Listbox(
            cadre_proj, selectmode=tk.MULTIPLE, height=4, exportselection=False,
            activestyle="none", bg="white", fg=TEXTE, relief="flat",
            highlightthickness=1, highlightbackground="#B8BEC7", highlightcolor=BLEU,
            selectbackground=BLEU, selectforeground="white", font=(self.police, 10))
        ascenseur = ttk.Scrollbar(cadre_proj, orient="vertical",
                                  command=self.liste_projets.yview)
        self.liste_projets.config(yscrollcommand=ascenseur.set)
        self.liste_projets.grid(row=0, column=0, sticky="ew")
        ascenseur.grid(row=0, column=1, sticky="ns")

        boutons = ttk.Frame(cadre)
        boutons.grid(row=6, column=0, columnspan=4, sticky="ew", pady=(12, 0))
        self.btn_valider = ttk.Button(boutons, command=self.action_valider)
        self.btn_valider.pack(side="left")
        self.btn_annuler = ttk.Button(boutons, text="Annuler", command=self._mode_ajout)
        ttk.Label(boutons, text="* champ obligatoire", foreground=GRIS).pack(side="right")

        self._mode_ajout()

    @staticmethod
    def _etiquette(parent, texte, ligne, colonne, sticky="w", pady=4):
        etiquette = ttk.Label(parent, text=texte)
        etiquette.grid(row=ligne, column=colonne, sticky=sticky, pady=pady,
                       padx=(16 if colonne else 0, 8))
        return etiquette

    def _champ(self, parent, texte, ligne, colonne):
        self._etiquette(parent, texte, ligne, colonne)
        entree = ttk.Entry(parent)
        entree.grid(row=ligne, column=colonne + 1, sticky="ew", pady=4)
        return entree

    @staticmethod
    def _combo(parent, variable, valeurs, width=None):
        options = {"textvariable": variable, "values": list(valeurs), "state": "readonly"}
        if width:
            options["width"] = width
        return ttk.Combobox(parent, **options)

    def _construire_liste(self):
        self.cadre_liste = ttk.LabelFrame(self, padding=10)
        cadre = self.cadre_liste
        cadre.grid(row=1, column=0, sticky="nsew", padx=12, pady=6)
        cadre.columnconfigure(0, weight=1)
        cadre.rowconfigure(1, weight=1)

        # Ligne de recherche et de filtres
        barre = ttk.Frame(cadre)
        barre.grid(row=0, column=0, sticky="ew")
        ttk.Label(barre, text="Recherche").pack(side="left")
        ttk.Entry(barre, textvariable=self.var_recherche, width=22).pack(
            side="left", padx=(6, 18))
        ttk.Label(barre, text="Département").pack(side="left")
        self.menu_filtre_dept = self._combo(barre, self.var_filtre_dept, [TOUS], width=14)
        self.menu_filtre_dept.pack(side="left", padx=(6, 18))
        ttk.Label(barre, text="Statut").pack(side="left")
        self._combo(barre, self.var_filtre_statut, [TOUS, *TYPES_EMPLOYES], width=11).pack(
            side="left", padx=(6, 18))
        ttk.Label(barre, text="Projet").pack(side="left")
        self.menu_filtre_projet = self._combo(barre, self.var_filtre_projet, [TOUS], width=14)
        self.menu_filtre_projet.pack(side="left", padx=(6, 0))
        ttk.Button(barre, text="Supprimer la sélection", style="Danger.TButton",
                   command=self.action_supprimer).pack(side="right")

        corps = ttk.Frame(cadre)
        corps.grid(row=1, column=0, sticky="nsew", pady=(10, 0))
        corps.columnconfigure(0, weight=1)
        corps.rowconfigure(0, weight=1)
        ascenseur = ttk.Scrollbar(corps, orient="vertical")
        ascenseur.grid(row=0, column=1, sticky="ns")

        self.liste = ttk.Treeview(corps, columns=[c[0] for c in COLONNES],
                                  show="headings", selectmode="browse", height=8,
                                  yscrollcommand=ascenseur.set)
        for i, (cle, titre, largeur, ancre) in enumerate(COLONNES):
            self.liste.heading(cle, text=titre, anchor=ancre,
                               command=lambda i=i: self.action_trier(i))
            # largeur fixe : seule la colonne « Projets » s'étire si on agrandit la fenêtre
            self.liste.column(cle, width=largeur, minwidth=largeur, anchor=ancre,
                              stretch=(cle == "projets"))
        self.liste.grid(row=0, column=0, sticky="nsew")
        ascenseur.config(command=self.liste.yview)
        self.liste.bind("<Double-Button-1>", self.action_charger)

        # Lignes en alternance + couleur du texte selon le statut
        self.liste.tag_configure("pair", background="white")
        self.liste.tag_configure("impair", background="#F3F6FA")
        self.liste.tag_configure("freelance", foreground="#B45309")
        self.liste.tag_configure("stagiaire", foreground=GRIS)

        # Message affiché quand la liste est vide
        self.lbl_vide = ttk.Label(self.liste, background="white", foreground=GRIS,
                                  font=(self.police, 11))
        self._maj_entetes()

        ttk.Label(cadre, foreground=GRIS,
                  text="Double-clic : modifier   •   Suppr : supprimer la ligne   •   "
                       "Clic sur un titre : trier").grid(row=2, column=0, sticky="w",
                                                         pady=(8, 0))

    def _construire_barre_etat(self):
        self.lbl_message = ttk.Label(self, anchor="w", padding=(14, 8))
        self.lbl_message.grid(row=2, column=0, sticky="ew")
        self.message("Prêt.", info=True)

    def _raccourcis(self):
        # Entrée : valider le formulaire
        for champ in (self.ent_nom, self.ent_prenom, self.ent_email, self.ent_montant,
                      self.ent_rue, self.ent_ville, self.ent_jours):
            champ.bind("<Return>", lambda e: self.action_valider())
        # Suppr : supprimer la ligne sélectionnée
        self.liste.bind("<Delete>", lambda e: self.action_supprimer())
        # Échap : quitter le mode modification
        self.bind("<Escape>", lambda e: self._mode_ajout() if self.employe_en_edition else None)

    # ----- affichage -----
    def message(self, texte, erreur=False, info=False):
        if erreur:
            fond, couleur = "#FDE8E8", ROUGE
        elif info:
            fond, couleur = "#E8F0FE", "#1A4E9C"
        else:
            fond, couleur = "#E6F4EA", "#1E6B34"
        self.lbl_message.config(text=texte, background=fond, foreground=couleur)

    def _maj_formulaire(self):
        """Adapte le formulaire au statut choisi."""
        statut = self.var_statut.get()
        if statut == "Freelance":
            self.lbl_montant.config(text="Tarif journalier (TJM €) *")
            self.lbl_jours.config(text="Jours travaillés *")
            self.ent_jours.config(state="normal")
            if not self.ent_jours.get():
                self.ent_jours.insert(0, "20")
        else:
            if statut == "Stagiaire":
                self.lbl_montant.config(text="Gratification (€) *")
            else:
                self.lbl_montant.config(text="Salaire mensuel (€) *")
            self.lbl_jours.config(text="Jours travaillés")
            self.ent_jours.config(state="normal")
            self.ent_jours.delete(0, tk.END)
            self.ent_jours.config(state="disabled")

    def _maj_entetes(self):
        for i, (cle, titre, _, _) in enumerate(COLONNES):
            fleche = ""
            if i == self.tri_col:
                fleche = " ▼" if self.tri_desc else " ▲"
            self.liste.heading(cle, text=titre + fleche)

    def rafraichir_departements(self):
        try:
            self.departements = self.depot.lister_departements()
        except (ValueError, sqlite3.Error) as e:
            self.message(str(e), erreur=True)
            return
        noms = [d.nom for d in self.departements]

        self.menu_dept.config(values=[AUCUN] + noms)
        if self.var_dept.get() not in noms + [AUCUN]:
            self.var_dept.set(noms[0] if noms else AUCUN)

        self.menu_supp_dept.config(values=noms)
        if self.var_supp_dept.get() not in noms:
            self.var_supp_dept.set(noms[0] if noms else "")

        self.menu_filtre_dept.config(values=[TOUS, AUCUN] + noms)
        if self.var_filtre_dept.get() not in noms + [TOUS, AUCUN]:
            self.var_filtre_dept.set(TOUS)

    def _projets_choisis(self):
        """Objets Projet sélectionnés dans la liste du formulaire."""
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

        noms = [p.nom for p in self.projets]
        self.menu_supp_projet.config(values=noms)
        if self.var_supp_projet.get() not in noms:
            self.var_supp_projet.set(noms[0] if noms else "")

        self.menu_filtre_projet.config(values=[TOUS, AUCUN] + noms)
        if self.var_filtre_projet.get() not in noms + [TOUS, AUCUN]:
            self.var_filtre_projet.set(TOUS)

    def _id_dept_par_nom(self, nom):
        return next((d.id_dept for d in self.departements if d.nom == nom), None)

    def _dept_filtre(self):
        valeur = self.var_filtre_dept.get()
        if valeur == TOUS:
            return None
        if valeur == AUCUN:
            return 0
        return self._id_dept_par_nom(valeur)

    def _projet_filtre(self):
        valeur = self.var_filtre_projet.get()
        if valeur == TOUS:
            return None
        if valeur == AUCUN:
            return 0
        return next((p.id_projet for p in self.projets if p.nom == valeur), None)

    def rafraichir_liste(self):
        statut = self.var_filtre_statut.get()
        recherche = self.var_recherche.get().strip()
        try:
            employes = self.depot.lister_employes(
                recherche,
                self._dept_filtre(),
                None if statut == TOUS else statut,
                self._projet_filtre(),
                COLONNES[self.tri_col][0],
                self.tri_desc)
        except (ValueError, sqlite3.Error) as e:
            self.message(str(e), erreur=True)
            return
        self.employes_affiches = employes

        self.liste.delete(*self.liste.get_children())
        for i, emp in enumerate(employes):
            dept = emp.departement.nom if emp.departement else AUCUN
            projets = ", ".join(p.nom for p in emp.projets)
            tags = ["impair" if i % 2 else "pair"]
            if emp.contrat.type_contrat in TAGS_STATUT:
                tags.append(TAGS_STATUT[emp.contrat.type_contrat])
            self.liste.insert("", tk.END, iid=str(i), tags=tags, values=(
                emp.id_emp, emp.nom, emp.prenom, emp.email, emp.contrat.type_contrat,
                dept, emp.adresse.rue, emp.adresse.ville, projets, emp.revenu_affiche))
        self.cadre_liste.config(text=f" Personnel ({len(employes)}) ")

        if employes:
            self.lbl_vide.place_forget()
        else:
            filtre_actif = (recherche or statut != TOUS or self.var_filtre_dept.get() != TOUS
                            or self.var_filtre_projet.get() != TOUS)
            self.lbl_vide.config(text="Aucun résultat pour ces critères." if filtre_actif
                                 else "Aucun collaborateur pour l'instant.")
            self.lbl_vide.place(relx=0.5, rely=0.3, anchor="center")

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
        self.btn_valider.config(text="Ajouter le collaborateur", style="Accent.TButton")
        self.btn_annuler.pack_forget()
        self._vider_formulaire()

    def action_charger(self, event):
        """Double-clic : charge l'employé dans le formulaire."""
        ligne = self.liste.identify_row(event.y)
        if not ligne:  # clic sur l'en-tête ou dans le vide
            return
        emp = self.employes_affiches[int(ligne)]
        self.employe_en_edition = emp
        self.cadre_form.config(text=f" Modifier : {emp.prenom} {emp.nom} ")
        self.btn_valider.config(text="Enregistrer les modifications", style="Edit.TButton")
        self.btn_annuler.pack(side="left", padx=(8, 0))

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
        self.message("Modifiez les champs puis enregistrez (Entrée) ou annulez (Échap).",
                     info=True)

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
        fen.configure(background=FOND)
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

        ttk.Label(fen, text=texte, justify="left", padding=(24, 18)).pack()
        boutons = ttk.Frame(fen)
        boutons.pack(pady=(0, 16))
        ttk.Button(boutons, text="Oui, supprimer", style="DangerSolid.TButton",
                   command=oui).pack(side="left", padx=6)
        bouton_non = ttk.Button(boutons, text="Non", width=10, command=fermer)
        bouton_non.pack(side="left", padx=6)
        bouton_non.focus_set()  # par sécurité, « Non » est le choix par défaut
        fen.bind("<Escape>", lambda e: fermer())
        fen.protocol("WM_DELETE_WINDOW", fermer)

        fen.update_idletasks()
        x = self.winfo_rootx() + (self.winfo_width() - fen.winfo_reqwidth()) // 2
        y = self.winfo_rooty() + (self.winfo_height() - fen.winfo_reqheight()) // 2
        fen.geometry(f"+{max(x, 0)}+{max(y, 0)}")
        fen.wait_visibility()
        fen.grab_set()

    def action_supprimer(self):
        selection = self.liste.selection()
        if not selection:
            self.message("Sélectionnez d'abord un employé.", erreur=True)
            return
        emp = self.employes_affiches[int(selection[0])]
        self.confirmer(
            "Confirmer la suppression",
            f"Supprimer {emp.prenom} {emp.nom} ?\n\n"
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
            self.message(f"{emp.prenom} {emp.nom} supprimé.")

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
        nom = self.var_supp_dept.get()
        id_dept = self._id_dept_par_nom(nom)
        if id_dept is None:
            self.message("Choisissez d'abord le département à supprimer.", erreur=True)
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
        if not nom or nom in (TOUS, AUCUN):
            self.message("Saisissez un nom de projet valide.", erreur=True)
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
        nom = self.var_supp_projet.get()
        projet = next((p for p in self.projets if p.nom == nom), None)
        if projet is None:
            self.message("Choisissez d'abord le projet à supprimer.", erreur=True)
            return
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
