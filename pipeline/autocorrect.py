"""Loop de auto-corrección para jobs del pipeline Humara.

Después del primer pase de review, si el score quedó por debajo del target,
este módulo itera el review sobre su propio output (reviewed.json ya trae las
correcciones aplicadas) hasta que:
  - el score alcanza el target (default 0.90), o
  - se agotan los max_attempts, o
  - se supera el budget de costo en USD.

Si termina sin alcanzar el target, devuelve los datos del último intento y
un payload de warning para que notify.py lo incluya en el mail.

Uso desde run_job.py:

    from autocorrect import auto_correct_loop, LoopResult

    result: LoopResult = auto_correct_loop(
        reviewed_data=first_review,
        output_dir=job_dir,
        doc_type=doc_type,
        cost_tracker=tracker,
        target_score=0.90,
        max_attempts=3,
        cost_budget_usd=2.00,
    )
"""

import json
import os
from dataclasses import dataclass, field
from typing import Optional

from review_v2 import review_document


@dataclass
class LoopResult:
    """Resultado del loop de auto-corrección."""

    final_reviewed: dict               # reviewed.json del último intento
    final_report: dict                 # review_report.json del último intento
    attempts_used: int                 # cuántas iteraciones se corrieron
    cost_used_usd: float               # costo acumulado del loop (sin contar el review inicial)
    reached_target: bool               # si se alcanzó el target_score
    stopped_by: str                    # 'target_reached' | 'max_attempts' | 'cost_budget' | 'no_improvement'
    score_history: list[float] = field(default_factory=list)
    warning_payload: Optional[dict] = None  # para notify.py cuando no se alcanzó el target


def _load_report(path: str) -> dict:
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def _build_warning(final_report: dict, attempts_used: int, max_attempts: int,
                   cost_used_usd: float, cost_budget_usd: float, stopped_by: str,
                   score_history: list[float]) -> dict:
    """Arma el payload de warning para notify.py cuando no se alcanza el target."""
    issues = final_report.get("issues", [])
    # Agrupar por página, quedarse con mayores y críticos
    unresolved = [i for i in issues if i.get("severity") in ("critico", "mayor")]

    by_page: dict[int, list[dict]] = {}
    for iss in unresolved:
        page = iss.get("page", 0)
        by_page.setdefault(page, []).append(iss)

    # Top 10 items ordenados por severidad (críticos primero) y página
    flat = []
    for sev in ("critico", "mayor"):
        for iss in unresolved:
            if iss.get("severity") == sev:
                flat.append(iss)
    top_items = flat[:10]

    return {
        "score": final_report.get("score", 0.0),
        "attempts_used": attempts_used,
        "max_attempts": max_attempts,
        "cost_used_usd": round(cost_used_usd, 4),
        "cost_budget_usd": cost_budget_usd,
        "stopped_by": stopped_by,
        "score_history": score_history,
        "issues_count": len(unresolved),
        "issues_by_page": {
            str(p): len(items) for p, items in sorted(by_page.items())
        },
        "top_unresolved": [
            {
                "page": i.get("page"),
                "severity": i.get("severity"),
                "dimension": i.get("dimension"),
                "explanation": i.get("explanation", "")[:200],
            }
            for i in top_items
        ],
    }


def auto_correct_loop(
    reviewed_data: dict,
    output_dir: str,
    doc_type: str = "general",
    model: str = "claude-sonnet-4-20250514",
    cost_tracker=None,
    target_score: float = 0.90,
    max_attempts: int = 3,
    cost_budget_usd: float = 2.00,
) -> LoopResult:
    """Corre el loop de auto-corrección.

    El primer pase de review ya se ejecutó antes de llamar a esta función.
    `reviewed_data` es el resultado de ese primer pase (el que tiene texto ya
    corregido). `output_dir` debe contener `review_report.json` (el reporte del
    primer pase).

    Args:
        reviewed_data: dict con 'pages' y 'metadata', output del primer review.
        output_dir: carpeta del job (para leer review_report.json y guardar outputs).
        doc_type: tipo de documento (pasa al prompt del reviewer).
        model: modelo de Claude para review (Opus).
        cost_tracker: CostTracker para registrar tokens y costo.
        target_score: score mínimo a alcanzar (default 0.90).
        max_attempts: máximo de iteraciones (sin contar el review inicial).
        cost_budget_usd: tope de costo acumulado en USD para el loop entero.

    Returns:
        LoopResult con el estado final y el warning_payload (o None si se
        alcanzó el target).
    """
    # Leer el reporte del primer pase
    first_report_path = os.path.join(output_dir, "review_report.json")
    first_report = _load_report(first_report_path)
    initial_score = first_report.get("score", 0.0)
    score_history = [initial_score]

    print(f"\n  ═══ AUTO-CORRECT LOOP ═══")
    print(f"  Initial score: {initial_score:.3f} (target: {target_score:.2f})")

    # Caso feliz: el primer pase ya llegó al target
    if initial_score >= target_score:
        print(f"  ✓ Target already reached on first review, no loop needed")
        return LoopResult(
            final_reviewed=reviewed_data,
            final_report=first_report,
            attempts_used=1,
            cost_used_usd=0.0,
            reached_target=True,
            stopped_by="target_reached",
            score_history=score_history,
        )

    # Snapshot del costo del cost_tracker ANTES del loop (para aislar el costo del loop)
    cost_before_loop = cost_tracker.total_usd() if cost_tracker else 0.0

    current_reviewed = reviewed_data
    current_report = first_report
    reached = False
    stopped_by = "max_attempts"

    for attempt in range(2, max_attempts + 2):  # attempts 2, 3, 4...
        current_cost = (cost_tracker.total_usd() - cost_before_loop) if cost_tracker else 0.0
        if current_cost >= cost_budget_usd:
            print(f"  ✗ Cost budget reached (${current_cost:.4f} / ${cost_budget_usd:.2f})")
            stopped_by = "cost_budget"
            break

        print(f"\n  → Attempt {attempt}/{max_attempts + 1} (cost used so far: ${current_cost:.4f})")
        # Re-review sobre el output del review anterior (que ya tiene correcciones aplicadas)
        current_reviewed = review_document(
            translated_data=current_reviewed,
            output_dir=output_dir,
            doc_type=doc_type,
            model=model,
            cost_tracker=cost_tracker,
            attempt=attempt,
        )
        # Cargar el nuevo report que review_document acaba de guardar
        new_report_path = os.path.join(output_dir, f"review_report_attempt_{attempt}.json")
        current_report = _load_report(new_report_path)
        new_score = current_report.get("score", 0.0)
        score_history.append(new_score)

        print(f"  Score: {score_history[-2]:.3f} → {new_score:.3f}")

        if new_score >= target_score:
            reached = True
            stopped_by = "target_reached"
            print(f"  ✓ Target reached on attempt {attempt}")
            break

        # Si no mejoramos nada en esta iteración, no tiene sentido seguir gastando
        if attempt >= 3 and new_score <= score_history[-2]:
            print(f"  ✗ Score did not improve ({score_history[-2]:.3f} → {new_score:.3f}), stopping")
            stopped_by = "no_improvement"
            break

    attempts_used = len(score_history)  # incluye el pase inicial
    cost_used = (cost_tracker.total_usd() - cost_before_loop) if cost_tracker else 0.0

    warning_payload = None
    if not reached:
        warning_payload = _build_warning(
            final_report=current_report,
            attempts_used=attempts_used,
            max_attempts=max_attempts + 1,
            cost_used_usd=cost_used,
            cost_budget_usd=cost_budget_usd,
            stopped_by=stopped_by,
            score_history=[round(s, 3) for s in score_history],
        )

    print(f"\n  ═══ LOOP RESULT ═══")
    print(f"  Attempts used: {attempts_used}")
    print(f"  Loop cost: ${cost_used:.4f}")
    print(f"  Score history: {[f'{s:.3f}' for s in score_history]}")
    print(f"  Reached target: {'YES' if reached else 'NO'}")
    print(f"  Stopped by: {stopped_by}")

    return LoopResult(
        final_reviewed=current_reviewed,
        final_report=current_report,
        attempts_used=attempts_used,
        cost_used_usd=round(cost_used, 6),
        reached_target=reached,
        stopped_by=stopped_by,
        score_history=[round(s, 3) for s in score_history],
        warning_payload=warning_payload,
    )
