# Ren'Py Universal Dev Mod & Choice Descriptor (`_ZLZK_UCD`)

Un mod universel léger pour les jeux sous **Ren'Py** (versions 7.x et 8.x). Il active les outils de développement, ajoute la console et insère dynamiquement le détail des modifications de variables à côté de chaque choix de dialogue.

## 🌟 Fonctionnalités

- **Aperçu des choix (`Choice Descriptor`)** : Analyse le code des menus et affiche en direct les variations de variables (ex: `{color=#ee3}( love: +1 | quest_flag: True ){/color}`).
- **Mode Dev & Console** : Active `config.developer` et `config.console`.
- **Bouton d'activation On/Off rapide** : Un overlay discret apparaît en haut à droite de l'écran pour activer ou désactiver le mod à tout moment sans relancer le jeu.
- **Nettoyage dynamique** : Lorsque le mod est désactivé via le bouton, les annotations sur les choix disparaissent immédiatement pour ne pas polluer l'interface.
---

## 📥 Installation

1. Télécharge le fichier du mod (ex: `00_universal_dev_mod.rpy`).
2. Copie-le dans le dossier `game/` du jeu Ren'Py ciblé :
   ```text
   DossierDuJeu/
   └── game/
       └── 00_universal_dev_mod.rpy
---

## 🎮 Utilisation

Clique sur le bouton Dev Mod: ON / OFF (coin supérieur droit) pour basculer le mode. Le ré-affichage du menu en cours est instantané.

Raccourcis Ren'Py (Lorsque le mod est sur ON) :

- Shift + O : Ouvrir la console Ren'Py.
- Shift + D : Ouvrir le menu Développeur Ren'Py.
- Shift + R : Recharger le script/jeu à chaud.
