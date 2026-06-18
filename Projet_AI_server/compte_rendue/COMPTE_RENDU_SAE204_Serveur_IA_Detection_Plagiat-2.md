# Compte-Rendu de Projet — Serveur IA Local & Détection de Plagiat

> **Projet** : SAE204 — Soutenance Cybersécurité
> **Formation** : BUT Réseaux & Télécommunications — Site d'Auxerre
> **Auteur** : Enzo Maresia
> **Dépôt GitHub** : [AYK0-prog/Local_AI_server](https://github.com/AYK0-prog/Local_AI_server)
> **Date** : Juin 2026
> **Statut** : Phases 0, 1 et 2 terminées ✅ — Phase 3 (soutenance) en cours 🔲

---

## Sommaire

1. [Présentation du projet](#1-présentation-du-projet)
2. [Architecture réseau et matérielle](#2-architecture-réseau-et-matérielle)
3. [Identifiants et contrôle d'accès](#3-identifiants-et-contrôle-daccès)
4. [Phase 0 — Environnement logiciel et déploiement](#4-phase-0--environnement-logiciel-et-déploiement)
5. [Phase 1 — Pipeline de détection de plagiat (CLI)](#5-phase-1--pipeline-de-détection-de-plagiat-cli)
6. [Phase 2 — Application web Flask](#6-phase-2--application-web-flask)
7. [Vérification externe — État actuel](#7-vérification-externe--état-actuel)
8. [Sécurité et conformité](#8-sécurité-et-conformité)
9. [Déroulement du projet — Séances de travail](#9-déroulement-du-projet--séances-de-travail)
10. [Inventaire des fichiers de projet](#10-inventaire-des-fichiers-de-projet)
11. [Feuille de route — Phase 3](#11-feuille-de-route--phase-3)
12. [Glossaire](#12-glossaire)
13. [Récapitulatif des ports et chemins](#13-récapitulatif-des-ports-et-chemins)

---

## 1. Présentation du projet

### 1.1 Contexte

Ce projet répond à une demande concrète du département R&T d'Auxerre : disposer d'un
**serveur d'Intelligence Artificielle 100 % local**, indépendant des services cloud
commerciaux (ChatGPT, Gemini, etc.), pour deux usages distincts.

L'angle directeur est la **confidentialité des données** : tous les traitements sont
effectués en local, sans envoi de données sensibles (copies d'élèves, prompts, rapports)
vers des serveurs tiers. Une vérification externe était disponible en option mais a été
remplacée par un second modèle local — le pipeline est désormais **100 % local**.

### 1.2 Objectifs

| # | Objectif | Livrable |
|---|----------|----------|
| A | Héberger une IA locale, légère, rapide et autonome | Serveur Docker + Ollama + OpenWebUI |
| B | Détecter la fraude/plagiat dans les comptes-rendus de TP | Pipeline Python (CLI) + application web Flask |

### 1.3 Cahier des charges (domaine Informatique)

- Serveur capable d'**héberger une intelligence artificielle**
- IA servie par **Ollama** (API REST locale)
- IA **légère, rapide, efficace, autonome** et portant un nom (assistant basé sur **Qwen**)
- Système de **détection de fraude en Python**
- Utilisation **headless via interface web** + interaction vocale
- Compatibilité **Home Assistant** — *réalisée, présentée comme bonus*

### 1.4 Stack technologique retenue

> Après évaluation de LiteLLM, LM Studio et OpenCode, la stack retenue est
> volontairement minimale et entièrement auto-hébergée.
> LM Studio a été rejeté dès la séance 6 : le processeur Xeon E5-2630 v3 ne
> dispose pas du jeu d'instructions **AVX2**, requis par LM Studio pour
> l'inférence CPU. LiteLLM a été installé mais la liaison avec Ollama n'a jamais
> été fonctionnelle ; il a été abandonné au profit d'un accès direct à l'API Ollama.

| Couche | Technologie | Rôle |
|--------|-------------|------|
| Système d'exploitation | **Linux Mint 22.3** | Base headless légère |
| Conteneurisation | **Docker Engine** (CLI, sans Docker Desktop) | Isolation des services IA |
| Serveur de modèles | **Ollama** (API REST `:11434`) | Chargement et inférence des LLM |
| Interface web IA | **OpenWebUI** (1 instance — port 3000) | Front conversationnel multi-comptes |
| Détection de plagiat | **Python 3.12.3** (pipeline) + **Flask** | Analyse + interface web |
| Vérification (option) | **Ollama local → llama3.1:8b** | Second avis IA 100 % local |

### 1.5 État d'avancement

| Phase | Description | Statut |
|-------|-------------|--------|
| **Phase 0** | Environnement (Docker + Ollama + OpenWebUI + réseau) | ✅ Terminée |
| **Phase 1** | Script CLI de détection de plagiat | ✅ Terminée — testée en production |
| **Phase 2** | Application web Flask | ✅ Terminée — fonctionnelle |
| **Phase 3** | Préparation soutenance | 🔲 En cours |

---

## 2. Architecture réseau et matérielle

### 2.1 Topologie actuelle

Le serveur IA est un **PC custom connecté directement en filaire au réseau de l'IUT**.
Il n'existe pas d'infrastructure réseau intermédiaire : les clients (Lenovo, MacBook)
accèdent aux services hébergés sur le serveur via le réseau de la faculté.

```
        Réseau IUT (filaire / Wi-Fi)
                   │
        ┌──────────┴───────────────┐
        │       SERVEUR IA         │
        │       PC Custom          │
        │  2× Xeon E5-2630 v3      │
        │  RTX 3060 Ti — 8 Go VRAM │
        │  32 Go DDR3              │
        │  Linux Mint 22.3         │
        │  IP : DHCP (réseau IUT)  │
        │  Ollama / OpenWebUI      │
        │  + Flask (port 5000)     │
        └──────────┬───────────────┘
                   │
        ┌──────────┴──────────┐
        │                     │
   ┌────┴──────┐       ┌──────┴─────┐
   │  Lenovo   │       │  MacBook   │
   │  Client   │       │  Client    │
   └───────────┘       └────────────┘
```

### 2.2 Fiche technique du serveur

| Composant | Détail |
|-----------|--------|
| **Processeurs** | 2× Intel Xeon E5-2630 v3 (8 cœurs / 16 threads chacun — 32 threads au total) |
| **GPU** | NVIDIA RTX 3060 Ti — 8 Go VRAM |
| **RAM** | 32 Go DDR3 *(suite au retrait de barrettes défectueuses en séance 3)* |
| **Système** | Linux Mint 22.3 — mode headless |
| **Python** | 3.12.3 |
| **Utilisateur projet** | `enzo` |

> **Note sur la RAM** : lors de l'installation de l'OS (séance 3), des barrettes RAM
> défectueuses ont provoqué des instabilités. Elles ont été retirées avant de
> finaliser l'installation. La clé USB bootable a également dû être changée de port
> USB pour être reconnue au démarrage.

### 2.3 Évolution de l'architecture au cours du projet

En début de projet (séances 1 à 5), le réseau reposait sur un sous-réseau isolé
`10.42.0.0/24` créé via un switch physique, avec un Lenovo Ideapad en passerelle
NAT (Wi-Fi IUT → Ethernet switch) et un Raspberry Pi 5 hébergeant Home Assistant OS
à l'IP fixe `10.42.0.100`. Cette infrastructure a été simplifiée : le serveur est
désormais raccordé directement au réseau filaire de l'IUT.

### 2.4 Note sur Home Assistant (bonus)

Un Raspberry Pi 5 a été intégré en cours de projet pour valider la compatibilité
domotique du cahier des charges : intégration Ollama native dans HAOS, pipeline vocal
Assist (STT → agent Ollama → TTS). Cette brique n'est plus dans le setup actuel mais
démontre l'extensibilité de la stack vers des usages domotiques et constitue un
élément bonus de la soutenance.

---

## 3. Identifiants et contrôle d'accès

| Service | Port | Utilisateur | Mot de passe |
|---------|------|-------------|--------------|
| **OpenWebUI** | `:3000` | `ps.enzo.maresia@gmail.com` | `AI_serv` |
| **Flask (Plagiat)** | `:5000` | `admin` | `admin` *(à changer)* |
| **Home Assistant** | `10.42.0.100` | `rt3-raspberry` | `Etudiants89100` |
| **OS serveur** | SSH | `enzo` / `AI_serv` | — |

**Clé API HuggingFace** *(invalide — à révoquer avant soutenance)* :

```
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
```

> Les points de sécurité à corriger sont détaillés en §8.

---

## 4. Phase 0 — Environnement logiciel et déploiement

L'environnement est volontairement **léger et headless** : aucune interface graphique
côté serveur, services IA isolés dans des conteneurs Docker.

### 4.1 Checklist de déploiement

- [x] Retirer les barrettes RAM défectueuses
- [x] Installer **Linux Mint 22.3** (clé USB bootable)
- [x] Activer **SSH** et sécuriser les connexions
- [x] Installer **Docker Engine** (via paquet `.deb`)
- [x] Installer **Ollama** avec support GPU
- [x] Charger les **modèles IA** (voir §4.5)
- [x] Déployer **OpenWebUI** (une instance sur le port 3000)
- [x] Configurer l'environnement **Python 3.12.3** et le `venv`
- [x] Déployer le **pipeline de détection de plagiat**
- [x] Optimiser la **VRAM** (sentence_transformers → CPU, LLaVA désactivé)
- [ ] Réinstaller les **drivers GPU NVIDIA** correctement pour la soutenance

### 4.2 Prérequis système

```bash
sudo apt update
sudo apt install -y \
  tesseract-ocr tesseract-ocr-fra tesseract-ocr-eng \
  libpango-1.0-0 libpangoft2-1.0-0 \
  python3 python3-venv python3-pip git curl
```

### 4.3 Installation de Docker Engine

> L'installation via le dépôt APT standard a rencontré des problèmes sur le serveur.
> La solution retenue (séance 4) a été l'installation via le **paquet `.deb`**
> téléchargé directement depuis [docs.docker.com/engine/install/ubuntu](https://docs.docker.com/engine/install/ubuntu).

Méthode alternative via dépôt (pour référence) :

```bash
sudo apt install -y ca-certificates curl gnupg
sudo install -m 0755 -d /etc/apt/keyrings
curl -fsSL https://download.docker.com/linux/ubuntu/gpg \
  | sudo gpg --dearmor -o /etc/apt/keyrings/docker.gpg

# Linux Mint : utiliser le nom de code Ubuntu de base
echo "deb [arch=$(dpkg --print-architecture) \
  signed-by=/etc/apt/keyrings/docker.gpg] \
  https://download.docker.com/linux/ubuntu \
  $(. /etc/os-release && echo "$UBUNTU_CODENAME") stable" \
  | sudo tee /etc/apt/sources.list.d/docker.list > /dev/null

sudo apt update
sudo apt install -y \
  docker-ce docker-ce-cli containerd.io docker-compose-plugin

# Utiliser Docker sans sudo (reconnexion nécessaire ensuite)
sudo usermod -aG docker $USER
docker run --rm hello-world
```

### 4.4 Installation et configuration d'Ollama

Ollama expose une **API REST locale** sur le port `11434`.
Il a été réinstallé en séance 6 **avec le support GPU** activé.

```bash
curl -fsSL https://ollama.com/install.sh | sh
systemctl status ollama
```

Pour exposer Ollama sur le réseau (accès depuis les postes clients) :

```bash
sudo systemctl edit ollama
# Ajouter dans le bloc [Service] :
# Environment="OLLAMA_HOST=0.0.0.0:11434"

sudo systemctl daemon-reload
sudo systemctl restart ollama
```

### 4.5 Modèles IA installés

```bash
ollama pull gemma3:4b
ollama pull qwen2.5:7b
ollama pull llama3.2:3b
ollama pull llama3.1:8b
ollama pull llava:7b
ollama list
```

| Modèle | Type | Rôle dans le projet | Taille |
|--------|------|---------------------|--------|
| `gemma3:4b` | Texte (LLM) | Verdict IA local — étape 6 du pipeline | ~3 Go |
| `qwen2.5:7b` | Texte (LLM) | Assistant nommé « Qwen » dans OpenWebUI | ~4,7 Go |
| `llama3.2:3b` | Texte (LLM) | Modèle léger pour tests et usage courant | ~2 Go |
| `llama3.1:8b` | Texte (LLM) | Provider local (remplace la vérif. externe) | ~4,7 Go |
| `llava:7b` | Vision (VLM) | Installé — **désactivé** (contrainte VRAM) | ~4,7 Go |
| `multilingual-e5-base` | Embeddings | Similarité sémantique FR/EN — forcé CPU | ~1,1 Go |

### 4.6 Contrainte VRAM et optimisations

La RTX 3060 Ti dispose de **8 Go de VRAM**. Deux problèmes ont été rencontrés
en séance 8 lors de l'exécution simultanée du pipeline :

**Problème 1 — sentence_transformers sur GPU :**
Par défaut, la bibliothèque `sentence_transformers` charge le modèle d'embeddings
(`multilingual-e5-base`) sur le GPU, consommant **~2,3 Go de VRAM**.
Avec Ollama qui charge également son modèle texte, Ollama détectait l'état
`limited-vram` et tentait d'offloader LLaVA sur CPU.

**Problème 2 — LLaVA sur CPU et boucle CLIP :**
Une fois LLaVA offloadé sur CPU, le processus `llama-server` (encodeur CLIP
de LLaVA) se mettait à boucler à **1100 % d'utilisation CPU**, bloquant le
pipeline entier.

**Solutions appliquées :**

```python
# Forcer sentence_transformers sur CPU dans le module d'embeddings
from sentence_transformers import SentenceTransformer
model = SentenceTransformer("intfloat/multilingual-e5-base", device="cpu")

# Désactiver complètement LLaVA dans le pipeline
vision_model = None
```

**Résultat :** VRAM disponible pour Ollama **~7,3 Go / 8 Go**.
L'étape d'analyse d'images repose désormais **uniquement sur le hash perceptuel**
(bibliothèque `imagehash`), sans appel au modèle de vision.

### 4.7 Solutions rejetées

| Solution | Raison du rejet |
|----------|-----------------|
| **LM Studio** | Le Xeon E5-2630 v3 ne supporte pas **AVX2** (jeu d'instructions requis) |
| **LiteLLM** | Installé mais la liaison Ollama ↔ LiteLLM n'a jamais fonctionné |
| **VNC** | Ports SSH/VNC bloqués par le réseau de l'IUT — accès distant non résolu |

### 4.8 Déploiement OpenWebUI — deux instances

```bash
# Instance OpenWebUI — port 3000
docker run -d --name openwebui -p 3000:8080 \
  --add-host=host.docker.internal:host-gateway \
  -e OLLAMA_BASE_URL=http://host.docker.internal:11434 \
  -v openwebui:/app/backend/data \
  --restart unless-stopped \
  ghcr.io/open-webui/open-webui:main
```

Chaque instance dispose de son propre volume Docker → comptes et historiques
cloisonnés. Le premier compte créé sur une instance devient automatiquement
**administrateur**.

### 4.9 Assistant nommé

Dans OpenWebUI, un modèle personnalisé est créé sur la base de `qwen2.5:7b`
avec un *system prompt* dédié. C'est cet assistant qui « porte un nom » au
sens du cahier des charges, conformément à la demande initiale.

---

## 5. Phase 1 — Pipeline de détection de plagiat (CLI)

Cœur du système, **100 % local**. Orchestré par la fonction `analyze()`
dans `main.py`.

- **Emplacement** : `/home/enzo/Téléchargements/SAE204_scripts/`
- **Fichier principal** : `main.py`
- **Modules** : sous-dossier `modules/`
- **Environnement** : `venv` Python 3.12.3 dédié

### 5.1 Les 8 étapes de l'analyse

| # | Étape | Technologie | Poids |
|---|-------|-------------|-------|
| 1 | **Extraction PDF → Markdown** | PyMuPDF + Tesseract OCR (FR + EN) | — |
| 2 | **Exclusion du sujet** | Shingling — filtre les phrases de l'énoncé | — |
| 3 | **Détection lexicale** | Shingling k=5 + `rapidfuzz` | **35 %** |
| 4 | **Détection sémantique** | `multilingual-e5-base` (CPU) + cosinus | **35 %** |
| 5 | **Analyse d'images** | Hash perceptuel (`imagehash`) uniquement | **15 %** |
| 6 | **Verdict IA local** | `gemma3:4b` — JSON structuré via Ollama | **15 %** |
| 7 | **Scoring & niveau de risque** | Agrégation pondérée des 4 signaux | — |
| 8 | **Génération du rapport** | Markdown → HTML → PDF (WeasyPrint) | — |

> **Étape 5 — note importante** : l'analyse vision via `llava:7b` a été
> **désactivée** (contrainte VRAM — voir §4.6). Seul le **hash perceptuel**
> reste actif pour détecter la réutilisation d'images entre deux rapports.
> La distance de hash retenue est ≤ 10.

### 5.2 Paramètres clés

| Signal | Paramètre | Valeur |
|--------|-----------|--------|
| Lexical | Taille des n-grammes (shingling) | k = 5 |
| Sémantique | Seuil de similarité cosinus | ≥ 0,85 |
| Images | Distance de hash perceptuel | ≤ 10 |
| Verdict IA | Modèle | `gemma3:4b` via Ollama |

### 5.3 Grille des niveaux de risque

| Niveau | Score global |
|--------|--------------|
| 🟢 FAIBLE | < 40 % |
| 🟠 MODÉRÉ | 40 % – 69 % |
| 🔴 ÉLEVÉ | ≥ 70 % |

### 5.4 Approche multi-signaux — argument soutenance

Le score global n'est pas un simple ratio de copier-coller. Il combine
**quatre signaux indépendants** pour résister aux tentatives de contournement :

- **Lexical** : détecte le copier-coller direct et les reformulations superficielles.
- **Sémantique** : détecte la **paraphrase** — mots différents, sens identique.
  Signal absent de la plupart des détecteurs textuels classiques.
- **Images** : détecte la réutilisation de schémas et captures d'écran, souvent
  ignorée même par des outils professionnels.
- **Verdict IA** : apporte un jugement contextuel avec justification en langage
  naturel, pondéré par l'indice de confiance retourné par le modèle.

### 5.5 Utilisation en ligne de commande

```bash
cd /home/enzo/Téléchargements/SAE204_scripts
source venv/bin/activate

# Analyse standard (avec exclusion de l'énoncé)
python3 main.py \
  --a rapport_a.pdf \
  --b rapport_b.pdf \
  --sujet sujet.pdf \
  --output resultats/

# Avec second avis via Ollama local (llama3.1:8b)
python3 main.py \
  --a rapport_a.pdf \
  --b rapport_b.pdf \
  --external \
  --provider ollama
```

| Argument | Rôle |
|----------|------|
| `--a` / `--b` | Les deux rapports PDF à comparer |
| `--sujet` | PDF de l'énoncé (ses phrases sont exclues de l'analyse) |
| `--output` | Dossier de sortie pour le rapport généré |
| `--external` | Active le second avis IA |
| `--provider` | `ollama` (local) — HuggingFace désactivé |

---

## 6. Phase 2 — Application web Flask

Interface permettant aux enseignants de **déposer les TPs** et de
**suivre l'analyse en temps réel**, sans ligne de commande.

- **Emplacement** : `/home/enzo/Téléchargements/scripts/`
- **Fichier principal** : `app.py` (~480 lignes)
- **Vues** : `templates/` — 8 fichiers `.html` (moteur Jinja2)
- **Accès** : `http://localhost:5000`

### 6.1 Structure du projet Flask

L'application ne réimplémente pas l'analyse : elle **pilote le pipeline de la
Phase 1** via des **liens symboliques**, garantissant qu'un seul code source
fait foi.

```
scripts/
├── app.py                   # Flask : auth, upload, SSE, SQLite
├── templates/               # 8 vues HTML Jinja2
│   ├── login.html
│   ├── upload.html
│   ├── analyse_status.html  # terminal live (SSE)
│   └── ...
├── modules -> ../SAE204_scripts/modules   # lien symbolique
├── main.py -> ../SAE204_scripts/main.py   # lien symbolique
├── external_verify.py       # module de second avis IA
├── test_kimi_api.py         # test de l'API externe
└── venv/                    # environnement Python 3.12.3
```

### 6.2 Base de données (SQLite)

Fichier : `~/.plagiat_app/plagiat.db`

| Table | Rôle |
|-------|------|
| `users` | Comptes (login, hash SHA-256 du mot de passe, rôle) |
| `token_counters` | Tokens consommés par utilisateur (local / externe) |
| `analyses` | Historique : dates, scores, verdict, chemins des rapports |

### 6.3 Suivi en temps réel — SSE + monkey-patching

La page `analyse_status.html` affiche un **terminal simulé qui défile** en direct.
Fonctionnement :

1. Le pipeline CLI émet ses logs via des `print()`.
2. Flask **intercepte la sortie standard** (*monkey-patching* de `sys.stdout`).
3. Chaque ligne est **poussée au navigateur** via **Server-Sent Events (SSE)**.

Un terminal actif = pipeline opérationnel.
Le message « **Mode Démo** » indique un lien symbolique cassé ou une dépendance manquante.

### 6.4 Mode démo (fallback automatique)

Si les symlinks sont brisés ou si une dépendance est absente, l'application
bascule automatiquement en **Mode Démo** : elle génère des résultats fictifs
pour ne pas bloquer l'interface. Ce mode est utile pour une démonstration de
l'UI sans GPU disponible.

**Réparation des liens symboliques :**

```bash
ln -sfn /home/enzo/Téléchargements/SAE204_scripts/modules \
        /home/enzo/Téléchargements/scripts/modules

ln -sfn /home/enzo/Téléchargements/SAE204_scripts/main.py \
        /home/enzo/Téléchargements/scripts/main.py
```

### 6.5 Parcours utilisateur

1. **Login** sur `http://localhost:5000` (admin / admin).
2. **Upload** de 2 fichiers PDF (+ sujet optionnel).
3. **Suivi en temps réel** : terminal live avec les logs du pipeline.
4. **Rapport** consultable dans l'interface, exportable en PDF (WeasyPrint).
5. **Historique** : toutes les analyses sont enregistrées en base SQLite.

### 6.6 Démarrage de l'application

```bash
cd /home/enzo/Téléchargements/scripts
source venv/bin/activate

# Libère le port 5000 si un ancien processus est en cours
pkill -f "python app.py" 2>/dev/null

python app.py
```

> **Important** : toujours activer le `venv` avant de lancer `python app.py`.
> Sans le `venv`, les imports échouent et l'application passe en mode démo.

---

## 7. Vérification externe — État actuel

### 7.1 Situation

La vérification externe via **HuggingFace / Kimi K2.6** a été abandonnée
en séance 8 : la clé API est devenue **invalide (erreur 401)**. Plutôt que de
la renouveler, la décision a été prise de remplacer cet appel distant par un
**second modèle local** (`llama3.1:8b` via Ollama).

Le pipeline est désormais **100 % local**, sans aucune dépendance réseau externe.
C'est un renforcement de l'approche « confidentialité d'abord » du projet.

### 7.2 Paramètres API HuggingFace (référence)

Ces paramètres sont conservés dans la documentation au cas où la vérification
externe serait réactivée.

| Paramètre | Valeur |
|-----------|--------|
| Endpoint | `https://router.huggingface.co/novita/v3/openai/chat/completions` |
| Modèle | `moonshotai/Kimi-K2.6:fastest` |
| Clé | `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` *(invalide — 401)* |
| Format | JSON — API OpenAI-compatible |

### 7.3 Fallback local — llama3.1:8b

Le module `external_verify.py` a été mis à jour pour supporter un provider
`ollama`. Lorsque ce provider est actif, les scores et les paires de phrases
suspectes sont soumis à `llama3.1:8b` en local, qui retourne un verdict structuré.

| Champ retourné | Signification |
|----------------|---------------|
| `verdict_final` | Verdict consolidé par le second modèle |
| `accord_avec_local` | Confirmation du verdict de `gemma3:4b` |
| `confiance` | Indice de confiance du second avis |
| `justification` | Explication en langage naturel |

**Test du module :**

```bash
python3 test_kimi_api.py           # test réseau + clé + appel
python3 test_kimi_api.py --full    # + test de external_verify()
```

### 7.4 Arbitrage local vs externe

| Critère | Local (Ollama) | Externe (Kimi K2.6) |
|---------|----------------|---------------------|
| Confidentialité | ✅ Aucune donnée ne sort | ⚠️ Extraits envoyés à un tiers |
| Conformité RGPD | ✅ Traitement local | ⚠️ À vérifier selon fournisseur |
| Puissance du modèle | Limité par la VRAM | Modèle massif, meilleur raisonnement |
| Disponibilité | Sans Internet | Requiert connexion + quota actif |
| Coût | Gratuit | Crédits HuggingFace |

---

## 8. Sécurité et conformité

### 8.1 Approche « local d'abord »

- Prompts, copies d'élèves et rapports **ne quittent jamais le serveur**.
- Le second avis IA est désormais fourni par `llama3.1:8b` en local.
- La vérification externe reste disponible dans le code mais est **désactivée**
  dans l'application Flask.

### 8.2 Points à corriger avant soutenance

| Priorité | Problème | Remédiation |
|----------|----------|-------------|
| 🔴 Critique | Clé HF codée en dur dans `test_kimi_api.py` et `app.py` | Déplacer dans `.env`, **révoquer** la clé actuelle |
| 🔴 Critique | Compte Flask `admin/admin` par défaut | Changer via script SQLite (§8.3) |
| 🟠 Modéré | Même mot de passe `AI_serv` sur OpenWebUI Admin et User | Différencier par service |
| 🟠 Modéré | Serveur Werkzeug en frontal (développement) | Passer sur **gunicorn** pour la soutenance |

### 8.3 Changer le mot de passe admin Flask

```bash
python3 -c "
import sqlite3, hashlib
db = sqlite3.connect('/home/enzo/.plagiat_app/plagiat.db')
pw = hashlib.sha256(b'NouveauMotDePasse').hexdigest()
db.execute(
    'UPDATE users SET password=? WHERE username=?',
    (pw, 'admin')
)
db.commit()
print('Mot de passe mis a jour')
"
```

### 8.4 Commandes de diagnostic

```bash
# Vérifier les liens symboliques (si cassés → mode démo)
ls -l /home/enzo/Téléchargements/scripts/modules
ls -l /home/enzo/Téléchargements/scripts/main.py

# Vérifier les modèles Ollama présents
ollama list

# Tester les imports Python depuis le venv
cd /home/enzo/Téléchargements/scripts
source venv/bin/activate
python -c "import flask; from main import analyze; print('Imports OK')"

# Vérifier la VRAM disponible
nvidia-smi
```

### 8.5 Problèmes fréquents et solutions

| Symptôme | Cause probable | Solution |
|----------|----------------|----------|
| Mode démo affiché | Symlinks cassés ou venv non activé | Recréer les symlinks (§6.4), activer le venv |
| Port 5000 occupé | Ancien processus `app.py` actif | `pkill -f "python app.py"` |
| `ImportError` sur `main` | Symlink `main.py` cassé | Recréer le lien symbolique |
| Pipeline bloqué à 1100 % CPU | LLaVA chargé sur CPU (CLIP) | Vérifier que `vision_model = None` est actif |
| GPU non détecté par Ollama | Drivers NVIDIA absents ou corrompus | `sudo ubuntu-drivers autoinstall` |
| Vérification externe — erreur 401 | Clé HF invalide | Utiliser le provider `ollama` local |

---

## 9. Déroulement du projet — Séances de travail

| # | Date | Objectif principal | Réalisations clés |
|---|------|--------------------|-------------------|
| 1 | 12/05 | Prise en main | Dépôt GitHub, OS, SSH, 1er script plagiat, WebUI port 3000 |
| 2 | 21/05 | HAOS + liaison Ollama | HAOS activé, Ollama → HAOS via intégration native, test `qwen2.5:3b` |
| 3 | 22/05 | Installation serveur | Barrettes RAM défectueuses retirées, Linux Mint installé, choix `qwen2.5:7b` |
| 4 | 27/05 | Déploiement | Docker via `.deb`, LiteLLM, Ollama, OpenCode installés |
| 5 | 03/06 | Stabilisation | Mêmes objectifs que S4 — consolidation de l'environnement |
| 6 | 04/06 | Mise au point IA | LMStudio abandonné (AVX2), Ollama reinstallé GPU, OpenWebUI multiuser ✅ |
| 7 | 05/06 | Tests approfondis | Infrastructure et détecteur testés (2 versions) |
| 8 | 09/06 | Optimisation VRAM | `sentence_transformers` → CPU, LLaVA désactivé, provider Ollama local ajouté |
| 9 | 16/06 | Tests finaux | Tokens, intégrité IA, sécurisation infrastructure, détecteur renforcé |

**Décisions clés issues des séances :**

- **Séance 3** : décision de prioriser l'automatisation (plagiat) et de mettre de côté
  la gestion fine des tokens/logs pour une phase ultérieure.
- **Séance 6** : abandon de LM Studio (pas d'AVX2 sur Xeon E5-2630 v3) et de LiteLLM
  (liaison Ollama non fonctionnelle). Confirmation de la stack finale : Ollama + OpenWebUI.
- **Séance 8** : décision de désactiver la vérification externe HuggingFace (clé invalide)
  et de la remplacer par `llama3.1:8b` en local → pipeline 100 % local.

---

## 10. Inventaire des fichiers de projet

Les fichiers de travail sont stockés localement dans `F:\sae_projinte\`.

| Fichier / Dossier | Description |
|-------------------|-------------|
| `COMPTE_RENDU_SAE204_...md` | Rapport complet (ce document) |
| `BILAN_MODIFICATIONS.md` | Historique des correctifs GPU / VRAM / symlinks |
| `plagiat_detector.py` | Script CLI standalone — version initiale (531 lignes) |
| `pyvenv.cfg` | Configuration de l'environnement virtuel Python 3.12 |
| `Plan projet` | Notes de conception initiales (architecture, méthodologie) |
| `api token` | Clé HuggingFace `hf_KKfM...` — **à révoquer avant soutenance** |
| `ligne_de_commande` | Historique de 476 commandes shell saisies au cours du projet |
| `install_openwebui_...` | Log terminal complet (neofetch, netstat, Docker, NVIDIA) |
| `image_proj_inte/` | 37 captures d'écran du déploiement (référence visuelle) |
| `projet8inte8vid/` | Scripts, 3 vidéos de démo (`.mkv`), captures supplémentaires |

> Le fichier `api token` contient la clé HuggingFace en clair. Il doit être
> supprimé ou chiffré avant tout partage ou dépôt sur un dépôt public.

---

## 11. Feuille de route — Phase 3

### 11.1 Sécurité (prioritaire)

- [ ] Changer le mot de passe admin Flask (§8.3).
- [ ] Déplacer `HF_API_KEY` dans un fichier `.env` (exclu du dépôt Git via `.gitignore`).
- [ ] **Révoquer** la clé `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` sur HuggingFace.
- [ ] Supprimer ou chiffrer le fichier `api token` dans `F:\sae_projinte\`.
- [ ] Différencier les mots de passe entre OpenWebUI Admin et User.

### 11.2 Améliorations techniques

- [ ] **Comptage des tokens** : extraire `prompt_eval_count` et `eval_count` depuis
  les réponses Ollama et les enregistrer dans la table `token_counters`.
- [ ] **Serveur de production** : remplacer Werkzeug par **gunicorn** avec worker
  `gevent` pour stabiliser le streaming SSE lors de la soutenance.
- [ ] **Calibrage des seuils** : ajuster les paramètres lexicaux (k-shingles)
  et sémantiques (cosinus 0,85) sur un vrai jeu de données de TP.
- [ ] **Réinstaller les drivers GPU NVIDIA** pour une démo fluide sans dégradation.

### 11.3 Préparation de la soutenance

- [ ] **Jeu de test démonstratif** : 1 sujet + 2 rapports dont 1 intentionnellement
  plagié (paraphrase + image réutilisée) pour illustrer les 4 signaux.
- [ ] **Démonstration bout en bout** :
  OpenWebUI (assistant nommé Qwen)
  → app Flask (upload → terminal SSE → rapport PDF)
  → présentation du score multi-signaux.
- [ ] **Argumentaire « local d'abord »** : confidentialité / RGPD vs puissance
  d'un modèle externe ; assumer la contrainte des 8 Go de VRAM comme contrainte
  réelle gérée par des décisions techniques documentées.
- [ ] **Mention HAOS** : présenter brièvement l'intégration domotique comme
  preuve de l'extensibilité de la stack Ollama.

---

## 12. Glossaire

| Terme | Définition |
|-------|------------|
| **Ollama** | Serveur local qui télécharge et exécute des LLM, exposés via une API REST (`:11434`). |
| **OpenWebUI** | Interface web de chat connectée à Ollama, gestion multi-comptes. |
| **Embeddings** | Représentation vectorielle d'un texte permettant de mesurer la similarité de sens (distance cosinus). |
| **Shingling** | Découpage d'un texte en séquences de k mots consécutifs pour comparer les chevauchements lexicaux. |
| **Hash perceptuel** | Empreinte d'image robuste aux petites modifications, permet de détecter les images réutilisées. |
| **SSE** | *Server-Sent Events* — canal HTTP unidirectionnel serveur → navigateur, utilisé pour le terminal live. |
| **Monkey-patching** | Remplacement dynamique d'une fonction à l'exécution (ici, capture de `sys.stdout`). |
| **VLM** | *Vision-Language Model* — modèle capable d'analyser des images (ex. LLaVA). |
| **Headless** | Mode sans interface graphique, piloté exclusivement à distance via réseau. |
| **VRAM** | Mémoire embarquée sur le GPU, limite le nombre et la taille des modèles chargeables simultanément. |
| **AVX2** | Jeu d'instructions CPU requis par LM Studio pour l'inférence. Absent sur le Xeon E5-2630 v3. |
| **WSGI** | Interface serveur Python de production (gunicorn) remplaçant le serveur de développement Werkzeug. |

---

## 13. Récapitulatif des ports et chemins

| Élément | Valeur |
|---------|--------|
| Ollama (API REST) | `http://localhost:11434` |
| OpenWebUI | `http://localhost:3000` |
| Application Flask | `http://localhost:5000` |
| Pipeline CLI | `/home/enzo/Téléchargements/SAE204_scripts/` |
| Application Flask (dossier) | `/home/enzo/Téléchargements/scripts/` |
| Base SQLite | `~/.plagiat_app/plagiat.db` |
| Fichiers de travail | `F:\sae_projinte\` |

---

*Compte-rendu rédigé à partir des notes de projet, du journal des séances et du
dépôt GitHub [AYK0-prog/Local_AI_server](https://github.com/AYK0-prog/Local_AI_server)
— Mis à jour le 17 Juin 2026.*
