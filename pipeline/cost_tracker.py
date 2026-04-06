"""Cost tracker para jobs del pipeline Humara.

Registra cada llamada a Anthropic API con input/output tokens y calcula el costo
en USD. Persiste a un JSON local por job y opcionalmente sincroniza a Supabase.

Uso:
    from cost_tracker import CostTracker

    tracker = CostTracker(job_id, job_dir)
    response = client.messages.create(...)
    tracker.record(step="translate", attempt=1, model=MODEL, response=response, duration_ms=1234)
    ...
    tracker.sync_to_supabase()  # opcional, al final del job
    total = tracker.total_usd()
"""

import json
import os
import time
from datetime import datetime
from typing import Optional

import requests


# Precios por millón de tokens (USD). Actualizar cuando Anthropic cambie pricing.
# Fuente: https://www.anthropic.com/pricing (marzo 2026)
_OPUS_PRICING = {
    "input": 15.00,
    "output": 75.00,
    "cache_read": 1.50,
    "cache_write": 18.75,
}

_SONNET_PRICING = {
    "input": 3.00,
    "output": 15.00,
    "cache_read": 0.30,
    "cache_write": 3.75,
}

_HAIKU_PRICING = {
    "input": 1.00,
    "output": 5.00,
    "cache_read": 0.10,
    "cache_write": 1.25,
}

PRICING = {
    # Claude 4.6 (latest)
    "claude-opus-4-6": _OPUS_PRICING,
    "claude-opus-4-6[1m]": _OPUS_PRICING,
    "claude-sonnet-4-6": _SONNET_PRICING,
    # Claude 4.5
    "claude-haiku-4-5-20251001": _HAIKU_PRICING,
    # Claude 4 (legacy, still used by pipeline defaults)
    "claude-opus-4-20250514": _OPUS_PRICING,
    "claude-sonnet-4-20250514": _SONNET_PRICING,
    # Genericos por prefijo (match por startswith en _pricing_for)
    "claude-opus": _OPUS_PRICING,
    "claude-sonnet": _SONNET_PRICING,
    "claude-haiku": _HAIKU_PRICING,
    # Fallback: si algún ID no matchea nada, asumir Sonnet (no subestimar)
    "_default": _SONNET_PRICING,
}


def _pricing_for(model: str) -> dict:
    """Devuelve los precios para un modelo. Busca por prefijo si no hay match exacto."""
    if model in PRICING:
        return PRICING[model]
    # Match por prefijo: "claude-opus-4-6-20260101" → "claude-opus-4-6"
    for key in PRICING:
        if key != "_default" and model.startswith(key):
            return PRICING[key]
    return PRICING["_default"]


def calculate_cost(model: str, input_tokens: int, output_tokens: int,
                   cache_read_tokens: int = 0, cache_write_tokens: int = 0) -> float:
    """Calcula el costo en USD de una llamada."""
    p = _pricing_for(model)
    cost = (
        (input_tokens / 1_000_000) * p["input"]
        + (output_tokens / 1_000_000) * p["output"]
        + (cache_read_tokens / 1_000_000) * p["cache_read"]
        + (cache_write_tokens / 1_000_000) * p["cache_write"]
    )
    return round(cost, 6)


class CostTracker:
    """Registra llamadas LLM de un job y acumula el costo total."""

    def __init__(self, job_id: str, job_dir: str):
        self.job_id = job_id
        self.job_dir = job_dir
        self.calls: list[dict] = []
        self.costs_path = os.path.join(job_dir, "costs.json")
        # Cargar si ya existe (permite retomar jobs)
        if os.path.exists(self.costs_path):
            try:
                with open(self.costs_path) as f:
                    data = json.load(f)
                    self.calls = data.get("calls", [])
            except Exception:
                pass

    def record(
        self,
        step: str,
        attempt: int,
        model: str,
        response=None,
        input_tokens: Optional[int] = None,
        output_tokens: Optional[int] = None,
        cache_read_tokens: int = 0,
        cache_write_tokens: int = 0,
        duration_ms: Optional[int] = None,
    ) -> dict:
        """Registra una llamada. Podés pasarle el response de Anthropic
        directamente o los tokens manualmente.

        Args:
            step: 'translate', 'review', 'autofix', 'ocr', 'retranslate', etc.
            attempt: número de intento (para el loop de auto-corrección)
            model: ID del modelo usado
            response: objeto Message de anthropic (se extrae usage automático)
            input_tokens, output_tokens: manual override si no se pasa response
            duration_ms: tiempo de la llamada, opcional
        """
        if response is not None and hasattr(response, "usage"):
            u = response.usage
            input_tokens = getattr(u, "input_tokens", 0) or 0
            output_tokens = getattr(u, "output_tokens", 0) or 0
            cache_read_tokens = getattr(u, "cache_read_input_tokens", 0) or 0
            cache_write_tokens = getattr(u, "cache_creation_input_tokens", 0) or 0

        if input_tokens is None or output_tokens is None:
            raise ValueError("Se requiere response o (input_tokens, output_tokens)")

        cost = calculate_cost(
            model, input_tokens, output_tokens, cache_read_tokens, cache_write_tokens
        )

        entry = {
            "job_id": self.job_id,
            "step": step,
            "attempt": attempt,
            "model": model,
            "input_tokens": input_tokens,
            "output_tokens": output_tokens,
            "cache_read_tokens": cache_read_tokens,
            "cache_write_tokens": cache_write_tokens,
            "cost_usd": cost,
            "duration_ms": duration_ms,
            "created_at": datetime.utcnow().isoformat() + "Z",
        }
        self.calls.append(entry)
        self._save_local()
        return entry

    def _save_local(self):
        os.makedirs(self.job_dir, exist_ok=True)
        payload = {
            "job_id": self.job_id,
            "total_usd": self.total_usd(),
            "total_input_tokens": sum(c["input_tokens"] for c in self.calls),
            "total_output_tokens": sum(c["output_tokens"] for c in self.calls),
            "num_calls": len(self.calls),
            "updated_at": datetime.utcnow().isoformat() + "Z",
            "calls": self.calls,
        }
        with open(self.costs_path, "w") as f:
            json.dump(payload, f, indent=2)

    def total_usd(self) -> float:
        return round(sum(c["cost_usd"] for c in self.calls), 6)

    def total_tokens(self) -> tuple[int, int]:
        inp = sum(c["input_tokens"] for c in self.calls)
        out = sum(c["output_tokens"] for c in self.calls)
        return inp, out

    def cost_by_step(self) -> dict:
        by_step = {}
        for c in self.calls:
            by_step.setdefault(c["step"], 0.0)
            by_step[c["step"]] += c["cost_usd"]
        return {k: round(v, 6) for k, v in by_step.items()}

    def cost_by_attempt(self) -> dict:
        by_attempt = {}
        for c in self.calls:
            key = f"attempt_{c['attempt']}"
            by_attempt.setdefault(key, 0.0)
            by_attempt[key] += c["cost_usd"]
        return {k: round(v, 6) for k, v in by_attempt.items()}

    def sync_to_supabase(self) -> bool:
        """Sincroniza todas las llamadas a la tabla job_llm_calls de Supabase.
        Devuelve True si tuvo éxito, False si hubo error."""
        supabase_url = os.environ.get("SUPABASE_URL")
        supabase_key = os.environ.get("SUPABASE_SERVICE_ROLE_KEY")
        if not supabase_url or not supabase_key:
            print("  [cost_tracker] SUPABASE env vars not set, skipping sync")
            return False

        if not self.calls:
            return True

        headers = {
            "apikey": supabase_key,
            "Authorization": f"Bearer {supabase_key}",
            "Content-Type": "application/json",
            "Prefer": "return=minimal",
        }

        # Enviar en batch
        try:
            r = requests.post(
                f"{supabase_url}/rest/v1/job_llm_calls",
                headers=headers,
                json=self.calls,
                timeout=30,
            )
            if r.status_code in (200, 201, 204):
                print(f"  [cost_tracker] Synced {len(self.calls)} calls to Supabase")
                return True
            else:
                print(f"  [cost_tracker] Sync failed: {r.status_code} {r.text[:200]}")
                return False
        except Exception as e:
            print(f"  [cost_tracker] Sync error: {e}")
            return False


class StopWatch:
    """Context manager para medir duración en ms. Uso:

        with StopWatch() as sw:
            response = client.messages.create(...)
        tracker.record(..., duration_ms=sw.elapsed_ms)
    """

    def __enter__(self):
        self.start = time.monotonic()
        return self

    def __exit__(self, *args):
        self.elapsed_ms = int((time.monotonic() - self.start) * 1000)
