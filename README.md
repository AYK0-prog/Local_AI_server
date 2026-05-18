# Local_AI_server
Local_AI_server pour projet intégratif

# 🚀 Local LLM Server (Ollama + Open WebUI)

Ce projet permet de transformer un PC en un serveur d'Intelligence Artificielle local facilement.
**Pourquoi ?**
Privé et ultra-rapide, accessible depuis n'importe quel appareil du réseau via une interface Web sécurisée.
Imagine que ton meilleur amie ravonte tout tes secret a tout le monde pour se faire du fric, tu fais quoi ?
Beh tu te barre alors pourquoi tu reste avec chat gpt gemini et compagnie alors que tu peux l' avoir en locale chez toi ?

Dans ce projet on utilisera beacoup de docker c' est le moment d' apprendre a l installer au debut c' est super chiant mais quand c' est fais c' est un vraie bonheur gais moi confiance ca vaut vrai,ent le coup.

## 🛠️ Architecture du Projet

* **Moteur IA :** [Ollama](https://ollama.com/) installé via Docker pour simplifier les chose.
* **Interface Utilisateur :** [Open WebUI](https://github.com/open-webui/open-webui) orchestré via Docker, offrant une expérience fluide "à la ChatGPT" avec gestion des utilisateurs (Login/MDP) et logs d'historique.

---

## ⚙️ Prérequis

* **OS :** Ubuntu Desktop 24.04 LTS (ou version récente)
* **Hardware recomandé :** GPU NVIDIA ou AMD avec pilotes propriétaires installés.
* **Logiciels :** Docker, Ollama.

---

## 🚀 Installation et Configuration Step-by-Step

### 1. Configuration d'Ollama (Serveur Natif)

Pour que le serveur Ollama écoute les requêtes du réseau local (et de Docker) plutôt que de rester bloqué sur `localhost`, applique la configuration suivante :

```bash
# Modifier la configuration du service
sudo systemctl edit ollama.service

```

Ajoute ces lignes dans le fichier :

```ini
[Service]
Environment="OLLAMA_HOST=0.0.0.0"

```

Recharge et redémarre le service :

```bash
sudo systemctl daemon-reload
sudo systemctl restart ollama

```

Télécharge le modèle recommandé (optimisé pour 6Go de VRAM) :

```bash
ollama pull qwen2.5:3b

```

### 2. Ouverture des Ports (Pare-feu Ubuntu)

Indispensable pour permettre à ton client d'accéder à l'interface et à l'API :

```bash
sudo ufw allow 3000/tcp   # Port d'Open WebUI
sudo ufw allow 11434/tcp  # Port de l'API Ollama
sudo ufw reload

```

### 3. Déploiement d'Open WebUI (Docker)

Lance l'interface utilisateur en l'exposant sur toutes les interfaces réseau (`0.0.0.0`) pour la rendre accessible à votre MacBook :

```bash
docker run -d -p 0.0.0.0:3000:8080 \
  --add-host=host.docker.internal:host-gateway \
  -v open-webui:/app/backend/data \
  --name open-webui \
  ghcr.io/open-webui/open-webui:main

```

---

## 💻 Utilisation

1. Récupére l'IP locale du serveur Linux (ex: `192.168.1.XX`) avec la commande `ip a`.
2. Depuis en n'allant sur ta seconde machine, ouvre ton navigateur à l'adresse : `http://xxx.xxx.x.XX:3000`.
3. Le premier compte créé devient automatiquement le compte **Administrateur**. Tu pourras ensuite créer des accès spécifiques (Login/MDP) pour d'autres utilisateurs.

---

## 📊 Monitoring des performances

Pour vérifier que l'IA sollicite bien la mémoire de ta carte graphique NVIDIA, ouvre un terminal sur le serveur et tapez :

```bash
nvidia-smi

```

---

Tu peux bien sûr adapter les versions des modèles d' IA selon tes besoin.

Tu veux ajouter ton IA a ton Home-Assistant ?

Dans cette partie nous conseillons d' avoir un au moins un équipement capable de d' envoyer des commande vocale au Home-Assistant.

Ici nous travailleront avec une enceinte connécté google NEST mais n' importe quel autre enceinte mère devrait fonctionner.

Voici la procédure : 

Étape 1 : Récupérer l'IP de ton PC portable

Sur ton ordinateur portable, récupère son adresse IP locale (ex: 192.168.1.25).

Étape 2 : L'ajouter dans HAOS

Dans l'interface de ton Home Assistant, va dans Paramètres ⚙️ -> Appareils et services.

Clique sur le bouton bleu + Ajouter une intégration en bas à droite.

Tape Ollama dans la barre de recherche et sélectionne-le.

Dans la case URL, entre l'adresse IP de ton ordinateur portable suivie du port de Docker :
[http://192.168.1.25:11434](http://192.168.1.25:11434) (pense à remplacer par la vraie IP de ton PC).

Clique sur Soumettre. HAOS va se connecter à ton Docker et charger automatiquement les modèles que tu as déjà téléchargés (comme Llama ou Mistral).

Étape 3 : Lier l'IA à tes commandes vocales ou textuelles

Pour pouvoir lui parler directement depuis ton interface :

Va dans Paramètres -> Voix et assistants.

Clique sur Home Assistant (l'assistant par défaut).

Dans la section Agent de conversation, remplace "Home Assistant" par Ollama.

C'est tout bon ! Ton IA locale en Docker est connectée. Tu peux ajouter une carte Conversation sur ton tableau de bord pour commencer à discuter avec elle.
