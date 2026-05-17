// Repository Intelligence Platform - Frontend Logic
// Connects to EXISTING backend APIs - NO backend modifications

const API_BASE = 'http://localhost:5000/api';

// State Management
const state = {
    currentRepository: null,
    currentView: 'dashboard',
    isUploading: false,
    isAnalyzing: false,
    cy: null,
    recentSessions: []
};

// DOM Elements
const elements = {
    // Upload
    uploadBtn: document.getElementById('uploadBtn'),
    zipInput: document.getElementById('zipInput'),
    uploadZone: document.getElementById('upload-zone'),
    uploadProgress: document.getElementById('upload-progress'),
    progressFill: document.getElementById('progress-fill'),
    progressText: document.getElementById('progress-text'),
    progressPercent: document.getElementById('progress-percent'),
    
    // Repository Info
    repoInfo: document.getElementById('repo-info'),
    repoName: document.getElementById('repo-name'),
    fileCount: document.getElementById('file-count'),
    nodeCount: document.getElementById('node-count'),
    edgeCount: document.getElementById('edge-count'),
    cycleCount: document.getElementById('cycle-count'),
    
    // Chat
    chatMessages: document.getElementById('chat-messages'),
    queryInput: document.getElementById('queryInput'),
    analyzeBtn: document.getElementById('analyzeBtn'),
    
    // Intelligence Cards
    intelFiles: document.getElementById('intel-files'),
    intelNodes: document.getElementById('intel-nodes'),
    intelEdges: document.getElementById('intel-edges'),
    intelCycles: document.getElementById('intel-cycles'),
    
    // Graph
    cyContainer: document.getElementById('cy'),
    fitGraphBtn: document.getElementById('fitGraphBtn'),
    resetGraphBtn: document.getElementById('resetGraphBtn'),
    graphStats: document.getElementById('graph-stats'),
    
    // Console
    consoleOutput: document.getElementById('console-output'),
    
    // Status
    backendStatus: document.getElementById('backend-status'),
    backendStatusText: document.getElementById('backend-status-text'),
    parserStatus: document.getElementById('parser-status'),
    graphStatus: document.getElementById('graph-status'),
    aiStatus: document.getElementById('ai-status'),
    
    // Navigation
    navItems: document.querySelectorAll('.nav-item[data-view]'),
    viewContainers: {
        dashboard: document.getElementById('dashboard-view'),
        graph: document.getElementById('graph-view'),
        analysis: document.getElementById('analysis-view')
    },
    
    // Loading
    loadingOverlay: document.getElementById('loading-overlay'),
    loadingText: document.getElementById('loading-text'),
    
    // Sidebar
    sidebarRepoName: document.getElementById('sidebar-repo-name'),
    recentSessions: document.getElementById('recent-sessions')
};

// Initialize
document.addEventListener('DOMContentLoaded', () => {
    initializeEventListeners();
    checkBackendHealth();
    loadRecentSessions();
});

// Event Listeners
function initializeEventListeners() {
    // Upload
    elements.uploadBtn.addEventListener('click', () => elements.zipInput.click());
    elements.zipInput.addEventListener('change', handleFileUpload);
    
    // Drag and drop
    elements.uploadZone.addEventListener('dragover', handleDragOver);
    elements.uploadZone.addEventListener('dragleave', handleDragLeave);
    elements.uploadZone.addEventListener('drop', handleDrop);
    elements.uploadZone.addEventListener('click', () => elements.zipInput.click());
    
    // Chat
    elements.analyzeBtn.addEventListener('click', handleQuery);
    elements.queryInput.addEventListener('keypress', (e) => {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            handleQuery();
        }
    });
    
    // Example queries
    document.querySelectorAll('.example-query').forEach(btn => {
        btn.addEventListener('click', () => {
            elements.queryInput.value = btn.dataset.query;
            handleQuery();
        });
    });
    
    // Graph controls
    if (elements.fitGraphBtn) {
        elements.fitGraphBtn.addEventListener('click', () => {
            if (state.cy) state.cy.fit(null, 50);
        });
    }
    
    if (elements.resetGraphBtn) {
        elements.resetGraphBtn.addEventListener('click', () => {
            if (state.cy) {
                state.cy.zoom(1);
                state.cy.center();
            }
        });
    }
    
    // Navigation
    elements.navItems.forEach(item => {
        item.addEventListener('click', (e) => {
            e.preventDefault();
            const view = item.dataset.view;
            switchView(view);
        });
    });
}

// Backend Health Check
async function checkBackendHealth() {
    try {
        const response = await fetch(`${API_BASE}/health`);
        const data = await response.json();
        
        if (data.status === 'ready') {
            elements.backendStatus.classList.remove('offline');
            elements.backendStatusText.textContent = 'Backend Online';
            elements.parserStatus.classList.add('active');
            elements.graphStatus.classList.add('active');
            elements.aiStatus.classList.add('active');
            
            // Check if there's an active repository
            if (data.active_repository && data.active_repository !== 'none') {
                state.currentRepository = data.active_repository;
                loadRepositoryData(data.active_repository);
            }
        }
    } catch (error) {
        elements.backendStatus.classList.add('offline');
        elements.backendStatusText.textContent = 'Backend Offline';
        console.error('Health check failed:', error);
        addConsoleLog('ERROR: Backend connection failed', 'error');
    }
}

// Drag and Drop Handlers
function handleDragOver(e) {
    e.preventDefault();
    e.stopPropagation();
    elements.uploadZone.classList.add('dragover');
}

function handleDragLeave(e) {
    e.preventDefault();
    e.stopPropagation();
    elements.uploadZone.classList.remove('dragover');
}

function handleDrop(e) {
    e.preventDefault();
    e.stopPropagation();
    elements.uploadZone.classList.remove('dragover');
    
    const files = e.dataTransfer.files;
    if (files.length > 0 && files[0].name.endsWith('.zip')) {
        elements.zipInput.files = files;
        handleFileUpload({ target: { files: files } });
    } else {
        showNotification('Please drop a ZIP file', 'error');
    }
}

// File Upload Handler
async function handleFileUpload(event) {
    const file = event.target.files[0];
    if (!file) return;
    
    if (!file.name.endsWith('.zip')) {
        showNotification('Please select a ZIP file', 'error');
        return;
    }
    
    state.isUploading = true;
    elements.uploadZone.style.display = 'none';
    elements.uploadProgress.style.display = 'block';
    
    // Reset progress
    updateProgress(0, 'Uploading repository...');
    setProgressStep('upload', 'active');
    
    const formData = new FormData();
    formData.append('file', file);
    
    try {
        addConsoleLog(`Uploading ${file.name}...`);
        
        // Simulate upload progress
        updateProgress(25, 'Uploading...');
        
        const response = await fetch(`${API_BASE}/upload-repository`, {
            method: 'POST',
            body: formData
        });
        
        const data = await response.json();
        
        if (data.success) {
            setProgressStep('upload', 'complete');
            updateProgress(50, 'Extracting files...');
            setProgressStep('extract', 'active');
            
            await new Promise(resolve => setTimeout(resolve, 500));
            
            setProgressStep('extract', 'complete');
            updateProgress(75, 'Parsing repository...');
            setProgressStep('parse', 'active');
            
            await new Promise(resolve => setTimeout(resolve, 500));
            
            setProgressStep('parse', 'complete');
            updateProgress(90, 'Building dependency graph...');
            setProgressStep('graph', 'active');
            
            // Load repository data
            await loadRepositoryData(data.repository);
            
            setProgressStep('graph', 'complete');
            updateProgress(100, 'Complete!');
            
            addConsoleLog(`✓ Repository uploaded: ${data.repository}`, 'success');
            addConsoleLog(`  Files: ${data.file_count}`, 'info');
            
            // Hide progress after delay
            setTimeout(() => {
                elements.uploadProgress.style.display = 'none';
                elements.repoInfo.style.display = 'block';
            }, 1000);
            
            // Enable chat
            elements.queryInput.disabled = false;
            elements.analyzeBtn.disabled = false;
            
            // Save to recent sessions
            saveRecentSession(data.repository, data.file_count);
            
            showNotification('Repository uploaded successfully!', 'success');
        } else {
            throw new Error(data.error || 'Upload failed');
        }
    } catch (error) {
        console.error('Upload error:', error);
        addConsoleLog(`✗ Upload failed: ${error.message}`, 'error');
        showNotification(`Upload failed: ${error.message}`, 'error');
        
        // Reset UI
        elements.uploadProgress.style.display = 'none';
        elements.uploadZone.style.display = 'block';
    } finally {
        state.isUploading = false;
    }
}

// Load Repository Data
async function loadRepositoryData(repositoryId) {
    try {
        state.currentRepository = repositoryId;
        
        // Update UI
        elements.repoName.textContent = repositoryId;
        elements.sidebarRepoName.textContent = repositoryId;
        
        addConsoleLog(`Loading repository data for: ${repositoryId}`);
        
        // Fetch graph data
        const graphResponse = await fetch(`${API_BASE}/graph/${repositoryId}`);
        const graphData = await graphResponse.json();
        
        if (graphData.success && graphData.graph) {
            const graph = graphData.graph;
            
            // Update stats
            const nodeCount = graph.nodes ? graph.nodes.length : 0;
            const edgeCount = graph.edges ? graph.edges.length : 0;
            
            elements.fileCount.textContent = nodeCount;
            elements.nodeCount.textContent = nodeCount;
            elements.edgeCount.textContent = edgeCount;
            elements.cycleCount.textContent = '0'; // Will be updated if cycles are detected
            
            // Update intelligence cards
            elements.intelFiles.textContent = nodeCount;
            elements.intelNodes.textContent = nodeCount;
            elements.intelEdges.textContent = edgeCount;
            elements.intelCycles.textContent = '0';
            
            addConsoleLog(`✓ Graph loaded: ${nodeCount} nodes, ${edgeCount} edges`, 'success');
            
            // Render graph
            renderGraph(graph);
        } else {
            addConsoleLog('⚠ No graph data available', 'warning');
        }
    } catch (error) {
        console.error('Failed to load repository data:', error);
        addConsoleLog(`✗ Failed to load repository: ${error.message}`, 'error');
    }
}

// Render Cytoscape Graph
function renderGraph(graphData) {
    const container = elements.cyContainer;
    container.innerHTML = ''; // Clear placeholder
    
    // Extract nodes and edges
    let elements = [];
    
    if (graphData.elements) {
        elements = graphData.elements;
    } else if (graphData.nodes && graphData.edges) {
        elements = [
            ...graphData.nodes.map(n => ({ data: n })),
            ...graphData.edges.map(e => ({ data: e }))
        ];
    }
    
    if (elements.length === 0) {
        container.innerHTML = '<div class="graph-placeholder"><i class="fas fa-project-diagram"></i><p>No graph data available</p></div>';
        return;
    }
    
    addConsoleLog(`Rendering graph with ${elements.length} elements`);
    
    // Initialize Cytoscape
    state.cy = cytoscape({
        container: container,
        elements: elements,
        style: [
            {
                selector: 'node',
                style: {
                    'background-color': '#6366f1',
                    'label': 'data(label)',
                    'color': '#ffffff',
                    'text-valign': 'bottom',
                    'text-halign': 'center',
                    'text-margin-y': 5,
                    'font-size': '11px',
                    'font-weight': 'bold',
                    'text-outline-color': '#000000',
                    'text-outline-width': 2,
                    'width': '40px',
                    'height': '40px',
                    'border-width': '3px',
                    'border-color': '#4f46e5'
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
                    'line-color': '#6b7280',
                    'target-arrow-color': '#6b7280',
                    'target-arrow-shape': 'triangle',
                    'curve-style': 'bezier',
                    'arrow-scale': 1.5,
                    'opacity': 0.6
                }
            },
            {
                selector: 'edge.highlighted',
                style: {
                    'line-color': '#ef4444',
                    'target-arrow-color': '#ef4444',
                    'width': 3,
                    'opacity': 1,
                    'z-index': 999
                }
            }
        ],
        layout: {
            name: 'cose',
            animate: true,
            animationDuration: 500,
            nodeRepulsion: 12000,
            idealEdgeLength: 150,
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
    const nodeCount = state.cy.nodes().length;
    const edgeCount = state.cy.edges().length;
    elements.graphStats.textContent = `${nodeCount} nodes, ${edgeCount} edges`;
    
    addConsoleLog(`✓ Graph rendered: ${nodeCount} nodes, ${edgeCount} edges`, 'success');
    
    // Add node click handler
    state.cy.on('tap', 'node', function(evt) {
        const node = evt.target;
        const data = node.data();
        
        // Highlight connected nodes
        state.cy.elements().removeClass('highlighted focus');
        node.addClass('focus');
        node.neighborhood().addClass('highlighted');
        
        addConsoleLog(`Selected node: ${data.label || data.id}`, 'info');
    });
    
    // Add hover effect
    state.cy.on('mouseover', 'node', function(evt) {
        const node = evt.target;
        node.style({
            'border-width': '5px',
            'border-color': '#ffffff'
        });
    });
    
    state.cy.on('mouseout', 'node', function(evt) {
        const node = evt.target;
        if (!node.hasClass('highlighted') && !node.hasClass('focus')) {
            node.style({
                'border-width': '3px'
            });
        }
    });
    
    // Fit graph to screen
    state.cy.fit(null, 50);
}

// Handle Query
async function handleQuery() {
    const query = elements.queryInput.value.trim();
    if (!query) {
        showNotification('Please enter a question', 'warning');
        return;
    }
    
    if (!state.currentRepository) {
        showNotification('Please upload a repository first', 'warning');
        return;
    }
    
    state.isAnalyzing = true;
    elements.analyzeBtn.disabled = true;
    showLoading('Analyzing repository...');
    
    // Add user message to chat
    addChatMessage('user', query);
    
    addConsoleLog(`Query: ${query}`);
    
    try {
        const response = await fetch(`${API_BASE}/ask-query`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ query })
        });
        
        const data = await response.json();
        
        if (data.success) {
            const result = data.result;
            const intelligence = result.intelligence || {};
            
            // Add AI response to chat
            let responseText = intelligence.summary || 'Analysis complete.';
            
            if (intelligence.affected_files && intelligence.affected_files.length > 0) {
                responseText += '\n\n**Affected Files:**\n';
                intelligence.affected_files.slice(0, 5).forEach(f => {
                    responseText += `\n• ${f.path || f.id} (${f.relation})`;
                });
            }
            
            if (intelligence.recommendations && intelligence.recommendations.length > 0) {
                responseText += '\n\n**Recommendations:**\n';
                intelligence.recommendations.slice(0, 3).forEach(rec => {
                    responseText += `\n• ${rec}`;
                });
            }
            
            addChatMessage('system', responseText);
            
            // Highlight affected nodes in graph
            if (intelligence.affected_files && state.cy) {
                highlightAffectedNodes(intelligence.affected_files);
            }
            
            // Log to console
            addConsoleLog(`✓ Analysis complete`, 'success');
            if (intelligence.affected_files) {
                addConsoleLog(`  Affected files: ${intelligence.affected_files.length}`, 'info');
            }
            
        } else {
            addChatMessage('system', `Error: ${data.error}`);
            addConsoleLog(`✗ Query failed: ${data.error}`, 'error');
        }
    } catch (error) {
        console.error('Query error:', error);
        addChatMessage('system', `Request failed: ${error.message}`);
        addConsoleLog(`✗ Request failed: ${error.message}`, 'error');
    } finally {
        hideLoading();
        state.isAnalyzing = false;
        elements.analyzeBtn.disabled = false;
        elements.queryInput.value = '';
    }
}

// Highlight Affected Nodes
function highlightAffectedNodes(affectedFiles) {
    if (!state.cy) return;
    
    // Reset highlights
    state.cy.elements().removeClass('highlighted focus');
    
    // Highlight affected nodes
    affectedFiles.forEach(file => {
        const nodeId = file.path || file.id;
        const node = state.cy.getElementById(nodeId);
        
        if (node.length > 0) {
            if (file.relation === 'focus' || file.relation === 'direct') {
                node.addClass('focus');
            } else {
                node.addClass('highlighted');
            }
            
            // Highlight edges
            node.connectedEdges().addClass('highlighted');
        }
    });
    
    // Fit to highlighted nodes
    const highlighted = state.cy.$('.highlighted, .focus');
    if (highlighted.length > 0) {
        state.cy.fit(highlighted, 50);
    }
}

// Add Chat Message
function addChatMessage(type, content) {
    const messageDiv = document.createElement('div');
    messageDiv.className = `chat-message ${type}`;
    
    const icon = type === 'user' ? 'fa-user' : 'fa-robot';
    
    messageDiv.innerHTML = `
        <div class="message-icon">
            <i class="fas ${icon}"></i>
        </div>
        <div class="message-content">
            <p>${escapeHtml(content).replace(/\n/g, '<br>')}</p>
        </div>
    `;
    
    elements.chatMessages.appendChild(messageDiv);
    elements.chatMessages.scrollTop = elements.chatMessages.scrollHeight;
}

// Add Console Log
function addConsoleLog(message, type = 'info') {
    const logLine = document.createElement('div');
    logLine.className = 'console-line';
    
    const timestamp = new Date().toLocaleTimeString();
    const prompt = type === 'error' ? '✗' : type === 'success' ? '✓' : type === 'warning' ? '⚠' : '$';
    
    logLine.innerHTML = `
        <span class="console-prompt">${prompt}</span>
        <span class="console-text">[${timestamp}] ${escapeHtml(message)}</span>
    `;
    
    elements.consoleOutput.appendChild(logLine);
    elements.consoleOutput.scrollTop = elements.consoleOutput.scrollHeight;
}

// Progress Helpers
function updateProgress(percent, text) {
    elements.progressFill.style.width = `${percent}%`;
    elements.progressPercent.textContent = `${percent}%`;
    elements.progressText.textContent = text;
}

function setProgressStep(step, status) {
    const stepElement = document.getElementById(`step-${step}`);
    if (stepElement) {
        stepElement.classList.remove('active', 'complete');
        if (status) {
            stepElement.classList.add(status);
        }
    }
}

// View Switching
function switchView(viewName) {
    state.currentView = viewName;
    
    // Update navigation
    elements.navItems.forEach(item => {
        item.classList.remove('active');
        if (item.dataset.view === viewName) {
            item.classList.add('active');
        }
    });
    
    // Update views
    Object.keys(elements.viewContainers).forEach(key => {
        elements.viewContainers[key].style.display = key === viewName ? 'block' : 'none';
    });
    
    addConsoleLog(`Switched to ${viewName} view`);
}

// Recent Sessions
function saveRecentSession(repositoryId, fileCount) {
    const session = {
        id: repositoryId,
        fileCount: fileCount,
        timestamp: Date.now()
    };
    
    state.recentSessions.unshift(session);
    state.recentSessions = state.recentSessions.slice(0, 5); // Keep last 5
    
    localStorage.setItem('recentSessions', JSON.stringify(state.recentSessions));
    updateRecentSessionsUI();
}

function loadRecentSessions() {
    const saved = localStorage.getItem('recentSessions');
    if (saved) {
        state.recentSessions = JSON.parse(saved);
        updateRecentSessionsUI();
    }
}

function updateRecentSessionsUI() {
    if (state.recentSessions.length === 0) {
        elements.recentSessions.innerHTML = '<div class="empty-state">No recent sessions</div>';
        return;
    }
    
    elements.recentSessions.innerHTML = state.recentSessions.map(session => `
        <div class="nav-item" onclick="loadRepositoryData('${session.id}')">
            <i class="fas fa-folder"></i>
            <span>${session.id}</span>
        </div>
    `).join('');
}

// UI Helpers
function showLoading(text) {
    elements.loadingText.textContent = text;
    elements.loadingOverlay.style.display = 'flex';
}

function hideLoading() {
    elements.loadingOverlay.style.display = 'none';
}

function showNotification(message, type = 'info') {
    // Simple console notification for now
    console.log(`[${type.toUpperCase()}] ${message}`);
    addConsoleLog(message, type);
}

function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

// Made with Bob