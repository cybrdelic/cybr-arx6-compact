import fs from 'node:fs';
import path from 'node:path';
import {fileURLToPath} from 'node:url';
import createMuJoCo from './runtime/mujoco.js';
import {reference,referenceDerivatives} from './reference.mjs';
const root=path.dirname(fileURLToPath(import.meta.url));
const mj=await createMuJoCo({locateFile:f=>path.join(root,'runtime',f)});
const xml=fs.readFileSync(path.join(root,'capture-model.xml'),'utf8');
const p=JSON.parse(fs.readFileSync(path.join(root,'capture-parameters.json'),'utf8'));
mj.FS.writeFile('/capture.xml',xml);
const m=mj.MjModel.mj_loadXML('/capture.xml');if(!m)throw Error('XML rejected');
const d=new mj.MjData(m);mj.mj_resetDataKeyframe(m,d,0);
const r0=reference(0,p);for(let j=0;j<6;j++)d.qpos[j]=r0.q[j];
mj.mj_forward(m,d);
const Mbuf=new mj.DoubleBuffer(m.nv*m.nv), frames=[], bodies=[];
const bodyNames=['fixed_hardware','turret','upper','fore','roll','bend','tool','jaw_left','jaw_right','puck'];
const ids=bodyNames.map(n=>mj.mj_name2id(m,1,n));
let maxErr=0,minY=1,gripDist=0;const peakTau=Array(6).fill(0);
const dt=m.opt.timestep,total=Math.round(10/dt),fps=120;
for(let k=0;k<=total;k++){
 const t=k*dt;
 if(k%Math.round(1/(fps*dt))===0){
  frames.push([t,...Array.from(d.qpos),...Array.from(d.qvel)]);
  bodies.push(ids.map(id=>[...Array.from(d.xpos).slice(3*id,3*id+3),...Array.from(d.xmat).slice(9*id,9*id+9)]));
 }
 if(k===total)break;
 const ref=referenceDerivatives(t,p);mj.mj_fullM(m,d,Mbuf);const M=Mbuf.GetView();
 const q=d.qpos,v=d.qvel,bias=d.qfrc_bias;
 const springs=[0,-6.46015082530387*(q[1]+.65),-3.3012251703041877*(q[2]-.55),0,0,0];
 for(let i=0;i<6;i++){
  d.qfrc_applied[i]=springs[i];
  let tau=bias[i]-springs[i];
  for(let j=0;j<6;j++)tau+=M[i*m.nv+j]*(ref.qdd[j]+0*(ref.q[j]-q[j])+0*(ref.qd[j]-v[j]));
  tau += [500,700,500,55,65,45][i]*(ref.q[i]-q[i])+[25,35,25,2.8,3.2,2.5][i]*(ref.qd[i]-v[i]);
  const limit=i<3?55:12;
  d.ctrl[i]=Math.max(-limit,Math.min(limit,tau));peakTau[i]=Math.max(peakTau[i],Math.abs(d.ctrl[i]));
  maxErr=Math.max(maxErr,Math.abs(ref.q[i]-q[i]));
 }
 const avg=(q[6]+q[7])/2,vel=(v[6]+v[7])/2;
 const force=Math.max(-14,Math.min(14,8000*(ref.gap-avg)-12*vel));
 d.ctrl[6]=force*.006;
 mj.mj_step(m,d);
 if(!Array.from(d.qpos).every(Number.isFinite))throw Error('Nonfinite simulation');
 minY=Math.min(minY,d.qpos[9]);
}
const out={version:'cinema-reconstruction-1',engine:'MuJoCo WASM '+mj.mj_versionString(),dt,columns:'t, qpos[15], qvel[14]',frames,bodies,bodyNames,scope:'Fresh computed-torque/contact capture of compact P5 body dimensions and mass tensors. Not the original electromechanical controller or 28-scenario validation; not a hardware result.',metrics:{peakTau,maxJointErrorRad:maxErr,minPuckY:minY}};
fs.writeFileSync(path.join(root,'../assets/capture.json'),JSON.stringify(out));
for(const time of [0,.65,1.5,2.5,3.6,4.8,5,6.5,7.5,8.7,9.9]){
 const f=frames[Math.round(time*120)];console.log(time,'puck',f.slice(9,12),'jaws',f.slice(7,9),'q',f.slice(1,7));
}
console.log(out.metrics);
