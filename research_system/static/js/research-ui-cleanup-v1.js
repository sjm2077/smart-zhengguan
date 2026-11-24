(function(){
'use strict';

const internalPhrases = [
  '点击图表下钻',
  '当前为指定教师画像模式',
  '演示数据',
  '模拟演示数据',
  '仅作演示',
  '图表不会补造缺失指标',
  '不代表真实绩效考核',
  '不代表真实合作事实',
  '当前数据模型未建立',
  '现有 Achievement 数据模型没有 Project 外键',
  '当前不推测该成果属于哪个科研项目'
];

function containsInternal(text){
  const value=(text||'').replace(/\s+/g,' ').trim();
  return internalPhrases.some(p=>value.includes(p));
}

function clean(root=document){
  // 只删除纯展示型徽标；绝不删除业务结构节点。
  root.querySelectorAll('.drilldown-badge').forEach(el=>el.remove());
  root.querySelectorAll('.teacher-direct-label').forEach(el=>el.remove());

  // 对业务脚本可能继续使用的状态节点，只清空内部说明文字，不删除节点。
  root.querySelectorAll('.profile-status,.status-note,.data-note,.demo-note,.internal-note').forEach(el=>{
    if(containsInternal(el.textContent)){
      el.textContent='';
      el.style.display='none';
    }
  });
}

function observe(){
  const obs=new MutationObserver(mutations=>{
    mutations.forEach(m=>{
      const target=m.target.nodeType===1?m.target:m.target.parentElement;
      if(!target)return;
      const holder=target.closest?.('.profile-status,.status-note,.data-note,.demo-note,.internal-note');
      if(holder){
        if(containsInternal(holder.textContent)){
          holder.textContent='';
          holder.style.display='none';
        }else if((holder.textContent||'').trim()){
          holder.style.display='';
        }
      }
    });
  });
  obs.observe(document.body,{subtree:true,childList:true,characterData:true});
}

document.addEventListener('DOMContentLoaded',()=>{
  clean();
  observe();
});
window.addEventListener('load',()=>clean());
})();