// ARX / 6: native CPU Monte Carlo path tracer. No rasterization, shadow maps,
// ambient-occlusion pass, generated-image inputs, or screen-space reflections.
// CAD triangles are immutable. Two-level BVHs are reused as rigid bodies move.
// Rectangular emitter next-event estimation, GGX VNDF sampling, MIS and diffuse
// bounce transport. All lengths are metres, output is scene-linear RGB.
#include <algorithm>
#include <array>
#include <atomic>
#include <chrono>
#include <cmath>
#include <cstdint>
#include <cstdio>
#include <cstring>
#include <fstream>
#include <iostream>
#include <limits>
#include <numeric>
#include <stdexcept>
#include <string>
#include <vector>
#include <omp.h>
constexpr float PI=3.14159265358979323846f, INF=1e30f, EPS=0.000004f;
struct V {
 float x=0,y=0,z=0;
 V()=default; V(float a):x(a),y(a),z(a){} V(float a,float b,float c):x(a),y(b),z(c){}
 float operator[](int i)const{return (&x)[i];} float& operator[](int i){return (&x)[i];}
 V operator+(V b)const{return {x+b.x,y+b.y,z+b.z};}
 V operator-(V b)const{return {x-b.x,y-b.y,z-b.z};}
 V operator-()const{return {-x,-y,-z};}
 V operator*(V b)const{return {x*b.x,y*b.y,z*b.z};}
 V operator*(float b)const{return {x*b,y*b,z*b};}
 V operator/(float b)const{return *this*(1/b);}
 V& operator+=(V b){x+=b.x;y+=b.y;z+=b.z;return *this;}
};
inline V operator*(float a,V b){return b*a;}
inline float dot(V a,V b){return a.x*b.x+a.y*b.y+a.z*b.z;}
inline V cross(V a,V b){return {a.y*b.z-a.z*b.y,a.z*b.x-a.x*b.z,a.x*b.y-a.y*b.x};}
inline float len(V v){return sqrtf(dot(v,v));}
inline V norm(V v){return v/std::max(1e-20f,len(v));}
inline V vmin(V a,V b){return {std::min(a.x,b.x),std::min(a.y,b.y),std::min(a.z,b.z)};}
inline V vmax(V a,V b){return {std::max(a.x,b.x),std::max(a.y,b.y),std::max(a.z,b.z)};}
inline float mx(V v){return std::max(v.x,std::max(v.y,v.z));}
inline float luminance(V v){return .2126f*v.x+.7152f*v.y+.0722f*v.z;}
inline float sq(float v){return v*v;}
inline float clamp(float v,float lo=0,float hi=1){return std::max(lo,std::min(v,hi));}
struct RNG{
 uint64_t state;
 explicit RNG(uint64_t seed){state=seed+0x9e3779b97f4a7c15ULL;next();}
 uint32_t next(){state=state*6364136223846793005ULL+1442695040888963407ULL;uint32_t x=(uint32_t)(((state>>18)^state)>>27);uint32_t r=state>>59;return (x>>r)|(x<<((-r)&31));}
 float u(){return (next()>>8)*0x1p-24f;}
};
inline uint32_t hash32(uint32_t a){a^=a>>16;a*=0x7feb352d;a^=a>>15;a*=0x846ca68b;a^=a>>16;return a;}
struct Ray{V o,d,inv;Ray(V O,V D):o(O),d(D),inv(1/(fabsf(D.x)>1e-19f?D.x:1e-19f),1/(fabsf(D.y)>1e-19f?D.y:1e-19f),1/(fabsf(D.z)>1e-19f?D.z:1e-19f)){} };
struct Box{
 V lo=V(INF),hi=V(-INF);
 void add(V p){lo=vmin(lo,p);hi=vmax(hi,p);} void add(Box b){lo=vmin(lo,b.lo);hi=vmax(hi,b.hi);}
 float area()const{V d=vmax(V(0),hi-lo);return 2*(d.x*d.y+d.y*d.z+d.z*d.x);}
};
inline float boxhit(const Box&b,const Ray&r,float maxt){
 V a=(b.lo-r.o)*r.inv,c=(b.hi-r.o)*r.inv;
 V n=vmin(a,c),f=vmax(a,c);
 float near=std::max(0.f,std::max(n.x,std::max(n.y,n.z)));
 float far=std::min(maxt,std::min(f.x,std::min(f.y,f.z)));
 return near<=far?near:INF;
}
struct Tri {V a,e1,e2,n0,n1,n2; int part=0,mat=0;};
inline Box bounds(const Tri&t){Box b;b.add(t.a);b.add(t.a+t.e1);b.add(t.a+t.e2);return b;}
inline V center(const Tri&t){return t.a+(t.e1+t.e2)*(1.f/3);}
struct alignas(32) Node{V lo;uint32_t left=0;V hi;uint32_t count=0;Box box()const{return {lo,hi};}};
struct Hit{float t=INF,u=0,v=0;int tri=-1,inst=-1,mat=0,part=-1;V p,n,ng,albedo;};
struct Mesh{
 std::vector<Tri> tri;std::vector<Node> nodes;
 void split(uint32_t ni,uint32_t first,uint32_t count,int depth){
  Box b,cb;for(uint32_t i=first;i<first+count;i++){b.add(bounds(tri[i]));cb.add(center(tri[i]));}
  nodes[ni].lo=b.lo;nodes[ni].hi=b.hi;nodes[ni].left=first;nodes[ni].count=count;
  if(count<=5 || depth>=48)return;
  constexpr int B=12;float best=INF;int axis=-1,binsplit=0;
  for(int a=0;a<3;a++){
   float span=cb.hi[a]-cb.lo[a];if(span<1e-7f)continue;
   struct Bin {Box b;int n=0;};std::array<Bin,B> bins{};
   for(uint32_t i=first;i<first+count;i++){int k=std::min(B-1,int((center(tri[i])[a]-cb.lo[a])*B/span));bins[k].b.add(bounds(tri[i]));bins[k].n++;}
   std::array<float,B> cost{};std::array<int,B> cnt{};Box l;int nl=0;
   for(int i=0;i<B;i++){if(bins[i].n)l.add(bins[i].b);nl+=bins[i].n;cost[i]=l.area()*nl;cnt[i]=nl;}
   Box rr;int nr=0;
   for(int i=B-1;i>0;i--){if(bins[i].n)rr.add(bins[i].b);nr+=bins[i].n;
    float c=cost[i-1]+rr.area()*nr;
    if(cnt[i-1] && nr && c<best){best=c;axis=a;binsplit=i;}
   }
  }
  if(axis<0)return;
  if(best>=b.area()*count && count<=12)return;
  float threshold=cb.lo[axis]+(cb.hi[axis]-cb.lo[axis])*float(binsplit)/B;
  auto it=std::partition(tri.begin()+first,tri.begin()+first+count,[&](const Tri&t){return center(t)[axis]<threshold;});
  uint32_t mid=it-tri.begin();if(mid==first||mid==first+count)return;
  uint32_t child=nodes.size();nodes.resize(child+2);nodes[ni].left=child;nodes[ni].count=0;
  split(child,first,mid-first,depth+1);split(child+1,mid,first+count-mid,depth+1);
 }
 void build(){nodes.clear();nodes.resize(1);split(0,0,tri.size(),0);}
 bool intersect(const Ray&r,Hit&h,bool any=false)const{
  if(nodes.empty())return false;int stack[96];int sp=0;stack[sp++]=0;bool found=false;
  while(sp){const Node&n=nodes[stack[--sp]];if(boxhit(n.box(),r,h.t)==INF)continue;
   if(n.count){for(uint32_t i=n.left;i<n.left+n.count;i++){
    const Tri&t=tri[i];V p=cross(r.d,t.e2);float det=dot(t.e1,p);if(fabsf(det)<1e-15f)continue;
    float id=1/det;V s=r.o-t.a;float u=dot(s,p)*id;if(u<0||u>1)continue;
    V q=cross(s,t.e1);float v=dot(r.d,q)*id;if(v<0||u+v>1)continue;
    float dist=dot(t.e2,q)*id;if(dist<=EPS||dist>=h.t)continue;
    h.t=dist;h.u=u;h.v=v;h.tri=i;found=true;if(any)return true;
   }}else{
    float l=boxhit(nodes[n.left].box(),r,h.t),rr=boxhit(nodes[n.left+1].box(),r,h.t);
    if(l<rr){if(rr!=INF)stack[sp++]=n.left+1;if(l!=INF)stack[sp++]=n.left;}
    else{if(l!=INF)stack[sp++]=n.left;if(rr!=INF)stack[sp++]=n.left+1;}
   }
  }return found;
 }
};
struct Mat3 {V row[3];V mul(V v)const{return {dot(row[0],v),dot(row[1],v),dot(row[2],v)};}
 V transpose(V v)const{return row[0]*v.x+row[1]*v.y+row[2]*v.z;}};
struct Instance{Mesh*mesh;Mat3 R;V o;Box b;};
struct Material{V base;float metal,rough;float roughY=0;V tangent=V(1,0,0);};
const Material materials[]={
 {{.71f,.73f,.76f},1,.36f},       // neutral warm ceramic/enamel finish
 {{.026f,.030f,.036f},.08f,.31f}, // dark anodized metal
 {{.73f,.75f,.78f},1,.25f},
 {{.56f,.60f,.64f},1,.24f},
 {{.65f,.36f,.12f},1,.22f},
 {{.018f,.075f,.034f},.1f,.45f},
 {{.012f,.013f,.015f},0,.62f},
 {{.022f,.024f,.028f},0,.40f},
 {{.024f,.026f,.031f},.10f,.27f},
 {{.12f,.14f,.16f},.85f,.28f} // turned black-anodized service caps
};
#include "part_centers.h"
struct Light{V c,u,v,n,Le;float area;
 Light(V center,V target,float w,float h,V emission):c(center),Le(emission){n=norm(target-c);V x=norm(cross(n,V(0,1,0)));u=x*(w*.5f);v=norm(cross(x,n))*(h*.5f);area=w*h;}
 bool hit(const Ray&r,float&d)const{float den=dot(n,r.d);if(den>-.000001f)return false;d=dot(c-r.o,n)/den;if(d<=EPS)return false;V p=r.o+r.d*d-c;return fabsf(dot(p,u))<=dot(u,u)&&fabsf(dot(p,v))<=dot(v,v);}
};
struct Frame{int index=0,w=1920,h=1080,spp=32,maxDepth=6,explode=0;V eye,target;float fov=32,aperture=0,exposure=1;
 std::vector<Mat3> R;std::vector<V> pos;};
struct Scene {
 std::vector<Mesh> partMeshes;std::array<Mesh,10> bodyMeshes;std::vector<int> partBody;std::vector<Instance> inst;
 std::vector<Light> lights;std::vector<Node> tlas;std::vector<int> order;
 Scene(const std::string&filename){
  std::ifstream f(filename,std::ios::binary);if(!f)throw std::runtime_error("Missing native geometry");
  uint32_t magic,n;f.read((char*)&magic,4);f.read((char*)&n,4);if(magic!=0x41525850)throw std::runtime_error("Invalid geometry header");
  partMeshes.resize(n);partBody.resize(n);
  for(uint32_t i=0;i<n;i++){uint32_t id,b,m,nt;f.read((char*)&id,4);f.read((char*)&b,4);f.read((char*)&m,4);f.read((char*)&nt,4);partBody[id]=b;
   auto&mes=partMeshes[id];mes.tri.reserve(nt);
   for(uint32_t k=0;k<nt;k++){float a[18];f.read((char*)a,sizeof(a));Tri t;t.a={a[0],a[1],a[2]};t.e1=V(a[3],a[4],a[5])-t.a;t.e2=V(a[6],a[7],a[8])-t.a;t.n0={a[9],a[10],a[11]};t.n1={a[12],a[13],a[14]};t.n2={a[15],a[16],a[17]};t.part=id;t.mat=(id==2||id==32||id==66||id==100||id==132||id==168||id==272)?1:m;if(id==3||id==33||id==67||id==101||id==133||id==169)t.mat=9;mes.tri.push_back(t);bodyMeshes[b].tri.push_back(t);}
  }if(!f)throw std::runtime_error("Truncated native geometry");
  #pragma omp parallel for schedule(dynamic)
  for(int i=0;i<(int)n;i++)partMeshes[i].build();
  #pragma omp parallel for schedule(dynamic)
  for(int i=0;i<10;i++)bodyMeshes[i].build();
  lights.emplace_back(V(-.58f,1.15f,.55f),V(.13f,.27f,0),.90f,.75f,V(6.8f,6.6f,6.2f));
  lights.emplace_back(V(.90f,.70f,.28f),V(.20f,.25f,0),.24f,.80f,V(1.8f,2.05f,2.5f));
  lights.emplace_back(V(.0f,1.35f,-.85f),V(.15f,.32f,0),.75f,.38f,V(4.1f,4.6f,5.3f));
  lights.emplace_back(V(.10f,.65f,1.5f),V(.15f,.30f,0),1.0f,.65f,V(1.1f,1.1f,1.1f));
 }
 void topBuild(int ni,int first,int count){Box box,cb;for(int j=first;j<first+count;j++){Box b=inst[order[j]].b;box.add(b);cb.add((b.lo+b.hi)*.5f);}tlas[ni].lo=box.lo;tlas[ni].hi=box.hi;tlas[ni].left=first;tlas[ni].count=count;if(count<=1)return;
  V e=cb.hi-cb.lo;int a=e.x>e.y?(e.x>e.z?0:2):(e.y>e.z?1:2);int mid=first+count/2;
  std::nth_element(order.begin()+first,order.begin()+mid,order.begin()+first+count,[&](int x,int y){return inst[x].b.lo[a]+inst[x].b.hi[a]<inst[y].b.lo[a]+inst[y].b.hi[a];});
  int ch=tlas.size();tlas.resize(ch+2);tlas[ni].count=0;tlas[ni].left=ch;topBuild(ch,first,mid-first);topBuild(ch+1,mid,first+count-mid);
 }
 void setFrame(const Frame&f){inst.clear();
  int n=f.explode?partMeshes.size():10;
  for(int i=0;i<n;i++){
   Mesh*mesh=f.explode?&partMeshes[i]:&bodyMeshes[i];if(mesh->tri.empty())continue;
   Mat3 R=f.R[i];V o=f.pos[i];Box b=mesh->nodes[0].box(),world;
   for(int a=0;a<8;a++){V p((a&1)?b.hi.x:b.lo.x,(a&2)?b.hi.y:b.lo.y,(a&4)?b.hi.z:b.lo.z);world.add(R.mul(p)+o);}
   world.lo=world.lo-V(EPS);world.hi=world.hi+V(EPS);inst.push_back({mesh,R,o,world});
  }
  order.resize(inst.size());std::iota(order.begin(),order.end(),0);tlas.clear();tlas.resize(1);topBuild(0,0,order.size());
 }
 bool intersect(const Ray&r,Hit&h,bool any=false)const{
  bool found=false;if(r.d.y<-.0000001f){float d=(-.002f-r.o.y)/r.d.y;if(d>EPS&&d<h.t){h.t=d;h.inst=-2;h.tri=-1;h.part=-2;h.mat=8;h.n=h.ng=V(0,1,0);found=true;if(any)return true;}}
  int stack[96],sp=0;stack[sp++]=0;
  while(sp){const Node&n=tlas[stack[--sp]];if(boxhit(n.box(),r,h.t)==INF)continue;
   if(n.count){int id=order[n.left];const auto&i=inst[id];Ray lr(i.R.transpose(r.o-i.o),i.R.transpose(r.d));Hit local;local.t=h.t;
    if(i.mesh->intersect(lr,local,any)){if(any)return true;h=local;h.inst=id;found=true;}
   }else{float a=boxhit(tlas[n.left].box(),r,h.t),b=boxhit(tlas[n.left+1].box(),r,h.t);if(a<b){if(b!=INF)stack[sp++]=n.left+1;if(a!=INF)stack[sp++]=n.left;}else{if(a!=INF)stack[sp++]=n.left;if(b!=INF)stack[sp++]=n.left+1;}}
  }
  if(found&&!any){h.p=r.o+r.d*h.t;if(h.inst>=0){const auto&i=inst[h.inst];const Tri&t=i.mesh->tri[h.tri];h.ng=norm(i.R.mul(cross(t.e1,t.e2)));h.n=norm(i.R.mul(t.n0*(1-h.u-h.v)+t.n1*h.u+t.n2*h.v));if(dot(h.ng,-r.d)<0)h.ng=-h.ng;if(dot(h.n,h.ng)<0)h.n=-h.n;if(dot(h.n,-r.d)<.01f)h.n=h.ng;h.mat=t.mat;h.part=t.part;}
   h.albedo=materials[h.mat].base;
  }return found;
 }
 bool blocked(V p,V d,float t)const{Hit h;h.t=t;return intersect(Ray(p,d),h,true);}
};

struct Basis {
 V x,y,n;
 explicit Basis(V N):n(N){x=norm(cross(fabsf(n.y)<.9f?V(0,1,0):V(1,0,0),n));y=cross(n,x);}
 Basis(V N,V T):n(N){x=T-n*dot(T,n);if(dot(x,x)<1e-8f)x=cross(fabsf(n.y)<.9f?V(0,1,0):V(1,0,0),n);x=norm(x);y=cross(n,x);}
 V local(V v)const{return {dot(v,x),dot(v,y),dot(v,n)};}
 V world(V v)const{return x*v.x+y*v.y+n*v.z;}
};
inline float fade(float x){return x*x*(3-2*x);}
float noise3(V p){
 int ix=int(floorf(p.x)),iy=int(floorf(p.y)),iz=int(floorf(p.z));
 float x=fade(p.x-ix),y=fade(p.y-iy),z=fade(p.z-iz),a[8];
 for(int k=0;k<8;k++)a[k]=float(hash32(uint32_t(ix+(k&1))*73856093u ^ uint32_t(iy+((k>>1)&1))*19349663u ^ uint32_t(iz+((k>>2)&1))*83492791u)>>8)*0x1p-24f;
 float b0=(a[0]*(1-x)+a[1]*x)*(1-y)+(a[2]*(1-x)+a[3]*x)*y;
 float b1=(a[4]*(1-x)+a[5]*x)*(1-y)+(a[6]*(1-x)+a[7]*x)*y;
 return b0*(1-z)+b1*z;
}
inline float band(float frequency,float footprint){return expf(-sq(PI*frequency*footprint)*.5f);}
Material materialAt(const Scene&scene,Hit&h,const Ray&ray,float footprint){
 Material m=materials[h.mat];V local=h.p,ln=h.n;
 if(h.inst>=0){const auto&i=scene.inst[h.inst];local=i.R.transpose(h.p-i.o);ln=i.R.transpose(h.n);}
 // Coordinates are tied to each rigid body; patterns cannot slide in world space.
 V seed(float((h.part*17)%97)*.17f,float((h.part*29)%89)*.13f,float((h.part*13)%71)*.19f);
 V axis(0,1,0);V tangent=axis-ln*dot(axis,ln);
 if(dot(tangent,tangent)<.05f)tangent=V(1,0,0)-ln*ln.x;
 tangent=norm(tangent);V across=norm(cross(ln,tangent));
 float coarse=noise3(local*230.f+seed)-.5f;
 float fine=(noise3(local*2100.f+seed)-.5f)*band(2100.f,footprint);
 float coord=dot(local,across),along=dot(local,tangent);
 float grain=0.65f*sinf(2*PI*(coord*1450.f+.09f*sinf(along*230.f)))*band(1450.f,footprint)
            +0.35f*sinf(2*PI*(coord*2397.f+.14f*sinf(along*155.f)))*band(2397.f,footprint);
 float bump=0;
 if(h.mat==0){ // satin/bead-blasted aluminum, mild directional tooling response
  m.base=m.base*(1+.025f*coarse+.008f*fine);
  m.rough=clamp(.33f+.026f*coarse+.012f*grain,.28f,.39f);m.roughY=.44f+.025f*coarse;
  bump=.010f*grain+.010f*fine;
 }else if(h.mat==2){ // brushed aluminum on adapters, plates, and exposed rims
  m.base=m.base*(1+.018f*coarse);m.rough=.22f+.014f*coarse;m.roughY=.39f+.027f*coarse;
  bump=.014f*grain;
 }else if(h.mat==1){ // dark coated metal: dielectric response, subtle orange peel
  m.base=m.base*(1+.055f*coarse);m.rough=.31f+.035f*coarse+.018f*fine;m.roughY=m.rough;
  bump=.018f*fine;
 }else if(h.mat==9){
  V axis=(h.part==33||h.part==67||h.part==133)?V(0,0,1):V(0,1,0);
  V delta=local-partCenters[h.part];V radial=delta-axis*dot(delta,axis);float radius=len(radial);
  if(radius>1e-6f){radial=radial/radius;tangent=norm(cross(axis,radial));across=radial;}
  float turning=sinf(2*PI*radius/0.00025f)*band(4000.f,footprint);
  m.rough=.24f+.01f*coarse;m.roughY=.34f+.012f*coarse;m.base=m.base*(1+.018f*coarse);bump=.013f*turning;
 }else if(h.mat==3||h.mat==4){
  m.rough+=.018f*coarse;m.roughY=m.rough*1.22f;bump=.006f*grain;
 }else if(h.mat==6||h.mat==7){
  m.rough+=.025f*coarse;m.base=m.base*(1+.025f*coarse);bump=.016f*fine;
 }else if(h.mat==8){
  m.base=m.base*(1+.045f*coarse);m.rough=.30f+.015f*coarse;m.roughY=m.rough;bump=.006f*fine;
 }
 V tx=tangent,ac=across;
 if(h.inst>=0){tx=scene.inst[h.inst].R.mul(tx);ac=scene.inst[h.inst].R.mul(ac);}
 V candidate=norm(h.n+ac*bump+tx*(fine*.006f));
 if(dot(candidate,h.ng)>.72f&&dot(candidate,-ray.d)>.01f)h.n=candidate;
 m.tangent=tx;return m;
}
inline float D_aniso(V h,float ax,float ay){float q=sq(h.x/ax)+sq(h.y/ay)+sq(h.z);return 1/(PI*ax*ay*q*q);}
inline float G1_aniso(V v,float ax,float ay){if(v.z<=0)return 0;return 2/(1+sqrtf(1+(sq(ax*v.x)+sq(ay*v.y))/sq(v.z)));}
inline V fresnel(V f0,float c){float x=1-clamp(c);float v=x*x*x*x*x;return f0+(V(1)-f0)*v;}
struct Eval{V f;float pdf;};
Eval evaluate(const Material&m,V n,V wo,V wi){
 Basis b(n,m.tangent);V v=b.local(wo),l=b.local(wi);
 if(v.z<=0||l.z<=0)return {V(0),0};V h=norm(v+l);float vh=clamp(dot(v,h));
 float ax=std::max(.025f,m.rough*m.rough),ry=m.roughY>0?m.roughY:m.rough,ay=std::max(.025f,ry*ry);
 float D=D_aniso(h,ax,ay),Gv=G1_aniso(v,ax,ay),Gl=G1_aniso(l,ax,ay);
 V F=fresnel(V(.04f)*(1-m.metal)+m.base*m.metal,vh);
 V spec=F*(D*Gv*Gl/std::max(1e-8f,4*v.z*l.z));V diff=m.base*((1-m.metal)/PI)*(V(1)-F);
 float q=.25f+.70f*m.metal;return {spec+diff,q*(D*Gv/(4*v.z))+(1-q)*l.z/PI};
}
V sampleBSDF(const Material&m,V n,V wo,RNG&rng){
 Basis b(n,m.tangent);V v=b.local(wo);float q=.25f+.7f*m.metal;
 if(rng.u()>q){float r=sqrtf(rng.u()),p=2*PI*rng.u();return b.world({r*cosf(p),r*sinf(p),sqrtf(std::max(0.f,1-r*r))});}
 float ax=std::max(.025f,m.rough*m.rough),ry=m.roughY>0?m.roughY:m.rough,ay=std::max(.025f,ry*ry);
 V vh=norm(V(ax*v.x,ay*v.y,v.z));V t1=vh.z<.99999f?norm(cross(V(0,0,1),vh)):V(1,0,0),t2=cross(vh,t1);
 float radius=sqrtf(rng.u()),phi=2*PI*rng.u(),p1=radius*cosf(phi),p2=radius*sinf(phi),s=.5f*(1+vh.z);
 p2=(1-s)*sqrtf(std::max(0.f,1-p1*p1))+s*p2;
 V nh=t1*p1+t2*p2+vh*sqrtf(std::max(0.f,1-p1*p1-p2*p2));V h=norm(V(ax*nh.x,ay*nh.y,std::max(0.f,nh.z)));
 return norm(b.world(h*(2*dot(v,h))-v));
}
inline float mis(float p,float q){return p*p/(p*p+q*q+1e-30f);}
V trace(const Scene&scene,Ray ray,RNG&rng,int maxDepth,uint64_t&raycount,float coneSpread=0.0002f){V result(0),throughput(1);float lastPdf=0;float lastProb[4]={1,1,1,1};V lastP;bool first=true;
 for(int bounce=0;bounce<maxDepth;bounce++){
  raycount++;Hit h;bool got=scene.intersect(ray,h);int emitter=-1;float et=h.t;
  for(int j=0;j<(int)scene.lights.size();j++){float d;if(scene.lights[j].hit(ray,d)&&d<et){et=d;emitter=j;}}
  if(emitter>=0){const auto&l=scene.lights[emitter];float lightPdf=lastProb[emitter]*et*et/(l.area*std::max(.000001f,-dot(l.n,ray.d)));float weight=first?1:mis(lastPdf,lightPdf);result+=throughput*l.Le*weight;break;}
  if(!got){V env(.012f,.015f,.020f);result+=throughput*env;break;}
  Material m=materialAt(scene,h,ray,std::max(.000008f,coneSpread*h.t/std::max(.25f,fabsf(dot(h.ng,ray.d)))));V wo=-ray.d;
  float weights[4],sumW=0;
  for(int j=0;j<4;j++){const auto&l=scene.lights[j];V dd=l.c-h.p;float d2=dot(dd,dd);V direction=dd/sqrtf(d2);weights[j]=luminance(l.Le)*l.area*std::max(.04f,dot(h.n,direction))*std::max(.04f,-dot(l.n,direction))/d2;sumW+=weights[j];}
  for(int j=0;j<4;j++)lastProb[j]=weights[j]/sumW;
  float choice=rng.u();int chosen=0;for(;chosen<3 && choice>lastProb[chosen];chosen++)choice-=lastProb[chosen];
  for(int only=0;only<1;only++){const auto&l=scene.lights[chosen];
   V lp=l.c+l.u*(2*rng.u()-1)+l.v*(2*rng.u()-1);V delta=lp-h.p;float d2=dot(delta,delta),d=sqrtf(d2);V wi=delta/d;float nl=dot(h.n,wi),lc=-dot(l.n,wi);
   if(nl<=0||lc<=0||dot(h.ng,wi)<=0)continue;
   Eval e=evaluate(m,h.n,wo,wi);float pdf=lastProb[chosen]*d2/(lc*l.area);if(mx(e.f)<1e-10f)continue;
   raycount++;if(scene.blocked(h.p+h.ng*(2*EPS),wi,d-4*EPS))continue;
   result+=throughput*e.f*l.Le*(nl*(bounce+1==maxDepth?1.f:mis(pdf,e.pdf))/pdf);
  }
  V wi=sampleBSDF(m,h.n,wo,rng);float nl=dot(h.n,wi);if(nl<=0||dot(h.ng,wi)<=0)break;Eval e=evaluate(m,h.n,wo,wi);if(e.pdf<1e-12f)break;
  throughput=throughput*e.f*(nl/e.pdf);if(!std::isfinite(mx(throughput)))break;
  if(bounce>=2){float survive=clamp(mx(throughput),.10f,.96f);if(rng.u()>survive)break;throughput=throughput/survive;}
  lastPdf=e.pdf;lastP=h.p;first=false;ray=Ray(h.p+h.ng*(2*EPS),wi);
 }return result;}
Frame readFrame(const std::string&path){std::ifstream f(path,std::ios::binary);if(!f)throw std::runtime_error("Missing frame "+path);Frame a;int32_t ints[7];f.read((char*)ints,sizeof(ints));a.index=ints[0];a.w=ints[1];a.h=ints[2];a.spp=ints[3];a.maxDepth=ints[4];a.explode=ints[5];int n=ints[6];float cam[9];f.read((char*)cam,sizeof(cam));a.eye={cam[0],cam[1],cam[2]};a.target={cam[3],cam[4],cam[5]};a.fov=cam[6];a.aperture=cam[7];a.exposure=cam[8];a.R.resize(n);a.pos.resize(n);
 for(int i=0;i<n;i++){float rows[12];f.read((char*)rows,48);for(int j=0;j<3;j++)a.R[i].row[j]={rows[j*4],rows[j*4+1],rows[j*4+2]};a.pos[i]={rows[3],rows[7],rows[11]};}if(!f)throw std::runtime_error("Truncated frame input");return a;}
void render(const Scene&scene,const Frame&f,const std::string&out){
 auto started=std::chrono::steady_clock::now();std::vector<float> image((size_t)f.w*f.h*12);V forward=norm(f.target-f.eye),right=norm(cross(forward,V(0,1,0))),up=cross(right,forward);float tanhalf=tanf(f.fov*PI/360.f),aspect=float(f.w)/f.h,focus=len(f.target-f.eye);uint64_t totalRays=0;
 #pragma omp parallel for schedule(dynamic,2) reduction(+:totalRays)
 for(int y=0;y<f.h;y++){
  for(int x=0;x<f.w;x++){
   int px=y*f.w+x;float*o=&image[(size_t)px*12];auto direction=[&](float u,float v){return norm(forward+right*((2*u/f.w-1)*tanhalf*aspect)+up*((1-2*v/f.h)*tanhalf));};
   V guideDir=direction(x+.5f,y+.5f);Hit guide;scene.intersect(Ray(f.eye,guideDir),guide);
   V color(0);uint64_t nr=0;
   const int samples=f.spp; // Uniform coverage: thin features receive the full sample budget.
   int strata=std::max(1,int(sqrtf(float(samples))));
   for(int s=0;s<samples;s++){
    RNG rng((uint64_t(hash32(px+12391))<<32)|hash32(s+793));
    // Temporal seed is fixed, so camera motion does not create independent flicker.
    float ux=(s%strata+rng.u())/strata,uy=((s/strata)%strata+rng.u())/strata;
    // Non-square sample counts use random subpixel offsets for remaining strata.
    if(s>=strata*strata){ux=rng.u();uy=rng.u();}
    V d=direction(x+ux,y+uy);V ori=f.eye;
    if(f.aperture>0){float radius=f.aperture*sqrtf(rng.u()),phi=2*PI*rng.u();V lens=right*(radius*cosf(phi))+up*(radius*sinf(phi));V point=f.eye+d*(focus/std::max(.01f,dot(d,forward)));ori+=lens;d=norm(point-ori);}
    color+=trace(scene,Ray(ori,d),rng,f.maxDepth,nr,2*tanhalf/f.h);
   }color=color/float(samples);totalRays+=nr;
   o[0]=color.x;o[1]=color.y;o[2]=color.z;o[3]=guide.n.x;o[4]=guide.n.y;o[5]=guide.n.z;o[6]=guide.t;o[7]=float(guide.part);o[8]=guide.albedo.x;o[9]=guide.albedo.y;o[10]=guide.albedo.z;o[11]=float(samples);
  }
 }
 std::ofstream file(out,std::ios::binary);int32_t h[4]={f.w,f.h,12,f.spp};file.write((char*)h,sizeof(h));file.write((char*)image.data(),image.size()*sizeof(float));if(!file)throw std::runtime_error("Output write failed");
 double sec=std::chrono::duration<double>(std::chrono::steady_clock::now()-started).count();
 std::cout<<"FRAME "<<f.index<<" "<<f.w<<"x"<<f.h<<" spp="<<f.spp<<" depth="<<f.maxDepth<<" rays="<<totalRays<<" seconds="<<sec<<" output="<<out<<std::endl;
}
int main(int argc,char**argv){try{if(argc<4){std::cerr<<"Usage: pathtrace native.bin frame.bin out.f32 [threads]\n  Or pathtrace native.bin --stream dummy [threads] then stdin: frame.bin out.f32\n";return 2;}omp_set_num_threads(argc>4?std::stoi(argv[4]):4);auto start=std::chrono::steady_clock::now();Scene scene(argv[1]);std::cout<<"BVH_READY "<<std::chrono::duration<double>(std::chrono::steady_clock::now()-start).count()<<std::endl;
 if(std::string(argv[2])=="--stream"){std::string input,output;while(std::cin>>input>>output){Frame f=readFrame(input);scene.setFrame(f);render(scene,f,output);}}
 else{Frame f=readFrame(argv[2]);scene.setFrame(f);render(scene,f,argv[3]);}return 0;
 }catch(const std::exception&e){std::cerr<<"ERROR: "<<e.what()<<"\n";return 1;}}
