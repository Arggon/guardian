# Runbook: credenciales de Telegram vencidas

El reporte de resultado por Telegram (issue #5, planificado) falla por token o
chat_id inválidos/vencidos. Rotar credenciales, verificar, y por qué esto NUNCA
debe tumbar el backup.

## Trigger

- El log del timer/cron muestra errores de notificación tras una corrida
  (hoy el módulo de notificación no existe; el trigger aplica desde que aterrice
  issue #5).
- Síntoma típico: la corrida de backup termina bien (exit 0) pero no llegó mensaje
  a Telegram, o llega `401 Unauthorized` / `400 chat not found`.

## Diagnosis

```bash
# 1. Confirmar que el backup SÍ corre (la notificación es un canal, no el pipeline)
uv run guardian backup; echo "exit=$?"   # 0 esperado

# 2. Ver las credenciales configuradas (solo longitud/prefijo, NO imprimir el token completo)
echo "token len=${#GUARDIAN_TELEGRAM_TOKEN} prefijo=${GUARDIAN_TELEGRAM_TOKEN:0:10}"
echo "chat_id=$GUARDIAN_TELEGRAM_CHAT_ID"

# 3. Probar el token contra la API (diagnóstico seguro, sin exponer el token)
curl -s "https://api.telegram.org/bot${GUARDIAN_TELEGRAM_TOKEN}/getMe" | python3 -m json.tool
#   ok:true  → token válido; ok:false, 401 → token vencido/revocado
# 4. Probar chat_id (una vez confirmado el token)
curl -s "https://api.telegram.org/bot${GUARDIAN_TELEGRAM_TOKEN}/sendMessage" \
  -d chat_id="${GUARDIAN_TELEGRAM_CHAT_ID}" -d text="prueba guardian" | python3 -m json.tool
#   ok:false "chat not found" → chat_id mal (hablarle al bot desde el chat correcto
#   y re-obtener el id)
```

## Mitigation

1. **Rotar el token:** con @BotFather (`/revoke` genera token nuevo) y/o revisar
   que el bot siga en el chat. El chat_id no "vence", pero cambia si se usa otro
   chat/canal.

2. **Actualizar las variables de entorno donde corre guardian** (systemd timer:
   `EnvironmentFile=`; cron: perfil del usuario o wrapper). Sin valores en claro
   en el repo:
   ```bash
   export GUARDIAN_TELEGRAM_TOKEN="<nuevo-token>"   # en el EnvironmentFile real
   export GUARDIAN_TELEGRAM_CHAT_ID="<chat-id-correcto>"
   ```

3. **Verificar:** repetir Diagnosis pasos 3-4 hasta `ok:true` en ambos.

4. **Forzar una corrida end-to-end** y confirmar el mensaje:
   ```bash
   uv run guardian backup   # exit 0 + mensaje en Telegram
   ```

5. **Principio inviolable:** un fallo de notificación no debe tumbar ni marcar
   como fallido el backup — el backup verificó sus hashes, el Telegram es solo el
   chismoso. Si al implementar issue #5 un error de Telegram aborta la corrida,
   eso es un bug: filear `arggon create bug "notificación tumba backup" --parent
   <story-notificación>`. Mientras tanto, el exit code del backup manda.

## Escalation

- El token se revoca y no hay acceso al @BotFather dueño del bot → escalar al
  dueño de la cuenta de Telegram: sin bot no hay notificaciones.
- La pérdida de notificaciones pasa desapercibida varios días (nadie miró) →
  escalar: falta un canal alterno (el reporte no debe depender de un solo proveedor).
- Sospecha de fuga del token (estuvo en un log, un dump, un commit) → escalar y
  revocar YA, además de auditar dónde quedó expuesto.

## Rollback

Restaurar las credenciales anteriores en el EnvironmentFile y re-cargar el
servicio/timer. El backup no fue modificado por esta mitigación: no hay nada que
deshacer en el pipeline. Si la rotación del token rompió otra integración que
usaba el token viejo, actualizarla con el nuevo (el viejo quedó revocado).
