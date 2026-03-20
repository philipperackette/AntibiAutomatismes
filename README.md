# AntibiAutomatismes

Générateur de sujets de mathématiques inspiré de la méthode d’André Antibi.

L’objectif est de produire des feuilles d’entraînement et des contrôles composés d’exercices **proches de ceux déjà travaillés en classe**, avec une **même structure** mais des **données numériques différentes** selon les sujets.

Le projet vise donc une évaluation plus lisible, plus juste et plus sereine : l’élève doit être évalué sur des techniques réellement entraînées, et non sur des pièges ou des variations imprévues.

## Idée pédagogique

Ce projet s’inscrit dans l’esprit de l’**évaluation par contrat de confiance (EPCC)** défendue par André Antibi :

- la phase d’apprentissage et la phase d’évaluation sont clairement distinguées ;
- les exercices donnés en contrôle sont proches de ceux préparés à l’entraînement ;
- on évite de transformer l’évaluation en outil de sélection par l’échec ;
- la difficulté peut être pilotée pour obtenir des sujets comparables.

Dans cette logique, **AntibiAutomatismes** automatise la fabrication de sujets individualisés tout en conservant une structure familière pour les élèves.

## Ce que fait le projet

L’application permet de :

- composer un sujet à partir d’un catalogue d’exercices ;
- configurer chaque exercice ;
- générer plusieurs sujets individualisés ;
- produire un fichier `.tex` prêt à compiler ;
- inclure des corrigés complets ou succincts ;
- inclure des QR codes de réponses ;
- sauvegarder et recharger des compositions de sujets au format JSON ;
- filtrer statistiquement la difficulté pour rapprocher les sujets d’un niveau cible.

## Public visé

Ce projet s’adresse principalement à des enseignants de mathématiques souhaitant :

- préparer des entraînements et contrôles dans l’esprit de la méthode Antibi ;
- générer rapidement plusieurs versions d’un même sujet ;
- conserver une cohérence de difficulté entre les sujets ;
- gagner du temps sur la mise en page et la variation des données.

## Niveaux et exercices actuellement disponibles

### 5e
- Sommes de relatifs
- Priorités opératoires
- Distributivité simple

### 3e
- Réduction d’expressions
- Développement
- Équations du 1er degré
- Équations produit
- Théorème de Pythagore
- Théorème de Thalès

### 2nde
- Puissances de 10
- Inéquations du 1er degré
- Racines carrées
- Calcul fractionnaire
- Vecteurs — coordonnées
- Équations de droites
- Inéquations produit / quotient

## Fonctionnement général

L’application propose une interface graphique Tkinter avec :

- des **paramètres globaux** : titre, classe, type de devoir, nombre de sujets ;
- un **catalogue d’exercices** classés par niveau ;
- une **composition de sujet** modifiable ;
- une **génération LaTeX** avec corrigés, QR codes et options de présentation.

Le cœur du projet repose sur trois fichiers principaux :

- `main.py` : interface graphique et orchestration ;
- `generators.py` : générateurs d’exercices ;
- `latex_builder.py` : assemblage du document LaTeX final.

## Installation

### Prérequis Python
- Python 3.8 ou plus récent
- `sympy`
- `tkinter` (souvent inclus avec Python selon les systèmes)

Installation minimale :

```bash
pip install sympy
```

## Lancement

```bash
python main.py
```

## Compilation LaTeX

Le programme génère un fichier `.tex`.

Compilation recommandée :

```bash
xelatex sujet.tex
```

Packages LaTeX utilisés :
- `amsmath`
- `lmodern`
- `babel`
- `geometry`
- `pgf`
- `tikz`
- `tkz-tab`
- `fancyhdr`
- `qrcode`
- `enumitem`
- `datetime2`

## Exemple d’usage

1. Choisir le titre, la classe et le type de document.
2. Ajouter des exercices depuis le catalogue.
3. Configurer chaque exercice.
4. Définir le nombre de sujets à produire.
5. Choisir le mode de corrigé et l’option QR code.
6. Générer le fichier `.tex`.
7. Compiler en PDF avec XeLaTeX.

## Presets et personnalisation

Les compositions peuvent être sauvegardées et rechargées en JSON.

Cela permet de :
- réutiliser un devoir d’une année sur l’autre ;
- conserver des banques de sujets types ;
- préparer rapidement plusieurs variantes d’un même chapitre.

## Gestion de la difficulté

Le projet inclut un mécanisme de calibration statistique de la difficulté :

- estimation d’une difficulté brute par exercice ;
- stockage de statistiques dans `difficulty_stats.json` ;
- filtrage par cible de difficulté ;
- limitation du nombre de tentatives de génération.

Cette partie est particulièrement utile pour éviter que deux sujets d’un même contrôle aient des niveaux trop différents.

## Ajouter un nouvel exercice

Pour créer un nouveau générateur, il suffit d’ajouter dans `generators.py` une classe décorée par `@register` :

```python
@register
class MonExercice(ExerciseGenerator):
    id = "mon_exercice"
    name = "Mon exercice"
    niveau = "3e"
    category = "Calcul littéral"
    description = "Description de l'exercice"

    @staticmethod
    def get_config():
        return [
            {
                "key": "nb_questions",
                "label": "Nombre de questions",
                "type": "int",
                "default": 5,
                "min": 1,
                "max": 20
            }
        ]

    def generate(self, config):
        return {
            "enonce": "...",
            "corrige": "...",
            "corrige_succinct": "...",
            "qr_data": None,
            "qr_answers": [],
            "difficulte_raw": 0.0
        }
```

Le générateur apparaît ensuite automatiquement dans l’interface.

## Philosophie du projet

AntibiAutomatismes n’est pas seulement un générateur d’exercices aléatoires.

Le projet cherche à fournir un outil compatible avec une certaine conception de l’évaluation :

- on entraîne sur des types d’exercices identifiés ;
- on contrôle sur des exercices du même type ;
- on fait varier les données plutôt que de changer subrepticement la nature des tâches ;
- on cherche la justice pédagogique autant que l’efficacité pratique.

## État du projet

Le projet est déjà utilisable pour produire de vrais sujets.

Il reste néanmoins perfectible sur plusieurs points :
- enrichissement du catalogue d’exercices ;
- homogénéisation de la difficulté entre chapitres ;
- amélioration de la documentation ;
- ajout de tests automatiques ;
- amélioration de l’export PDF ou du flux de compilation.

## Auteur et statut

Projet personnel d’automatisation pour la génération de sujets de mathématiques dans l’esprit de la méthode Antibi.

## Licence

Code source : MIT  
Documentation et contenus pédagogiques : CC BY 4.0
