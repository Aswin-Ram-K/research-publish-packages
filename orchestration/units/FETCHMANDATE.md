# FETCHMANDATE

Status: done

Fix 1: make_row now persists answer_raw/answer_kind/answer_value/answer_parse_error from grade_v5.parse_answer_contract(content) on every row.
Fix 2: checkpoint_prompt D mandates fetch of each [MASKED <ref>]; retrieval_omitted recorded on D marked turns without fetch.

Live: 10 requests, cap 2678->2688, 10 rows, task_id TX-01, fixture sha 44a1b4356536a0a55757ed2a4c90f5ef7f9d0541836007dc195a50ab3db2ec21.
Turn 5: C answered "ANSWER: NONE"; D answered "ANSWER: NONE"; D did not fetch (fetch_rows null), retrieval_omitted=true; tools_declared=true for D.
