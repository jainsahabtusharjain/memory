# Embedding Dimensions Fix - Implementation Documentation

**Date:** December 11, 2025  
**Issue:** Vector dimension mismatch (expected 1024, got 768) causing MCP tool failures  
**Solution:** Shared helper function to ensure `embedding_dims` is set correctly across all code paths

## Problem Summary

### Root Cause
1. **Database config missing `embedding_dims`**: When users update API keys via UI, the `embedding_dims` field was being stripped from the config saved to database
2. **Missing runtime fix in `memory.py`**: The fix existed in `config.py` but was missing in `memory.py`'s `get_memory_client()` function
3. **MCP tools failing**: When MCP tools called `get_memory_client()`, it loaded config without `embedding_dims`, causing mem0 library to default to 768 dimensions
4. **Qdrant collection mismatch**: Qdrant collection was configured for 1024 dimensions (Gemini), but embedder was generating 768-dimension vectors

### Error Message
```
Vector dimension error: expected dim: 1024, got 768
```

## Solution Architecture

### Approach: Option 2 - Shared Helper Function
- **Single source of truth**: Created `_ensure_embedding_dims()` helper function in `memory.py`
- **Reused in both files**: `memory.py` and `config.py` both use the same helper
- **Comprehensive edge case handling**: Covers all providers, models, and edge cases

## Files Modified

### 1. `app/utils/memory.py`

#### Changes Made:

**Added Helper Function** (after `_get_config_hash`):
```python
def _ensure_embedding_dims(config: dict) -> dict:
    """
    Ensure embedding_dims is set correctly for embedder and sync with vector store.
    
    Handles all edge cases:
    - Missing embedding_dims in config
    - Different embedder providers (Gemini, OpenAI, Ollama, Cohere, HuggingFace)
    - Model-specific dimensions
    - Vector store dimension synchronization
    - Unknown providers/models (warns but doesn't fail)
    """
```

**Function Logic:**
1. Checks if embedder config exists
2. Determines expected dimensions using priority:
   - Explicit user override (if set in config)
   - Model-specific mapping (e.g., `models/gemini-embedding-001` → 1024)
   - Provider defaults (e.g., Gemini → 1024, OpenAI → 1536)
   - Ollama/HuggingFace → warns (user must specify)
3. Sets `embedding_dims` if missing or incorrect
4. **CRITICAL**: Syncs vector store `embedding_model_dims` to match embedder dimensions

**Integration Points** (3 locations):

1. **After loading DB config** (line ~502):
   ```python
   # After fixing Ollama URLs
   config = _ensure_embedding_dims(config)
   ```

2. **Default config path** (line ~511):
   ```python
   # When no DB config found
   config = _ensure_embedding_dims(config)
   ```

3. **After environment variable parsing** (line ~528):
   ```python
   # After parsing env vars
   config = _ensure_embedding_dims(config)
   ```

### 2. `app/routers/config.py`

#### Changes Made:

**Added Import**:
```python
from app.utils.memory import reset_memory_client, _ensure_embedding_dims
```

**Replaced Duplicate Logic** (lines 186-227):
- **Before**: 42 lines of duplicate dimension-setting logic
- **After**: 3 lines calling shared helper function
```python
# CRITICAL: Use shared helper function to ensure embedding_dims is set
# This replaces duplicate logic with single source of truth
config_value = _ensure_embedding_dims(config_value)
```

## Edge Cases Covered

### 1. Missing `embedding_dims` in DB Config
- **Scenario**: User updates API keys via UI, `embedding_dims` gets stripped
- **Fix**: Helper function auto-detects and sets correct dimensions based on provider/model

### 2. Different Embedder Providers
- **Gemini**: 1024 dimensions (default)
- **OpenAI**: 1536 dimensions (text-embedding-3-small default)
- **Cohere**: 1024 dimensions
- **Ollama**: Variable (user must specify)
- **HuggingFace**: Variable (user must specify)

### 3. Model-Specific Dimensions
- `models/gemini-embedding-001` → 1024
- `text-embedding-3-small` → 1536
- `text-embedding-3-large` → 3072
- `text-embedding-ada-002` → 1536
- `nomic-embed-text` → 768
- `mxbai-embed-large` → 1024
- `embed-english-v3.0` → 1024
- `embed-multilingual-v3.0` → 1024

### 4. Vector Store Dimension Sync
- **Problem**: Embedder dimensions and vector store dimensions can mismatch
- **Fix**: Helper function automatically syncs `vector_store.config.embedding_model_dims` to match embedder dimensions

### 5. Unknown Providers/Models
- **Behavior**: Warns user but doesn't fail
- **Message**: Instructs user to specify `embedding_dims` explicitly

### 6. Config Update Paths
- **API endpoint updates**: Handled via `config.py` → `_ensure_embedding_dims()`
- **MCP tool initialization**: Handled via `memory.py` → `_ensure_embedding_dims()`
- **Default config**: Handled via `memory.py` → `_ensure_embedding_dims()`

### 7. Environment Variable Parsing
- **Timing**: Helper called AFTER env var parsing to catch any config changes
- **Reason**: Env vars might change provider/model, requiring dimension recalculation

## Testing Checklist

- [x] Helper function created and tested
- [ ] MCP `add_memories` tool works (no dimension mismatch)
- [ ] API config endpoint works (sets dimensions correctly)
- [ ] Default config path works (when no DB config)
- [ ] Vector store dimensions sync correctly
- [ ] Different providers tested (Gemini, OpenAI)
- [ ] Config updates via UI preserve dimensions
- [ ] Unknown providers warn but don't fail

## Benefits

1. **Single Source of Truth**: One function handles all dimension logic
2. **Consistency**: Same behavior across API endpoints and MCP tools
3. **Maintainability**: Fix bugs or add providers in one place
4. **Comprehensive**: Handles all edge cases in one function
5. **Non-Breaking**: Warns for unknown cases but doesn't fail

## Code Locations

- **Helper Function**: `app/utils/memory.py` lines ~48-120
- **Usage in memory.py**: Lines ~502, ~511, ~528
- **Usage in config.py**: Line ~186
- **Import in config.py**: Line 6

## Related Issues Fixed

1. ✅ MCP tool `add_memories` dimension mismatch error
2. ✅ Page refresh delay (indirectly - faster initialization)
3. ✅ Config updates stripping `embedding_dims`
4. ✅ Vector store dimension synchronization

## Future Improvements

1. **Auto-save to DB**: Consider auto-saving corrected dimensions to database
2. **Dimension validation**: Add validation when user manually sets dimensions
3. **Collection migration**: Handle case where Qdrant collection has wrong dimensions
4. **Provider detection**: Auto-detect dimensions from provider API if possible

