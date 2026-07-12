# -*- coding: utf-8 -*-
"""
Genere le SITE PUBLIC des deux veilles logement Coimbra, a partager par lien
(pensees pour etre consultees par lien, sans email). Aucun nom ni donnee
personnelle sur les pages ni dans ce depot.

Produit 3 fichiers statiques dans CE dossier (racine du repo GitHub PUBLIC
LaVieEstUnJeu/veille-coimbra, servi par GitHub Pages - repo public : ne
JAMAIS y mettre nom, courriel perso ou secret ; identite Git du depot =
adresse noreply GitHub) :
    index.html          accueil avec les liens vers les 2 pages
    longue-duree.html   tableau triable des T2 longue duree (scraper-t2)
    courte-duree.html   tableau triable des logements meubles (sejour-temporaire)

Donnees lues (jamais modifiees) :
    ../scraper-t2/data/resultats-tous-t2.json  + listings-vues.json (first_seen)
    ../sejour-temporaire/data/resultats-sejour.json + annonces-vues.json

Le tri des colonnes est du JavaScript pur embarque (aucune dependance, aucun
CDN). Tri par defaut : DATE DE DECOUVERTE decroissante (les plus recentes en
premier, demande de Chham du 2026-07-12) ; tous les autres tris au clic.

La distance a l'ecole (page longue duree) est l'ESTIMATION PAR QUARTIER de la
veille T2 (core/heuristics.py), pas une mesure a l'adresse : c'est ecrit sur
la page.

Usage :  python generer_site.py   (generation seule)
         python publier.py        (generation + commit + push automatiques,
                                   appele par les taches planifiees)
"""

import html
import json
import sys
from datetime import date
from pathlib import Path

HERE = Path(__file__).parent
T2_DIR = HERE.parent / "scraper-t2"
SEJOUR_DIR = HERE.parent / "sejour-temporaire"

# Importe les heuristiques de la veille T2 (distance ecole, meuble, agence
# incertaine) avec SON config. Un seul projet importe : pas de collision.
sys.path.insert(0, str(T2_DIR))
from core.heuristics import furnished_status, is_uncertain, walk_distance  # noqa: E402


# ------------------------------------------------------------------
# Chargement des donnees
# ------------------------------------------------------------------

def _load(path):
    return json.loads(path.read_text(encoding="utf-8"))


def _first_seen_map(state_file):
    state = _load(state_file)
    return {key: entry.get("first_seen") or ""
            for key, entry in (state.get("listings") or {}).items()}


def load_t2():
    data = _load(T2_DIR / "data" / "resultats-tous-t2.json")
    seen = _first_seen_map(T2_DIR / "data" / "listings-vues.json")
    for item in data["listings"]:
        item["first_seen"] = seen.get(f"{item['source']}:{item['id']}", "")
    return data


def load_sejour():
    data = _load(SEJOUR_DIR / "data" / "resultats-sejour.json")
    seen = _first_seen_map(SEJOUR_DIR / "data" / "annonces-vues.json")
    for item in data["listings"]:
        item["first_seen"] = seen.get(f"{item['source']}:{item['id']}", "")
    return data


# ------------------------------------------------------------------
# Briques HTML communes
# ------------------------------------------------------------------

STYLE = """
:root { --vert:#1e7a3e; --rouge:#a71f10; --gris:#666; }
* { box-sizing:border-box; }
body { font-family:Arial,Helvetica,sans-serif; margin:0; color:#1a1a1a; background:#f7f7f5; }
header { background:#1a1a1a; color:#fff; padding:18px 16px; }
header h1 { margin:0 0 6px; font-size:22px; }
header p { margin:2px 0; color:#ccc; font-size:13px; }
header a { color:#9fd4ae; }
main { max-width:1200px; margin:0 auto; padding:14px 10px 40px; }
.note { background:#fdf6e3; border:1px solid #e6d9a8; border-radius:8px; padding:8px 12px;
        font-size:13px; color:#6b5a00; margin:12px 0; }
input#filtre { width:100%; max-width:420px; padding:8px 10px; margin:10px 0; font-size:14px;
        border:1px solid #bbb; border-radius:6px; }
.table-wrap { overflow-x:auto; background:#fff; border:1px solid #ddd; border-radius:8px; }
table { border-collapse:collapse; width:100%; font-size:13px; min-width:900px; }
th { background:#efefec; text-align:left; padding:8px 8px; cursor:pointer; white-space:nowrap;
     user-select:none; position:sticky; top:0; }
th:hover { background:#e3e3de; }
th .fl { color:#999; font-size:11px; }
td { padding:7px 8px; border-top:1px solid #eee; vertical-align:top; }
tr:hover td { background:#f4f9f5; }
td.prix { font-weight:bold; white-space:nowrap; }
.prio td.prix { color:var(--vert); }
.badge-warn { background:#fdeeec; color:var(--rouge); border:1px solid #c0392b;
        padding:1px 6px; border-radius:4px; font-size:11px; font-weight:bold; }
.badge-verif { background:#fdf6e3; color:#8a6d00; border:1px solid #d8c56f;
        padding:1px 6px; border-radius:4px; font-size:11px; }
a.lien { color:#155ab6; }
footer { text-align:center; color:#999; font-size:12px; padding:18px; }
.cards { display:flex; gap:16px; flex-wrap:wrap; margin-top:18px; }
.card { flex:1 1 300px; background:#fff; border:1px solid #ddd; border-radius:10px;
        padding:18px; text-decoration:none; color:inherit; }
.card:hover { border-color:#1e7a3e; }
.card h2 { margin:0 0 8px; font-size:18px; color:#1e7a3e; }
.card p { margin:4px 0; font-size:13px; color:#444; }
"""

SORT_JS = """
function initTable() {
  const table = document.querySelector('table');
  const tbody = table.querySelector('tbody');
  let dir = {};
  table.querySelectorAll('th').forEach((th, col) => {
    th.addEventListener('click', () => {
      const asc = !(dir[col] === 'asc');
      dir = {}; dir[col] = asc ? 'asc' : 'desc';
      table.querySelectorAll('th .fl').forEach(f => f.textContent = '\\u21C5');
      th.querySelector('.fl').textContent = asc ? '\\u2191' : '\\u2193';
      const rows = Array.from(tbody.querySelectorAll('tr'));
      rows.sort((a, b) => {
        const va = a.children[col].dataset.v, vb = b.children[col].dataset.v;
        const na = parseFloat(va), nb = parseFloat(vb);
        let cmp;
        if (!isNaN(na) && !isNaN(nb)) cmp = na - nb;
        else cmp = String(va).localeCompare(String(vb), 'fr');
        return asc ? cmp : -cmp;
      });
      rows.forEach(r => tbody.appendChild(r));
    });
  });
  const filtre = document.getElementById('filtre');
  filtre.addEventListener('input', () => {
    const q = filtre.value.toLowerCase();
    tbody.querySelectorAll('tr').forEach(r => {
      r.style.display = r.textContent.toLowerCase().includes(q) ? '' : 'none';
    });
  });
  // tri par defaut (serveur) = "Detectee le" decroissant : afficher la
  // fleche et armer l'etat pour que le premier clic inverse le sens
  const def = table.querySelector('th[data-default]');
  if (def) {
    const col = Array.from(def.parentNode.children).indexOf(def);
    dir[col] = 'desc';
    def.querySelector('.fl').textContent = '\\u2193';
  }
}
document.addEventListener('DOMContentLoaded', initTable);
"""


def esc(v):
    return html.escape(str(v if v is not None else ""))


def cell(display, sort_value=None, css=""):
    sv = esc(sort_value if sort_value is not None else display)
    cls = f" class='{css}'" if css else ""
    return f"<td{cls} data-v=\"{sv}\">{display}</td>"


def page(title, subtitle_lines, note, headers, rows_html, generated):
    # la colonne "Détectée le" porte le tri par defaut (decroissant), le JS
    # y pose la fleche au chargement
    ths = "".join(
        f"<th{' data-default=\"1\"' if h == 'Détectée le' else ''}>{esc(h)} <span class='fl'>⇅</span></th>"
        for h in headers)
    subs = "".join(f"<p>{line}</p>" for line in subtitle_lines)
    return f"""<!DOCTYPE html>
<html lang="fr">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<meta name="robots" content="noindex">
<title>{esc(title)}</title>
<style>{STYLE}</style>
</head>
<body>
<header>
<h1>{esc(title)}</h1>
{subs}
<p><a href="index.html">&larr; Accueil</a></p>
</header>
<main>
<div class="note">{note}</div>
<input id="filtre" type="text" placeholder="Filtrer (quartier, agence, source...)">
<div class="table-wrap">
<table>
<thead><tr>{ths}</tr></thead>
<tbody>
{rows_html}
</tbody>
</table>
</div>
</main>
<footer>Page g&eacute;n&eacute;r&eacute;e le {generated} &middot; cliquer un en-t&ecirc;te de colonne pour trier</footer>
<script>{SORT_JS}</script>
</body>
</html>"""


def _sort_key(item):
    """Tri par defaut du site : date de decouverte DECROISSANTE (les plus
    recentes en premier, demande de Chham du 2026-07-12), rien d'autre.
    A utiliser avec sorted(..., reverse=True) ; les dates manquantes
    ("0000") tombent en fin de tableau."""
    return item.get("first_seen") or "0000-00-00"


def _sources_label(item):
    label = item.get("source") or ""
    also = item.get("also_on") or []
    if also:
        label += ", " + ", ".join(a.get("source", "?") for a in also)
    return label


def _num(v, fmt="{:.0f}"):
    try:
        return fmt.format(float(v))
    except (TypeError, ValueError):
        return ""


# ------------------------------------------------------------------
# Page longue duree (T2)
# ------------------------------------------------------------------

def build_t2(data):
    rows = []
    for it in sorted(data["listings"], key=_sort_key, reverse=True):
        price = it.get("price_eur")
        prio = price is not None and price <= 900
        agency = it.get("agency") or "non précisée"
        if is_uncertain(it):
            agency = "<span class='badge-verif'>particulier, à vérifier</span>"
        else:
            agency = esc(agency)
        dist = walk_distance(it).replace(" (estimation par quartier)", "")
        row = "<tr class='prio'>" if prio else "<tr>"
        row += cell(_num(price) + " €" if price is not None else "?", price or 99999, "prix")
        row += cell(_num(it.get("area_m2")) or "?", it.get("area_m2") or 0)
        row += cell(esc(it.get("location") or "?"))
        row += cell(esc(furnished_status(it)))
        row += cell(esc(dist))
        row += cell(esc(it.get("energy") or "Inconnu"))
        row += cell(agency, sort_value=("zzz particulier" if is_uncertain(it) else it.get("agency") or "zz"))
        row += cell(esc(it.get("first_seen") or "?"))
        row += cell(esc(_sources_label(it)))
        row += cell(f"<a class='lien' href='{esc(it.get('url'))}' target='_blank' rel='noopener'>Voir</a>", "-")
        rows.append(row + "</tr>")

    scraped = (data.get("scraped_at") or "")[:16].replace("T", " ")
    note = ("La <b>distance à l'école</b> (Centro Básica da Solum Sul) est une <b>estimation par "
            "quartier</b>, pas une mesure à l'adresse. Les annonces de <b>particuliers</b> sont à "
            "vérifier avant tout engagement (risque d'arnaque : jamais de paiement sans visite et "
            "sans vérification de l'annonceur). Lignes vertes = loyer &le; 900 €.")
    return page(
        "Location longue durée - T2 à Coimbra",
        [f"Bail 12 mois (visa D7) · quartiers Solum / Santo António dos Olivais · {len(rows)} annonces",
         f"Sites interrogés : Imovirtual, ERA, Remax, Century21, KW Union, Idealista, Supercasa, Casa Sapo, OLX · dernier relevé : {scraped}"],
        note,
        ["Prix", "m²", "Quartier", "Meublé", "École (à pied)", "Énergie",
         "Annonceur", "Détectée le", "Source(s)", "Annonce"],
        "\n".join(rows), date.today().isoformat())


# ------------------------------------------------------------------
# Page courte duree
# ------------------------------------------------------------------

def build_sejour(data):
    rows = []
    for it in sorted(data["listings"], key=_sort_key, reverse=True):
        price = it.get("price_eur")
        prio = price is not None and price <= 1000 and it.get("available_from")
        platform = esc(it.get("agency") or it.get("source") or "?")
        if it.get("warning"):
            platform += " <span class='badge-warn'>&#9888; litiges remboursement</span>"
        min_days = it.get("min_stay_days")
        min_txt, min_sort = "", 0
        if min_days:
            months = min_days // 30
            min_txt = f"{months} mois" if months >= 1 else f"{min_days} j"
            min_sort = min_days
            if min_days > 31:
                min_txt += " &#9888;"
        charges = {True: "incluses", False: "en sus"}.get(it.get("utilities_included"), "?")
        row = "<tr class='prio'>" if prio else "<tr>"
        row += cell(_num(price) + " €/mois" if price is not None else "?", price or 99999, "prix")
        row += cell(esc(it.get("type") or "?"))
        row += cell(it.get("bedrooms") if it.get("bedrooms") is not None else "?", it.get("bedrooms") or 0)
        row += cell(it.get("persons") if it.get("persons") is not None else "?", it.get("persons") or 0)
        row += cell(_num(it.get("area_m2")) or "?", it.get("area_m2") or 0)
        row += cell(esc(it.get("available_from") or "indispo. sept."),
                    it.get("available_from") or "zzzz")
        row += cell(min_txt or "?", min_sort)
        row += cell(charges)
        row += cell(esc((it.get("location") or "")[:70]))
        row += cell(platform, sort_value=("zzz uniplaces" if it.get("warning") else it.get("agency") or "zz"))
        row += cell(esc(it.get("first_seen") or "?"))
        row += cell(f"<a class='lien' href='{esc(it.get('url'))}' target='_blank' rel='noopener'>Voir</a>", "-")
        rows.append(row + "</tr>")

    scraped = (data.get("scraped_at") or "")[:16].replace("T", " ")
    note = ("Séjour visé : <b>1 mois ferme, arrivée septembre 2026, 2 personnes, logement entier</b>. "
            "&#9888; = séjour minimum plus long que le mois visé, ou plateforme à litiges "
            "(Uniplaces : réserver en dernier recours, jamais plus d'un mois d'avance). "
            "Règles d'or : jamais de paiement hors plateforme ; visite vidéo en direct avant de "
            "réserver ; tout documenter par photos horodatées dans les premières 24-48h. "
            "Lignes vertes = dispo en septembre et &le; 1000 €/mois.")
    return page(
        "Location courte durée - logements meublés à Coimbra",
        [f"Logements ENTIERS meublés, réservables en ligne · {len(rows)} annonces",
         f"Plateformes : Flatio, HousingAnywhere, Spotahome, Inlife, Spacest, Uniplaces · dernier relevé : {scraped}"],
        note,
        ["Prix", "Type", "Ch.", "Pers.", "m²", "Dispo dès", "Séjour min.", "Charges",
         "Annonce", "Plateforme", "Détectée le", "Lien"],
        "\n".join(rows), date.today().isoformat())


# ------------------------------------------------------------------
# Accueil
# ------------------------------------------------------------------

def build_index(n_t2, n_sejour, d_t2, d_sejour):
    return f"""<!DOCTYPE html>
<html lang="fr">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<meta name="robots" content="noindex">
<title>Logement Coimbra - les deux recherches</title>
<style>{STYLE}</style>
</head>
<body>
<header>
<h1>Logement &agrave; Coimbra</h1>
<p>Les deux recherches en cours, mises &agrave; jour automatiquement.</p>
</header>
<main>
<div class="cards">
<a class="card" href="courte-duree.html">
<h2>1. S&eacute;jour temporaire (septembre 2026)</h2>
<p>Logement meubl&eacute; ENTIER pour 1 mois, r&eacute;servable en ligne avant d'arriver.
Le temps de visiter sur place et de signer le vrai bail.</p>
<p><b>{n_sejour} annonces</b> &middot; dernier relev&eacute; : {d_sejour}</p>
</a>
<a class="card" href="longue-duree.html">
<h2>2. Bail longue dur&eacute;e (T2, visa D7)</h2>
<p>T2 en location classique 12 mois, quartiers Solum / Santo Ant&oacute;nio dos Olivais,
proche de l'&eacute;cole. &Agrave; signer en personne sur place.</p>
<p><b>{n_t2} annonces</b> &middot; dernier relev&eacute; : {d_t2}</p>
</a>
</div>
<div class="note">Chaque page est un tableau : <b>cliquer un en-t&ecirc;te de colonne pour trier</b>,
taper dans le champ pour filtrer. "D&eacute;tect&eacute;e le" = date &agrave; laquelle la veille a vu
l'annonce pour la premi&egrave;re fois.</div>
</main>
<footer>G&eacute;n&eacute;r&eacute; le {date.today().isoformat()}</footer>
</body>
</html>"""


def main():
    t2 = load_t2()
    sejour = load_sejour()
    (HERE / "longue-duree.html").write_text(build_t2(t2), encoding="utf-8")
    (HERE / "courte-duree.html").write_text(build_sejour(sejour), encoding="utf-8")
    d_t2 = (t2.get("scraped_at") or "")[:10]
    d_sejour = (sejour.get("scraped_at") or "")[:10]
    (HERE / "index.html").write_text(
        build_index(len(t2["listings"]), len(sejour["listings"]), d_t2, d_sejour),
        encoding="utf-8")
    print(f"Site genere : {len(t2['listings'])} annonces longue duree ({d_t2}), "
          f"{len(sejour['listings'])} courte duree ({d_sejour}).")
    print(f"Fichiers dans {HERE}")


if __name__ == "__main__":
    main()
