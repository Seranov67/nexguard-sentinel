# Bazantic A/B benchmark — pending real-model run

The 5 September report was generated from simulated responses, including fabricated
example IDs and fixed 1/4 versus 4/4 scores. It is superseded and must not be used as
qualification evidence. The original remains available in Git history.

The runner now calls a real Ollama model with the same task, settings and tools in
both conditions. Only Recipe guidance differs. It records actual tool calls,
responses and structural checks; explanation accuracy needs human transcript review.
Missing API/model services fail explicitly, without synthetic fallback.

```bash
python -m sentinel.bazantic.benchmark_ab --model YOUR_INSTALLED_MODEL
```

Prerequisites: configured model, reachable Evidence API, explicit server demo mode,
and a real persisted incident. Run against a stable incident snapshot. Payment
settlement is not implemented and must not be claimed in the comparison.
