# Runbook: falso verde del hash

Sospecha de que la verificación SHA-256 "pasó" pero la copia está mal. Caso
típico: el origen mutó entre el hash previo a la copia y la lectura de la copia
(hay un proceso escribiendo los datos durante la corrida), o el hash se calculó
sobre datos ya cambiados — la copia es fiel a lo que leyó, pero no a lo que el
usuario cree que respaldó.

## Trigger

- Un archivo restaurado desde un backup "verificado" no abre o difiere de lo
  esperado, pese a que la corrida reportó todos los hashes OK.
- Se sabe que hay procesos escribiendo en los orígenes durante la ventana de
  backup (base de datos viva, sincronización de nube, editor con autosave).
- Auditoría post-incidente: confirmar que un backup dado es confiable.

## Diagnosis

El punto ciego estructural: guardian hashea el origen ANTES de copiar y la copia
DESPUÉS (docs/DECISIONS.md §5). Si el origen cambió entre el hash y la copia,
ambos hashes reflejan contenidos distintos... no: ambos reflejan estados
distintos del origen, y el manifiesto guarda el hash del primer estado. Un falso
verde real ocurre cuando el origen muta ANTES del hash y sigue mutado: la copia
verificada respalda fielmente la versión mutada.

```bash
# 1. Auditar el backup completo con sha256sum de SISTEMA contra el manifiesto
B=/ruta/destino/<ID>
cd "$B" && python3 -c "
import json,hashlib,pathlib
m=json.load(open('manifest.json'))
for s in m['sources']:
    for f in s['files']:
        h=hashlib.sha256(pathlib.Path(f['destination']).read_bytes()).hexdigest()
        print(('OK ' if h==f['sha256'] else 'MISMATCH '), f['destination'])
" | grep -v '^OK '
# Sin output = la copia en disco coincide bit a bit con el manifiesto.

# 2. Comparar tamaños del manifiesto contra la copia (detección barata de trunques)
python3 -c "
import json,pathlib,os
m=json.load(open('$B/manifest.json'))
for s in m['sources']:
    for f in s['files']:
        real=os.path.getsize(f['destination']) if os.path.exists(f['destination']) else -1
        if real!=f['size']: print('SIZE DIFF', f['destination'], f['size'], '->', real)
"

# 3. Comparar el backup contra el ORIGEN actual: diferencias = el origen mutó
#    después del backup (o antes, y el backup capturó otra versión)
ORIG=$(python3 -c "
import json;m=json.load(open('$B/manifest.json'));print(m['sources'][0]['root'])")
NAME=$(basename "$ORIG")
cd "$B/$NAME" && find . -type f -exec sha256sum {} + | sort > /tmp/backup.sha
cd "$ORIG"    && find . -type f -exec sha256sum {} + | sort > /tmp/origen.sha
diff /tmp/backup.sha /tmp/origen.sha | head -20
```

Interpretación: backups íntegros en el paso 1 pero con diffs en el paso 3 NO son
un falso verde: son simplemente una versión anterior de los datos. Falso verde =
el paso 1 falla (la copia no coincide con su propio manifiesto).

## Mitigation

1. **Re-hash posterior de la copia** (Mitigation principal — mismo comando del
   Diagnosis paso 1): re-ejecutar la auditoría completa contra el manifiesto.
   Si da OK, la copia está íntegra respecto de lo que se respaldó.

2. **Re-verificar contra el manifiesto en otro momento** (horas después, tras un
   reboot): descarta corrupción transitoria de memoria/driver que un solo pase
   pudo no ver. Dos pases OK con separación temporal = confianza alta.
   (hoy, manual: re-correr el script; planificado: `uv run guardian verify`
   — issue #2 — hace exactamente esto.)

3. **Cerrar la ventana de mutación**: la prevención es respaldar datos quietos.
   Identificar el proceso escritor y pausarlo durante la corrida:
   ```bash
   # quién escribe en el origen durante el backup
   lsof +D "<ORIGEN>" 2>/dev/null | awk '{print $1, $2}' | sort -u
   ```
   Mover la ventana del timer/cron fuera de los horarios de escritura, o congelar
   el servicio escritor antes de `uv run guardian backup`.

4. **Si el paso 1 da MISMATCH en un backup**: es corrupción real, derivar a
   `corrupt-rotation.md` para el tratamiento (no borrar el más nuevo sin leerlo).

## Escalation

- El paso 1 da mismatches en el backup MÁS NUEVO → escalar (posible hardware
  fallando: RAM, cable, disco del destino; los backups consecutivos pueden estar
  comprometidos).
- El escritor identificado es una base de datos viva → escalar al dueño: backup
  de DB viva requiere snapshot/dump consistente, no copia de archivos; eso es una
  decisión de diseño, no un parche de cron.
- Falsos verdes confirmados en varios backups históricos → escalar: hay que
  re-auditar toda la retención antes de confiar en ella.

## Rollback

Las mitigaciones 1-2 son de solo lectura: no hay nada que deshacer. La pausa del
proceso escritor (paso 3) se revierte reactivando el servicio:
```bash
systemctl start <servicio-escritor>   # o el mecanismo que se haya usado
```
Ningún paso de este runbook modifica backups ni manifiestos (invariante 4 de
docs/FORMAT.md: el manifiesto nunca se reescribe después de la corrida).
