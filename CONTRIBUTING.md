# Development

Run:

```bash
PYTHONPATH=src pytest -q
```

Keep the replay engine independent of model clients. New computer surfaces should implement the `ComputerSurface` protocol rather than leaking surface-specific APIs into artifact/replay code.
