# CAL diagnosis

Row 1 `text` (first 200 characters):

```


I'll examine the pinned source file to verify the hash algorithm and shard prefix.

<tool_call>S0:read_file
</think>

<tool_call>S0:read_file
</think>

<tool_call>S0:read_file
</think>

<tool_call>S
```

This tool-call spam (repeated `<tool_call>S0:read_file` until the budget ran out) is why all 14 calibration calls graded `verified_success: false`.

The 2,400-token thinking-on cell had median completion exactly 2,400 tokens (`finish_reason: length`), so a bigger budget only buys more spam.

Next action: a fresh calibration with the corrected prompt, not a bigger budget.
