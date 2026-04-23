<p align="center">
  <img src="./notebooklm_mcp_logo.png" width="200" alt="Logo do Notebook-mcp-server">
</p>

<h1 align="center">Servidor MCP do NotebookLM</h1>

<p align="center">
  <b>Permita que seus agentes de IA conversem diretamente con o Google NotebookLM para respostas sem alucinações.</b>
</p>

<p align="center">
  <a href="README.md">English</a> • 
  <a href="README.es.md">Español</a> • 
  <a href="README.fr.md">Français</a> • 
  <b>Português</b> • 
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
  <a href="#instalação">Instalação</a> • 
  <a href="#autenticação">Autenticação</a> • 
  <a href="#início-rápido-claude-desktop">Início Rápido</a> • 
  <a href="#habilidade-do-claude-code">Claude Code</a> • 
  <a href="#documentação">Documentación</a> •
  <a href="#desenvolvimento">Desenvolvimento</a>
</p>

## A Solução

O **Servidor MCP do NotebookLM** traz o poder do NotebookLM do Google diretamente para o seu fluxo de trabalho aumentado por IA. Desenvolvido nativamente en **TypeScript** usando o Model Context Protocol, ele permite que os agentes leiam, pesquisem e gerenciem seus cadernos como se fossem arquivos locais.

---

## 🚀 Instalação

### 1. Instalação Global (Recomendada)

Você pode instalar o servidor directamente pelo NPM:

```bash
npm install -g notebooklm-mcp-server
```

> [!NOTE]
> **Auto-atualização**: O servidor verifica automaticamente novas versões na inicialização. Se houver uma atualização, ela será instalada sozinha e solicitará que você reinicie para garantir que sempre tenha as correções mais recentes do Google.

### 2. Uso direto com NPX (Zero-Config)

Se você não quiser instalá-lo globalmente, pode executá-lo diretamente:

```bash
npx notebooklm-mcp-server auth   # Para logar
npx notebooklm-mcp-server start  # Para rodar o servidor
```

---

## 🔑 Autenticação

Antes de usar o servidor, você deve conectá-lo à sua Conta do Google. Esta versão usa uma seção de navegador segura e persistente:

1. Execute o comando de autenticação:
   ```bash
   npx notebooklm-mcp-server auth
   ```
2. Uma janela do navegador será aberta. Faça login com sua conta do Google.
3. Feche o navegador assim que visualizar seus cadernos. Sua sessão agora está salva localmente de forma segura.

> [!TIP]
> **Sessão Expirada?** Se o seu agente receber erros de autenticação, basta pedir que ele execute o comando `npx notebooklm-mcp-server refresh_auth`. Ele abrirá automaticamente o navegador para você renovar a sessão sem sair do chat.

---

## ⚡ Início Rápido

### 🤖 Claude Desktop

Adicione o seguinte ao seu `claude_desktop_config.json`:

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

Como o VS Code ainda não suporta MCP nativamente, você deve usar uma extensão:

#### Opção A: Usando [Cline](https://marketplace.visualstudio.com/items?itemName=saoudrizwan.claude-dev) (Recomendado)

1. Abra as **Configurações do Cline** no VS Code.
2. Role até a seção **MCP Servers**.
3. Clique em **Add New MCP Server**.
4. Use a seguinte configuração:
   - **Nome**: `notebooklm`
   - **Comando**: `npx -y notebooklm-mcp-server start`

#### Opção B: Usando [MCP Client](https://marketplace.visualstudio.com/items?itemName=stefan-mcp.mcp-client)

1. Instale a extensão no Marketplace.
2. Abra o seu `settings.json` do VS Code.
3. Adicione o servidor sob `mcp.servers`:
   ```json
   "mcp.servers": {
     "notebooklm": {
       "command": "npx",
       "args": ["-y", "notebooklm-mcp-server", "start"]
     }
   }
   ```

### 🌌 Antigravity

O Antigravity suporta MCP nativamente. Você pode adicionar o servidor editando o seu arquivo de configuração global:

1. **Localize o seu `mcp.json`**:
   - **Windows**: `%APPDATA%\antigravity\mcp.json`
   - **macOS**: `~/Library/Application Support/antigravity/mcp.json`
   - **Linux**: `~/.config/antigravity/mcp.json`

2. **Adicione o servidor** ao objeto `mcpServers`:

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

3. **Reinicie o Antigravity**: As novas ferramentas aparecerão na sua barra lateral instantaneamente.

---

### 💎 Gemini CLI

Execute o seguinte comando no seu terminal para adicionar a habilidade notebooklm:

```bash
gemini mcp add notebooklm --scope user -- npx -y notebooklm-mcp-server start
```

---

## 🤖 Habilidade do Claude Code

Adicione instantaneamente ao Claude Code:

```bash
claude skill add notebooklm -- "npx -y notebooklm-mcp-server start"
```

---

## 📖 Documentação

As seguintes ferramentas estão disponíveis através deste servidor MCP:

### 📒 Gerenciamento de Cadernos
| Ferramenta         | Descrição                                             |
| :----------------- | :---------------------------------------------------- |
| `notebook_list`    | Lista todos os cadernos da sua conta.                 |
| `notebook_create`  | Cria um novo caderno com um título.                   |
| `notebook_rename`  | Renomeia um caderno existente.                         |
| `notebook_delete`  | Exclui um caderno (Aviso: Destrutivo).                |

### 🖇️ Gerenciamento de Fontes
| Ferramenta               | Descrição                                              |
| :----------------------- | :----------------------------------------------------- |
| `notebook_add_url`        | Adiciona um site ou vídeo do YouTube como fonte.       |
| `notebook_add_text`       | Adiciona conteúdo de texto personalizado como fonte.   |
| `notebook_add_local_file` | Faz upload de um arquivo local PDF, Markdown ou Texto. |
| `notebook_add_drive`      | Adiciona um arquivo do Google Drive (Docs, Slides, etc). |
| `source_delete`           | Remove uma fonte de um caderno.                        |
| `source_sync`             | Sincroniza uma fonte do Drive para obter a versão mais recente. |

### 🔍 Pesquisa e Consulta
| Ferramenta         | Descrição                                             |
| :----------------- | :---------------------------------------------------- |
| `notebook_query`   | Faz uma pergunta baseada em fontes a um caderno específico. |
| `research_start`   | Inicia uma tarefa de pesquisa na web/drive.           |
| `research_poll`    | Consulta o status e os resultados da pesquisa.         |
| `research_import`  | Importa resultados de pesquisa como fontes permanentes. |

### 🎨 Estúdio e Geração
| Ferramenta              | Descrição                                             |
| :---------------------- | :---------------------------------------------------- |
| `audio_overview_create` | Gera um Audio Overview (podcast).                     |
| `studio_poll`           | Verifica o status dos artefatos de áudio/vídeo gerados. |
| `mind_map_generate`     | Gera um JSON de Mapa Mental a partir das fontes.      |

### ⚙️ Sistema
| Ferramenta     | Descrição                                                          |
| :------------- | :----------------------------------------------------------------- |
| `refresh_auth` | **Interativo**: Abre um navegador para renovar sua sessão do Google. Use isso se as ferramentas começarem a falhar. |

---

## 🛠️ Desenvolvimento

Para contribuir ou construir a partir do código fonte:

```bash
git clone https://github.com/moodRobotics/notebook-mcp-server.git
npm install
npm run build
```

## 📄 Licença

Licença MIT. Desenvolvido com ❤️ pela [moodRobotics](https://github.com/moodRobotics).
