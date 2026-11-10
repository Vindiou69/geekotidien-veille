"""Collecte des flux RSS Geekotidien et écrit veille.csv (48 dernières heures).

Modèle à compléter : les adresses RSS des sites ne sont pas encore renseignées.
Remplace chaque ligne « A_REMPLIR » par le vrai flux de chaque site.
"""
import csv
import html
import re
from datetime import datetime, timedelta, timezone
from zoneinfo import ZoneInfo

import feedparser

# Thème, nom du site, adresse du flux RSS. Les flux GamesRadar et Notebookcheck sont en anglais.
FLUX = [
    ("Smartphones et mobile", "Phonandroid", "http://www.phonandroid.com/feed"),
    ("Smartphones et mobile", "Numerama", "http://www.numerama.com/rss/news.rss"),
    ("Smartphones et mobile", "Frandroid", "https://www.frandroid.com/feed"),
    ("Smartphones et mobile", "Journal du Geek", "http://feeds2.feedburner.com/LeJournalduGeek"),
    ("Smartphones et mobile", "Notebookcheck", "http://www.notebookcheck.net/News.152.100.html"),
    ("Hardware et PC", "Tom's Hardware", "https://www.tomshardware.fr/feed/"),
    ("Hardware et PC", "Génération NT", "http://www.generation-nt.com/export/rss.xml"),
    ("Intelligence artificielle", "Siècle Digital", "https://siecledigital.fr/feed/"),
    ("Jeux vidéo", "Jeuxvideo.com", "https://www.jeuxvideo.com/rss/rss.xml"),
    ("Jeux vidéo", "Gamekult", "https://www.gamekult.com/feed.xml"),
    ("Jeux vidéo", "GamesRadar", "https://www.gamesradar.com/feeds.xml"),
    ("BD, comics et manga", "ActuBD", "https://www.actuabd.com/spip.php?page=backend"),
    ("Science et espace", "Futura Sciences", "https://www.futura-sciences.com/rss/actualites.xml"),
    ("Science et espace", "NASA", "https://www.nasa.gov/news-release/feed/"),
    ("Actualité générale et vérification", "Libération", "http://rss.liberation.fr/rss/latest/"),
    ("Actualité générale et vérification", "Franceinfo", "https://www.franceinfo.fr/titres.rss"),
]

PARIS = ZoneInfo("Europe/Paris")
FENETRE = timedelta(hours=48)
SPONSO = re.compile(r"#sponso|article en partenariat|sponsoris|\bsponso\b", re.IGNORECASE)
# Articles de bons plans et promotions (titre)
PROMO = re.compile(
    r"black friday|réduction|remise|discount|price drop|drops below|lowest price|soldes|\bdeal\b|\bcodes?\b"
    r"|\$?\d+\s?(%|percent)\s?off|\$\d+\s+off|-\s?\d+\s?%",
    re.IGNORECASE,
)
# Chemins d'adresse typiques des bons plans (lien)
PROMO_LIEN = re.compile(r"/bons-plans/|promo|pas-cher|black-friday", re.IGNORECASE)


def est_sponsorise(titre):
    return bool(SPONSO.search(titre))


def est_promo(titre, lien):
    return bool(PROMO.search(titre) or PROMO_LIEN.search(lien))


def collecter():
    limite = datetime.now(timezone.utc) - FENETRE
    lignes = []
    for theme, site, url in FLUX:
        if url == "A_REMPLIR":
            print(f"[ignoré] {site} : adresse RSS pas encore renseignée")
            continue
        flux = feedparser.parse(url)
        if not flux.entries:
            print(f"[vide] {site} : aucun article lu")
            continue
        for entree in flux.entries:
            date_struct = entree.get("published_parsed") or entree.get("updated_parsed")
            if not date_struct:
                continue
            quand = datetime(*date_struct[:6], tzinfo=timezone.utc)
            if quand < limite:
                continue
            titre = html.unescape(entree.get("title", "").strip())
            lien = entree.get("link", "").strip()
            if not titre or est_sponsorise(titre) or est_promo(titre, lien):
                continue
            lignes.append({
                "Date": quand.astimezone(PARIS).strftime("%d/%m/%Y %H:%M"),
                "Thème": theme,
                "Site": site,
                "Titre": titre,
                "Lien": lien,
                "_tri": quand,
            })
    lignes.sort(key=lambda l: l["_tri"], reverse=True)
    return lignes


def ecrire(lignes, fichier="veille.csv"):
    with open(fichier, "w", newline="", encoding="utf-8-sig") as f:
        writer = csv.writer(f, delimiter=";")
        writer.writerow(["Date", "Thème", "Site", "Titre", "Lien"])
        for l in lignes:
            writer.writerow([l["Date"], l["Thème"], l["Site"], l["Titre"], l["Lien"]])
    print(f"{len(lignes)} articles écrits dans {fichier}")


if __name__ == "__main__":
    ecrire(collecter())
