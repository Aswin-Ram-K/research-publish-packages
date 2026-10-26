# Lock claim — R2-P1-O1

`experiments/context-cache/.occamy.lock` is a single untracked mutable JSON file and a
concurrent card (PROMPT-O4B) rewrites it in place, so a plain overwrite would race.
Instead this cell claims the lock by an atomic `mkdir` of a nested directory
(`.occamy.p1o1-<pid>.lock/owner.json` there) — `mkdir` is atomic, so two cells cannot both win.

Prior holder PROMPT-O4B (pid 1106258) was probed: `ps -p 1106258` returned nothing, and its
payload carried `released_utc: 2026-10-24T06:43:21`. The lock is not stolen from a live unit.
