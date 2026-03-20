#!/usr/bin/env python3
"""
Générateur de sujets Antibi — Interface Tkinter
Auteur: Philippe (architecture), Claude (implémentation)
Usage: python3 main.py
"""

import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import os
import json
import datetime

from generators import REGISTRY, get_generators_by_level, ExerciseGenerator, get_difficulty_stats_file_path, clear_difficulty_stats_cache
from latex_builder import build_document

# ============================================================
# Couleurs et style
# ============================================================
BG = "#f5f5f5"
BG_PANEL = "#ffffff"
ACCENT = "#2c5f8a"
ACCENT_LIGHT = "#e8f0f8"
FONT = ("Helvetica", 12)
FONT_SMALL = ("Helvetica", 10)
FONT_BOLD = ("Helvetica", 12, "bold")
FONT_TITLE = ("Helvetica", 16, "bold")


class ExerciseConfigDialog(tk.Toplevel):
    """Dialogue de configuration d'un exercice."""

    def __init__(self, parent, gen_class, existing_config=None):
        super().__init__(parent)
        self.title(f"Configuration — {gen_class.name}")
        self.gen_class = gen_class
        self.result = None
        self.transient(parent)
        self.grab_set()

        self.configure(bg=BG)
        self.resizable(False, False)

        # Description
        ttk.Label(self, text=gen_class.description, font=FONT_SMALL,
                  background=BG, wraplength=350).pack(padx=15, pady=(15, 5))

        # Paramètres
        self.widgets = {}
        params = gen_class.get_config()
        frame = ttk.Frame(self)
        frame.pack(padx=15, pady=10, fill='x')

        for i, param in enumerate(params):
            ttk.Label(frame, text=param['label'] + " :").grid(
                row=i, column=0, sticky='w', padx=(0, 10), pady=3)

            val = existing_config.get(param['key'], param['default']) if existing_config else param['default']

            if param['type'] == 'int':
                var = tk.IntVar(value=val)
                spin = ttk.Spinbox(frame, from_=param.get('min', 1),
                                   to=param.get('max', 20),
                                   textvariable=var, width=6)
                spin.grid(row=i, column=1, sticky='w', pady=3)
                self.widgets[param['key']] = var

            elif param['type'] == 'choice':
                var = tk.StringVar(value=val)
                combo = ttk.Combobox(frame, textvariable=var,
                                     values=param['choices'], state='readonly', width=20)
                combo.grid(row=i, column=1, sticky='w', pady=3)
                self.widgets[param['key']] = var

        # Boutons
        btn_frame = ttk.Frame(self)
        btn_frame.pack(pady=15)
        ttk.Button(btn_frame, text="OK", command=self._ok).pack(side='left', padx=5)
        ttk.Button(btn_frame, text="Annuler", command=self.destroy).pack(side='left', padx=5)

        self.geometry("+%d+%d" % (parent.winfo_rootx() + 100, parent.winfo_rooty() + 100))
        self.wait_window()

    def _ok(self):
        self.result = {}
        for key, var in self.widgets.items():
            self.result[key] = var.get()
        self.destroy()


class AntibiApp(tk.Tk):
    """Application principale."""

    def __init__(self):
        super().__init__()
        self.title("Générateur de sujets Antibi")
        self.configure(bg=BG)
        self.geometry("950x700")
        self.minsize(900, 600)

        # Données
        self.composition = []  # Liste de {'gen_id': str, 'config': dict}
        self.generators_by_level = get_generators_by_level()

        self._build_ui()

    def _build_ui(self):
        # ===== Titre =====
        title_frame = tk.Frame(self, bg=ACCENT, height=50)
        title_frame.pack(fill='x')
        title_frame.pack_propagate(False)
        tk.Label(title_frame, text="Générateur de sujets Antibi",
                 font=FONT_TITLE, fg="white", bg=ACCENT).pack(side='left', padx=15, pady=8)

        # ===== Paramètres globaux =====
        params_frame = tk.LabelFrame(self, text="Paramètres globaux", font=FONT_BOLD,
                                      bg=BG_PANEL, padx=10, pady=8)
        params_frame.pack(fill='x', padx=10, pady=(10, 5))

        row1 = tk.Frame(params_frame, bg=BG_PANEL)
        row1.pack(fill='x', pady=2)

        tk.Label(row1, text="Titre :", font=FONT, bg=BG_PANEL).pack(side='left')
        self.var_titre = tk.StringVar(value="Entraînement de calcul")
        tk.Entry(row1, textvariable=self.var_titre, font=FONT, width=30).pack(side='left', padx=(5, 20))

        tk.Label(row1, text="Classe :", font=FONT, bg=BG_PANEL).pack(side='left')
        self.var_classe = tk.StringVar(value="3e turquoise")
        tk.Entry(row1, textvariable=self.var_classe, font=FONT, width=15).pack(side='left', padx=(5, 20))

        tk.Label(row1, text="Type :", font=FONT, bg=BG_PANEL).pack(side='left')
        self.var_type = tk.StringVar(value="Entraînement")
        ttk.Combobox(row1, textvariable=self.var_type,
                     values=["Entraînement", "Contrôle", "DM"], state='readonly',
                     width=14).pack(side='left', padx=5)

        row2 = tk.Frame(params_frame, bg=BG_PANEL)
        row2.pack(fill='x', pady=2)

        tk.Label(row2, text="Nb sujets :", font=FONT, bg=BG_PANEL).pack(side='left')
        self.var_nb_sujets = tk.IntVar(value=38)
        ttk.Spinbox(row2, from_=1, to=50, textvariable=self.var_nb_sujets, width=5).pack(side='left', padx=(5, 20))

        tk.Label(row2, text="Corrigés :", font=FONT, bg=BG_PANEL).pack(side='left')
        self.var_corrige = tk.StringVar(value="Après chaque sujet")
        ttk.Combobox(row2, textvariable=self.var_corrige,
                     values=["Après chaque sujet", "Tous à la fin", "Aucun"],
                     state='readonly', width=18).pack(side='left', padx=5)

        tk.Label(row2, text="Mode :", font=FONT, bg=BG_PANEL).pack(side='left', padx=(10, 0))
        self.var_corrige_mode = tk.StringVar(value="Complet")
        ttk.Combobox(row2, textvariable=self.var_corrige_mode,
                     values=["Complet", "Succinct"],
                     state='readonly', width=10).pack(side='left', padx=5)

        tk.Label(row2, text="QR codes :", font=FONT, bg=BG_PANEL).pack(side='left', padx=(10, 0))
        self.var_qr = tk.StringVar(value="Oui")
        ttk.Combobox(row2, textvariable=self.var_qr,
                     values=["Oui", "Non"],
                     state='readonly', width=5).pack(side='left', padx=5)

        row3 = tk.Frame(params_frame, bg=BG_PANEL)
        row3.pack(fill='x', pady=2)

        self.var_show_nom = tk.BooleanVar(value=False)
        tk.Checkbutton(row3, text="Afficher 'Prénom, nom'", variable=self.var_show_nom,
                       font=FONT, bg=BG_PANEL, activebackground=BG_PANEL).pack(side='left', padx=(0, 10))

        self.var_show_consigne = tk.BooleanVar(value=False)
        tk.Checkbutton(row3, text="Afficher la consigne :", variable=self.var_show_consigne,
                       font=FONT, bg=BG_PANEL, activebackground=BG_PANEL).pack(side='left', padx=(10, 5))
        self.var_consigne = tk.StringVar(value="La qualité de la rédaction entre en compte dans la notation")
        tk.Entry(row3, textvariable=self.var_consigne, font=FONT, width=65).pack(side='left', padx=(0, 5))

        row4 = tk.Frame(params_frame, bg=BG_PANEL)
        row4.pack(fill='x', pady=2)

        self.var_diff_filter = tk.BooleanVar(value=False)
        tk.Checkbutton(row4, text="Filtre statistique de difficulté", variable=self.var_diff_filter,
                       font=FONT, bg=BG_PANEL, activebackground=BG_PANEL).pack(side='left')

        tk.Label(row4, text="Centre z :", font=FONT, bg=BG_PANEL).pack(side='left', padx=(12, 0))
        self.var_diff_zcenter = tk.DoubleVar(value=0.0)
        ttk.Spinbox(row4, from_=-3.0, to=3.0, increment=0.25, textvariable=self.var_diff_zcenter, width=6).pack(side='left', padx=(5, 12))

        tk.Label(row4, text="Tolérance ±z :", font=FONT, bg=BG_PANEL).pack(side='left')
        self.var_diff_ztol = tk.DoubleVar(value=0.75)
        ttk.Spinbox(row4, from_=0.0, to=3.0, increment=0.25, textvariable=self.var_diff_ztol, width=6).pack(side='left', padx=(5, 12))

        tk.Label(row4, text="Échantillons de calibration :", font=FONT, bg=BG_PANEL).pack(side='left')
        self.var_diff_samples = tk.IntVar(value=80)
        ttk.Spinbox(row4, from_=20, to=500, increment=20, textvariable=self.var_diff_samples, width=6).pack(side='left', padx=(5, 12))

        tk.Label(row4, text="Essais max :", font=FONT, bg=BG_PANEL).pack(side='left')
        self.var_diff_attempts = tk.IntVar(value=40)
        ttk.Spinbox(row4, from_=1, to=500, increment=5, textvariable=self.var_diff_attempts, width=6).pack(side='left', padx=(5, 12))

        row5 = tk.Frame(params_frame, bg=BG_PANEL)
        row5.pack(fill='x', pady=2)
        tk.Label(row5, text="Stats difficulté :", font=FONT_SMALL, bg=BG_PANEL, fg="#444").pack(side='left')
        self.stats_path_var = tk.StringVar(value=get_difficulty_stats_file_path())
        tk.Entry(row5, textvariable=self.stats_path_var, font=FONT_SMALL, width=55, state='readonly').pack(side='left', padx=(5, 8))
        ttk.Button(row5, text="Vider le cache", command=self._clear_difficulty_cache).pack(side='left')
        tk.Label(row5, text="(cible : z dans [centre - tolérance ; centre + tolérance])",
                 font=FONT_SMALL, bg=BG_PANEL, fg="#555").pack(side='left', padx=(10, 0))

        tk.Label(row2, text="Fichier :", font=FONT, bg=BG_PANEL).pack(side='left', padx=(20, 0))
        self.var_fichier = tk.StringVar(value="sujet.tex")
        tk.Entry(row2, textvariable=self.var_fichier, font=FONT, width=20).pack(side='left', padx=5)
        ttk.Button(row2, text="...", width=3, command=self._browse_file).pack(side='left')

        # ===== Zone principale : catalogue + composition =====
        main_frame = tk.Frame(self, bg=BG)
        main_frame.pack(fill='both', expand=True, padx=10, pady=5)

        # --- Panneau gauche : catalogue ---
        left_frame = tk.LabelFrame(main_frame, text="Exercices disponibles", font=FONT_BOLD,
                                    bg=BG_PANEL, padx=5, pady=5)
        left_frame.pack(side='left', fill='both', expand=True, padx=(0, 5))

        # Treeview pour le catalogue
        self.tree = ttk.Treeview(left_frame, height=15, selectmode='browse')
        self.tree.heading('#0', text='Exercice', anchor='w')
        self.tree.column('#0', width=280)

        scrollbar = ttk.Scrollbar(left_frame, orient='vertical', command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)

        self.tree.pack(side='left', fill='both', expand=True)
        scrollbar.pack(side='right', fill='y')

        # Remplir le catalogue
        self._populate_catalog()

        # Bouton Ajouter
        ttk.Button(left_frame, text="➕ Ajouter au sujet", command=self._add_exercise).pack(
            pady=(5, 0), fill='x')

        # Double-clic pour ajouter
        self.tree.bind('<Double-1>', lambda e: self._add_exercise())

        # --- Panneau droit : composition du sujet ---
        right_frame = tk.LabelFrame(main_frame, text="Composition du sujet", font=FONT_BOLD,
                                     bg=BG_PANEL, padx=5, pady=5)
        right_frame.pack(side='right', fill='both', expand=True, padx=(5, 0))

        self.comp_list = tk.Listbox(right_frame, font=FONT, selectmode='browse',
                                     height=12, bg='white', activestyle='none')
        self.comp_list.pack(fill='both', expand=True)

        # Boutons de gestion
        btn_frame = tk.Frame(right_frame, bg=BG_PANEL)
        btn_frame.pack(fill='x', pady=(5, 0))

        ttk.Button(btn_frame, text="⚙ Configurer", command=self._configure_exercise).pack(side='left', padx=2)
        ttk.Button(btn_frame, text="▲", width=3, command=self._move_up).pack(side='left', padx=2)
        ttk.Button(btn_frame, text="▼", width=3, command=self._move_down).pack(side='left', padx=2)
        ttk.Button(btn_frame, text="✕ Supprimer", command=self._remove_exercise).pack(side='left', padx=2)
        ttk.Button(btn_frame, text="Tout vider", command=self._clear_all).pack(side='right', padx=2)

        # ===== Barre du bas =====
        bottom_frame = tk.Frame(self, bg=BG)
        bottom_frame.pack(fill='x', padx=10, pady=(5, 10))

        # Preset buttons
        preset_frame = tk.Frame(bottom_frame, bg=BG)
        preset_frame.pack(side='left')
        ttk.Button(preset_frame, text="💾 Sauver preset", command=self._save_preset).pack(side='left', padx=3)
        ttk.Button(preset_frame, text="📂 Charger preset", command=self._load_preset).pack(side='left', padx=3)

        # Bouton Générer
        gen_btn = tk.Button(bottom_frame, text="  GÉNÉRER LE FICHIER .tex  ",
                            font=("Helvetica", 14, "bold"),
                            bg=ACCENT, fg="white", activebackground="#1e4060",
                            activeforeground="white", relief='flat', padx=20, pady=8,
                            command=self._generate)
        gen_btn.pack(side='right', padx=5)

        # Status bar
        self.status_var = tk.StringVar(value="Prêt. Ajoutez des exercices au sujet.")
        tk.Label(self, textvariable=self.status_var, font=FONT_SMALL,
                 bg=BG, fg="#666", anchor='w').pack(fill='x', padx=10, pady=(0, 5))

    def _populate_catalog(self):
        """Remplit le Treeview avec les générateurs disponibles."""
        for niveau, gens in self.generators_by_level.items():
            node = self.tree.insert('', 'end', text=f"📚 {niveau}", open=True)
            for gen_class in gens:
                self.tree.insert(node, 'end', text=f"  {gen_class.name}",
                                 tags=(gen_class.id,))

    def _get_selected_gen_id(self):
        """Retourne l'id du générateur sélectionné, ou None."""
        sel = self.tree.selection()
        if not sel:
            return None
        tags = self.tree.item(sel[0], 'tags')
        if tags and tags[0] in REGISTRY:
            return tags[0]
        return None

    def _add_exercise(self):
        """Ajouter l'exercice sélectionné à la composition."""
        gen_id = self._get_selected_gen_id()
        if not gen_id:
            messagebox.showinfo("Info", "Sélectionnez un type d'exercice (pas un niveau).")
            return

        gen_class = REGISTRY[gen_id]
        dialog = ExerciseConfigDialog(self, gen_class)
        if dialog.result is not None:
            self.composition.append({
                'gen_id': gen_id,
                'config': dialog.result
            })
            self._refresh_composition()
            self.status_var.set(f"Ajouté : {gen_class.name}")

    def _configure_exercise(self):
        """Reconfigurer un exercice existant."""
        idx = self.comp_list.curselection()
        if not idx:
            return
        idx = idx[0]
        item = self.composition[idx]
        gen_class = REGISTRY[item['gen_id']]
        dialog = ExerciseConfigDialog(self, gen_class, item['config'])
        if dialog.result is not None:
            self.composition[idx]['config'] = dialog.result
            self._refresh_composition()

    def _remove_exercise(self):
        idx = self.comp_list.curselection()
        if not idx:
            return
        del self.composition[idx[0]]
        self._refresh_composition()

    def _move_up(self):
        idx = self.comp_list.curselection()
        if not idx or idx[0] == 0:
            return
        i = idx[0]
        self.composition[i - 1], self.composition[i] = self.composition[i], self.composition[i - 1]
        self._refresh_composition()
        self.comp_list.selection_set(i - 1)

    def _move_down(self):
        idx = self.comp_list.curselection()
        if not idx or idx[0] >= len(self.composition) - 1:
            return
        i = idx[0]
        self.composition[i], self.composition[i + 1] = self.composition[i + 1], self.composition[i]
        self._refresh_composition()
        self.comp_list.selection_set(i + 1)

    def _clear_all(self):
        if self.composition and messagebox.askyesno("Confirmer", "Vider toute la composition ?"):
            self.composition.clear()
            self._refresh_composition()

    def _refresh_composition(self):
        """Met à jour l'affichage de la composition."""
        self.comp_list.delete(0, 'end')
        for i, item in enumerate(self.composition):
            gen_class = REGISTRY[item['gen_id']]
            conf = item['config']
            # Résumé des paramètres
            params_str = ", ".join(f"{k}={v}" for k, v in conf.items())
            label = f"{i + 1}. [{gen_class.niveau}] {gen_class.name}  ({params_str})"
            self.comp_list.insert('end', label)

    def _browse_file(self):
        f = filedialog.asksaveasfilename(
            defaultextension=".tex",
            filetypes=[("Fichiers LaTeX", "*.tex"), ("Tous", "*.*")],
            initialfile=self.var_fichier.get()
        )
        if f:
            self.var_fichier.set(f)

    def _generate(self):
        """Génère le fichier .tex."""
        if not self.composition:
            messagebox.showwarning("Attention", "Ajoutez au moins un exercice au sujet.")
            return

        titre = self.var_titre.get()
        classe = self.var_classe.get()
        is_controle = self.var_type.get() in ["Contrôle", "DM"]
        nb_sujets = self.var_nb_sujets.get()
        fichier = self.var_fichier.get()

        corrige_mode = self.var_corrige.get()
        include_corrige = corrige_mode != "Aucun"
        if corrige_mode == "Tous à la fin":
            corrige_position = "a_la_fin"
        else:
            corrige_position = "apres_sujet"

        corrige_mode = "succinct" if self.var_corrige_mode.get() == "Succinct" else "complet"

        include_qr = (self.var_qr.get() == "Oui")
        include_nom = self.var_show_nom.get()
        include_consigne = self.var_show_consigne.get()
        consigne_texte = self.var_consigne.get().strip()
        difficulty_filter_enabled = self.var_diff_filter.get()
        difficulty_z_center = self.var_diff_zcenter.get()
        difficulty_z_tolerance = self.var_diff_ztol.get()
        difficulty_calibration_samples = self.var_diff_samples.get()
        difficulty_max_attempts = self.var_diff_attempts.get()

        # Construire la liste des exercices
        exercises = []
        for item in self.composition:
            exercises.append({
                'generator': REGISTRY[item['gen_id']],
                'config': item['config'],
            })

        self.status_var.set("Génération en cours...")
        self.update()

        try:
            doc = build_document(
                titre=titre,
                classe=classe,
                is_controle=is_controle,
                nb_sujets=nb_sujets,
                exercises=exercises,
                include_corrige=include_corrige,
                corrige_position=corrige_position,
                include_qr=include_qr,
                include_nom=include_nom,
                include_consigne=include_consigne,
                consigne_texte=consigne_texte,
                difficulty_filter_enabled=difficulty_filter_enabled,
                difficulty_z_center=difficulty_z_center,
                difficulty_z_tolerance=difficulty_z_tolerance,
                difficulty_calibration_samples=difficulty_calibration_samples,
                difficulty_max_attempts=difficulty_max_attempts,
                corrige_mode=corrige_mode,
            )

            # Écrire le fichier
            if not os.path.isabs(fichier):
                fichier = os.path.join(os.getcwd(), fichier)

            with open(fichier, 'w', encoding='utf-8') as f:
                f.write(doc)

            self.status_var.set(f"✅ Fichier généré : {fichier} ({nb_sujets} sujets)")
            messagebox.showinfo("Succès",
                                f"Fichier généré avec succès :\n{fichier}\n\n"
                                f"{nb_sujets} sujets × {len(exercises)} exercice(s)\n\n"
                                f"Compilez avec : xelatex {os.path.basename(fichier)}")

        except Exception as e:
            self.status_var.set(f"❌ Erreur : {e}")
            messagebox.showerror("Erreur", f"Erreur lors de la génération :\n{e}")

    def _clear_difficulty_cache(self):
        message = (
            "Supprimer le cache des statistiques de difficulté ?\n\n"
            "Le fichier difficulty_stats.json sera réinitialisé et les calibrations seront recalculées au besoin."
        )
        if not messagebox.askyesno("Statistiques de difficulté", message):
            return
        try:
            clear_difficulty_stats_cache(save=True)
            self.status_var.set("Cache des statistiques de difficulté réinitialisé.")
            messagebox.showinfo(
                "Statistiques de difficulté",
                "Le cache a été vidé. Les statistiques seront recalculées automatiquement lors des prochaines générations."
            )
        except Exception as e:
            messagebox.showerror("Erreur", f"Impossible de réinitialiser le cache :\n{e}")

    def _save_preset(self):
        """Sauvegarde la composition actuelle dans un fichier JSON."""
        if not self.composition:
            messagebox.showinfo("Info", "Rien à sauvegarder.")
            return

        f = filedialog.asksaveasfilename(
            defaultextension=".json",
            filetypes=[("Presets JSON", "*.json")],
            initialfile="preset.json"
        )
        if not f:
            return

        data = {
            'titre': self.var_titre.get(),
            'classe': self.var_classe.get(),
            'type': self.var_type.get(),
            'nb_sujets': self.var_nb_sujets.get(),
            'corrige': self.var_corrige.get(),
            'qr_codes': self.var_qr.get(),
            'corrige_mode': self.var_corrige_mode.get(),
            'fichier': self.var_fichier.get(),
            'afficher_nom': self.var_show_nom.get(),
            'afficher_consigne': self.var_show_consigne.get(),
            'consigne_texte': self.var_consigne.get(),
            'difficulty_filter_enabled': self.var_diff_filter.get(),
            'difficulty_z_center': self.var_diff_zcenter.get(),
            'difficulty_z_tolerance': self.var_diff_ztol.get(),
            'difficulty_calibration_samples': self.var_diff_samples.get(),
            'difficulty_max_attempts': self.var_diff_attempts.get(),
            'composition': self.composition,
        }
        with open(f, 'w', encoding='utf-8') as fh:
            json.dump(data, fh, ensure_ascii=False, indent=2)

        self.status_var.set(f"Preset sauvegardé : {f}")

    def _load_preset(self):
        """Charge un preset depuis un fichier JSON."""
        f = filedialog.askopenfilename(
            filetypes=[("Presets JSON", "*.json")]
        )
        if not f:
            return

        with open(f, 'r', encoding='utf-8') as fh:
            data = json.load(fh)

        self.var_titre.set(data.get('titre', ''))
        self.var_classe.set(data.get('classe', ''))
        self.var_type.set(data.get('type', 'Entraînement'))
        self.var_nb_sujets.set(data.get('nb_sujets', 38))

        # Backward compatibility: old presets had combined corrigé/QR options
        old_corrige = data.get('corrige', 'Après chaque sujet')
        if old_corrige == 'Corrigé + QR code':
            self.var_corrige.set('Après chaque sujet')
            self.var_qr.set('Oui')
        elif old_corrige == 'QR codes uniquement':
            self.var_corrige.set('Aucun')
            self.var_qr.set('Oui')
        else:
            self.var_corrige.set(old_corrige if old_corrige in ['Après chaque sujet', 'Tous à la fin', 'Aucun'] else 'Après chaque sujet')
            self.var_qr.set(data.get('qr_codes', 'Oui'))

        self.var_corrige_mode.set(data.get('corrige_mode', 'Complet'))

        self.var_fichier.set(data.get('fichier', 'sujet.tex'))
        self.var_show_nom.set(data.get('afficher_nom', False))
        self.var_show_consigne.set(data.get('afficher_consigne', False))
        self.var_consigne.set(data.get('consigne_texte', "La qualité de la rédaction entre en compte dans la notation"))
        self.var_diff_filter.set(data.get('difficulty_filter_enabled', False))
        self.var_diff_zcenter.set(data.get('difficulty_z_center', 0.0))
        self.var_diff_ztol.set(data.get('difficulty_z_tolerance', data.get('difficulty_z_abs_max', 0.75)))
        self.var_diff_samples.set(data.get('difficulty_calibration_samples', 80))
        self.var_diff_attempts.set(data.get('difficulty_max_attempts', 40))
        self.composition = data.get('composition', [])
        self._refresh_composition()

        self.status_var.set(f"Preset chargé : {f}")


def main():
    app = AntibiApp()
    app.mainloop()


if __name__ == '__main__':
    main()
