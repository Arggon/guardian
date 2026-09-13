# Decisiones de diseño (informal)

Registro informal, sin ceremonia: qué decidimos, por qué, y qué descartamos.
Orden cronológico.

## 1. No usamos restic (ni borg, ni deja-dup)

**Fecha:** 2026-09-13 · **Estado:** decidido

`restic` hace backups incrementales deduplicados y cifrados, y es una herramienta
excelente. No la usamos igual:

- El objetivo de `guardian` es tener copias **legibles sin herramientas extra**:
  entrar a la carpeta del backup con el file manager y abrir los archivos. Un
  repositorio restic es opaco sin el binario (y sin recordar la contraseña).
- Quería una herramienta mía, entendible línea por línea: si el backup falla, quiero
  saber exactamente dónde y por qué, no depurar un formato ajeno.
- restic no verifica contra el origen: verifica su propio repositorio. El chequeo que
  me importa es "la copia de hoy es bit a bit igual al archivo original", y eso lo
  hago con SHA-256 a ambos lados de la copia.

**Costo aceptado:** más espacio (sin deduplicación ni incrementales) y backups más
lentos para árboles grandes. Para carpetas personales de decenas de GB, es un precio
razonable por transparencia.

## 2. Timestamps por corrida: cada backup es inmutable y autocontenido

**Fecha:** 2026-09-13 · **Estado:** decidido

Cada corrida escribe a `<destino>/<YYYYMMDD-HHMMSS>/` y nunca toca backups anteriores.

- Alternativa descartada: un único directorio espejo estilo `rsync -a --delete`. Es
  compacto pero destruye historia: un archivo borrado del origen desaparece del
  backup en la próxima corrida, y un backup a mitad de corrida deja el espejo
  inconsistente.
- Con timestamps, restaurar es `cp -r`, auditar es leer un `manifest.json`, y un
  backup interrumpido queda claramente incompleto (sin manifiesto) sin contaminar
  nada previo.

## 3. Rotación simple keep-last-N (no GFS, no incremental)

**Fecha:** 2026-09-13 · **Estado:** decidido (implementación pendiente, issue #3)

La rotación va a ser: ordenar los directorios con timestamp y borrar los más viejos
dejando `keep_last`. Nada más.

- Abuela-GFS (diario/semanal/mensual) es óptima en espacio pero difícil de razonar
  ("¿por qué desapareció el backup del martes?") y difícil de testear. La rotación
  simple es predecible: si `keep_last = 5`, siempre hay exactamente 5.
- La decisión #2 hace que la rotación sea segura: borrar un directorio entero con
  timestamp no puede romper otros backups porque no hay dependencias entre ellos
  (a diferencia de incrementales encadenados).

## 4. Solo stdlib en runtime; pytest y ruff como únicas deps de dev

**Fecha:** 2026-09-13 · **Estado:** decidido

`shutil.copy2` preserva mtime/permisos, `tomllib` (3.11+) lee el TOML, `hashlib`
hashea en streaming, `argparse` arma el CLI. No hay nada que justifique una
dependencia de runtime en una herramienta que tiene que arrancar incluso con el
sistema medio roto. Las únicas dependencias son de desarrollo (`pytest`, `ruff`).

## 5. Verificación con SHA-256 duplicado (origen y copia), no checksum al copiar

**Fecha:** 2026-09-13 · **Estado:** decidido

Hash del origen **antes** de copiar y hash de la copia **después**: si la RAM, el
cable SATA o el driver del disco corrompieron la transferencia, el `HashMismatch`
lo detecta y la copia se descarta. Un checksum calculado "durante" la copia solo
validaría el stream en memoria, no el archivo asentado en el destino.
