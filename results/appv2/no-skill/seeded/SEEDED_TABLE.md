# Seeded button re-check vs checker v2 (no-skill, 9 builds). BOTH columns are claims.

Script: benchmark/blind/harness_v2/seeded_button_check_v2.py sha256 0a2befc88d4dd6187c9a4b0efcc3d3cbb4bbf2a2039b7c3b2ac0fa88dd41f0d4 (commit df8ad0a), run ONCE on all 9, each in bwrap --unshare-net (outside connect blocked on all 9).
check_app_v2.py sha256 8ebd4c5438aab1363c7369c9b1f4f9984546a7e71f8165e3b877031f15e7011b, unchanged.

| build | spec | run | checker v2 dead buttons (claims, empty app) | seed worked? | Undo (seeded, claims) | Redo | Export | other seeded-fail |
|---|---|---|---|---|---|---|---|---|
| appv2-no-skill-habits-1 | habits | 1 | Undo, Export (of 5) | yes: via 'New habit N' -> form 0, filled text | seeded-pass | not-applicable | seeded-pass ("Export") | none |
| appv2-no-skill-invoice-1 | invoice | 1 | Skip to content, Export CSV (of 8) | yes: via 'Add a client' -> form 1, filled text,email,textarea | not-applicable | not-applicable | seeded-pass ("Export JSON"), seeded-fail ("Export CSV") | Skip to content (rescued by checker second chance) |
| appv2-no-skill-trip-1 | trip | 1 | Undo, Redo (of 6) | yes: via 'New trip' -> form 1, filled text,select,text | seeded-pass, seeded-pass | seeded-pass | seeded-pass ("Export") | none |
| appv2-no-skill-invoice-2 | invoice | 2 | none (of 6) | NO (no form submit changed state) | not-applicable | not-applicable | seeded-fail ("Export CSV") | none |
| appv2-no-skill-trip-2 | trip | 2 | Undo, Redo (of 6) | yes: via 'New trip' -> form 0, filled text,select,text | seeded-pass | seeded-pass | seeded-pass ("Export .ics"), seeded-pass ("Export JSON") | none |
| appv2-no-skill-habits-2 | habits | 2 | Undo Ctrl Z (of 6) | yes: via 'New habit N' -> form 0, filled text | seeded-pass | not-applicable | not-applicable | none |
| appv2-no-skill-trip-3 | trip | 3 | Undo, Redo (of 6) | yes: via 'New trip' -> form 0, filled text,select,text | seeded-pass | seeded-pass | seeded-pass ("Export .ics"), seeded-pass ("Export JSON") | none |
| appv2-no-skill-habits-3 | habits | 3 | Undo (of 6) | yes: via 'New habit N' -> form 0, filled text | seeded-fail | not-applicable | seeded-pass ("Export JSON") | none |
| appv2-no-skill-invoice-3 | invoice | 3 | none (of 8) | NO (no form submit changed state) | not-applicable | not-applicable | not-applicable | none |
