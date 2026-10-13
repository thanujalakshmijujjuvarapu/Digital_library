/**
 * Digital Library Hub - Interactive Client-Side Features
 * ES6+ JavaScript:
 * 1. Live Instant Search & Filter Engine (cards & count update in real-time)
 * 2. Dynamic Loan Due Date & Overdue Late Fee Simulator Modal
 * 3. Interactive Star Rating Picker & Live Character Counter
 * 4. Auto-Dismiss Alert Notifications
 */

document.addEventListener('DOMContentLoaded', () => {

    // =========================================================================
    // FEATURE 1: LIVE INSTANT SEARCH & FILTER ENGINE
    // =========================================================================
    const liveSearchInput = document.getElementById('liveSearchInput');
    const bookCards = document.querySelectorAll('.book-item-col');
    const resultsCountBadge = document.getElementById('resultsCountBadge');
    const noResultsMessage = document.getElementById('noResultsMessage');
    const categoryFilterPills = document.querySelectorAll('.filter-pill[data-category]');

    let activeCategory = 'all';
    let activeAvailability = 'all';

    function filterBooks() {
        const query = (liveSearchInput ? liveSearchInput.value : '').toLowerCase().trim();
        let visibleCount = 0;

        bookCards.forEach(card => {
            const title = (card.getAttribute('data-title') || '').toLowerCase();
            const author = (card.getAttribute('data-author') || '').toLowerCase();
            const isbn = (card.getAttribute('data-isbn') || '').toLowerCase();
            const category = (card.getAttribute('data-category') || '').toLowerCase();
            const available = card.getAttribute('data-available') === 'true';

            // Check query match
            const matchesQuery = !query || title.includes(query) || author.includes(query) || isbn.includes(query);

            // Check category match
            const matchesCategory = (activeCategory === 'all') || (category === activeCategory.toLowerCase());

            // Check availability match
            let matchesAvailability = true;
            if (activeAvailability === 'available') {
                matchesAvailability = available;
            } else if (activeAvailability === 'unavailable') {
                matchesAvailability = !available;
            }

            if (matchesQuery && matchesCategory && matchesAvailability) {
                card.style.display = '';
                visibleCount++;
            } else {
                card.style.display = 'none';
            }
        });

        // Update count badge
        if (resultsCountBadge) {
            resultsCountBadge.textContent = `${visibleCount} book${visibleCount === 1 ? '' : 's'} displayed`;
        }

        // Show/hide empty state
        if (noResultsMessage) {
            if (visibleCount === 0) {
                noResultsMessage.classList.remove('d-none');
            } else {
                noResultsMessage.classList.add('d-none');
            }
        }
    }

    if (liveSearchInput) {
        liveSearchInput.addEventListener('input', () => {
            filterBooks();
        });
    }

    if (categoryFilterPills.length > 0) {
        categoryFilterPills.forEach(pill => {
            pill.addEventListener('click', (e) => {
                e.preventDefault();
                categoryFilterPills.forEach(p => p.classList.remove('active'));
                pill.classList.add('active');
                activeCategory = pill.getAttribute('data-category');
                filterBooks();
            });
        });
    }

    // Availability Toggle switch (if present)
    const availabilityToggle = document.getElementById('availabilityFilterToggle');
    if (availabilityToggle) {
        availabilityToggle.addEventListener('change', () => {
            activeAvailability = availabilityToggle.checked ? 'available' : 'all';
            filterBooks();
        });
    }


    // =========================================================================
    // FEATURE 2: DYNAMIC LOAN DUE DATE & LATE FEE SIMULATOR MODAL
    // =========================================================================
    const loanDurationSelect = document.getElementById('loanDurationSelect');
    const calculatedDueDateEl = document.getElementById('calculatedDueDate');
    const daysLateSlider = document.getElementById('daysLateSlider');
    const daysLateDisplay = document.getElementById('daysLateDisplay');
    const estimatedFineDisplay = document.getElementById('estimatedFineDisplay');

    function updateLoanDates() {
        if (!loanDurationSelect || !calculatedDueDateEl) return;

        const duration = parseInt(loanDurationSelect.value, 10) || 14;
        const now = new Date();
        const dueDate = new Date();
        dueDate.setDate(now.getDate() + duration);

        const options = { weekday: 'long', year: 'numeric', month: 'long', day: 'numeric' };
        calculatedDueDateEl.textContent = dueDate.toLocaleDateString(undefined, options);
    }

    if (loanDurationSelect) {
        loanDurationSelect.addEventListener('change', updateLoanDates);
        updateLoanDates(); // initialize on load
    }

    // Dynamic Late Fee Simulator
    if (daysLateSlider && daysLateDisplay && estimatedFineDisplay) {
        const DAILY_RATE = 0.50; // $0.50 per day

        daysLateSlider.addEventListener('input', () => {
            const days = parseInt(daysLateSlider.value, 10);
            daysLateDisplay.textContent = `${days} day${days === 1 ? '' : 's'}`;
            const totalFine = (days * DAILY_RATE).toFixed(2);
            estimatedFineDisplay.textContent = `$${totalFine}`;

            if (days === 0) {
                estimatedFineDisplay.className = 'text-success fw-bold';
            } else if (days < 5) {
                estimatedFineDisplay.className = 'text-warning fw-bold';
            } else {
                estimatedFineDisplay.className = 'text-danger fw-bold';
            }
        });
    }


    // =========================================================================
    // FEATURE 3: STAR RATING PICKER & LIVE CHARACTER COUNTERS
    // =========================================================================
    const ratingLabels = {
        '5': '★★★★★ (5/5) - Outstanding / Essential Read',
        '4': '★★★★☆ (4/5) - Very Good / Highly Recommended',
        '3': '★★★☆☆ (3/5) - Good / Worth Reading',
        '2': '★★☆☆☆ (2/5) - Fair / Needs Improvement',
        '1': '★☆☆☆☆ (1/5) - Poor / Disappointing'
    };

    const ratingSelect = document.getElementById('reviewRatingSelect');
    const ratingHelpText = document.getElementById('ratingHelpText');

    if (ratingSelect && ratingHelpText) {
        ratingSelect.addEventListener('change', () => {
            const val = ratingSelect.value;
            ratingHelpText.textContent = ratingLabels[val] || '';
        });
    }

    // Character Counter for Review & Description textareas
    function setupCharCounter(inputId, badgeId, maxLimit) {
        const input = document.getElementById(inputId);
        const badge = document.getElementById(badgeId);

        if (!input || !badge) return;

        function updateCounter() {
            const currentLen = input.value.length;
            const remaining = maxLimit - currentLen;
            badge.textContent = `${currentLen} / ${maxLimit} characters`;

            badge.classList.remove('bg-secondary', 'bg-warning', 'bg-danger', 'bg-success');
            if (currentLen === 0) {
                badge.classList.add('bg-secondary');
            } else if (remaining < 50) {
                badge.classList.add('bg-danger');
            } else if (remaining < 150) {
                badge.classList.add('bg-warning');
            } else {
                badge.classList.add('bg-success');
            }
        }

        input.addEventListener('input', updateCounter);
        updateCounter(); // initialize
    }

    setupCharCounter('reviewCommentInput', 'reviewCharCounter', 1000);
    setupCharCounter('book-description-input', 'descCharCounter', 3000);


    // =========================================================================
    // FEATURE 4: AUTO-DISMISS ALERTS & TOAST NOTIFICATIONS
    // =========================================================================
    const flashAlerts = document.querySelectorAll('.alert-dismissible');
    flashAlerts.forEach(alert => {
        setTimeout(() => {
            alert.style.transition = 'opacity 0.6s ease, transform 0.6s ease';
            alert.style.opacity = '0';
            alert.style.transform = 'translateY(-10px)';
            setTimeout(() => {
                if (alert.parentNode) {
                    alert.parentNode.removeChild(alert);
                }
            }, 600);
        }, 5000);
    });

    // Delete Modal Dynamic Title Injection
    const deleteButtons = document.querySelectorAll('[data-bs-target="#deleteConfirmModal"]');
    const deleteBookTitleSpan = document.getElementById('deleteModalBookTitle');
    const deleteFormAction = document.getElementById('deleteModalForm');

    deleteButtons.forEach(btn => {
        btn.addEventListener('click', () => {
            const title = btn.getAttribute('data-book-title');
            const deleteUrl = btn.getAttribute('data-delete-url');
            if (deleteBookTitleSpan) deleteBookTitleSpan.textContent = title;
            if (deleteFormAction) deleteFormAction.action = deleteUrl;
        });
    });

});
