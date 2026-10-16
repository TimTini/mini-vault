const assert = require('node:assert/strict');
const fs = require('node:fs');
const { Model, targets, error } = require('../simulator/mechanism.js');
const actual = JSON.parse(fs.readFileSync('work/physical-dialing-audit.json','utf8'));
assert.equal(new Model([0,1,6],1,'author').measured,false);
for(const fixture of actual.results){
 const m=new Model(fixture.holes,1,'mesh');
 fixture.contact_bands_degrees.forEach((b,i)=>{
  assert.ok(Math.abs(m.low[i]-b[0])<1e-8,'use actual selected-pin contact, not reused default geometry');
  assert.ok(Math.abs(m.high[i]-b[1])<1e-8);
 });
 require('../simulator/mechanism.js').dialTargets(fixture.dial_code,m.low,m.high).forEach(q=>m.move(q));
 assert.equal(m.aligned(),false,'physical-input mismatch must not show ideal success');
 fixture.gate_checks.forEach(g=>assert.ok(Math.abs(error(m.q[4-g.disk])-g.angle_error_degrees)<1e-6));
 const corrected=new Model(fixture.holes,1,'mesh');
 targets(corrected.low,corrected.high,false,-1).forEach(q=>corrected.move(q));
 assert.ok(corrected.aligned());
 fixture.corrected_gate_checks.forEach(g=>assert.ok(g.max_link_overlap_mm3<.001,'measured adjusted-stop fixture must clear sampled link path'));
}
assert.ok(!fs.readFileSync('simulator/app.js','utf8').includes("new Model(holes,scale,'author')"),'UI must not default to ideal contacts after physical mismatch');
const { authorHoles, numbersForHoles, dialTargets } = require('../simulator/mechanism.js');
// Independent reference: MakerWorld original chart, example code13/9/2.
assert.deepEqual(authorHoles([13,9,2]),[5,6,12]);
assert.deepEqual(numbersForHoles([5,6,12]),[13,9,2]);
assert.throws(()=>authorHoles([7,9,2]),/Đĩa 1/);
assert.throws(()=>authorHoles([13,2,2]),/Đĩa 2/);
assert.throws(()=>authorHoles([13,9,5]),/Đĩa 3/);
assert.throws(()=>authorHoles([13.5,9,2]),/nguyên/);
for(let i=0;i<3;i++)for(let h=0;h<15;h++){
 const hs=[5,6,12];hs[i]=h;assert.deepEqual(authorHoles(numbersForHoles(hs)),hs);
}
const authored=new Model([5,6,12]);
const authoredStops=dialTargets([13,9,2],authored.low,authored.high);
assert.ok(authoredStops[0]<0 && authoredStops[1]>authoredStops[0] && authoredStops[2]<authoredStops[1]);
authoredStops.forEach((q,i)=>assert.ok(Math.abs(error(q-[13,9,2][i]*22.5))<1e-6));
const exactCW=targets(authored.low,authored.high,false,-1);exactCW.forEach(q=>authored.move(q));
assert.ok(authored.aligned(),'CW/CCW/CW exact-contact sequence must align the gates');
const illustration=new Model([5,6,12],1,'author');
dialTargets([13,9,2],illustration.low,illustration.high).forEach((q,i)=>{
 illustration.move(q);
 for(let disk=0;disk<=i;disk++)assert.ok(Math.abs(error(illustration.q[3-disk]))<1e-6,'park disks in order1,2,3');
});
assert.ok(illustration.aligned(),'author example must open in illustrative mode');
// Every accepted chart input must produce exactly three monotonic legs CW/CCW/CW.
for(const code of [[13,9,2],[1,1,1],[16,16,16],[8,3,6]]){
 const demo=new Model(authorHoles(code),1,'author');
 const route=dialTargets(code,demo.low,demo.high);
 assert.equal(route.length,3);let previous=0;
 route.forEach((stop,i)=>{assert.equal(Math.sign(stop-previous),[-1,1,-1][i]);assert.ok(Math.abs(error(stop-code[i]*22.5))<1e-6);previous=stop;});
}
const cases = JSON.parse(fs.readFileSync('work/dialing-contact-verification.json','utf8'));
for (const fixture of cases) {
  for (const trial of fixture.exact_trials) {
    const model = new Model([7,3,12],fixture.scale);
    const stops = targets(model.low,model.high);
    for (let i=0;i<3;i++) {
      model.move(stops[i]);
      model.q.forEach((q,j)=>assert.ok(Math.abs(error(q-trial.stages_rear_to_front[i][j]))<1e-5));
    }
    assert.ok(model.aligned());
  }
  const model = new Model([7,3,12],fixture.scale);
  const stops = targets(model.low,model.high,true);
  stops.forEach(q=>model.move(q));
  assert.equal(model.aligned(),false);
  model.q.slice(1).forEach((q,i)=>assert.ok(Math.abs(error(q)-fixture.rounded_trial.disk_angles_degrees_rear_to_front[i])<1e-5));
}
assert.throws(()=>new Model([15,3,12]),/0.*14/);
assert.throws(()=>authorHoles([NaN,3,4]),/số/);
const m=new Model();m.move(1800);const before=m.q.slice();m.move(1799);
assert.deepEqual(m.q.slice(1),before.slice(1),'reversing one degree must preserve followers');
console.log('Verified 2 selected mesh-contact cases and false-success regressions; author13/9/2 chart, 45 hole round trips, unavailable numbers, CW/CCW/CW stops, 20 historical traces and negative controls.');
