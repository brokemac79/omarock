const fs=require('node:fs'),vm=require('node:vm'),assert=require('node:assert/strict');
const ctx={};vm.createContext(ctx);vm.runInContext(fs.readFileSync('RoomGeometry.js','utf8'),ctx);
const mask={coordinateFrame:'cropped-image-pixels',rooms:[{id:16,rects:[[0,0,10,2],[0,2,2,8]]},{id:17,rects:[[20,0,5,5]]}]};
const rooms=[{id:16},{id:17}],pick=(x,y,m=mask,r=rooms)=>ctx.roomAt(m,r,x,y);
assert.equal(pick(1,8),16);assert.equal(pick(8,8),null); // concavity, not bounding box
assert.equal(pick(22,2),17);assert.equal(pick(10,1),null); // half-open boundary
assert.equal(pick(-1,0),null);assert.equal(pick(NaN,0),null);
assert.equal(pick(1,1,null),null);assert.equal(pick(1,1,mask,[]),null);
assert.equal(pick(1,1,{...mask,coordinateFrame:'raw'}),null);
assert.equal(pick(1,1,{...mask,rooms:[...mask.rooms,{id:17,rects:[[0,0,2,2]]}]}),null);
console.log('10 exact-cell picking assertions passed');
