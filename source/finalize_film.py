"""Join and independently verify the six completed native P5 camera shots.

Refuses missing/incomplete clips, wrong dimensions, wrong frame counts, missing
render reports, or repeated raw frames. No substitute media is searched for.
"""
from __future__ import annotations
import argparse
import hashlib
import json
import shutil
import subprocess
import sys
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SHOT_NAMES = [
    '01-Reveal', '02-Pick-transfer-return', '03-Precision-grip',
    '04-Compact-elbow', '05-Exploded-architecture', '06-Reassembly-hero',
]
DURATIONS = [3, 10, 4, 3, 5, 3]
FPS = 24
WIDTH, HEIGHT = 1920, 1080
EXPECTED_SOURCE = '48b3dcf993f78a9e1f386c8458644bb5829d627c895b88e58e616ae14aa565a0'

def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open('rb') as f:
        for data in iter(lambda: f.read(1024 * 1024), b''):
            h.update(data)
    return h.hexdigest()

def command(args: list[str], timeout: int = 180) -> str:
    p = subprocess.run(args, text=True, capture_output=True, timeout=timeout)
    if p.returncode:
        raise RuntimeError(f'Command failed ({p.returncode}): {args!r}\n{p.stderr[-5000:]}')
    return p.stdout

def probe(path: Path) -> dict:
    return json.loads(command(['ffprobe', '-v', 'error', '-show_streams',
                              '-show_format', '-of', 'json', str(path)]))

def inspect_clips() -> tuple[list[Path], list[dict]]:
    clips, reports = [], []
    geometry = ROOT / 'assets/design.json'
    if sha256(geometry) != EXPECTED_SOURCE:
        raise RuntimeError('The compact P5 canonical geometry was changed.')
    for i, (name, duration) in enumerate(zip(SHOT_NAMES, DURATIONS), 1):
        clip = ROOT / 'shots' / (name + '.mp4')
        evidence = ROOT / 'reports' / f'shot-{i:02}.json'
        if not clip.is_file() or not evidence.is_file():
            raise FileNotFoundError(f'Incomplete shot {i}: {clip} / {evidence}')
        report = json.loads(evidence.read_text())
        frames = report.get('frames', [])
        if report.get('resolution') != [WIDTH, HEIGHT] or report.get('fps') != FPS:
            raise ValueError(f'Wrong rendering specification in {evidence}')
        hashes = [x['rgb_sha256'] for x in frames]
        if len(frames) != duration * FPS or len(set(hashes)) != len(hashes):
            raise ValueError(f'Missing or repeated raw frames in {evidence}')
        info = probe(clip)
        stream = next(s for s in info['streams'] if s['codec_type'] == 'video')
        if (stream['width'], stream['height']) != (WIDTH, HEIGHT):
            raise ValueError(f'Wrong encoded resolution: {clip}')
        if stream['avg_frame_rate'] != f'{FPS}/1':
            raise ValueError(f'Wrong encoded frame rate: {clip}')
        if abs(float(info['format']['duration']) - duration) > .01:
            raise ValueError(f'Incomplete encoded duration: {clip}')
        clips.append(clip)
        reports.append({
            'shot': i, 'file': clip.name, 'duration_s': duration,
            'raw_rendered_frames': len(frames), 'distinct_raw_frames': len(set(hashes)),
            'clip_sha256': sha256(clip), 'render_report_sha256': sha256(evidence),
        })
    return clips, reports

def package(output: Path, verification_path: Path, movie: Path) -> Path:
    archive = output / 'ARX6-P5-Cinematic-Source.zip'
    members: dict[str, Path] = {}
    source_files = [
        'native_film.py', 'geometry.py', 'build_meshes.py', 'capture.mjs',
        'reference.mjs', 'capture-model.xml', 'capture-parameters.json',
        'finalize_film.py', 'inspect_capture.py',
    ]
    for name in source_files:
        f = ROOT / 'source' / name
        if f.is_file():
            members['ARX6-P5-Cinematic/source/' + name] = f
    for folder in ['source/runtime', 'licenses', 'assets/meshes']:
        for f in (ROOT / folder).rglob('*'):
            if f.is_file() and f.suffix.lower() not in {'.ttf', '.otf', '.woff', '.woff2'}:
                members['ARX6-P5-Cinematic/' + f.relative_to(ROOT).as_posix()] = f
    for name in ['design.json', 'mass-properties.json', 'capture.json']:
        f = ROOT / 'assets' / name
        members['ARX6-P5-Cinematic/assets/' + name] = f
    for f in (ROOT / 'reports').glob('shot-*.json'):
        members['ARX6-P5-Cinematic/reports/' + f.name] = f
    for name in ['native-mesh-build.json', 'capture-review.json', 'production-source-hashes.json']:
        f = ROOT / 'reports' / name
        if f.is_file():
            members['ARX6-P5-Cinematic/reports/' + name] = f
    members['ARX6-P5-Cinematic/README.md'] = ROOT / 'PACKAGE-NOTES.md'
    members['ARX6-P5-Cinematic/PACKAGE-NOTES.md'] = ROOT / 'PACKAGE-NOTES.md'
    members['ARX6-P5-Cinematic/requirements.txt'] = ROOT / 'requirements.txt'
    members['ARX6-P5-Cinematic/reports/video-verification.json'] = verification_path
    for name in ['chapters.ffmetadata', 'decoded-frames.framemd5']:
        members['ARX6-P5-Cinematic/reports/' + name] = ROOT / 'reports' / name
    manifest = {name: sha256(path) for name, path in sorted(members.items())}
    with zipfile.ZipFile(archive, 'w', zipfile.ZIP_DEFLATED, compresslevel=6) as z:
        for name, path in sorted(members.items()):
            z.write(path, name)
        z.writestr('MANIFEST-SHA256.json', json.dumps(manifest, indent=2) + '\n')
    with zipfile.ZipFile(archive) as z:
        if z.testzip() is not None:
            raise RuntimeError('ZIP CRC check failed')
        for name, digest in manifest.items():
            if hashlib.sha256(z.read(name)).hexdigest() != digest:
                raise RuntimeError(f'ZIP content verification failed: {name}')
    (output / 'ARX6-P5-Cinematic-Source-Verification.json').write_text(json.dumps({
        'archive': archive.name, 'sha256': sha256(archive),
        'member_hashes_verified': len(manifest), 'zip_crc_passed': True,
        'font_files_distributed': False, 'video_file': movie.name,
    }, indent=2) + '\n')
    return archive

def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--output-directory', type=Path, default=ROOT / 'delivery')
    args = ap.parse_args()
    output = args.output_directory.resolve()
    output.mkdir(parents=True, exist_ok=True)
    clips, source_reports = inspect_clips()
    concat = ROOT / 'reports/shots.ffconcat'
    concat.write_text('ffconcat version 1.0\n' + ''.join(
        "file '" + str(f).replace("'", "'\\''") + "'\n" for f in clips))
    chapters = ROOT / 'reports/chapters.ffmetadata'
    lines = [';FFMETADATA1', 'title=ARX / 6 — Compact P5 cinematic action film']
    t = 0
    for name, duration in zip(SHOT_NAMES, DURATIONS):
        lines += ['[CHAPTER]', 'TIMEBASE=1/1000', f'START={t * 1000}',
                  f'END={(t + duration) * 1000}', 'title=' + name[3:].replace('-', ' ')]
        t += duration
    chapters.write_text('\n'.join(lines) + '\n')
    movie = output / 'ARX6-P5-Cinematic-Action.mp4'
    command(['ffmpeg', '-y', '-v', 'error', '-f', 'concat', '-safe', '0',
             '-i', str(concat), '-i', str(chapters), '-map', '0:v:0',
             '-map_metadata', '1', '-map_chapters', '1', '-c:v', 'copy',
             '-movflags', '+faststart', str(movie)])
    # An actual independent full decode, not a container-only metadata check.
    decoded = command(['ffmpeg', '-v', 'error', '-i', str(movie),
                       '-map', '0:v:0', '-f', 'framemd5', '-'])
    (ROOT / 'reports/decoded-frames.framemd5').write_text(decoded)
    rows = [r for r in decoded.splitlines() if r and not r.startswith('#')]
    hashes = [r.rsplit(',', 1)[-1].strip() for r in rows]
    expected_frames = sum(DURATIONS) * FPS
    if len(hashes) != expected_frames or len(set(hashes)) != expected_frames:
        raise RuntimeError(f'Unexpected final frame coverage: {len(hashes)} / {len(set(hashes))}')
    info = probe(movie)
    stream = next(s for s in info['streams'] if s['codec_type'] == 'video')
    verification = {
        'movie': movie.name, 'width': stream['width'], 'height': stream['height'],
        'fps': stream['avg_frame_rate'], 'duration_s': float(info['format']['duration']),
        'decoded_frames': len(hashes), 'distinct_decoded_frames': len(set(hashes)),
        'full_decode_passed': True, 'sha256': sha256(movie), 'size_bytes': movie.stat().st_size,
        'chapters': len(DURATIONS), 'canonical_geometry_sha256': EXPECTED_SOURCE,
        'modeled_part_instances': 278, 'native_render_triangles': 778046,
        'rendering': 'Native CAD tessellation with VTK PBR / software EGL; not the earlier single-pass CSG shader',
        'motion': 'Fresh P5-based computed-torque / contact reconstruction, not original 28-scenario engineering validation',
        'explosion': 'Inspection presentation offsets; not a physical disassembly simulation',
        'audio': 'None', 'generative_images_used': False, 'video_frame_interpolation_used': False,
        'source_shots': source_reports,
    }
    vp = output / 'ARX6-P5-Cinematic-Verification.json'
    vp.write_text(json.dumps(verification, indent=2) + '\n')
    shutil.copyfile(ROOT / 'PACKAGE-NOTES.md', output / 'ARX6-P5-Cinematic-Notes.md')
    poster = output / 'ARX6-P5-Cinematic-Poster.jpg'
    command(['ffmpeg', '-y', '-v', 'error', '-ss', '1.5', '-i', str(movie),
             '-frames:v', '1', '-q:v', '2', '-update', '1', str(poster)])
    archive = package(output, vp, movie)
    print(json.dumps({'movie': str(movie), 'source': str(archive),
                      'verification': str(vp), 'metadata': verification}, indent=2))

if __name__ == '__main__':
    main()
