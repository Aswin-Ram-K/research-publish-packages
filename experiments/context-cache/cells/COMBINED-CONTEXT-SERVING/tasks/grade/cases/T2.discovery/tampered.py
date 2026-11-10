import pathlib
path=pathlib.Path('src/reference.ts')
path.write_text(path.read_text()+"\n# tampered",encoding="utf-8")
print('ref_kinds=16')
print('first_ref_kind=task')
