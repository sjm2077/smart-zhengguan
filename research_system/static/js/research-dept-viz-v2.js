
(function(){
  const palette=['#4b6fff','#5b9cf6','#42b883','#d8a106','#e66a6a','#8064d6'];

  function hasPositive(arr){ return Array.isArray(arr) && arr.some(v => Number(v) > 0); }

  function empty(chart,message){
    chart.clear();
    chart.setOption({
      xAxis:{show:false}, yAxis:{show:false}, series:[],
      graphic:[{
        type:'text', left:'center', top:'middle',
        style:{text:message || '当前筛选范围暂无数据', fill:'#8a94a6', fontSize:16, fontWeight:500}
      }]
    }, true);
  }

  function wordCloud(chart,data,message){
    if(!Array.isArray(data) || !data.length){ empty(chart,message || '当前筛选范围暂无可提取研究主题'); return; }
    const max=Math.max(...data.map(x=>Number(x.value)||0),1);
    const min=Math.min(...data.map(x=>Number(x.value)||0),max);
    const normalized=data.map((x,i)=>({
      name:x.name,
      value:Number(x.value)||0,
      textStyle:{color:palette[i%palette.length]}
    }));
    chart.clear();
    chart.setOption({
      tooltip:{show:true,formatter:p=>`${p.name}：${p.value}`},
      series:[{
        type:'wordCloud',
        shape:'circle',
        gridSize:10,
        sizeRange:[18, Math.max(34, Math.min(58, 24 + normalized.length*1.2))],
        rotationRange:[-18,18],
        rotationStep:18,
        width:'92%', height:'88%',
        left:'center', top:'center',
        drawOutOfBound:false,
        data:normalized
      }]
    },true);
  }

  function bar(chart,categories,values,opts){
    opts=opts||{};
    if(!hasPositive(values)){ empty(chart,opts.emptyText || '当前筛选范围暂无统计数据'); return; }
    chart.clear();
    chart.setOption({
      tooltip:{trigger:'axis',axisPointer:{type:'shadow'}},
      grid:{left:opts.horizontal ? 110 : 52,right:28,top:28,bottom:opts.horizontal ? 30 : 55,containLabel:true},
      xAxis:opts.horizontal ? {type:'value',minInterval:1} : {type:'category',data:categories,axisLabel:{interval:0,rotate:categories.length>5?18:0}},
      yAxis:opts.horizontal ? {type:'category',data:categories,axisLabel:{interval:0}} : {type:'value',minInterval:1},
      series:[{type:'bar',barMaxWidth:42,data:values,itemStyle:{color:palette[0],borderRadius:opts.horizontal?[0,5,5,0]:[5,5,0,0]},label:{show:true,position:opts.horizontal?'right':'top'}}]
    },true);
  }

  function pie(chart,data,message){
    if(!Array.isArray(data) || !data.some(x=>Number(x.value)>0)){ empty(chart,message || '当前筛选范围暂无结构数据'); return; }
    chart.clear();
    chart.setOption({
      tooltip:{trigger:'item',formatter:'{b}<br>{c}（{d}%）'},
      legend:{bottom:4,left:'center'},
      series:[{type:'pie',radius:['38%','66%'],center:['50%','44%'],avoidLabelOverlap:true,data:data,label:{formatter:'{b}\\n{c}'},itemStyle:{borderColor:'#fff',borderWidth:2}}]
    },true);
  }

  function radar(chart,indicators,values,message){
    if(!hasPositive(values)){ empty(chart,message || '当前筛选范围暂无研究方向数据'); return; }
    chart.clear();
    chart.setOption({
      tooltip:{},
      radar:{indicator:indicators.map(n=>({name:n,max:100})),radius:'62%',splitNumber:4,axisName:{color:'#475569'}},
      series:[{type:'radar',data:[{value:values,name:'相对活跃度'}],symbolSize:6,areaStyle:{opacity:.18}}]
    },true);
  }

  window.ResearchDeptViz={empty,wordCloud,bar,pie,radar,hasPositive};
})();
