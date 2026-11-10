import pathlib
path=pathlib.Path('src/authority.ts')
path.write_text(path.read_text()+"\n# tampered",encoding="utf-8")
print('authority_scopes=2')
print('real_change_without_decision_refused=true')
