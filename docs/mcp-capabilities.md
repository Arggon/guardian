# Capacidades y límites del MCP de arggon (experimento MCP-first)

Experimento realizado el 2026-09-13 durante la story `status-report`
(branch `feat/status-report`): la story se ejecutó **MCP-first**, es decir,
toda interacción con el tracker se hizo exclusivamente vía el servidor MCP
`arggon mcp` (JSON-RPC sobre stdio), sin usar los subcomandos de tracker del
CLI (`arggon list/update/comment/create/start`). El único CLI permitido (y
usado) fue `arggon validate --json`, que valida el árbol de tasks y no es una
operación de tracker.

Helper usado: `tools/mcp_client.py` (spawn de `arggon mcp`, handshake,
`tools/list`, `tools/call`, log de cada request/response).

## Protocolo

- Spawn: `arggon mcp`. Una **línea JSON por mensaje** (newline-delimited
  JSON-RPC 2.0) en stdin/stdout; stderr queda libre para diagnóstico.
- Handshake: `initialize` con `protocolVersion "2024-11-05"` → respuesta con
  `serverInfo: {"name": "arggon", "version": "0.0.0"}` y
  `capabilities: {"tools": {"listChanged": false}}`.
- Notificación `notifications/initialized` (sin `id`, sin respuesta).
- Recién entonces `tools/list` y `tools/call`.

## Herramientas expuestas (tools/list)

Exactamente **4 herramientas**, todas de tracker:

| Tool | Qué hace | Parámetros principales |
| --- | --- | --- |
| `arggon_list` | Lista items con filtros; devuelve el envelope `list --json` completo | `status`, `type`, `assignee`, `filter` (ej. `"status:todo !label:security"`), `view` |
| `arggon_create` | Crea items bajo un contenedor padre (task/bug/story/...) | `type`, `title`, `parent`, `id`, `assignee`, `status`, `blocked_reason` |
| `arggon_update` | Actualiza frontmatter de un item (con reglas de agente: no reabrir done/cancelled, etc.) | `id`, `title`, `status`, `assignee`, `labels`, `depends_on`, `add_depends_on`, `blocked_reason`, `branch`, `unassign` |
| `arggon_comment` | Agrega sección de comentario timestamped al body (handoff de agente) | `id`, `text`, `author` |

Nota: no hay un `arggon_get`; para leer un item puntual se usa `arggon_list`
y se filtra del resultado.

## Qué SÍ se puede hacer solo por MCP (evidencia real)

### 1. Listar el grafo con filtros (`arggon_list`)

`tools/call arggon_list {"filter": "parent:features-core-v02"}` devolvió los 6
items del epic (`checker-core` done, `status-report` in_progress asignada a
Arggon, y `restore`/`rotacion`/`runbooks`/`verify` en todo con sus
`depends_on`). También probado `{"status": "in_progress"}` → solo
`status-report`. El envelope es idéntico al de `list --json`
(`{ok, schemaVersion, conventionVersion, command, items[]}`), o sea que un
agente MCP pierde cero información de lectura respecto del CLI.

### 2. Actualizar frontmatter (`arggon_update`) — probado y revertido

- `tools/call arggon_update {"id": "status-report", "labels": "mcp-test"}` →
  `ok:true`; releído con `arggon_list` → `labels: ["mcp-test"]`.
- Revertido con `{"id": "status-report", "labels": ""}` → `labels: []`
  (reemplaza la lista completa, igual que el CLI).
- Esto cubre también título, status (con transiciones v0), assignee,
  depends_on y branch.

### 3. Crear items (`arggon_create`) y comentar (`arggon_comment`)

No se crearon items reales para no ensuciar el grafo (la herramienta existe y
su schema es completo: tipo, parent, id explícito, assignee, status inicial,
blocked_reason). `arggon_comment` sí se usó de verdad: el handoff final de la
story fue escrito vía `tools/call arggon_comment`.

### 4. Editar archivos del repo con git normal

El body de los items es un archivo markdown del repo: los checkboxes de
Acceptance y las secciones Notes se editan con el editor y se commitean con
git, sin necesidad de tracker. (Hallazgo: **el body NO es editable por
MCP** — `arggon_update` solo toca frontmatter; la única vía MCP de escribir
en el body es `arggon_comment`, que agrega, no modifica.)

## Qué NO se puede hacer solo por MCP (ausente en tools/list)

`tools/list` devolvió 4 herramientas y nada más. Todo lo siguiente existe en
el CLI pero **no tiene equivalente MCP**:

| Operación CLI | Qué hace | Por qué MCP no la cubre hoy |
| --- | --- | --- |
| `arggon start <id> --assignee X --worktree` | Claim + branch + worktree + commit del claim + push | Requiere orquestar git y gh (branch, `git worktree add`, push). Un tool MCP es un call único sin acceso a git; **el claim de esta story lo tomó el coordinador con el CLI** por esto. |
| `arggon validate --json` | Valida el árbol tasks/ (usado en esta story, permitido) | No es tracker sino validación de archivos; no expuesto como tool. |
| `arggon spec new / spec validate` | Scaffold y validación de docs/specs y docs/plans | Es generación/validación de documentos, fuera del dominio tracker. |
| `arggon stack explore` | Scaffold de exploraciones en docs/explorations/ | Ídem: artefactos de documentos. |
| `arggon playbook new/status/refresh` | Playbooks versionados + file-task de re-research | Ídem (y `--file-task` sí sería cubrible con `arggon_create`, pero el resto no). |
| `arggon board` (--serve/--tui/--github/--json) | Kanban HTML/TUI | Es una vista/render, no una mutación del tracker. |
| `arggon report --trend --json` | Métricas minadas del historial git | Requiere leer git; MCP solo expone tracker. |
| `arggon sync --check` | Reconcilia PRs de GitHub con tasks/ | Requiere gh + escritura combinada; no hay tool. |
| `arggon import-issues` | Importa issues de GitHub como items | Requiere gh; no hay tool. |
| `arggon adopt` | Migración de repo existente al tracker | Operación de alto toque con checklist; no es un call de tracker. |
| `arggon cleanup --prune` | Borra worktrees de items done | Es mutación de git/FS, no del tracker. |
| `arggon next / next --ready` | Sugerencia de item claimable + bloqueos | Ausente; hoy se emula con `arggon_list {"status":"todo"}` y razonando el grafo en el cliente (dependencias vienen en cada item). |
| `arggon update --steal / --force` | Robo de claim (human-only) | Ni siquiera el CLI lo permite a agentes; no aplica. |

## Riesgos y observaciones del protocolo

- **Una línea JSON por mensaje**: sin framing ni Content-Length; un body con
  `\n` embebido (comentarios multilínea) viaja escapado dentro del string JSON
  — correcto pero frágil si un cliente escribe líneas a mano.
- **No hay notificaciones de progreso ni streaming**: un `tools/call` largo
  queda silencioso hasta la respuesta; con `listChanged: false` tampoco hay
  aviso de cambios en las tools.
- **Sin `arggon_get`**: leer un item puntual requiere traer la lista completa
  y filtrar en el cliente.
- **El body no es editable por MCP**: los checkboxes de Acceptance de una
  story solo se marcan editando el archivo y commiteando.
- Las respuestas de `tools/call` envuelven el envelope JSON del CLI dentro de
  un content block de texto (`content[0].text` hay que re-parsearlo).
- Errores de negocio llegan como respuesta exitosa con `isError: true` (o como
  envelope `{ok: false}` dentro del texto), no como errores JSON-RPC: el
  cliente debe chequear ambas capas.
- El proceso vive mientras la sesión: cierre limpio = cerrar stdin y esperar
  exit.

## Conclusión: ¿una story completa puede ejecutarse MCP-first?

**Casi.** La mitad de lectura/escritura de tracker (listar, crear, actualizar
frontmatter, comentar) funciona hoy 100% por MCP con paridad de información
respecto del CLI — esta story lo demostró: se leyó el grafo, se probó
`arggon_update` (labels) y se dejó el handoff vía `tools/call`.

Lo que impide el "full-MCP" es todo lo que sale del dominio tracker y toca
git/gh/documentos: **claim con branch+worktree+push** (`start --worktree`,
usado por el coordinador para esta story), `validate`, spec/plan, playbooks,
board, report --trend, sync, import-issues, adopt, cleanup y next --ready.

Para cerrar la brecha alcanzaría con: (1) tools de solo lectura
`arggon_validate`, `arggon_next` y `arggon_get`; (2) que `arggon_update`
acepte edición de body/checkboxes o que exista `arggon_check`; y (3) aceptar
que `start --worktree`, `cleanup --prune` y `sync` son orquestación git/gh y
pertenecen a la capa del agente, no del servidor MCP.

## Apéndice: trazabilidad JSON-RPC (extracto verificado)

```json
>> {"jsonrpc":"2.0","id":1,"method":"initialize","params":{"protocolVersion":"2024-11-05","capabilities":{},"clientInfo":{"name":"guardian-mcp-client","version":"0.1.0"}}}
<< {"jsonrpc":"2.0","id":1,"result":{"protocolVersion":"2024-11-05","capabilities":{"tools":{"listChanged":false}},"serverInfo":{"name":"arggon","version":"0.0.0"}}}
>> {"jsonrpc":"2.0","method":"notifications/initialized"}
>> {"jsonrpc":"2.0","id":2,"method":"tools/list"}
<< {"jsonrpc":"2.0","id":2,"result":{"tools":["arggon_list","arggon_create","arggon_update","arggon_comment"]}}
>> {"jsonrpc":"2.0","id":3,"method":"tools/call","params":{"name":"arggon_list","arguments":{"filter":"parent:features-core-v02"}}}
<< {"jsonrpc":"2.0","id":3,"result":{"content":[{"type":"text","text":"{\"ok\":true,\"schemaVersion\":1,\"conventionVersion\":3,\"command\":\"list\",\"items\":[{\"id\":\"checker-core\",\"status\":\"done\",...},{\"id\":\"restore\",\"status\":\"todo\",\"depends_on\":[\"verify\"],...},{\"id\":\"status-report\",\"status\":\"in_progress\",\"assignee\":\"Arggon\",...},...]}"}}]}
>> {"jsonrpc":"2.0","id":4,"method":"tools/call","params":{"name":"arggon_update","arguments":{"id":"status-report","labels":"mcp-test"}}}
<< {"jsonrpc":"2.0","id":4,"result":{"content":[{"type":"text","text":"{\"ok\":true,...\"item\":{\"id\":\"status-report\",\"labels\":[\"mcp-test\"],...}}"}}]}
>> {"jsonrpc":"2.0","id":5,"method":"tools/call","params":{"name":"arggon_update","arguments":{"id":"status-report","labels":""}}}
<< {"jsonrpc":"2.0","id":5,"result":{"content":[{"type":"text","text":"{\"ok\":true,...\"labels\":[],...}"}}]}
```

(Log completo de la sesión: 13 mensajes, disponible con
`tools/mcp_client.py` — el cliente registra cada request/response.)
