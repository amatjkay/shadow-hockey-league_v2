<p align="center">
  <img src="./notebooklm_mcp_logo.png" width="200" alt="Logo de Notebook-mcp-server">
</p>

<h1 align="center">Servidor MCP de NotebookLM</h1>

<p align="center">
  <b>Permite que tus agentes de IA chateen directamente con Google NotebookLM para obtener respuestas sin alucinaciones.</b>
</p>

<p align="center">
  <a href="README.md">English</a> • 
  <b>Español</b> • 
  <a href="README.fr.md">Français</a> • 
  <a href="README.pt.md">Português</a> • 
  <a href="README.de.md">Deutsch</a>
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
  <a href="#instalación">Instalación</a> • 
  <a href="#autenticación">Autenticación</a> • 
  <a href="#inicio-rápido-claude-desktop">Inicio Rápido</a> • 
  <a href="#habilidad-de-claude-code">Claude Code</a> • 
  <a href="#documentación">Documentación</a> •
  <a href="#desarrollo">Desarrollo</a>
</p>

## La Solución

El **Servidor MCP de NotebookLM** lleva el poder de NotebookLM de Google directamente a tu flujo de trabajo aumentado por IA. Construido nativamente en **TypeScript** usando el Model Context Protocol, permite a los agentes leer, buscar y gestionar tus cuadernos como si fueran archivos locales.

---

## 🚀 Instalación

### 1. Instalación Global (Recomendado)

Puedes instalar el servidor directamente desde NPM:

```bash
npm install -g notebooklm-mcp-server
```

> [!NOTE]
> **Auto-actualización**: El servidor busca automáticamente nuevas versiones al iniciarse. Si existe una actualización, se instalará sola y te pedirá que reinicies para asegurar que siempre tengas las últimas correcciones de Google.

### 2. Uso directo con NPX (Sin Configuración)

Si no quieres instalarlo globalmente, puedes ejecutarlo directamente:

```bash
npx notebooklm-mcp-server auth   # Para iniciar sesión
npx notebooklm-mcp-server start  # Para ejecutar el servidor
```

---

## 🔑 Autenticación

Antes de usar el servidor, debes vincularlo a tu Cuenta de Google. Esta versión utiliza una sesión de navegador segura y persistente:

1. Ejecuta el comando de autenticación:
   ```bash
   npx notebooklm-mcp-server auth
   ```
2. Se abrirá una ventana del navegador. Inicia sesión con tu cuenta de Google.
3. Cierra el navegador una vez que veas tus cuadernos. Tu sesión ahora está guardada de forma segura localmente.

> [!TIP]
> **¿Sesión Expirada?** Si tu agente recibe errores de autenticación, simplemente pídele que ejecute el comando `npx notebooklm-mcp-server refresh_auth`. Abrirá automáticamente el navegador para que renueves la sesión sin salir de tu chat.

---

## ⚡ Inicio Rápido

### 🤖 Claude Desktop

Añade lo siguiente a tu `claude_desktop_config.json`:

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

Como VS Code aún no soporta MCP de forma nativa, debes usar una extensión:

#### Opción A: Usando [Cline](https://marketplace.visualstudio.com/items?itemName=saoudrizwan.claude-dev) (Recomendado)

1. Abre los **Ajustes de Cline** en VS Code.
2. Desplázate hasta la sección de **Servidores MCP**.
3. Haz clic en **Añadir Nuevo Servidor MCP**.
4. Usa la siguiente configuración:
   - **Nombre**: `notebooklm`
   - **Comando**: `npx -y notebooklm-mcp-server start`

#### Opción B: Usando [MCP Client](https://marketplace.visualstudio.com/items?itemName=stefan-mcp.mcp-client)

1. Instala la extensión desde el Marketplace.
2. Abre tu `settings.json` de VS Code.
3. Añade el servidor bajo `mcp.servers`:
   ```json
   "mcp.servers": {
     "notebooklm": {
       "command": "npx",
       "args": ["-y", "notebooklm-mcp-server", "start"]
     }
   }
   ```

### 🌌 Antigravity

Antigravity soporta MCP de forma nativa. Puedes añadir el servidor editando tu archivo de configuración global:

1. **Localiza tu `mcp.json`**:
   - **Windows**: `%APPDATA%\antigravity\mcp.json`
   - **macOS**: `~/Library/Application Support/antigravity/mcp.json`
   - **Linux**: `~/.config/antigravity/mcp.json`

2. **Añade el servidor** al objeto `mcpServers`:

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

3. **Reinicia Antigravity**: Las nuevas herramientas aparecerán en tu barra lateral al instante.

---

### 💎 Gemini CLI

Ejecuta el siguiente comando en tu terminal para añadir la habilidad de notebooklm:

```bash
gemini mcp add notebooklm --scope user -- npx -y notebooklm-mcp-server start
```

---

## 🤖 Habilidad de Claude Code

Añádelo instantáneamente a Claude Code:

```bash
claude skill add notebooklm -- "npx -y notebooklm-mcp-server start"
```

---

## 📖 Documentación

Las siguientes herramientas están disponibles a través de este servidor MCP:

### 📒 Gestión de Cuadernos
| Herramienta        | Descripción                                           |
| :----------------- | :---------------------------------------------------- |
| `notebook_list`    | Enumera todos los cuadernos en tu cuenta.             |
| `notebook_create`  | Crea un nuevo cuaderno con un título.                 |
| `notebook_rename`  | Renombra un cuaderno existente.                       |
| `notebook_delete`  | Elimina un cuaderno (Advertencia: Destructivo).       |

### 🖇️ Gestión de Fuentes
| Herramienta              | Descripción                                            |
| :----------------------- | :----------------------------------------------------- |
| `notebook_add_url`        | Añade un sitio web o vídeo de YouTube como fuente.     |
| `notebook_add_text`       | Añade contenido de texto personalizado como fuente.    |
| `notebook_add_local_file` | Sube un archivo local PDF, Markdown o de texto.        |
| `notebook_add_drive`      | Añade un archivo de Google Drive (Docs, Slides, etc).  |
| `source_delete`           | Elimina una fuente de un cuaderno.                     |
| `source_sync`             | Sincroniza una fuente de Drive para obtener la versión más reciente. |

### 🔍 Investigación y Consulta
| Herramienta        | Descripción                                           |
| :----------------- | :---------------------------------------------------- |
| `notebook_query`   | Hace una pregunta basada en fuentes a un cuaderno específico. |
| `research_start`   | Inicia una tarea de investigación en la web/drive.    |
| `research_poll`    | Consulta el estado y los resultados de la investigación. |
| `research_import`  | Importa los resultados de la investigación como fuentes permanentes. |

### 🎨 Estudio y Generación
| Herramienta             | Descripción                                           |
| :---------------------- | :---------------------------------------------------- |
| `audio_overview_create` | Genera un Audio Overview (pódcast).                   |
| `studio_poll`           | Comprueba el estado de los artefactos de audio/vídeo generados. |
| `mind_map_generate`     | Genera un JSON de Mapa Mental a partir de fuentes.    |

### ⚙️ Sistema
| Herramienta    | Descripción                                                        |
| :------------- | :----------------------------------------------------------------- |
| `refresh_auth` | **Interactivo**: Abre un navegador para renovar tu sesión de Google. Úsalo si las herramientas empiezan a fallar. |

---

## 🛠️ Desarrollo

Para contribuir o construir desde el código fuente:

```bash
git clone https://github.com/moodRobotics/notebook-mcp-server.git
npm install
npm run build
```

## 📄 Licencia

Licencia MIT. Desarrollado con ❤️ por [moodRobotics](https://github.com/moodRobotics).
