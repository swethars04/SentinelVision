// AI Surveillance System - Dashboard JavaScript
// Handles real-time updates, alert management, and interactive features

class SurveillanceDashboard {
    constructor() {
        this.alertCount = 0;
        this.autoRefreshInterval = 30000; // 30 seconds
        this.processingUpdateInterval = 5000; // 5 seconds
        this.charts = {};
        
        this.init();
    }
    
    init() {
        this.setupEventListeners();
        this.initializeCharts();
        this.startAutoRefresh();
        this.updateAlertCounter();
        
        // Initialize tooltips if Bootstrap is available
        if (typeof bootstrap !== 'undefined') {
            this.initializeTooltips();
        }
        
        console.log('Surveillance Dashboard initialized');
    }
    
    setupEventListeners() {
        // Alert counter click handler
        const alertCounter = document.getElementById('alert-counter');
        if (alertCounter) {
            alertCounter.addEventListener('click', () => {
                this.showRecentAlerts();
            });
        }
        
        // Real-time search functionality
        const searchInputs = document.querySelectorAll('[data-search-target]');
        searchInputs.forEach(input => {
            input.addEventListener('input', (e) => {
                this.performSearch(e.target.value, e.target.dataset.searchTarget);
            });
        });
        
        // Status filter handlers
        const statusFilters = document.querySelectorAll('[data-filter-type]');
        statusFilters.forEach(filter => {
            filter.addEventListener('change', (e) => {
                this.applyFilters();
            });
        });
        
        // Video player event handlers
        const videoPlayers = document.querySelectorAll('video');
        videoPlayers.forEach(player => {
            player.addEventListener('loadstart', () => {
                this.showVideoLoading(player);
            });
            player.addEventListener('loadeddata', () => {
                this.hideVideoLoading(player);
            });
            player.addEventListener('error', (e) => {
                this.handleVideoError(player, e);
            });
        });
    }
    
    // Real-time alert management
    updateAlertCounter() {
        fetch('/api/alerts')
            .then(response => response.json())
            .then(alerts => {
                const unacknowledgedCount = alerts.filter(alert => !alert.is_acknowledged).length;
                this.alertCount = unacknowledgedCount;
                
                const alertCountElement = document.getElementById('alert-count');
                if (alertCountElement) {
                    alertCountElement.textContent = unacknowledgedCount;
                    alertCountElement.className = `badge ${unacknowledgedCount > 0 ? 'bg-danger' : 'bg-secondary'}`;
                }
                
                // Update navbar alert indicator
                const alertCounter = document.getElementById('alert-counter');
                if (alertCounter && unacknowledgedCount > 0) {
                    alertCounter.classList.add('text-warning');
                    alertCounter.title = `${unacknowledgedCount} unacknowledged alerts`;
                } else if (alertCounter) {
                    alertCounter.classList.remove('text-warning');
                    alertCounter.title = 'No pending alerts';
                }
            })
            .catch(error => {
                console.error('Error updating alert counter:', error);
            });
    }
    
    showRecentAlerts() {
        fetch('/api/alerts')
            .then(response => response.json())
            .then(alerts => {
                this.displayAlertsModal(alerts.slice(0, 10));
            })
            .catch(error => {
                console.error('Error fetching alerts:', error);
                this.showNotification('Error loading alerts', 'error');
            });
    }
    
    displayAlertsModal(alerts) {
        const modalHtml = `
            <div class="modal fade" id="alertsModal" tabindex="-1">
                <div class="modal-dialog modal-lg">
                    <div class="modal-content">
                        <div class="modal-header">
                            <h5 class="modal-title">
                                <i class="fas fa-bell me-2"></i>Recent Alerts
                            </h5>
                            <button type="button" class="btn-close" data-bs-dismiss="modal"></button>
                        </div>
                        <div class="modal-body">
                            ${alerts.length > 0 ? this.renderAlertsList(alerts) : this.renderEmptyAlerts()}
                        </div>
                        <div class="modal-footer">
                            <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">Close</button>
                            ${alerts.some(a => !a.is_acknowledged) ? 
                                '<button type="button" class="btn btn-primary" onclick="dashboard.acknowledgeAllAlerts()">Acknowledge All</button>' : 
                                ''}
                        </div>
                    </div>
                </div>
            </div>
        `;
        
        // Remove existing modal
        const existingModal = document.getElementById('alertsModal');
        if (existingModal) {
            existingModal.remove();
        }
        
        // Add new modal
        document.body.insertAdjacentHTML('beforeend', modalHtml);
        
        // Show modal
        const modal = new bootstrap.Modal(document.getElementById('alertsModal'));
        modal.show();
    }
    
    renderAlertsList(alerts) {
        return `
            <div class="list-group">
                ${alerts.map(alert => `
                    <div class="list-group-item ${!alert.is_acknowledged ? 'border-warning' : ''}">
                        <div class="d-flex w-100 justify-content-between">
                            <h6 class="mb-1">
                                <span class="badge bg-${this.getAlertLevelColor(alert.level)} me-2">
                                    ${alert.level?.toUpperCase() || 'INFO'}
                                </span>
                                ${alert.message}
                            </h6>
                            <small>${this.formatDateTime(alert.created_time)}</small>
                        </div>
                        <p class="mb-1 text-muted">${alert.anomaly_type || 'System Alert'}</p>
                        <div class="d-flex justify-content-between align-items-center">
                            <small>Video: ${alert.video_filename || 'Unknown'}</small>
                            ${!alert.is_acknowledged ? 
                                `<button class="btn btn-sm btn-outline-primary" onclick="dashboard.acknowledgeAlert(${alert.id})">
                                    <i class="fas fa-check me-1"></i>Acknowledge
                                </button>` : 
                                '<small class="text-success"><i class="fas fa-check-circle me-1"></i>Acknowledged</small>'
                            }
                        </div>
                    </div>
                `).join('')}
            </div>
        `;
    }
    
    renderEmptyAlerts() {
        return `
            <div class="text-center py-4">
                <i class="fas fa-bell-slash fa-3x text-muted mb-3"></i>
                <h5>No Alerts</h5>
                <p class="text-muted">All clear! No recent alerts to display.</p>
            </div>
        `;
    }
    
    acknowledgeAlert(alertId) {
        fetch(`/api/alerts/${alertId}/acknowledge`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                acknowledged_by: 'Dashboard User'
            })
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                this.showNotification('Alert acknowledged', 'success');
                this.updateAlertCounter();
                
                // Update the alert in the modal
                const alertElement = document.querySelector(`[onclick="dashboard.acknowledgeAlert(${alertId})"]`);
                if (alertElement) {
                    alertElement.parentElement.innerHTML = '<small class="text-success"><i class="fas fa-check-circle me-1"></i>Acknowledged</small>';
                }
            }
        })
        .catch(error => {
            console.error('Error acknowledging alert:', error);
            this.showNotification('Error acknowledging alert', 'error');
        });
    }
    
    acknowledgeAllAlerts() {
        const unacknowledgedAlerts = document.querySelectorAll('[onclick*="acknowledgeAlert"]');
        
        Promise.all(
            Array.from(unacknowledgedAlerts).map(button => {
                const alertId = button.getAttribute('onclick').match(/\d+/)[0];
                return fetch(`/api/alerts/${alertId}/acknowledge`, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ acknowledged_by: 'Dashboard User' })
                });
            })
        )
        .then(responses => {
            this.showNotification('All alerts acknowledged', 'success');
            this.updateAlertCounter();
            
            // Close modal and refresh if needed
            const modal = bootstrap.Modal.getInstance(document.getElementById('alertsModal'));
            if (modal) modal.hide();
        })
        .catch(error => {
            console.error('Error acknowledging all alerts:', error);
            this.showNotification('Error acknowledging alerts', 'error');
        });
    }
    
    // Chart management
    initializeCharts() {
        // Initialize analytics chart on dashboard
        const analyticsChart = document.getElementById('analyticsChart');
        if (analyticsChart) {
            this.initAnalyticsChart(analyticsChart);
        }
        
        // Initialize anomaly distribution charts
        const anomalyChart = document.getElementById('anomalyChart');
        if (anomalyChart) {
            this.initAnomalyChart(anomalyChart);
        }
        
        // Initialize real-time monitoring chart
        const monitoringChart = document.getElementById('monitoringChart');
        if (monitoringChart) {
            this.initMonitoringChart(monitoringChart);
        }
    }
    
    initAnalyticsChart(canvas) {
        fetch('/api/statistics')
            .then(response => response.json())
            .then(stats => {
                const ctx = canvas.getContext('2d');
                
                // Use real daily data if available, fallback to generated data
                const labels = stats.daily_labels || ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'];
                const anomalyData = stats.daily_anomalies || this.generateWeeklyData(stats.total_anomalies || 0);
                const videoData = stats.daily_videos || this.generateWeeklyData(stats.total_videos || 0);
                
                this.charts.analytics = new Chart(ctx, {
                    type: 'line',
                    data: {
                        labels: labels,
                        datasets: [{
                            label: 'Anomalies Detected',
                            data: anomalyData,
                            borderColor: 'rgb(255, 99, 132)',
                            backgroundColor: 'rgba(255, 99, 132, 0.1)',
                            tension: 0.1,
                            fill: true
                        }, {
                            label: 'Videos Processed',
                            data: videoData,
                            borderColor: 'rgb(54, 162, 235)',
                            backgroundColor: 'rgba(54, 162, 235, 0.1)',
                            tension: 0.1,
                            fill: true
                        }]
                    },
                    options: {
                        responsive: true,
                        maintainAspectRatio: false,
                        plugins: {
                            legend: {
                                position: 'top',
                                labels: {
                                    color: 'rgb(255, 255, 255)'
                                }
                            },
                            tooltip: {
                                mode: 'index',
                                intersect: false,
                                callbacks: {
                                    title: function(tooltipItems) {
                                        return 'Day: ' + tooltipItems[0].label;
                                    },
                                    label: function(context) {
                                        return context.dataset.label + ': ' + context.parsed.y;
                                    }
                                }
                            }
                        },
                        scales: {
                            x: {
                                title: {
                                    display: true,
                                    text: 'Days (Last 7 Days)',
                                    color: 'rgb(255, 255, 255)'
                                },
                                ticks: { color: 'rgb(255, 255, 255)' },
                                grid: { color: 'rgba(255, 255, 255, 0.1)' }
                            },
                            y: {
                                title: {
                                    display: true,
                                    text: 'Count',
                                    color: 'rgb(255, 255, 255)'
                                },
                                beginAtZero: true,
                                ticks: { 
                                    color: 'rgb(255, 255, 255)',
                                    stepSize: 1  // Show whole numbers only
                                },
                                grid: { color: 'rgba(255, 255, 255, 0.1)' }
                            }
                        },
                        interaction: {
                            mode: 'nearest',
                            axis: 'x',
                            intersect: false
                        }
                    }
                });
            })
            .catch(error => {
                console.error('Error loading analytics data:', error);
                // Show fallback chart with empty data
                this.showFallbackChart(canvas);
            });
    }
    
    showFallbackChart(canvas) {
        const ctx = canvas.getContext('2d');
        this.charts.analytics = new Chart(ctx, {
            type: 'line',
            data: {
                labels: ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'],
                datasets: [{
                    label: 'No data available',
                    data: [0, 0, 0, 0, 0, 0, 0],
                    borderColor: 'rgb(108, 117, 125)',
                    backgroundColor: 'rgba(108, 117, 125, 0.1)',
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        labels: { color: 'rgb(255, 255, 255)' }
                    }
                },
                scales: {
                    x: { ticks: { color: 'rgb(255, 255, 255)' } },
                    y: { ticks: { color: 'rgb(255, 255, 255)' } }
                }
            }
        });
    }
    
    initAnomalyChart(canvas) {
        fetch('/api/statistics')
            .then(response => response.json())
            .then(stats => {
                const ctx = canvas.getContext('2d');
                const anomalyTypes = stats.anomaly_types || {};
                
                this.charts.anomaly = new Chart(ctx, {
                    type: 'doughnut',
                    data: {
                        labels: Object.keys(anomalyTypes).map(type => 
                            type.replace('_', ' ').replace(/\b\w/g, l => l.toUpperCase())
                        ),
                        datasets: [{
                            data: Object.values(anomalyTypes),
                            backgroundColor: [
                                'rgba(255, 99, 132, 0.8)',
                                'rgba(54, 162, 235, 0.8)',
                                'rgba(255, 205, 86, 0.8)',
                                'rgba(75, 192, 192, 0.8)',
                                'rgba(153, 102, 255, 0.8)'
                            ],
                            borderColor: [
                                'rgba(255, 99, 132, 1)',
                                'rgba(54, 162, 235, 1)',
                                'rgba(255, 205, 86, 1)',
                                'rgba(75, 192, 192, 1)',
                                'rgba(153, 102, 255, 1)'
                            ],
                            borderWidth: 2
                        }]
                    },
                    options: {
                        responsive: true,
                        maintainAspectRatio: false,
                        plugins: {
                            legend: {
                                position: 'right',
                                labels: {
                                    color: 'rgb(255, 255, 255)',
                                    padding: 20
                                }
                            }
                        }
                    }
                });
            })
            .catch(error => {
                console.error('Error loading anomaly distribution data:', error);
            });
    }
    
    // Processing status updates
    startAutoRefresh() {
        // Update alerts regularly
        setInterval(() => {
            this.updateAlertCounter();
        }, this.autoRefreshInterval);
        
        // Update processing status more frequently
        setInterval(() => {
            this.updateProcessingStatus();
        }, this.processingUpdateInterval);
    }
    
    updateProcessingStatus() {
        const processingRows = document.querySelectorAll('[data-analysis-id][data-status="processing"]');
        
        processingRows.forEach(row => {
            const analysisId = row.getAttribute('data-analysis-id');
            if (analysisId) {
                this.refreshAnalysisStatus(analysisId);
            }
        });
    }
    
    refreshAnalysisStatus(analysisId) {
        fetch(`/api/analysis/${analysisId}/status`)
            .then(response => response.json())
            .then(data => {
                this.updateAnalysisRow(analysisId, data);
            })
            .catch(error => {
                console.error(`Error refreshing status for analysis ${analysisId}:`, error);
            });
    }
    
    updateAnalysisRow(analysisId, statusData) {
        const row = document.querySelector(`[data-analysis-id="${analysisId}"]`);
        if (!row) return;
        
        // Update status badge
        const statusBadge = row.querySelector('.badge');
        if (statusBadge) {
            const statusColor = this.getStatusColor(statusData.status);
            statusBadge.className = `badge bg-${statusColor}`;
            statusBadge.textContent = statusData.status.charAt(0).toUpperCase() + statusData.status.slice(1);
        }
        
        // Update progress bar
        const progressBar = row.querySelector('.progress-bar');
        if (progressBar && statusData.status === 'processing') {
            progressBar.style.width = `${statusData.progress}%`;
            progressBar.setAttribute('aria-valuenow', statusData.progress);
        }
        
        // Update progress text
        const progressText = row.querySelector('.progress-text');
        if (progressText && statusData.status === 'processing') {
            progressText.textContent = `${statusData.processed_frames}/${statusData.total_frames}`;
        }
        
        // Update row data attribute
        row.setAttribute('data-status', statusData.status);
        
        // Reload page if processing completed
        if (statusData.status === 'completed') {
            setTimeout(() => {
                location.reload();
            }, 2000);
        }
    }
    
    // Utility functions
    generateWeeklyData(total) {
        // Simple algorithm to distribute data across the week
        const base = Math.max(1, Math.floor(total / 7));
        return Array.from({length: 7}, () => 
            Math.max(0, base + Math.floor(Math.random() * base))
        );
    }
    
    getStatusColor(status) {
        const colors = {
            'completed': 'success',
            'processing': 'warning',
            'failed': 'danger',
            'pending': 'secondary'
        };
        return colors[status] || 'secondary';
    }
    
    getAlertLevelColor(level) {
        const colors = {
            'danger': 'danger',
            'critical': 'danger',
            'warning': 'warning',
            'info': 'info',
            'low': 'secondary'
        };
        return colors[level] || 'info';
    }
    
    formatDateTime(dateString) {
        const date = new Date(dateString);
        return date.toLocaleString();
    }
    
    performSearch(query, targetSelector) {
        const target = document.querySelector(targetSelector);
        if (!target) return;
        
        const searchableItems = target.querySelectorAll('[data-searchable]');
        const lowerQuery = query.toLowerCase();
        
        searchableItems.forEach(item => {
            const text = item.textContent.toLowerCase();
            const shouldShow = text.includes(lowerQuery);
            item.style.display = shouldShow ? '' : 'none';
        });
    }
    
    applyFilters() {
        // Generic filter application
        const filterElements = document.querySelectorAll('[data-filter-type]');
        const activeFilters = {};
        
        filterElements.forEach(element => {
            const filterType = element.getAttribute('data-filter-type');
            const filterValue = element.value;
            if (filterValue) {
                activeFilters[filterType] = filterValue;
            }
        });
        
        // Apply filters to filterable items
        const filterableItems = document.querySelectorAll('[data-filterable]');
        filterableItems.forEach(item => {
            let shouldShow = true;
            
            Object.entries(activeFilters).forEach(([type, value]) => {
                const itemValue = item.getAttribute(`data-${type}`);
                if (itemValue && itemValue !== value) {
                    shouldShow = false;
                }
            });
            
            item.style.display = shouldShow ? '' : 'none';
        });
    }
    
    showVideoLoading(player) {
        const loadingOverlay = document.createElement('div');
        loadingOverlay.className = 'video-loading-overlay position-absolute d-flex align-items-center justify-content-center';
        loadingOverlay.style.cssText = `
            top: 0; left: 0; right: 0; bottom: 0; 
            background: rgba(0, 0, 0, 0.7); 
            z-index: 10;
        `;
        loadingOverlay.innerHTML = `
            <div class="text-center text-white">
                <div class="spinner-border mb-2" role="status"></div>
                <div>Loading video...</div>
            </div>
        `;
        
        const container = player.parentElement;
        if (container.style.position !== 'relative') {
            container.style.position = 'relative';
        }
        container.appendChild(loadingOverlay);
    }
    
    hideVideoLoading(player) {
        const container = player.parentElement;
        const overlay = container.querySelector('.video-loading-overlay');
        if (overlay) {
            overlay.remove();
        }
    }
    
    handleVideoError(player, error) {
        console.error('Video loading error:', error);
        
        const errorOverlay = document.createElement('div');
        errorOverlay.className = 'video-error-overlay position-absolute d-flex align-items-center justify-content-center';
        errorOverlay.style.cssText = `
            top: 0; left: 0; right: 0; bottom: 0; 
            background: rgba(220, 53, 69, 0.1); 
            border: 2px solid var(--bs-danger);
            z-index: 10;
        `;
        errorOverlay.innerHTML = `
            <div class="text-center text-danger">
                <i class="fas fa-exclamation-triangle fa-2x mb-2"></i>
                <div>Failed to load video</div>
                <small>Please check the file format and try again</small>
            </div>
        `;
        
        const container = player.parentElement;
        if (container.style.position !== 'relative') {
            container.style.position = 'relative';
        }
        container.appendChild(errorOverlay);
    }
    
    showNotification(message, type = 'info') {
        const toast = document.createElement('div');
        toast.className = `alert alert-${type === 'error' ? 'danger' : type} alert-dismissible fade show position-fixed`;
        toast.style.cssText = `
            top: 20px; right: 20px; z-index: 9999; 
            min-width: 300px; max-width: 500px;
        `;
        toast.innerHTML = `
            <div class="d-flex align-items-center">
                <i class="fas fa-${this.getNotificationIcon(type)} me-2"></i>
                <div>${message}</div>
                <button type="button" class="btn-close ms-auto" data-bs-dismiss="alert"></button>
            </div>
        `;
        
        document.body.appendChild(toast);
        
        // Auto-remove after 5 seconds
        setTimeout(() => {
            if (toast.parentElement) {
                toast.remove();
            }
        }, 5000);
    }
    
    getNotificationIcon(type) {
        const icons = {
            'success': 'check-circle',
            'error': 'exclamation-triangle',
            'warning': 'exclamation-circle',
            'info': 'info-circle'
        };
        return icons[type] || 'info-circle';
    }
    
    initializeTooltips() {
        // Initialize Bootstrap tooltips
        const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
        tooltipTriggerList.map(function (tooltipTriggerEl) {
            return new bootstrap.Tooltip(tooltipTriggerEl);
        });
    }
}

// Initialize dashboard when DOM is loaded
let dashboard;
document.addEventListener('DOMContentLoaded', function() {
    dashboard = new SurveillanceDashboard();
});

// Export for global access
window.dashboard = dashboard;
