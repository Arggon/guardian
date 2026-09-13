# Runbook: rotación con backup corrupto

La rotación (o un humano revisando) detecta que un backup viejo tiene el
`manifest.json` inválido o archivos que no coinciden con sus hashes. Qué acotar,
qué borrar con seguridad y qué NUNCA borrar.

## Trigger

- La rotación (issue #3, keep-last-N) encuentra un directorio viejo sin
  `manifest.json` o con JSON inválido.
- `guardian verify` (issue #2, planificado) reporta hash mismatch en un backup viejo.
- Auditoría manual con `sha256sum` contra un manifiesto da fallos en un backup antiguo.

## Diagnosis

```bash
# 1. Inventariar el destino: backups, tamaños y presencia de manifiesto
for d in /ruta/destino/*/; do
  printf '%s  %s  manifiesto:%s\n' "$(basename "$d")" \
    "$(du -sh "$d" | cut -f1)" \
    "$([ -f "$d/manifest.json" ] && echo sí || echo 'NO — incompleto')"
done

# 2. Validar el manifiesto del backup sospechado
python3 -m json.tool "/ruta/destino/<ID>/manifest.json" > /dev/null; echo "exit=$?"

# 3. Si el manifiesto es válido, auditar hashes del backup sospechado
#    (hoy, manual: guardian verify no existe todavía)
cd "/ruta/destino/<ID>" && python3 -c "
import json,hashlib,pathlib
m=json.load(open('manifest.json'))
for s in m['sources']:
    for f in s['files']:
        h=hashlib.sha256(pathlib.Path(f['destination']).read_bytes()).hexdigest()
        if h!=f['sha256']: print('MISMATCH', f['destination'])
"
```

Interpretación: sin manifiesto = corrida interrumpida (invariante 1 de
docs/FORMAT.md). Con manifiesto pero mismatches = corrupción en disco posterior
a la copia (la copia se verificó contra el origen al momento del backup).

## Mitigation

1. **Acotar: verificar que existe un backup MÁS NUEVO sano antes de borrar nada.**
   ```bash
   ls -1t /ruta/destino/ | head -5
   # repetir el chequeo de manifiesto + hashes (pasos 2-3 de Diagnosis) sobre
   # el backup más nuevo: debe estar OK
   ```

2. **Seguro borrar:** el backup corrupto, SOLO si (a) tiene timestamp más viejo
   que al menos un backup verificado OK, y (b) su manifiesto es inválido o sus
   hashes fallan:
   ```bash
   rm -rf "/ruta/destino/<ID_CORRUPTO>"
   ```

3. **Nunca borrar:**
   - El backup **más nuevo** del destino, corrupto o no: es el único que cubre el
     estado actual del origen. Un backup nuevo con manifiesto ausente es una
     corrida interrumpida — ver `partial-backup.md`, no se rota a mano a ciegas.
   - Directorios **sin manifiesto** que sean MÁS NUEVOS que el último backup sano:
     pueden estar en corrida ahora mismo (chequear con `pgrep -af guardian`).
   - Cualquier directorio cuyo `manifest.json` no puedas leer/parsear: tratarlo
     con el paso 3 de Diagnosis antes de decidir.

4. **Re-lanzar rotación** para que el keep-last-N quede consistente (hoy, manual:
   no hay subcomando `guardian rotate`; el plan es `uv run guardian rotate`).
   Alternativa manual: repetir la limpieza guiada de este runbook hasta que
   `ls -1t /ruta/destino/ | wc -l` sea `keep_last + backups sanos retenidos`.

## Escalation

- El backup corrupto es el MÁS NUEVO → no borrar, escalar: puede indicar fallo de
  hardware del destino (la corrupción posterior a la copia no la detecta el
  pipeline en tiempo real).
- Varios backups con mismatches simultáneos → patrón de corrupción de disco/RAM:
  escalar antes de borrar nada, prioridad a mover los backups sanos a otro medio.
- Duda razonable sobre si un directorio es una corrida en curso → esperar y
  re-chequear; no operar bajo duda.

## Rollback

`rm -rf` no es reversible. La mitigación de este runbook es deliberadamente de un
solo sentido, por eso el paso 1 exige un backup más nuevo verificado ANTES de
borrar. No hay rollback post-borrado: la protección es el orden de los pasos.
Si borraste de más y el origen todavía está intacto: correr `uv run guardian
backup` inmediatamente para regenerar un backup bueno.
