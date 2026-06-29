// Repository Intelligence Platform - Frontend Controller

const API_BASE = 'http://localhost:5000/api';

// DOM Elements
const uploadBtn = document.getElementById('uploadBtn');
const uploadZone = document.getElementById('upload-zone');
const zipInput = document.getElementById('zipInput');
const uploadStatus = document.getElementById('upload-status');
const repoInfo = document.getElementById('repo-info');
const repoName = document.getElementById('repo-name');
const fileCount = document.getElementById('file-count');
const fileList = document.getElementById('file-list');
const statusBadge = null; // removed for production
const statusText = null;  // removed for production
const repoBadge = document.getElementById('repo-badge');
const repoStatusBar = document.getElementById('repo-status-bar');
const uploadProgressOverlay = document.getElementById('upload-progress-overlay');
const uploadProgressText = document.getElementById('upload-progress-text');

const queryInput = document.getElementById('queryInput');
const analyzeBtn = document.getElementById('analyzeBtn');
const loading = document.getElementById('loading');
const responseOutput = document.getElementById('response-output');
const graphOutput = document.getElementById('graph-output');

// Graph elements
const fitGraphBtn = document.getElementById('fitGraphBtn');
const resetGraphBtn = document.getElementById('resetGraphBtn');
const graphStats = document.getElementById('graph-stats');
const graphLayoutSelect = document.getElementById('graphLayoutSelect');
const nodeDetailPanel = document.getElementById('node-detail-panel');
const closeNodeInspectorBtn = document.getElementById('close-node-inspector');

// Example query buttons
const exampleBtns = document.querySelectorAll('.example-btn-modern');

// Copy console button
const copyConsoleBtn = document.getElementById('copyConsoleBtn');

// Cytoscape instance
let cy = null;
let lastGraphData = null;
const filesOnlyToggle = document.getElementById('filesOnlyToggle');

// Initialize Tabs
initTabs();

// Initialize Health Check
checkHealth();

// Event Listeners
if (uploadBtn) {
    uploadBtn.addEventListener('click', (e) => { 
        e.stopPropagation(); 
        zipInput.click(); 
    });
}

if (uploadZone) {
    uploadZone.addEventListener('click', () => zipInput.click());
    uploadZone.addEventListener('dragover', (e) => { 
        e.preventDefault(); 
        uploadZone.classList.add('drag-over'); 
    });
    uploadZone.addEventListener('dragleave', () => uploadZone.classList.remove('drag-over'));
    uploadZone.addEventListener('drop', (e) => {
        e.preventDefault();
        uploadZone.classList.remove('drag-over');
        if (e.dataTransfer.files.length) {
            zipInput.files = e.dataTransfer.files;
            handleFileUpload({ target: zipInput });
        }
    });
}

if (zipInput) {
    zipInput.addEventListener('change', handleFileUpload);
}

if (analyzeBtn) {
    analyzeBtn.addEventListener('click', handleQuery);
}

if (queryInput) {
    queryInput.addEventListener('keydown', (e) => {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            handleQuery();
        }
    });
}

exampleBtns.forEach(btn => {
    btn.addEventListener('click', () => {
        queryInput.value = btn.dataset.query;
        // Switch to query tab
        const copilotTabBtn = document.querySelector('[data-target="pane-copilot"]');
        if (copilotTabBtn) {
            switchTab('pane-copilot', copilotTabBtn);
        }
        handleQuery();
    });
});

if (closeNodeInspectorBtn) {
    closeNodeInspectorBtn.addEventListener('click', () => {
        if (nodeDetailPanel) nodeDetailPanel.hidden = true;
        if (cy) {
            cy.elements().removeClass('highlighted');
            // Remove selection class on all nodes
            cy.nodes().removeClass('focus');
        }
    });
}

if (graphLayoutSelect) {
    graphLayoutSelect.addEventListener('change', (e) => {
        const layoutName = e.target.value;
        if (cy && lastGraphData) {
            const options = getLayoutOptions(layoutName);
            const layout = cy.layout(options);
            layout.run();
        }
    });
}

if (copyConsoleBtn) {
    copyConsoleBtn.addEventListener('click', () => {
        const text = graphOutput.innerText;
        navigator.clipboard.writeText(text).then(() => {
            const span = copyConsoleBtn.querySelector('span');
            const originalText = span.textContent;
            span.textContent = 'Copied!';
            setTimeout(() => {
                span.textContent = originalText;
            }, 2000);
        }).catch(err => {
            console.error('Failed to copy logs:', err);
        });
    });
}

// ----------------------------------------------------
// Tab Routing Logic
// ----------------------------------------------------
function initTabs() {
    document.querySelectorAll('.tab-btn').forEach(btn => {
        btn.addEventListener('click', () => {
            const targetId = btn.dataset.target;
            switchTab(targetId, btn);
        });
    });
}

function switchTab(targetId, btnEl) {
    if (!targetId) return;
    
    const nav = btnEl.closest('.pane-tabs');
    nav.querySelectorAll('.tab-btn').forEach(b => {
        b.classList.remove('active');
        b.setAttribute('aria-selected', 'false');
    });
    
    btnEl.classList.add('active');
    btnEl.setAttribute('aria-selected', 'true');
    
    const pane = btnEl.closest('.pane');
    pane.querySelectorAll('.tab-panel').forEach(panel => {
        panel.classList.remove('active');
    });
    
    const targetPanel = document.getElementById(targetId);
    if (targetPanel) {
        targetPanel.classList.add('active');
        
        // Trigger Cytoscape redraw when graph panel is visible
        if (targetId === 'pane-graph' && cy) {
            cy.resize();
            cy.fit(null, 50);
        }
    }
}

// ----------------------------------------------------
// Health Check Check health on loading
// ----------------------------------------------------
async function checkHealth() {
    try {
        const response = await fetch(`${API_BASE}/health`);
        const data = await response.json();
        
        // Log LLM config state to console only (status UI removed for production)
        if (data.status === 'ready' && !data.llm_configured) {
            const llm = data.llm_provider || 'unknown';
            console.warn(`LLM not configured (${llm}). Edit repo-ai/.env and restart app.py`);
        }
        
        if (data.active_repository && data.active_repository !== 'none') {
            showRepoBar(data.active_repository);
            const statsEl = document.getElementById('repo-stats');
            if (statsEl) statsEl.textContent = `${data.file_count} files`;
            
            // Reload graph for active repository
            loadRepositoryGraph(data.active_repository);
        }
    } catch (error) {
        console.error('Health check failed:', error);
    }
}


// ----------------------------------------------------
// File Upload Logic
// ----------------------------------------------------
async function handleFileUpload(event) {
    const file = event.target.files[0];
    if (!file) return;
    
    // Show progress overlay, hide drop zone
    if (uploadProgressOverlay) {
        uploadZone.style.display = 'none';
        uploadProgressOverlay.hidden = false;
    }
    if (uploadProgressText) uploadProgressText.textContent = `Uploading ${file.name}...`;
    uploadStatus.textContent = '';
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
            // Hide overlay, restore zone
            if (uploadProgressOverlay) {
                uploadProgressOverlay.hidden = true;
                uploadZone.style.display = '';
            }
            uploadStatus.textContent = 'Upload successful';
            uploadStatus.className = 'upload-status-modern ok';
            
            repoName.textContent = data.repository;
            fileCount.textContent = data.file_count;
            showRepoBar(data.repository);
            const statsEl = document.getElementById('repo-stats');
            if (statsEl) statsEl.textContent = `${data.file_count} files`;
            
            // Render hierarchical project tree explorer
            renderFileTree(data.files);
            repoInfo.hidden = false;
            
            // Enable Query forms
            queryInput.disabled = false;
            analyzeBtn.disabled = false;
            
            // Transition user to query tab (AI Copilot)
            const copilotTabBtn = document.querySelector('[data-target="pane-copilot"]');
            if (copilotTabBtn) {
                switchTab('pane-copilot', copilotTabBtn);
            }
            
            // Fetch dependency graph
            loadRepositoryGraph(data.repository);
        } else {
            // Hide overlay, restore zone
            if (uploadProgressOverlay) {
                uploadProgressOverlay.hidden = true;
                uploadZone.style.display = '';
            }
            uploadStatus.textContent = `Error: ${data.error}`;
            uploadStatus.className = 'upload-status-modern err';
        }
    } catch (error) {
        if (uploadProgressOverlay) {
            uploadProgressOverlay.hidden = true;
            uploadZone.style.display = '';
        }
        uploadStatus.textContent = `Upload failed: ${error.message}`;
        uploadStatus.className = 'upload-status-modern err';
        console.error('Upload error:', error);
    } finally {
        uploadBtn.disabled = false;
    }
}

// ----------------------------------------------------
// Project Tree Explorer Builder
// ----------------------------------------------------
function renderFileTree(files) {
    const treeData = buildFileTreeData(files);
    fileList.innerHTML = renderTreeNodesHTML(treeData);
    
    // Bind collapsible folders click
    document.querySelectorAll('.folder-node').forEach(node => {
        node.addEventListener('click', (e) => {
            e.stopPropagation();
            const folderContents = node.nextElementSibling;
            const isExpanded = node.classList.toggle('expanded');
            if (folderContents) {
                folderContents.classList.toggle('hidden', !isExpanded);
            }
        });
    });
    
    // Bind file selections
    document.querySelectorAll('.file-item').forEach(node => {
        node.addEventListener('click', (e) => {
            e.stopPropagation();
            document.querySelectorAll('.file-item').forEach(n => n.classList.remove('highlighted-file'));
            node.classList.add('highlighted-file');
        });
        node.addEventListener('dblclick', (e) => {
            e.stopPropagation();
            const filePath = node.dataset.filePath;
            queryInput.value = `What breaks if ${filePath} changes?`;
            
            // Transition user to query tab (AI Copilot)
            const copilotTabBtn = document.querySelector('[data-target="pane-copilot"]');
            if (copilotTabBtn) {
                switchTab('pane-copilot', copilotTabBtn);
            }
            
            queryInput.focus();
        });
    });

    // Setup filter/search actions
    setupFileTreeSearch();
}

function buildFileTreeData(files) {
    const root = { files: [], dirs: {} };
    files.forEach(filePath => {
        const parts = filePath.replace(/\\/g, '/').split('/');
        let current = root;
        for (let i = 0; i < parts.length; i++) {
            const part = parts[i];
            if (i === parts.length - 1) {
                current.files.push({ name: part, path: filePath });
            } else {
                if (!current.dirs[part]) {
                    current.dirs[part] = { files: [], dirs: {} };
                }
                current.dirs[part].currentPath = parts.slice(0, i + 1).join('/');
                current = current.dirs[part];
            }
        }
    });
    return root;
}

function renderTreeNodesHTML(node) {
    let html = '';
    
    const dirKeys = Object.keys(node.dirs).sort();
    const sortedFiles = node.files.sort((a, b) => a.name.localeCompare(b.name));
    
    dirKeys.forEach(dirName => {
        const subNode = node.dirs[dirName];
        const dirPath = subNode.currentPath || dirName;
        html += `
            <div class="tree-folder" data-folder-path="${dirPath}">
                <div class="tree-node folder-node expanded">
                    <svg class="folder-arrow" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                        <polyline points="9 18 15 12 9 6"/>
                    </svg>
                    <svg class="node-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                        <path d="M22 19a2 2 0 0 1-2 2H4a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h5l2 3h9a2 2 0 0 1 2 2z"/>
                    </svg>
                    <span class="node-label">${dirName}</span>
                </div>
                <div class="folder-contents">
                    ${renderTreeNodesHTML(subNode)}
                </div>
            </div>
        `;
    });
    
    sortedFiles.forEach(file => {
        html += `
            <div class="tree-node file-item" data-file-path="${file.path}">
                <svg class="node-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                    <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/>
                    <polyline points="14 2 14 8 20 8"/>
                </svg>
                <span class="node-label">${file.name}</span>
            </div>
        `;
    });
    
    return html;
}

function setupFileTreeSearch() {
    const fileSearchInput = document.getElementById('file-search');
    const clearSearchBtn = document.getElementById('clear-search-btn');
    
    if (!fileSearchInput) return;
    
    const handleSearch = () => {
        const query = fileSearchInput.value.toLowerCase().trim();
        if (query) {
            clearSearchBtn.hidden = false;
        } else {
            clearSearchBtn.hidden = true;
        }
        
        const filesList = document.querySelectorAll('.file-item');
        const folders = document.querySelectorAll('.tree-folder');
        
        if (!query) {
            filesList.forEach(item => item.style.display = '');
            folders.forEach(folder => {
                folder.style.display = '';
                const contents = folder.querySelector('.folder-contents');
                const node = folder.querySelector('.folder-node');
                node.classList.add('expanded');
                if (contents) contents.classList.remove('hidden');
            });
            return;
        }
        
        folders.forEach(folder => folder.style.display = 'none');
        filesList.forEach(fileItem => {
            const path = fileItem.dataset.filePath.toLowerCase();
            if (path.includes(query)) {
                fileItem.style.display = '';
                let parent = fileItem.closest('.tree-folder');
                while (parent) {
                    parent.style.display = '';
                    const node = parent.querySelector('.folder-node');
                    node.classList.add('expanded');
                    const contents = parent.querySelector('.folder-contents');
                    if (contents) contents.classList.remove('hidden');
                    parent = parent.parentElement.closest('.tree-folder');
                }
            } else {
                fileItem.style.display = 'none';
            }
        });
    };
    
    fileSearchInput.addEventListener('input', handleSearch);
    
    if (clearSearchBtn) {
        clearSearchBtn.addEventListener('click', () => {
            fileSearchInput.value = '';
            handleSearch();
            fileSearchInput.focus();
        });
    }
}

// ----------------------------------------------------
// Handle AI Analysis Query
// ----------------------------------------------------
async function handleQuery() {
    const query = queryInput.value.trim();
    if (!query) {
        alert('Please enter a question');
        return;
    }
    
    loading.hidden = false;
    responseOutput.innerHTML = '';
    graphOutput.innerHTML = '';
    analyzeBtn.disabled = true;
    
    // Switch right panel view to Intelligence Tab
    const intelligenceTabBtn = document.querySelector('[data-target="pane-intelligence"]');
    if (intelligenceTabBtn) {
        switchTab('pane-intelligence', intelligenceTabBtn);
    }
    
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
            
            // Highlight affected nodes in dependency graph
            if (data.result.intelligence && data.result.intelligence.affected_files) {
                highlightAffectedNodes(data.result.intelligence.affected_files);
            }
        } else {
            responseOutput.innerHTML = `<div class="msg-error">Error: ${escapeHtml(data.error)}</div>`;
        }
    } catch (error) {
        responseOutput.innerHTML = `<div class="msg-error">Request failed: ${escapeHtml(error.message)}</div>`;
        console.error('Query error:', error);
    } finally {
        loading.hidden = true;
        analyzeBtn.disabled = false;
    }
}

function setStatus(kind, label) {
    if (statusBadge) statusBadge.className = `status-dot ${kind}`;
    if (statusText) statusText.textContent = label;
}

function showRepoBar(name) {
    if (repoBadge) repoBadge.textContent = name;
    if (repoStatusBar) repoStatusBar.hidden = false;
}

// ----------------------------------------------------
// Display Intelligence Insights
// ----------------------------------------------------
function displayResponse(result) {
    const intelligence = result.intelligence || {};
    const impact = result.impact || {};
    const graph = result.graph || {};
    
    let html = '<div class="response-content-modern">';
    
    // Metadata Dashboard
    const riskLevel = intelligence.risk_level || 'unknown';
    const riskClass = riskLevel === 'high' ? 'risk-high' : 
                      riskLevel === 'medium' ? 'risk-medium' : 'risk-low';
                      
    html += `
        <div class="metrics-dashboard-grid">
            <div class="metric-gauge-card">
                <span class="lbl">Risk Level</span>
                <span class="val ${riskClass}">${riskLevel.toUpperCase()}</span>
            </div>
            <div class="metric-gauge-card">
                <span class="lbl">Confidence</span>
                <span class="val">${(intelligence.confidence_score || 0).toFixed(2)}</span>
            </div>
            <div class="metric-gauge-card">
                <span class="lbl">Propagation Depth</span>
                <span class="val">${graph.propagation_depth || 0}</span>
            </div>
            <div class="metric-gauge-card">
                <span class="lbl">Impact Severity</span>
                <span class="val">${(impact.impact_severity || 'unknown').toUpperCase()}</span>
            </div>
        </div>
    `;
    
    // Markdown Summary Analysis
    if (intelligence.summary) {
        html += `
            <div class="analysis-header-card">
                <div class="response-section-title-modern">
                    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" style="width:14px; height:14px;">
                        <circle cx="12" cy="12" r="10"/><path d="M12 16v-4M12 8h.01"/>
                    </svg>
                    <span>Analysis Summary</span>
                </div>
                <div class="response-text-modern response-markdown">${formatMarkdown(intelligence.summary)}</div>
            </div>
        `;
    }
    
    // Affected files list with action hooks to locators
    if (intelligence.affected_files && intelligence.affected_files.length > 0) {
        html += `
            <div>
                <div class="response-section-title-modern">📂 Affected files (${intelligence.affected_files.length})</div>
                <ul class="affected-list-modern">
                    ${intelligence.affected_files.map(f => {
                        const path = f.path || f.id;
                        const relation = f.relation || 'indirect';
                        const badgeClass = relation === 'focus' ? 'focus' :
                                           relation === 'direct' ? 'direct' : 'indirect';
                        return `
                            <li>
                                <div class="affected-file-info">
                                    <svg class="file-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                                        <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/>
                                        <polyline points="14 2 14 8 20 8"/>
                                    </svg>
                                    <span class="affected-file-name" title="${escapeHtml(path)}">${escapeHtml(path)}</span>
                                </div>
                                <div class="affected-file-actions">
                                    <span class="relation-badge ${badgeClass}">${escapeHtml(relation)}</span>
                                    <button type="button" class="btn-file-inspect" data-inspect-path="${escapeHtml(path)}" title="Locate in Dependency Graph">
                                        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                                            <circle cx="12" cy="12" r="10"/><circle cx="12" cy="12" r="3"/>
                                        </svg>
                                    </button>
                                </div>
                            </li>
                        `;
                    }).join('')}
                </ul>
            </div>
        `;
    }
    
    // Dependency Reasoning Chain List
    if (intelligence.dependency_chain && intelligence.dependency_chain.length > 0) {
        html += `
            <div>
                <div class="response-section-title-modern">🔗 Dependency Reasoning Chain</div>
                <ul class="reasoning-list-modern">
                    ${intelligence.dependency_chain.slice(0, 8).map((chain, index) => {
                        let paths = [];
                        try {
                            paths = typeof chain === 'string' ? JSON.parse(chain) : chain;
                            if (!Array.isArray(paths)) {
                                paths = [chain];
                            }
                        } catch (e) {
                            if (typeof chain === 'string' && chain.includes('->')) {
                                paths = chain.split('->').map(p => p.trim());
                            } else {
                                paths = [chain];
                            }
                        }
                        
                        const summaryFlow = paths.map(p => {
                            const name = basename(p);
                            return `<span class="chain-node-summary" title="${escapeHtml(p)}">${escapeHtml(name)}</span>`;
                        }).join('<span class="chain-arrow"> → </span>');
                        
                        const detailSteps = paths.map((p, i) => {
                            const isLast = i === paths.length - 1;
                            return `
                                <div class="chain-detail-item">
                                    <div class="chain-detail-path">${escapeHtml(p)}</div>
                                    ${!isLast ? `
                                        <div class="chain-detail-arrow">
                                            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                                                <line x1="12" y1="5" x2="12" y2="19"/><polyline points="19 12 12 19 5 12"/>
                                            </svg>
                                        </div>
                                    ` : ''}
                                </div>
                            `;
                        }).join('');
                        
                        return `
                            <li>
                                <details class="chain-details-dropdown">
                                    <summary class="chain-summary-header">
                                        <span class="chain-index">Chain ${index + 1}</span>
                                        <div class="chain-summary-flow">${summaryFlow}</div>
                                        <span class="chain-toggle-hint">Inspect flow</span>
                                    </summary>
                                    <div class="chain-expanded-content">
                                        ${detailSteps}
                                    </div>
                                </details>
                            </li>
                        `;
                    }).join('')}
                </ul>
            </div>
        `;
    }
    
    // Actionable Recommendations - Premium Cards
    if (intelligence.recommendations && intelligence.recommendations.length > 0) {
        html += `
            <div>
                <div class="response-section-title-modern">🚀 Recommended Architectural Actions</div>
                <div class="recommendations-box-modern">
                    ${intelligence.recommendations.map(rec => {
                        const match = rec.match(/^\*\*([^*]+)\*\*:\s*(.+)$/);
                        let title = "Architectural Advisory";
                        let desc = rec;
                        
                        if (match) {
                            title = match[1].trim();
                            desc = match[2].trim();
                        } else {
                            desc = rec.replace(/\*\*/g, '');
                            if (desc.toLowerCase().startsWith("review")) {
                                title = "Design Review Requirement";
                            } else if (desc.toLowerCase().startsWith("run tests")) {
                                title = "Test Coverage Advisory";
                            }
                        }
                        
                        let tag = "ADVISORY";
                        let iconHtml = `
                            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" class="rec-icon">
                                <path d="M12 22c5.523 0 10-4.477 10-10S17.523 2 12 2 2 6.477 2 12s4.477 10 10 10z"/>
                                <path d="M12 16v-4"/>
                                <path d="M12 8h.01"/>
                            </svg>
                        `;
                        
                        const combined = (title + " " + desc).toLowerCase();
                        if (combined.includes("interface") || combined.includes("abstract") || combined.includes("decouple") || combined.includes("inversion")) {
                            tag = "DECOUPLING";
                            iconHtml = `
                                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" class="rec-icon">
                                    <rect x="3" y="3" width="18" height="18" rx="2" ry="2"/>
                                    <line x1="9" y1="3" x2="9" y2="21"/>
                                    <line x1="15" y1="3" x2="15" y2="21"/>
                                    <line x1="3" y1="9" x2="21" y2="9"/>
                                    <line x1="3" y1="15" x2="21" y2="15"/>
                                </svg>
                            `;
                        } else if (combined.includes("modular") || combined.includes("utility") || combined.includes("helper")) {
                            tag = "MODULARIZATION";
                            iconHtml = `
                                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" class="rec-icon">
                                    <path d="M21 16V8a2 2 0 0 0-1-1.73l-7-4a2 2 0 0 0-2 0l-7 4A2 2 0 0 0 3 8v8a2 2 0 0 0 1 1.73l7 4a2 2 0 0 0 2 0l7-4A2 2 0 0 0 21 16z"/>
                                    <polyline points="3.27 6.96 12 12.01 20.73 6.96"/>
                                    <line x1="12" y1="22.08" x2="12" y2="12"/>
                                </svg>
                            `;
                        } else if (combined.includes("refactor") || combined.includes("reduce") || combined.includes("depth")) {
                            tag = "REFACTORING";
                            iconHtml = `
                                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" class="rec-icon">
                                    <path d="M14.7 6.3a1 1 0 0 0 0 1.4l1.6 1.6a1 1 0 0 0 1.4 0l3.77-3.77a6 6 0 0 1-7.94 7.94l-6.91 6.91a2.12 2.12 0 0 1-3-3l6.91-6.91a6 6 0 0 1 7.94-7.94l-3.76 3.76z"/>
                                </svg>
                            `;
                        } else if (combined.includes("review") || combined.includes("test") || combined.includes("merg")) {
                            tag = "QUALITY GATE";
                            iconHtml = `
                                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" class="rec-icon">
                                    <path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/>
                                </svg>
                            `;
                        }
                        
                        return `
                            <div class="recommendation-card-premium">
                                <div class="rec-card-header">
                                    <div class="rec-icon-box">${iconHtml}</div>
                                    <div class="rec-title-group">
                                        <h5>${escapeHtml(title)}</h5>
                                        <span class="rec-tag ${tag.toLowerCase().replace(' ', '-')}">${tag}</span>
                                    </div>
                                </div>
                                <div class="rec-card-body">
                                    <p>${escapeHtml(desc)}</p>
                                </div>
                            </div>
                        `;
                    }).join('')}
                </div>
            </div>
        `;
    }
    
    html += '</div>';
    responseOutput.innerHTML = html;
}

// Deep link inspect button handler
document.addEventListener('click', (e) => {
    const inspectBtn = e.target.closest('[data-inspect-path]');
    if (inspectBtn) {
        const path = inspectBtn.dataset.inspectPath;
        const graphTabBtn = document.querySelector('[data-target="pane-graph"]');
        if (graphTabBtn) {
            switchTab('pane-graph', graphTabBtn);
        }
        
        if (cy) {
            const node = cy.getElementById(path);
            if (node.length > 0) {
                cy.elements().removeClass('highlighted');
                // Remove focus on other nodes
                cy.nodes().removeClass('focus');
                
                node.addClass('highlighted focus');
                node.neighborhood().addClass('highlighted');
                
                cy.animate({
                    center: { el: node },
                    zoom: 1.5,
                    duration: 500
                });
                
                showNodeInspector(node.data(), node);
            }
        }
    }
});

// ----------------------------------------------------
// Terminal Console Logging formatter
// ----------------------------------------------------
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
    html += '<span class="title-line">=== Graph Reasoning Shell ===</span>\n\n';
    for (const [key, value] of Object.entries(debug)) {
        html += `<span class="metric-line">${escapeHtml(key)}</span>: <span class="traversal-line">${escapeHtml(String(value))}</span>\n`;
    }
    
    if (graph.traversal_explain && graph.traversal_explain.length > 0) {
        html += '\n<span class="title-line">=== Traversal Explanation Trace ===</span>\n\n';
        graph.traversal_explain.forEach(line => {
            html += `<span class="traversal-line">• ${escapeHtml(line)}</span>\n`;
        });
    }
    
    if (graph.circular_dependencies && graph.circular_dependencies.length > 0) {
        html += '\n<span class="title-line">=== Circular Loops Identified ===</span>\n\n';
        graph.circular_dependencies.forEach((cycle, i) => {
            html += `<span class="cycle-line">Cycle ${i + 1}: ${escapeHtml(cycle.join(' → '))}</span>\n`;
        });
    }
    
    html += '</pre>';
    graphOutput.innerHTML = html;
}

// ----------------------------------------------------
// Render Repository Dependency Graph (Cytoscape)
// ----------------------------------------------------
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
        container.innerHTML = `
            <div class="empty-state-modern">
                <h3>Empty Graph</h3>
                <p>No displayable node elements match current filter conditions.</p>
            </div>
        `;
        return;
    }

    const layoutName = graphLayoutSelect ? graphLayoutSelect.value : 'cose';

    cy = cytoscape({
        container: container,
        elements: elements,
        style: [
            {
                selector: 'node',
                style: {
                    'shape': 'round-rectangle',
                    'background-color': '#1e1b4b',
                    'label': 'data(shortLabel)',
                    'color': '#cbd5e1',
                    'text-valign': 'center',
                    'text-halign': 'center',
                    'text-wrap': 'ellipsis',
                    'text-max-width': '100px',
                    'font-family': 'Outfit, sans-serif',
                    'font-size': '10px',
                    'font-weight': '500',
                    'width': 'label',
                    'height': 'label',
                    'padding': '12px 16px',
                    'min-width': '64px',
                    'min-height': '32px',
                    'border-width': 1.5,
                    'border-color': '#4338ca',
                }
            },
            {
                selector: 'node[type = "entrypoint"]',
                style: {
                    'background-color': '#064e3b',
                    'border-color': '#059669',
                    'color': '#ecfdf5',
                }
            },
            {
                selector: 'node[node_type = "entrypoint"]',
                style: {
                    'background-color': '#064e3b',
                    'border-color': '#059669',
                    'color': '#ecfdf5',
                }
            },
            {
                selector: 'node[node_type = "external"]',
                style: {
                    'background-color': '#78350f',
                    'border-color': '#b45309',
                    'color': '#fef3c7',
                    'shape': 'round-rectangle',
                }
            },
            {
                selector: 'node.highlighted',
                style: {
                    'border-color': '#a855f7',
                    'border-width': 2.5,
                    'color': '#ffffff',
                }
            },
            {
                selector: 'node.focus',
                style: {
                    'background-color': '#4c1d95',
                    'border-color': '#a855f7',
                    'border-width': 2.5,
                    'color': '#ffffff',
                    'shadow-color': '#a855f7',
                    'shadow-blur': 12,
                    'shadow-opacity': 0.5
                }
            },
            {
                selector: 'edge',
                style: {
                    'width': 2,
                    'line-color': '#334155',
                    'target-arrow-color': '#475569',
                    'target-arrow-shape': 'triangle',
                    'curve-style': 'bezier',
                    'arrow-scale': 1.1,
                    'label': 'data(label)',
                    'font-family': 'Outfit, sans-serif',
                    'font-size': '8px',
                    'color': '#64748b',
                    'text-rotation': 'autorotate',
                    'text-margin-y': -8,
                    'opacity': 0.75,
                }
            },
            {
                selector: 'edge.highlighted',
                style: {
                    'line-color': '#c084fc',
                    'target-arrow-color': '#c084fc',
                    'width': 3,
                    'opacity': 1,
                    'z-index': 999,
                }
            },
        ],
        layout: getLayoutOptions(layoutName),
        minZoom: 0.15,
        maxZoom: 3.5,
        wheelSensitivity: 0.15,
    });
    
    // Update count labels
    const nodeCount = cy.nodes().length;
    const edgeCount = cy.edges().length;
    if (graphStats) graphStats.textContent = `${nodeCount} nodes, ${edgeCount} edges`;
    
    // Tap node handler
    cy.on('tap', 'node', function(evt) {
        const node = evt.target;
        const data = node.data();
        
        cy.elements().removeClass('highlighted');
        cy.nodes().removeClass('focus');
        
        node.addClass('highlighted focus');
        node.neighborhood().addClass('highlighted');
        
        // Show details in inspector card drawer
        showNodeInspector(data, node);
    });
    
    // Mouse hover events (micro-animations)
    cy.on('mouseover', 'node', function(evt) {
        const node = evt.target;
        if (!node.hasClass('focus')) {
            node.style({
                'border-width': '2.5px',
                'border-color': '#6366f1',
                'background-color': '#312e81'
            });
        }
        document.body.style.cursor = 'pointer';
    });
    
    cy.on('mouseout', 'node', function(evt) {
        const node = evt.target;
        if (!node.hasClass('highlighted') && !node.hasClass('focus')) {
            node.removeStyle();
        }
        document.body.style.cursor = 'default';
    });
    
    cy.on('mouseover', 'edge', function(evt) {
        const edge = evt.target;
        if (!edge.hasClass('highlighted')) {
            edge.style({
                'width': 2.5,
                'opacity': 1.0,
                'line-color': '#818cf8',
                'target-arrow-color': '#818cf8'
            });
        }
    });
    
    cy.on('mouseout', 'edge', function(evt) {
        const edge = evt.target;
        if (!edge.hasClass('highlighted')) {
            edge.removeStyle();
        }
    });
    
    cy.fit(null, 50);
}

// Get cytoscape layout engine parameters
function getLayoutOptions(name) {
    const base = {
        animate: true,
        animationDuration: 600,
        fit: true,
        padding: 50
    };
    
    if (name === 'cose') {
        return {
            ...base,
            name: 'cose',
            nodeRepulsion: 8000,
            idealEdgeLength: 140,
            edgeElasticity: 100,
            nestingFactor: 1.2,
            gravity: 1,
            numIter: 1500
        };
    } else if (name === 'circle') {
        return { ...base, name: 'circle', radius: 250 };
    } else if (name === 'grid') {
        return { ...base, name: 'grid', columns: undefined };
    } else if (name === 'concentric') {
        return { ...base, name: 'concentric', minNodeSpacing: 60 };
    } else if (name === 'breadthfirst') {
        return { ...base, name: 'breadthfirst', directed: true };
    }
    return { ...base, name: 'cose' };
}

// Render floating card inspector details
function showNodeInspector(data, node) {
    if (!nodeDetailPanel) return;
    
    const labelEl = document.getElementById('node-detail-label');
    const typeEl = document.getElementById('node-detail-type');
    const pathEl = document.getElementById('node-detail-path');
    const connectionsEl = document.getElementById('node-detail-connections');
    const listEl = document.getElementById('node-detail-connected-list');
    
    if (labelEl) labelEl.textContent = data.shortLabel || data.label || data.id;
    if (typeEl) {
        const t = data.node_type || data.type || 'file';
        typeEl.textContent = t.toUpperCase();
        typeEl.className = `badge-type ${t}`;
    }
    
    const path = data.full_path || data.tooltip || data.id;
    if (pathEl) {
        pathEl.textContent = path;
        pathEl.title = path;
    }
    
    if (node) {
        const degree = node.degree();
        if (connectionsEl) connectionsEl.textContent = `${degree} connection(s)`;
        
        if (listEl) {
            const neighbors = node.neighborhood('node');
            if (neighbors.length > 0) {
                let html = '';
                neighbors.forEach(n => {
                    const nd = n.data();
                    html += `<li title="${nd.id}">${nd.shortLabel || nd.label || nd.id}</li>`;
                });
                listEl.innerHTML = html;
            } else {
                listEl.innerHTML = '<li>No connected items</li>';
            }
        }
    }
    
    nodeDetailPanel.hidden = false;
}

// ----------------------------------------------------
// Highlight nodes and center viewport
// ----------------------------------------------------
function highlightAffectedNodes(affectedFiles) {
    if (!cy) return;
    
    cy.elements().removeClass('highlighted focus');
    
    affectedFiles.forEach(file => {
        const nodeId = file.path || file.id;
        const node = cy.getElementById(nodeId);
        
        if (node.length > 0) {
            if (file.relation === 'focus' || file.relation === 'direct') {
                node.addClass('focus');
            } else {
                node.addClass('highlighted');
            }
            node.connectedEdges().addClass('highlighted');
        }
    });
    
    const highlighted = cy.$('.highlighted, .focus');
    if (highlighted.length > 0) {
        cy.animate({
            fit: {
                eles: highlighted,
                padding: 50
            },
            duration: 800
        });
    }
}

// Graph toolbar controllers
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

// ----------------------------------------------------
// Formatting Utilities
// ----------------------------------------------------
function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

function formatMarkdown(text) {
    if (!text) return '';
    let s = escapeHtml(text);
    
    // Parse inline code blocks (backticks) to check for file paths
    s = s.replace(/`([^`]+)`/g, (match, p1) => {
        const hasSeparator = p1.includes('/') || p1.includes('\\');
        const hasExtension = /\.[a-zA-Z0-9]+$/.test(p1);
        if (hasSeparator || hasExtension) {
            const filename = basename(p1);
            return `<code class="path-hover-code" title="${p1}">${filename}</code>`;
        }
        return `<code class="inline-code">${p1}</code>`;
    });
    
    s = s.replace(/^## (.+)$/gm, '<h3 class="md-h3">$1</h3>');
    s = s.replace(/^### (.+)$/gm, '<h4 class="md-h4">$1</h4>');
    s = s.replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>');
    s = s.replace(/^- (.+)$/gm, '<li>$1</li>');
    s = s.replace(/(<li>[\s\S]*?<\/li>)+/g, m => `<ul class="response-list">${m}</ul>`);
    s = s.replace(/\n\n/g, '</p><p>');
    return `<p>${s}</p>`;
}

// Made with Bob
