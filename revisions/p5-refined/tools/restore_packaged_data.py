"""Restore losslessly packaged data, checking every byte identity first."""
from pathlib import Path
import argparse, gzip, hashlib, json, os
ROOT=Path(__file__).resolve().parents[1]
def digest(data):return hashlib.sha256(data).hexdigest()
def safe(relative):
    p=(ROOT/relative).resolve()
    if not p.is_relative_to(ROOT):raise ValueError("Path escapes revision root")
    return p
def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--verify-only',action='store_true')
    args=parser.parse_args()
    manifest=json.loads((ROOT/'PACKAGED-DATA.json').read_text())
    for item in manifest['files']:
        pieces=[]
        for part in item['parts']:
            data=safe(part['path']).read_bytes()
            if len(data)!=part['bytes'] or digest(data)!=part['sha256']:raise ValueError('Part identity mismatch: '+part['path'])
            pieces.append(data)
        compressed=b''.join(pieces)
        if len(compressed)!=item['gzip_bytes'] or digest(compressed)!=item['gzip_sha256']:raise ValueError('Compressed identity mismatch')
        data=gzip.decompress(compressed)
        if len(data)!=item['bytes'] or digest(data)!=item['sha256']:raise ValueError('Restored identity mismatch')
        target=safe(item['path'])
        if not args.verify_only:
            if target.exists():
                if target.is_symlink() or digest(target.read_bytes())!=item['sha256']:raise ValueError('Refusing to overwrite an existing different output: '+item['path'])
            else:
                target.parent.mkdir(parents=True,exist_ok=True)
                temp=target.with_name(target.name+'.restore-temp')
                with temp.open('xb') as f:f.write(data)
                os.replace(temp,target)
        print(('verified ' if args.verify_only else 'restored ')+item['path']+' '+item['sha256'])
if __name__=='__main__':main()
