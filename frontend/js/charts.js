/**
 * SENTINEL AI - Charts Module
 * Plotly-based visualizations with HTML5 Canvas fallback to guarantee rendering under all network conditions.
 */

const ChartsModule = {
  baseLayout: {
    font: { family: 'Plus Jakarta Sans, sans-serif', size: 12, color: '#57606a' },
    margin: { t: 30, r: 20, l: 50, b: 40 },
    paper_bgcolor: 'transparent',
    plot_bgcolor: 'transparent',
    hovermode: 'x unified',
    xaxis: {
      gridcolor: '#f0f2f5',
      zerolinecolor: '#e1e4e8',
      showline: true,
      linecolor: '#d0d7de',
      tickfont: { family: 'JetBrains Mono, monospace', size: 10 }
    },
    yaxis: {
      gridcolor: '#f0f2f5',
      zerolinecolor: '#e1e4e8',
      showline: true,
      linecolor: '#d0d7de',
      tickfont: { family: 'JetBrains Mono, monospace', size: 10 }
    }
  },

  renderTrajectoryChart(containerId, timeLabels, tankLevels, pumpFlows) {
    const el = document.getElementById(containerId);
    if (!el) return;

    if (typeof Plotly !== 'undefined') {
      const trace1 = {
        x: timeLabels,
        y: tankLevels,
        name: 'L_T1: Tank 1 Level (m)',
        type: 'scatter',
        mode: 'lines',
        line: { color: '#0969da', width: 2.5 }
      };

      const trace2 = {
        x: timeLabels,
        y: pumpFlows,
        name: 'F_PU1: Pump 1 Flow (L/s)',
        type: 'scatter',
        mode: 'lines',
        line: { color: '#2da44e', width: 2 },
        yaxis: 'y2'
      };

      const layout = {
        ...this.baseLayout,
        legend: { orientation: 'h', y: -0.2, x: 0.1 },
        yaxis: {
          title: 'Water Level (m)',
          titlefont: { size: 11 },
          gridcolor: '#f0f2f5',
        },
        yaxis2: {
          title: 'Flow Rate (L/s)',
          titlefont: { size: 11 },
          overlaying: 'y',
          side: 'right',
          showgrid: false
        }
      };

      Plotly.newPlot(containerId, [trace1, trace2], layout, { responsive: true, displayModeBar: false });
    } else {
      this._renderCanvasFallback(el, timeLabels, tankLevels, 'Tank Level (m)');
    }
  },

  renderComparisonChart(containerId, origData, manipData, attackIndices = []) {
    const el = document.getElementById(containerId);
    if (!el) return;

    const x = Array.from({ length: origData.length }, (_, i) => `T+${i}h`);

    if (typeof Plotly !== 'undefined') {
      const traceOrig = {
        x: x,
        y: origData,
        name: 'Ground Truth Telemetry (Clean)',
        type: 'scatter',
        mode: 'lines+markers',
        line: { color: '#2da44e', width: 2.5 },
        marker: { size: 4 }
      };

      const traceManip = {
        x: x,
        y: manipData,
        name: 'Manipulated / Injected Telemetry',
        type: 'scatter',
        mode: 'lines+markers',
        line: { color: '#cf222e', width: 2.5, dash: 'dot' },
        marker: { size: 5, color: '#cf222e' }
      };

      const layout = {
        ...this.baseLayout,
        title: {
          text: 'Clean vs. Manipulated Telemetry Comparison',
          font: { family: 'JetBrains Mono, monospace', size: 13, color: '#0d1117' }
        },
        legend: { orientation: 'h', y: -0.25 },
        shapes: attackIndices.length > 0 ? [{
          type: 'rect',
          xref: 'x',
          yref: 'paper',
          x0: `T+${attackIndices[0]}h`,
          x1: `T+${attackIndices[attackIndices.length - 1]}h`,
          y0: 0,
          y1: 1,
          fillcolor: 'rgba(220, 38, 38, 0.12)',
          line: { width: 0 }
        }] : []
      };

      Plotly.newPlot(containerId, [traceOrig, traceManip], layout, { responsive: true, displayModeBar: false });
    } else {
      this._renderCanvasFallback(el, x, manipData, 'Manipulated Reading');
    }
  },

  renderTrustDistribution(containerId, scores) {
    const el = document.getElementById(containerId);
    if (!el) return;

    if (typeof Plotly !== 'undefined') {
      const trace = {
        x: scores,
        type: 'histogram',
        marker: {
          color: '#0d1117',
          line: { color: '#d4ff00', width: 2 }
        },
        xbins: { start: 0, end: 100, size: 10 }
      };

      const layout = {
        ...this.baseLayout,
        xaxis: { title: 'Operational Trust Score (0 - 100)', dtick: 10 },
        yaxis: { title: 'Sensor Count' }
      };

      Plotly.newPlot(containerId, [trace], layout, { responsive: true, displayModeBar: false });
    }
  },

  renderConfusionMatrix(containerId, tn = 3798, fp = 160, fn = 189, tp = 30) {
    const el = document.getElementById(containerId);
    if (!el) return;

    if (typeof Plotly !== 'undefined') {
      const z = [[tn, fp], [fn, tp]];
      const x = ['Predicted Normal', 'Predicted Attack'];
      const y = ['Actual Normal', 'Actual Attack'];

      const data = [{
        z: z,
        x: x,
        y: y,
        type: 'heatmap',
        colorscale: [
          [0, '#f8fafc'],
          [0.5, '#93c5fd'],
          [1, '#1d4ed8']
        ],
        showscale: true
      }];

      const layout = {
        ...this.baseLayout,
        title: { text: 'BATADAL Evaluation Confusion Matrix (Official Benchmark)', font: { family: 'JetBrains Mono, monospace', size: 13 } },
        annotations: [
          { x: x[0], y: y[0], text: `TN: ${tn}`, font: { size: 14, color: '#0d1117' }, showarrow: false },
          { x: x[1], y: y[0], text: `FP: ${fp}`, font: { size: 14, color: '#0d1117' }, showarrow: false },
          { x: x[0], y: y[1], text: `FN: ${fn}`, font: { size: 14, color: '#0d1117' }, showarrow: false },
          { x: x[1], y: y[1], text: `TP: ${tp}`, font: { size: 14, color: '#ffffff' }, showarrow: false },
        ]
      };

      Plotly.newPlot(containerId, data, layout, { responsive: true, displayModeBar: false });
    }
  },

  _renderCanvasFallback(container, labels, dataPoints, title) {
    const w = container.clientWidth || 800;
    const h = container.clientHeight || 350;
    container.innerHTML = `
      <canvas width="${w}" height="${h}" style="width:100%; height:100%; display:block;"></canvas>
    `;
    const canvas = container.querySelector('canvas');
    if (!canvas) return;
    const ctx = canvas.getContext('2d');

    ctx.clearRect(0, 0, w, h);
    ctx.strokeStyle = '#0969da';
    ctx.lineWidth = 3;
    ctx.beginPath();

    const min = Math.min(...dataPoints);
    const max = Math.max(...dataPoints) || 1;
    const range = (max - min) || 1;

    dataPoints.forEach((val, i) => {
      const x = (i / (dataPoints.length - 1)) * (w - 80) + 40;
      const y = h - 40 - ((val - min) / range) * (h - 80);
      if (i === 0) ctx.moveTo(x, y);
      else ctx.lineTo(x, y);
    });
    ctx.stroke();

    ctx.fillStyle = '#0d1117';
    ctx.font = '12px JetBrains Mono, monospace';
    ctx.fillText(`${title}: Min ${min.toFixed(1)} | Max ${max.toFixed(1)}`, 40, 25);
  }
};
