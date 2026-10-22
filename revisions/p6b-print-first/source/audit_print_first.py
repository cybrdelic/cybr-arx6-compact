"""Classify the actual P6-A inventory against a print-first manufacturing target.
The register is a design disposition, not evidence that each target is qualified.
Run: python source/audit_print_first.py
"""
from pathlib import Path
import json, hashlib, collections, math, html
ROOT=Path(__file__).resolve().parents[1]

def disposition(p):
    n=p['name'].lower(); i=p['id']; material=p['material']
    if 'compliant_seat' in n or i in [242,249,251]:
        return ('PRINT_TPU','Flexible contact/retention component. Print TPU rather than forcing rigid PETG to act as rubber.',
                'Requalify friction, grip force, compression set, wall thickness, and wear; do not reuse silicone/rubber contact constants.')
    if i==255:
        return ('EXTERNAL_TEST_PAYLOAD','This is the handled workpiece, not a robot fabrication part.',
                'A printed dummy is allowed only with explicit payload mass/inertia and surface-friction replacement in the test.')
    if p.get('category') in ['shoulder_spacer','retaining_washer'] or ('shoulder_spacer' in n or 'retaining_washer' in n):
        return ('METAL_COMPRESSION_HARDWARE','Small metal preload member, not an excuse to retain the surrounding structure in metal.',
                'Recalculate length and bearing area against the redesigned printed host; supplier/physical fit validation required.')
    if any(x in n for x in ['_screw','_bolt','bench_m8','case_mount_m4','cover_m2p5','clamp_m','clamp_nut','_nut_']):
        return ('METAL_FASTENER','Purchased screw/nut retains clamp load and provides serviceable threads.',
                'Use through-bolts, compression sleeves and captive metal nuts/inserts; no tightening torque is released.')
    if 'csd_' in n:
        return ('PRINTED_REDUCTION_REDESIGN','Replace the purchased reduction architecture with printed gears/carriers if the new drive meets its declared performance target.',
                'Not an STL of a sealed supplier envelope. Design gear teeth, bearings, backlash, efficiency, load capacity and life; do not inherit the CSD torque rating.')
    if i in [237,245,252]:
        return ('PRINTED_GEAR_REDESIGN','Printed pinion/racks are in scope; the 0.3-module metal tooth set is not accepted as a final FDM design.',
                'Coarser teeth, wider faces and larger roots require coordinated bridge/jaw/reduction redesign and wear/force tests.')
    if i in [243,244,253,254]:
        return ('PRINT_PETG_WEAR_TRIAL','Print replaceable guide bushings as wear-test candidates.',
                'Measure bore clearance, breakaway friction, running friction, wear and creep; metal guide rods stay separate.')
    if i in [239,240,233] or 'input_bearing_' in n or i in [232,238]:
        return ('METAL_PRECISION_WEAR_HARDWARE','Rolling bearing, ground sliding rod, or precision shaft/bushing surface.',
                'The carrier around it is a printed-design target. Purchased bearing load/life and wear remain to be established.')
    if 'stepped_rotor_carrier' in n:
        return ('PRINT_HYBRID_HUB_REDESIGN','Printed carrier/hub around a small metal shaft or journal is in scope.',
                'Rework torque transfer, concentricity, retention, balance and temperature. Existing all-metal carrier is a reference, not a final exception.')
    if 'encoder_magnet_target' in n or 'encoder_board' in n or 'motor_stator' in n or 'motor_rotor' in n or i==236:
        return ('PURCHASE_ELECTROMAGNETIC_PART','Functional winding, rotor/magnet, sensor/electronics, or complete gripper motor.',
                'Mounts and surrounding housings are printed where qualified; electrical/magnetic material is not replaced by clear plastic.')
    if 'motor_mounting_flange' in n:
        return ('HYBRID_PRINTED_MOUNT_THERMAL_INSERT','A printed load-carrying mount with a localized metal heat-transfer/contact plate is the target.',
                'Not a blanket metal motor mount. Demonstrate motor alignment and heat rejection for the actual duty cycle.')
    if 'spring_applied_brake_stator' in n or 'brake_rotor_and_hub' in n:
        return ('PURCHASE_BRAKE_FUNCTION','Electromagnetic/friction brake function retained as purchased hardware.',
                'The surrounding support is a printed target with temperature and torque checks; no brake certification is transferred.')
    if 'torsion_spring' in n or 'leg_reaction_pin' in n:
        return ('METAL_SPRING_OR_PIN','Spring wire or concentrated reaction pin retains its functional material.',
                'The surrounding enclosure and support are printed targets; retained-energy containment is separately unresolved.')
    if 'reaction_arbor' in n:
        return ('PRINT_HYBRID_HUB_REDESIGN','Printed counterbalance hub around a metal pin/journal is in scope.',
                'Check hub bearing stress, creep, torque transfer and positive spring retention before energizing.')
    if p.get('category')=='revised_cover':
        return ('PRINT_PETG_EXISTING_PROTOTYPE','Already a P6-A PETG cover, retained as a prototype, not the limit of the conversion.',
                'P6-A thermal failures and cover-retention limitations remain open; mating metal hosts are now being redesigned.')
    if any(s in n for s in ['structural_frame','weldment','u_yoke','roll_yoke','bend_frame']):
        return ('PRINT_PETG_STRUCTURE_REDESIGN','Primary load-bearing structure is a print-first target, with ribbed sections and local metal interfaces only.',
                'Rebuild stiffness, connection details, build orientation, creep, modal behavior and assembly clearance; no metal-robot precision claim.')
    if 'structural_heat_spreader_case' in n:
        return ('PRINT_PETG_HOUSING_REDESIGN','Printed structural actuator casing, with separate minimal metal thermal inserts only where justified.',
                'Relocate heat paths, enlarge/rib shell, review bearing load paths, and test duty-cycle temperature; transparent appearance is not a thermal calculation.')
    if 'captured_spring_case' in n or 'spring_cover' in n:
        return ('PRINT_PETG_ENCLOSURE_REDESIGN','Print the enclosure; localized metal capture/reaction members remain separately identified.',
                'No claim of fragment containment or preload tooling. Do not open or operate a loaded spring prototype without a qualified retention scheme.')
    if i in [256,257,258,259]:
        return ('PRINT_PETG_FIXTURE','Print workpiece nests and seats.',
                'Recalculate loaded deflection, friction, wear and attachment; original metal-fixture simulation is not transferred.')
    if material in ['aluminum','steel','polymer','PETG']:
        return ('PRINT_PETG_CUSTOM_REDESIGN','Custom support, adapter, bearing carrier, gripper body or cable-management part is targeted for printing.',
                'Preserve required interfaces while adding section, ribs, bosses and local metal inserts; geometry/strength/thermal/fit checks pending.')
    raise ValueError('Unclassified part: '+p['name'])

def main():
    original=json.loads((ROOT/'inputs/P5-design.json').read_text())['parts']
    p6=json.loads((ROOT/'inputs/P6A-design.json').read_text())
    replacements={p['id']:p for p in p6['replacement_records']}
    records=[]
    for i in range(p6['part_instances']):
        base=original[i] if i<len(original) else {}
        p={**base,**replacements.get(i,{})}
        cat,why,gate=disposition(p)
        records.append({'id':i,'name':p['name'],'body':p['body'],'current_material':p['material'],
                        'target':cat,'reason':why,'release_gate':gate,'status':'TARGET_NOT_QUALIFIED',
                        'original_group':base.get('group','P6 cover mounting hardware')})
    counts=dict(collections.Counter(p['target'] for p in records))
    summary={'inventory_instances':len(records),'target_counts':counts,
             'printed_or_print_redesign_instances':sum(v for k,v in counts.items() if k.startswith('PRINT') or k.startswith('HYBRID_PRINT')),
             'scope':'Every P6-A instance explicitly reviewed. Targets do not imply completed/qualified CAD conversions.',
             'policy':'No custom part is retained in metal merely because it carries load. Printed structural and transmission redesigns are in scope.',
             'printer_basis':'Bambu A1; 256 mm nominal cube; fit results use a separate 246 mm per-axis prototype planning envelope with a 5 mm margin.',
             'preserved_source_sha256':{p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in (ROOT/'inputs').glob('*.json')}}
    (ROOT/'reports/part-register.json').write_text(json.dumps(records,indent=2))
    (ROOT/'reports/audit-summary.json').write_text(json.dumps(summary,indent=2))
    print(json.dumps(summary,indent=2))
if __name__=='__main__':main()
