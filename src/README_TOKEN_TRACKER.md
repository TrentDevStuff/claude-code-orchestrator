# TokenTracker - Token Usage and Cost Tracking

## Overview

The `TokenTracker` class provides token usage parsing and cost calculation for Claude API calls. It integrates seamlessly with the `BudgetManager` to enable comprehensive usage tracking and budget management.

## Features

- **Parse Claude CLI JSON Output**: Extract token usage from API responses
- **Multi-Model Cost Calculation**: Support for Haiku, Sonnet, and Opus pricing
- **High-Precision Arithmetic**: Uses `Decimal` for accurate cost calculations
- **Model Tier Detection**: Automatically identifies model from full model names
- **Comprehensive Error Handling**: Validates JSON structure and catches missing fields
- **BudgetManager Integration**: Direct compatibility with budget tracking system

## Model Pricing (per 1K tokens)

| Model  | Input Cost | Output Cost |
|--------|-----------|-------------|
| Haiku  | $0.00025  | $0.00125    |
| Sonnet | $0.003    | $0.015      |
| Opus   | $0.015    | $0.075      |

## Usage

### Basic Parsing

```python
from src.token_tracker import TokenTracker
import json

# Parse Claude CLI output
claude_output = json.dumps({
    "usage": {
        "input_tokens": 1500,
        "output_tokens": 800
    },
    "model": "claude-3-sonnet-20240229"
})

result = TokenTracker.parse_claude_output(claude_output)
# {
#     "input_tokens": 1500,
#     "output_tokens": 800,
#     "total_tokens": 2300,
#     "model": "claude-3-sonnet-20240229",
#     "model_tier": "sonnet",
#     "cost_usd": 0.0165
# }
```

### Direct Cost Calculation

```python
from src.token_tracker import TokenTracker

# Calculate cost for specific token counts
cost = TokenTracker.calculate_cost(
    input_tokens=10000,
    output_tokens=5000,
    model="sonnet"
)
# Returns: Decimal('0.105')
```

### Integration with BudgetManager

```python
from src.token_tracker import TokenTracker
from src.budget_manager import BudgetManager
import json

# Initialize
budget_manager = BudgetManager("project.db")

# Parse API response
result = TokenTracker.parse_claude_output(api_response_json)

# Track usage
await budget_manager.track_usage(
    project_id="my-project",
    model=result["model_tier"],
    tokens=result["total_tokens"],
    cost=result["cost_usd"]
)
```

## API Reference

### `parse_claude_output(json_str: str) -> Dict[str, Any]`

Parses Claude CLI JSON output to extract token usage and calculate cost.

**Parameters:**
- `json_str` (str): JSON string from Claude CLI output

**Returns:**
- Dictionary containing:
  - `input_tokens` (int): Number of input tokens
  - `output_tokens` (int): Number of output tokens
  - `total_tokens` (int): Sum of input and output tokens
  - `model` (str): Full model name from API response
  - `model_tier` (str): Model tier ("haiku", "sonnet", or "opus")
  - `cost_usd` (float): Calculated cost in USD

**Raises:**
- `ValueError`: If JSON is invalid or malformed
- `KeyError`: If required fields are missing from JSON

**Expected JSON Format:**
```json
{
    "usage": {
        "input_tokens": 1000,
        "output_tokens": 500
    },
    "model": "claude-3-haiku-20240307"
}
```

### `calculate_cost(input_tokens: int, output_tokens: int, model: str) -> Decimal`

Calculates the cost in USD for token usage based on model pricing.

**Parameters:**
- `input_tokens` (int): Number of input tokens consumed
- `output_tokens` (int): Number of output tokens generated
- `model` (str): Model tier ("haiku", "sonnet", or "opus") - case insensitive

**Returns:**
- `Decimal`: Cost in USD with 6 decimal place precision

**Raises:**
- `ValueError`: If model name is not recognized

**Example:**
```python
cost = TokenTracker.calculate_cost(1000, 500, "haiku")
# Returns: Decimal('0.000875')
```

## Error Handling

The TokenTracker provides robust error handling:

### Invalid JSON
```python
try:
    result = TokenTracker.parse_claude_output("{invalid json}")
except ValueError as e:
    print(f"Invalid JSON: {e}")
```

### Missing Fields
```python
try:
    result = TokenTracker.parse_claude_output('{"usage": {}}')
except KeyError as e:
    print(f"Missing required field: {e}")
```

### Unknown Model
```python
try:
    cost = TokenTracker.calculate_cost(1000, 500, "unknown-model")
except ValueError as e:
    print(f"Unknown model: {e}")
```

## Cost Calculation Details

Token costs are calculated using the formula:

```
input_cost = (input_tokens / 1000) × input_price_per_1k
output_cost = (output_tokens / 1000) × output_price_per_1k
total_cost = input_cost + output_cost
```

Results are rounded to 6 decimal places for USD cent precision.

### Example Calculation (Sonnet)

```
Input:  2,000 tokens @ $0.003 per 1K = $0.006
Output: 1,000 tokens @ $0.015 per 1K = $0.015
Total:  3,000 tokens               = $0.021
```

## Testing

Comprehensive test suite with 26 tests covering:

- ✅ Valid parsing for all model tiers
- ✅ Cost calculations with various token counts
- ✅ Invalid JSON handling
- ✅ Missing field detection
- ✅ Unknown model handling
- ✅ Edge cases (zero tokens, large counts)
- ✅ Precision and rounding
- ✅ BudgetManager integration compatibility

Run tests:
```bash
python -m pytest tests/test_token_tracker.py -v
```

## Examples

See `examples/token_tracker_usage.py` for comprehensive examples including:

1. Basic token parsing and cost calculation
2. Cost comparison across models
3. Integration with BudgetManager
4. Budget checking before API calls

Run examples:
```bash
PYTHONPATH=/path/to/claude-code-api-service python examples/token_tracker_usage.py
```

## Design Decisions

### Why Decimal for Cost Calculations?

Using Python's `Decimal` type ensures:
- Exact arithmetic without floating-point errors
- Precise financial calculations
- Consistent rounding behavior
- No accumulation of rounding errors

### Why Separate Model Tier from Full Model Name?

The API returns full model names like "claude-3-haiku-20240307", but pricing is based on model tiers ("haiku", "sonnet", "opus"). Separating these allows:
- Future-proof handling of new model versions
- Simpler pricing lookups
- Clear distinction between API naming and pricing tiers

### Why Class Methods Instead of Instance Methods?

`TokenTracker` uses class methods because:
- No instance state is required
- Can be used without instantiation
- Clear that operations are stateless
- Simplifies usage in integration code

## Future Enhancements

Potential improvements for future iterations:

1. **Streaming Token Tracking**: Support for streaming responses
2. **Batch Processing**: Optimize parsing of multiple API responses
3. **Custom Pricing**: Allow override of default pricing
4. **Token Estimation**: Predict token counts before API calls
5. **Usage Analytics**: Built-in reporting and analytics
6. **Rate Limiting**: Integration with rate limit tracking

## Integration Checklist

When integrating TokenTracker into your application:

- [ ] Parse all API responses through `parse_claude_output()`
- [ ] Pass parsed results to `BudgetManager.track_usage()`
- [ ] Check budgets before making API calls
- [ ] Handle `ValueError` for invalid JSON
- [ ] Handle `KeyError` for missing fields
- [ ] Log token usage for monitoring
- [ ] Set up alerts for budget thresholds

## Related Components

- **BudgetManager** (`src/budget_manager.py`): Tracks usage and enforces budgets
- **ModelRouter** (`src/model_router.py`): Routes requests to appropriate models
- **WorkerPool** (`src/worker_pool.py`): Manages concurrent API workers

## License

Part of the Claude Code API Service project.
