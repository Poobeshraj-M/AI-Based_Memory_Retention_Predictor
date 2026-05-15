document.addEventListener('DOMContentLoaded', () => {
    // 1. Get the JSON data safely from the script tag
    const dataElement = document.getElementById('chartData');
    if (!dataElement) return; // No data available

    const rawData = JSON.parse(dataElement.textContent);
    
    // Modern dark theme config for charts
    Chart.defaults.color = '#94a3b8';
    Chart.defaults.font.family = "'Inter', sans-serif";
    const gridColor = 'rgba(255, 255, 255, 0.05)';

    // --- Chart 1: Retention Score vs Hours Studied (Scatter) ---
    const ctxRetention = document.getElementById('retentionChart');
    if (ctxRetention) {
        const scatterData = rawData.hours_studied.map((hours, index) => ({
            x: hours,
            y: rawData.retention_score[index]
        }));

        new Chart(ctxRetention, {
            type: 'scatter',
            data: {
                datasets: [{
                    label: 'Retention Score',
                    data: scatterData,
                    backgroundColor: 'rgba(59, 130, 246, 0.6)',
                    borderColor: '#3b82f6',
                    borderWidth: 1,
                    pointRadius: 4,
                    pointHoverRadius: 6
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                scales: {
                    x: {
                        title: { display: true, text: 'Hours Studied' },
                        grid: { color: gridColor }
                    },
                    y: {
                        title: { display: true, text: 'Retention Score (%)' },
                        grid: { color: gridColor },
                        min: 0, max: 100
                    }
                },
                plugins: {
                    legend: { display: false }
                }
            }
        });
    }

    // --- Chart 2: Sleep Impact on Retention (Bar) ---
    const ctxSleep = document.getElementById('sleepChart');
    if (ctxSleep) {
        // Group data by sleep ranges to make a cleaner bar chart
        const sleepBins = { '<6 hrs': [], '6-8 hrs': [], '>8 hrs': [] };
        
        rawData.sleep_hours.forEach((sleep, i) => {
            const score = rawData.retention_score[i];
            if (sleep < 6) sleepBins['<6 hrs'].push(score);
            else if (sleep <= 8) sleepBins['6-8 hrs'].push(score);
            else sleepBins['>8 hrs'].push(score);
        });

        const averages = Object.keys(sleepBins).map(key => {
            const arr = sleepBins[key];
            if (arr.length === 0) return 0;
            return arr.reduce((a, b) => a + b, 0) / arr.length;
        });

        new Chart(ctxSleep, {
            type: 'bar',
            data: {
                labels: Object.keys(sleepBins),
                datasets: [{
                    label: 'Average Retention (%)',
                    data: averages,
                    backgroundColor: [
                        'rgba(239, 68, 68, 0.6)', // <6
                        'rgba(245, 158, 11, 0.6)', // 6-8
                        'rgba(16, 185, 129, 0.6)'  // >8
                    ],
                    borderColor: [
                        '#ef4444',
                        '#f59e0b',
                        '#10b981'
                    ],
                    borderWidth: 1,
                    borderRadius: 4
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                scales: {
                    y: {
                        beginAtZero: true,
                        max: 100,
                        grid: { color: gridColor }
                    },
                    x: {
                        grid: { display: false }
                    }
                },
                plugins: {
                    legend: { display: false }
                }
            }
        });
    }

    // --- Chart 3: Score Distribution (Line / Area) ---
    const ctxDist = document.getElementById('distributionChart');
    if (ctxDist) {
        // Create bins for distribution (0-20, 20-40, etc.)
        const bins = [0, 0, 0, 0, 0];
        const binLabels = ['0-20', '21-40', '41-60', '61-80', '81-100'];
        
        rawData.retention_score.forEach(score => {
            if (score <= 20) bins[0]++;
            else if (score <= 40) bins[1]++;
            else if (score <= 60) bins[2]++;
            else if (score <= 80) bins[3]++;
            else bins[4]++;
        });

        new Chart(ctxDist, {
            type: 'line',
            data: {
                labels: binLabels,
                datasets: [{
                    label: 'Number of Students',
                    data: bins,
                    backgroundColor: 'rgba(139, 92, 246, 0.2)',
                    borderColor: '#8b5cf6',
                    borderWidth: 2,
                    fill: true,
                    tension: 0.4
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                scales: {
                    y: {
                        beginAtZero: true,
                        title: { display: true, text: 'Student Count' },
                        grid: { color: gridColor }
                    },
                    x: {
                        title: { display: true, text: 'Retention Score Range' },
                        grid: { color: gridColor }
                    }
                }
            }
        });
    }
});
