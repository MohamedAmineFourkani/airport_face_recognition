/**
 * Airport Face Recognition System - Main JavaScript
 */

// Auto-refresh stats on dashboard
document.addEventListener('DOMContentLoaded', function() {
    // Initialize tooltips
    const tooltipTriggerList = document.querySelectorAll('[data-bs-toggle="tooltip"]');
    tooltipTriggerList.forEach(el => new bootstrap.Tooltip(el));

    // Auto-refresh dashboard stats every 10 seconds
    if (document.querySelector('.dashboard-stats')) {
        setInterval(refreshStats, 10000);
    }
});

function refreshStats() {
    fetch('/api/stats')
        .then(r => r.json())
        .then(data => {
            // Update stat cards if they exist
            const totalEl = document.getElementById('stat-total-travelers');
            const todayEl = document.getElementById('stat-today-scans');
            const unauthEl = document.getElementById('stat-unauthorized');

            if (totalEl) totalEl.textContent = data.total_travelers;
            if (todayEl) todayEl.textContent = data.today_recognitions;
            if (unauthEl) unauthEl.textContent = data.unauthorized_today;
        })
        .catch(err => console.error('Stats refresh failed:', err));
}

// Toast notification helper
function showToast(message, type = 'info') {
    const toastContainer = document.getElementById('toast-container') || createToastContainer();

    const toast = document.createElement('div');
    toast.className = `alert alert-${type} alert-dismissible fade show`;
    toast.innerHTML = `
        ${message}
        <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
    `;

    toastContainer.appendChild(toast);

    setTimeout(() => {
        toast.remove();
    }, 5000);
}

function createToastContainer() {
    const container = document.createElement('div');
    container.id = 'toast-container';
    container.style.cssText = 'position: fixed; top: 20px; right: 20px; z-index: 9999; width: 300px;';
    document.body.appendChild(container);
    return container;
}

// Format confidence percentage with color
function formatConfidence(confidence) {
    let color = 'text-danger';
    if (confidence >= 90) color = 'text-success';
    else if (confidence >= 70) color = 'text-warning';

    return `<span class="${color} fw-bold">${confidence.toFixed(1)}%</span>`;
}

// Copy to clipboard helper
function copyToClipboard(text) {
    navigator.clipboard.writeText(text).then(() => {
        showToast('Copied to clipboard!', 'success');
    }).catch(() => {
        showToast('Failed to copy', 'error');
    });
}
