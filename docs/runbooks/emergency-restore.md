# Runbook: restore de emergencia

Origen perdido o corrupto (borrado por accidente, disco dañado, ransomware):
recuperar los datos desde el último backup bueno de guardian.

## Trigger

- Una carpeta origen (`sources[]` del `guardian.toml`) fue borrada, vaciada o corrompida.
- Sospecha de corrupción en el origen (archivos que no abren, tamaños en cero).
- Necesidad de recuperar UNA versión anterior de archivos (no la actual).

## Diagnosis

Confirmar cuál es el último backup VÁLIDO. Invariante (docs/FORMAT.md #1): un
backup sin `manifest.json` es incompleto/interrumpido — no sirve para restaurar.

```bash
# 1. Listar backups por fecha (el destino es `destination` del guardian.toml)
ls -1t /ruta/destino/

# 2. Tomar el más nuevo y verificar que tenga manifiesto válido
B=/ruta/destino/$(ls -1t /ruta/destino/ | head -1)
python3 -m json.tool "$B/manifest.json" > /dev/null && echo "manifiesto OK: $B"

# 3. Verificar qué contiene (carpetas origen y cantidad de archivos)
python3 -c "import json;m=json.load(open('$B/manifest.json'));print(*[(s['root'],len(s['files'])) for s in m['sources']],sep='\n')"
```

Si el más nuevo no tiene manifiesto (corrida interrumpida), bajar al siguiente:
```bash
ls -1t /ruta/destino/ | sed -n 2p
```

## Mitigation

Pasos individuales, copy-pasteables. `<ORIGEN>` es la ruta absoluta de la carpeta
origen dañada; ajustar `<B>` al backup elegido en Diagnosis.

1. **Congelar el área dañada: no escribir en el origen.** Si el disco está vivo,
   montarlo read-only o dejar de usarlo antes de tocar nada.

2. **Verificar la integridad del backup ANTES de restaurar** (hoy, manual:
   `guardian verify` está planificado, issue #2):
   ```bash
   cd "$B" && python3 -c "
   import json,hashlib,pathlib
   m=json.load(open('manifest.json'))
   for s in m['sources']:
       for f in s['files']:
           h=hashlib.sha256(pathlib.Path(f['destination']).read_bytes()).hexdigest()
           print('OK ' if h==f['sha256'] else 'MISMATCH ', f['destination'])
   " | grep -v '^OK ' ; echo "exit=$?"
   ```
   Sin output de `MISMATCH` = backup íntegro. Si hay mismatches, elegir otro backup.

3. **Restaurar la carpeta origen completa:**
   ```bash
   ORIG_NAME=$(basename "<ORIGEN>")
   mv "<ORIGEN>" "<ORIGEN>.dañado.$(date +%Y%m%d-%H%M%S)"   # no borrar lo dañado todavía
   cp -a "$B/$ORIG_NAME" "<ORIGEN>"
   ```

4. **Verificar la restauración contra el manifiesto** (hoy, manual: re-correr
   backup y comparar `sha256sum` a mano). Verificación con sha256sum de sistema,
   adaptando el manifiesto:
   ```bash
   cd "$B" && python3 -c "
   import json;m=json.load(open('manifest.json'))
   for s in m['sources']:
       if s['root'].endswith('$(basename <ORIGEN>)'):
           [print(f\"{f['sha256']}  {s['root']}/{f['path']}\") for f in s['files']]
   " | sed "s#$(basename <ORIGEN>)#$ORIG_NAME#" > /tmp/restore.sha256
   cd / && sha256sum -c /tmp/restore.sha256 --quiet && echo "RESTAURACIÓN ÍNTEGRA"
   ```

5. **Re-lanzar el pipeline:** correr `uv run guardian backup` para volver a tener
   un backup fresco de los datos restaurados.

## Escalation

- Ningún backup pasa la verificación de hashes → no restaurar nada: escalar al
  dueño del sistema antes de borrar el `<ORIGEN>.dañado.*`.
- El origen dañado y TODOS los backups comparten el mismo disco que falló →
  escalar: se necesita el destino en otro dispositivo antes de seguir.
- Restauración selectiva de archivos dentro de árboles grandes o conflictos de
  permisos raros → humano al mando.

## Rollback

La mitigación no destruye nada: el origen dañado queda en `<ORIGEN>.dañado.<ts>`.

```bash
rm -rf "<ORIGEN>"
mv "<ORIGEN>.dañado.<ts>" "<ORIGEN>"
```

Sólo eliminar `<ORIGEN>.dañado.<ts>` cuando el usuario confirme que los datos
restaurados son los correctos.
