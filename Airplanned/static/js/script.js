/* ========== static/js/script.js ========== */
/* AirPlanned - Complete JavaScript functionality - FIXED VERSION */

// Wait for DOM to be fully loaded
document.addEventListener('DOMContentLoaded', function() {
    console.log('AirPlanned JavaScript loaded');
    
    // Initialize all functionality
    initializeDateInputs();
    initializeFormValidations();
    initializeInteractiveElements();
    autoHideFlashMessages();
    initializeSearchFilters();
    initializeAnimations();
});

/**
 * Initialize date inputs with appropriate constraints
 */
function initializeDateInputs() {
    const today = new Date().toISOString().split('T')[0];
    
    // Set minimum date for all date inputs to today
    const dateInputs = document.querySelectorAll('input[type="date"]');
    dateInputs.forEach(input => {
        if (!input.value) {
            input.min = today;
        }
    });
    
    // Special handling for departure and return dates
    const departureDate = document.getElementById('departure_date');
    const tripType = document.getElementById('trip_type');
    
    if (departureDate && tripType) {
        // Create return date input if it doesn't exist
        createReturnDateInput();
        
        // Handle trip type changes
        tripType.addEventListener('change', function() {
            toggleReturnDate(this.value === 'round-trip');
        });
        
        // Handle departure date changes
        departureDate.addEventListener('change', function() {
            updateReturnDateMinimum(this.value);
        });
    }
    
    // Hotel check-in/check-out date handling
    const checkInDate = document.getElementById('check_in');
    const checkOutDate = document.getElementById('check_out');
    
    if (checkInDate && checkOutDate) {
        checkInDate.addEventListener('change', function() {
            checkOutDate.min = this.value;
            if (checkOutDate.value && checkOutDate.value <= this.value) {
                const nextDay = new Date(this.value);
                nextDay.setDate(nextDay.getDate() + 1);
                checkOutDate.value = nextDay.toISOString().split('T')[0];
            }
        });
    }
    
    // Car rental pickup/return date handling
    const pickupDate = document.getElementById('pickup_date');
    const returnDate = document.getElementById('return_date');
    
    if (pickupDate && returnDate) {
        pickupDate.addEventListener('change', function() {
            returnDate.min = this.value;
            if (returnDate.value && returnDate.value <= this.value) {
                const nextDay = new Date(this.value);
                nextDay.setDate(nextDay.getDate() + 1);
                returnDate.value = nextDay.toISOString().split('T')[0];
            }
        });
    }
}

/**
 * Create return date input for round-trip flights
 */
function createReturnDateInput() {
    const departureGroup = document.getElementById('departure_date')?.closest('.form-group');
    if (!departureGroup || document.getElementById('return_date')) return;
    
    const returnDateHtml = `
        <div class="form-group" id="return_date_group" style="display: none;">
            <label for="return_date">Return Date</label>
            <input type="date" name="return_date" id="return_date" class="form-control">
        </div>
    `;
    departureGroup.insertAdjacentHTML('afterend', returnDateHtml);
}

/**
 * Toggle return date visibility for round-trip flights
 */
function toggleReturnDate(show) {
    const returnDateGroup = document.getElementById('return_date_group');
    if (returnDateGroup) {
        returnDateGroup.style.display = show ? 'flex' : 'none';
        const returnDateInput = document.getElementById('return_date');
        if (returnDateInput) {
            returnDateInput.required = show;
        }
    }
}

/**
 * Update return date minimum based on departure date
 */
function updateReturnDateMinimum(departureDate) {
    const returnDateInput = document.getElementById('return_date');
    if (returnDateInput && departureDate) {
        returnDateInput.min = departureDate;
        if (returnDateInput.value && returnDateInput.value <= departureDate) {
            const nextDay = new Date(departureDate);
            nextDay.setDate(nextDay.getDate() + 1);
            returnDateInput.value = nextDay.toISOString().split('T')[0];
        }
    }
}

/**
 * Initialize form validations
 */
function initializeFormValidations() {
    // Password confirmation validation
    const passwordInput = document.getElementById('password');
    const confirmPasswordInput = document.getElementById('confirm_password');
    
    if (passwordInput && confirmPasswordInput) {
        confirmPasswordInput.addEventListener('input', function() {
            if (passwordInput.value !== this.value) {
                this.setCustomValidity('Passwords do not match');
            } else {
                this.setCustomValidity('');
            }
        });
        
        passwordInput.addEventListener('input', function() {
            if (confirmPasswordInput.value && this.value !== confirmPasswordInput.value) {
                confirmPasswordInput.setCustomValidity('Passwords do not match');
            } else {
                confirmPasswordInput.setCustomValidity('');
            }
        });
    }
    
    // Email validation
    const emailInputs = document.querySelectorAll('input[type="email"]');
    emailInputs.forEach(input => {
        input.addEventListener('blur', function() {
            if (this.value && !isValidEmail(this.value)) {
                this.setCustomValidity('Please enter a valid email address');
            } else {
                this.setCustomValidity('');
            }
        });
    });
    
    // Phone number validation
    const phoneInputs = document.querySelectorAll('input[type="tel"]');
    phoneInputs.forEach(input => {
        input.addEventListener('input', function() {
            // Allow only numbers, spaces, hyphens, and parentheses
            this.value = this.value.replace(/[^\d\s\-\(\)\+]/g, '');
        });
        
        input.addEventListener('blur', function() {
            if (this.value && !isValidPhone(this.value)) {
                this.setCustomValidity('Please enter a valid phone number');
            } else {
                this.setCustomValidity('');
            }
        });
    });
    
    // Form submission validation
    const forms = document.querySelectorAll('form');
    forms.forEach(form => {
        form.addEventListener('submit', function(e) {
            if (!validateForm(this)) {
                e.preventDefault();
            }
        });
    });
}

/**
 * Validate email format
 */
function isValidEmail(email) {
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    return emailRegex.test(email);
}

/**
 * Validate phone number format
 */
function isValidPhone(phone) {
    const phoneRegex = /^[\+]?[\d\s\-\(\)]{10,}$/;
    return phoneRegex.test(phone.replace(/\s/g, ''));
}

/**
 * Initialize interactive elements
 */
function initializeInteractiveElements() {
    // Seat selection functionality
    initializeSeatSelection();
    
    // Payment form formatting
    initializePaymentFormatting();
    
    // Search form enhancements
    initializeSearchEnhancements();
    
    // Smooth scrolling for anchor links
    initializeSmoothScrolling();
    
    // Mobile menu toggle
    initializeMobileMenu();
    
    // Card hover effects
    initializeCardHoverEffects();
}

/**
 * Initialize seat selection functionality
 */
function initializeSeatSelection() {
    const seatMap = document.getElementById('seatMap');
    if (!seatMap) return;
    
    // Get seat selection elements
    const selectedSeatInput = document.getElementById('selectedSeat');
    const confirmButton = document.getElementById('confirmBooking');
    
    // Handle seat selection
    seatMap.addEventListener('click', function(e) {
        if (e.target.classList.contains('seat') && e.target.classList.contains('available')) {
            // Remove previous selection
            const previouslySelected = seatMap.querySelector('.seat.selected');
            if (previouslySelected) {
                previouslySelected.classList.remove('selected');
            }
            
            // Select new seat
            e.target.classList.add('selected');
            
            // Update form
            if (selectedSeatInput) {
                selectedSeatInput.value = e.target.dataset.seatNumber;
            }
            
            if (confirmButton) {
                confirmButton.disabled = false;
                const price = confirmButton.dataset.price || '0';
                confirmButton.textContent = `Confirm Booking - Seat ${e.target.dataset.seatNumber} - $${price}`;
            }
            
            // Visual feedback
            showSeatSelectionFeedback(e.target.dataset.seatNumber);
        }
    });
}

/**
 * Show seat selection feedback
 */
function showSeatSelectionFeedback(seatNumber) {
    // Create or update feedback message
    let feedback = document.getElementById('seat-feedback');
    if (!feedback) {
        feedback = document.createElement('div');
        feedback.id = 'seat-feedback';
        feedback.className = 'seat-feedback';
        feedback.style.cssText = `
            position: fixed;
            top: 20px;
            right: 20px;
            background: #10b981;
            color: white;
            padding: 1rem;
            border-radius: 8px;
            z-index: 1000;
            animation: slideIn 0.3s ease;
            box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
        `;
        document.body.appendChild(feedback);
    }
    
    feedback.textContent = `✓ Seat ${seatNumber} selected!`;
    feedback.style.display = 'block';
    
    // Auto-hide after 3 seconds
    setTimeout(() => {
        if (feedback) {
            feedback.style.animation = 'slideOut 0.3s ease';
            setTimeout(() => {
                if (feedback.parentNode) {
                    feedback.parentNode.removeChild(feedback);
                }
            }, 300);
        }
    }, 3000);
}

/**
 * Initialize payment form formatting
 */
function initializePaymentFormatting() {
    // Card number formatting
    const cardNumberInput = document.getElementById('card_number');
    if (cardNumberInput) {
        cardNumberInput.addEventListener('input', function(e) {
            let value = e.target.value.replace(/\s/g, '');
            let formattedValue = value.replace(/(.{4})/g, '$1 ').trim();
            if (formattedValue.length > 19) {
                formattedValue = formattedValue.substring(0, 19);
            }
            e.target.value = formattedValue;
        });
        
        cardNumberInput.addEventListener('keypress', function(e) {
            // Allow only numbers and backspace
            if (!/[\d\s]/.test(e.key) && e.key !== 'Backspace') {
                e.preventDefault();
            }
        });
    }
    
    // Expiry date formatting
    const expiryDateInput = document.getElementById('expiry_date');
    if (expiryDateInput) {
        expiryDateInput.addEventListener('input', function(e) {
            let value = e.target.value.replace(/\D/g, '');
            if (value.length >= 2) {
                value = value.substring(0, 2) + '/' + value.substring(2, 4);
            }
            e.target.value = value;
        });
        
        expiryDateInput.addEventListener('keypress', function(e) {
            // Allow only numbers and backspace
            if (!/\d/.test(e.key) && e.key !== 'Backspace') {
                e.preventDefault();
            }
        });
    }
    
    // CVV formatting
    const cvvInput = document.getElementById('cvv');
    if (cvvInput) {
        cvvInput.addEventListener('input', function(e) {
            e.target.value = e.target.value.replace(/\D/g, '');
        });
        
        cvvInput.addEventListener('keypress', function(e) {
            // Allow only numbers and backspace
            if (!/\d/.test(e.key) && e.key !== 'Backspace') {
                e.preventDefault();
            }
        });
    }
}

/**
 * Initialize search form enhancements
 */
function initializeSearchEnhancements() {
    // Add loading state to search buttons
    const searchForms = document.querySelectorAll('.search-form');
    searchForms.forEach(form => {
        form.addEventListener('submit', function() {
            const submitButton = form.querySelector('button[type="submit"]');
            if (submitButton) {
                const originalText = submitButton.textContent;
                submitButton.innerHTML = '🔍 Searching...';
                submitButton.disabled = true;
                
                // Re-enable after 5 seconds if form doesn't submit
                setTimeout(() => {
                    submitButton.innerHTML = originalText;
                    submitButton.disabled = false;
                }, 5000);
            }
        });
    });
    
    // Price range validation
    const minPriceInput = document.getElementById('min_price');
    const maxPriceInput = document.getElementById('max_price');
    
    if (minPriceInput && maxPriceInput) {
        function validatePriceRange() {
            const minPrice = parseFloat(minPriceInput.value) || 0;
            const maxPrice = parseFloat(maxPriceInput.value) || Infinity;
            
            if (minPrice > maxPrice) {
                maxPriceInput.setCustomValidity('Maximum price must be greater than minimum price');
            } else {
                maxPriceInput.setCustomValidity('');
            }
        }
        
        minPriceInput.addEventListener('input', validatePriceRange);
        maxPriceInput.addEventListener('input', validatePriceRange);
    }
}

/**
 * Initialize smooth scrolling
 */
function initializeSmoothScrolling() {
    const links = document.querySelectorAll('a[href^="#"]');
    links.forEach(link => {
        link.addEventListener('click', function(e) {
            e.preventDefault();
            const targetId = this.getAttribute('href').substring(1);
            const targetElement = document.getElementById(targetId);
            
            if (targetElement) {
                targetElement.scrollIntoView({
                    behavior: 'smooth',
                    block: 'start'
                });
            }
        });
    });
}

/**
 * Initialize mobile menu
 */
function initializeMobileMenu() {
    const navMenu = document.querySelector('.nav-menu');
    if (!navMenu) return;
    
    // Create mobile menu toggle button
    const toggleButton = document.createElement('button');
    toggleButton.className = 'mobile-menu-toggle';
    toggleButton.innerHTML = '☰';
    toggleButton.style.cssText = `
        display: none;
        background: none;
        border: none;
        color: white;
        font-size: 1.5rem;
        cursor: pointer;
        padding: 0.5rem;
    `;
    
    // Insert toggle button before nav menu
    navMenu.parentNode.insertBefore(toggleButton, navMenu);
    
    // Toggle menu on button click
    toggleButton.addEventListener('click', function() {
        navMenu.classList.toggle('mobile-open');
        this.innerHTML = navMenu.classList.contains('mobile-open') ? '✕' : '☰';
    });
    
    // Close menu when clicking outside
    document.addEventListener('click', function(e) {
        if (!navMenu.contains(e.target) && !toggleButton.contains(e.target)) {
            navMenu.classList.remove('mobile-open');
            toggleButton.innerHTML = '☰';
        }
    });
    
    // Close menu on window resize
    window.addEventListener('resize', function() {
        if (window.innerWidth > 768) {
            navMenu.classList.remove('mobile-open');
            toggleButton.innerHTML = '☰';
        }
    });
}

/**
 * Initialize card hover effects
 */
function initializeCardHoverEffects() {
    const cards = document.querySelectorAll('.flight-card, .hotel-card, .car-card, .booking-card');
    
    cards.forEach(card => {
        card.addEventListener('mouseenter', function() {
            this.style.transform = 'translateY(-4px)';
            this.style.transition = 'all 0.3s ease';
        });
        
        card.addEventListener('mouseleave', function() {
            this.style.transform = 'translateY(0)';
        });
    });
}

/**
 * Auto-hide flash messages
 */
function autoHideFlashMessages() {
    const alerts = document.querySelectorAll('.alert');
    alerts.forEach(alert => {
        setTimeout(() => {
            if (alert && alert.parentNode) {
                alert.style.animation = 'fadeOut 0.5s ease';
                setTimeout(() => {
                    if (alert.parentNode) {
                        alert.parentNode.removeChild(alert);
                    }
                }, 500);
            }
        }, 5000);
    });
}

/**
 * Initialize search filters
 */
function initializeSearchFilters() {
    // Real-time flight filtering
    const filterInputs = document.querySelectorAll('#min_price, #max_price, select[name="airline"]');
    filterInputs.forEach(input => {
        input.addEventListener('change', filterFlights);
    });
    
    // Airline filter
    populateAirlineFilter();
}

/**
 * Filter flights based on current filter values
 */
function filterFlights() {
    const minPrice = parseFloat(document.getElementById('min_price')?.value) || 0;
    const maxPrice = parseFloat(document.getElementById('max_price')?.value) || Infinity;
    const selectedAirline = document.querySelector('select[name="airline"]')?.value || '';
    
    const flightCards = document.querySelectorAll('.flight-card');
    
    flightCards.forEach(card => {
        const priceElement = card.querySelector('.price');
        const airlineElement = card.querySelector('.airline');
        
        if (!priceElement || !airlineElement) return;
        
        const price = parseFloat(priceElement.textContent.replace(/[$,]/g, ''));
        const airline = airlineElement.textContent.trim();
        
        const priceMatch = price >= minPrice && price <= maxPrice;
        const airlineMatch = !selectedAirline || airline.includes(selectedAirline);
        
        if (priceMatch && airlineMatch) {
            card.style.display = 'block';
            card.style.animation = 'fadeIn 0.3s ease';
        } else {
            card.style.display = 'none';
        }
    });
    
    updateFlightCount();
}

/**
 * Populate airline filter dropdown
 */
function populateAirlineFilter() {
    const airlineSelect = document.querySelector('select[name="airline"]');
    if (!airlineSelect) return;
    
    const airlines = new Set();
    document.querySelectorAll('.airline').forEach(element => {
        airlines.add(element.textContent.trim());
    });
    
    airlines.forEach(airline => {
        if (airline) {
            const option = document.createElement('option');
            option.value = airline;
            option.textContent = airline;
            airlineSelect.appendChild(option);
        }
    });
}

/**
 * Update flight count display
 */
function updateFlightCount() {
    const visibleFlights = document.querySelectorAll('.flight-card[style*="display: block"], .flight-card:not([style*="display: none"])').length;
    const countElement = document.querySelector('.flights-count');
    
    if (countElement) {
        countElement.textContent = `${visibleFlights} flights found`;
    }
}

/**
 * Initialize animations
 */
function initializeAnimations() {
    // Observe elements for scroll animations
    const observerOptions = {
        threshold: 0.1,
        rootMargin: '0px 0px -50px 0px'
    };
    
    const observer = new IntersectionObserver(function(entries) {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                entry.target.style.animation = 'fadeInUp 0.6s ease forwards';
                observer.unobserve(entry.target);
            }
        });
    }, observerOptions);
    
    // Observe cards and sections
    const animatedElements = document.querySelectorAll('.flight-card, .hotel-card, .car-card, .info-card, .stat-card');
    animatedElements.forEach(element => {
        element.style.opacity = '0';
        element.style.transform = 'translateY(20px)';
        observer.observe(element);
    });
}

/**
 * Utility function to format currency
 */
function formatCurrency(amount) {
    return new Intl.NumberFormat('en-US', {
        style: 'currency',
        currency: 'USD'
    }).format(amount);
}

/**
 * Utility function to format date
 */
function formatDate(dateString) {
    const date = new Date(dateString);
    return date.toLocaleDateString('en-US', {
        year: 'numeric',
        month: 'long',
        day: 'numeric'
    });
}

/**
 * Utility function to format time
 */
function formatTime(timeString) {
    const [hours, minutes] = timeString.split(':');
    const time = new Date();
    time.setHours(parseInt(hours), parseInt(minutes));
    return time.toLocaleTimeString('en-US', {
        hour: 'numeric',
        minute: '2-digit',
        hour12: true
    });
}

/**
 * Show loading spinner
 */
function showLoading(element, text = 'Loading...') {
    if (element) {
        const originalContent = element.innerHTML;
        element.dataset.originalContent = originalContent;
        element.innerHTML = `<span class="loading-spinner">⏳</span> ${text}`;
        element.disabled = true;
    }
}

/**
 * Hide loading spinner
 */
function hideLoading(element) {
    if (element && element.dataset.originalContent) {
        element.innerHTML = element.dataset.originalContent;
        element.disabled = false;
        delete element.dataset.originalContent;
    }
}

/**
 * Show toast notification
 */
function showToast(message, type = 'info', duration = 4000) {
    const toast = document.createElement('div');
    toast.className = `toast toast-${type}`;
    toast.style.cssText = `
        position: fixed;
        top: 20px;
        right: 20px;
        background: ${getToastColor(type)};
        color: white;
        padding: 1rem 1.5rem;
        border-radius: 8px;
        z-index: 1000;
        animation: slideIn 0.3s ease;
        max-width: 300px;
        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
        font-weight: 500;
    `;
    toast.textContent = message;
    
    document.body.appendChild(toast);
    
    setTimeout(() => {
        toast.style.animation = 'slideOut 0.3s ease';
        setTimeout(() => {
            if (toast.parentNode) {
                toast.parentNode.removeChild(toast);
            }
        }, 300);
    }, duration);
}

/**
 * Get toast background color based on type
 */
function getToastColor(type) {
    const colors = {
        success: '#10b981',
        error: '#ef4444',
        warning: '#f59e0b',
        info: '#3b82f6'
    };
    return colors[type] || colors.info;
}

/**
 * Validate form before submission
 */
function validateForm(form) {
    const requiredFields = form.querySelectorAll('[required]');
    let isValid = true;
    let firstInvalidField = null;
    
    requiredFields.forEach(field => {
        if (!field.value.trim()) {
            field.classList.add('error');
            isValid = false;
            if (!firstInvalidField) {
                firstInvalidField = field;
            }
        } else {
            field.classList.remove('error');
        }
    });
    
    if (!isValid && firstInvalidField) {
        firstInvalidField.focus();
        showToast('Please fill in all required fields', 'error');
    }
    
    return isValid;
}

/**
 * Initialize search suggestions
 */
function initializeSearchSuggestions() {
    const locationInputs = document.querySelectorAll('input[list]');
    
    locationInputs.forEach(input => {
        input.addEventListener('input', function() {
            const value = this.value.toLowerCase();
            const datalist = document.getElementById(this.getAttribute('list'));
            
            if (datalist && value.length >= 2) {
                // Filter options based on input
                const options = datalist.querySelectorAll('option');
                options.forEach(option => {
                    const text = option.value.toLowerCase();
                    option.style.display = text.includes(value) ? 'block' : 'none';
                });
            }
        });
    });
}

/**
 * Handle offline functionality
 */
function initializeOfflineSupport() {
    window.addEventListener('online', function() {
        showToast('Connection restored', 'success');
        document.body.classList.remove('offline');
    });
    
    window.addEventListener('offline', function() {
        showToast('No internet connection', 'warning', 6000);
        document.body.classList.add('offline');
    });
}

/**
 * Initialize accessibility features
 */
function initializeAccessibility() {
    // Skip to main content link
    const skipLink = document.createElement('a');
    skipLink.href = '#main-content';
    skipLink.textContent = 'Skip to main content';
    skipLink.className = 'skip-link';
    skipLink.style.cssText = `
        position: absolute;
        top: -40px;
        left: 6px;
        background: #000;
        color: #fff;
        padding: 8px;
        text-decoration: none;
        z-index: 1000;
        border-radius: 4px;
    `;
    
    skipLink.addEventListener('focus', function() {
        this.style.top = '6px';
    });
    
    skipLink.addEventListener('blur', function() {
        this.style.top = '-40px';
    });
    
    document.body.insertBefore(skipLink, document.body.firstChild);
    
    // Add keyboard navigation for cards
    const cards = document.querySelectorAll('.flight-card, .hotel-card, .car-card');
    cards.forEach(card => {
        card.setAttribute('tabindex', '0');
        card.setAttribute('role', 'button');
        
        card.addEventListener('keydown', function(e) {
            if (e.key === 'Enter' || e.key === ' ') {
                e.preventDefault();
                const button = this.querySelector('.btn');
                if (button) {
                    button.click();
                }
            }
        });
    });
}

// Add CSS animations
const style = document.createElement('style');
style.textContent = `
    @keyframes slideIn {
        from { transform: translateX(100%); opacity: 0; }
        to { transform: translateX(0); opacity: 1; }
    }
    
    @keyframes slideOut {
        from { transform: translateX(0); opacity: 1; }
        to { transform: translateX(100%); opacity: 0; }
    }
    
    @keyframes fadeOut {
        from { opacity: 1; }
        to { opacity: 0; }
    }
    
    @keyframes fadeIn {
        from { opacity: 0; }
        to { opacity: 1; }
    }
    
    @keyframes fadeInUp {
        from { 
            opacity: 0; 
            transform: translateY(20px); 
        }
        to { 
            opacity: 1; 
            transform: translateY(0); 
        }
    }
    
    .loading-spinner {
        display: inline-block;
        animation: spin 1s linear infinite;
    }
    
    @keyframes spin {
        from { transform: rotate(0deg); }
        to { transform: rotate(360deg); }
    }
    
    .form-control.error {
        border-color: #ef4444 !important;
        box-shadow: 0 0 0 3px rgba(239, 68, 68, 0.1) !important;
    }
    
    .seat {
        position: relative;
        overflow: hidden;
    }
    
    .seat.available::before {
        content: '';
        position: absolute;
        top: 0;
        left: -100%;
        width: 100%;
        height: 100%;
        background: linear-gradient(90deg, transparent, rgba(255,255,255,0.3), transparent);
        transition: left 0.5s;
    }
    
    .seat.available:hover::before {
        left: 100%;
    }
    
    .skip-link:focus {
        top: 6px !important;
    }
    
    .offline {
        filter: grayscale(50%);
    }
    
    .offline::before {
        content: "⚠ Offline Mode";
        position: fixed;
        top: 0;
        left: 0;
        right: 0;
        background: #f59e0b;
        color: white;
        text-align: center;
        padding: 0.5rem;
        z-index: 1001;
        font-weight: bold;
    }
    
    @media (max-width: 768px) {
        .mobile-menu-toggle {
            display: block !important;
        }
        
        .nav-menu {
            position: absolute;
            top: 100%;
            left: 0;
            right: 0;
            background: inherit;
            flex-direction: column;
            max-height: 0;
            overflow: hidden;
            transition: max-height 0.3s ease;
        }
        
        .nav-menu.mobile-open {
            max-height: 300px;
            padding: 1rem 0;
        }
        
        .nav-menu .nav-link {
            padding: 0.75rem 2rem;
            border-bottom: 1px solid rgba(255, 255, 255, 0.1);
        }
    }
`;
document.head.appendChild(style);

// Initialize additional features
initializeSearchSuggestions();
initializeOfflineSupport();
initializeAccessibility();

// Export functions for global use
window.AirPlanned = {
    formatCurrency,
    formatDate,
    formatTime,
    showLoading,
    hideLoading,
    showToast,
    validateForm,
    filterFlights
};