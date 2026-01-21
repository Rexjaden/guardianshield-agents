// GuardianShield Dashboard - Analytics & Charts

let performanceChart = null;
let evolutionChart = null;
let accuracyChart = null;
let responseChart = null;

function initializeCharts() {
    // Initialize performance chart
    initPerformanceChart();
    
    // Initialize other charts when their sections are shown
    setTimeout(() => {
        if (DashboardState.currentSection === 'analytics') {
            initAnalyticsCharts();
        }
    }, 1000);
}

function initPerformanceChart() {
    const ctx = document.getElementById('performance-chart');
    if (!ctx) return;
    
    const config = {
        type: 'line',
        data: {
            labels: generateTimeLabels(20),
            datasets: [
                {
                    label: 'CPU Usage %',
                    data: generateRandomData(20, 20, 80),
                    borderColor: 'rgb(59, 130, 246)',
                    backgroundColor: 'rgba(59, 130, 246, 0.1)',
                    tension: 0.4,
                    fill: true
                },
                {
                    label: 'Memory Usage %',
                    data: generateRandomData(20, 30, 70),
                    borderColor: 'rgb(16, 185, 129)',
                    backgroundColor: 'rgba(16, 185, 129, 0.1)',
                    tension: 0.4,
                    fill: true
                }
            ]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                title: {
                    display: false
                },
                legend: {
                    position: 'top',
                    labels: {
                        color: '#cbd5e1',
                        usePointStyle: true
                    }
                }
            },
            scales: {
                x: {
                    grid: {
                        color: 'rgba(148, 163, 184, 0.1)'
                    },
                    ticks: {
                        color: '#94a3b8'
                    }
                },
                y: {
                    beginAtZero: true,
                    max: 100,
                    grid: {
                        color: 'rgba(148, 163, 184, 0.1)'
                    },
                    ticks: {
                        color: '#94a3b8'
                    }
                }
            },
            elements: {
                point: {
                    radius: 3,
                    hoverRadius: 6
                }
            }
        }
    };
    
    performanceChart = new Chart(ctx, config);
    window.performanceChart = performanceChart; // Make globally accessible
}

function initAnalyticsCharts() {
    initEvolutionChart();
    initAccuracyChart();
    initResponseChart();
}

function initEvolutionChart() {
    const ctx = document.getElementById('evolution-chart');
    if (!ctx) return;
    
    const agentNames = DashboardState.agents.map(agent => agent.name);
    const evolutionCounts = DashboardState.agents.map(agent => agent.evolutions);
    
    const config = {
        type: 'bar',
        data: {
            labels: agentNames,
            datasets: [{
                label: 'Evolution Count',
                data: evolutionCounts,
                backgroundColor: [
                    'rgba(59, 130, 246, 0.8)',
                    'rgba(16, 185, 129, 0.8)',
                    'rgba(245, 158, 11, 0.8)',
                    'rgba(239, 68, 68, 0.8)',
                    'rgba(139, 92, 246, 0.8)',
                    'rgba(6, 182, 212, 0.8)',
                    'rgba(236, 72, 153, 0.8)',
                    'rgba(34, 197, 94, 0.8)'
                ],
                borderColor: [
                    'rgb(59, 130, 246)',
                    'rgb(16, 185, 129)',
                    'rgb(245, 158, 11)',
                    'rgb(239, 68, 68)',
                    'rgb(139, 92, 246)',
                    'rgb(6, 182, 212)',
                    'rgb(236, 72, 153)',
                    'rgb(34, 197, 94)'
                ],
                borderWidth: 2
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
                x: {
                    grid: {
                        color: 'rgba(148, 163, 184, 0.1)'
                    },
                    ticks: {
                        color: '#94a3b8',
                        maxRotation: 45
                    }
                },
                y: {
                    beginAtZero: true,
                    grid: {
                        color: 'rgba(148, 163, 184, 0.1)'
                    },
                    ticks: {
                        color: '#94a3b8'
                    }
                }
            }
        }
    };
    
    evolutionChart = new Chart(ctx, config);
}

function initAccuracyChart() {
    const ctx = document.getElementById('accuracy-chart');
    if (!ctx) return;
    
    const agentNames = DashboardState.agents.map(agent => agent.name);
    const accuracyValues = DashboardState.agents.map(agent => agent.accuracy);
    
    const config = {
        type: 'radar',
        data: {
            labels: agentNames,
            datasets: [{
                label: 'Accuracy %',
                data: accuracyValues,
                borderColor: 'rgb(59, 130, 246)',
                backgroundColor: 'rgba(59, 130, 246, 0.2)',
                pointBackgroundColor: 'rgb(59, 130, 246)',
                pointBorderColor: '#fff',
                pointHoverBackgroundColor: '#fff',
                pointHoverBorderColor: 'rgb(59, 130, 246)'
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    labels: {
                        color: '#cbd5e1'
                    }
                }
            },
            scales: {
                r: {
                    beginAtZero: true,
                    max: 100,
                    grid: {
                        color: 'rgba(148, 163, 184, 0.1)'
                    },
                    angleLines: {
                        color: 'rgba(148, 163, 184, 0.1)'
                    },
                    pointLabels: {
                        color: '#94a3b8',
                        font: {
                            size: 10
                        }
                    },
                    ticks: {
                        color: '#94a3b8',
                        backdropColor: 'transparent'
                    }
                }
            }
        }
    };
    
    accuracyChart = new Chart(ctx, config);
}

function initResponseChart() {
    const ctx = document.getElementById('response-chart');
    if (!ctx) return;
    
    const config = {
        type: 'doughnut',
        data: {
            labels: ['< 1ms', '1-10ms', '10-100ms', '> 100ms'],
            datasets: [{
                data: [45, 35, 15, 5],
                backgroundColor: [
                    'rgba(16, 185, 129, 0.8)',
                    'rgba(59, 130, 246, 0.8)',
                    'rgba(245, 158, 11, 0.8)',
                    'rgba(239, 68, 68, 0.8)'
                ],
                borderColor: [
                    'rgb(16, 185, 129)',
                    'rgb(59, 130, 246)',
                    'rgb(245, 158, 11)',
                    'rgb(239, 68, 68)'
                ],
                borderWidth: 2
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    position: 'bottom',
                    labels: {
                        color: '#cbd5e1',
                        usePointStyle: true,
                        padding: 20
                    }
                }
            }
        }
    };
    
    responseChart = new Chart(ctx, config);
}

function updatePerformanceChart(timeRange) {
    if (!performanceChart) return;
    
    console.log(`Updating performance chart for: ${timeRange}`);
    
    let dataPoints;
    switch (timeRange) {
        case '1h':
            dataPoints = 12; // 5-minute intervals
            break;
        case '24h':
            dataPoints = 24; // 1-hour intervals
            break;
        case '7d':
            dataPoints = 7; // 1-day intervals
            break;
        default:
            dataPoints = 20;
    }
    
    // Update chart data
    performanceChart.data.labels = generateTimeLabels(dataPoints, timeRange);
    performanceChart.data.datasets[0].data = generateRandomData(dataPoints, 20, 80);
    performanceChart.data.datasets[1].data = generateRandomData(dataPoints, 30, 70);
    
    performanceChart.update();
}

function refreshAnalytics() {
    console.log('Refreshing analytics...');
    
    // Reinitialize charts with fresh data
    if (evolutionChart) {
        updateEvolutionChart();
    }
    
    if (accuracyChart) {
        updateAccuracyChart();
    }
    
    if (responseChart) {
        updateResponseChart();
    }
}

function updateEvolutionChart() {
    if (!evolutionChart) return;
    
    const agentNames = DashboardState.agents.map(agent => agent.name);
    const evolutionCounts = DashboardState.agents.map(agent => agent.evolutions);
    
    evolutionChart.data.labels = agentNames;
    evolutionChart.data.datasets[0].data = evolutionCounts;
    evolutionChart.update();
}

function updateAccuracyChart() {
    if (!accuracyChart) return;
    
    const agentNames = DashboardState.agents.map(agent => agent.name);
    const accuracyValues = DashboardState.agents.map(agent => agent.accuracy);
    
    accuracyChart.data.labels = agentNames;
    accuracyChart.data.datasets[0].data = accuracyValues;
    accuracyChart.update();
}

function updateResponseChart() {
    if (!responseChart) return;
    
    // Simulate new response time data
    const newData = [
        45 + Math.random() * 10 - 5,
        35 + Math.random() * 10 - 5,
        15 + Math.random() * 5 - 2,
        5 + Math.random() * 3 - 1
    ];
    
    responseChart.data.datasets[0].data = newData;
    responseChart.update();
}

// Utility functions for chart data generation
function generateTimeLabels(count, range = '1h') {
    const labels = [];
    const now = new Date();
    
    for (let i = count - 1; i >= 0; i--) {
        let time;
        switch (range) {
            case '1h':
                time = new Date(now.getTime() - i * 5 * 60 * 1000); // 5-minute intervals
                labels.push(time.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }));
                break;
            case '24h':
                time = new Date(now.getTime() - i * 60 * 60 * 1000); // 1-hour intervals
                labels.push(time.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }));
                break;
            case '7d':
                time = new Date(now.getTime() - i * 24 * 60 * 60 * 1000); // 1-day intervals
                labels.push(time.toLocaleDateString([], { weekday: 'short' }));
                break;
            default:
                time = new Date(now.getTime() - i * 3 * 60 * 1000); // 3-minute intervals
                labels.push(time.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }));
        }
    }
    
    return labels;
}

function generateRandomData(count, min, max) {
    const data = [];
    let lastValue = (min + max) / 2;
    
    for (let i = 0; i < count; i++) {
        // Generate somewhat realistic data with trends
        const change = (Math.random() - 0.5) * 10;
        lastValue += change;
        lastValue = Math.max(min, Math.min(max, lastValue));
        data.push(Math.round(lastValue * 10) / 10);
    }
    
    return data;
}

// Export for global use
window.initializeCharts = initializeCharts;
window.updatePerformanceChart = updatePerformanceChart;
window.refreshAnalytics = refreshAnalytics;