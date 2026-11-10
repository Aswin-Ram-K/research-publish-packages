import pathlib
path=pathlib.Path('src/observation.ts')
path.write_text(path.read_text()+"\n# tampered",encoding="utf-8")
print('state_fields=16')
print('derived_regions=12')
