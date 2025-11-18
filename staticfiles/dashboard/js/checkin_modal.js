// ===== CHECK-IN MODAL FUNCTIONALITY =====

document.addEventListener('DOMContentLoaded', function() {
    // Ensure showNotification is available
    if (typeof window.showNotification !== 'function') {
        console.error('[CHECK-IN MODAL] showNotification not found! Make sure global notifications.js is loaded.');
    }
    setupCheckInModal();
});

function setupCheckInModal() {
    const modal = document.getElementById('checkInModal');
    const btnCheckIn = document.getElementById('btnCheckIn');
    const closeModal = document.getElementById('closeModal');
    const cancelMemberCheckIn = document.getElementById('cancelMemberCheckIn');
    const cancelWalkIn = document.getElementById('cancelWalkIn');
    
    const optionBtns = document.querySelectorAll('.option-btn');
    const memberForm = document.getElementById('memberCheckInForm');
    const walkInForm = document.getElementById('walkInForm');
    
    const memberSearch = document.getElementById('memberSearch');
    const memberSearchResults = document.getElementById('memberSearchResults');
    const selectedMemberInfo = document.getElementById('selectedMemberInfo');
    const selectedMemberId = document.getElementById('selectedMemberId');
    
    let searchTimeout = null;
    let selectedMember = null;
    
    // Open modal
    btnCheckIn.addEventListener('click', () => {
        modal.classList.add('active');
    });
    
    // Close modal
    function closeModalHandler() {
        modal.classList.remove('active');
        resetModal();
    }
    
    closeModal.addEventListener('click', closeModalHandler);
    cancelMemberCheckIn.addEventListener('click', closeModalHandler);
    cancelWalkIn.addEventListener('click', closeModalHandler);
    
    // Click outside modal to close
    modal.addEventListener('click', (e) => {
        if (e.target === modal) {
            closeModalHandler();
        }
    });
    
    // Switch between member and walk-in
    optionBtns.forEach(btn => {
        btn.addEventListener('click', () => {
            const type = btn.dataset.type;
            
            // Update active button
            optionBtns.forEach(b => b.classList.remove('active'));
            btn.classList.add('active');
            
            // Show corresponding form
            if (type === 'member') {
                memberForm.classList.add('active');
                walkInForm.classList.remove('active');
            } else {
                memberForm.classList.remove('active');
                walkInForm.classList.add('active');
            }
        });
    });
    
    // Member search
    memberSearch.addEventListener('input', function() {
        const query = this.value.trim();
        
        clearTimeout(searchTimeout);
        
        if (query.length < 2) {
            memberSearchResults.classList.remove('active');
            memberSearchResults.innerHTML = '';
            return;
        }
        
        searchTimeout = setTimeout(() => {
            searchMembers(query);
        }, 300);
    });
    
    function searchMembers(query) {
        fetch(`/dashboard/search-active-members/?q=${encodeURIComponent(query)}`)
            .then(response => response.json())
            .then(data => {
                displayMemberResults(data.members);
            })
            .catch(error => {
                console.error('Error searching members:', error);
            });
    }
    
    function displayMemberResults(members) {
        if (members.length === 0) {
            memberSearchResults.innerHTML = '<div class="search-result-item">No members found</div>';
        } else {
            memberSearchResults.innerHTML = members.map(member => `
                <div class="search-result-item" data-member='${JSON.stringify(member)}'>
                    <div class="search-result-name">${member.name}</div>
                    <div class="search-result-id">ID: ${member.member_id} • Status: ${getStatusLabel(member.status)}</div>
                </div>
            `).join('');
            
            // Add click handlers
            document.querySelectorAll('.search-result-item').forEach(item => {
                item.addEventListener('click', function() {
                    const memberData = this.dataset.member;
                    if (memberData) {
                        selectMember(JSON.parse(memberData));
                    }
                });
            });
        }
        
        memberSearchResults.classList.add('active');
    }
    
    function getStatusLabel(status) {
        const labels = {
            'active': 'Active',
            'expiring': 'Expiring Soon',
            'expired': 'Expired',
            'inactive': 'Inactive'
        };
        return labels[status] || status;
    }
    
    function selectMember(member) {
        selectedMember = member;
        selectedMemberId.value = member.member_id;
        
        // Hide search results
        memberSearchResults.classList.remove('active');
        memberSearch.value = '';
        
        // Update member card (already visible by default)
        const avatarElement = document.getElementById('memberCardAvatar');
        
        // Clear previous content
        avatarElement.innerHTML = '';
        
        // Display photo if available, otherwise show initials
        if (member.photo) {
            const img = document.createElement('img');
            img.src = member.photo;
            img.alt = member.name;
            img.style.width = '100%';
            img.style.height = '100%';
            img.style.objectFit = 'cover';
            img.style.borderRadius = '50%';
            avatarElement.appendChild(img);
        } else {
            // Generate initials
            const initials = member.name.split(' ').map(n => n[0]).join('').toUpperCase().substring(0, 2);
            avatarElement.textContent = initials;
        }
        
        document.getElementById('memberCardName').textContent = member.name;
        document.getElementById('memberCardId').textContent = `ID: ${member.member_id}`;
        
        const statusBadge = document.getElementById('memberCardStatus');
        statusBadge.textContent = getStatusLabel(member.status);
        statusBadge.className = 'member-card-status ' + member.status;
        statusBadge.style.display = 'inline-block';
    }
    
    // Member check-in submission
    memberForm.addEventListener('submit', function(e) {
        e.preventDefault();
        
        if (!selectedMemberId.value) {
            // Check if showNotification exists
            if (typeof window.showNotification === 'function') {
                window.showNotification('Please select a member first', 'error');
            } else {
                alert('Please select a member first');
            }
            return;
        }
        
        const submitBtn = document.getElementById('submitMemberCheckIn');
        submitBtn.disabled = true;
        submitBtn.textContent = 'Processing...';
        
        console.log('Submitting check-in for member:', selectedMemberId.value);
        
        fetch('/dashboard/log-checkin/', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': getCsrfToken()
            },
            body: JSON.stringify({
                member_id: selectedMemberId.value
            })
        })
        .then(response => {
            console.log('Response status:', response.status);
            return response.json();
        })
        .then(data => {
            console.log('Response data:', data);
            if (data.success) {
                // Success - show notification and close modal immediately
                console.log('Check-in successful, closing modal...');
                
                // Check if showNotification exists
                if (typeof window.showNotification === 'function') {
                    window.showNotification('Check-in logged successfully!', 'success');
                    console.log('[CHECK-IN] Success notification called');
                } else {
                    console.error('[CHECK-IN] showNotification function not available!');
                    alert('Check-in logged successfully!'); // Fallback
                }
                
                // Immediately add check-in to recent check-ins list
                addCheckInToRecentList(selectedMember);
                
                // Update member check-ins count
                updateMemberCheckInsCount();
                
                // Close modal immediately
                closeModalHandler();
                
                // Reload page after delay to refresh all data
                setTimeout(() => {
                    window.location.reload();
                }, 2000);
            } else {
                console.error('Check-in failed:', data.error);
                
                // Check if showNotification exists
                if (typeof window.showNotification === 'function') {
                    window.showNotification(data.error || 'Failed to log check-in', 'error');
                    console.log('[CHECK-IN] Error notification called');
                } else {
                    console.error('[CHECK-IN] showNotification function not available!');
                    alert(data.error || 'Failed to log check-in'); // Fallback
                }
            }
        })
        .catch(error => {
            console.error('Error logging check-in:', error);
            
            // Check if showNotification exists
            if (typeof window.showNotification === 'function') {
                window.showNotification('An error occurred: ' + error.message, 'error');
            } else {
                console.error('[CHECK-IN] showNotification function not available!');
                alert('An error occurred: ' + error.message); // Fallback
            }
        })
        .finally(() => {
            // Reset button state only if not successful
            if (!document.querySelector('.notification-success')) {
                submitBtn.disabled = false;
                submitBtn.textContent = 'Log Check-in';
            }
        });
    });
    
    // Walk-in submission
    walkInForm.addEventListener('submit', function(e) {
        e.preventDefault();
        
        const name = document.getElementById('guestName').value.trim();
        const gender = document.getElementById('guestGender').value;
        
        if (!name || !gender) {
            showNotification('Please fill in all fields', 'error');
            return;
        }
        
        // Store walk-in data in sessionStorage
        sessionStorage.setItem('walkInGuest', JSON.stringify({ name, gender }));
        
        // Redirect to payments
        window.location.href = '/payments/?walkin=true';
    });
    
    // Reset modal
    function resetModal() {
        // Reset to member tab
        optionBtns[0].click();
        
        // Clear member search
        memberSearch.value = '';
        memberSearchResults.classList.remove('active');
        memberSearchResults.innerHTML = '';
        selectedMemberId.value = '';
        selectedMember = null;
        
        // Reset member card to default state (keep it visible)
        document.getElementById('memberCardAvatar').textContent = '--';
        document.getElementById('memberCardName').textContent = 'No member selected';
        document.getElementById('memberCardId').textContent = 'Search for a member above';
        const statusBadge = document.getElementById('memberCardStatus');
        statusBadge.textContent = '';
        statusBadge.className = 'member-card-status';
        statusBadge.style.display = 'none';
        
        // Clear walk-in form
        document.getElementById('guestName').value = 'Guest';
        document.getElementById('guestGender').value = '';
    }
    
    // Get CSRF token
    function getCsrfToken() {
        const cookies = document.cookie.split(';');
        for (let cookie of cookies) {
            const [name, value] = cookie.trim().split('=');
            if (name === 'csrftoken') {
                return value;
            }
        }
        return document.querySelector('[name=csrfmiddlewaretoken]')?.value || '';
    }
    
    // Add check-in to recent list immediately
    function addCheckInToRecentList(member) {
        const activityList = document.querySelector('.activity-list');
        const emptyState = document.querySelector('.empty-state');
        
        // Hide empty state if it's showing
        if (emptyState) {
            emptyState.style.display = 'none';
        }
        
        // Generate avatar HTML
        let avatarHtml;
        if (member.photo) {
            avatarHtml = `<img src="${member.photo}" alt="${member.name}" style="width: 100%; height: 100%; object-fit: cover; border-radius: 50%;">`;
        } else {
            // Generate initials
            const names = member.name.split(' ');
            let initials;
            if (names.length > 1) {
                initials = names[0][0].toUpperCase() + names[1][0].toUpperCase();
            } else {
                initials = member.name.slice(0, 2).toUpperCase();
            }
            avatarHtml = initials;
        }
        
        // Create new check-in item
        const newItem = document.createElement('div');
        newItem.className = 'activity-item';
        newItem.style.cssText = 'border-bottom: 1px solid #e0e0e0; padding-bottom: 0.75rem; margin-bottom: 0.75rem; animation: slideIn 0.3s ease;';
        newItem.innerHTML = `
            <div class="activity-avatar">${avatarHtml}</div>
            <div class="activity-details">
                <div class="activity-name">${member.name}</div>
                <div class="activity-time">Just now</div>
            </div>
        `;
        
        // Add to top of list
        if (activityList) {
            activityList.style.display = 'block';
            activityList.insertBefore(newItem, activityList.firstChild);
        } else {
            // Create activity list if it doesn't exist
            const activityCard = document.querySelector('.activity-card');
            const newList = document.createElement('div');
            newList.className = 'activity-list';
            newList.style.display = 'block';
            newList.appendChild(newItem);
            activityCard.appendChild(newList);
        }
        
        // Update badge count
        const badge = document.querySelector('.card-badge');
        if (badge) {
            const currentCount = parseInt(badge.textContent) || 0;
            badge.textContent = currentCount + 1;
        }
    }
    
    // Update member check-ins count
    function updateMemberCheckInsCount() {
        const memberCheckInsEl = document.querySelectorAll('.stat-card')[1]?.querySelector('.stat-value');
        if (memberCheckInsEl) {
            const currentCount = parseInt(memberCheckInsEl.textContent) || 0;
            memberCheckInsEl.textContent = currentCount + 1;
            
            // Add pulse animation
            memberCheckInsEl.parentElement.parentElement.style.animation = 'pulse 0.5s ease';
            setTimeout(() => {
                memberCheckInsEl.parentElement.parentElement.style.animation = '';
            }, 500);
        }
    }
    
    // Update dashboard stats dynamically
    function updateDashboardStats() {
        console.log('Fetching updated dashboard stats...');
        
        // Add pulse animation to stat cards
        document.querySelectorAll('.stat-card').forEach(card => {
            card.style.animation = 'pulse 0.5s ease';
        });
        
        fetch('/dashboard/get-stats/')
            .then(response => response.json())
            .then(data => {
                console.log('Updated stats:', data);
                
                // Update stat values
                const dailyWalkinsEl = document.querySelector('.stat-card .stat-value');
                const monthlyCheckinsEl = document.querySelectorAll('.stat-card')[1]?.querySelector('.stat-value');
                const recentCountEl = document.querySelector('.card-badge');
                
                if (dailyWalkinsEl) {
                    animateValue(dailyWalkinsEl, parseInt(dailyWalkinsEl.textContent), data.daily_walk_ins, 500);
                }
                
                if (monthlyCheckinsEl) {
                    animateValue(monthlyCheckinsEl, parseInt(monthlyCheckinsEl.textContent), data.member_check_ins, 500);
                }
                
                if (recentCountEl) {
                    recentCountEl.textContent = data.recent_check_ins.length;
                }
                
                // Update recent check-ins list
                updateRecentCheckIns(data.recent_check_ins);
                
                // Remove pulse animation after completion
                setTimeout(() => {
                    document.querySelectorAll('.stat-card').forEach(card => {
                        card.style.animation = '';
                    });
                }, 500);
            })
            .catch(error => {
                console.error('Error updating stats:', error);
            });
    }
    
    // Animate number changes
    function animateValue(element, start, end, duration) {
        const range = end - start;
        const increment = range / (duration / 16); // 60fps
        let current = start;
        
        const timer = setInterval(() => {
            current += increment;
            if ((increment > 0 && current >= end) || (increment < 0 && current <= end)) {
                current = end;
                clearInterval(timer);
            }
            element.textContent = Math.round(current);
        }, 16);
    }
    
    // Update recent check-ins list
    function updateRecentCheckIns(checkIns) {
        const activityList = document.querySelector('.activity-list');
        const emptyState = document.querySelector('.empty-state');
        const activityCard = document.querySelector('.activity-card');
        
        if (checkIns.length === 0) {
            if (activityList) activityList.style.display = 'none';
            if (emptyState) emptyState.style.display = 'flex';
            return;
        }
        
        // Hide empty state, show list
        if (emptyState) emptyState.style.display = 'none';
        
        // Build HTML for check-ins
        const html = checkIns.map(checkIn => {
            // Generate avatar HTML - either photo or initials
            let avatarHtml;
            if (checkIn.photo) {
                avatarHtml = `<img src="${checkIn.photo}" alt="${checkIn.member_name}" style="width: 100%; height: 100%; object-fit: cover; border-radius: 50%;">`;
            } else {
                // Generate initials
                const names = checkIn.member_name.split(' ');
                let initials;
                if (names.length > 1) {
                    initials = names[0][0].toUpperCase() + names[1][0].toUpperCase();
                } else {
                    initials = checkIn.member_name.slice(0, 2).toUpperCase();
                }
                avatarHtml = initials;
            }
            
            // Show (Walk-in) label for walk-in guests
            const walkInLabel = checkIn.type === 'walkin' ? ' <span style="color: #666; font-size: 0.85em;">(Walk-in)</span>' : '';
            
            return `
                <div class="activity-item" style="border-bottom: 1px solid #e0e0e0; padding-bottom: 0.75rem; margin-bottom: 0.75rem;">
                    <div class="activity-avatar">${avatarHtml}</div>
                    <div class="activity-details">
                        <div class="activity-name">${checkIn.member_name}${walkInLabel}</div>
                        <div class="activity-time">${checkIn.time_ago}</div>
                    </div>
                </div>
            `;
        }).join('');
        
        if (activityList) {
            activityList.innerHTML = html;
            activityList.style.display = 'block';
        } else {
            // Create activity list if it doesn't exist
            const newList = document.createElement('div');
            newList.className = 'activity-list';
            newList.innerHTML = html;
            activityCard.appendChild(newList);
        }
    }
}
