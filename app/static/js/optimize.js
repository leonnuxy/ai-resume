document.addEventListener('DOMContentLoaded', function() {
    // Get form elements
    const form = document.getElementById('optimizeForm');
    const toggleUrl = document.getElementById('toggleUrl');
    const urlSection = document.querySelector('.url-section');
    const jobDescription = document.getElementById('job_description');
    const jobUrl = document.getElementById('job_url');
    const fetchBtn = document.getElementById('fetchJob');
    const progressContainer = document.getElementById('progressContainer');

    // Only initialize if elements exist (we're on the form page)
    if (form && toggleUrl && urlSection) {
        // Toggle between URL and text input
        toggleUrl.addEventListener('click', function() {
            urlSection.classList.toggle('hidden');
            if (!urlSection.classList.contains('hidden')) {
                jobUrl.focus();
            }
        });

        // Handle job description fetch
        if (fetchBtn) {
            fetchBtn.addEventListener('click', async function() {
                const url = jobUrl.value.trim();
                if (!url) {
                    showNotification('Please enter a valid URL', 'error');
                    return;
                }

                try {
                    fetchBtn.disabled = true;
                    fetchBtn.innerHTML = '<span class="btn-text">Fetching...</span>';

                    const response = await fetch('/analysis/fetch_job_description', {
                        method: 'POST',
                        headers: {
                            'Content-Type': 'application/json',
                            'Accept': 'application/json'
                        },
                        body: JSON.stringify({ url })
                    });

                    const data = await response.json();
                    
                    if (data.error) {
                        throw new Error(data.error);
                    }

                    jobDescription.value = data.description;
                    showNotification('Job description fetched successfully!', 'success');
                } catch (error) {
                    showNotification(error.message || 'Failed to fetch job description', 'error');
                } finally {
                    fetchBtn.disabled = false;
                    fetchBtn.innerHTML = '<span class="btn-text">Fetch</span><span class="btn-icon">↓</span>';
                }
            });
        }

        // Handle form submission
        form.addEventListener('submit', async function(e) {
            e.preventDefault();
            
            if (!jobDescription.value.trim()) {
                showNotification('Please provide a job description', 'error');
                return;
            }

            try {
                // Submit the form data
                const formData = new FormData(form);
                const response = await fetch('/analysis/optimize', {
                    method: 'POST',
                    headers: {
                        'Accept': 'application/json'
                    },
                    body: formData
                });

                const data = await response.json();
                
                if (data.error) {
                    throw new Error(data.error);
                }

                if (data.task_id) {
                    // Redirect to processing page with task ID
                    window.location.href = `/processing?task_id=${data.task_id}`;
                }
            } catch (error) {
                showNotification(error.message || 'Failed to process the request', 'error');
            }
        });
    }

    // Notifications
    function showNotification(message, type = 'info') {
        const notification = document.createElement('div');
        notification.className = `notification ${type}`;
        notification.textContent = message;

        document.body.appendChild(notification);
        
        // Trigger animation
        setTimeout(() => notification.classList.add('show'), 10);

        // Remove after delay
        setTimeout(() => {
            notification.classList.remove('show');
            setTimeout(() => notification.remove(), 300);
        }, 3000);
    }
});