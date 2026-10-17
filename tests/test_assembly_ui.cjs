// Actual handlers and animation in a DOM fixture; no WebGL claim.
const assert=require('node:assert/strict'),fs=require('node:fs'),vm=require('node:vm');
const mechanism=require('../simulator/mechanism.js'),view=require('../simulator/view.js');
const html=fs.readFileSync('simulator/index.html','utf8'),elements=new Map();
function element(){return {textContent:'',innerHTML:'',hidden:false,disabled:false,attrs:{},children:[],setAttribute(k,v){this.attrs[k]=v;},replaceChildren(){this.children=[];},append(n){this.children.push(n);}};}
for(const [,id] of html.matchAll(/\bid="([^"]+)"/g))elements.set(id,element());
const get=id=>{assert.ok(elements.has(id),'page element exists: '+id);return elements.get(id);};
for(const [,id,value] of html.matchAll(/<input id="([^"]+)"[^>]*value="([^"]+)"/g))get(id).valueAsNumber=Number(value);
let frame;
const context=vm.createContext({VaultMechanism:mechanism,VaultView:view,window:{},document:{getElementById:get,createElement:element,createTextNode:text=>({textContent:text})},requestAnimationFrame:cb=>frame=cb});
vm.runInContext(fs.readFileSync('simulator/app.js','utf8'),context);
assert.equal(elements.has('correctedPlay'),false,'no fractional-code workaround');
assert.equal(get('assemblyView').attrs['aria-pressed'],'true');
assert.ok(get('holeCards').innerHTML.includes('rãnh bên phải'));
let time=0;
function finish(){for(let i=0;i<400;i++){time+=50;frame(time);}}
for(const [code,holes,visits] of [[[13,5,9],[5,2,3],[4,3,2]],[[13,9,2],[5,6,12],[4,2,2]],[[8,4,12],[0,1,6],[4,2,2]]]) {
  code.forEach((n,i)=>get('n'+(i+1)).valueAsNumber=n);
  get('codeForm').onsubmit({preventDefault(){}});
  assert.deepEqual([1,2,3].map(i=>get('v'+i).valueAsNumber),visits);
  holes.forEach((h,i)=>assert.ok(get('holeCards').innerHTML.includes(`Đĩa ${i+1} · số ${code[i]} · lỗ ${h}`)));
  get('play').onclick();finish();
  assert.equal(get('readout').textContent,code[2].toFixed(3));
  assert.equal(get('status').className,'badge good');
  assert.ok(get('diskErrors').textContent.includes('Đĩa 1: lệch 0.00°'));
  assert.equal(get('stop').disabled,true);
  get('latch').onclick();assert.equal(get('message').textContent,'Thanh gạt đã vào ba rãnh trong mô hình.');
}
get('holeCards').onclick({target:{closest:()=>({dataset:{disk:'3'}})}});
assert.ok(get('viewCaption').textContent.startsWith('Đĩa 3'));
get('dialView').onclick();assert.ok(get('holeCards').innerHTML.includes('rãnh bên trái'));
get('assemblyView').onclick();assert.ok(get('viewCaption').textContent.startsWith('Đĩa 3'));
get('wholeDoor').onclick();assert.ok(get('viewCaption').textContent.startsWith('Toàn bộ'));
[13,5,9].forEach((n,i)=>get('n'+(i+1)).valueAsNumber=n);
[4,2,2].forEach((n,i)=>get('v'+(i+1)).valueAsNumber=n);
get('fixedRoute').onclick();
assert.ok(get('holeCards').innerHTML.includes('Đĩa 1 · số 13 · lỗ 5'),'counts never remap pins');
get('play').onclick();finish();assert.equal(get('status').className,'badge');
for(const code of [[7,5,9],[13,2,9],[13,5,5],[13.5,5,9],[0,5,9]]) {
  code.forEach((n,i)=>get('n'+(i+1)).valueAsNumber=n);
  get('codeForm').onsubmit({preventDefault(){}});
  assert.ok(get('message').textContent.length>0);
  assert.ok(get('holeCards').innerHTML.includes('Đĩa 1 · số 13 · lỗ 5'),'invalid code keeps last valid result');
}
console.log('Verified chart labels, author example/user code replay, latch, manual wrong counts, view controls and invalid input (DOM fixture).');
