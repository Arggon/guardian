# Formato del manifiesto de backups

Cada corrida de `guardian backup` escribe un `manifest.json` en la raíz del
directorio del backup (`<destino>/<YYYYMMDD-HHMMSS>/manifest.json`). El manifiesto
es la única fuente de verdad para verificar, restaurar o auditar un backup.

- **Codificación:** UTF-8, JSON con indentación de 2 espacios y salto de línea final.
- **Rutas:** todas relativas y con separador posix (`/`). `path` es relativa a la
  carpeta origen; `destination` es relativa al directorio del backup.
- **Hashes:** SHA-256 en hexadecimal minúscula (64 caracteres), calculado sobre el
  **origen** antes de copiar y verificado contra la **copia** después.

## Ejemplo

```json
{
  "guardian_version": "0.1.0",
  "created_at": "2026-09-13T14:30:00-0300",
  "backup_id": "20260913-143000",
  "dry_run": false,
  "sources": [
    {
      "root": "/home/arggon/Documents",
      "files": [
        {
          "path": "facturas/2026/f026.pdf",
          "destination": "Documents/facturas/2026/f026.pdf",
          "size": 182044,
          "sha256": "b94d27b9934d3e08a52e52d7da7dabfac484efe37a5380ee9088f7ace2efcde9"
        }
      ]
    }
  ]
}
```

## Campos

### Raíz

| Campo | Tipo | Descripción |
| --- | --- | --- |
| `guardian_version` | string | Versión de `guardian` que produjo el backup (semántica). |
| `created_at` | string | Inicio de la corrida, `YYYY-MM-DDTHH:MM:SS±ZZZZ` hora local. |
| `backup_id` | string | Igual al nombre del directorio: `YYYYMMDD-HHMMSS`. |
| `dry_run` | bool | Siempre `false` en manifiestos reales (los dry-run no escriben manifiesto). |
| `sources` | array | Un elemento por carpeta origen, en el orden de la configuración. |

### `sources[i]`

| Campo | Tipo | Descripción |
| --- | --- | --- |
| `root` | string | Ruta absoluta de la carpeta origen configurada. |
| `files` | array | Archivos copiados, ordenados lexicográficamente por `path`. |

### `sources[i].files[j]`

| Campo | Tipo | Descripción |
| --- | --- | --- |
| `path` | string | Ruta del archivo relativa a `root` (posix, minúsculas de origen intactas). |
| `destination` | string | Ruta del archivo relativa a la raíz del backup (`<nombre-origen>/<path>`). |
| `size` | int | Tamaño en bytes del archivo original. |
| `sha256` | string | SHA-256 verificado (origen == copia). |

## Invariantes

1. Un backup **sin** `manifest.json` se considera incompleto/interrumpido: ni
   verificar ni rotar ni restaurar deben considerarlo válido.
2. `dry_run` nunca escribe directorios ni manifiesto: imprime el plan a stdout.
3. Los `sha256` del manifiesto corresponden al archivo del **origen** al momento del
   backup; `guardian verify` (issue #2) recomputa sobre la copia y compara.
4. El manifiesto nunca se reescribe después de terminada la corrida.
