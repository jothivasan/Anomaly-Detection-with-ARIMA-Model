// ===================================
// FRAUD INTELLIGENCE DASHBOARD JS
// Enterprise-Grade Interactive Features
// ===================================

// Global State
const dashboardState = {
    currentSection: 'dashboard',
    analysisData: null,
    charts: {},
    alerts: []
};

// ===================================
// INITIALIZATION
// ===================================

document.addEventListener('DOMContentLoaded', function() {
    initializeDashboard();
    setupEventListeners();
    updateClock();
    setInterval(updateClock, 1000);
});

function initializeDashboard() {
    // Initialize charts
    initializeCharts();
    
    // Load sample alerts
    loadSampleAlerts();
    
    // Load demo dashboard data
    loadDemoData();
    
    // Set default section
    showSection('dashboard');
}

// Load demo/placeholder data for dashboard
function loadDemoData() {
    // Set placeholder values for KPIs
    const totalTransactions = document.getElementById('totalTransactions');
    if (totalTransactions) {
        totalTransactions.textContent = '—';
        totalTransactions.style.color = 'var(--gray-light)';
    }
    
    const detectedAnomalies = document.getElementById('detectedAnomalies');
    if (detectedAnomalies) {
        detectedAnomalies.textContent = '—';
        detectedAnomalies.style.color = 'var(--gray-light)';
    }
    
    const avgRiskScore = document.getElementById('avgRiskScore');
    if (avgRiskScore) {
        avgRiskScore.textContent = '—';
        avgRiskScore.style.color = 'var(--gray-light)';
    }
    
    const modelConfidence = document.getElementById('modelConfidence');
    if (modelConfidence) {
        modelConfidence.textContent = '—';
        modelConfidence.style.color = 'var(--gray-light)';
    }
}

function setupEventListeners() {
    // Sidebar navigation
    document.querySelectorAll('.menu-item').forEach(item => {
        item.addEventListener('click', function(e) {
            e.preventDefault();
            const section = this.dataset.section;
            showSection(section);
            
            // Update active state
            document.querySelectorAll('.menu-item').forEach(m => m.classList.remove('active'));
            this.classList.add('active');
        });
    });
    
    // File upload
    const fileInput = document.getElementById('fileInput');
    const uploadZone = document.getElementById('uploadZone');
    
    if (fileInput && uploadZone) {
        fileInput.addEventListener('change', handleFileSelect);
        
        uploadZone.addEventListener('dragover', function(e) {
            e.preventDefault();
            this.style.borderColor = 'var(--primary)';
            this.style.background = 'var(--gray-lighter)';
        });
        
        uploadZone.addEventListener('dragleave', function(e) {
            e.preventDefault();
            this.style.borderColor = 'var(--gray-light)';
            this.style.background = 'transparent';
        });
        
        uploadZone.addEventListener('drop', function(e) {
            e.preventDefault();
            this.style.borderColor = 'var(--gray-light)';
            this.style.background = 'transparent';
            
            const files = e.dataTransfer.files;
            if (files.length > 0) {
                fileInput.files = files;
                handleFileSelect({ target: fileInput });
            }
        });
    }
}

// ===================================
// SECTION NAVIGATION
// ===================================

function showSection(sectionName) {
    // Hide all sections
    document.querySelectorAll('.content-section').forEach(section => {
        section.classList.remove('active');
    });
    
    // Show selected section
    const targetSection = document.getElementById(`${sectionName}-section`);
    if (targetSection) {
        targetSection.classList.add('active');
        dashboardState.currentSection = sectionName;
    }
}

// ===================================
// FILE HANDLING
// ===================================

function handleFileSelect(event) {
    const file = event.target.files[0];
    if (!file) return;
    
    // Validate file type
    const validTypes = ['.xlsx', '.csv'];
    const fileExt = '.' + file.name.split('.').pop().toLowerCase();
    
    if (!validTypes.includes(fileExt)) {
        alert('Please upload a .xlsx or .csv file');
        return;
    }
    
    // Update UI
    const uploadZone = document.getElementById('uploadZone');
    const filePreview = document.getElementById('filePreview');
    const fileName = document.getElementById('fileName');
    const fileSize = document.getElementById('fileSize');
    const analyzeBtn = document.getElementById('analyzeBtn');
    
    if (uploadZone && filePreview) {
        uploadZone.style.display = 'none';
        filePreview.style.display = 'flex';
    }
    
    if (fileName) fileName.textContent = file.name;
    if (fileSize) fileSize.textContent = formatFileSize(file.size);
    if (analyzeBtn) analyzeBtn.disabled = false;
    
    // Update dataset summary
    updateDatasetSummary(file);
}

function removeFile() {
    const fileInput = document.getElementById('fileInput');
    const uploadZone = document.getElementById('uploadZone');
    const filePreview = document.getElementById('filePreview');
    const analyzeBtn = document.getElementById('analyzeBtn');
    
    if (fileInput) fileInput.value = '';
    if (uploadZone) uploadZone.style.display = 'block';
    if (filePreview) filePreview.style.display = 'none';
    if (analyzeBtn) analyzeBtn.disabled = true;
}

function formatFileSize(bytes) {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return Math.round(bytes / Math.pow(k, i) * 100) / 100 + ' ' + sizes[i];
}

function updateDatasetSummary(file) {
    // Show that file is loaded, but wait for analysis for real stats
    const recordCount = document.getElementById('recordCount');
    const featureCount = document.getElementById('featureCount');
    const missingCount = document.getElementById('missingCount');
    const dataQuality = document.getElementById('dataQuality');
    
    if (recordCount) recordCount.textContent = 'Analyzing...';
    if (featureCount) featureCount.textContent = 'Analyzing...';
    if (missingCount) missingCount.textContent = 'Analyzing...';
    if (dataQuality) dataQuality.textContent = 'Analyzing...';
}

function updateIngestionSummary(data) {
    const stats = data.statistics || {};
    const dq = stats.data_quality || {};
    
    const recordCount = document.getElementById('recordCount');
    const featureCount = document.getElementById('featureCount');
    const missingCount = document.getElementById('missingCount');
    const dataQuality = document.getElementById('dataQuality');
    
    const count = stats.total_transactions || (data.risk_results ? data.risk_results.total_transactions : 0);
    
    if (recordCount) recordCount.textContent = (count || 0).toLocaleString();
    if (featureCount) featureCount.textContent = dq.columns || '—';
    if (missingCount) missingCount.textContent = dq.missing_values !== undefined ? dq.missing_values.toLocaleString() : '—';
    
    if (dataQuality) {
        if (dq.missing_values === 0) {
            dataQuality.textContent = 'Excellent';
            dataQuality.className = 'summary-value quality-good';
        } else if (dq.missing_values < 5) {
            dataQuality.textContent = 'Good';
            dataQuality.className = 'summary-value quality-good';
        } else {
            dataQuality.textContent = 'Fair';
            dataQuality.className = 'summary-value quality-warning';
        }
    }
}

// ===================================
// ANALYSIS
// ===================================

async function startAnalysis() {
    const fileInput = document.getElementById('fileInput');
    const file = fileInput.files[0];
    
    if (!file) {
        alert('Please select a file first');
        return;
    }
    
    // Show loading overlay
    showLoading('Analyzing transaction data...');
    
    // Update pipeline status
    updatePipelineStatus('step1', 'complete');
    await sleep(1000);
    updatePipelineStatus('step2', 'processing');
    await sleep(2000);
    updatePipelineStatus('step2', 'complete');
    updatePipelineStatus('step3', 'processing');
    
    // Prepare form data
    const formData = new FormData();
    formData.append('file', file);
    
    const analysisType = document.querySelector('input[name="analysisType"]:checked').value;
    formData.append('analysis_type', analysisType);
    formData.append('sample_size', '1000');
    
    try {
        const response = await fetch('/api/analyze', {
            method: 'POST',
            body: formData
        });
        
        if (!response.ok) {
            throw new Error('Analysis failed');
        }
        
        const data = await response.json();
        
        if (data.success) {
            dashboardState.analysisData = data;
            updatePipelineStatus('step3', 'complete');
            await sleep(500);
            hideLoading();
            
            // Update dashboard with results
            updateDashboard(data);
            
            // Switch to dashboard view
            showSection('dashboard');
            document.querySelectorAll('.menu-item').forEach(m => m.classList.remove('active'));
            document.querySelector('[data-section="dashboard"]').classList.add('active');
        } else {
            throw new Error(data.error || 'Analysis failed');
        }
        
    } catch (error) {
        hideLoading();
        alert('Error: ' + error.message);
        console.error('Analysis error:', error);
    }
}

function updatePipelineStatus(stepId, status) {
    const step = document.getElementById(stepId);
    if (!step) return;
    
    const icon = step.querySelector('.step-icon i');
    
    if (status === 'processing') {
        icon.className = 'fas fa-spinner fa-spin';
        icon.style.color = 'var(--primary)';
    } else if (status === 'complete') {
        icon.className = 'fas fa-check-circle';
        icon.style.color = 'var(--success)';
    }
}

// ===================================
// DASHBOARD UPDATE
// ===================================

function updateDashboard(data) {
    // Update KPIs
    updateKPIs(data);
    
    // Update charts
    updateCharts(data);
    
    // Update alerts
    updateAlerts(data);
    
    // Update fraud detection table
    updateFraudTable(data);
    
    // Update risk analysis
    updateRiskAnalysis(data);
    
    // Update model comparison
    updateModelComparison(data);
    
    // Update explainability
    updateExplainability(data);

    // Update ingestion summary
    updateIngestionSummary(data);
}

function updateKPIs(data) {
    const stats = data.statistics || {};
    const riskResults = data.risk_results || {};
    const modelPerf = data.model_performance || {};
    
    // Total Transactions
    const totalTransactions = document.getElementById('totalTransactions');
    if (totalTransactions) {
        // Fix: stats.total_records was incorrect, should be total_transactions
        const count = stats.total_transactions || riskResults.total_transactions || 0;
        totalTransactions.textContent = count.toLocaleString();
        totalTransactions.style.color = ''; // Reset color
    }
    
    // Detected Anomalies
    const detectedAnomalies = document.getElementById('detectedAnomalies');
    if (detectedAnomalies) {
        detectedAnomalies.textContent = (riskResults.high_risk_count || 0).toLocaleString();
        detectedAnomalies.style.color = ''; // Reset color
    }
    
    // Average Risk Score
    const avgRisk = riskResults.average_risk_score || 0;
    const avgRiskScore = document.getElementById('avgRiskScore');
    if (avgRiskScore) {
        avgRiskScore.textContent = avgRisk.toFixed(1);
        avgRiskScore.style.color = ''; // Reset color
    }
    
    // Update risk bar
    const riskBar = document.getElementById('riskBar');
    if (riskBar) {
        riskBar.style.width = avgRisk + '%';
    }
    
    // Model Confidence
    const avgConfidence = (modelPerf.ensemble_avg || 0);
    const modelConfidence = document.getElementById('modelConfidence');
    if (modelConfidence) {
        modelConfidence.textContent = avgConfidence.toFixed(1) + '%';
        modelConfidence.style.color = ''; // Reset color
    }
}

function updateCharts(data) {
    // Update timeline chart
    if (dashboardState.charts.timeline) {
        updateTimelineChart(data);
    }
    
    // Update risk pie chart
    if (dashboardState.charts.riskPie) {
        updateRiskPieChart(data);
    }
    
    // Update risk distribution chart
    if (dashboardState.charts.riskDist) {
        updateRiskDistChart(data);
    }
    
    // Update model comparison chart
    if (dashboardState.charts.modelComparison) {
        updateModelComparisonChart(data);
    }
}

function updateAlerts(data) {
    const riskResults = data.risk_results || {};
    const samples = riskResults.samples || [];
    
    // Filter high-risk transactions
    const highRisk = samples.filter(s => s.risk_score >= 60);
    
    // Update alert count (with null check)
    const alertCount = document.getElementById('alertCount');
    if (alertCount) {
        alertCount.textContent = highRisk.length;
    }
    
    // Update recent alerts panel
    const recentAlerts = document.getElementById('recentAlerts');
    if (recentAlerts) {
        recentAlerts.innerHTML = '';
        
        highRisk.slice(0, 5).forEach((alert, index) => {
            const severity = getSeverity(alert.risk_score);
            const alertHTML = `
                <div class="alert-item ${severity}">
                    <div class="alert-content">
                        <h4>Transaction #${index + 1} - Risk Score: ${alert.risk_score.toFixed(1)}</h4>
                        <p>${alert.category} - Detected at ${new Date().toLocaleTimeString()}</p>
                    </div>
                    <span class="alert-badge badge-${severity}">${severity.toUpperCase()}</span>
                </div>
            `;
            recentAlerts.innerHTML += alertHTML;
        });
    }
    
    // Update full alerts grid
    updateAlertsGrid(highRisk);
}

function updateFraudTable(data) {
    const riskResults = data.risk_results || {};
    const samples = riskResults.samples || [];
    
    const tbody = document.getElementById('fraudTableBody');
    if (!tbody) return;
    
    tbody.innerHTML = '';
    
    samples.filter(s => s.risk_score >= 60).forEach((txn, index) => {
        const severity = getSeverity(txn.risk_score);
        const row = `
            <tr>
                <td>TXN-${String(index + 1).padStart(6, '0')}</td>
                <td>$${(Math.random() * 100000).toFixed(2)}</td>
                <td>TRANSFER</td>
                <td><strong>${txn.risk_score.toFixed(1)}</strong></td>
                <td><span class="severity-badge severity-${severity}">${severity.toUpperCase()}</span></td>
                <td>${new Date().toLocaleString()}</td>
            </tr>
        `;
        tbody.innerHTML += row;
    });
}

function updateRiskAnalysis(data) {
    const riskResults = data.risk_results || {};
    
    const total = riskResults.total_transactions || 1;
    const critical = riskResults.samples?.filter(s => s.risk_score > 85).length || 0;
    const high = riskResults.samples?.filter(s => s.risk_score > 60 && s.risk_score <= 85).length || 0;
    const medium = riskResults.samples?.filter(s => s.risk_score > 30 && s.risk_score <= 60).length || 0;
    const low = riskResults.samples?.filter(s => s.risk_score <= 30).length || 0;
    
    // Update counts (with null checks)
    const criticalCount = document.getElementById('criticalCount');
    const highCount = document.getElementById('highCount');
    const mediumCount = document.getElementById('mediumCount');
    const lowCount = document.getElementById('lowCount');
    
    if (criticalCount) criticalCount.textContent = critical;
    if (highCount) highCount.textContent = high;
    if (mediumCount) mediumCount.textContent = medium;
    if (lowCount) lowCount.textContent = low;
    
    // Update bars (with null checks)
    const criticalBar = document.getElementById('criticalBar');
    const highBar = document.getElementById('highBar');
    const mediumBar = document.getElementById('mediumBar');
    const lowBar = document.getElementById('lowBar');
    
    if (criticalBar) criticalBar.style.width = (critical / total * 100) + '%';
    if (highBar) highBar.style.width = (high / total * 100) + '%';
    if (mediumBar) mediumBar.style.width = (medium / total * 100) + '%';
    if (lowBar) lowBar.style.width = (low / total * 100) + '%';
}

function updateModelComparison(data) {
    const modelPerf = data.model_performance || {};
    
    // Update model scores in the comparison table
    const sarimaxScore = document.getElementById('sarimaxScore');
    const iforestScore = document.getElementById('iforestScore');
    const ocsvmScore = document.getElementById('ocsvmScore');
    const lstmScore = document.getElementById('lstmScore');
    const ensembleScoreTable = document.getElementById('ensembleScoreTable');
    
    if (sarimaxScore) sarimaxScore.textContent = (modelPerf.sarimax_avg || 0).toFixed(1) + '%';
    if (iforestScore) iforestScore.textContent = (modelPerf.isolation_forest_avg || 0).toFixed(1) + '%';
    if (ocsvmScore) ocsvmScore.textContent = (modelPerf.ocsvm_avg || 0).toFixed(1) + '%';
    if (lstmScore) lstmScore.textContent = (modelPerf.lstm_avg || 0).toFixed(1) + '%';
    if (ensembleScoreTable) ensembleScoreTable.textContent = (modelPerf.ensemble_avg || 0).toFixed(1) + '%';
    
    // Update the main overview score
    const ensembleScore = document.getElementById('ensembleScore');
    if (ensembleScore) ensembleScore.textContent = (modelPerf.ensemble_avg || 0).toFixed(0);
}

function updateExplainability(data) {
    const explanations = data.explanations || [];
    const transactionSelect = document.getElementById('transactionSelect');
    
    if (transactionSelect) {
        transactionSelect.innerHTML = '<option value="">Choose a high-risk transaction...</option>';
        
        explanations.forEach((exp, index) => {
            const option = document.createElement('option');
            option.value = index;
            option.textContent = `Transaction #${exp.transaction_index + 1} - Risk: ${exp.explanation.risk_score}`;
            transactionSelect.appendChild(option);
        });
    }
}

// ===================================
// CHARTS INITIALIZATION
// ===================================

function initializeCharts() {
    // Timeline Chart
    const timelineCtx = document.getElementById('timelineChart');
    if (timelineCtx) {
        dashboardState.charts.timeline = new Chart(timelineCtx, {
            type: 'line',
            data: {
                labels: [],
                datasets: [{
                    label: 'Anomaly Score',
                    data: [],
                    borderColor: 'rgb(239, 68, 68)',
                    backgroundColor: 'rgba(239, 68, 68, 0.1)',
                    tension: 0.4,
                    fill: true
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        display: false
                    }
                },
                scales: {
                    y: {
                        beginAtZero: true,
                        max: 100
                    }
                }
            }
        });
    }
    
    // Risk Pie Chart
    const riskPieCtx = document.getElementById('riskPieChart');
    if (riskPieCtx) {
        dashboardState.charts.riskPie = new Chart(riskPieCtx, {
            type: 'doughnut',
            data: {
                labels: ['Low Risk', 'Medium Risk', 'High Risk', 'Critical Risk'],
                datasets: [{
                    data: [0, 0, 0, 0],
                    backgroundColor: [
                        'rgb(16, 185, 129)',
                        'rgb(6, 182, 212)',
                        'rgb(245, 158, 11)',
                        'rgb(239, 68, 68)'
                    ]
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        position: 'bottom'
                    }
                }
            }
        });
    }
    
    // Risk Distribution Chart
    const riskDistCtx = document.getElementById('riskDistChart');
    if (riskDistCtx) {
        dashboardState.charts.riskDist = new Chart(riskDistCtx, {
            type: 'bar',
            data: {
                labels: [],
                datasets: [{
                    label: 'Frequency',
                    data: [],
                    backgroundColor: 'rgba(37, 99, 235, 0.8)'
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        display: false
                    }
                }
            }
        });
    }
    
    // Model Comparison Chart
    const modelCompCtx = document.getElementById('modelComparisonChart');
    if (modelCompCtx) {
        dashboardState.charts.modelComparison = new Chart(modelCompCtx, {
            type: 'bar',
            data: {
                labels: ['SARIMAX', 'Isolation Forest', 'One-Class SVM', 'LSTM Autoencoder', 'Ensemble'],
                datasets: [{
                    label: 'Average Score (%)',
                    data: [0, 0, 0, 0, 0],
                    backgroundColor: [
                        'rgba(255, 107, 107, 0.8)',
                        'rgba(78, 205, 196, 0.8)',
                        'rgba(69, 183, 209, 0.8)',
                        'rgba(255, 160, 122, 0.8)',
                        'rgba(152, 216, 200, 0.8)'
                    ]
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                scales: {
                    y: {
                        beginAtZero: true,
                        max: 100
                    }
                }
            }
        });
    }
}

function updateTimelineChart(data) {
    const chart = dashboardState.charts.timeline;
    if (!chart) return;
    
    const samples = data.risk_results?.samples || [];
    chart.data.labels = samples.map((_, i) => `T${i + 1}`);
    chart.data.datasets[0].data = samples.map(s => s.risk_score);
    chart.update();
}

function updateRiskPieChart(data) {
    const chart = dashboardState.charts.riskPie;
    if (!chart) return;
    
    const samples = data.risk_results?.samples || [];
    const low = samples.filter(s => s.risk_score <= 30).length;
    const medium = samples.filter(s => s.risk_score > 30 && s.risk_score <= 60).length;
    const high = samples.filter(s => s.risk_score > 60 && s.risk_score <= 85).length;
    const critical = samples.filter(s => s.risk_score > 85).length;
    
    chart.data.datasets[0].data = [low, medium, high, critical];
    chart.update();
}

function updateRiskDistChart(data) {
    const chart = dashboardState.charts.riskDist;
    if (!chart) return;
    
    const samples = data.risk_results?.samples || [];
    const bins = [0, 10, 20, 30, 40, 50, 60, 70, 80, 90, 100];
    const counts = new Array(bins.length - 1).fill(0);
    
    samples.forEach(s => {
        const score = s.risk_score;
        for (let i = 0; i < bins.length - 1; i++) {
            if (score >= bins[i] && score < bins[i + 1]) {
                counts[i]++;
                break;
            }
        }
    });
    
    chart.data.labels = bins.slice(0, -1).map((b, i) => `${b}-${bins[i + 1]}`);
    chart.data.datasets[0].data = counts;
    chart.update();
}

function updateModelComparisonChart(data) {
    const chart = dashboardState.charts.modelComparison;
    if (!chart) return;
    
    const modelPerf = data.model_performance || {};
    chart.data.datasets[0].data = [
        modelPerf.sarimax_avg || 0,
        modelPerf.isolation_forest_avg || 0,
        modelPerf.ocsvm_avg || 0,
        modelPerf.lstm_avg || 0,
        modelPerf.ensemble_avg || 0
    ];
    chart.update();
}

// ===================================
// UTILITY FUNCTIONS
// ===================================

function getSeverity(riskScore) {
    if (riskScore > 85) return 'critical';
    if (riskScore > 60) return 'high';
    if (riskScore > 30) return 'medium';
    return 'low';
}

function updateClock() {
    const clockElement = document.getElementById('currentTime');
    if (clockElement) {
        const now = new Date();
        clockElement.textContent = now.toLocaleTimeString();
    }
}

function showLoading(message = 'Processing...') {
    const overlay = document.getElementById('loadingOverlay');
    const messageEl = document.getElementById('loadingMessage');
    
    if (overlay) {
        overlay.classList.add('active');
    }
    if (messageEl) {
        messageEl.textContent = message;
    }
}

function hideLoading() {
    const overlay = document.getElementById('loadingOverlay');
    if (overlay) {
        overlay.classList.remove('active');
    }
}

function sleep(ms) {
    return new Promise(resolve => setTimeout(resolve, ms));
}

function loadSampleAlerts() {
    // Load some sample alerts for demo
    dashboardState.alerts = [
        { id: 1, severity: 'critical', message: 'Large transfer detected', time: new Date() },
        { id: 2, severity: 'high', message: 'Unusual transaction pattern', time: new Date() },
        { id: 3, severity: 'medium', message: 'Velocity spike detected', time: new Date() }
    ];
}

function updateAlertsGrid(alerts) {
    const grid = document.getElementById('alertsGrid');
    if (!grid) return;
    
    grid.innerHTML = '';
    
    alerts.forEach((alert, index) => {
        const severity = getSeverity(alert.risk_score);
        const alertCard = `
            <div class="alert-item ${severity}">
                <div class="alert-content">
                    <h4>High-Risk Transaction Detected</h4>
                    <p>Transaction #${index + 1} - Risk Score: ${alert.risk_score.toFixed(1)}</p>
                    <p>${alert.category}</p>
                    <p><small>${new Date().toLocaleString()}</small></p>
                </div>
                <span class="alert-badge badge-${severity}">${severity.toUpperCase()}</span>
            </div>
        `;
        grid.innerHTML += alertCard;
    });
}

function refreshDashboard() {
    if (dashboardState.analysisData) {
        updateDashboard(dashboardState.analysisData);
    }
}

function exportReport() {
    alert('Export functionality will be implemented');
}

function clearAlerts() {
    const grid = document.getElementById('alertsGrid');
    if (grid) {
        grid.innerHTML = '<p style="text-align: center; color: var(--gray);">No alerts</p>';
    }
}

function viewDetails(index) {
    alert(`Viewing details for transaction ${index + 1}`);
}

function loadExplanation() {
    const select = document.getElementById('transactionSelect');
    const index = select.value;
    
    if (!index) return;
    
    const explanations = dashboardState.analysisData?.explanations || [];
    const exp = explanations[index];
    
    if (!exp) return;
    
    // Update factors list
    const factorsList = document.getElementById('factorsList');
    if (factorsList && exp.explanation.top_contributors) {
        factorsList.innerHTML = '';
        exp.explanation.top_contributors.forEach(factor => {
            const factorHTML = `
                <div class="factor-item">
                    <h4>${factor.feature}</h4>
                    <p>Value: ${factor.value}</p>
                    <p>Contribution: +${factor.contribution} points</p>
                </div>
            `;
            factorsList.innerHTML += factorHTML;
        });
    }
    
    // Update counterfactuals
    const counterfactualList = document.getElementById('counterfactualList');
    if (counterfactualList && exp.explanation.counterfactuals) {
        counterfactualList.innerHTML = '';
        exp.explanation.counterfactuals.forEach(cf => {
            const cfHTML = `
                <div class="counterfactual-item">
                    <h4>${cf.feature.toUpperCase()}</h4>
                    <p>Current: ${cf.current}</p>
                    <p>Suggested: ${cf.suggested}</p>
                    <p><em>${cf.explanation}</em></p>
                </div>
            `;
            counterfactualList.innerHTML += cfHTML;
        });
    }
}
