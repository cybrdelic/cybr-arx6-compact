"""Transparent, rerunnable first-order structural tradeoff screen.
Uniform-section beam surrogates ONLY: not FEM of the complete CAD, TCP accuracy,
motor capacity or physical hardware safety. Parameters are declared assumptions.
"""
from pathlib import Path
import json,math
ROOT=Path(__file__).resolve().parents[1]
def section(w,h,t):
    return {'A_mm2':w*h-(w-2*t)*(h-2*t),
            'I_weak_mm4':(w*h**3-(w-2*t)*(h-2*t)**3)/12,
            'I_strong_mm4':(h*w**3-(h-2*t)*(w-2*t)**3)/12}
def main():
    cases=[]
    for name,w,h,L in [('upper',60,44,280),('fore',60,60,260)]:
        for thickness in [2.5,6.0]:
            sec=section(w,h,thickness)
            for E,G,tag in [(69000,26000,'aluminum_reference_assumption'),(1500,280,'PETG_nominal_screen_assumption'),(800,220,'PETG_lower_stiffness_sensitivity')]:
                for force in [10.,25.,50.]:
                    d_b=force*L**3/(3*E*sec['I_weak_mm4'])
                    d_s=force*L/(.8*G*sec['A_mm2'])
                    stress=force*L*h/2/sec['I_weak_mm4']
                    cases.append({'link_surrogate':name,'L_mm':L,'outside_mm':[w,h],'wall_mm':thickness,
                                  'property_set':tag,'E_MPa':E,'G_MPa':G,'force_N':force,**sec,
                                  'bending_deflection_mm':d_b,'shear_deflection_mm':d_s,'total_deflection_mm':d_b+d_s,
                                  'nominal_root_bending_stress_MPa':stress,'below_chosen_0p5mm_surrogate_threshold':(d_b+d_s)<=.5,
                                  'not_whole_arm_result':True})
    chosen=[c for c in cases if c['wall_mm']==6 and c['property_set']=='PETG_nominal_screen_assumption' and c['force_N']==25]
    comp=[{'link_surrogate':c['link_surrogate'],'load_N':25,'compliance_factor':k,'deflection_mm':c['total_deflection_mm']*k,
           'elapsed_time_s':None,'not_lifetime_prediction':True} for c in chosen for k in [1,2,4,8]]
    ratios={name:section(w,h,6)['I_weak_mm4']/section(w,h,2.5)['I_weak_mm4'] for name,w,h in [('upper',60,44),('fore',60,60)]}
    assert all(math.isfinite(c['total_deflection_mm']) and c['total_deflection_mm']>0 for c in cases)
    # Verify analytic proportionality and monotonic stiffness, not physical qualification.
    tests=[]
    for name in ['upper','fore']:
        c=[x for x in cases if x['link_surrogate']==name and x['property_set']=='PETG_nominal_screen_assumption' and x['wall_mm']==6]
        tests.append({'name':name+' linear-load scaling','passed':abs(c[2]['total_deflection_mm']/c[0]['total_deflection_mm']-5)<1e-10})
        tests.append({'name':name+' thick-wall greater section stiffness','passed':ratios[name]>1})
    result={'method':'Euler-Bernoulli bending plus Timoshenko shear, closed rectangular uniform-section surrogates; k_shear=0.8.',
            'assumptions_not_certification':True,'cases':cases,'section_second_moment_improvement_factor':ratios,
            'compliance_sensitivity':comp,'analytic_code_checks':tests,
            'limits':['Section dimensions describe reinforced tube spans, but the surrogate extends uniformly across each kinematic link length.',
                      'Real flange roots, stepped geometry, printed layer defects, joint splice, bearing seats and fasteners are omitted.',
                      'Radii, holes and nut pockets omitted from closed-form section properties; not CAD-exact stress results.',
                      'A 0.5 mm screen is an arbitrary comparison threshold for this surrogate, not a released robot accuracy requirement.',
                      'Compliance multipliers have no time or temperature calibration; no creep lifetime is predicted.',
                      'Local 1.25 g/cm3 density is a prototype assumption; real sliced fill, print and moisture alter properties.',
                      'Do not transfer old metal-frame motion/thermal qualification to the printed arm.']}
    (ROOT/'reports/structural-screen.json').write_text(json.dumps(result,indent=2))
    print(json.dumps({'cases':len(cases),'I_factors':ratios,'25N_6mm_PETG_mm':{c['link_surrogate']:c['total_deflection_mm'] for c in chosen},
                      'tests':tests},indent=2))
if __name__=='__main__':main()
