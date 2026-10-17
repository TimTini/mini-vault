const assert=require('node:assert/strict');
const {planCode,Model,targets,error}=require('../simulator/mechanism.js');
for(const code of [[13,5,9],[8,4,12],[16,16,16]]) {
  const plan=planCode(code);
  assert.ok(plan.maxStageError<2.1,`reasonable route for ${code}`);
  if(code[0]===13) {
    assert.deepEqual(plan.holes,[5,2,3]);
    assert.deepEqual(plan.visits,[4,3,2]);
    assert.equal(plan.matches,false,'integer code must not become a false positive');
  }
  const model=new Model(plan.holes);
  targets(model.low,model.high,false,-1).forEach(stop=>model.move(stop));
  assert.ok(model.aligned(),`corrected contact route opens ${code}`);
  assert.ok(model.q.slice(1).every(q=>Math.abs(error(q))<1e-6));
}
assert.throws(()=>planCode([0,5,9]));
console.log('Verified automatic visits, 13/5/9 pins, honest integer mismatch and corrected replay.');
