document.addEventListener('DOMContentLoaded', function() {
    // DOM Elements
    const stockSymbolInput = document.getElementById('stockSymbol');
    const analyzeBtn = document.getElementById('analyzeBtn');
    const loadingIndicator = document.getElementById('loadingIndicator');
    const resultContainer = document.getElementById('resultContainer');
    const errorContainer = document.getElementById('errorContainer');
    const errorMessage = document.getElementById('errorMessage');
    const reportContent = document.getElementById('reportContent');
    const stockTitle = document.getElementById('stockTitle');
    const refreshBtn = document.getElementById('refreshBtn');
    const downloadBtn = document.getElementById('downloadBtn');
    const rawDataContainer = document.getElementById('rawDataContainer');
    const toggleRawDataBtn = document.getElementById('toggleRawData');
    const rawDataContent = document.getElementById('rawDataContent');
    const rawDataJson = document.getElementById('rawDataJson');

    // Current stock data
    let currentSymbol = '';
    let currentReport = '';
    let currentRawData = null;
    let pageLoadComplete = false;

    // Force hide loading indicator on page load 
    loadingIndicator.style.display = 'none';
    loadingIndicator.classList.add('hidden');
    hideLoading();
    hideError();
    hideResults();

    // Set the pageLoadComplete flag after a brief delay
    setTimeout(() => {
        pageLoadComplete = true;
    }, 500);

    // Event Listeners
    analyzeBtn.addEventListener('click', analyzeStock);
    stockSymbolInput.addEventListener('keypress', function(e) {
        if (e.key === 'Enter') {
            analyzeStock();
        }
    });
    refreshBtn.addEventListener('click', () => {
        showError('Fetching latest market data...');
        setTimeout(() => {
            analyzeStock(true);
        }, 500);
    });
    downloadBtn.addEventListener('click', downloadReport);
    toggleRawDataBtn.addEventListener('click', toggleRawData);

    // Functions
    async function analyzeStock(forceRefresh = false) {
        const symbol = stockSymbolInput.value.trim().toUpperCase();
        
        if (!symbol) {
            showError('Please enter a valid stock symbol (e.g., AAPL, MSFT, GOOGL)');
            return;
        }

        currentSymbol = symbol;
        
        // Only show loading if page load is complete
        if (pageLoadComplete) {
            showLoading();
        }
        
        hideError();
        hideResults();

        try {
            // Prepare request data
            const requestData = { 
                "symbol": symbol, 
                "force_refresh": forceRefresh 
            };
            
            console.log('Sending request data:', requestData);
            
            // Make API request to analyze stock
            const response = await fetch('/analyze2', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(requestData)
            });

            console.log('Response status:', response.status);
            
            if (!response.ok) {
                const errorData = await response.json();
                console.error('Error data:', errorData);
                throw new Error(errorData.detail || 'Failed to analyze stock');
            }

            const data = await response.json();
            console.log('Response data:', data);
            
            currentReport = data.report;
            currentRawData = data.raw_data;

            // Display results
            displayResults(data);
        } catch (error) {
            // Improved error handling to ensure we show a proper message
            let errorMsg = 'An error occurred while analyzing the stock';
            if (error instanceof Error) {
                errorMsg = error.message || errorMsg;
            }
            showError(errorMsg);
            console.error('Error:', error);
        } finally {
            hideLoading();
        }
    }

    function displayResults(data) {
        stockTitle.textContent = `${data.symbol} - Stock Analysis`;
        
        // Use marked.js to convert markdown to HTML
        reportContent.innerHTML = marked.parse(data.report);
        
        // Display raw data
        if (data.raw_data) {
            rawDataJson.textContent = JSON.stringify(data.raw_data, null, 2);
            rawDataContainer.classList.remove('hidden');
        } else {
            rawDataContainer.classList.add('hidden');
        }
        
        resultContainer.classList.remove('hidden');
    }

    function downloadReport() {
        if (!currentReport || !currentSymbol) return;
        
        const filename = `${currentSymbol}_Analysis_${formatDate(new Date())}.md`;
        const blob = new Blob([currentReport], { type: 'text/markdown' });
        const url = URL.createObjectURL(blob);
        
        const a = document.createElement('a');
        a.href = url;
        a.download = filename;
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        URL.revokeObjectURL(url);
    }

    function toggleRawData() {
        rawDataContent.classList.toggle('hidden');
        toggleRawDataBtn.classList.toggle('active');
        
        const icon = toggleRawDataBtn.querySelector('i');
        if (rawDataContent.classList.contains('hidden')) {
            icon.className = 'fas fa-chevron-down';
        } else {
            icon.className = 'fas fa-chevron-up';
        }
    }

    function showLoading() {
        loadingIndicator.style.display = 'flex';
        loadingIndicator.classList.remove('hidden');
    }

    function hideLoading() {
        loadingIndicator.style.display = 'none';
        loadingIndicator.classList.add('hidden');
    }

    function showError(message) {
        errorMessage.textContent = message;
        errorContainer.classList.remove('hidden');
    }

    function hideError() {
        errorContainer.classList.add('hidden');
    }

    function hideResults() {
        resultContainer.classList.add('hidden');
        rawDataContainer.classList.add('hidden');
    }

    function formatDate(date) {
        const year = date.getFullYear();
        const month = String(date.getMonth() + 1).padStart(2, '0');
        const day = String(date.getDate()).padStart(2, '0');
        return `${year}${month}${day}`;
    }
}); 