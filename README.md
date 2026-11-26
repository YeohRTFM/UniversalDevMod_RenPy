# Universal Dev Mod pour Ren'Py

Un mod universel à glisser dans n'importe quel jeu Ren'Py. Il active le mode développeur et affiche, **directement dans les choix de menu**, l'effet de chaque option sur les variables du jeu :

- 🟢 **vert** : la variable augmente (ou passe à `True`)
- 🔴 **rouge** : la variable diminue (ou passe à `False`)
- 🟡 **jaune** : changement de texte ou de type non numérique

Exemple d'affichage dans un menu :

```
Aider le marchand   ( confiance: +2 | argent: -50 )
Le voler            ( confiance: -3 | suspicion: +1 )
```

## Installation

1. Copie `00_universal_dev_mod.rpy` dans le dossier `game/` du jeu.
2. Lance le jeu : un bouton **Dev Mod: ON/OFF** apparaît en haut à droite de l'écran.
3. Pour retirer le mod, supprime simplement le fichier (et le `.rpyc` associé).

## Utilisation

Clique sur le bouton **Dev Mod** pour activer ou désactiver les annotations. Le choix est mémorisé dans `persistent`, donc conservé entre les sessions.

> Le changement s'applique **au prochain menu affiché**, pas à celui déjà à l'écran.

## Raccourcis clavier

Le mod n'ajoute **aucun raccourci personnalisé** : tout passe par le bouton à l'écran. En revanche, il active le mode développeur de Ren'Py (`config.developer`), ce qui débloque les raccourcis natifs suivants :

| Raccourci | Action |
|-----------|--------|
| `Shift + D` | Menu développeur (labels, variables, performances...) |
| `Shift + O` | Console (permet de lire et modifier les variables en direct) |
| `Shift + R` | Recharger le script sans quitter le jeu |
| `Shift + E` | Ouvrir le script courant dans l'éditeur |
| `Shift + I` | Inspecteur de styles |

Exemple dans la console (`Shift + O`) : `confiance = 10` ou `renpy.jump("chapitre2")`.

### Ajouter un raccourci pour le toggle (optionnel)

Dans l'écran `dev_mod_toggle_button` du fichier, ajoute cette ligne pour basculer le mod avec `Alt + D` :

```renpy
key "alt_K_d" action Function(toggle_dev_mod)
```

## Réglages

En haut du fichier, dans la section `REGLAGES` :

| Variable | Rôle |
|----------|------|
| `_UCD_FORCE_DEVELOPER` | `True` force `config.developer` et `config.console`. Mets `False` pour une version publique. |
| `_UCD_INVERTED` | Liste des variables où **monter est mauvais** (ex. `stress`, `corruption`) : leurs hausses s'affichent en rouge. |
| `_UCD_UP` / `_UCD_DOWN` / `_UCD_NEUTRAL` | Couleurs (hexadécimal) des hausses, baisses et changements neutres. |
| `_UCD_MAX_DEPTH` | Profondeur maximale de suivi des `call` / `jump` (8 par défaut). |

## Comment ça marche

1. Un callback Ren'Py (`config.statement_callbacks`) se déclenche avant chaque `menu`.
2. Pour chaque choix dont la condition est vraie, le mod **simule** le bloc : affectations (`$ x += 1`, `x = 5`, `x *= 2`...), `if`, `call`, `jump`, `return`.
3. Il compare les valeurs avant/après et ajoute le résultat coloré au libellé du choix.
4. Désactiver le mod retire proprement les annotations.

## Limites connues

- Seules les variables `bool`, `int`, `float` et texte sont suivies (pas les listes, dictionnaires ni objets).
- Les modifications situées **après** la fin du bloc de choix ne sont pas analysées.
- Les expressions contenant `renpy`, `random` ou `input` sont ignorées, pour ne pas fausser l'aléatoire du jeu.
- Les affectations multiples (`a, b = 1, 2`) sont ignorées.
- Les jeux qui remplacent complètement l'écran `choice` peuvent afficher les annotations différemment.

## Dépannage

Les erreurs internes du mod ne font pas planter le jeu : elles sont écrites dans `log.txt` (préfixe `UCD error`). Si tu signales un problème, joins cette ligne.

## Version publique du jeu

Avant de distribuer ton jeu, mets `_UCD_FORCE_DEVELOPER = False` ou retire le fichier, sinon les joueurs auront accès à la console et au menu développeur.
