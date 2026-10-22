#define main renderer_entry
#include "pathtrace.cpp"
#undef main
// Independent brute-force intersections, not the renderer's triangle query.
bool brute(const Scene&s,const Ray&r,Hit&out){
 bool got=false;
 if(r.d.y<-.0000001f){float t=(-.002f-r.o.y)/r.d.y;if(t>EPS&&t<out.t){out.t=t;out.part=-2;got=true;}}
 for(const auto&i:s.inst){
  Ray lr(i.R.transpose(r.o-i.o),i.R.transpose(r.d));
  if(boxhit(i.b,r,out.t)==INF)continue;
  for(const Tri&t:i.mesh->tri){
   V gn=cross(t.e1,t.e2);float denom=dot(gn,lr.d);if(fabsf(denom)<1e-16f)continue;
   float dist=dot(gn,t.a-lr.o)/denom;if(dist<=EPS||dist>=out.t)continue;
   V p=lr.o+lr.d*dist;float nn=dot(gn,gn);if(nn<1e-24f)continue;
   float u=dot(cross(p-t.a,t.e2),gn)/nn,v=dot(cross(t.e1,p-t.a),gn)/nn;
   if(u>=-1e-6f&&v>=-1e-6f&&u+v<=1.000001f){out.t=dist;out.part=t.part;got=true;}
  }
 }
 return got;
}
int main(int argc,char**argv){
 if(argc!=3)return 2;omp_set_num_threads(1);Scene s(argv[1]);Frame f=readFrame(argv[2]);s.setFrame(f);RNG rng(83210);
 int passed=0,checks=128;float worst=0;
 for(int i=0;i<checks;i++){
  V target=V(.16f,.28f,0)+V((rng.u()-.5f)*.6f,(rng.u()-.5f)*.7f,(rng.u()-.5f)*.45f);
  Ray ray(f.eye,norm(target-f.eye));Hit a,b;bool aa=s.intersect(ray,a),bb=brute(s,ray,b);
  float err=aa&&bb?fabsf(a.t-b.t):0;worst=std::max(err,worst);
  if(aa==bb && (!aa || err<.00002f))passed++;else std::cerr<<"Mismatch "<<i<<" "<<a.t<<" "<<b.t<<"\n";
 }
 int bsdf=0;
 for(int m=0;m<9;m++){
  for(int i=0;i<1000;i++){
   V v=norm(V(.25f,.4f,1)),n(0,0,1);V wi=sampleBSDF(materials[m],n,v,rng);Eval e=evaluate(materials[m],n,v,wi);
   if(std::isfinite(e.pdf)&&e.pdf>=0 && std::isfinite(mx(e.f))&&e.f.x>=0&&e.f.y>=0&&e.f.z>=0 && fabsf(len(wi)-1)<1e-4)bsdf++;
  }
 }
 std::cout<<"{\"bvh_bruteforce_tests\":"<<checks<<",\"bvh_passed\":"<<passed<<",\"max_distance_error_m\":"<<worst<<",\"finite_nonnegative_bsdf_tests\":9000,\"bsdf_passed\":"<<bsdf<<",\"scope\":\"Numerical software checks, not certification of all transport cases.\"}\n";
 return passed==checks&&bsdf==9000?0:1;
}
