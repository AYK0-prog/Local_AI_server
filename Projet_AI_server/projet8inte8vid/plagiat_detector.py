#!/home/enzo/Documents/plagiat_venv/bin/python3
"""
Détecteur de plagiat entre fichiers PDF via Ollama (conversion en Markdown).

Usage :
  python plagiat_detector.py eleve1.pdf eleve2.pdf
  python plagiat_detector.py eleve*.pdf --sujet sujet.pdf
  python plagiat_detector.py eleve*.pdf --sujet sujet.pdf --correction correction.pdf
  python plagiat_detector.py                              # scanne ~/Documents
  python plagiat_detector.py --rep /chemin/vers/dossier    # scanne un dossier
"""

import sys
import os
import re
import json
import argparse
import itertools
from pathlib import Path

try:
    import pdfplumber
except ImportError:
    sys.exit("Installez pdfplumber :  pip install pdfplumber")

try:
    import requests
except ImportError:
    sys.exit("Installez requests :  pip install requests")

OLLAMA_URL   = "http://localhost:11434/api/generate"
OLLAMA_MODEL = "llama3"
SEUIL_ALERTE = 40
REP_DEFAUT   = str(Path.home() / "Documents")


def pdf_vers_markdown(chemin_pdf: str) -> str:
    markdown = []
    with pdfplumber.open(chemin_pdf) as pdf:
        for i, page in enumerate(pdf.pages, start=1):
            texte = page.extract_text()
            if texte:
                markdown.append(f"## Page {i}\n\n{texte.strip()}")
            for table in page.extract_tables():
                if not table:
                    continue
                lignes_md = []
                for j, ligne in enumerate(table):
                    cellules = [str(c or "").replace("\n", " ") for c in ligne]
                    lignes_md.append("| " + " | ".join(cellules) + " |")
                    if j == 0:
                        lignes_md.append("|" + "|".join(["---"] * len(ligne)) + "|")
                markdown.append("\n".join(lignes_md))
    return "\n\n".join(markdown)


def tokeniser(texte: str) -> list:
    return re.findall(r"\b\w+\b", texte.lower())

def ngrammes(tokens: list, n: int = 3) -> set:
    return set(zip(*[tokens[i:] for i in range(n)]))

def construire_ngrammes_reference(texte_sujet, texte_correction, n: int = 3) -> set:
    reference = ""
    if texte_sujet:
        reference += " " + texte_sujet
    if texte_correction:
        reference += " " + texte_correction
    return ngrammes(tokeniser(reference), n) if reference.strip() else set()

def filtrer_ngrammes(ng: set, ng_reference: set) -> set:
    return ng - ng_reference


def similarite_jaccard_filtree(texte_a, texte_b, ng_reference, n=3):
    ng_a_brut = ngrammes(tokeniser(texte_a), n)
    ng_b_brut = ngrammes(tokeniser(texte_b), n)
    if ng_a_brut and ng_b_brut:
        inter_brut = len(ng_a_brut & ng_b_brut)
        union_brut = len(ng_a_brut | ng_b_brut)
        score_brut = round(inter_brut / union_brut * 100, 2)
    else:
        score_brut = 0.0
    ng_a = filtrer_ngrammes(ng_a_brut, ng_reference)
    ng_b = filtrer_ngrammes(ng_b_brut, ng_reference)
    if ng_a and ng_b:
        inter = len(ng_a & ng_b)
        union = len(ng_a | ng_b)
        score_filtre = round(inter / union * 100, 2)
    else:
        score_filtre = 0.0
    return score_brut, score_filtre


def barre_pourcentage(score: float, largeur: int = 20) -> str:
    rempli = round(score / 100 * largeur)
    vide = largeur - rempli
    if score >= SEUIL_ALERTE:
        couleur = "31"  # rouge
    elif score >= 20:
        couleur = "33"  # jaune
    else:
        couleur = "32"  # vert
    return f"\033[{couleur}m{'█' * rempli}{'░' * vide}\033[0m {score:.1f}%"


def analyser_avec_ollama(md_a, md_b, nom_a, nom_b, score_brut, score_filtre, md_sujet, md_correction, modele="llama3"):
    extrait_a = md_a[:3000]
    extrait_b = md_b[:3000]
    extrait_sujet = md_sujet[:1500] if md_sujet else None
    extrait_corr = md_correction[:1500] if md_correction else None

    contexte_ref = ""
    if extrait_sujet:
        contexte_ref += f"""
--- SUJET (à NE PAS considérer comme du plagiat) ---
{extrait_sujet}
"""
    if extrait_corr:
        contexte_ref += f"""
--- CORRECTION DE RÉFÉRENCE (à NE PAS considérer comme du plagiat) ---
{extrait_corr}
"""

    if md_sujet or md_correction:
        detail_scores = (
            f"Score Jaccard brut (avec sujet/correction) : {score_brut}%\n"
            f"Score Jaccard filtré (hors sujet/correction) : {score_filtre}%  score pertinent"
        )
        consigne_filtre = (
            "IMPORTANT : le sujet et/ou la correction ont été fournis. "
            "Les similitudes provenant directement de ces documents ne doivent PAS être signalées comme du plagiat. "
            "Concentre-toi uniquement sur les ressemblances entre les réponses personnelles des deux copies."
        )
    else:
        detail_scores = f"Score de similarité lexicale (Jaccard 3-grammes) : {score_brut}%"
        consigne_filtre = ""

    prompt = f"""Tu es un expert en détection de plagiat académique.
{consigne_filtre}

Voici deux copies d'élèves (extraits) converties en Markdown.
{contexte_ref}
--- COPIE A : {nom_a} ---
{extrait_a}

--- COPIE B : {nom_b} ---
{extrait_b}

{detail_scores}

Analyse en profondeur et réponds en respectant EXACTEMENT cette structure :

## Niveau de plagiat
[faible / modéré / élevé / très élevé]

## Passages communs (copiés ou fortement similaires)
Liste les passages textuels identiques ou quasi-identiques entre les deux copies, hors sujet/correction.

## Passages différents (originaux dans chaque copie)
Liste ce qui est propre à chaque élève et qui n'apparaît pas chez l'autre.

## Explication détaillée
Explique pourquoi tu suspectes (ou non) un plagiat.

## Actions recommandées
Donne exactement 5 recommandations maximum, numérotées de 1 à 5, à l'intention de l'enseignant."""

    payload = {"model": modele, "prompt": prompt, "stream": False}
    try:
        resp = requests.post(OLLAMA_URL, json=payload, timeout=180)
        resp.raise_for_status()
        return resp.json().get("response", "Réponse vide d'Ollama.")
    except requests.exceptions.ConnectionError:
        return (
            "Impossible de joindre Ollama.\n"
            "    Vérifiez qu'il tourne sur http://localhost:11434\n"
            "    et que le modèle est chargé (ollama run llama3)."
        )
    except requests.exceptions.Timeout:
        return "Délai dépassé. Le modèle est peut-être trop lent."
    except Exception as e:
        return f"Erreur inattendue : {e}"


def extraire_analyse_ia_sections(texte_ia: str) -> dict:
    sections = {}
    current = None
    lignes = []
    for ligne in texte_ia.split("\n"):
        m = re.match(r"^##\s+(.+)", ligne)
        if m:
            if current:
                sections[current] = "\n".join(lignes).strip()
            current = m.group(1).strip()
            lignes = []
        else:
            lignes.append(ligne)
    if current:
        sections[current] = "\n".join(lignes).strip()
    return sections


def afficher_banniere(avec_sujet, avec_correction):
    print("\n" + "=" * 65)
    print("   DÉTECTEUR DE PLAGIAT  —  PDF -> Markdown + Ollama IA")
    if avec_sujet:
        print("   Sujet chargé      — ses phrases sont ignorées")
    if avec_correction:
        print("   Correction chargée — ses éléments sont ignorés")
    print("=" * 65 + "\n")

def extraire_recommandations(texte_ia: str) -> list:
    sections = extraire_analyse_ia_sections(texte_ia)
    raw = sections.get("Actions recommandées", "")
    phrases = re.findall(r"(?:^|\n)\s*(?:\d+[.)]\s*|[-*]\s*)(.+?)(?=\s*(?:\n\s*(?:\d+[.)]\s*|[-*]\s*)|\Z))", raw, re.DOTALL)
    if not phrases:
        phrases = [l.strip() for l in raw.split("\n") if l.strip()]
    return [p.strip() for p in phrases if p.strip()][:5]


def afficher_resultat(nom_a, nom_b, score_brut, score_filtre, avec_reference, analyse_ia, seuil_alerte=40):
    print(f"\n{'─'*65}")
    print(f"  📄  {nom_a}  <->  {nom_b}")
    print(f"{'─'*65}")
    score_retenu = score_filtre if avec_reference else score_brut
    if avec_reference:
        print(f"  Similarité brute   (avec sujet/correction)  : {score_brut}%")
        print(f"  Similarité filtrée (hors sujet/correction)  : {barre_pourcentage(score_filtre)}")
    else:
        print(f"  Similarité lexicale (Jaccard)               : {barre_pourcentage(score_brut)}")
    if score_retenu >= seuil_alerte:
        print(f"  ⚠️  ALERTE : seuil de {seuil_alerte}% depasse !")
    print()
    recommandations = extraire_recommandations(analyse_ia)
    if recommandations:
        print("  Recommandations :")
        for i, r in enumerate(recommandations, 1):
            print(f"    {i}. {r}")
    print()

def sauvegarder_rapport(resultats, dossier_sortie="."):
    chemin = Path(dossier_sortie) / "rapport_plagiat.json"
    with open(chemin, "w", encoding="utf-8") as f:
        json.dump(resultats, f, ensure_ascii=False, indent=2)
    print(f"\nRapport JSON sauvegardé : {chemin}")

    chemin_html = Path(dossier_sortie) / "rapport_plagiat.html"
    html = generer_html(resultats)
    with open(chemin_html, "w", encoding="utf-8") as f:
        f.write(html)
    print(f"Rapport HTML généré      : {chemin_html}")


def generer_html(resultats: list) -> str:
    noms = set()
    toto = {"score": {}, "detail": {}}
    for r in resultats:
        a, b = r["document_a"], r["document_b"]
        noms.add(a)
        noms.add(b)
        score = r["score_retenu"]
        toto["score"][(a, b)] = score
        toto["score"][(b, a)] = score
        toto["detail"][(a, b)] = r
        toto["detail"][(b, a)] = r

    noms = sorted(noms)
    couleur_score = lambda s: f"hsl({max(0, 120 - s * 1.2)}, 70%, {(100 - s*0.35) if s < 90 else 30}%)"

    rows_tableau_croise = ""
    for nom in noms:
        cells = f'<td class="nom-eleve">{nom}</td>'
        for autre in noms:
            if nom == autre:
                cells += '<td class="diag"></td>'
            else:
                s = toto["score"].get((nom, autre), 0)
                coul = couleur_score(s)
                alerte = " alerte" if s >= SEUIL_ALERTE else ""
                cells += f'<td class="score{alerte}" style="background:{coul}">{s:.1f}%</td>'
        rows_tableau_croise += f"<tr>{cells}</tr>\n"

    headers_croise = '<th></th>' + ''.join(f'<th>{n}</th>' for n in noms)

    details_paires = ""
    for a, b in sorted(toto["detail"].keys()):
        if a >= b:
            continue
        r = toto["detail"][(a, b)]
        score = r["score_retenu"]
        alerte = score >= SEUIL_ALERTE
        ia = r.get("analyse_ia", "")
        sections = extraire_analyse_ia_sections(ia)

        communs = sections.get("Passages communs (copiés ou fortement similaires)", "")
        differents_a = ""
        differents_b = ""
        for cle, val in sections.items():
            if "différent" in cle.lower() or "original" in cle.lower():
                differents_a += val

        recommandations = extraire_recommandations(ia)
        rows_reco = "".join(
            f"<tr><td>{i}</td><td>{r}</td></tr>"
            for i, r in enumerate(recommandations, 1)
        ) or "<tr><td colspan='2'>Aucune recommandation.</td></tr>"

        alerte_badge = '<span class="badge-ok">✓</span>'
        if alerte:
            alerte_badge = '<span class="badge-alerte">⚠️ ALERTE</span>'

        s_brut = r["score_jaccard_brut"]
        s_filtre = r["score_jaccard_filtre"]
        coul = couleur_score(score)

        details_paires += f"""
<div class="paire">
  <div class="paire-header" style="border-left: 6px solid {coul};">
    <h3>{a} ↔ {b} {alerte_badge}</h3>
    <div class="bar-container">
      <div class="bar" style="width:{score}%;background:{coul};"></div>
      <span class="bar-label">{score:.1f}%</span>
    </div>
    <div class="scores-aux">
      Jaccard brut: {s_brut:.1f}% &nbsp;|&nbsp; Filtré: {s_filtre:.1f}%
    </div>
  </div>
  <div class="paire-content">
    <div class="col-sim">
      <h4>🔴 Passages communs</h4>
      <pre>{communs[:2000] or "Aucun passage commun détecté."}</pre>
    </div>
    <div class="col-diff">
      <h4>🟢 Passages différents</h4>
      <pre>{differents_a[:2000] or "Analyse non disponible."}</pre>
    </div>
    <div class="col-reco">
      <h4>📋 Recommandations</h4>
      <table class="reco-table">
        <thead><tr><th>#</th><th>Recommandation</th></tr></thead>
        <tbody>{rows_reco}</tbody>
      </table>
    </div>
  </div>
</div>"""

    return f"""<!DOCTYPE html>
<html lang="fr">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Rapport de Détection de Plagiat</title>
<style>
  *, *::before, *::after {{ box-sizing: border-box; margin: 0; padding: 0; }}
  body {{ font-family: 'Segoe UI', system-ui, -apple-system, sans-serif; background: #f0f2f5; color: #1a1a2e; padding: 30px; }}
  h1 {{ text-align: center; margin-bottom: 10px; font-size: 1.8rem; }}
  .subtitle {{ text-align: center; color: #666; margin-bottom: 30px; }}
  h2 {{ margin: 30px 0 15px; font-size: 1.4rem; border-bottom: 2px solid #ddd; padding-bottom: 6px; }}
  table {{ border-collapse: collapse; width: 100%; margin-bottom: 30px; background: #fff; border-radius: 12px; overflow: hidden; box-shadow: 0 2px 12px rgba(0,0,0,0.06); }}
  th, td {{ padding: 8px 12px; text-align: center; font-size: 0.85rem; border-bottom: 1px solid #eee; }}
  th {{ background: #1a1a2e; color: #fff; font-weight: 600; white-space: nowrap; }}
  th:first-child {{ text-align: left; }}
  .nom-eleve {{ font-weight: 600; text-align: left; white-space: nowrap; background: #f8f9fa; }}
  .diag {{ background: #e9ecef; }}
  .score {{ font-weight: 700; color: #fff; text-shadow: 0 1px 2px rgba(0,0,0,0.3); transition: transform 0.1s; cursor: default; }}
  .score.alerte {{ outline: 3px solid #e74c3c; outline-offset: -1px; }}
  .paire {{ background: #fff; border-radius: 12px; margin-bottom: 20px; box-shadow: 0 2px 12px rgba(0,0,0,0.06); overflow: hidden; }}
  .paire-header {{ padding: 16px 20px; }}
  .paire-header h3 {{ font-size: 1.1rem; margin-bottom: 8px; display: flex; align-items: center; gap: 10px; }}
  .bar-container {{ height: 24px; background: #e9ecef; border-radius: 12px; overflow: hidden; position: relative; margin-bottom: 6px; }}
  .bar {{ height: 100%; border-radius: 12px; transition: width 0.6s ease; }}
  .bar-label {{ position: absolute; right: 10px; top: 50%; transform: translateY(-50%); font-weight: 700; font-size: 0.85rem; color: #1a1a2e; }}
  .scores-aux {{ font-size: 0.8rem; color: #888; }}
  .badge-alerte {{ display: inline-block; background: #e74c3c; color: #fff; padding: 2px 10px; border-radius: 20px; font-size: 0.7rem; font-weight: 700; }}
  .badge-ok {{ display: inline-block; background: #2ecc71; color: #fff; padding: 2px 10px; border-radius: 20px; font-size: 0.7rem; font-weight: 700; }}
  .paire-content {{ display: grid; grid-template-columns: 1fr 1fr; gap: 0; }}
  .paire-content > div {{ padding: 16px 20px; border-top: 1px solid #eee; }}
  .paire-content > div:first-child {{ border-right: 1px solid #eee; }}
  .col-reco {{ grid-column: 1 / -1; }}
  .reco-table {{ width: 100%; border-collapse: collapse; font-size: 0.85rem; }}
  .reco-table th {{ background: #2c3e50; padding: 6px 10px; text-align: left; width: 40px; }}
  .reco-table th:first-child {{ width: 40px; text-align: center; }}
  .reco-table td {{ padding: 8px 10px; border-bottom: 1px solid #eee; vertical-align: top; }}
  .reco-table td:first-child {{ text-align: center; font-weight: 700; color: #7f8c8d; }}
  .reco-table tr:last-child td {{ border-bottom: none; }}
  h4 {{ font-size: 0.9rem; margin-bottom: 8px; color: #444; }}
  pre {{ white-space: pre-wrap; font-family: 'Consolas', 'Monaco', monospace; font-size: 0.8rem; background: #f8f9fa; padding: 12px; border-radius: 8px; max-height: 300px; overflow-y: auto; line-height: 1.5; }}
  @media (max-width: 800px) {{
    .paire-content {{ grid-template-columns: 1fr; }}
    .paire-content > div:first-child {{ border-right: none; }}
  }}
</style>
</head>
<body>
<h1>🔍 Rapport de Détection de Plagiat</h1>
<p class="subtitle">Analyse basée sur la similarité lexicale (Jaccard 3-grammes) et l'intelligence artificielle (Ollama)</p>

<h2>📊 Tableau croisé des similarités</h2>
<div style="overflow-x: auto;">
<table>
<thead><tr>{headers_croise}</tr></thead>
<tbody>{rows_tableau_croise}</tbody>
</table>
</div>

<h2>📝 Détail par paire d'élèves</h2>
{details_paires}

<p style="text-align:center;color:#999;margin-top:40px;font-size:0.8rem;">
  Généré automatiquement par le Détecteur de Plagiat &mdash; {Path(__file__).name}
</p>
</body>
</html>"""


def scanner_repertoire(chemin: str) -> list:
    p = Path(chemin)
    if not p.is_dir():
        print(f"Attention : {chemin} n'est pas un dossier valide. Utilisation du dossier par défaut.")
        p = Path(REP_DEFAUT)
    pdfs = sorted(p.glob("*.pdf"))
    if not pdfs:
        sys.exit(f"Aucun fichier PDF trouvé dans {p}")
    print(f"{len(pdfs)} fichier(s) PDF trouvé(s) dans {p}")
    return [str(f) for f in pdfs]


def main():
    parser = argparse.ArgumentParser(
        description="Detection de plagiat entre fichiers PDF via Ollama.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""Exemples :
  python plagiat_detector.py copie1.pdf copie2.pdf copie3.pdf
  python plagiat_detector.py copie*.pdf --sujet sujet.pdf
  python plagiat_detector.py copie*.pdf --sujet sujet.pdf --correction correction.pdf
  python plagiat_detector.py copie*.pdf --sujet sujet.pdf --sans-ia --seuil 30
  python plagiat_detector.py                           # scanne ~/Documents
  python plagiat_detector.py --rep /chemin/dossier      # scanne un dossier
""",
    )
    parser.add_argument("pdfs", nargs="*", metavar="COPIE.pdf", help="Copies des eleves a analyser (2 minimum).")
    parser.add_argument("--rep", metavar="DOSSIER", default=None, help=f"Scanner un dossier de PDFs (defaut : {REP_DEFAUT}).")
    parser.add_argument("--sujet", metavar="SUJET.pdf", default=None, help="PDF du sujet.")
    parser.add_argument("--correction", metavar="CORRECTION.pdf", default=None, help="PDF de la correction.")
    parser.add_argument("--modele", default=OLLAMA_MODEL, help=f"Modele Ollama (defaut : {OLLAMA_MODEL}).")
    parser.add_argument("--seuil", type=int, default=SEUIL_ALERTE, help=f"Seuil d'alerte en %% (defaut : {SEUIL_ALERTE}).")
    parser.add_argument("--sans-ia", action="store_true", help="Desactive l'analyse Ollama.")
    parser.add_argument("--sortie", default=".", help="Dossier de sortie pour le rapport JSON/HTML.")
    args = parser.parse_args()

    if args.pdfs:
        fichiers = args.pdfs
    else:
        repertoire = args.rep or REP_DEFAUT
        fichiers = scanner_repertoire(repertoire)

    if len(fichiers) < 2:
        parser.error("Fournissez au moins 2 fichiers PDF de copies.")

    avec_sujet = args.sujet is not None
    avec_correction = args.correction is not None
    avec_reference = avec_sujet or avec_correction

    afficher_banniere(avec_sujet, avec_correction)

    md_sujet = None
    md_correction = None

    if avec_sujet:
        if not os.path.isfile(args.sujet):
            sys.exit(f"Sujet introuvable : {args.sujet}")
        print(f"Chargement du sujet         : {Path(args.sujet).name} ...")
        md_sujet = pdf_vers_markdown(args.sujet)

    if avec_correction:
        if not os.path.isfile(args.correction):
            sys.exit(f"Correction introuvable : {args.correction}")
        print(f"Chargement de la correction : {Path(args.correction).name} ...")
        md_correction = pdf_vers_markdown(args.correction)

    ng_reference = construire_ngrammes_reference(md_sujet, md_correction)
    if avec_reference:
        print(f"{len(ng_reference)} n-grammes du sujet/correction seront ignorés.\n")

    docs = {}
    for chemin in fichiers:
        if not os.path.isfile(chemin):
            print(f"Fichier introuvable : {chemin} — ignoré.")
            continue
        nom = Path(chemin).name
        print(f"Extraction de {nom} ...")
        docs[nom] = pdf_vers_markdown(chemin)

    if len(docs) < 2:
        sys.exit("Il faut au moins 2 copies PDF valides.")

    nb_paires = len(docs) * (len(docs) - 1) // 2
    print(f"\n{len(docs)} copies chargées — {nb_paires} paire(s) à comparer.\n")

    noms = list(docs.keys())
    resultats = []

    for nom_a, nom_b in itertools.combinations(noms, 2):
        score_brut, score_filtre = similarite_jaccard_filtree(docs[nom_a], docs[nom_b], ng_reference)

        if args.sans_ia:
            analyse = "(analyse IA désactivée)"
        else:
            print(f"Analyse Ollama : {nom_a} <-> {nom_b} ...")
            analyse = analyser_avec_ollama(docs[nom_a], docs[nom_b], nom_a, nom_b, score_brut, score_filtre, md_sujet, md_correction, args.modele)

        afficher_resultat(nom_a, nom_b, score_brut, score_filtre, avec_reference, analyse, args.seuil)

        score_retenu = score_filtre if avec_reference else score_brut
        resultats.append({
            "document_a": nom_a,
            "document_b": nom_b,
            "score_jaccard_brut": score_brut,
            "score_jaccard_filtre": score_filtre,
            "score_retenu": score_retenu,
            "alerte": score_retenu >= args.seuil,
            "analyse_ia": analyse,
        })

    sauvegarder_rapport(resultats, args.sortie)
    print("\nAnalyse terminée.\n")


if __name__ == "__main__":
    main()
