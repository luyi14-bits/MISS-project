(function() {
  var style = getComputedStyle(document.documentElement);
  var accent = style.getPropertyValue('--accent').trim();
  var accent2 = style.getPropertyValue('--accent2').trim();
  var ink = style.getPropertyValue('--ink').trim();
  var muted = style.getPropertyValue('--muted').trim();
  var rule = style.getPropertyValue('--rule').trim();
  var bg2 = style.getPropertyValue('--bg2').trim();
  var warn = style.getPropertyValue('--warn').trim();
  var danger = style.getPropertyValue('--danger').trim();
  var ice = style.getPropertyValue('--ice').trim();

  // ======================
  // Chart 1: Phase Progress (Stacked Bar)
  // ======================
  var c1 = echarts.init(document.getElementById('chart-progress'), null, { renderer: 'svg' });
  c1.setOption({
    animation: false,
    tooltip: {
      trigger: 'axis',
      axisPointer: { type: 'shadow' },
      appendToBody: true,
      backgroundColor: bg2,
      borderColor: rule,
      textStyle: { color: ink, fontSize: 13 }
    },
    legend: {
      data: ['已完成', '进行中', '计划中'],
      bottom: 0,
      textStyle: { color: muted, fontSize: 12 }
    },
    grid: { left: '3%', right: '4%', bottom: '10%', top: '8%', containLabel: true },
    xAxis: {
      type: 'category',
      data: ['P0', 'P1', 'P2', 'P3', 'P4', 'P7', 'Spec'],
      axisLine: { lineStyle: { color: rule } },
      axisLabel: { color: ink, fontWeight: 700, fontSize: 13 },
      axisTick: { show: false }
    },
    yAxis: {
      type: 'value',
      minInterval: 1,
      max: 5,
      axisLine: { show: false },
      axisTick: { show: false },
      axisLabel: { color: muted, fontSize: 11 },
      splitLine: { lineStyle: { color: rule, type: 'dashed' } }
    },
    series: [
      {
        name: '已完成',
        type: 'bar',
        stack: 'total',
        data: [1, 4, 4, 3, 2, 2, 2],
        itemStyle: { color: accent2, borderColor: accent2, borderRadius: [4, 4, 0, 0] },
        emphasis: { itemStyle: { color: accent2 } },
        label: { show: true, position: 'inside', color: '#fff', fontSize: 12, fontWeight: 700 }
      },
      {
        name: '进行中',
        type: 'bar',
        stack: 'total',
        data: [0, 0, 0, 0, 0, 0, 1],
        itemStyle: { color: warn },
        label: { show: true, position: 'inside', color: '#fff', fontSize: 12, fontWeight: 700 }
      },
      {
        name: '计划中',
        type: 'bar',
        stack: 'total',
        data: [0, 0, 0, 0, 0, 0, 0],
        itemStyle: { color: muted },
        label: { show: true, position: 'inside', color: '#fff', fontSize: 12, fontWeight: 700 }
      }
    ]
  });

  // ======================
  // Chart 2: Bug Severity (Doughnut)
  // ======================
  var c2 = echarts.init(document.getElementById('chart-severity'), null, { renderer: 'svg' });
  c2.setOption({
    animation: false,
    tooltip: {
      trigger: 'item',
      appendToBody: true,
      backgroundColor: bg2,
      borderColor: rule,
      textStyle: { color: ink, fontSize: 13 },
      formatter: '{b}: {c} 个 ({d}%)'
    },
    legend: {
      bottom: 0,
      textStyle: { color: muted, fontSize: 12 },
      data: ['🔴 严重', '🟠 中等', '🟡 轻微', '🔵 建议']
    },
    series: [
      {
        type: 'pie',
        radius: ['55%', '80%'],
        center: ['50%', '48%'],
        avoidLabelOverlap: false,
        label: {
          show: true,
          position: 'outside',
          formatter: '{c}',
          fontSize: 14,
          fontWeight: 700,
          color: ink
        },
        emphasis: {
          label: { show: true, fontSize: 18, fontWeight: 'bold' }
        },
        labelLine: { show: true, lineStyle: { color: rule } },
        data: [
          { value: 6, name: '🔴 严重', itemStyle: { color: danger } },
          { value: 7, name: '🟠 中等', itemStyle: { color: warn } },
          { value: 11, name: '🟡 轻微', itemStyle: { color: accent } },
          { value: 16, name: '🔵 建议', itemStyle: { color: ice } }
        ]
      }
    ]
  });

  window.addEventListener('resize', function() {
    c1.resize();
    c2.resize();
  });
})();
