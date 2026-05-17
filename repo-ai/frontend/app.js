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
            statusBadge.textContent = 'Ready';
            statusBadge.className = 'badge badge-ready';
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
            <div class="response-section-title">📝 Explanation</div>
            <div class="response-text">${escapeHtml(intelligence.summary)}</div>
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
            renderGraph(data.graph);
        }
    } catch (error) {
        console.error('Failed to load graph:', error);
    }
}

// Render Cytoscape Graph
function renderGraph(graphData) {
    const container = document.getElementById('cy');
    container.innerHTML = ''; // Clear placeholder
    
    // Extract nodes and edges from graph data
    let elements = [];
    
    if (graphData.elements) {
        // Format 1: Cytoscape elements array
        elements = graphData.elements;
    } else if (graphData.nodes && graphData.edges) {
        // Format 2: Separate nodes and edges
        elements = [
            ...graphData.nodes.map(n => ({ data: n })),
            ...graphData.edges.map(e => ({ data: e }))
        ];
    }
    
    if (elements.length === 0) {
        container.innerHTML = '<p class="placeholder">No graph data available</p>';
        return;
    }
    
    // Initialize Cytoscape with premium styling
    cy = cytoscape({
        container: container,
        elements: elements,
        style: [
            {
                selector: 'node',
                style: {
                    'background-color': '#6366f1',
                    'label': 'data(label)',
                    'color': '#e5e7eb',
                    'text-valign': 'bottom',
                    'text-halign': 'center',
                    'text-margin-y': 8,
                    'font-size': '12px',
                    'font-weight': '600',
                    'text-outline-color': '#0a0e1a',
                    'text-outline-width': 2,
                    'width': '40px',
                    'height': '40px',
                    'border-width': '3px',
                    'border-color': '#8b5cf6',
                    'transition-property': 'background-color, border-color, width, height',
                    'transition-duration': '0.2s'
                }
            },
            {
                selector: 'node.highlighted',
                style: {
                    'background-color': '#ef4444',
                    'border-color': '#dc2626',
                    'border-width': '4px',
                    'width': '50px',
                    'height': '50px',
                    'z-index': 999
                }
            },
            {
                selector: 'node.focus',
                style: {
                    'background-color': '#10b981',
                    'border-color': '#059669',
                    'border-width': '4px',
                    'width': '50px',
                    'height': '50px',
                    'z-index': 999
                }
            },
            {
                selector: 'edge',
                style: {
                    'width': 2,
                    'line-color': '#374151',
                    'target-arrow-color': '#374151',
                    'target-arrow-shape': 'triangle',
                    'curve-style': 'bezier',
                    'arrow-scale': 1.3,
                    'opacity': 0.6,
                    'transition-property': 'line-color, width, opacity',
                    'transition-duration': '0.2s'
                }
            },
            {
                selector: 'edge.highlighted',
                style: {
                    'line-color': '#10b981',
                    'target-arrow-color': '#10b981',
                    'width': 3,
                    'opacity': 1,
                    'z-index': 998
                }
            }
        ],
        layout: {
            name: 'cose',
            animate: true,
            animationDuration: 500,
            nodeRepulsion: 10000,
            idealEdgeLength: 120,
            edgeElasticity: 100,
            nestingFactor: 5,
            gravity: 80,
            numIter: 1000,
            initialTemp: 200,
            coolingFactor: 0.95,
            minTemp: 1.0
        },
        minZoom: 0.1,
        maxZoom: 3,
        wheelSensitivity: 0.2
    });
    
    // Update stats
    const nodeCount = cy.nodes().length;
    const edgeCount = cy.edges().length;
    graphStats.textContent = `${nodeCount} nodes, ${edgeCount} edges`;
    
    // Add click handler for nodes
    cy.on('tap', 'node', function(evt) {
        const node = evt.target;
        const data = node.data();
        console.log('Clicked node:', data);
        
        // Highlight connected nodes
        cy.elements().removeClass('highlighted');
        node.addClass('highlighted');
        node.neighborhood().addClass('highlighted');
        
        // Show tooltip
        const filename = data.label || data.id;
        const fileType = data.type || 'Unknown';
        const degree = node.degree();
        
        console.log(`File: ${filename}`);
        console.log(`Type: ${fileType}`);
        console.log(`Connections: ${degree}`);
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

// Utility
function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

// Made with Bob
