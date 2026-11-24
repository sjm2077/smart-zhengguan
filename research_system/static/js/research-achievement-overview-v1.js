(function(){
'use strict';
const $=id=>document.getElementById(id);
function esc(v){const d=document.createElement('div');d.textContent=v==null?'':String(v);return d.innerHTML}
function info(label,value){return `<div class="achievement-info-item"><label>${esc(label)}</label><div>${esc(value||'—')}</div></div>`}
window.toggleSubmenu=el=>{const s=el.nextElementSibling;if(s)s.classList.toggle('open')};
window.goToSmartAnalysis=()=>{const role=localStorage.getItem('userRole')||'admin';location.href=role==='admin'?'/analysis/admin/':'/analysis/teacher/'};
document.addEventListener('DOMContentLoaded',async()=>{
  const id=new URLSearchParams(location.search).get('id');
  if(!id){$('achievementTitle').textContent='缺少成果 ID';return}
  try{
    const res=await fetch(`/api/achievement/detail?id=${encodeURIComponent(id)}`);
    const data=await res.json();
    if(!res.ok)throw new Error(data.error||'成果详情加载失败');
    const a=data.item;
    document.title=`${a.title} - 成果综合详情`;
    $('achievementBreadcrumbName').textContent=a.title;
    $('achievementMetaTop').textContent=`${a.publish_year||'—'} 年 · ${a.dept_name||'未分配系别'}`;
    $('achievementTitle').textContent=a.title;
    $('achievementType').textContent=`类型：${a.achievement_type||'—'}`;
    $('achievementLevel').textContent=`级别：${a.level||'未填写'}`;
    $('achievementSubject').textContent=`学科：${a.subject||'未分类'}`;
    $('achievementInternational').textContent=a.is_international?'国际发表':'非国际发表';
    $('achievementCitation').textContent=Number(a.citation_count||0);
    $('achievementInfoGrid').innerHTML=[
      info('成果类型',a.achievement_type),
      info('成果级别 / 收录',a.level||'未填写'),
      info('发表年份',a.publish_year),
      info('所属学科',a.subject||'未分类'),
      info('所属系别',a.dept_name||'未分配'),
      info('国际发表',a.is_international?'是':'否')
    ].join('');
    $('achievementAuthor').textContent=a.author_name||'未指定';
    $('achievementAuthorDept').textContent=a.dept_name||'未分配系别';
    $('achievementAuthorProfile').href=`/analysis/teacher/?teacher_id=${encodeURIComponent(a.author_id)}`;
  }catch(e){
    console.error(e);
    $('achievementTitle').textContent=e.message||'成果详情加载失败';
  }
});
})();