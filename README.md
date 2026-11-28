# Universal Dev Mod pour Ren'Py

Un mod universel à glisser dans n'importe quel jeu Ren'Py. Il fait deux choses :

1. Il active le mode développeur et affiche, **directement dans les choix de menu**, l'effet de chaque option sur les variables du jeu.
2. Il **bloque les ouvertures externes** : pages web qui s'ouvrent toute seules (Patreon à la fermeture, etc.) et connexions réseau sortantes (métriques, mises à jour).

### Affichage dans les choix

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
2. Lance le jeu : une pastille ronde apparaît en bas à gauche de l'écran.
3. Pour retirer le mod, supprime simplement le fichier (et le `.rpyc` associé).

## Utilisation

Une petite **pastille ronde** discrète apparaît en **bas à gauche** de l'écran (semi-transparente au repos, pleinement visible au survol) :

- 🟢 pastille verte : annotations des choix actives
- ⚪ pastille grise : annotations désactivées

Clique dessus pour ouvrir la **fenêtre de réglages** :

| Option | Rôle |
|--------|------|
| **Annotations des choix** | Active ou désactive l'affichage vert/rouge dans les menus. |
| **Accès externes** | Bloque ou libère les pages web et les connexions réseau. Le nombre entre parenthèses est le nombre de tentatives bloquées depuis le lancement. |
| **Position de la pastille** | Haut gauche, haut droite, bas gauche ou bas droite, pour éviter le HUD du jeu. La fenêtre s'ouvre toujours du côté de la pastille. |
| **Fermer** | Referme la fenêtre (un clic sur la pastille fait pareil). |

Les réglages sont mémorisés dans `persistent` (annotations, blocage et position). La fenêtre est toujours fermée au lancement du jeu. Le blocage est **actif par défaut**.

## Raccourcis clavier

Le mod n'ajoute **aucun raccourci personnalisé** : tout passe par la pastille à l'écran. En revanche, il active le mode développeur de Ren'Py (`config.developer`), ce qui débloque les raccourcis natifs suivants :

| Raccourci | Action |
|-----------|--------|
| `Shift + D` | Menu développeur (labels, variables, performances...) |
| `Shift + O` | Console (permet de lire et modifier les variables en direct) |
| `Shift + R` | Recharger le script sans quitter le jeu |
| `Shift + E` | Ouvrir le script courant dans l'éditeur |
| `Shift + I` | Inspecteur de styles |

Exemple dans la console (`Shift + O`) : `confiance = 10` ou `renpy.jump("chapitre2")`.

### Ajouter un raccourci pour le toggle (optionnel)

Dans l'écran `dev_mod_toggle_button` du fichier, ajoute cette ligne (juste après `zorder 1000`) pour ouvrir ou fermer la fenêtre de réglages avec `Alt + D` :

```renpy
key "alt_K_d" action Function(ucd_toggle_panel)
```

## Réglages

En haut du fichier, dans la section `REGLAGES` :

| Variable | Rôle |
|----------|------|
| `_UCD_FORCE_DEVELOPER` | `True` force `config.developer` et `config.console`. Mets `False` pour une version publique. |
| `_UCD_INVERTED` | Liste des variables où **monter est mauvais** (ex. `stress`, `corruption`) : leurs hausses s'affichent en rouge. |
| `_UCD_UP` / `_UCD_DOWN` / `_UCD_NEUTRAL` | Couleurs (hexadécimal) des hausses, baisses et changements neutres. |
| `_UCD_MAX_DEPTH` | Profondeur maximale de suivi des `call` / `jump` (8 par défaut). |
| `_UCD_BLOCK_NETWORK` | `True` coupe aussi les connexions sortantes. `False` ne bloque que les pages web. |
| `_UCD_ALLOWED_HOSTS` | Hôtes autorisés malgré le blocage, ex. `("api.mon-jeu.com",)` pour un jeu qui a besoin d'un serveur. |
| `_UCD_DOT_SIZE` | Diamètre de la pastille en pixels (26 par défaut). |
| `_UCD_DOT_IDLE_ALPHA` | Opacité de la pastille au repos, de 0 à 255 (110 par défaut). Baisse la valeur pour la rendre plus discrète. |
| `_UCD_MARGIN` | Marge entre la pastille et le bord de l'écran. |

## Blocage des accès externes

Quand le blocage est actif, le mod neutralise :

- `webbrowser.open`, `open_new`, `open_new_tab` et `webbrowser.get()` ;
- l'action d'écran `OpenURL` ;
- les commandes système contenant une URL (`subprocess`, `os.system`, `os.startfile`) ;
- les connexions réseau sortantes (`connect`, `connect_ex`, `sendto`) et la résolution DNS, sauf vers `localhost` / `127.x` ;
- chaque tentative est écrite dans `log.txt` (`UCD blocked ...`), et une notification s'affiche pour les pages web.

Le jeu voit une connexion refusée ou un navigateur introuvable, ce qui est géré sans plantage par la plupart des jeux.

### Ce que ce blocage ne garantit pas

C'est un blocage **au niveau Python, dans le même processus que le jeu**. Il arrête les pratiques courantes, mais pas un code qui contourne volontairement Python (`ctypes`, bibliothèques natives, etc.). **Ce n'est pas un bac à sable.** Pour une vraie isolation :

- **Windows** : règle sortante bloquante dans le pare-feu Windows pour l'exécutable du jeu.
- **Linux** : lancer le jeu avec `firejail --net=none` ou `unshare -n`.
- **macOS** : un pare-feu applicatif comme LuLu ou Little Snitch.

## Comment ça marche (annotations)

1. Un callback Ren'Py (`config.statement_callbacks`) se déclenche avant chaque `menu`.
2. Pour chaque choix dont la condition est vraie, le mod **simule** le bloc : affectations (`$ x += 1`, `x = 5`, `x *= 2`...), `if`, `call`, `jump`, `return`.
3. Il compare les valeurs avant/après et ajoute le résultat coloré au libellé du choix.
4. Désactiver le mod retire proprement les annotations.

## Limites connues

- Seules les variables `bool`, `int`, `float` et texte sont suivies (pas les listes, dictionnaires ni objets).
- Les modifications situées **après** la fin du bloc de choix ne sont pas analysées.
- Les expressions contenant `renpy`, `random` ou `input` sont ignorées, pour ne pas fausser l'aléatoire du jeu.
- Les affectations multiples (`a, b = 1, 2`) sont ignorées.
- La pastille n'apparaît pas dans le menu principal (comme tous les écrans d'overlay de Ren'Py), seulement en jeu.
- Les jeux qui remplacent complètement l'écran `choice` peuvent afficher les annotations différemment.
- Un jeu qui a **besoin** du réseau (multijoueur, mise à jour, serveur de comptes) cessera de fonctionner tant que le blocage est actif : passe le bouton sur **LIBRE** ou ajoute l'hôte à `_UCD_ALLOWED_HOSTS`.

## Dépannage

Les erreurs internes du mod ne font pas planter le jeu : elles sont écrites dans `log.txt` (préfixe `UCD error`). Si tu signales un problème, joins cette ligne.

## Version publique du jeu

Avant de distribuer ton propre jeu, mets `_UCD_FORCE_DEVELOPER = False` ou retire le fichier, sinon les joueurs auront accès à la console et au menu développeur.
