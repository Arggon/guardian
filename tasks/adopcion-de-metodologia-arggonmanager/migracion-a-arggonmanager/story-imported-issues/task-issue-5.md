---
type: task
status: todo
id: task-issue-5
title: "issue #5: Reporte de estado de backups por Telegram"
parent: story-imported-issues
labels: [enhancement]
created: "2026-09-13"
updated: "2026-09-13"
issue: 5
---
## Objetivo
Después de cada corrida (o de un fallo), enviar un resumen a un chat de Telegram: backup id, archivos, bytes, verificación SHA-256 ok/fallida, errores.

## Detalles
- Token y chat_id vía variables de entorno (`GUARDIAN_TELEGRAM_TOKEN`, `GUARDIAN_TELEGRAM_CHAT_ID`) — nunca en el TOML ni en el repo.
- Fallo de envío **no** debe fallar el backup (reportar warning).
- Endpoint: https://api.telegram.org/bot<token>/sendMessage

## Criterio de aceptación
- Con credenciales válidas, un backup envía el mensaje; sin red, el backup sigue exit 0 con warning.
> imported from issue #5
