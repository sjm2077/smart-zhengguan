
(function(){
'use strict';

const routeDept={
  '/dept/science/':'科学社会主义系',
  '/dept/political/':'政治学系',
  '/dept/international/':'国际政治系',
  '/dept/public/':'公共管理系'
};
const dept=routeDept[location.pathname];
if(!dept || typeof echarts==='undefined')return;

function go(type,extra){
  const p=new URLSearchParams({type,dept,...extra});
  location.href=`/research-query/?${p.toString()}`;
}
function chart(id){
  const el=document.getElementById(id);
  return el?echarts.getInstanceByDom(el):null;
}
function mark(id){
  const el=document.getElementById(id);
  if(el)el.style.cursor='pointer';
}
function bind(id,handler){
  const el=document.getElementById(id);if(!el||el.dataset.drilldownBound==='1')return;
  const c=chart(id);if(!c)return;
  c.on('click',handler);el.dataset.drilldownBound='1';mark(id);
}
function selectedYear(){
  const el=document.getElementById('year');return el&&el.value&&el.value!=='all'?el.value:'';
}
function init(){
  if(location.pathname==='/dept/science/'){
    bind('pie-type',p=>go('achievement',{achievement_type:p.name,year:selectedYear()}));
    bind('bar-level',p=>go('project',{project_type:p.name,year:selectedYear()}));
    bind('line-trend',p=>go('achievement',{year:String(p.name),achievement_type:p.seriesName||''}));
  }
  if(location.pathname==='/dept/political/'){
    bind('fundLineChart',p=>go('project',{fund_year:String(p.name)}));
    bind('ringChart',p=>go('achievement',{achievement_type:p.name,year:selectedYear()}));
    bind('sourceBarChart',p=>go('achievement',{achievement_level:p.name,year:selectedYear()}));
  }
  if(location.pathname==='/dept/international/'){
    bind('lineDoubleChart',p=>go('project',{fund_year:String(p.name)}));
    bind('ringDonutChart',p=>go('achievement',{achievement_type:p.name,international:'true',year:selectedYear()}));
  }
  if(location.pathname==='/dept/public/'){
    bind('lineTrendChart',p=>go('project',{fund_year:String(p.name)}));
    bind('pieSourceChart',p=>go('project',{fund_source:p.name,year:selectedYear()}));
    bind('resultCompareChart',p=>go('achievement',{year:String(p.name),achievement_type:p.seriesName||''}));
  }
}
window.addEventListener('load',()=>setTimeout(init,800));
setTimeout(init,1600);
})();