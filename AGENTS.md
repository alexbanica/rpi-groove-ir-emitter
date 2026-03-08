# AGENTS

## Project implementation status

The codebase is aligned to a DDD + Onion style layout.

### Layers

- `domains`: entities, DTOs, and interfaces.
- `applications`: business services and orchestration.
- `infrastructures`: pigpio and JSON adapters.
- `controllers`: CLI request/response and coordination.
- `shared/constants`: centralized static strings and defaults.

### Invariants

The following behavior must remain stable unless a new approved spec changes it:

1. CLI flags and defaults:
   - positional `file` required
   - `--out-gpio=12`
   - `--carrier=38000`
   - `--repeat=1`
2. Input JSON shape compatibility:
   - `{ "gpio_in": <int>, "pulse_us": <list[int]> }`
3. Playback behavior:
   - mark/space handling and carrier-wave generation semantics remain equivalent.
4. pigpio connection failure exits with status code `2`.

### Testing

- Unit tests live in `tests/`.
- Run with:

```bash
python -m unittest discover -s tests -p 'test_*.py'
```

### API docs scope

No HTTP API exists. OpenAPI and `.http` artifacts are not applicable for the current project scope.
