const assert=require('node:assert/strict');
const {authorGuide,numbersForHoles,Model}=require('../simulator/mechanism.js');
for(const [numbers,holes,visits] of [
  [[13,5,9],[5,2,3],[4,3,2]],
  [[13,9,2],[5,6,12],[4,2,2]],
  [[8,4,12],[0,1,6],[4,2,2]]
]) {
  const guide=authorGuide(numbers);
  assert.deepEqual(guide.holes,holes);
  assert.deepEqual(guide.visits,visits);
  const model=new Model(holes,1,'author');
  guide.stops.forEach(stop=>model.move(stop));
  assert.ok(model.aligned());
  assert.equal(guide.matches,true);
}
const wrong=authorGuide([13,5,9],[4,2,2]);
assert.deepEqual(wrong.holes,[5,2,3],'manual counts never change chart pin positions');
assert.equal(wrong.matches,false);
for(const code of [[7,5,9],[13,2,9],[13,5,5],[13.5,5,9]])assert.throws(()=>authorGuide(code));
let tested=0;
for(let a=1;a<=16;a++)for(let b=1;b<=16;b++)for(let c=1;c<=16;c++) {
  if(a===7||b===2||c===5)continue;
  assert.deepEqual(numbersForHoles(authorGuide([a,b,c]).holes),[a,b,c]);
  tested++;
}
assert.equal(tested,3375);
assert.equal(authorGuide([1,1,4]).matches,false,'chart lookup alone does not certify a route that drags a previously set disk');
console.log('Verified author chart, example13/9/2, user13/5/9, 3->2->1 routes, invalid holes and manual-count rejection.');
