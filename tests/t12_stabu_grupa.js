const L=require('./lib.js');
(async()=>{const S=__dirname+'/modeli/';
const html=L.build(S+'lievenis-stabi.json');const {browser,page,errs}=await L.open(html);
const m=await L.model(page);const p0=m.posts[0],p1=m.posts[1];
await L.click(page,'plan',p0.x+p0.w/2,p0.y+p0.d/2);
console.log('sel1',JSON.stringify(await L.sel(page)));
await page.keyboard.down('Shift');await L.click(page,'plan',p1.x+p1.w/2,p1.y+p1.d/2);await page.keyboard.up('Shift');
const s=await L.sel(page);console.log('sel2',JSON.stringify(s));
L.ok(s&&s.more&&s.more.length===1,'grupa 2 stabi');
await page.keyboard.press('Delete');await L.ready(page);
const m2=await L.model(page);L.ok(m2.posts.length===m.posts.length-2,'abi dzēsti',m2.posts.length);
L.done(errs);await browser.close()})()
