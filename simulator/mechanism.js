/* Fixed-band pickup approximation; no friction or elasticity.
   Contacts: work/simulate-dialing.py and work/audit-physical-dialing.py.
   Other hole configurations reuse edge widths: approximate until mesh-checked. */
(function (root) {
  const mod = x => ((x % 360) + 360) % 360;
  const error = x => mod(x + 180) - 180;
  const contacts = {
    1: [[-21.652643214911222,21.87775194644928],[-22.078484129160643,21.61063203588128],[-21.754455231130123,21.997143663465977]],
    1.5: [[-21.653065215796232,21.878009345382452],[-22.078954242169857,21.611152589321136],[-21.754944697022438,21.99751501902938]]
  };
  // Current200mesh, remeasured selected holes; work/physical-dialing-audit.json.
  const selectedContacts={
    '0,1,6':[[-134.34016960673034,-90.75355953536928],[-134.3548301141709,-90.64536564983428],[-44.35447895899415,-.6453706324100494]],
    '8,4,12':[[.8473567571491003,44.37775196507573],[-201.85435141436756,-158.14517193473876],[68.14564579166472,111.85479113832116]]
  };
  function bands(holes,scale=1,basis='mesh') {
    if (holes.length!==3 || holes.some(h=>!Number.isInteger(h)||h<0||h>14)) throw Error('Lỗ phải là số nguyên 0 đến 14.');
    if (!contacts[scale]) throw Error('Tỷ lệ hỗ trợ: 1 hoặc 1.5.');
    if(!['mesh','author'].includes(basis))throw Error('Chọn mô hình author hoặc mesh.');
    if(basis==='mesh'&&scale===1&&selectedContacts[holes.join(',')])return selectedContacts[holes.join(',')].map(x=>x.slice());
    const a=[90,...holes.slice().reverse().map(h=>(h-7)*22.5)];
    return contacts[scale].map((e,i)=>(basis==='author'?[-22.5,22.5]:e).map(v=>v+a[i+1]-a[i]));
  }
  function stopsForPhases(phases,low,high,direction) {
    const span=low.map((x,i)=>360-(high[i]-x));
    const first=direction>0?phases[0]+1800:phases[0]-2160;
    let d=mod(direction*(first-phases[1]));while(d<span[0]+span[1]-1e-6)d+=360;
    const second=first-direction*d;
    d=mod(direction*(phases[2]-second));while(d<span[0]-1e-6)d+=360;
    return [first,second,second+direction*d];
  }
  function targets(low,high,rounded=false,direction=1) {
    let phases=(direction>0?[low.reduce((a,b)=>a+b,0),high[0]+high[1],low[0]]:
      [high.reduce((a,b)=>a+b,0),low[0]+low[1],high[0]]).map(mod);
    if (rounded) phases=phases.map(x=>Math.round(x/22.5)*22.5);
    return stopsForPhases(phases,low,high,direction);
  }
  // Author chart is viewed from the back, notch right. Our drawing is front,
  // notch left: mirror X before assigning the SCAD hole index.
  const offsets=[8,3,6];
  function numbersForHoles(holes) {
    bands(holes);
    return holes.map((h,i)=>(h+offsets[i])%16||16);
  }
  function authorHoles(numbers) {
    if(numbers.length!==3||numbers.some(n=>!Number.isInteger(n)||n<1||n>16))throw Error('Nhập ba số nguyên trên núm, từ 1 đến 16.');
    return numbers.map((n,i)=>{
      const h=(n-offsets[i]+16)%16;
      if(h===15)throw Error(`Đĩa ${i+1}: số ${n} nằm tại rãnh mở, không có lỗ đặt chốt. Chọn số khác.`);
      return h;
    });
  }
  function dialTargets(numbers,low,high) {
    validateNumbers(numbers);
    return stopsForPhases(numbers.map(n=>mod(n*22.5)),low,high,-1);
  }
  function validateNumbers(numbers) {
    if(numbers.length!==3||numbers.some(n=>!Number.isFinite(n)||n<1||n>16))throw Error('Nhập ba số trên núm, từ 1 đến 16.');
  }
  function visitTargets(numbers,visits) {
    validateNumbers(numbers);
    if(visits.length!==3||visits.some(n=>!Number.isInteger(n)||n<1||n>10))throw Error('Nhập ba lượt gặp số nguyên, từ 1 đến 10.');
    let previous=0;
    return numbers.map((n,i)=>{
      const direction=[-1,1,-1][i];
      const first=mod(direction*(n*22.5-previous))||360;
      previous+=direction*(first+360*(visits[i]-1));
      return previous;
    });
  }
  function describeVisits(numbers,stops) {
    return stops.map((q,i)=>{
      const previous=i?stops[i-1]:0,direction=[-1,1,-1][i];
      const first=mod(direction*(numbers[i]*22.5-previous))||360;
      return 1+Math.round((Math.abs(q-previous)-first)/360);
    });
  }
  class Model {
    constructor(holes=[7,3,12],scale=1,basis='mesh') {
      this.basis=basis;
      this.measured=basis==='mesh'&&scale===1&&Object.hasOwn(selectedContacts,holes.join(','));
      const b=bands(holes,scale,basis);this.low=b.map(x=>x[0]);this.high=b.map(x=>x[1]);
      this.span=b.map(x=>360-(x[1]-x[0]));this.q=[0];this.pulling=[false,false,false];
      for(let i=0;i<3;i++)this.q.push(this.q[i]-this.high[i]-this.span[i]/2);
    }
    move(target) {
      // A monotone move crosses each pickup edge once. Keep the full unwrapped
      // travel, clamp the free gap, then propagate actual motion to the next disk.
      const old=this.q.slice();this.q[0]=target;
      for(let i=0;i<3;i++) {
        let gap=mod(old[i]-old[i+1]-this.high[i]);if(gap>360-1e-7)gap=0;
        const proposed=gap+this.q[i]-old[i];
        this.pulling[i]=proposed<0||proposed>this.span[i];
        if(proposed>this.span[i])this.q[i+1]=old[i+1]+proposed-this.span[i];
        else if(proposed<0)this.q[i+1]=old[i+1]+proposed;
      }
    }
    aligned() {return this.q.slice(1).every(q=>Math.abs(error(q))<.25);}
  }
  function solveCode(numbers,scale=1,visits=null) {
    validateNumbers(numbers);
    const explicitStops=visits?visitTargets(numbers,visits):null;
    let best=null,matches=0;
    function inspect(holes) {
      const model=new Model(holes,scale),stages=[];
      (explicitStops||dialTargets(numbers,model.low,model.high)).forEach((q,stage)=>{
        model.move(q);
        stages.push(model.q.slice(1).reverse().slice(0,stage+1).map(error));
      });
      return {stageErrors:stages,maxStageError:Math.max(...stages.flat().map(Math.abs))};
    }
    for(let a=0;a<15;a++)for(let b=0;b<15;b++)for(let c=0;c<15;c++) {
      const holes=[a,b,c],model=new Model(holes,scale);
      const predicted=targets(model.low,model.high,false,-1);
      const stopErrors=predicted.map((q,i)=>error(q-numbers[i]*22.5));
      const maxStopError=Math.max(...stopErrors.map(Math.abs));
      const stageCheck=explicitStops||maxStopError<.25?inspect(holes):null;
      const match=stageCheck!==null&&stageCheck.maxStageError<.25;
      if(match)matches++;
      const score=explicitStops?stageCheck.maxStageError:maxStopError;
      if(!best||(match&&!best.matches)||(match===best.matches&&score<best.score)) {
        best={holes,predictedNumbers:predicted.map(q=>mod(q)/22.5||16),stopErrors,maxStopError,
              measured:model.measured,matches:match,score,...stageCheck};
      }
    }
    if(!best.stageErrors)Object.assign(best,inspect(best.holes));
    return {...best,tested:3375,matchingCandidates:matches,...(visits?{visits:visits.slice(),stops:explicitStops}:{} )};
  }
  function planCode(numbers,scale=1) {
    // Four first encounters clear all three pickup gaps, even from unknown phases.
    // Later legs need at most three / two encounters; extra turns drag set disks.
    let best=null;
    for(let second=1;second<=3;second++)for(let third=1;third<=2;third++) {
      const candidate=solveCode(numbers,scale,[4,second,third]);
      if(!best||candidate.maxStageError<best.maxStageError-1e-7||
        (Math.abs(candidate.maxStageError-best.maxStageError)<1e-7&&candidate.maxStopError<best.maxStopError-1e-7))best=candidate;
    }
    return best;
  }
  function authorGuide(numbers,visits=null) {
    const holes=authorHoles(numbers),model=new Model(holes,1,'author');
    if(visits===null) {
      visits=describeVisits(numbers,dialTargets(numbers,model.low,model.high));
      visits[0]=4;
    }
    const stops=visitTargets(numbers,visits),stageErrors=[];
    stops.forEach((stop,i)=>{
      model.move(stop);
      stageErrors.push(model.q.slice(1).reverse().slice(0,i+1).map(error));
    });
    return {holes,visits:visits.slice(),stops,matches:stageErrors.flat().every(e=>Math.abs(e)<.25)};
  }
  const api={Model,targets,bands,error,mod,authorHoles,numbersForHoles,dialTargets,solveCode,planCode,authorGuide,visitTargets,describeVisits};
  if(typeof module==='object'&&module.exports)module.exports=api;else root.VaultMechanism=api;
})(globalThis);
