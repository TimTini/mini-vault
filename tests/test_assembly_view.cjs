const assert=require('node:assert/strict');
const {holePoint,viewPose}=require('../simulator/view.js');
const eps=1e-9;
for(let h=0;h<15;h++){
 const front=holePoint(h,'dial'),rear=holePoint(h,'assembly');
 assert.ok(Math.abs(front.x+rear.x)<eps,'same physical hole mirrors horizontally when viewed from inside');
 assert.ok(Math.abs(front.y-rear.y)<eps,'top remains top');
}
assert.ok(holePoint(7,'dial').x>0);
assert.ok(holePoint(7,'assembly').x<0);
const moving=[21,-45,97],original=moving.slice();
const assembly=viewPose('assembly',2,moving);
assert.deepEqual(assembly.angles,[0,0,0],'assembly guide must stay at notch datum after dialing');
assert.deepEqual(assembly.visible,[false,true,false]);
assert.equal(assembly.notch,'phải');
assert.ok(Math.cos(assembly.yaw)<0,'camera must look from interior towards door');
const dial=viewPose('dial',2,moving);
assert.deepEqual(dial.angles,moving);
assert.deepEqual(dial.visible,[true,true,true]);
assert.equal(dial.notch,'trái');
assert.ok(Math.cos(dial.yaw)>0);
assert.deepEqual(moving,original,'changing view must preserve physical simulation state');
assert.deepEqual(viewPose('assembly',0,moving).visible,[true,true,true]);
assert.throws(()=>holePoint(15,'assembly'));
assert.throws(()=>viewPose('other',1,moving));
assert.throws(()=>viewPose('assembly',4,moving));
console.log('Verified front/rear physical-hole projection, fixed top, neutral assembly poses, persistent disk indices and simulation-state preservation.');
