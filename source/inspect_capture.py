"""Inspect capture provenance and data integrity, not robot safety or qualification."""
from pathlib import Path
import hashlib
import json
import xml.etree.ElementTree as ET
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
trace = json.loads((ROOT / 'assets/capture.json').read_text())
frames = np.asarray(trace['frames'], dtype=float)
bodies = np.asarray(trace['bodies'], dtype=float)
xml = ET.parse(ROOT / 'source/capture-model.xml').getroot()
masses = json.loads((ROOT / 'assets/mass-properties.json').read_text())
comparison = []
for name, facts in masses.items():
    if name == 'fixed':
        continue
    element = xml.find(f".//body[@name='{name}']/inertial")
    if element is None:
        raise RuntimeError('Missing body inertia: ' + name)
    actual_mass = float(element.attrib['mass'])
    actual_com = np.fromstring(element.attrib['pos'], sep=' ')
    actual_inertia = np.fromstring(element.attrib['fullinertia'], sep=' ')
    exact = (actual_mass == facts['mass_kg'] and
             np.array_equal(actual_com, facts['com_m']) and
             np.array_equal(actual_inertia, facts['fullinertia_mujoco_kg_m2']))
    if not exact:
        raise RuntimeError('Changed supplied body inertia: ' + name)
    comparison.append({'body': name, 'mass_kg': actual_mass,
                       'mass_com_full_inertia_equal_to_P5': exact})
rotation = bodies[:, :, 3:].reshape(-1, 3, 3)
orthogonal_error = np.max(np.abs(rotation @ np.swapaxes(rotation, 1, 2) - np.eye(3)))
minimum_determinant = np.linalg.det(rotation).min()
if frames.shape != (1201, 30) or bodies.shape != (1201, 10, 12):
    raise RuntimeError('Unexpected trace schema')
if not np.isfinite(frames).all() or not np.isfinite(bodies).all():
    raise RuntimeError('Nonfinite state')
if np.any(np.diff(frames[:, 0]) <= 0) or frames[-1, 0] != 10.0:
    raise RuntimeError('Nonmonotonic or incomplete trace')
puck = xml.find(".//body[@name='puck']")
free_joint = puck is not None and (puck.find('freejoint') is not None or
                                  puck.find("joint[@type='free']") is not None)
if not free_joint or xml.find('.//equality/weld') is not None:
    raise RuntimeError('Puck is not an independent non-welded body')
observations = []
for t, target in [(1.5, None), (3.6, [.330, .028, .124]),
                  (6.5, None), (9.9, [.290, .028, -.124])]:
    i = np.argmin(abs(frames[:, 0] - t))
    p = bodies[i, -1, :3]
    observation = {'time_s': float(frames[i, 0]), 'puck_position_m': p.tolist()}
    if target is not None:
        observation['distance_to_nominal_station_mm'] = float(1000 * np.linalg.norm(p - target))
    observations.append(observation)
report = {
    'scope': 'Integrity and provenance inspection of the new rendering capture; not the old engineering validation or hardware qualification.',
    'frame_samples': len(frames), 'capture_duration_s': float(frames[-1, 0]),
    'finite_states': True, 'monotonic_timestamps': True,
    'max_rotation_orthogonality_error': float(orthogonal_error),
    'minimum_rotation_determinant': float(minimum_determinant),
    'independent_puck_freejoint': free_joint, 'weld_constraints': 0,
    'original_moving_body_inertias': comparison, 'observations': observations,
    'capture_sha256': hashlib.sha256((ROOT / 'assets/capture.json').read_bytes()).hexdigest(),
    'controller': 'Reconstructed computed-torque / PD, not original motor electrical or safety firmware.',
}
(ROOT / 'reports/capture-review.json').write_text(json.dumps(report, indent=2) + '\n')
print(json.dumps(report, indent=2))
