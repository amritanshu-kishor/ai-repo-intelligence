// Repository Intelligence Testing - Frontend Logic

const API_BASE = 'http://localhost:5000/api';

// DOM Elements
const uploadBtn = document.getElementById('uploadBtn');
const zipInput = document.getElementById('zipInput');
const uploadStatus = document.getElementById('upload-status');
const repoInfo = document.getElementById('repo-info');
const repoName = document.getElementById('repo-name');
const fileCount = document.getElementById('file-count');
const fileList = document.getElementById('file-list');
const statusBadge = document.getElementById('status-badge');
const repoBadge = document.getElementById('repo-badge');

const queryInput = document.getElementById('queryInput');
const analyzeBtn = document.getElementById('analyzeBtn');
const loading = document.getElementById('loading');
const responseOutput = document.getElementById('response-output');
const graphOutput = document.getElementById('graph-output');

// Graph elements
const fitGraphBtn = document.getElementById('fitGraphBtn');
const resetGraphBtn = document.getElementById('resetGraphBtn');
const graphStats = document.getElementById('graph-stats');

// Example query buttons
const exampleBtns = document.querySelectorAll('.example-btn');

// Cytoscape instance
let cy = null;
let lastGraphData = null;
const filesOnlyToggle = document.getElementById('filesOnlyToggle');

// Initialize
checkHealth();

// Event Listeners
uploadBtn.addEventListener('click', () => zipInput.click());
zipInput.addEventListener('change', handleFileUpload);
analyzeBtn.addEventListener('click', handleQuery);
queryInput.addEventListener('keypress', (e) => {
    if (e.key === 'Enter') handleQuery();
});

exampleBtns.forEach(btn => {
    btn.addEventListener('click', () => {
        queryInput.value = btn.dataset.query;
        handleQuery();
    });
});

// Check API Health
async function checkHealth() {
    try {
        const response = await fetch(`${API_BASE}/health`);
        const data = await response.json();
        
        if (data.status === 'ready') {
            const llm = data.llm_configured ? (data.llm_provider || 'llm') : 'no API key';
            statusBadge.textContent = data.llm_configured ? 'Ready' : 'LLM key missing';
            statusBadge.className = data.llm_configured ? 'badge badge-ready' : 'badge badge-error';
            if (!data.llm_configured) {
                console.warn(`LLM not configured (${llm}). Edit repo-ai/.env and restart app.py`);
            }
        }
        
        if (data.active_repository && data.active_repository !== 'none') {
            repoBadge.textContent = `Repository: ${data.active_repository}`;
            repoBadge.className = 'badge badge-info';
        }
    } catch (error) {
        statusBadge.textContent = 'API Offline';
        statusBadge.className = 'badge badge-error';
        console.error('Health check failed:', error);
    }
}

// Handle File Upload
async function handleFileUpload(event) {
    const file = event.target.files[0];
    if (!file) return;
    
    uploadStatus.textContent = 'Uploading...';
    uploadBtn.disabled = true;
    
    const formData = new FormData();
    formData.append('file', file);
    
    try {
        const response = await fetch(`${API_BASE}/upload-repository`, {
            method: 'POST',
            body: formData
        });
        
        const data = await response.json();
        
        if (data.success) {
            uploadStatus.textContent = '✓ Upload successful';
            uploadStatus.style.color = '#3fb950';
            
            // Update repository info
            repoName.textContent = data.repository;
            fileCount.textContent = data.file_count;
            repoBadge.textContent = `Repository: ${data.repository}`;
            repoBadge.className = 'badge badge-info';
            
            // Display files
            fileList.innerHTML = data.files.map(f => `<div>📄 ${f}</div>`).join('');
            repoInfo.style.display = 'block';
            
            // Enable query
            queryInput.disabled = false;
            analyzeBtn.disabled = false;
            
            // Load and render graph
            loadRepositoryGraph(data.repository);
        } else {
            uploadStatus.textContent = `✗ Error: ${data.error}`;
            uploadStatus.style.color = '#f85149';
        }
    } catch (error) {
        uploadStatus.textContent = `✗ Upload failed: ${error.message}`;
        uploadStatus.style.color = '#f85149';
        console.error('Upload error:', error);
    } finally {
        uploadBtn.disabled = false;
    }
}

// Handle Query
async function handleQuery() {
    const query = queryInput.value.trim();
    if (!query) {
        alert('Please enter a question');
        return;
    }
    
    // Show loading
    loading.style.display = 'block';
    responseOutput.innerHTML = '';
    graphOutput.innerHTML = '';
    analyzeBtn.disabled = true;
    
    try {
        const response = await fetch(`${API_BASE}/ask-query`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ query })
        });
        
        const data = await response.json();
        
        if (data.success) {
            displayResponse(data.result);
            displayGraphDebug(data.result);
            
            // Highlight affected nodes in graph
            if (data.result.intelligence && data.result.intelligence.affected_files) {
                highlightAffectedNodes(data.result.intelligence.affected_files);
            }
        } else {
            responseOutput.innerHTML = `<div class="placeholder" style="color:#f85149;">Error: ${data.error}</div>`;
        }
    } catch (error) {
        responseOutput.innerHTML = `<div class="placeholder" style="color:#f85149;">Request failed: ${error.message}</div>`;
        console.error('Query error:', error);
    } finally {
        loading.style.display = 'none';
        analyzeBtn.disabled = false;
    }
}

// Display Response
function displayResponse(result) {
    const intelligence = result.intelligence || {};
    const impact = result.impact || {};
    const graph = result.graph || {};
    
    let html = '<div class="response-content">';
    
    // Summary
    if (intelligence.summary) {
        html += `
            <div class="response-section-title">Analysis</div>
            <div class="response-text response-markdown">${formatMarkdown(intelligence.summary)}</div>
        `;
    }
    
    // Affected Files
    if (intelligence.affected_files && intelligence.affected_files.length > 0) {
        html += `
            <div class="response-section-title">📂 Affected Files</div>
            <ul class="response-list">
                ${intelligence.affected_files.map(f => 
                    `<li><strong>${f.path || f.id}</strong> <span style="color:#8b949e;">(${f.relation})</span></li>`
                ).join('')}
            </ul>
        `;
    }
    
    // Dependency Chain
    if (intelligence.dependency_chain && intelligence.dependency_chain.length > 0) {
        html += `
            <div class="response-section-title">🔗 Dependency Reasoning</div>
            <ul class="response-list">
                ${intelligence.dependency_chain.slice(0, 5).map(chain => 
                    `<li>${typeof chain === 'string' ? escapeHtml(chain) : JSON.stringify(chain)}</li>`
                ).join('')}
            </ul>
        `;
    }
    
    // Recommendations
    if (intelligence.recommendations && intelligence.recommendations.length > 0) {
        html += `
            <div class="response-section-title">💡 Recommendations</div>
            <ul class="response-list">
                ${intelligence.recommendations.map(rec => 
                    `<li>${escapeHtml(rec)}</li>`
                ).join('')}
            </ul>
        `;
    }
    
    // Meta Info
    const riskClass = intelligence.risk_level === 'high' ? 'risk-high' : 
                      intelligence.risk_level === 'medium' ? 'risk-medium' : 'risk-low';
    
    html += `
        <div class="meta-info">
            <div class="meta-item">
                <div class="meta-label">Risk Level</div>
                <div class="meta-value ${riskClass}">${intelligence.risk_level || 'unknown'}</div>
            </div>
            <div class="meta-item">
                <div class="meta-label">Confidence</div>
                <div class="meta-value">${(intelligence.confidence_score || 0).toFixed(2)}</div>
            </div>
            <div class="meta-item">
                <div class="meta-label">Propagation Depth</div>
                <div class="meta-value">${graph.propagation_depth || 0}</div>
            </div>
            <div class="meta-item">
                <div class="meta-label">Impact Severity</div>
                <div class="meta-value">${impact.impact_severity || 'unknown'}</div>
            </div>
        </div>
    `;
    
    html += '</div>';
    responseOutput.innerHTML = html;
}

// Display Graph Debug
function displayGraphDebug(result) {
    const graph = result.graph || {};
    const impact = result.impact || {};
    
    let debug = {
        'Focus Node': graph.focus_label || graph.focus_node_id || 'N/A',
        'Propagation Depth': graph.propagation_depth || 0,
        'Direct Dependencies': (graph.direct_dependencies || []).length,
        'Indirect Dependencies': (graph.indirect_dependencies || []).length,
        'Upstream Dependencies': (graph.upstream_dependencies || []).length,
        'Circular Dependencies': (graph.circular_dependencies || []).length,
        'Risk Score': (impact.risk_score || 0).toFixed(2),
        'Total Affected': (impact.propagation_scope || {}).total_affected || 0,
    };
    
    let html = '<pre>';
    html += '=== Graph Reasoning Debug ===\n\n';
    for (const [key, value] of Object.entries(debug)) {
        html += `${key}: ${value}\n`;
    }
    
    if (graph.traversal_explain && graph.traversal_explain.length > 0) {
        html += '\n=== Traversal Explanation ===\n\n';
        graph.traversal_explain.forEach(line => {
            html += `• ${escapeHtml(line)}\n`;
        });
    }
    
    if (graph.circular_dependencies && graph.circular_dependencies.length > 0) {
        html += '\n=== Circular Dependencies ===\n\n';
        graph.circular_dependencies.forEach((cycle, i) => {
            html += `Cycle ${i + 1}: ${cycle.join(' → ')}\n`;
        });
    }
    
    html += '</pre>';
    graphOutput.innerHTML = html;
}

// Load and Render Repository Graph
async function loadRepositoryGraph(repositoryId) {
    try {
        const response = await fetch(`${API_BASE}/graph/${repositoryId}`);
        const data = await response.json();
        
        if (data.success && data.graph) {
            lastGraphData = data.graph;
            renderGraph(data.graph);
        }
    } catch (error) {
        console.error('Failed to load graph:', error);
    }
}

function basename(path) {
    if (!path) return '';
    return String(path).replace(/\\/g, '/').split('/').pop();
}

function normalizeElements(graphData) {
    let elements = [];
    if (graphData.elements && graphData.elements.length) {
        elements = graphData.elements.map(el => {
            if (el.data && (el.data.id || el.data.source)) return el;
            return { data: el };
        });
    } else {
        const nodes = graphData.nodes || [];
        const edges = graphData.edges || [];
        nodes.forEach(n => {
            const data = n.data || n;
            elements.push({ data: data, classes: n.classes || data.node_type || '' });
        });
        edges.forEach(e => {
            const data = e.data || e;
            elements.push({ data: data, classes: e.classes || data.edge_type || '' });
        });
    }
    return elements;
}

function filterFileLevelElements(elements) {
    const fileTypes = new Set(['file', 'entrypoint', 'module', 'external']);
    const nodeIds = new Set();
    elements.forEach(el => {
        const d = el.data;
        if (!d.source) {
            const t = (d.node_type || d.type || 'file').toLowerCase();
            if (fileTypes.has(t) || !d.node_type) nodeIds.add(d.id);
        }
    });
    const filtered = elements.filter(el => {
        const d = el.data;
        if (!d.source) return nodeIds.has(d.id);
        return nodeIds.has(d.source) && nodeIds.has(d.target);
    });
    return filtered.length ? filtered : elements;
}

// Render Cytoscape Graph
function renderGraph(graphData) {
    const container = document.getElementById('cy');
    container.innerHTML = '';

    let elements = normalizeElements(graphData);
    if (filesOnlyToggle && filesOnlyToggle.checked) {
        elements = filterFileLevelElements(elements);
    }

    elements = elements.map(el => {
        const d = { ...el.data };
        if (!d.source) {
            const path = d.full_path || d.tooltip || d.id || '';
            d.label = d.label || basename(path) || d.id;
            d.shortLabel = basename(d.label) || d.label;
        } else {
            d.label = d.label || d.relation || d.relationship || 'imports';
        }
        return { ...el, data: d };
    });

    if (elements.length === 0) {
        container.innerHTML = '<p class="placeholder">No graph data available</p>';
        return;
    }

    cy = cytoscape({
        container: container,
        elements: elements,
        style: [
            {
                selector: 'node',
                style: {
                    'shape': 'round-rectangle',
                    'background-color': '#4f46e5',
                    'label': 'data(label)',
                    'color': '#f3f4f6',
                    'text-valign': 'center',
                    'text-halign': 'center',
                    'text-wrap': 'ellipsis',
                    'text-max-width': '90px',
                    'font-size': '10px',
                    'font-weight': '600',
                    'text-outline-color': '#0a0e1a',
                    'text-outline-width': 2,
                    'width': 'label',
                    'height': 'label',
                    'padding': '10px',
                    'min-width': '56px',
                    'min-height': '28px',
                    'border-width': 2,
                    'border-color': '#818cf8',
                }
            },
            {
                selector: 'node[type = "entrypoint"]',
                style: {
                    'background-color': '#059669',
                    'border-color': '#34d399',
                }
            },
            {
                selector: 'node[node_type = "external"]',
                style: {
                    'background-color': '#b45309',
                    'border-color': '#fbbf24',
                    'shape': 'ellipse',
                }
            },
            {
                selector: 'node.highlighted',
                style: {
                    'background-color': '#dc2626',
                    'border-color': '#fca5a5',
                    'border-width': 3,
                }
            },
            {
                selector: 'node.focus',
                style: {
                    'background-color': '#10b981',
                    'border-color': '#6ee7b7',
                    'border-width': 3,
                }
            },
            {
                selector: 'edge',
                style: {
                    'width': 2.5,
                    'line-color': '#64748b',
                    'target-arrow-color': '#94a3b8',
                    'target-arrow-shape': 'triangle',
                    'curve-style': 'bezier',
                    'arrow-scale': 1.2,
                    'label': 'data(label)',
                    'font-size': '8px',
                    'color': '#9ca3af',
                    'text-rotation': 'autorotate',
                    'text-margin-y': -8,
                    'opacity': 0.85,
                }
            },
            {
                selector: 'edge.highlighted',
                style: {
                    'line-color': '#22c55e',
                    'target-arrow-color': '#22c55e',
                    'width': 3.5,
                    'opacity': 1,
                    'z-index': 998,
                }
            },
        ],
        layout: {
            name: 'cose',
            animate: true,
            animationDuration: 600,
            nodeRepulsion: 8000,
            idealEdgeLength: 140,
            edgeElasticity: 100,
            nestingFactor: 1.2,
            gravity: 1,
            numIter: 1500,
        },
        minZoom: 0.2,
        maxZoom: 4,
        wheelSensitivity: 0.2,
    });
    
    // Update stats
    const nodeCount = cy.nodes().length;
    const edgeCount = cy.edges().length;
    graphStats.textContent = `${nodeCount} nodes, ${edgeCount} edges`;
    
    cy.on('tap', 'node', function(evt) {
        const node = evt.target;
        const data = node.data();
        cy.elements().removeClass('highlighted');
        node.addClass('highlighted');
        node.neighborhood().addClass('highlighted');
        if (graphStats) {
            const path = data.tooltip || data.full_path || data.id;
            graphStats.textContent = `${data.label} — ${node.degree()} connection(s) — ${path}`;
        }
    });
    
    // Add premium hover effect
    cy.on('mouseover', 'node', function(evt) {
        const node = evt.target;
        node.style({
            'border-width': '5px',
            'border-color': '#8b5cf6',
            'background-color': '#7c3aed'
        });
        document.body.style.cursor = 'pointer';
    });
    
    cy.on('mouseout', 'node', function(evt) {
        const node = evt.target;
        if (!node.hasClass('highlighted') && !node.hasClass('focus')) {
            node.style({
                'border-width': '3px',
                'border-color': '#8b5cf6',
                'background-color': '#6366f1'
            });
        }
        document.body.style.cursor = 'default';
    });
    
    // Add edge hover effect
    cy.on('mouseover', 'edge', function(evt) {
        const edge = evt.target;
        if (!edge.hasClass('highlighted')) {
            edge.style({
                'width': 3,
                'opacity': 0.9,
                'line-color': '#6366f1',
                'target-arrow-color': '#6366f1'
            });
        }
    });
    
    cy.on('mouseout', 'edge', function(evt) {
        const edge = evt.target;
        if (!edge.hasClass('highlighted')) {
            edge.style({
                'width': 2,
                'opacity': 0.6,
                'line-color': '#374151',
                'target-arrow-color': '#374151'
            });
        }
    });
    
    // Fit graph to screen
    cy.fit(null, 50);
}

// Highlight Affected Nodes
function highlightAffectedNodes(affectedFiles) {
    if (!cy) return;
    
    // Reset all highlights
    cy.elements().removeClass('highlighted focus');
    
    // Highlight affected nodes
    affectedFiles.forEach(file => {
        const nodeId = file.path || file.id;
        const node = cy.getElementById(nodeId);
        
        if (node.length > 0) {
            if (file.relation === 'focus' || file.relation === 'direct') {
                node.addClass('focus');
            } else {
                node.addClass('highlighted');
            }
            
            // Highlight edges to/from this node
            node.connectedEdges().addClass('highlighted');
        }
    });
    
    // Fit to highlighted nodes
    const highlighted = cy.$('.highlighted, .focus');
    if (highlighted.length > 0) {
        cy.fit(highlighted, 50);
    }
}

// Graph Control Buttons
if (fitGraphBtn) {
    fitGraphBtn.addEventListener('click', () => {
        if (cy) cy.fit(null, 50);
    });
}

if (resetGraphBtn) {
    resetGraphBtn.addEventListener('click', () => {
        if (cy) {
            cy.zoom(1);
            cy.center();
        }
    });
}

if (filesOnlyToggle) {
    filesOnlyToggle.addEventListener('change', () => {
        if (lastGraphData) renderGraph(lastGraphData);
    });
}

// Utility
function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

function formatMarkdown(text) {
    if (!text) return '';
    let s = escapeHtml(text);
    s = s.replace(/^## (.+)$/gm, '<h3 class="md-h3">$1</h3>');
    s = s.replace(/^### (.+)$/gm, '<h4 class="md-h4">$1</h4>');
    s = s.replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>');
    s = s.replace(/^- (.+)$/gm, '<li>$1</li>');
    s = s.replace(/(<li>[\s\S]*?<\/li>)+/g, m => `<ul class="response-list">${m}</ul>`);
    s = s.replace(/\n\n/g, '</p><p>');
    return `<p>${s}</p>`;
}

// Made with Bob
