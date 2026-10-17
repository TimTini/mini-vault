const assert=require('node:assert/strict');
const {Model,planCode}=require('../simulator/mechanism.js');
// Endpoint clamping must equal fine stepping through every direction reversal.
for(const holes of [[5,2,3],[0,1,6],[14,0,14]]) {
  const direct=new Model(holes),stepped=new Model(holes);
  for(const target of [-1147.5,-247.5,-877.5,2345,-100,0,-4000]) {
    direct.move(target);
    const start=stepped.q[0],count=Math.ceil(Math.abs(target-start)/.37);
    for(let k=1;k<=count;k++)stepped.move(start+(target-start)*k/count);
    direct.q.forEach((q,i)=>assert.ok(Math.abs(q-stepped.q[i])<1e-7));
  }
}
const start=performance.now();
planCode([13,5,9]);
const elapsed=performance.now()-start;
assert.ok(elapsed<1000,`auto search should avoid per-degree simulation; took ${elapsed.toFixed(0)}ms`);
console.log(`Verified monotone pickup clamping against fine stepping; auto search ${elapsed.toFixed(0)}ms.`);
