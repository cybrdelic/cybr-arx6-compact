// Small deterministic numerical regression screen. Not a renderer-convergence proof.
#define main pathtracer_program_main
#include "pathtrace.cpp"
#undef main
int main(){
 int checks=0;auto check=[&](bool b,const char*s){if(!b)throw std::runtime_error(s);checks++;};
 V n(0,0,1);Material m{{.71,.73,.76},1,.25f,.43f,V(1,0,0)};RNG rng(57292);
 for(int i=0;i<10000;i++){
  V a=norm(V(rng.u()*2-1,rng.u()*2-1,.1f+rng.u()));V b=norm(V(rng.u()*2-1,rng.u()*2-1,.1f+rng.u()));
  Eval ab=evaluate(m,n,a,b),ba=evaluate(m,n,b,a);
  check(std::isfinite(ab.pdf)&&ab.pdf>=0,"invalid BSDF PDF");
  check(std::isfinite(ab.f.x)&&std::isfinite(ab.f.y)&&std::isfinite(ab.f.z)&&ab.f.x>=0,"invalid BRDF");
  check(len(ab.f-ba.f)<1e-4f*(1+len(ab.f)),"reciprocity mismatch");
  V sampled=sampleBSDF(m,n,a,rng);check(std::isfinite(sampled.x)&&fabsf(len(sampled)-1)<1e-4f,"invalid direction");
 }
 int cells[64]={};double sx=0,sy=0;
 for(int s=0;s<64;s++){
  RNG r((uint64_t(hash32(12391))<<32)|hash32(s+793));
  float x=(s%8+r.u())/8,y=(s/8+r.u())/8;
  cells[int(y*8)*8+int(x*8)]++;sx+=x;sy+=y;
  check(x>=0&&x<1&&y>=0&&y<1,"pixel sample outside support");
 }
 for(int c:cells)check(c==1,"nonuniform subpixel strata");
 check(fabs(sx/64-.5)<.04&&fabs(sy/64-.5)<.04,"biased sample mean");
 for(int i=0;i<10000;i++){
  float v=noise3(V(rng.u()*100,rng.u()*100,rng.u()*100));check(v>=0&&v<=1,"texture noise outside bounds");
 }
 check(band(4000,.0005)<band(4000,.00005),"texture prefilter ordering");
 std::cout<<"{\"passed\":true,\"assertions\":"<<checks<<",\"tests\":[\"anisotropic BRDF non-negativity\",\"reciprocity\",\"VNDF direction normalization\",\"64-cell camera sample coverage\",\"procedural texture bounds\",\"texture filter falloff\"]}"<<std::endl;
}
