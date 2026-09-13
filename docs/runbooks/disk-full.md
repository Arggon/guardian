# Runbook: disco lleno en el destino

El backup falla porque el disco del destino se queda sin espacio (ENOSPC):
diagnosticar, liberar de forma segura y reanudar.

## Trigger

- `uv run guardian backup` termina con `OSError: [Errno 28] No space left on device`
  (hoy puede manifestarse como traceback: ENOSPC no está mapeado a exit code
  todavía — exit codes actuales: 0 ok, 2 config, 3 integridad).
- El directorio del backup quedó sin `manifest.json` (la corrida murió a mitad:
  invariante 1 de docs/FORMAT.md → backup incompleto).

## Diagnosis

```bash
# 1. Espacio en el filesystem del destino
df -h /ruta/destino

# 2. Cuánto ocupan los backups y cuáles son los más pesados
du -sh /ruta/destino/* | sort -rh | head

# 3. Quedó residuo de la corrida fallida? (sin manifiesto = incompleto)
ls -1t /ruta/destino/
ls /ruta/destino/$(ls -1t /ruta/destino/ | head -1)/manifest.json 2>&1

# 4. Corrida en curso? (no liberar nada si hay un guardian vivo)
pgrep -af guardian
```

Referencia de escala: el costo por corrida es ~el tamaño de los orígenes completos
(sin deduplicación ni incrementales, docs/DECISIONS.md §1). Si `df` muestra menos
libre que eso, la próxima corrida también va a fallar.

## Mitigation

1. **Eliminar el residuo de la corrida interrumpida** (directorio más nuevo sin
   `manifest.json`, verificado en Diagnosis paso 3, y sin guardian corriendo):
   ```bash
   rm -rf "/ruta/destino/<ID_SIN_MANIFIESTO>"
   ```

2. **Liberación por rotación manual guiada**: borrar los backups MÁS VIEJOS que
   pasen el chequeo de "existe uno más nuevo sano", dejando margen holgado:
   ```bash
   # más viejos primero (ls -1t invierte), salteando el más nuevo
   ls -1tr /ruta/destino/ | head -n -1
   # para cada candidato, confirmar que tiene manifiesto válido antes de borrar:
   python3 -m json.tool "/ruta/destino/<ID>/manifest.json" > /dev/null && \
     rm -rf "/ruta/destino/<ID>"
   ```
   Regla dura: **nunca borrar el backup más nuevo con manifiesto válido**, ni
   aunque el disco esté al 100%. Si no hay más margen que ese, ir a Escalation.

3. **Confirmar margen** para una corrida completa:
   ```bash
   du -shc <rutas-orígenes-del-toml>   # tamaño total a respaldar
   df -h /ruta/destino                  # libre > tamaño total + margen
   ```

4. **Reanudar:**
   ```bash
   uv run guardian backup
   echo $?   # 0 esperado
   ```
   Si se cortó de nuevo por espacio, repetir desde el paso 1 (el nuevo residuo
   también quedará sin manifiesto).

## Escalation

- El ÚNICO backup del destino es el más nuevo y no hay nada rotable → escalar:
  se necesita ampliar el destino (otro disco/volumen) antes de la próxima corrida;
  borrarlo dejaría al sistema sin backups.
- El destino comparte filesystem con datos vivos y liberar allí no es opción →
  decisión de infraestructura, no de este runbook.
- ENOSPC recurrente cada N días → repensar `keep_last` de la rotación (issue #3)
  o el tamaño de los orígenes; escalar al dueño con los números de Diagnosis.

## Rollback

Los pasos de mitigación borran backups viejos: `rm -rf` no se deshace. El orden
del runbook protege (residuo sin manifiesto primero, backups viejos verificados
después, el más nuevo intocable). Si liberaste de más y el origen está intacto:
`uv run guardian backup` regenera un backup bueno de inmediato. Si el origen
también está dañado y borraste el último backup válido: no hay rollback —
escalación inmediata al dueño.
