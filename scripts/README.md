# Cache Management Scripts

Utility scripts for managing JutulGPT's documentation cache.

## Quick Reference

```bash
# Check cache status
uv run scripts/manage_cache.py status

# Force update from GitHub
uv run scripts/manage_cache.py update

# Clear all caches
uv run scripts/manage_cache.py clear

# Re-extract function docs
uv run scripts/manage_cache.py extract
```

## How It Works

JutulGPT automatically downloads documentation from GitHub on first run and caches it in `.cache/`:
- **Documentation & Examples**: Fetched from [JutulDarcy.jl](https://github.com/sintefmath/JutulDarcy.jl)
- **Function Docs**: Extracted using Julia's `@doc` macro
- **Auto-Update**: Checks for new commits/versions automatically
- **Offline-Ready**: Works without network after initial download

## Troubleshooting

**Cache issues?** Clear and re-download:
```bash
uv run scripts/manage_cache.py clear
uv run scripts/manage_cache.py update
```
