from pathlib import Path
import hashlib,json
import trimesh
ROOT=Path(__file__).resolve().parents[1]
def main():
    checks=[]
    for f in sorted((ROOT/'stl').glob('*.stl')):
        m=trimesh.load_mesh(f,process=True)
        result={'file':f.name,'watertight':bool(m.is_watertight),'consistent_winding':bool(m.is_winding_consistent),
                'positive_mesh_volume':bool(m.volume>0),'mesh_components':len(m.split(only_watertight=False)),
                'triangles':len(m.faces),'bounds_mm':m.bounds.tolist(),
                'fits_nominal_256mm_cube':bool((m.bounds[0]>=-1e-5).all() and (m.bounds[1]<=256).all()),
                'sha256':hashlib.sha256(f.read_bytes()).hexdigest()}
        if not all([result['watertight'],result['consistent_winding'],result['positive_mesh_volume'],result['fits_nominal_256mm_cube'],result['mesh_components']==1]):
            raise RuntimeError(result)
        checks.append(result)
    register=json.loads((ROOT/'reports/part-register.json').read_text())
    if len(register)!=398 or len({p['id'] for p in register})!=398:raise RuntimeError('Incomplete P6-A audit')
    structural=json.loads((ROOT/'reports/structural-prototypes.json').read_text())
    if any(r['intersection_volume_mm3']>.01 for r in structural['nominal_intersections']):raise RuntimeError('Splice interference')
    screen=json.loads((ROOT/'reports/structural-screen.json').read_text())
    if not all(x['passed'] for x in screen['analytic_code_checks']):raise RuntimeError('Analytic checks')
    r={'scope':'Six geometric test articles. File topology and build envelope checked, not a qualified whole-arm print conversion.',
       'inventory_records_reviewed':len(register),'all_STL_checks_pass':True,'STL_files':checks,
       'nominal_three_piece_splice_intersections_checked':True,
       'new_rigid_body_dynamics_executed':False,'new_whole_arm_FEA_executed':False,
       'new_thermal_validation_executed':False,'qualified_disassembly_sequence':False,'physical_prints_tested':False,
       'no_image_generation':True,'new_whole_arm_render':False}
    (ROOT/'reports/delivery-verification.json').write_text(json.dumps(r,indent=2))
    print('VERIFIED',len(checks),'watertight, single-component, positive-volume STL files;',len(register),'audited part records')
if __name__=='__main__':main()
