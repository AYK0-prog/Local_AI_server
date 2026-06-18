# Serveur IA Local & Détection de Plagiat

![Python](https://img.shields.io/badge/Python-3.12.3-3776AB?logo=python&logoColor=white)
![Docker](https://img.shields.io/badge/Docker-Engine-2496ED?logo=docker&logoColor=white)
![Ollama](https://img.shields.io/badge/Ollama-Local_LLM-black?logo=ollama)
![Flask](https://img.shields.io/badge/Flask-3.x-000000?logo=flask&logoColor=white)
![Linux](https://img.shields.io/badge/Linux_Mint-22.3-87CF3E?logo=linux&logoColor=white)
![License](https://img.shields.io/badge/Licence-MIT-green)

> Projet SAE204 — BUT Réseaux & Télécommunications, Auxerre  
> Auteur : **Enzo Maresia**

Infrastructure IA **100 % locale** hébergeant un assistant conversationnel et un pipeline
de détection de plagiat multi-signaux, sans aucune dépendance à des services cloud externes.

---

## Sommaire

- [Aperçu](#aperçu)
- [Fonctionnalités](#fonctionnalités)
- [Architecture](#architecture)
- [Matériel](#matériel)
- [Prérequis](#prérequis)
- [Installation](#installation)
- [Utilisation](#utilisation)
- [Structure du projet](#structure-du-projet)
- [Modèles IA](#modèles-ia)
- [Notes techniques](#notes-techniques)
- [Licence](#licence)

---

## Aperçu

Ce projet répond à une problématique concrète du département R&T :
disposer d'un serveur IA maîtrisé sur le réseau de l'IUT, conforme RGPD,
sans envoyer de données d'élèves vers des services tiers.

Il est composé de deux blocs indépendants :

| Bloc | Description | Technologies |
|------|-------------|--------------|
| **IA locale** | Assistant conversationnel type ChatGPT, auto-hébergé | Ollama + OpenWebUI + Docker |
| **Anti-plagiat** | Pipeline de comparaison de rapports PDF, 4 signaux combinés | Python 3.12 + Flask + Ollama |

---

## Fonctionnalités

### IA locale
- Modèles de langage servis en local via **Ollama** (API REST sur `:11434`)
- Interface web **OpenWebUI** sur le port `3000` (style ChatGPT, multi-comptes)
- Assistant nommé **Qwen** (modèle `qwen2.5:7b` avec system prompt dédié)
- Compatible **Home Assistant OS** via l'intégration Ollama native (bonus)

### Détection de plagiat
- Extraction de texte PDF natif + **OCR** (Tesseract FR/EN) pour les documents scannés
- **4 signaux indépendants** pondérés pour résister aux contournements classiques :
  - Lexical — shingling k=5 + `rapidfuzz` **(35 %)**
  - Sémantique — embeddings multilingues + similarité cosinus **(35 %)**
  - Images — hash perceptuel **(15 %)**
  - Verdict IA — `gemma3:4b` via Ollama, JSON structuré **(15 %)**
- Exclusion automatique des passages de l'énoncé (`--sujet`)
- **Interface web Flask** avec terminal live (SSE) et export du rapport en PDF
- Historique des analyses en base SQLite

---

## Architecture

```
Réseau privé salle réseaux IUT — 172.17.0.0/24
              |
  +-----------+------------------+
  |         SERVEUR IA           |
  |   2x Xeon E5-2630 v3         |
  |   RTX 3060 Ti — 8 Go VRAM    |
  |   32 Go DDR3                 |
  |   Linux Mint 22.3 (headless) |
  |                              |
  |   [Docker]  OpenWebUI :3000  |
  |   [Systemd] Ollama    :11434 |
  |   [Python]  Flask     :5000  |
  +-----------+------------------+
              |
     +--------+--------+
     |                 |
  Lenovo            MacBook
  (client)          (client)
```

Le pipeline de détection :

```
PDF A + PDF B
     |
     v
[1] Extraction PDF → Markdown (PyMuPDF + Tesseract OCR)
[2] Exclusion du sujet (shingling)
[3] Détection lexicale (shingling k=5 + rapidfuzz)          → score 35 %
[4] Détection sémantique (multilingual-e5-base + cosinus)   → score 35 %
[5] Analyse images (hash perceptuel)                        → score 15 %
[6] Verdict IA (gemma3:4b via Ollama → JSON)                → score 15 %
[7] Score final pondéré + niveau de risque
[8] Rapport PDF (Markdown → HTML → WeasyPrint)
```

---

## Matériel

| Composant | Détail |
|-----------|--------|
| Processeurs | 2× Intel Xeon E5-2630 v3 (32 threads) |
| GPU | NVIDIA RTX 3060 Ti — 8 Go VRAM |
| RAM | 32 Go DDR3 |
| Système | Linux Mint 22.3 — headless |
| Réseau | Filaire — réseau privé salle réseaux IUT (172.17.0.0/24) |

---

## Prérequis

- Linux (testé sur Linux Mint 22.3 / Ubuntu 22.04+)
- Python 3.12+
- Docker Engine (sans Docker Desktop)
- Drivers NVIDIA + `nvidia-container-toolkit` (pour l'accélération GPU)
- Tesseract OCR

```bash
sudo apt update
sudo apt install -y tesseract-ocr tesseract-ocr-fra tesseract-ocr-eng \
                   libpango-1.0-0 libpangoft2-1.0-0 \
                   python3 python3-venv python3-pip git curl
```

---

## Installation

### 1 — Cloner le dépôt

```bash
git clone https://github.com/AYK0-prog/Local_AI_server.git
cd Local_AI_server
```

### 2 — Installer Docker Engine

```bash
# Via le paquet .deb (recommandé sur Linux Mint)
# Télécharger depuis https://docs.docker.com/engine/install/ubuntu/
sudo usermod -aG docker $USER   # puis se reconnecter
```

### 3 — Installer et configurer Ollama

```bash
curl -fsSL https://ollama.com/install.sh | sh

# Exposer Ollama sur le réseau local
sudo systemctl edit ollama
# Ajouter :
# [Service]
# Environment="OLLAMA_HOST=0.0.0.0:11434"

sudo systemctl daemon-reload && sudo systemctl restart ollama
```

### 4 — Télécharger les modèles

```bash
ollama pull gemma3:4b        # verdict IA (pipeline)
ollama pull qwen2.5:7b       # assistant nommé (OpenWebUI)
ollama pull llama3.2:3b      # modèle léger
ollama pull llama3.1:8b      # second avis IA
ollama pull llava:7b         # vision (installé, désactivé — voir Notes)
```

### 5 — Déployer OpenWebUI

```bash
docker run -d --name openwebui -p 3000:8080 \
  --add-host=host.docker.internal:host-gateway \
  -e OLLAMA_BASE_URL=http://host.docker.internal:11434 \
  -v openwebui:/app/backend/data \
  --restart unless-stopped \
  ghcr.io/open-webui/open-webui:main
```

> Ouvrir `http://localhost:3000` — le premier compte créé devient administrateur.

### 6 — Installer le pipeline anti-plagiat

```bash
cd SAE204_scripts
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### 7 — Installer l'application Flask

```bash
cd ../scripts
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Créer les liens symboliques vers le pipeline
ln -sfn ../SAE204_scripts/modules ./modules
ln -sfn ../SAE204_scripts/main.py ./main.py
```

---

## Utilisation

### Pipeline CLI

```bash
cd SAE204_scripts
source venv/bin/activate

# Analyse standard
python3 main.py --a rapport_a.pdf --b rapport_b.pdf --output resultats/

# Avec exclusion de l'énoncé
python3 main.py --a rapport_a.pdf --b rapport_b.pdf --sujet sujet.pdf --output resultats/

# Avec second avis IA local (llama3.1:8b)
python3 main.py --a rapport_a.pdf --b rapport_b.pdf --external --provider ollama
```

### Application web Flask

```bash
cd scripts
source venv/bin/activate
pkill -f "python app.py" 2>/dev/null   # libère le port si nécessaire
python app.py
```

Ouvrir `http://localhost:5000` — identifiants par défaut : `admin` / `admin`

### Niveaux de risque

| Niveau | Score |
|--------|-------|
| 🟢 Faible | < 40 % |
| 🟠 Modéré | 40 % – 69 % |
| 🔴 Élevé | ≥ 70 % |

### Ports et accès

| Service | URL | Identifiants |
|---------|-----|-------------|
| OpenWebUI | `http://localhost:3000` | compte créé à l'installation |
| Flask (plagiat) | `http://localhost:5000` | admin / admin |
| Ollama API | `http://localhost:11434` | accès libre |

---

## Structure du projet

```
Local_AI_server/
├── SAE204_scripts/          # Pipeline de détection (Phase 1)
│   ├── main.py              # Point d'entrée — fonction analyze()
│   ├── modules/             # Modules par signal (lexical, sémantique, images, IA)
│   ├── requirements.txt
│   └── venv/
│
├── scripts/                 # Application web Flask (Phase 2)
│   ├── app.py               # Serveur Flask (~480 lignes)
│   ├── templates/           # 8 vues HTML (Jinja2)
│   ├── external_verify.py   # Module second avis IA
│   ├── modules -> ../SAE204_scripts/modules   # lien symbolique
│   ├── main.py  -> ../SAE204_scripts/main.py  # lien symbolique
│   ├── requirements.txt
│   └── venv/
│
└── README.md
```

La base SQLite des analyses est stockée dans `~/.plagiat_app/plagiat.db`.

---

## Modèles IA

| Modèle | Type | Usage | Taille |
|--------|------|-------|--------|
| `gemma3:4b` | LLM | Verdict IA — étape 6 du pipeline | ~3 Go |
| `qwen2.5:7b` | LLM | Assistant Qwen dans OpenWebUI | ~4,7 Go |
| `llama3.2:3b` | LLM | Modèle léger / tests | ~2 Go |
| `llama3.1:8b` | LLM | Second avis IA (provider local) | ~4,7 Go |
| `llava:7b` | Vision | Installé — **désactivé** (contrainte VRAM) | ~4,7 Go |
| `multilingual-e5-base` | Embeddings | Similarité sémantique FR/EN — forcé CPU | ~1,1 Go |

---

## Notes techniques

### Optimisation VRAM (8 Go)

La RTX 3060 Ti ne peut pas charger simultanément un modèle texte et LLaVA.
Deux ajustements ont été appliqués pour stabiliser le pipeline :

```python
# sentence_transformers forcé sur CPU (libère ~2,3 Go VRAM)
model = SentenceTransformer("intfloat/multilingual-e5-base", device="cpu")

# LLaVA désactivé (évite la boucle llama-server à 1100 % CPU)
vision_model = None
```

### Terminal live — SSE

L'interface Flask intercepte la sortie standard du pipeline (`sys.stdout`)
et pousse chaque ligne vers le navigateur via **Server-Sent Events**.
Si le terminal affiche "Mode Démo", vérifier les liens symboliques :

```bash
ls -l scripts/modules scripts/main.py
```

### Solutions rejetées

| Solution | Raison |
|----------|--------|
| LM Studio | Xeon E5-2630 v3 sans AVX2 (requis pour l'inférence CPU) |
| LiteLLM | Liaison Ollama non fonctionnelle lors des tests d'intégration |
| HuggingFace externe | Clé API invalidée + principe "local d'abord" / RGPD |

---

## Licence

Ce projet est distribué sous licence **MIT**.  
Voir le fichier [LICENSE](LICENSE) pour les détails.

---

*BUT Réseaux & Télécommunications — IUT d'Auxerre — Juin 2026*
