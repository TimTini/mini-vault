'use strict';
const $=id=>document.getElementById(id);
const {Model,authorGuide,numbersForHoles,visitTargets,error,mod}=VaultMechanism;
const {holePoint,viewPose}=VaultView;
let numbers=[13,5,9],solution=authorGuide(numbers),visits=solution.visits,holes=solution.holes;
let planned=solution.stops,routeStart=0;
let model=new Model(holes,1,'author'),mode='assembly',selectedDisk=1,queue=[],inserted=false,last=0,pauseUntil=0;
let renderMechanism=()=>{},rebuild=()=>{};
const colors=['#60c5f0','#ae90fa','#f6b46a'];
function showSolution(){
  const box=$('suggestion');box.className=solution.matches?'result good':'result';
  const title=solution.matches?'Vị trí chốt theo bảng tác giả.':'Vị trí chốt theo bảng tác giả; chuỗi quay này chưa khớp trong mô hình hướng dẫn. Hãy thử mã khi cửa còn mở.';
  box.replaceChildren();const strong=document.createElement('strong');strong.textContent=title;box.append(strong);
  box.append(document.createTextNode(`Mã giữ nguyên: ${numbers.join(' → ')}. Chốt đĩa 1 / 2 / 3: lỗ ${holes.join(' / ')}.`));
  $('precision').textContent='Tra vị trí chốt trực tiếp theo bảng tác giả. Animation minh họa truyền động lý tưởng theo quy tắc 3 → 2 → 1 đĩa; không mô phỏng lực, ma sát hay dung sai bản in.';
  $('route').innerHTML=numbers.map((n,i)=>`<li>${['⭮','⭯','⭮'][i]} ${['Quay đến khi cả ba đĩa cùng quay','Đảo chiều đến khi đĩa 2 và 3 cùng quay','Đảo chiều đến khi chỉ đĩa 3 quay'][i]}, tiếp tục đến <b>${n}</b>. Từ mốc 16 theo chuỗi này: lần thứ ${visits[i]} · ${Math.abs(planned[i]-(i?planned[i-1]:0)).toFixed(1)}°.</li>`).join('');
}
function drawCards(){
  const pose=viewPose(mode,selectedDisk,[0,0,0]);
  $('holes-title').textContent=`Vị trí chốt theo tác giả — nhìn từ ${mode==='assembly'?'mặt trong':'bên ngoài'}`;
  $('assemblyInstruction').textContent=mode==='assembly'?'Mặt có đầu lớn hướng về bạn. Giữ rãnh bên phải, đặt chốt vào lỗ màu vàng. Lắp đĩa 1 sát cửa → đĩa 2 → đĩa 3.':'Góc nhìn theo núm ngoài: rãnh ở bên trái. Chọn một đĩa để trở lại hướng dẫn lắp từ mặt trong.';
  $('holeCards').innerHTML=holes.map((h,i)=>{
    let circles='';
    for(let j=0;j<15;j++){
      const p=holePoint(j,mode),t=holePoint(j,mode,73),number=numbersForHoles([j,j,j])[i];
      circles+=`<circle cx="${90+p.x}" cy="${90+p.y}" r="6" fill="${j===h?'#ffe18d':'#101923'}" stroke="${j===h?'#fff2b9':colors[i]}"/><text x="${90+t.x}" y="${94+t.y}" fill="${j===h?'#ffe18d':'#aab9cd'}" font-size="10" text-anchor="middle">${number}</text>`;
    }
    const notch=pose.notch==='phải'?'M158 84H144V96H158':'M22 84H36V96H22';
    return `<button type="button" class="hole-card" data-disk="${i+1}" aria-pressed="${mode==='assembly'&&selectedDisk===i+1}" aria-label="Lắp đĩa ${i+1}, số ${numbers[i]}, lỗ ${h}"><b style="color:${colors[i]}">Đĩa ${i+1} · số ${numbers[i]} · lỗ ${h}</b><svg viewBox="0 0 180 180" role="img" aria-label="Đĩa ${i+1}, lỗ ${h}, rãnh bên ${pose.notch}"><circle cx="90" cy="90" r="66" fill="${colors[i]}" fill-opacity=".16" stroke="${colors[i]}"/><path d="${notch}" fill="#101923" stroke="${colors[i]}"/><circle cx="90" cy="90" r="20" fill="#101923" stroke="${colors[i]}"/>${circles}</svg><small>${['Sát cửa','Ở giữa','Trong cùng'][i]}</small></button>`;
  }).join('');
}
function update(){
  const aligned=model.aligned();
  $('assemblyView').setAttribute('aria-pressed',String(mode==='assembly'));
  $('dialView').setAttribute('aria-pressed',String(mode==='dial'));
  $('dialStatus').hidden=mode!=='dial';
  $('wholeDoor').hidden=mode!=='assembly';
  $('wholeDoor').setAttribute('aria-pressed',String(selectedDisk===0));
  $('viewCaption').textContent=mode==='assembly'?(selectedDisk?`Đĩa ${selectedDisk} · ${['sát cửa','ở giữa','trong cùng'][selectedDisk-1]}. Nhìn từ trong thân về phía cửa: đầu lớn màu vàng hướng về bạn; rãnh ở bên phải. Các đĩa khác đang ẩn để dễ đặt chốt.`:'Toàn bộ mặt trong nắp và vị trí cụm đĩa. Các đĩa ở tư thế mốc đặt chốt; chọn từng đĩa để xem gần.'):'Nhìn từ ngoài cửa vào núm. Chiều mở khóa: ⭮ → ⭯ → ⭮. Số đĩa và số lỗ giữ nguyên.';
  $('status').textContent=aligned?'Ba rãnh khớp trong mô hình':'Rãnh còn lệch — chưa mở được';
  $('status').className=aligned?'badge good':'badge';
  $('readout').textContent=(mod(model.q[0])/22.5||16).toFixed(3);
  const stage=3-queue.length;
  const traveled=Math.abs(model.q[0]-routeStart),phaseTravel=queue.length?Math.abs(planned[stage]-routeStart)-360*(visits[stage]-1):0;
  const passed=queue.length&&traveled>=phaseTravel-1e-6?Math.min(visits[stage],1+Math.floor((traveled-phaseTravel+1e-6)/360)):0;
  $('stage').textContent=queue.length?`Chặng ${stage+1}/3 · ${['⭮','⭯','⭮'][stage]} đến ${numbers[stage]} lần ${visits[stage]} · đã gặp ${passed}/${visits[stage]} lần`:'⭮ → ⭯ → ⭮ · nhìn từ bên ngoài';
  $('diskErrors').textContent=model.q.slice(1).reverse().map((q,i)=>`Đĩa ${i+1}: lệch ${error(q).toFixed(2)}°`).join(' · ');
  $('stop').disabled=queue.length===0;
  renderMechanism();
}
function changeView(next,disk=selectedDisk){
  mode=next;selectedDisk=disk;queue=[];inserted=false;
  drawCards();update();
}
function reset(){model=new Model(holes,1,'author');queue=[];inserted=false;update();}
function apply(auto=false){
  const next=[1,2,3].map(i=>$('n'+i).valueAsNumber);
  const nextVisits=[1,2,3].map(i=>$('v'+i).valueAsNumber);
  try{
    const proposal=authorGuide(next,auto?null:nextVisits);
    numbers=next;visits=proposal.visits;solution=proposal;holes=proposal.holes;planned=proposal.stops;
    if(auto)visits.forEach((n,i)=>{$('v'+(i+1)).value=n;$('v'+(i+1)).valueAsNumber=n;});
    reset();rebuild();
    showSolution();drawCards();update();$('message').textContent='';return true;
  }catch(e){$('message').textContent=e.message;return false;}
}
$('codeForm').onsubmit=e=>{e.preventDefault();if(apply(true))changeView('assembly',1);};
$('fixedRoute').onclick=()=>{if(apply())changeView('assembly',1);};
$('assemblyView').onclick=()=>changeView('assembly');
$('dialView').onclick=()=>changeView('dial');
$('wholeDoor').onclick=()=>changeView('assembly',0);
$('holeCards').onclick=e=>{const card=e.target.closest('button[data-disk]');if(card)changeView('assembly',Number(card.dataset.disk));};
$('play').onclick=()=>{
  if(!apply())return;mode='dial';inserted=false;pauseUntil=0;
  planned=visitTargets(numbers,visits);queue=planned.slice();routeStart=0;drawCards();update();
  $('message').textContent=`Đang thử đúng mã ${numbers.join(' → ')} từ phía núm ngoài.`;
};
$('stop').onclick=()=>{queue=[];$('message').textContent='Đã dừng thử mã.';update();};
$('latch').onclick=()=>{
  if(model.aligned()){inserted=!inserted;$('message').textContent=inserted?'Thanh gạt đã vào ba rãnh trong mô hình.':'Đã rút thanh gạt.';}
  else $('message').textContent='Thanh gạt bị chặn vì các rãnh còn lệch.';
  update();
};
function init3D(){
  const host=$('scene'),T=window.THREE;
  if(!T)throw Error('Chưa tải được Three.js. Giữ thư mục vendor bên cạnh HTML.');
  if(!window.VaultContextMeshes)throw Error('Thiếu context-meshes.js chứa mặt trong cửa.');
  const renderer=new T.WebGLRenderer({antialias:true,alpha:true});renderer.setPixelRatio(Math.min(devicePixelRatio,2));host.appendChild(renderer.domElement);
  const scene=new T.Scene(),camera=new T.PerspectiveCamera(36,1,.1,1500);
  scene.add(new T.HemisphereLight(0xcde7ff,0x334053,2.4));
  for(const [x,z] of [[50,100],[-50,-100]]){const light=new T.DirectionalLight(0xffffff,2);light.position.set(x,70,z);scene.add(light);}
  const root=new T.Group();scene.add(root);
  let disks=[],context=[],door,driver,dial,bar,pointer,zoom=1;
  function material(color,extra={}){return new T.MeshStandardMaterial({color,roughness:.55,metalness:.12,...extra});}
  function cylinder(radius,depth,mat){const m=new T.Mesh(new T.CylinderGeometry(radius,radius,depth,48),mat);m.rotation.x=Math.PI/2;return m;}
  rebuild=()=>{
    root.traverse(o=>{if(o.geometry)o.geometry.dispose();if(o.material){if(o.material.map)o.material.map.dispose();o.material.dispose();}});
    root.clear();disks=[];context=[];
    const source=window.VaultContextMeshes['1'];
    if(!source)throw Error('Thiếu mesh mặt cửa cho bản đã chọn.');
    for(const [name,data] of Object.entries(source.parts)){
      const geometry=new T.BufferGeometry();geometry.setAttribute('position',new T.Float32BufferAttribute(data.positions,3));geometry.setIndex(data.indices);geometry.computeVertexNormals();geometry.computeBoundingBox();
      const mesh=new T.Mesh(geometry,material(name==='door'?'#536575':name==='shaft'?'#a6b8c4':'#79908b',{flatShading:true}));
      root.add(mesh);context.push({name,mesh});if(name==='door')door=mesh;
    }
    for(let i=0;i<3;i++){
      const group=new T.Group(),s=new T.Shape(),r=17.5,a=Math.asin(1.5/r);
      s.moveTo(-14,-1.5);s.lineTo(-Math.sqrt(r*r-2.25),-1.5);
      for(let k=0;k<=128;k++){const t=Math.PI+a+(2*Math.PI-2*a)*k/128;s.lineTo(r*Math.cos(t),r*Math.sin(t));}
      s.lineTo(-14,1.5);s.closePath();
      const bore=new T.Path();bore.absarc(0,0,4.8,0,Math.PI*2,true);s.holes.push(bore);
      for(let h=0;h<15;h++){const t=(h-7)*Math.PI/8,p=new T.Path();p.absarc(13.5*Math.cos(t),13.5*Math.sin(t),1.6,0,Math.PI*2,true);s.holes.push(p);}
      const plate=new T.Mesh(new T.ExtrudeGeometry(s,{depth:2,bevelEnabled:false,curveSegments:24}),material(colors[i]));plate.position.z=-2;group.add(plate);
      // Scene +Z faces the outside; the large head stays behind the disk.
      const aPin=(holes[i]-7)*Math.PI/8,head=cylinder(3.6,2,material('#ffe18d')),stem=cylinder(1.55,4,material('#6ed9ed'));
      head.position.set(13.5*Math.cos(aPin),13.5*Math.sin(aPin),-3);stem.position.set(head.position.x,head.position.y,0);group.add(head,stem);
      root.add(group);disks.push(group);
    }
    driver=new T.Group();const rim=cylinder(19.5,2,material('#74908b'));rim.position.z=-2;driver.add(rim);const peg=cylinder(1.5,2,material('#ffe18d'));peg.position.set(0,13.5,0);driver.add(peg);root.add(driver);
    dial=new T.Group();const face=cylinder(31,3,material('#28454e'));face.position.z=-1.5;dial.add(face);
    const grip=cylinder(8,8,material('#8ab9bd'));grip.position.z=4;dial.add(grip);
    for(let n=1;n<=16;n++){
      const a=n*Math.PI/8,canvas=document.createElement('canvas');canvas.width=128;canvas.height=128;
      const ctx=canvas.getContext('2d');ctx.fillStyle='#f1f8ed';ctx.font='bold 60px system-ui';ctx.textAlign='center';ctx.textBaseline='middle';ctx.fillText(String(n),64,64);
      const label=new T.Sprite(new T.SpriteMaterial({map:new T.CanvasTexture(canvas),depthTest:false}));label.scale.set(4,4,1);label.position.set(25*Math.sin(a),25*Math.cos(a),1);dial.add(label);
      const tick=new T.Mesh(new T.BoxGeometry(.5,2,.4),material('#b1d5ce'));tick.position.set(29*Math.sin(a),29*Math.cos(a),.4);tick.rotation.z=-a;dial.add(tick);
    }
    root.add(dial);pointer=new T.Mesh(new T.ConeGeometry(1.7,4,3),material('#71e7b4'));pointer.rotation.z=Math.PI;pointer.position.set(0,35,9);root.add(pointer);
    bar=new T.Mesh(new T.BoxGeometry(14,2.3,14),material('#f08d71'));root.add(bar);
  };
  renderMechanism=()=>{
    const pose=viewPose(mode,selectedDisk,model.q.slice(1).reverse());
    disks.forEach((group,i)=>{group.position.z=-i*5;group.rotation.z=pose.angles[i]*Math.PI/180;group.visible=pose.visible[i];});
    context.forEach(({name,mesh})=>{mesh.visible=name==='door'||mode==='dial'||selectedDisk===0||name==='shaft'||Number(name.slice(-1))<=selectedDisk;if(name==='shaft')mesh.rotation.z=mode==='dial'?model.q[0]*Math.PI/180:0;});
    driver.position.z=-14;driver.rotation.z=mode==='dial'?model.q[0]*Math.PI/180:0;driver.visible=mode==='dial'||selectedDisk===0;
    dial.position.z=8;dial.rotation.z=model.q[0]*Math.PI/180;dial.visible=mode==='dial';pointer.visible=mode==='dial';
    bar.position.set(inserted?-21:-29,0,-5);bar.visible=mode==='dial';bar.material.color.set(model.aligned()?'#71e7b4':'#f08d71');
    let center=new T.Vector3(0,0,mode==='assembly'?-(selectedDisk-1)*5:8),distance=mode==='assembly'?85:125;
    if(mode==='assembly'&&selectedDisk===0){const bounds=door.geometry.boundingBox;bounds.getCenter(center);const size=new T.Vector3();bounds.getSize(size);distance=Math.max(size.x,size.y)*1.9;}
    distance*=zoom*Math.max(1,host.clientHeight/Math.max(host.clientWidth,1));
    camera.position.set(center.x+Math.sin(pose.yaw)*Math.cos(pose.pitch)*distance,center.y+Math.sin(pose.pitch)*distance,center.z+Math.cos(pose.yaw)*Math.cos(pose.pitch)*distance);camera.lookAt(center);
    renderer.setSize(host.clientWidth,host.clientHeight,false);camera.aspect=host.clientWidth/Math.max(host.clientHeight,1);camera.updateProjectionMatrix();renderer.render(scene,camera);
  };
  renderer.domElement.addEventListener('wheel',e=>{e.preventDefault();zoom=Math.max(.6,Math.min(2,zoom+e.deltaY*.001));renderMechanism();},{passive:false});
  new ResizeObserver(renderMechanism).observe(host);rebuild();
}
try{init3D();}catch(e){$('fatal').textContent='Không hiển thị được mô hình: '+e.message;}
showSolution();drawCards();update();
function frame(time){
  const dt=last?Math.min((time-last)/1000,.05):0;last=time;
  if(queue.length&&time>=pauseUntil){
    const target=queue[0],d=target-model.q[0],step=900*dt;
    model.move(Math.abs(d)<=step?target:model.q[0]+Math.sign(d)*step);
    if(Math.abs(target-model.q[0])<1e-6){queue.shift();routeStart=target;pauseUntil=time+1000;if(!queue.length)$('message').textContent=model.aligned()?'Hoàn tất ⭮ ⭯ ⭮: ba rãnh khớp trong mô hình hướng dẫn tác giả.':'Hoàn tất đúng lượt đã chọn: rãnh còn lệch; kiểm tra lại lượt quay 3 → 2 → 1 đĩa.';}
    update();
  }
  requestAnimationFrame(frame);
}
requestAnimationFrame(frame);
