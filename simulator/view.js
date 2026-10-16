/* Physical hole indices stay fixed when the observer changes sides. */
(function(root){
  function viewPose(mode,selected,angles){
    if(!['assembly','dial'].includes(mode))throw Error('Unknown view mode');
    if(!Number.isInteger(selected)||selected<0||selected>3)throw Error('Choose disk0..3');
    const assembling=mode==='assembly';
    return {
      angles:assembling?[0,0,0]:angles.slice(),
      visible:[1,2,3].map(d=>!assembling||selected===0||selected===d),
      notch:assembling?'phải':'trái',
      yaw:assembling?(selected?Math.PI:Math.PI-.45):0,
      pitch:assembling&&!selected?.15:0
    };
  }
  function holePoint(hole,mode,radius=55){
    if(!Number.isInteger(hole)||hole<0||hole>14)throw Error('Choose hole0..14');
    const pose=viewPose(mode,0,[0,0,0]),a=(hole-7)*Math.PI/8;
    return {x:(pose.notch==='phải'?-1:1)*radius*Math.cos(a),y:-radius*Math.sin(a)};
  }
  const api={holePoint,viewPose};
  if(typeof module==='object'&&module.exports)module.exports=api;else root.VaultView=api;
})(globalThis);
