(function(){
'use strict';
const $=id=>document.getElementById(id);
const fmt=n=>Number(n||0).toLocaleString('zh-CN',{maximumFractionDigits:2});
function esc(v){const d=document.createElement('div');d.textContent=v==null?'':String(v);return d.innerHTML}

function infoItem(label,value){
  return `<div class="info-item"><label>${esc(label)}</label><div>${esc(value||'—')}</div></div>`;
}

function renderFundChart(trend){
  const el=$('fundTrendChart');
  const chart=echarts.init(el);
  const rows=Array.isArray(trend)?trend:[];
  chart.setOption({
    color:['#2F6BFF','#D4A017'],
    tooltip:{trigger:'axis'},
    legend:{data:['经费记录','预算'],top:0,textStyle:{color:'#667085'}},
    grid:{left:44,right:18,top:38,bottom:28},
    xAxis:{type:'category',data:rows.map(r=>r.year),axisLine:{lineStyle:{color:'#E5E7EB'}},axisLabel:{color:'#667085'}},
    yAxis:{type:'value',axisLine:{show:false},axisLabel:{color:'#667085'},splitLine:{lineStyle:{color:'#EEF0F3',type:'dashed'}}},
    series:[
      {name:'经费记录',type:'line',smooth:true,symbol:'circle',symbolSize:6,data:rows.map(r=>r.fund)},
      {name:'预算',type:'line',smooth:true,symbol:'circle',symbolSize:6,data:rows.map(r=>r.budget)}
    ]
  });
  addEventListener('resize',()=>chart.resize());
}

function render(data){
  const p=data.project,l=data.leader,f=data.fund,r=data.risk,c=data.cooperation;
  document.title=`${p.project_name} - 项目综合详情`;
  $('projectBreadcrumbName').textContent=p.project_name;
  $('projectNo').textContent=p.project_no||'未填写项目编号';
  $('projectName').textContent=p.project_name;
  $('projectLeader').textContent=`负责人：${l.real_name}`;
  $('projectDept').textContent=`系别：${p.dept||'未分配'}`;
  $('projectSubject').textContent=`学科：${p.subject||'未分类'}`;
  $('projectType').textContent=`类型：${p.project_type}`;
  $('projectStatus').textContent=p.status;
  $('projectProgressText').textContent=`${p.actual_progress}%`;
  $('projectProgressBar').style.width=`${Math.max(0,Math.min(100,Number(p.actual_progress||0)))}%`;

  $('kpiFundAmount').textContent=fmt(f.project_fund_amount);
  $('kpiFundDetail').textContent=fmt(f.detail_total);
  $('kpiBudget').textContent=fmt(f.budget_total);
  $('kpiRisk').textContent=r.active_count;

  $('projectInfoGrid').innerHTML=[
    infoItem('项目编号',p.project_no),
    infoItem('项目类型',p.project_type),
    infoItem('所属学科',p.subject||'未分类'),
    infoItem('所属系别',p.dept||'未分配'),
    infoItem('开始日期',p.start_date),
    infoItem('结束日期',p.end_date),
    infoItem('当前状态',p.status),
    infoItem('期限状态',p.deadline_state)
  ].join('');

  $('leaderName').textContent=l.real_name;
  $('leaderMeta').textContent=[l.title,l.dept].filter(Boolean).join(' · ')||'暂无职称/系别信息';
  $('leaderProjectCount').textContent=l.project_count;
  $('leaderAchievementCount').textContent=l.achievement_count;
  $('leaderProfileLink').href=l.profile_url;

  renderFundChart(f.trend);

  $('fundTableBody').innerHTML=f.details.length
    ? f.details.map(x=>`<tr><td>${esc(x.year)}</td><td>${esc(x.source_type)}</td><td>${esc(x.usage_type)}</td><td>${fmt(x.amount)}</td></tr>`).join('')
    : '<tr><td colspan="4" class="empty-note">暂无经费明细记录</td></tr>';

  let deadlineText=`期限状态：<strong>${esc(p.deadline_state)}</strong>`;
  if(p.deadline_days!==null){
    deadlineText+=p.deadline_days<0
      ? ` · 已逾期 <strong>${Math.abs(p.deadline_days)}</strong> 天`
      : ` · 距离结束 <strong>${p.deadline_days}</strong> 天`;
  }
  $('deadlinePanel').innerHTML=deadlineText;
  $('riskCountBadge').textContent=r.active_count;
  $('riskList').innerHTML=r.warnings.length
    ? r.warnings.map(x=>`<div class="risk-item ${x.risk_level==='高'?'high':x.risk_level==='中'?'medium':'low'}"><div class="risk-item-top"><span>${esc(x.risk_level)}风险 · ${esc(x.reason)}</span><span class="${x.is_resolved?'risk-resolved':'risk-open'}">${x.is_resolved?'已解决':'未解决'}</span></div><p>${esc(x.suggested_action||'暂无建议措施')} · ${esc(x.warning_date||'')}</p></div>`).join('')
    : '<div class="empty-note">当前没有风险预警记录</div>';

  $('cooperationList').innerHTML=c.items.length
    ? c.items.map(x=>`<div class="coop-item"><span><strong>${esc(x.source)}</strong> ↔ <strong>${esc(x.target)}</strong></span><span>合作次数 ${Number(x.coop_count||1)}</span></div>`).join('')
    : '<div class="empty-note">当前没有正式合作关系记录</div>';

  const relationNote=$('relationNote'); if(relationNote) relationNote.textContent=data.relation_note||'';
}

function showError(msg){
  $('projectName').textContent=msg;
  document.querySelector('.project-hero-card').classList.add('error');
}

window.toggleSubmenu=el=>{const s=el.nextElementSibling;if(s)s.classList.toggle('open')};
window.goToSmartAnalysis=()=>{const role=localStorage.getItem('userRole')||'admin';location.href=role==='admin'?'/analysis/admin/':'/analysis/teacher/'};

document.addEventListener('DOMContentLoaded',async()=>{
  const id=new URLSearchParams(location.search).get('id');
  if(!id){showError('缺少项目编号');return}
  try{
    const res=await fetch(`/api/project/overview?id=${encodeURIComponent(id)}`);
    const data=await res.json();
    if(!res.ok)throw new Error(data.error||'项目详情加载失败');
    render(data);
  }catch(e){
    console.error(e);
    showError(e.message||'项目详情加载失败');
  }
});
})();