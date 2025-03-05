document.addEventListener('DOMContentLoaded', () => {
    const UI = {
        resumeInput: document.getElementById('resume'),
        fileName: document.getElementById('file-name'),
        uploadContainer: document.getElementById('upload-container'),
        analysisContainer: document.getElementById('analysis-container'),
        analyzeBtn: document.getElementById('analyze-btn'),
        jobDescription: document.getElementById('job_description'),
        errorContainer: document.getElementById('error-container'),
        resumeForm: document.getElementById('resume-form')
    };

    // File input handling
    UI.resumeInput.addEventListener('change', handleFileSelection);
    UI.analyzeBtn?.addEventListener('click', handleAnalysis);
    UI.resumeForm?.addEventListener('submit', handleFormSubmit);

    // Initialize state based on session
    initializeState();

    function handleFileSelection(e) {
        const fileName = e.target.files[0] ? e.target.files[0].name : 'No file selected';
        UI.fileName.textContent = fileName;
    }

    function handleFormSubmit(e) {
        const button = e.target.querySelector('button[type="submit"]');
        setLoadingState(button, true);
    }

    async function handleAnalysis(e) {
        e.preventDefault();
        const jobDescription = UI.jobDescription.value.trim();
        
        clearErrors();
        
        if (!validateJobDescription(jobDescription)) {
            return;
        }

        setLoadingState(UI.analyzeBtn, true);

        try {
            const response = await fetch('/analyze', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/x-www-form-urlencoded',
                    'Accept': 'application/json'
                },
                body: new URLSearchParams({ job_description: jobDescription })
            });

            const data = await response.json();
            
            if (response.ok) {
                window.location.href = `/processing?task_id=${data.task_id}`;
            } else {
                showError(data.error || 'An error occurred while starting the analysis.');
            }
        } catch (error) {
            showError('Failed to communicate with the server. Please try again.');
            console.error('Error:', error);
        } finally {
            setLoadingState(UI.analyzeBtn, false);
        }
    }

    function validateJobDescription(text) {
        if (!text) {
            showError('Please enter a job description.');
            return false;
        }
        if (text.length < 50) {
            showError('Job description is too short. Please provide more details.');
            return false;
        }
        return true;
    }

    function showError(message) {
        UI.errorContainer.innerHTML = `
            <h3>Error</h3>
            <p>${message}</p>
        `;
        UI.errorContainer.classList.remove('hidden');
        UI.errorContainer.scrollIntoView({ behavior: 'smooth' });
    }

    function clearErrors() {
        UI.errorContainer.innerHTML = '';
        UI.errorContainer.classList.add('hidden');
    }

    function setLoadingState(button, isLoading) {
        if (!button) return;
        
        const btnText = button.querySelector('.btn-text');
        const spinner = button.querySelector('.loading-spinner');
        
        button.disabled = isLoading;
        btnText.textContent = isLoading ? 
            button.dataset.loadingText : 
            button.dataset.loadingText.replace('...', '');
        spinner.classList.toggle('hidden', !isLoading);
    }

    function initializeState() {
        // Check if we're in analysis state (this assumes the server sets a flag in the page)
        const isAnalysisState = document.body.dataset.state === 'analysis';
        if (isAnalysisState) {
            UI.uploadContainer.classList.add('hidden');
            UI.analysisContainer.classList.remove('hidden');
        }
    }
});