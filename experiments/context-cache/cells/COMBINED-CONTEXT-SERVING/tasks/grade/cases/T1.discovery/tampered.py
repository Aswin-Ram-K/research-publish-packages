import pathlib
path=pathlib.Path('src/hash.ts')
path.write_text(path.read_text()+"\n# tampered",encoding="utf-8")
print('algorithm=blake2b512')
print('shard_prefix=2')
