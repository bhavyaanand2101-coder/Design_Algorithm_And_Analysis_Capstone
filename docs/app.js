/**
 * Intelligent Courier Planning System - Interactive Web Client
 * DAA Capstone Project
 * Integrates: Multi-Criteria Sorting, 0/1 Knapsack DP, Dijkstra Shortest Path, TSP 2-Opt Approximation
 */

// ============================================================================
// 1. DATA STRUCTURES & ALGORITHMS (PORTED FROM PYTHON ENGINE)
// ============================================================================

function parcelComparator(p1, p2) {
  // 1. Deadline ascending (within 0.25 hr buffer)
  if (Math.abs(p1.deadline_hours - p2.deadline_hours) > 0.25) {
    return p1.deadline_hours < p2.deadline_hours ? -1 : 1;
  }
  // 2. Priority descending (5 = highest)
  if (p1.priority !== p2.priority) {
    return p1.priority > p2.priority ? -1 : 1;
  }
  // 3. Value density descending
  const d1 = p1.composite_value / Math.max(1, p1.weight);
  const d2 = p2.composite_value / Math.max(1, p2.weight);
  if (Math.abs(d1 - d2) > 1e-4) {
    return d1 > d2 ? -1 : 1;
  }
  return 0;
}

function calculateCompositeValue(p) {
  const urgencyBonus = Math.max(0, (24.0 - p.deadline_hours) * 2.0);
  const total = (p.base_value * p.priority) + urgencyBonus;
  return Math.max(1, Math.round(total));
}

// MergeSort
function mergeSort(arr, metrics) {
  if (arr.length <= 1) return [...arr];
  const mid = Math.floor(arr.length / 2);
  const left = mergeSort(arr.slice(0, mid), metrics);
  const right = mergeSort(arr.slice(mid), metrics);

  const merged = [];
  let i = 0, j = 0;
  while (i < left.length && j < right.length) {
    if (metrics) metrics.comparisons++;
    if (parcelComparator(left[i], right[j]) <= 0) {
      merged.push(left[i]);
      i++;
    } else {
      merged.push(right[j]);
      j++;
    }
  }
  while (i < left.length) merged.push(left[i++]);
  while (j < right.length) merged.push(right[j++]);
  return merged;
}

// QuickSort (Median-of-3)
function quickSort(arr, metrics) {
  const copy = [...arr];
  function qsort(low, high) {
    if (low < high) {
      const pIdx = partition(low, high);
      qsort(low, pIdx - 1);
      qsort(pIdx + 1, high);
    }
  }
  function partition(low, high) {
    // Median-of-3 pivot
    const mid = Math.floor((low + high) / 2);
    const triplet = [[low, copy[low]], [mid, copy[mid]], [high, copy[high]]];
    for (let i = 0; i < 2; i++) {
      for (let j = 0; j < 2 - i; j++) {
        if (metrics) metrics.comparisons++;
        if (parcelComparator(triplet[j][1], triplet[j + 1][1]) > 0) {
          const temp = triplet[j];
          triplet[j] = triplet[j + 1];
          triplet[j + 1] = temp;
        }
      }
    }
    const pivotIdx = triplet[1][0];
    const pivotTemp = copy[pivotIdx];
    copy[pivotIdx] = copy[high];
    copy[high] = pivotTemp;

    const pivot = copy[high];
    let i = low - 1;
    for (let j = low; j < high; j++) {
      if (metrics) metrics.comparisons++;
      if (parcelComparator(copy[j], pivot) <= 0) {
        i++;
        const t = copy[i];
        copy[i] = copy[j];
        copy[j] = t;
      }
    }
    const t2 = copy[i + 1];
    copy[i + 1] = copy[high];
    copy[high] = t2;
    return i + 1;
  }
  qsort(0, copy.length - 1);
  return copy;
}

// 0/1 Knapsack DP
function knapsack01DP(parcels, capacity) {
  const t0 = performance.now();
  const n = parcels.length;
  const W = Math.max(0, Math.floor(capacity));

  const dp = Array.from({ length: n + 1 }, () => new Int32Array(W + 1));

  for (let i = 1; i <= n; i++) {
    const p = parcels[i - 1];
    const wt = p.weight;
    const val = p.composite_value;
    for (let w = 0; w <= W; w++) {
      if (wt <= w) {
        const inc = dp[i - 1][w - wt] + val;
        const exc = dp[i - 1][w];
        dp[i][w] = inc > exc ? inc : exc;
      } else {
        dp[i][w] = dp[i - 1][w];
      }
    }
  }

  // Backtracking
  const selectedIndices = new Set();
  let currW = W;
  for (let i = n; i > 0; i--) {
    if (dp[i][currW] !== dp[i - 1][currW]) {
      selectedIndices.add(i - 1);
      currW -= parcels[i - 1].weight;
    }
  }

  const selected = [];
  const unselected = [];
  parcels.forEach((p, idx) => {
    if (selectedIndices.has(idx)) selected.push(p);
    else unselected.push(p);
  });

  const totalWeight = selected.reduce((s, p) => s + p.weight, 0);
  const totalValue = dp[n][W];
  const elapsed = performance.now() - t0;

  return {
    selected,
    unselected,
    totalWeight,
    totalValue,
    capacity: W,
    dpTable: dp,
    elapsedMs: elapsed
  };
}

// Dijkstra Min-Heap Shortest Paths
class MinHeap {
  constructor() { this.data = []; }
  push(val) {
    this.data.push(val);
    this.up(this.data.length - 1);
  }
  pop() {
    if (!this.data.length) return null;
    const top = this.data[0];
    const bottom = this.data.pop();
    if (this.data.length) {
      this.data[0] = bottom;
      this.down(0);
    }
    return top;
  }
  up(idx) {
    while (idx > 0) {
      const p = Math.floor((idx - 1) / 2);
      if (this.data[idx][0] < this.data[p][0]) {
        [this.data[idx], this.data[p]] = [this.data[p], this.data[idx]];
        idx = p;
      } else break;
    }
  }
  down(idx) {
    const len = this.data.length;
    while (true) {
      let left = 2 * idx + 1;
      let right = 2 * idx + 2;
      let smallest = idx;
      if (left < len && this.data[left][0] < this.data[smallest][0]) smallest = left;
      if (right < len && this.data[right][0] < this.data[smallest][0]) smallest = right;
      if (smallest !== idx) {
        [this.data[idx], this.data[smallest]] = [this.data[smallest], this.data[idx]];
        idx = smallest;
      } else break;
    }
  }
  isEmpty() { return this.data.length === 0; }
}

function dijkstra(network, startNode) {
  const distances = {};
  const predecessors = {};
  network.nodes.forEach(nd => {
    distances[nd.id] = Infinity;
    predecessors[nd.id] = null;
  });

  distances[startNode] = 0;
  const pq = new MinHeap();
  pq.push([0, startNode]);

  const adj = network.adjacency;

  while (!pq.isEmpty()) {
    const [d, u] = pq.pop();
    if (d > distances[u]) continue;

    const neighbors = adj[u] || [];
    for (const [v, weight] of neighbors) {
      const newD = d + weight;
      if (newD < distances[v]) {
        distances[v] = newD;
        predecessors[v] = u;
        pq.push([newD, v]);
      }
    }
  }
  return { distances, predecessors };
}

function computeMetricMatrix(network, activeNodes) {
  const distMatrix = {};
  const pathMatrix = {};

  activeNodes.forEach(u => {
    const { distances, predecessors } = dijkstra(network, u);
    activeNodes.forEach(v => {
      distMatrix[`${u},${v}`] = distances[v];
      // reconstruct path
      const path = [];
      let curr = v;
      while (curr !== null) {
        path.push(curr);
        curr = predecessors[curr];
      }
      path.reverse();
      pathMatrix[`${u},${v}`] = path;
    });
  });

  return { distMatrix, pathMatrix };
}

// TSP Nearest Neighbor
function tspNearestNeighbor(startNode, stops, distMatrix) {
  const t0 = performance.now();
  const unvisited = new Set(stops);
  unvisited.delete(startNode);

  let current = startNode;
  const tour = [current];
  let totalDist = 0;

  while (unvisited.size > 0) {
    let nearest = null;
    let minDist = Infinity;
    for (const cand of unvisited) {
      const d = distMatrix[`${current},${cand}`] ?? Infinity;
      if (d < minDist) {
        minDist = d;
        nearest = cand;
      }
    }
    if (nearest === null) break;
    tour.push(nearest);
    totalDist += minDist;
    unvisited.delete(nearest);
    current = nearest;
  }

  const returnD = distMatrix[`${current},${startNode}`] ?? Infinity;
  tour.push(startNode);
  totalDist += returnD;

  return { tour, distance: totalDist, elapsedMs: performance.now() - t0 };
}

function calculateTourLength(tour, distMatrix) {
  let len = 0;
  for (let i = 0; i < tour.length - 1; i++) {
    len += distMatrix[`${tour[i]},${tour[i + 1]}`] ?? Infinity;
  }
  return len;
}

// TSP 2-Opt
function tsp2Opt(initialTour, distMatrix, maxIter = 500) {
  const t0 = performance.now();
  let bestTour = [...initialTour];
  let bestDist = calculateTourLength(bestTour, distMatrix);
  const n = bestTour.length;

  let improved = true;
  let swaps = 0;
  let iter = 0;

  while (improved && iter < maxIter) {
    improved = false;
    iter++;
    for (let i = 1; i < n - 2; i++) {
      for (let j = i + 1; j < n - 1; j++) {
        const a = bestTour[i - 1], b = bestTour[i];
        const c = bestTour[j], d = bestTour[j + 1];

        const curCost = (distMatrix[`${a},${b}`] || Infinity) + (distMatrix[`${c},${d}`] || Infinity);
        const newCost = (distMatrix[`${a},${c}`] || Infinity) + (distMatrix[`${b},${d}`] || Infinity);

        if (newCost < curCost - 1e-6) {
          // Reverse segment i to j
          const reversedSeg = bestTour.slice(i, j + 1).reverse();
          bestTour.splice(i, reversedSeg.length, ...reversedSeg);
          bestDist -= (curCost - newCost);
          improved = true;
          swaps++;
          break;
        }
      }
      if (improved) break;
    }
  }

  const finalDist = calculateTourLength(bestTour, distMatrix);
  return {
    tour: bestTour,
    distance: finalDist,
    swaps,
    elapsedMs: performance.now() - t0
  };
}

// ============================================================================
// 2. UI & CANVAS VISUALIZATION ENGINE
// ============================================================================

let currentScenarioData = null;
let currentPipelineResults = null;
let benchmarkCharts = {};

function buildAdjacencyList(nodes, edges) {
  const adj = {};
  nodes.forEach(nd => { adj[nd.id] = []; });
  edges.forEach(ed => {
    adj[ed.u].push([ed.v, ed.distance, ed.road_name]);
    adj[ed.v].push([ed.u, ed.distance, ed.road_name]);
  });
  return adj;
}

function loadScenario(datasetKey) {
  const raw = BUNDLED_DATASETS[datasetKey];
  if (!raw) return;

  currentScenarioData = {
    ...raw,
    adjacency: buildAdjacencyList(raw.nodes, raw.edges),
    parcels: raw.parcels.map(p => ({
      ...p,
      composite_value: calculateCompositeValue(p)
    }))
  };

  document.getElementById("capacitySlider").value = currentScenarioData.vehicle_capacity_weight;
  document.getElementById("capacityValue").innerText = `${currentScenarioData.vehicle_capacity_weight} kg`;
  document.getElementById("scenarioTitle").innerText = currentScenarioData.name;
  document.getElementById("scenarioNodesCount").innerText = `${currentScenarioData.nodes.length} nodes`;
  document.getElementById("scenarioEdgesCount").innerText = `${currentScenarioData.edges.length} road links`;
  document.getElementById("scenarioParcelsCount").innerText = `${currentScenarioData.parcels.length} parcels`;

  runPipeline();
}

function runPipeline() {
  if (!currentScenarioData) return;

  const tStart = performance.now();
  const sortAlgo = document.getElementById("sortAlgorithmSelect").value;
  const capacity = parseInt(document.getElementById("capacitySlider").value, 10);
  const use2Opt = document.getElementById("toggle2Opt").checked;

  // Phase 2.1: Sorting
  const sortMetrics = { comparisons: 0 };
  const tSort0 = performance.now();
  let sortedParcels = [];
  if (sortAlgo === "quicksort") {
    sortedParcels = quickSort(currentScenarioData.parcels, sortMetrics);
  } else {
    sortedParcels = mergeSort(currentScenarioData.parcels, sortMetrics);
  }
  const sortTime = performance.now() - tSort0;

  // Phase 2.2: Knapsack DP
  const packingPlan = knapsack01DP(sortedParcels, capacity);

  // Phase 3.1: Dijkstra All-Pairs
  const depotId = currentScenarioData.depot_id;
  const activeStopsSet = new Set(packingPlan.selected.map(p => p.destination_node));
  activeStopsSet.add(depotId);
  const activeStops = Array.from(activeStopsSet);

  const tDijk0 = performance.now();
  const { distMatrix, pathMatrix } = computeMetricMatrix(currentScenarioData, activeStops);
  const dijkTime = performance.now() - tDijk0;

  // Phase 3.2: TSP Heuristics
  const nnResult = tspNearestNeighbor(depotId, activeStops, distMatrix);
  let finalTour = nnResult.tour;
  let finalDist = nnResult.distance;
  let optResult = { swaps: 0, elapsedMs: 0 };

  if (use2Opt && activeStops.length > 2) {
    optResult = tsp2Opt(nnResult.tour, distMatrix);
    finalTour = optResult.tour;
    finalDist = optResult.distance;
  }

  // Turn-by-Turn Road Trace
  const fullTurnRoad = [];
  for (let idx = 0; idx < finalTour.length - 1; idx++) {
    const u = finalTour[idx], v = finalTour[idx + 1];
    const seg = pathMatrix[`${u},${v}`] || [u, v];
    if (fullTurnRoad.length === 0) fullTurnRoad.push(...seg);
    else fullTurnRoad.push(...seg.slice(1));
  }

  const totalTime = performance.now() - tStart;

  currentPipelineResults = {
    sortedParcels,
    sortMetrics,
    sortTime,
    packingPlan,
    activeStops,
    nnResult,
    optResult,
    finalTour,
    finalDist,
    fullTurnRoad,
    totalTime,
    sortAlgo
  };

  renderAllViews();
}

function renderAllViews() {
  renderMetricsCards();
  renderSortingTable();
  renderDPTable();
  renderRouteMap();
  renderManifest();
}

function renderMetricsCards() {
  const res = currentPipelineResults;
  const plan = res.packingPlan;

  document.getElementById("metricLoadedItems").innerText = `${plan.selected.length} / ${currentScenarioData.parcels.length}`;
  document.getElementById("metricPayloadWeight").innerText = `${plan.totalWeight} / ${plan.capacity} kg`;
  const pct = ((plan.totalWeight / Math.max(1, plan.capacity)) * 100).toFixed(1);
  document.getElementById("metricPayloadPct").innerText = `${pct}% utilized`;

  document.getElementById("metricTotalValue").innerText = `${plan.totalValue} pts`;
  document.getElementById("metricRouteDistance").innerText = `${res.finalDist.toFixed(2)} km`;
  document.getElementById("metricPipelineLatency").innerText = `${res.totalTime.toFixed(3)} ms`;

  const impr = res.nnResult.distance > 0 ? (((res.nnResult.distance - res.finalDist) / res.nnResult.distance) * 100).toFixed(1) : 0;
  document.getElementById("metric2OptImprovement").innerText = `${impr}% reduced (${res.optResult.swaps} swaps)`;
}

function renderSortingTable() {
  const res = currentPipelineResults;
  const tbody = document.getElementById("sortedParcelsTableBody");
  tbody.innerHTML = "";

  res.sortedParcels.slice(0, 12).forEach((p, idx) => {
    const dest = currentScenarioData.nodes.find(n => n.id === p.destination_node);
    const destName = dest ? dest.name : `Node ${p.destination_node}`;
    const isPacked = res.packingPlan.selected.some(sp => sp.id === p.id);

    const tr = document.createElement("tr");
    tr.className = isPacked ? "bg-emerald-50 dark:bg-emerald-950/20" : "opacity-60";
    tr.innerHTML = `
      <td class="px-3 py-2 text-xs font-mono font-bold">${p.id}</td>
      <td class="px-3 py-2 text-xs">${destName}</td>
      <td class="px-3 py-2 text-xs">${p.weight} kg</td>
      <td class="px-3 py-2 text-xs"><span class="px-2 py-0.5 rounded text-[10px] font-bold ${p.priority >= 4 ? 'bg-rose-100 text-rose-700' : 'bg-slate-100 text-slate-700'}">Tier ${p.priority}</span></td>
      <td class="px-3 py-2 text-xs font-semibold">${p.deadline_hours}h</td>
      <td class="px-3 py-2 text-xs font-bold text-blue-600">${p.composite_value}</td>
      <td class="px-3 py-2 text-xs">${(p.composite_value / p.weight).toFixed(1)}</td>
      <td class="px-3 py-2 text-xs">${isPacked ? '<span class="text-emerald-600 font-bold">✓ Loaded</span>' : '<span class="text-slate-400">Queue</span>'}</td>
    `;
    tbody.appendChild(tr);
  });
}

function renderDPTable() {
  const plan = currentPipelineResults.packingPlan;
  const parcels = currentPipelineResults.sortedParcels;
  const container = document.getElementById("dpTableContainer");
  container.innerHTML = "";

  if (parcels.length > 20 || plan.capacity > 40) {
    container.innerHTML = `
      <div class="p-6 text-center text-slate-500 text-xs">
        <p class="font-bold mb-1">State space matrix is ${parcels.length} items × ${plan.capacity} capacity states (${parcels.length * plan.capacity} cells).</p>
        <p>Full matrix evaluated in ${plan.elapsedMs.toFixed(3)} ms. To view the cell-by-cell matrix table, select the <b>Small Fleet Dataset</b>.</p>
      </div>
    `;
    return;
  }

  const table = document.createElement("table");
  table.className = "w-full text-[11px] border-collapse font-mono";

  // Header
  const thead = document.createElement("thead");
  let headerHtml = `<tr class="bg-slate-100 border-b"><th class="p-1 border text-left">Item / W</th>`;
  for (let w = 0; w <= plan.capacity; w++) {
    headerHtml += `<th class="p-1 border text-center">${w}</th>`;
  }
  headerHtml += `</tr>`;
  thead.innerHTML = headerHtml;
  table.appendChild(thead);

  // Rows
  const tbody = document.createElement("tbody");
  for (let i = 0; i <= parcels.length; i++) {
    const tr = document.createElement("tr");
    let label = i === 0 ? "0 (Init)" : `${parcels[i - 1].id} (w=${parcels[i - 1].weight})`;
    let rowHtml = `<td class="p-1 border font-bold bg-slate-50">${label}</td>`;
    for (let w = 0; w <= plan.capacity; w++) {
      const val = plan.dpTable[i][w];
      const isSelected = i > 0 && plan.dpTable[i][w] !== plan.dpTable[i - 1][w];
      const highlightClass = isSelected ? "bg-amber-100 text-amber-900 font-bold" : "";
      rowHtml += `<td class="p-1 border text-center ${highlightClass}">${val}</td>`;
    }
    tr.innerHTML = rowHtml;
    tbody.appendChild(tr);
  }
  table.appendChild(tbody);
  container.appendChild(table);
}

function renderRouteMap() {
  const canvas = document.getElementById("routeCanvas");
  if (!canvas) return;
  const ctx = canvas.getContext("2d");
  const w = canvas.width;
  const h = canvas.height;

  ctx.clearRect(0, 0, w, h);

  const nodes = currentScenarioData.nodes;
  const edges = currentScenarioData.edges;
  const res = currentPipelineResults;

  // Normalize coordinates to canvas
  const padding = 50;
  const xs = nodes.map(n => n.x);
  const ys = nodes.map(n => n.y);
  const minX = Math.min(...xs), maxX = Math.max(...xs);
  const minY = Math.min(...ys), maxY = Math.max(...ys);

  function toScreen(x, y) {
    const sx = padding + ((x - minX) / Math.max(1, maxX - minX)) * (w - 2 * padding);
    const sy = padding + ((y - minY) / Math.max(1, maxY - minY)) * (h - 2 * padding);
    return [sx, sy];
  }

  // 1. Draw Road Network (edges)
  ctx.strokeStyle = "#CBD5E1";
  ctx.lineWidth = 1.5;
  ctx.setLineDash([4, 4]);
  edges.forEach(ed => {
    const n1 = nodes.find(n => n.id === ed.u);
    const n2 = nodes.find(n => n.id === ed.v);
    if (n1 && n2) {
      const [x1, y1] = toScreen(n1.x, n1.y);
      const [x2, y2] = toScreen(n2.x, n2.y);
      ctx.beginPath();
      ctx.moveTo(x1, y1);
      ctx.lineTo(x2, y2);
      ctx.stroke();
    }
  });
  ctx.setLineDash([]);

  // 2. Draw Tour Path
  const tour = res.fullTurnRoad;
  if (tour.length > 1) {
    ctx.strokeStyle = "#059669";
    ctx.lineWidth = 3.5;
    ctx.beginPath();
    for (let i = 0; i < tour.length - 1; i++) {
      const n1 = nodes.find(n => n.id === tour[i]);
      const n2 = nodes.find(n => n.id === tour[i + 1]);
      if (n1 && n2) {
        const [x1, y1] = toScreen(n1.x, n1.y);
        const [x2, y2] = toScreen(n2.x, n2.y);
        if (i === 0) ctx.moveTo(x1, y1);
        ctx.lineTo(x2, y2);
      }
    }
    ctx.stroke();

    // Draw directional arrows
    for (let i = 0; i < tour.length - 1; i++) {
      const n1 = nodes.find(n => n.id === tour[i]);
      const n2 = nodes.find(n => n.id === tour[i + 1]);
      if (n1 && n2) {
        const [x1, y1] = toScreen(n1.x, n1.y);
        const [x2, y2] = toScreen(n2.x, n2.y);
        const mx = (x1 + x2) / 2;
        const my = (y1 + y2) / 2;
        const angle = Math.atan2(y2 - y1, x2 - x1);
        drawArrow(ctx, mx, my, angle, "#047857");
      }
    }
  }

  // 3. Draw Nodes
  nodes.forEach(nd => {
    const [x, y] = toScreen(nd.x, nd.y);
    const isDepot = nd.id === currentScenarioData.depot_id;
    const isVisited = res.finalTour.includes(nd.id);

    if (isDepot) {
      ctx.fillStyle = "#DC2626";
      ctx.fillRect(x - 9, y - 9, 18, 18);
      ctx.fillStyle = "#991B1B";
      ctx.font = "bold 12px sans-serif";
      ctx.fillText(`Depot (0)`, x + 12, y + 4);
    } else if (isVisited) {
      ctx.fillStyle = "#2563EB";
      ctx.beginPath();
      ctx.arc(x, y, 8, 0, Math.PI * 2);
      ctx.fill();

      const stopIdx = res.finalTour.indexOf(nd.id);
      ctx.fillStyle = "#1E3A8A";
      ctx.font = "bold 11px sans-serif";
      ctx.fillText(`#${stopIdx}: ${nd.name.slice(0, 15)}`, x + 11, y + 4);
    } else {
      ctx.fillStyle = "#94A3B8";
      ctx.beginPath();
      ctx.arc(x, y, 4, 0, Math.PI * 2);
      ctx.fill();
    }
  });
}

function drawArrow(ctx, x, y, angle, color) {
  const arrowSize = 8;
  ctx.save();
  ctx.translate(x, y);
  ctx.rotate(angle);
  ctx.fillStyle = color;
  ctx.beginPath();
  ctx.moveTo(0, 0);
  ctx.lineTo(-arrowSize, -arrowSize / 2);
  ctx.lineTo(-arrowSize, arrowSize / 2);
  ctx.closePath();
  ctx.fill();
  ctx.restore();
}

function renderManifest() {
  const res = currentPipelineResults;
  const listEl = document.getElementById("manifestStopList");
  listEl.innerHTML = "";

  res.finalTour.forEach((nodeId, idx) => {
    const node = currentScenarioData.nodes.find(n => n.id === nodeId);
    const isDepot = nodeId === currentScenarioData.depot_id;
    const parcelsHere = res.packingPlan.selected.filter(p => p.destination_node === nodeId);

    const li = document.createElement("li");
    li.className = "p-3 border-b border-slate-100 flex items-start gap-3 hover:bg-slate-50";
    li.innerHTML = `
      <div class="w-6 h-6 rounded-full flex items-center justify-center font-bold text-xs ${isDepot ? 'bg-red-500 text-white' : 'bg-blue-600 text-white'}">
        ${idx}
      </div>
      <div class="flex-1">
        <div class="flex justify-between items-center">
          <span class="font-bold text-sm text-slate-800">${node ? node.name : `Node ${nodeId}`}</span>
          ${isDepot ? '<span class="text-[10px] bg-red-100 text-red-700 px-2 py-0.5 rounded font-bold">Depot</span>' : ''}
        </div>
        <p class="text-xs text-slate-500">${node ? node.address : ''}</p>
        ${parcelsHere.length > 0 ? `
          <div class="mt-2 flex flex-wrap gap-1">
            ${parcelsHere.map(p => `
              <span class="inline-flex items-center text-[10px] bg-emerald-50 text-emerald-800 border border-emerald-200 px-2 py-0.5 rounded font-mono">
                ${p.id} (${p.weight}kg, ★${p.priority})
              </span>
            `).join('')}
          </div>
        ` : (isDepot && idx === 0 ? '<p class="text-[11px] text-slate-400 mt-1">Vehicle dispatch departure</p>' : '')}
      </div>
    `;
    listEl.appendChild(li);
  });
}

function initBenchmarkCharts() {
  if (typeof Chart === "undefined") return;

  // Sorting Chart
  const ctxSort = document.getElementById("chartSorting")?.getContext("2d");
  if (ctxSort) {
    new Chart(ctxSort, {
      type: "line",
      data: {
        labels: [10, 25, 50, 100, 250, 500, 1000],
        datasets: [
          { label: "QuickSort (Median-of-3)", data: [0.023, 0.028, 0.082, 0.164, 0.512, 1.305, 3.148], borderColor: "#E11D48", tension: 0.2 },
          { label: "MergeSort (Stable O(N log N))", data: [0.013, 0.024, 0.071, 0.141, 0.435, 1.122, 2.599], borderColor: "#2563EB", tension: 0.2 },
          { label: "TimSort (Builtin)", data: [0.007, 0.013, 0.033, 0.086, 0.294, 0.826, 1.948], borderColor: "#059669", tension: 0.2 }
        ]
      },
      options: { responsive: true, plugins: { legend: { position: "bottom" } } }
    });
  }

  // Knapsack Chart
  const ctxKnap = document.getElementById("chartKnapsack")?.getContext("2d");
  if (ctxKnap) {
    new Chart(ctxKnap, {
      type: "line",
      data: {
        labels: [200, 1000, 3750, 12000, 30000, 60000],
        datasets: [{
          label: "Knapsack DP Execution Time (ms) vs State Space (N × W)",
          data: [0.030, 0.073, 0.259, 0.855, 1.965, 4.063],
          borderColor: "#7C3AED",
          backgroundColor: "#7C3AED22",
          fill: true,
          tension: 0.2
        }]
      },
      options: { responsive: true, plugins: { legend: { position: "bottom" } } }
    });
  }

  // TSP Scalability
  const ctxTsp = document.getElementById("chartTSP")?.getContext("2d");
  if (ctxTsp) {
    new Chart(ctxTsp, {
      type: "line",
      data: {
        labels: [4, 6, 8, 9, 12, 16, 20, 25],
        datasets: [
          { label: "Nearest Neighbor Approx O(N²)", data: [0.005, 0.004, 0.015, 0.009, 0.012, 0.016, 0.025, 0.038], borderColor: "#2563EB" },
          { label: "2-Opt Refined Tour", data: [0.005, 0.010, 0.013, 0.015, 0.027, 0.048, 0.124, 0.424], borderColor: "#059669" },
          { label: "Exact Brute-Force O(N!)", data: [0.010, 0.114, 5.580, 50.169, null, null, null, null], borderColor: "#DC2626", borderDash: [5, 5] }
        ]
      },
      options: {
        responsive: true,
        scales: { y: { type: "logarithmic", title: { display: true, text: "Runtime (ms, Log Scale)" } } },
        plugins: { legend: { position: "bottom" } }
      }
    });
  }
}

// Tab Switching
function switchTab(tabId) {
  document.querySelectorAll(".tab-content").forEach(el => el.classList.add("hidden"));
  document.querySelectorAll(".tab-btn").forEach(el => el.classList.remove("border-blue-600", "text-blue-600"));

  document.getElementById(`tab-${tabId}`)?.classList.remove("hidden");
  document.getElementById(`btn-tab-${tabId}`)?.classList.add("border-blue-600", "text-blue-600");
}

window.addEventListener("DOMContentLoaded", () => {
  // Event listeners
  document.getElementById("scenarioSelect").addEventListener("change", e => loadScenario(e.target.value));
  document.getElementById("capacitySlider").addEventListener("input", e => {
    document.getElementById("capacityValue").innerText = `${e.target.value} kg`;
    runPipeline();
  });
  document.getElementById("sortAlgorithmSelect").addEventListener("change", runPipeline);
  document.getElementById("toggle2Opt").addEventListener("change", runPipeline);

  // Initial load
  loadScenario("small_dataset");
  initBenchmarkCharts();
});
