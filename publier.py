# -*- coding: utf-8 -*-
"""
PUBLICATION AUTOMATIQUE du site veille Coimbra sur GitHub Pages.

Appele en fin de chaque run planifie (veille_sejour.bat a 9h00,
veille_coimbra.bat a 9h20 et 13h00 - horaires decales, donc jamais deux
publications en meme temps) :

  1. regenere les 3 pages (generer_site.main());
  2. git add -A ; si rien n'a change -> sortie silencieuse ;
  3. sinon commit + push (GitHub Pages redeploie tout seul).

Hebergement GitHub Pages = pushes illimites et gratuits (le site a quitte
Netlify le 2026-07-12 : la-bas chaque deploiement coutait 15 credits sur
les 300/mois du compte, reserves a Champigrond).

REPO PUBLIC : l'identite Git du depot est l'adresse noreply GitHub
(configuree en local dans .git/config). Ne jamais y remettre le courriel
perso ni aucun nom.

Chaque decision (pousse / rien a pousser / erreur) est journalisee dans
publier.log. Une erreur (reseau, push refuse) n'interrompt JAMAIS la
veille appelante : code retour toujours 0.

Usage manuel :  python publier.py
"""

import subprocess
import sys
from datetime import datetime
from pathlib import Path

HERE = Path(__file__).parent
LOG_FILE = HERE / "publier.log"


def log(message):
    stamp = datetime.now().isoformat(timespec="seconds")
    line = f"{stamp} | {message}"
    print(line)
    with LOG_FILE.open("a", encoding="utf-8") as f:
        f.write(line + "\n")


def git(*args, check=True):
    return subprocess.run(["git", *args], cwd=HERE, check=check,
                          capture_output=True, text=True)


def main():
    # 1. Regeneration des pages
    try:
        sys.path.insert(0, str(HERE))
        import generer_site
        generer_site.main()
    except Exception as e:
        log(f"ECHEC generation du site : {e}")
        return

    # 2. Quelque chose a changer ?
    try:
        git("add", "-A")
        if git("diff", "--cached", "--quiet", check=False).returncode == 0:
            log("Rien a pousser (contenu inchange).")
            return
    except Exception as e:
        log(f"ECHEC git add/diff : {e}")
        return

    # 3. Commit + push
    try:
        stamp = datetime.now().strftime("%Y-%m-%d %H:%M")
        git("commit", "-m", f"Mise a jour automatique des annonces ({stamp})")
        git("push")
        log("Site pousse sur GitHub - Pages va redeployer.")
    except subprocess.CalledProcessError as e:
        log(f"ECHEC commit/push : {(e.stderr or e.stdout or '').strip()[:300]}")
    except Exception as e:
        log(f"ECHEC commit/push : {e}")


if __name__ == "__main__":
    main()
    sys.exit(0)   # ne jamais faire echouer la veille appelante
