// Initialize analysis storage
window.fullAnalysis = {
    missing_skills: [],
    improvement_suggestions: [],
    emphasis_suggestions: [],
    general_suggestions: []
};

function updateProgressCounters() {
    document.getElementById('missing-skills-counter').textContent =
        `Missing Skills: ${window.fullAnalysis.missing_skills.length}`;
    document.getElementById('improvements-counter').textContent =
        `Improvements: ${window.fullAnalysis.improvement_suggestions.length}`;
    document.getElementById('emphasis-counter').textContent =
        `Emphasis Points: ${window.fullAnalysis.emphasis_suggestions.length}`;
    document.getElementById('general-counter').textContent =
        `General Suggestions: ${window.fullAnalysis.general_suggestions.length}`;
}

function formatResumeText(text) {
    // Split the text into sections
    const sections = text.split('\n\n');
    const formattedSections = sections.map(section => {
        if (section.startsWith('SUMMARY') || section.startsWith('SKILLS') || 
            section.startsWith('RELEVANT EXPERIENCE') || section.startsWith('ADDITIONAL HIGHLIGHTS')) {
            // Add section headers in bold
            return section.replace(/^([A-Z\s]+)(\n|$)/, '<strong>$1</strong>$2');
        }
        return section;
    });

    // Process green highlights
    return formattedSections.join('\n\n').replace(
        /<span style="color:green">(.*?)<\/span>/g,
        '<span class="highlight">$1</span>'
    );
}

function updateAnalysisSections(analysis) {
    // Update missing skills section
    const missingSkillsList = document.getElementById('missing-skills-list');
    missingSkillsList.innerHTML = analysis.missing_skills.map(skill => 
        `<li><strong>${skill.skill}</strong>: ${skill.suggestion}</li>`
    ).join('');

    // Update improvements section
    const improvementsList = document.getElementById('improvements-list');
    improvementsList.innerHTML = analysis.improvement_suggestions.map(imp => 
        `<li><strong>Current:</strong> ${imp.current}<br>
         <strong>Suggested:</strong> ${imp.suggested}<br>
         <em>Reason:</em> ${imp.reason}</li>`
    ).join('');

    // Update emphasis suggestions
    const emphasisList = document.getElementById('emphasis-list');
    emphasisList.innerHTML = analysis.emphasis_suggestions.map(emp => 
        `<li><strong>${emp.experience}</strong><br>
         <em>Why relevant:</em> ${emp.why_relevant}<br>
         <em>How to emphasize:</em> ${emp.how_to_emphasize}</li>`
    ).join('');

    // Update general suggestions
    const generalList = document.getElementById('general-list');
    generalList.innerHTML = analysis.general_suggestions.map(sugg => 
        `<li>${sugg}</li>`
    ).join('');
}

function handleErrorType(error) {
    const errorMessages = {
        'validation_error': 'Please check your input and try again.',
        'timeout': 'The analysis took too long. Try with shorter content.',
        'result_format_error': 'The analysis result was invalid. Please try again.',
        'unknown_error': 'An unexpected error occurred. Please try again.'
    };
    
    return errorMessages[error.error_type] || 'An error occurred during analysis.';
}

function handleStreamChunk(chunkData) {
    const outputDiv = document.getElementById('output');
    
    try {
        if (chunkData.error) {
            const errorMessage = typeof chunkData.meta === 'object' ? 
                handleErrorType(chunkData.meta) : 
                chunkData.error;
            showError(errorMessage);
            return false;
        }
        
        if (chunkData.status === "error") {
            showError(chunkData.message || 'An error occurred during analysis');
            const details = chunkData.details || 'Please check your input and try again';
            outputDiv.innerHTML += `<div class="error-details">${details}</div>`;
            return false;
        }
        
        if (chunkData.status === "completed" && chunkData.result) {
            // Validate result structure
            if (!validateAnalysisResult(chunkData.result)) {
                showError('Invalid analysis result received');
                return false;
            }
            
            window.fullAnalysis = chunkData.result;
            showFinalResults();
            return false;
        }
        
        if (chunkData.status === "in_progress") {
            updateProgress(chunkData);
            return true;
        }
        
        return true;
    } catch (e) {
        console.error('Error processing chunk:', e);
        showError(`Error processing response: ${e.message}`);
        return false;
    }
}

function updateProgress(data) {
    const outputDiv = document.getElementById('output');
    const progress = Math.round((data.current / data.total) * 100);
    
    outputDiv.innerHTML = `
        <div class="progress-message">
            <p>${data.status_message || 'Processing...'}</p>
            <div class="progress-bar">
                <div class="progress" style="width: ${progress}%"></div>
            </div>
            <div class="progress-status">
                ${progress}% complete
                ${data.execution_time ? 
                    `<br>Time elapsed: ${Math.round(data.execution_time)}s` : 
                    ''}
            </div>
        </div>
    `;
    
    // Update counters if available
    if (data.current_counts) {
        updateProgressCounters(data.current_counts);
    }
}

function validateAnalysisResult(result) {
    if (!result || typeof result !== 'object') return false;
    
    const requiredSections = ['missing_skills', 'improvement_suggestions', 'emphasis_suggestions', 'general_suggestions'];
    if (!requiredSections.every(section => Array.isArray(result[section]))) return false;
    
    try {
        // Validate section contents
        const validations = {
            missing_skills: item => item.skill && item.suggestion,
            improvement_suggestions: item => item.current && item.suggested && item.reason,
            emphasis_suggestions: item => item.experience && item.why_relevant && item.how_to_emphasize,
            general_suggestions: item => typeof item === 'string'
        };
        
        return requiredSections.every(section => 
            result[section].every(item => validations[section](item))
        );
    } catch (e) {
        console.error('Validation error:', e);
        return false;
    }
}

function showFinalResults() {
    const resultDiv = document.getElementById('result');
    
    if (!window.fullAnalysis || typeof window.fullAnalysis !== 'object') {
        showError('Invalid analysis format received');
        return;
    }
    
    // Update progress counters first
    updateProgressCounters();
    
    // Then show the full results
    resultDiv.innerHTML = `
        <h2>Analysis Complete</h2>
        ${formatAnalysisSections(window.fullAnalysis)}
        <div class="action-buttons">
            <button onclick="window.location.href='/'" class="back-btn">Start New Analysis</button>
        </div>
    `;
}

function formatAnalysisSections(analysis) {
    if (!analysis || !analysis.missing_skills) {
        console.error('Invalid analysis format:', analysis);
        return `<div class="error-message">Invalid analysis format received. Please try again.</div>`;
    }

    return `
        <div class="suggestion-section">
            <h3>Missing Skills (${analysis.missing_skills.length})</h3>
            <ul>
                ${analysis.missing_skills.map(skill => `
                    <li>
                        <strong>${skill.skill}</strong>: ${skill.suggestion}
                    </li>
                `).join('')}
            </ul>
        </div>
        
        <div class="suggestion-section">
            <h3>Improvement Suggestions (${analysis.improvement_suggestions.length})</h3>
            <ul>
                ${analysis.improvement_suggestions.map(imp => `
                    <li>
                        <strong>Current:</strong> ${imp.current}<br>
                        <strong>Suggested:</strong> ${imp.suggested}<br>
                        <em>Reason:</em> ${imp.reason}
                    </li>
                `).join('')}
            </ul>
        </div>
        
        <div class="suggestion-section">
            <h3>Emphasis Recommendations (${analysis.emphasis_suggestions.length})</h3>
            <ul>
                ${analysis.emphasis_suggestions.map(emphasis => `
                    <li>
                        <strong>${emphasis.experience}</strong><br>
                        <em>Why relevant:</em> ${emphasis.why_relevant}<br>
                        <em>How to emphasize:</em> ${emphasis.how_to_emphasize}
                    </li>
                `).join('')}
            </ul>
        </div>
        
        <div class="suggestion-section">
            <h3>General Suggestions (${analysis.general_suggestions.length})</h3>
            <ul>
                ${analysis.general_suggestions.map(suggestion => `
                    <li>${suggestion}</li>
                `).join('')}
            </ul>
        </div>
    `;
}

function showError(title, message, detail = '') {
    const errorDisplay = document.getElementById('error-display');
    document.getElementById('error-title').textContent = title;
    document.getElementById('error-message').textContent = message;
    document.getElementById('error-details').textContent = detail;
    errorDisplay.classList.add('visible');
    document.getElementById('status').style.display = 'none';
    
    // Scroll to error
    errorDisplay.scrollIntoView({ behavior: 'smooth', block: 'center' });
}

function hideError() {
    const errorDisplay = document.getElementById('error-display');
    errorDisplay.classList.remove('visible');
    document.getElementById('status').style.display = 'block';
}

function formatErrorMessage(error) {
    if (error.exc_type && error.exc_message) {
        return `${error.exc_type}: ${error.exc_message}`;
    }
    return error.message || error.toString();
}

function checkTaskStatus(taskId) {
    fetch(`/analysis/status/${taskId}`)
        .then(response => {
            if (!response.ok) {
                return response.json().then(errorData => {
                    throw new Error(formatErrorMessage(errorData.error || errorData));
                });
            }
            return response.json();
        })
        .then(data => {
            console.debug('Status update:', data);
            
            if (data.state === 'SUCCESS' && data.chunk) {
                try {
                    const chunkData = JSON.parse(data.chunk);
                    if (!handleStreamChunk(chunkData)) {
                        return; // Stop polling if handleStreamChunk returns false
                    }
                } catch (e) {
                    console.error('JSON parse error:', e);
                    showError('Error', 'Invalid response format received', e.toString());
                    return; // Stop polling on error
                }
            }
            else if (data.state === 'FAILURE') {
                const errorTitle = data.error?.exc_type || 'Analysis Error';
                const errorMessage = data.error?.exc_message || data.status || 'Analysis failed';
                const errorDetail = data.error?.exc_module ? 
                    `${data.error.exc_module}.${data.error.exc_cls}` : '';
                showError(errorTitle, errorMessage, errorDetail);
                return; // Stop polling on failure
            }
            else if (data.state === 'PENDING' || data.state === 'PROGRESS') {
                // Update progress display if available
                if (data.chunk) {
                    try {
                        const chunkData = JSON.parse(data.chunk);
                        if (chunkData.status) {
                            document.getElementById('status').textContent = chunkData.status;
                        }
                        if (chunkData.current && chunkData.total) {
                            const progress = (chunkData.current / chunkData.total) * 100;
                            document.querySelector('.progress-fill').style.width = `${progress}%`;
                        }
                    } catch (e) {
                        console.error('Progress update parse error:', e);
                        // Continue polling despite progress parse error
                    }
                }
                setTimeout(() => checkTaskStatus(taskId), 1000);
            } else {
                showError('Unexpected State', 'The analysis task entered an unexpected state', data.state);
            }
        })
        .catch(error => {
            console.error('Error:', error);
            showError('Connection Error', 'Failed to check analysis status', error.message);
        });
}

// Initialize when the document is ready
document.addEventListener('DOMContentLoaded', function() {
    // Get task ID from URL parameters first, fallback to template variable
    const urlParams = new URLSearchParams(window.location.search);
    const taskId = urlParams.get('task_id');
    
    if (taskId) {
        checkTaskStatus(taskId);
    } else {
        showError('Configuration Error', 'No task ID provided');
    }
});