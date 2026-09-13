# Runbook: backup parcial (exit 4 planificado)

Una corrida terminó con orígenes fallidos: leer el manifiesto estado/error por
origen, decidir si re-correr, y qué hacer con el directorio parcial.

## Trigger

- `uv run guardian backup` devuelve exit 4 (planificado: checker-core / partial
  report; exit codes actuales del código: 0 ok, 2 config, 3 integridad).
- Cron/timer reporta un backup con salida `BACKUP` pero código distinto de 0.
- El resumen de stdout menciona orígenes con menos archivos de lo esperado.

Nota: hoy el manifiesto no tiene campo `status`/`error` por origen — los runbooks
lo asumen para cuando el exit 4 aterrice. Mientras tanto, el "estado por origen"
se infiere comparando `files[]` del manifiesto contra el origen real (Mitigation 1).

## Diagnosis

```bash
# 1. Estado por origen: qué copió cada uno
B=/ruta/destino/<ID_DEL_EXIT_4>
python3 -c "
import json;m=json.load(open('$B/manifest.json'))
for s in m['sources']:
    print(f\"{s['root']}: {len(s['files'])} archivo(s)\")
"

# 2. Comparar contra el origen real (conteo de archivos regulares)
for root in $(python3 -c "
import json;m=json.load(open('$B/manifest.json'))
[print(s['root']) for s in m['sources']]
"); do echo "$root: $(find "$root" -type f ! -type l | wc -l) en origen"; done

# 3. Identificar el origen que falló: el que tiene 0 archivos copiados o un
#    conteo muy menor al real. Causas típicas: carpeta renombrada/movida,
#    permisos, origen en volumen no montado.
ls -ld "<ROOT_SOSPECHOSO>" && find "<ROOT_SOSPECHOSO>" -maxdepth 1 | head
```

## Mitigation

1. **Corregir la causa raíz del origen fallido** (montar el volumen, restaurar
   permisos, corregir la ruta en `guardian.toml`). Si fue la ruta, editar el TOML
   y validar:
   ```bash
   $EDITOR guardian.toml && uv run guardian backup --dry-run   # plan sin escribir
   ```

2. **Re-correr el backup completo** una vez corregida la causa:
   ```bash
   uv run guardian backup; echo "exit=$?"   # 0 esperado
   ```
   El re-run escribe un directorio de timestamp NUEVO y nunca pisa el parcial
   (invariante de ARCHITECTURE.md: cada corrida es inmutable y autocontenida).

3. **El directorio parcial: NUNCA rotarlo a mano a ciegas.** Tiene manifiesto
   válido (la corrida terminó ordenadamente) pero contenido incompleto: si lo
   rotás y un día nadie tiene otro backup, no vas a saber qué falta. Tratamiento
   según caso:
   - Hay un backup posterior exit 0 → el parcial se puede borrar como cualquier
     backup viejo (ver `corrupt-rotation.md`), anotando por qué era parcial:
     ```bash
     rm -rf "$B"   # solo tras verificar que el backup nuevo está OK
     ```
   - Es el ÚNICO backup → NO borrarlo: es parcial pero contiene datos verificados
     con SHA-256 (cada archivo del manifiesto pasó el doble hash). Escalar y
     re-correr cuando la causa raíz esté corregida.

4. **Documentar** en el item tracker (o comentario) qué origen falló, por qué y
   cómo se corrigió — los parciales recurrentes del mismo origen indican un
   problema estructural, filear task.

## Escalation

- Exit 4 recurrente en el mismo origen tras "corregirlo" → escalar: la causa raíz
  no es la que se creía.
- El parcial es el único backup y el origen se daña antes de poder re-correr →
  escalación inmediata al dueño: restaurar solo los archivos que estén en el
  manifiesto del parcial (ver `emergency-restore.md`, con la advertencia de que
  NADIE sabe qué archivos faltan salvo comparar contra el origen si sobrevivió).
- Exit 4 con TODOS los orígenes con 0 archivos → patrón sistémico (destino mal
  montado, permisos globales): escalar antes de re-correr a ciegas.

## Rollback

La mitigación no altera backups existentes: corrige config/entorno y re-corre.
Rollback posible: revertir el cambio de `guardian.toml`
(`git diff guardian.toml` si está versionado) y re-validar con `--dry-run`. El
directorio parcial borrado no se recupera — por eso el paso 3 exige un
backup posterior OK antes del `rm -rf`.
