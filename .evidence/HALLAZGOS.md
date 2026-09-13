# Hallazgos sobre ArggonManager (2026-09-13)

Evidence cruda de la sesión de adopción de guardian. Los detalles y
reproducciones están en el reporte final de la sesión.

1. BUG (anti-robo no aplicado por CLI): `arggon update --steal` por CLI nunca es
   negado a un agente — cli/src/cli.ts:616 no pasa `agent:true` y rules.ts solo
   lo exige para MCP (mcp-server.ts:289). Evidencia: 08-steal-via-cli-NO-refused.json
   (ok:true, claimed_at refrescado). Vía MCP el tool arggon_update ni siquiera
   expone `steal` (protección por ausencia, no por regla).
2. ASPEREZA (claims ciegos al checkout primario): start --worktree commitea el
   claim solo en el branch nuevo (cli/src/start.ts:431-448). Desde main la task
   se ve todo/claimed_at null → `list --stale` desde main no ve el abandono
   (07-stale-empty-from-main.json); sí se ve desde el worktree.
3. ASPEREZA (adopt requiere epic preexistente): el error ADOPT_FAILED guía
   ("create epic --parent <initiative>") pero el skill no documenta el prerrequisito.
4. BUG/ASPEREZA (adopt --ack no protege del re-run de init): init --full
   regeneró silenciosamente (updated[]) los 5 docs llenados + ackeados. La
   protección modified[] solo cubre edits POST-ack. Evidencias 09/10/11.
5. ASPEREZA (--backup agresivo): con --backup se archivan Y regeneran TODOS los
   modified[], no solo el editado a mano (11-init-rerun-caso3-backup.json).
6. BUG (cleanup parcial): cleanup --prune removió el worktree pero falló
   borrando el branch (git branch -d vs upstream divergente) → CLEANUP_FAILED
   con estado parcial y worktree_path huérfano en el item (13-cleanup-fallo-branch.json).
   Causa raíz adicional: el push final del subagente nunca llegó al remoto.
7. ASPEREZA (report --trend ignora stories): trend.ts:139-146 solo cuenta
   task/bug; en un proyecto story-driven el trend da "(none)" (14-report-trend.json).
8. NOTA (update no auto-commitea): por diseño (skill lista create/comment/adopt/
   cleanup), los flips done requieren commit manual del item.
9. NOTA (create sin --labels ni --depends-on): se hacen post-creación via update.
10. NOTA (report agrupa stories como contenedores sin hojas): las stories hechas
    (done) son invisibles en el rollup del report.
