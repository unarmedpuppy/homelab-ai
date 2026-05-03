// Homelab AI Dashboard - Cron Job Tracker

let cronJobsData = null;

// Load cron jobs data
async function loadCronJobs() {
    try {
        const response = await fetch('data/cron-jobs.json');
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        cronJobsData = await response.json();
        renderJobs();
        updateStats();
        updateLastUpdate();
    } catch (error) {
        console.error('Error loading cron jobs:', error);
        document.getElementById('jobs-container').innerHTML = `
            <div class="loading">
                Error loading cron jobs data. Please try again later.
            </div>
        `;
    }
}

// Render cron jobs
function renderJobs() {
    const container = document.getElementById('jobs-container');
    container.innerHTML = '';
    
    if (!cronJobsData || !cronJobsData.jobs || cronJobsData.jobs.length === 0) {
        container.innerHTML = '<div class="loading">No cron jobs found</div>';
        return;
    }
    
    // Sort by name
    const sortedJobs = [...cronJobsData.jobs].sort((a, b) => a.name.localeCompare(b.name));
    
    sortedJobs.forEach(job => {
        const jobCard = createJobCard(job);
        container.appendChild(jobCard);
    });
}

// Create job card element
function createJobCard(job) {
    const card = document.createElement('div');
    card.className = `job-card ${job.enabled ? 'enabled' : 'paused'}`;
    
    const statusIcon = job.enabled ? '✅' : '⏸️';
    const nextRun = job.next_run_at ? formatDate(job.next_run_at) : 'N/A';
    const lastRun = job.last_run_at ? formatDate(job.last_run_at) : 'Never';
    
    card.innerHTML = `
        <div class="job-header">
            <h3>${statusIcon} ${escapeHtml(job.name)}</h3>
            <span class="job-id">${escapeHtml(job.job_id.substring(0, 8))}...</span>
        </div>
        <div class="job-details">
            <p class="description">${escapeHtml(job.description || 'No description')}</p>
            <p class="schedule">🕐 ${escapeHtml(job.schedule_human || job.schedule || 'N/A')}</p>
            <p class="next-run">📅 Next: ${nextRun}</p>
            <p class="last-run">⏱️ Last: ${lastRun}</p>
            <a href="${escapeHtml(job.documentation || '#')}" class="doc-link" target="_blank">
                📖 View Documentation
            </a>
        </div>
    `;
    
    return card;
}

// Update stats display
function updateStats() {
    if (!cronJobsData || !cronJobsData.jobs) return;
    
    const jobs = cronJobsData.jobs;
    const total = jobs.length;
    const active = jobs.filter(j => j.enabled).length;
    const paused = total - active;
    
    document.getElementById('total-jobs').textContent = total;
    document.getElementById('active-jobs').textContent = active;
    document.getElementById('paused-jobs').textContent = paused;
}

// Format date for display
function formatDate(dateString) {
    if (!dateString) return 'N/A';
    
    try {
        const date = new Date(dateString);
        return date.toLocaleString('en-US', {
            weekday: 'short',
            year: 'numeric',
            month: 'short',
            day: 'numeric',
            hour: '2-digit',
            minute: '2-digit',
            timeZoneName: 'short'
        });
    } catch (error) {
        return dateString;
    }
}

// Update last update timestamp
function updateLastUpdate() {
    const now = new Date();
    document.getElementById('last-update').textContent = now.toLocaleString('en-US', {
        weekday: 'long',
        year: 'numeric',
        month: 'long',
        day: 'numeric',
        hour: '2-digit',
        minute: '2-digit'
    });
}

// Escape HTML to prevent XSS
function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

// Refresh data periodically
function startAutoRefresh(intervalMs = 60000) {
    setInterval(() => {
        console.log('Refreshing cron jobs data...');
        loadCronJobs();
    }, intervalMs);
}

// Initialize
document.addEventListener('DOMContentLoaded', () => {
    loadCronJobs();
    startAutoRefresh();
});

// Make functions available globally for debugging
window.dashboard = {
    loadCronJobs,
    renderJobs,
    updateStats,
    formatDate,
    updateLastUpdate,
    getCronJobsData: () => cronJobsData
};
