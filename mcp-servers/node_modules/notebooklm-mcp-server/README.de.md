<p align="center">
  <img src="./notebooklm_mcp_logo.png" width="200" alt="Notebook-mcp-server Logo">
</p>

<h1 align="center">NotebookLM MCP-Server</h1>

<p align="center">
  <b>Lassen Sie Ihre KI-Agenten direkt mit Google NotebookLM chatten, um Antworten ohne Halluzinationen zu erhalten.</b>
</p>

<p align="center">
  <a href="README.md">English</a> • 
  <a href="README.es.md">Español</a> • 
  <a href="README.fr.md">Français</a> • 
  <a href="README.pt.md">Português</a> • 
  <b>Deutsch</b>
</p>

<p align="center">
  <a href="https://www.typescriptlang.org/"><img src="https://img.shields.io/badge/TypeScript-3178C6?style=for-the-badge&logo=typescript&logoColor=white" alt="TypeScript"></a>
  <a href="https://modelcontextprotocol.io"><img src="https://img.shields.io/badge/MCP-Model%20Context%20Protocol-orange?style=for-the-badge" alt="MCP"></a>
  <a href="https://www.npmjs.com/package/notebooklm-mcp-server"><img src="https://img.shields.io/badge/NPM-CB3837?style=for-the-badge&logo=npm&logoColor=white" alt="NPM"></a>
</p>

<p align="center">
  <img src="https://img.shields.io/badge/Windows-0078D4?style=for-the-badge&logo=windows&logoColor=white" alt="Windows">
  <img src="https://img.shields.io/badge/macOS-000000?style=for-the-badge&logo=apple&logoColor=white" alt="macOS">
  <img src="https://img.shields.io/badge/Linux-FCC624?style=for-the-badge&logo=linux&logoColor=black" alt="Linux">
</p>

<p align="center">
  <a href="https://anthropic.com"><img src="https://img.shields.io/badge/Claude%20Code-Skill-blueviolet?style=for-the-badge" alt="Claude Code"></a>
  <a href="https://geminicli.com/"><img src="https://img.shields.io/badge/Gemini%20CLI-Skill-blueviolet?style=for-the-badge" alt="Gemini CLI"></a>
  <img src="https://img.shields.io/badge/Cursor-000000?style=for-the-badge&logo=cursor&logoColor=white" alt="Cursor">
  <img src="https://img.shields.io/badge/Windsurf-00AEEF?style=for-the-badge" alt="Windsurf">
  <img src="https://img.shields.io/badge/Cline-FF5733?style=for-the-badge" alt="Cline">
</p>

<p align="center">
  <a href="#installation">Installation</a> • 
  <a href="#authentifizierung">Authentifizierung</a> • 
  <a href="#schnellstart-claude-desktop">Schnellstart</a> • 
  <a href="#claude-code-skill">Claude Code</a> • 
  <a href="#dokumentation">Dokumentation</a> •
  <a href="#entwicklung">Entwicklung</a>
</p>

## Die Lösung

Der **NotebookLM MCP-Server** bringt die Leistungsfähigkeit von Google NotebookLM direkt in Ihren KI-unterstützten Arbeitsablauf. Nativ in **TypeScript** unter Verwendung des Model Context Protocols entwickelt, ermöglicht er KI-Agenten das Lesen, Suchen und Verwalten Ihrer Notebooks so, als wären es lokale Dateien.

---

## 🚀 Installation

### 1. Globale Installation (Empfohlen)

Sie können den Server direkt über NPM installieren:

```bash
npm install -g notebooklm-mcp-server
```

> [!NOTE]
> **Auto-Update**: Der Server prüft beim Start automatisch auf neue Versionen. Wenn ein Update verfügbar ist, installiert er sich selbst und bittet Sie um einen Neustart, um sicherzustellen, dass Sie immer die neuesten Google-Fixes haben.

### 2. Direkte Verwendung mit NPX (Zero-Config)

Wenn Sie den Server nicht global installieren möchten, können Sie ihn direkt ausführen:

```bash
npx notebooklm-mcp-server auth   # Zur Anmeldung
npx notebooklm-mcp-server start  # Zum Starten des Servers
```

---

## 🔑 Authentifizierung

Bevor Sie den Server verwenden können, müssen Sie ihn mit Ihrem Google-Konto verknüpfen. Diese Version verwendet eine sichere, persistente Browsersitzung:

1. Führen Sie den Authentifizierungsbefehl aus:
   ```bash
   npx notebooklm-mcp-server auth
   ```
2. Ein Browserfenster öffnet sich. Melden Sie sich mit Ihrem Google-Konto an.
3. Schließen Sie den Browser, sobald Sie Ihre Notebooks sehen. Ihre Sitzung ist nun lokal sicher gespeichert.

> [!TIP]
> **Sitzung abgelaufen?** Wenn Ihr Agent Authentifizierungsfehler erhält, bitten Sie ihn einfach, den Befehl `npx notebooklm-mcp-server refresh_auth` auszuführen. Er öffnet automatisch den Browser, damit Sie die Sitzung erneuern können, ohne den Chat verlassen zu müssen.

---

## ⚡ Schnellstart

### 🤖 Claude Desktop

Fügen Sie Folgendes zu Ihrer `claude_desktop_config.json` hinzu:

```json
{
  "mcpServers": {
    "notebooklm": {
      "command": "npx",
      "args": ["-y", "notebooklm-mcp-server", "start"]
    }
  }
}
```

### 💻 Visual Studio Code

Da VS Code MCP noch nicht nativ unterstützt, müssen Sie eine Erweiterung verwenden:

#### Option A: Verwendung von [Cline](https://marketplace.visualstudio.com/items?itemName=saoudrizwan.claude-dev) (Empfohlen)

1. Öffnen Sie die **Cline-Einstellungen** in VS Code.
2. Scrollen Sie zum Abschnitt **MCP-Server**.
3. Klicken Sie auf **Add New MCP Server**.
4. Verwenden Sie die folgende Konfiguration:
   - **Name**: `notebooklm`
   - **Befehl**: `npx -y notebooklm-mcp-server start`

#### Option B: Verwendung von [MCP Client](https://marketplace.visualstudio.com/items?itemName=stefan-mcp.mcp-client)

1. Installieren Sie die Erweiterung aus dem Marketplace.
2. Öffnen Sie Ihre VS Code `settings.json`.
3. Fügen Sie den Server unter `mcp.servers` hinzu:
   ```json
   "mcp.servers": {
     "notebooklm": {
       "command": "npx",
       "args": ["-y", "notebooklm-mcp-server", "start"]
     }
   }
   ```

### 🌌 Antigravity

Antigravity unterstützt MCP nativ. Sie können den Server hinzufügen, indem Sie Ihre globale Konfigurationsdatei bearbeiten:

1. **Suchen Sie Ihre `mcp.json`**:
   - **Windows**: `%APPDATA%\antigravity\mcp.json`
   - **macOS**: `~/Library/Application Support/antigravity/mcp.json`
   - **Linux**: `~/.config/antigravity/mcp.json`

2. **Fügen Sie den Server** zum `mcpServers`-Objekt hinzu:

```json
{
  "mcpServers": {
    "notebooklm": {
      "command": "npx",
      "args": ["-y", "notebooklm-mcp-server", "start"]
    }
  }
}
```

3. **Starten Sie Antigravity neu**: Die neuen Tools erscheinen sofort in Ihrer Seitenleiste.

---

### 💎 Gemini CLI

Führen Sie den folgenden Befehl in Ihrem Terminal aus, um den notebooklm-Skill hinzuzufügen:

```bash
gemini mcp add notebooklm --scope user -- npx -y notebooklm-mcp-server start
```

---

## 🤖 Claude Code Skill

Fügen Sie ihn sofort zu Claude Code hinzu:

```bash
claude skill add notebooklm -- "npx -y notebooklm-mcp-server start"
```

---

## 📖 Dokumentation

Die folgenden Tools sind über diesen MCP-Server verfügbar:

### 📒 Notebook-Verwaltung
| Tool               | Beschreibung                                           |
| :----------------- | :----------------------------------------------------|
| `notebook_list`    | Listet alle Notebooks in Ihrem Konto auf.             |
| `notebook_create`  | Erstellt ein neues Notebook mit einem Titel.          |
| `notebook_rename`  | Benennt ein vorhandenes Notebook um.                  |
| `notebook_delete`  | Löscht ein Notebook (Warnung: Destruktiv).            |

### 🖇️ Quellen-Verwaltung
| Tool                     | Beschreibung                                           |
| :----------------------- | :----------------------------------------------------- |
| `notebook_add_url`        | Fügt eine Website oder ein YouTube-Video als Quelle hinzu. |
| `notebook_add_text`       | Fügt benutzerdefinierten Textinhalt als Quelle hinzu. |
| `notebook_add_local_file` | Lädt eine lokale PDF-, Markdown- oder Textdatei hoch. |
| `notebook_add_drive`      | Fügt eine Datei von Google Drive (Docs, Slides etc.) hinzu. |
| `source_delete`           | Entfernt eine Quelle aus einem Notebook.               |
| `source_sync`             | Synchronisiert eine Drive-Quelle, um die neueste Version zu erhalten. |

### 🔍 Recherche & Abfrage
| Tool               | Beschreibung                                           |
| :----------------- | :---------------------------------------------------- |
| `notebook_query`   | Stellt eine auf Quellen basierende Frage an ein bestimmtes Notebook. |
| `research_start`   | Startet eine Web-/Drive-Rechercheaufgabe.             |
| `research_poll`    | Fragt den Status und die Ergebnisse der Recherche ab. |
| `research_import`  | Importiert Rechercheergebnisse als permanente Quellen. |

### 🎨 Studio & Generierung
| Tool                    | Beschreibung                                           |
| :---------------------- | :---------------------------------------------------- |
| `audio_overview_create` | Generiert eine Audio-Übersicht (Podcast).             |
| `studio_poll`           | Prüft den Status generierter Audio-/Video-Artefakte.  |
| `mind_map_generate`     | Generiert eine Mind-Map-JSON aus Quellen.             |

### ⚙️ System
| Tool           | Beschreibung                                                        |
| :------------- | :----------------------------------------------------------------- |
| `refresh_auth` | **Interaktiv**: Öffnet einen Browser, um Ihre Google-Sitzung zu erneuern. Verwenden Sie dies, wenn die Tools fehlschlagen. |

---

## 🛠️ Entwicklung

Um beizutragen oder aus dem Quellcode zu erstellen:

```bash
git clone https://github.com/moodRobotics/notebook-mcp-server.git
npm install
npm run build
```

## 📄 Lizenz

MIT-Lizenz. Entwickelt mit ❤️ von [moodRobotics](https://github.com/moodRobotics).
