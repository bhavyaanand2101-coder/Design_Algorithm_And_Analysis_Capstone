/**
 * Intelligent Courier Planning System - Dispatch Command Center Engine
 * DAA Capstone Project
 * Design: High-Precision Logistics Telemetry & Interactive Algorithmic Simulation
 */

// ============================================================================
// 1. CORE ALGORITHMIC ENGINE (PORTED & ENHANCED FROM PYTHON BACKEND)
// ============================================================================

function calculateCompositeValue(p) {
  const urgencyBonus = Math.max(0, (24.0 - p.deadline_hours) * 2.0);
  const total = (p.base_value * p.priority) + urgencyBonus;
  return Math.max(1, Math.round(total));
}

function parcelComparator(p1, p2) {
  // 1. Deadline ascending (within 0.25h SLA threshold)
  if (Math.abs(p1.deadline_hours - p2.deadline_hours) > 0.25) {
    return p1.deadline_hours < p2.deadline_hours ? -1 : 1;
  }
  // 2. Priority tier descending (Tier 5 = emergency/same-day)
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

// Stable MergeSort
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

// QuickSort with Median-of-Three Partitioning
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
    const mid = Math.floor((low + high) / 2);
    const triplet = [[low, copy[low]], [mid, copy[mid]], [high, copy[high]]];
    for (let i = 0; i < 2; i++) {
      for (let j = 0; j < 2 - i; j++) {
        if (metrics) metrics.comparisons++;
        if (parcelComparator(triplet[j][1], triplet[j + 1][1]) > 0) {
          const t = triplet[j];
          triplet[j] = triplet[j + 1];
          triplet[j + 1] = t;
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
        const temp = copy[i];
        copy[i] = copy[j];
        copy[j] = temp;
      }
    }
    const temp2 = copy[i + 1];
    copy[i + 1] = copy[high];
    copy[high] = temp2;
    return i + 1;
  }
  qsort(0, copy.length - 1);
  return copy;
}

// 0/1 Knapsack DP with Full Table & Backtracking Path
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

  // Backtrack optimal item choices and record decision states
  const selectedIndices = new Set();
  const backtrackStates = [];
  let currW = W;
  for (let i = n; i > 0; i--) {
    const wasIncluded = dp[i][currW] !== dp[i - 1][currW];
    backtrackStates.push({ i, w: currW, wasIncluded, parcel: parcels[i - 1] });
    if (wasIncluded) {
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

  return {
    selected,
    unselected,
    totalWeight,
    totalValue,
    capacity: W,
    dpTable: dp,
    backtrackStates,
    selectedIndices,
    elapsedMs: performance.now() - t0
  };
}

// Dijkstra Min-Heap
class MinHeap {
  constructor() { this.data = []; }
  push(val) {
    this.data.push(val);
    this.up(this.data.length - 1);
  }
  pop() {
    if (!this.data.length) return null;
    const top = this.data[0];
    const b = this.data.pop();
    if (this.data.length) {
      this.data[0] = b;
      this.down(0);
    }
    return top;
  }
  up(i) {
    while (i > 0) {
      const p = Math.floor((i - 1) / 2);
      if (this.data[i][0] < this.data[p][0]) {
        [this.data[i], this.data[p]] = [this.data[p], this.data[i]];
        i = p;
      } else break;
    }
  }
  down(i) {
    const l = this.data.length;
    while (true) {
      let left = 2 * i + 1;
      let right = 2 * i + 2;
      let s = i;
      if (left < l && this.data[left][0] < this.data[s][0]) s = left;
      if (right < l && this.data[right][0] < this.data[s][0]) s = right;
      if (s !== i) {
        [this.data[i], this.data[s]] = [this.data[s], this.data[i]];
        i = s;
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

// TSP 2-Opt Local Search
function tsp2Opt(initialTour, distMatrix, maxIter = 500) {
  const t0 = performance.now();
  let bestTour = [...initialTour];
  let bestDist = calculateTourLength(bestTour, distMatrix);
  const n = bestTour.length;

  let improved = true;
  let swaps = 0;
  let iter = 0;
  const swapHistory = [];

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
          swapHistory.push({ fromEdges: [[a, b], [c, d]], toEdges: [[a, c], [b, d]], saving: curCost - newCost });
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
    swapHistory,
    elapsedMs: performance.now() - t0
  };
}


// ============================================================================
// 2. DISPATCH COMMAND INTERACTIVE STATE & VISUALIZATION
// ============================================================================

let currentScenarioData = null;
let currentPipelineResults = null;
let customAddedParcels = [];
let chartInstances = {};

// Viewport Pan/Zoom state
let viewTransform = { x: 0, y: 0, scale: 1.0, isDragging: false, startX: 0, startY: 0 };
let hoveredNode = null;
let selectedNodeId = null;

// Vehicle Animation state
let animationState = {
  isPlaying: false,
  segmentIdx: 0,
  progress: 0.0, // 0.0 to 1.0 along current segment
  speed: 1.0,
  reqId: null
};

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

  customAddedParcels = [];
  const baseParcels = raw.parcels.map(p => ({
    ...p,
    composite_value: calculateCompositeValue(p)
  }));

  currentScenarioData = {
    ...raw,
    adjacency: buildAdjacencyList(raw.nodes, raw.edges),
    parcels: baseParcels
  };

  // Populate Destination dropdown in modal
  const destSelect = document.getElementById("newParcelDest");
  if (destSelect) {
    destSelect.innerHTML = "";
    currentScenarioData.nodes.filter(n => !n.is_depot).forEach(n => {
      const opt = document.createElement("option");
      opt.value = n.id;
      opt.innerText = `${n.id}: ${n.name}`;
      destSelect.appendChild(opt);
    });
  }

  // Update controls
  document.getElementById("capacitySlider").value = currentScenarioData.vehicle_capacity_weight;
  document.getElementById("capacityValue").innerText = `${currentScenarioData.vehicle_capacity_weight} kg`;
  document.getElementById("scenarioTitle").innerText = currentScenarioData.name;
  document.getElementById("scenarioNodesCount").innerText = `${currentScenarioData.nodes.length} hubs`;
  document.getElementById("scenarioEdgesCount").innerText = `${currentScenarioData.edges.length} roads`;
  document.getElementById("scenarioParcelsCount").innerText = `${currentScenarioData.parcels.length} parcels`;

  resetViewTransform();
  stopVehicleAnimation();
  runPipeline();
}

function resetViewTransform() {
  viewTransform = { x: 0, y: 0, scale: 1.0, isDragging: false, startX: 0, startY: 0 };
}

function runPipeline() {
  if (!currentScenarioData) return;

  const tStart = performance.now();
  const sortAlgo = document.getElementById("sortAlgorithmSelect").value;
  const capacity = parseInt(document.getElementById("capacitySlider").value, 10);
  const use2Opt = document.getElementById("toggle2Opt").checked;

  const allParcels = [...currentScenarioData.parcels, ...customAddedParcels];

  // Phase 2.1: Sorting
  const sortMetrics = { comparisons: 0 };
  const tSort0 = performance.now();
  let sortedParcels = [];
  if (sortAlgo === "quicksort") {
    sortedParcels = quickSort(allParcels, sortMetrics);
  } else {
    sortedParcels = mergeSort(allParcels, sortMetrics);
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
  let optResult = { swaps: 0, elapsedMs: 0, swapHistory: [] };

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
    allParcels,
    sortedParcels,
    sortMetrics,
    sortTime,
    packingPlan,
    activeStops,
    distMatrix,
    pathMatrix,
    nnResult,
    optResult,
    finalTour,
    finalDist,
    fullTurnRoad,
    totalTime,
    sortAlgo,
    use2Opt
  };

  renderAllViews();
}

function renderAllViews() {
  renderTelemetryStrip();
  renderSortingTable();
  renderDPTable();
  renderManifest();
  drawCanvas();
}

function renderTelemetryStrip() {
  const res = currentPipelineResults;
  const plan = res.packingPlan;

  document.getElementById("metricLoadedItems").innerText = `${plan.selected.length} / ${res.allParcels.length}`;
  document.getElementById("metricPayloadWeight").innerText = `${plan.totalWeight} / ${plan.capacity} kg`;
  
  const pct = ((plan.totalWeight / Math.max(1, plan.capacity)) * 100).toFixed(1);
  const pctEl = document.getElementById("metricPayloadPct");
  pctEl.innerText = `${pct}% utilized`;
  
  // Payload bar fill
  const barEl = document.getElementById("payloadBarFill");
  if (barEl) {
    barEl.style.width = `${Math.min(100, pct)}%`;
    barEl.className = pct >= 90 ? "bg-emerald-500 h-full rounded-full transition-all duration-300" :
                      pct >= 70 ? "bg-blue-500 h-full rounded-full transition-all duration-300" :
                      "bg-amber-500 h-full rounded-full transition-all duration-300";
  }

  document.getElementById("metricTotalValue").innerText = `${plan.totalValue.toLocaleString()} pts`;
  document.getElementById("metricRouteDistance").innerText = `${res.finalDist.toFixed(2)} km`;
  document.getElementById("metricPipelineLatency").innerText = `${res.totalTime.toFixed(3)} ms`;

  const impr = res.nnResult.distance > 0 ? (((res.nnResult.distance - res.finalDist) / res.nnResult.distance) * 100).toFixed(1) : 0;
  document.getElementById("metric2OptImprovement").innerText = `${impr}% saved (${res.optResult.swaps} swaps)`;
}

function renderSortingTable() {
  const res = currentPipelineResults;
  const tbody = document.getElementById("sortedParcelsTableBody");
  if (!tbody) return;
  tbody.innerHTML = "";

  const lbl = document.getElementById("lblSortAlgo");
  if (lbl) {
    lbl.innerText = res.sortAlgo === "quicksort" ? "QuickSort (Median-of-3)" : "MergeSort (Stable O(N log N))";
  }
  const cmpEl = document.getElementById("lblSortComparisons");
  if (cmpEl) {
    cmpEl.innerText = `${res.sortMetrics.comparisons} comparisons in ${res.sortTime.toFixed(3)} ms`;
  }

  res.sortedParcels.forEach((p) => {
    const dest = currentScenarioData.nodes.find(n => n.id === p.destination_node);
    const destName = dest ? dest.name : `Node ${p.destination_node}`;
    const isPacked = res.packingPlan.selected.some(sp => sp.id === p.id);

    const tr = document.createElement("tr");
    tr.className = isPacked 
      ? "bg-emerald-50/70 dark:bg-emerald-950/20 hover:bg-emerald-100/60 transition-colors" 
      : "opacity-60 hover:opacity-100 transition-opacity";
    tr.innerHTML = `
      <td class="px-3 py-2 text-xs font-mono font-bold text-slate-800">${p.id}</td>
      <td class="px-3 py-2 text-xs text-slate-700">${destName}</td>
      <td class="px-3 py-2 text-xs font-mono font-semibold">${p.weight} kg</td>
      <td class="px-3 py-2 text-xs">
        <span class="px-2 py-0.5 rounded text-[10px] font-bold ${
          p.priority === 5 ? 'bg-rose-100 text-rose-800 border border-rose-300' :
          p.priority === 4 ? 'bg-amber-100 text-amber-800 border border-amber-300' :
          p.priority === 3 ? 'bg-blue-100 text-blue-800' : 'bg-slate-100 text-slate-700'
        }">Tier ${p.priority}</span>
      </td>
      <td class="px-3 py-2 text-xs font-semibold ${p.deadline_hours <= 2.0 ? 'text-rose-600 font-bold' : 'text-slate-600'}">
        ${p.deadline_hours.toFixed(1)}h
      </td>
      <td class="px-3 py-2 text-xs font-bold text-indigo-600 font-mono">${p.composite_value}</td>
      <td class="px-3 py-2 text-xs font-mono text-slate-500">${(p.composite_value / p.weight).toFixed(1)}</td>
      <td class="px-3 py-2 text-xs font-bold">
        ${isPacked ? '<span class="text-emerald-700 flex items-center gap-1">✓ Loaded</span>' : '<span class="text-slate-400">In Queue</span>'}
      </td>
    `;
    tbody.appendChild(tr);
  });
}

function renderDPTable() {
  const plan = currentPipelineResults.packingPlan;
  const parcels = currentPipelineResults.sortedParcels;
  const container = document.getElementById("dpTableContainer");
  if (!container) return;
  container.innerHTML = "";

  if (parcels.length > 25 || plan.capacity > 50) {
    container.innerHTML = `
      <div class="p-8 text-center text-slate-600">
        <div class="inline-flex items-center justify-center w-12 h-12 rounded-full bg-blue-100 text-blue-600 mb-3 text-xl font-mono">
          ∑
        </div>
        <p class="font-bold text-sm text-slate-800 mb-1">State Space: ${parcels.length} items × ${plan.capacity} capacity states (${parcels.length * plan.capacity} cells)</p>
        <p class="text-xs text-slate-500 max-w-md mx-auto mb-4">
          The 2D dynamic programming recurrence relation evaluated optimally in <b class="text-blue-600 font-mono">${plan.elapsedMs.toFixed(3)} ms</b>.
        </p>
        <span class="inline-block px-3 py-1 bg-slate-200 text-slate-700 rounded text-xs font-medium">
          💡 Switch to <b>Small Fleet Dataset</b> to inspect every single individual cell & live recurrence calculation.
        </span>
      </div>
    `;
    return;
  }

  const table = document.createElement("table");
  table.className = "w-full text-[11px] border-collapse font-mono select-none";

  // Header
  const thead = document.createElement("thead");
  let headerHtml = `<tr class="bg-slate-100 border-b text-slate-600 sticky top-0 z-10"><th class="p-1.5 border text-left bg-slate-100 min-w-[120px]">Item / W</th>`;
  for (let w = 0; w <= plan.capacity; w++) {
    headerHtml += `<th class="p-1 border text-center ${w === plan.capacity ? 'bg-blue-100 text-blue-900 font-bold' : ''}">${w}</th>`;
  }
  headerHtml += `</tr>`;
  thead.innerHTML = headerHtml;
  table.appendChild(thead);

  // Rows
  const tbody = document.createElement("tbody");
  for (let i = 0; i <= parcels.length; i++) {
    const tr = document.createElement("tr");
    let label = i === 0 ? "0 (Init)" : `${parcels[i - 1].id} (w=${parcels[i - 1].weight},v=${parcels[i - 1].composite_value})`;
    let rowHtml = `<td class="p-1.5 border font-bold bg-slate-50 text-slate-700 sticky left-0 z-1">${label}</td>`;
    
    for (let w = 0; w <= plan.capacity; w++) {
      const val = plan.dpTable[i][w];
      const isSelected = i > 0 && plan.dpTable[i][w] !== plan.dpTable[i - 1][w];
      const highlightClass = isSelected ? "bg-amber-100/90 text-amber-950 font-bold border-amber-300" : "text-slate-600 hover:bg-blue-50";
      
      rowHtml += `<td class="p-1 border text-center cursor-pointer transition-colors ${highlightClass}" 
                      onmouseover="showDPCellInfo(${i}, ${w})" 
                      title="Item ${i}, Weight ${w}: Value ${val}">${val}</td>`;
    }
    tr.innerHTML = rowHtml;
    tbody.appendChild(tr);
  }
  table.appendChild(tbody);
  container.appendChild(table);
}

function showDPCellInfo(i, w) {
  const infoEl = document.getElementById("dpCellInfoBox");
  if (!infoEl || !currentPipelineResults) return;

  const plan = currentPipelineResults.packingPlan;
  const parcels = currentPipelineResults.sortedParcels;

  if (i === 0) {
    infoEl.innerHTML = `<span class="font-bold">Base Case:</span> Row 0, Capacity ${w} kg ➔ Value = 0 (no items considered)`;
    return;
  }

  const p = parcels[i - 1];
  const prevVal = plan.dpTable[i - 1][w];
  if (p.weight > w) {
    infoEl.innerHTML = `
      <span class="font-bold text-slate-700">${p.id}</span> (w=${p.weight}kg): Exceeds capacity ${w}kg.
      <code class="text-blue-600">DP[${i}][${w}] = DP[${i-1}][${w}] = ${prevVal}</code> (Item Excluded)
    `;
  } else {
    const incVal = plan.dpTable[i - 1][w - p.weight] + p.composite_value;
    const isInc = incVal > prevVal;
    infoEl.innerHTML = `
      <span class="font-bold text-slate-700">${p.id}</span> (w=${p.weight}kg, v=${p.composite_value}): 
      Exclude = ${prevVal} vs Include = (DP[${i-1}][${w-p.weight}] + ${p.composite_value}) = ${incVal} ➔ 
      <b class="${isInc ? 'text-amber-700' : 'text-slate-700'}">Choice: ${plan.dpTable[i][w]} (${isInc ? 'Included ✓' : 'Excluded'})</b>
    `;
  }
}

function renderManifest() {
  const res = currentPipelineResults;
  const listEl = document.getElementById("manifestStopList");
  if (!listEl) return;
  listEl.innerHTML = "";

  res.finalTour.forEach((nodeId, idx) => {
    const node = currentScenarioData.nodes.find(n => n.id === nodeId);
    const isDepot = nodeId === currentScenarioData.depot_id;
    const parcelsHere = res.packingPlan.selected.filter(p => p.destination_node === nodeId);
    const dropWeight = parcelsHere.reduce((s, p) => s + p.weight, 0);

    const li = document.createElement("li");
    li.className = `p-3 border-b border-slate-100 flex items-start gap-3 cursor-pointer transition-colors ${selectedNodeId === nodeId ? 'bg-blue-50 border-l-4 border-l-blue-600' : 'hover:bg-slate-50'}`;
    li.onclick = () => {
      selectedNodeId = nodeId;
      renderManifest();
      drawCanvas();
    };

    li.innerHTML = `
      <div class="w-6 h-6 rounded-full flex items-center justify-center font-bold text-xs shrink-0 ${isDepot ? 'bg-red-500 text-white' : 'bg-blue-600 text-white'}">
        ${idx}
      </div>
      <div class="flex-1 min-w-0">
        <div class="flex justify-between items-center">
          <span class="font-bold text-xs text-slate-900 truncate">${node ? node.name : `Stop ${nodeId}`}</span>
          ${isDepot ? '<span class="text-[10px] bg-red-100 text-red-700 px-1.5 py-0.5 rounded font-bold">Depot</span>' : `<span class="text-[10px] text-slate-500 font-mono">${dropWeight} kg</span>`}
        </div>
        <p class="text-[11px] text-slate-500 truncate">${node ? node.address : ''}</p>
        ${parcelsHere.length > 0 ? `
          <div class="mt-1.5 flex flex-wrap gap-1">
            ${parcelsHere.map(p => `
              <span class="inline-flex items-center text-[10px] bg-white border border-slate-200 text-slate-800 px-1.5 py-0.5 rounded font-mono font-semibold">
                ${p.id} (${p.weight}kg, ★${p.priority})
              </span>
            `).join('')}
          </div>
        ` : (isDepot && idx === 0 ? '<p class="text-[10px] text-slate-400 mt-1">Vehicle dispatch departure</p>' : '')}
      </div>
    `;
    listEl.appendChild(li);
  });
}


// ============================================================================
// 3. RETINA CANVAS RENDERER & INTERACTIVE ANIMATION
// ============================================================================

function initCanvasInteractions() {
  const canvas = document.getElementById("routeCanvas");
  if (!canvas) return;

  canvas.addEventListener("mousedown", e => {
    viewTransform.isDragging = true;
    viewTransform.startX = e.clientX - viewTransform.x;
    viewTransform.startY = e.clientY - viewTransform.y;
  });

  window.addEventListener("mouseup", () => {
    viewTransform.isDragging = false;
  });

  canvas.addEventListener("mousemove", e => {
    if (viewTransform.isDragging) {
      viewTransform.x = e.clientX - viewTransform.startX;
      viewTransform.y = e.clientY - viewTransform.startY;
      drawCanvas();
      return;
    }

    // Check hit test for node hover
    const rect = canvas.getBoundingClientRect();
    const mouseX = e.clientX - rect.left;
    const mouseY = e.clientY - rect.top;

    const hit = findNodeAtPoint(mouseX, mouseY);
    if (hit !== hoveredNode) {
      hoveredNode = hit;
      canvas.style.cursor = hit ? "pointer" : "grab";
      drawCanvas();
    }
  });

  canvas.addEventListener("click", e => {
    const rect = canvas.getBoundingClientRect();
    const mouseX = e.clientX - rect.left;
    const mouseY = e.clientY - rect.top;
    const hit = findNodeAtPoint(mouseX, mouseY);
    selectedNodeId = hit ? hit.id : null;
    renderManifest();
    drawCanvas();
  });

  canvas.addEventListener("wheel", e => {
    e.preventDefault();
    const zoomFactor = e.deltaY < 0 ? 1.1 : 0.9;
    viewTransform.scale = Math.max(0.5, Math.min(4.0, viewTransform.scale * zoomFactor));
    drawCanvas();
  }, { passive: false });
}

function findNodeAtPoint(screenX, screenY) {
  if (!currentScenarioData) return null;
  const canvas = document.getElementById("routeCanvas");
  const nodes = currentScenarioData.nodes;
  const coords = getCoordinateMapping(canvas.width, canvas.height);

  for (const nd of nodes) {
    const [nx, ny] = coords(nd.x, nd.y);
    const dist = Math.hypot(screenX - nx, screenY - ny);
    if (dist <= 14) return nd;
  }
  return null;
}

function getCoordinateMapping(w, h) {
  const nodes = currentScenarioData.nodes;
  const padding = 60;
  const xs = nodes.map(n => n.x);
  const ys = nodes.map(n => n.y);
  const minX = Math.min(...xs), maxX = Math.max(...xs);
  const minY = Math.min(...ys), maxY = Math.max(...ys);

  return function(x, y) {
    const normX = padding + ((x - minX) / Math.max(1, maxX - minX)) * (w - 2 * padding);
    const normY = padding + ((y - minY) / Math.max(1, maxY - minY)) * (h - 2 * padding);
    // Apply pan & zoom
    const finalX = (normX - w / 2) * viewTransform.scale + w / 2 + viewTransform.x;
    const finalY = (normY - h / 2) * viewTransform.scale + h / 2 + viewTransform.y;
    return [finalX, finalY];
  };
}

function drawCanvas() {
  const canvas = document.getElementById("routeCanvas");
  if (!canvas || !currentScenarioData || !currentPipelineResults) return;
  const ctx = canvas.getContext("2d");
  const w = canvas.width;
  const h = canvas.height;

  ctx.clearRect(0, 0, w, h);

  const coords = getCoordinateMapping(w, h);
  const nodes = currentScenarioData.nodes;
  const edges = currentScenarioData.edges;
  const res = currentPipelineResults;

  // 1. Draw Background Grid & Territory Outline
  ctx.strokeStyle = "#F1F5F9";
  ctx.lineWidth = 1;
  const gridSize = 40 * viewTransform.scale;
  for (let gx = (viewTransform.x % gridSize); gx < w; gx += gridSize) {
    ctx.beginPath(); ctx.moveTo(gx, 0); ctx.lineTo(gx, h); ctx.stroke();
  }
  for (let gy = (viewTransform.y % gridSize); gy < h; gy += gridSize) {
    ctx.beginPath(); ctx.moveTo(0, gy); ctx.lineTo(w, gy); ctx.stroke();
  }

  // 2. Draw Road Network (edges)
  ctx.strokeStyle = "#CBD5E1";
  ctx.lineWidth = 1.5;
  edges.forEach(ed => {
    const n1 = nodes.find(n => n.id === ed.u);
    const n2 = nodes.find(n => n.id === ed.v);
    if (n1 && n2) {
      const [x1, y1] = coords(n1.x, n1.y);
      const [x2, y2] = coords(n2.x, n2.y);
      ctx.beginPath();
      ctx.moveTo(x1, y1);
      ctx.lineTo(x2, y2);
      ctx.stroke();
    }
  });

  // 3. Draw 2-Opt Diff Mode (if enabled)
  const showDiff = document.getElementById("toggleShowDiff")?.checked;
  if (showDiff && res.nnResult && res.use2Opt) {
    // Draw raw NN tour in dashed red
    const nnTour = res.nnResult.tour;
    ctx.strokeStyle = "#EF444488";
    ctx.lineWidth = 2.5;
    ctx.setLineDash([5, 5]);
    ctx.beginPath();
    for (let i = 0; i < nnTour.length - 1; i++) {
      const n1 = nodes.find(n => n.id === nnTour[i]);
      const n2 = nodes.find(n => n.id === nnTour[i + 1]);
      if (n1 && n2) {
        const [x1, y1] = coords(n1.x, n1.y);
        const [x2, y2] = coords(n2.x, n2.y);
        if (i === 0) ctx.moveTo(x1, y1);
        ctx.lineTo(x2, y2);
      }
    }
    ctx.stroke();
    ctx.setLineDash([]);
  }

  // 4. Draw Active Shortest Path Circuit (Turn-by-turn road)
  const tour = res.fullTurnRoad;
  if (tour.length > 1) {
    // Outer glow
    ctx.strokeStyle = "#10B98144";
    ctx.lineWidth = 8;
    ctx.lineCap = "round";
    ctx.lineJoin = "round";
    ctx.beginPath();
    for (let i = 0; i < tour.length - 1; i++) {
      const n1 = nodes.find(n => n.id === tour[i]);
      const n2 = nodes.find(n => n.id === tour[i + 1]);
      if (n1 && n2) {
        const [x1, y1] = coords(n1.x, n1.y);
        const [x2, y2] = coords(n2.x, n2.y);
        if (i === 0) ctx.moveTo(x1, y1);
        ctx.lineTo(x2, y2);
      }
    }
    ctx.stroke();

    // Solid core line
    ctx.strokeStyle = "#059669";
    ctx.lineWidth = 3.5;
    ctx.stroke();

    // Draw directional arrows
    for (let i = 0; i < tour.length - 1; i++) {
      const n1 = nodes.find(n => n.id === tour[i]);
      const n2 = nodes.find(n => n.id === tour[i + 1]);
      if (n1 && n2) {
        const [x1, y1] = coords(n1.x, n1.y);
        const [x2, y2] = coords(n2.x, n2.y);
        const mx = (x1 + x2) / 2;
        const my = (y1 + y2) / 2;
        const angle = Math.atan2(y2 - y1, x2 - x1);
        drawArrow(ctx, mx, my, angle, "#047857");
      }
    }
  }

  // 5. Draw Animated Courier Van (if playing)
  if (animationState.isPlaying && tour.length > 1) {
    const segIdx = animationState.segmentIdx;
    const n1 = nodes.find(n => n.id === tour[segIdx]);
    const n2 = nodes.find(n => n.id === tour[(segIdx + 1) % tour.length]);
    if (n1 && n2) {
      const [x1, y1] = coords(n1.x, n1.y);
      const [x2, y2] = coords(n2.x, n2.y);
      const vx = x1 + (x2 - x1) * animationState.progress;
      const vy = y1 + (y2 - y1) * animationState.progress;
      const angle = Math.atan2(y2 - y1, x2 - x1);
      drawVehicle(ctx, vx, vy, angle);
    }
  }

  // 6. Draw Nodes
  nodes.forEach(nd => {
    const [x, y] = coords(nd.x, nd.y);
    const isDepot = nd.id === currentScenarioData.depot_id;
    const isVisited = res.finalTour.includes(nd.id);
    const isSelected = selectedNodeId === nd.id;
    const isHovered = hoveredNode && hoveredNode.id === nd.id;

    if (isDepot) {
      // Central Depot
      ctx.fillStyle = "#EF4444";
      ctx.fillRect(x - 10, y - 10, 20, 20);
      ctx.strokeStyle = "#FFFFFF";
      ctx.lineWidth = 2;
      ctx.strokeRect(x - 10, y - 10, 20, 20);

      ctx.fillStyle = "#991B1B";
      ctx.font = "bold 12px sans-serif";
      ctx.fillText("DEPOT (0)", x + 14, y + 4);
    } else if (isVisited) {
      // Visited Delivery Stop
      const stopSeq = res.finalTour.indexOf(nd.id);

      ctx.beginPath();
      ctx.arc(x, y, isSelected || isHovered ? 12 : 9, 0, Math.PI * 2);
      ctx.fillStyle = isSelected ? "#4338CA" : "#2563EB";
      ctx.fill();
      ctx.strokeStyle = "#FFFFFF";
      ctx.lineWidth = 2.5;
      ctx.stroke();

      // Number badge
      ctx.fillStyle = "#FFFFFF";
      ctx.font = "bold 10px sans-serif";
      ctx.textAlign = "center";
      ctx.textBaseline = "middle";
      ctx.fillText(stopSeq, x, y);
      ctx.textAlign = "left";
      ctx.textBaseline = "alphabetic";

      // Label
      ctx.fillStyle = isSelected ? "#312E81" : "#1E3A8A";
      ctx.font = "bold 11px sans-serif";
      ctx.fillText(`${nd.name.slice(0, 16)}`, x + 14, y + 4);
    } else {
      // Unvisited Hub / Junction
      ctx.beginPath();
      ctx.arc(x, y, 4, 0, Math.PI * 2);
      ctx.fillStyle = "#94A3B8";
      ctx.fill();
    }
  });

  // 7. Draw Tooltip (if hovering)
  if (hoveredNode) {
    drawNodeTooltip(ctx, hoveredNode, coords);
  }
}

function drawVehicle(ctx, x, y, angle) {
  ctx.save();
  ctx.translate(x, y);
  ctx.rotate(angle);

  // Pulse shadow
  ctx.beginPath();
  ctx.arc(0, 0, 16, 0, Math.PI * 2);
  ctx.fillStyle = "#10B98133";
  ctx.fill();

  // Van body
  ctx.fillStyle = "#0F172A";
  ctx.fillRect(-12, -7, 24, 14);
  // Cab
  ctx.fillStyle = "#38BDF8";
  ctx.fillRect(4, -5, 6, 10);
  // Headlights
  ctx.fillStyle = "#FDE047";
  ctx.fillRect(12, -5, 2, 3);
  ctx.fillRect(12, 2, 2, 3);

  ctx.restore();
}

function drawArrow(ctx, x, y, angle, color) {
  const size = 7;
  ctx.save();
  ctx.translate(x, y);
  ctx.rotate(angle);
  ctx.fillStyle = color;
  ctx.beginPath();
  ctx.moveTo(0, 0);
  ctx.lineTo(-size, -size / 2);
  ctx.lineTo(-size, size / 2);
  ctx.closePath();
  ctx.fill();
  ctx.restore();
}

function drawNodeTooltip(ctx, node, coords) {
  const [nx, ny] = coords(node.x, node.y);
  const res = currentPipelineResults;
  const parcelsHere = res.packingPlan.selected.filter(p => p.destination_node === node.id);

  const textLines = [
    node.is_depot ? "Central Depot (Start & Return)" : node.name,
    node.address,
    `Parcels: ${parcelsHere.length} loaded (${parcelsHere.reduce((s,p)=>s+p.weight,0)} kg)`
  ];

  ctx.font = "11px sans-serif";
  const boxW = 200;
  const boxH = 65;
  const tx = Math.min(nx + 15, ctx.canvas.width - boxW - 10);
  const ty = Math.max(10, ny - boxH - 10);

  ctx.fillStyle = "#0F172ACC";
  ctx.beginPath();
  ctx.roundRect(tx, ty, boxW, boxH, 6);
  ctx.fill();

  ctx.fillStyle = "#FFFFFF";
  ctx.font = "bold 11px sans-serif";
  ctx.fillText(textLines[0], tx + 10, ty + 18);
  ctx.fillStyle = "#CBD5E1";
  ctx.font = "10px sans-serif";
  ctx.fillText(textLines[1], tx + 10, ty + 34);
  ctx.fillStyle = "#34D399";
  ctx.font = "semibold 10px sans-serif";
  ctx.fillText(textLines[2], tx + 10, ty + 50);
}


// ============================================================================
// 4. ANIMATION LOOP & SIMULATION CONTROLS
// ============================================================================

function togglePlaySimulation() {
  if (animationState.isPlaying) {
    stopVehicleAnimation();
  } else {
    startVehicleAnimation();
  }
}

function startVehicleAnimation() {
  if (!currentPipelineResults || currentPipelineResults.fullTurnRoad.length < 2) return;
  animationState.isPlaying = true;
  document.getElementById("btnPlaySim").innerText = "⏸ Pause Simulation";
  document.getElementById("btnPlaySim").className = "px-3 py-1.5 rounded-lg bg-amber-600 hover:bg-amber-700 text-white font-semibold text-xs transition shadow-sm";

  let lastTime = performance.now();
  function loop(currentTime) {
    if (!animationState.isPlaying) return;
    const delta = (currentTime - lastTime) / 1000.0;
    lastTime = currentTime;

    const tour = currentPipelineResults.fullTurnRoad;
    // Step vehicle forward
    animationState.progress += delta * animationState.speed * 0.8;
    if (animationState.progress >= 1.0) {
      animationState.progress = 0;
      animationState.segmentIdx = (animationState.segmentIdx + 1) % (tour.length - 1);
    }

    drawCanvas();
    animationState.reqId = requestAnimationFrame(loop);
  }
  animationState.reqId = requestAnimationFrame(loop);
}

function stopVehicleAnimation() {
  animationState.isPlaying = false;
  if (animationState.reqId) cancelAnimationFrame(animationState.reqId);
  const btn = document.getElementById("btnPlaySim");
  if (btn) {
    btn.innerText = "▶ Play Delivery Route Simulation";
    btn.className = "px-3 py-1.5 rounded-lg bg-emerald-600 hover:bg-emerald-700 text-white font-semibold text-xs transition shadow-sm";
  }
  drawCanvas();
}

function resetSimulation() {
  stopVehicleAnimation();
  animationState.segmentIdx = 0;
  animationState.progress = 0;
  drawCanvas();
}


// ============================================================================
// 5. CUSTOM PARCEL ADDER & IN-BROWSER BENCHMARK RUNNER
// ============================================================================

function openAddParcelModal() {
  document.getElementById("modalAddParcel").classList.remove("hidden");
}

function closeAddParcelModal() {
  document.getElementById("modalAddParcel").classList.add("hidden");
}

function handleAddCustomParcel(e) {
  e.preventDefault();
  const destId = parseInt(document.getElementById("newParcelDest").value, 10);
  const weight = parseInt(document.getElementById("newParcelWeight").value, 10);
  const priority = parseInt(document.getElementById("newParcelPriority").value, 10);
  const deadline = parseFloat(document.getElementById("newParcelDeadline").value);
  const baseVal = parseInt(document.getElementById("newParcelBaseVal").value, 10);

  const customP = {
    id: `C${customAddedParcels.length + 1}`,
    destination_node: destId,
    weight,
    priority,
    deadline_hours: deadline,
    base_value: baseVal,
    composite_value: 0
  };
  customP.composite_value = calculateCompositeValue(customP);

  customAddedParcels.push(customP);
  closeAddParcelModal();
  runPipeline();
}

// In-Browser Live Benchmark Runner
function runInBrowserBenchmark() {
  const statusEl = document.getElementById("benchmarkLiveStatus");
  if (statusEl) statusEl.innerText = "Running client-side scaling benchmark...";

  setTimeout(() => {
    const sizes = [10, 50, 100, 250, 500, 1000];
    const qsTimes = [];
    const msTimes = [];

    sizes.forEach(n => {
      const synthetic = Array.from({ length: n }, (_, i) => ({
        id: `P${i}`,
        weight: (i % 10) + 2,
        priority: (i % 5) + 1,
        deadline_hours: (i % 20) + 1.0,
        base_value: 20,
        composite_value: 50
      }));

      // QS
      const t0 = performance.now();
      quickSort(synthetic, null);
      qsTimes.push(performance.now() - t0);

      // MS
      const t1 = performance.now();
      mergeSort(synthetic, null);
      msTimes.push(performance.now() - t1);
    });

    if (chartInstances.sorting) {
      chartInstances.sorting.data.datasets[0].data = qsTimes.map(t => Number(t.toFixed(3)));
      chartInstances.sorting.data.datasets[1].data = msTimes.map(t => Number(t.toFixed(3)));
      chartInstances.sorting.update();
    }

    if (statusEl) statusEl.innerText = `✓ Benchmark completed on your device in ${(qsTimes.reduce((a,b)=>a+b,0)+msTimes.reduce((a,b)=>a+b,0)).toFixed(2)} ms!`;
  }, 50);
}

function initBenchmarkCharts() {
  if (typeof Chart === "undefined") return;

  const ctxSort = document.getElementById("chartSorting")?.getContext("2d");
  if (ctxSort) {
    chartInstances.sorting = new Chart(ctxSort, {
      type: "line",
      data: {
        labels: [10, 50, 100, 250, 500, 1000],
        datasets: [
          { label: "QuickSort (Median-of-3)", data: [0.023, 0.082, 0.164, 0.512, 1.305, 3.148], borderColor: "#E11D48", backgroundColor: "#E11D4811", tension: 0.2 },
          { label: "MergeSort (Stable O(N log N))", data: [0.013, 0.071, 0.141, 0.435, 1.122, 2.599], borderColor: "#2563EB", backgroundColor: "#2563EB11", tension: 0.2 }
        ]
      },
      options: { responsive: true, plugins: { legend: { position: "bottom" } } }
    });
  }

  const ctxKnap = document.getElementById("chartKnapsack")?.getContext("2d");
  if (ctxKnap) {
    chartInstances.knapsack = new Chart(ctxKnap, {
      type: "line",
      data: {
        labels: [200, 1000, 3750, 12000, 30000, 60000],
        datasets: [{
          label: "0/1 Knapsack DP Complexity vs (N × W)",
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

  const ctxTsp = document.getElementById("chartTSP")?.getContext("2d");
  if (ctxTsp) {
    chartInstances.tsp = new Chart(ctxTsp, {
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
  document.querySelectorAll(".tab-btn").forEach(el => {
    el.classList.remove("border-blue-600", "text-blue-600");
    el.classList.add("border-transparent", "text-slate-500");
  });

  document.getElementById(`tab-${tabId}`)?.classList.remove("hidden");
  const activeBtn = document.getElementById(`btn-tab-${tabId}`);
  if (activeBtn) {
    activeBtn.classList.remove("border-transparent", "text-slate-500");
    activeBtn.classList.add("border-blue-600", "text-blue-600");
  }
}


// ============================================================================
// 6. INITIALIZATION ON DOM READY
// ============================================================================

window.addEventListener("DOMContentLoaded", () => {
  // Controls
  document.getElementById("scenarioSelect").addEventListener("change", e => loadScenario(e.target.value));
  document.getElementById("capacitySlider").addEventListener("input", e => {
    document.getElementById("capacityValue").innerText = `${e.target.value} kg`;
    runPipeline();
  });
  document.getElementById("sortAlgorithmSelect").addEventListener("change", runPipeline);
  document.getElementById("toggle2Opt").addEventListener("change", runPipeline);
  document.getElementById("toggleShowDiff")?.addEventListener("change", drawCanvas);

  // Buttons
  document.getElementById("btnPlaySim")?.addEventListener("click", togglePlaySimulation);
  document.getElementById("btnResetSim")?.addEventListener("click", resetSimulation);
  document.getElementById("btnZoomIn")?.addEventListener("click", () => { viewTransform.scale *= 1.2; drawCanvas(); });
  document.getElementById("btnZoomOut")?.addEventListener("click", () => { viewTransform.scale /= 1.2; drawCanvas(); });
  document.getElementById("btnResetView")?.addEventListener("click", () => { resetViewTransform(); drawCanvas(); });

  // Add Parcel Modal
  document.getElementById("btnAddParcel")?.addEventListener("click", openAddParcelModal);
  document.getElementById("btnCancelAddParcel")?.addEventListener("click", closeAddParcelModal);
  document.getElementById("formAddParcel")?.addEventListener("submit", handleAddCustomParcel);

  // Live in-browser benchmark
  document.getElementById("btnRunLiveBenchmark")?.addEventListener("click", runInBrowserBenchmark);

  initCanvasInteractions();
  loadScenario("small_dataset");
  initBenchmarkCharts();
});
