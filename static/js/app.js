/**
 * Grand Stay Hotel Booking System
 * Dynamic Frontend Logic with Fetch API, Modals, State Management, and Real-time validation
 */

document.addEventListener('DOMContentLoaded', () => {
  // Global In-Memory State
  let rooms = [];
  let bookings = [];

  // DOM Elements
  const toastContainer = document.getElementById('toast-container');
  const statTotalRooms = document.getElementById('stat-total-rooms');
  const statAvailableRooms = document.getElementById('stat-available-rooms');
  const statBookedRooms = document.getElementById('stat-booked-rooms');
  const statActiveBookings = document.getElementById('stat-active-bookings');

  const roomsTableBody = document.getElementById('rooms-table-body');
  const bookingsTableBody = document.getElementById('bookings-table-body');
  const bookingRoomSelect = document.getElementById('booking-room-select');

  // Forms
  const createRoomForm = document.getElementById('create-room-form');
  const createBookingForm = document.getElementById('create-booking-form');
  const searchAvailabilityForm = document.getElementById('search-availability-form');
  const editRoomForm = document.getElementById('edit-room-form');
  const quickBookForm = document.getElementById('quick-book-form');

  // Modals
  const editRoomModal = document.getElementById('edit-room-modal');
  const quickBookModal = document.getElementById('quick-book-modal');

  // Filters & Controls
  const filterRoomInput = document.getElementById('filter-room-input');
  const filterBookingStatus = document.getElementById('filter-booking-status');
  const btnRefreshAll = document.getElementById('btn-refresh-all');
  const btnOpenAddRoomModal = document.getElementById('btn-open-add-room-modal');
  const btnClearSearch = document.getElementById('btn-clear-search');
  const availabilityResultsContainer = document.getElementById('availability-results-container');
  const availabilityResultsGrid = document.getElementById('availability-results-grid');
  const availabilityResultsHeading = document.getElementById('availability-results-heading');

  // --------------------------------------------------------------------------
  // Utility: Toast Notifications
  // --------------------------------------------------------------------------
  function showToast(message, type = 'info', duration = 4000) {
    const toast = document.createElement('div');
    toast.className = `toast toast-${type}`;

    const iconMap = {
      success: '✅',
      error: '❌',
      info: 'ℹ️'
    };

    toast.innerHTML = `
      <div style="display:flex; align-items:center; gap:0.5rem;">
        <span>${iconMap[type] || 'ℹ️'}</span>
        <span>${message}</span>
      </div>
      <button class="toast-close">&times;</button>
    `;

    toast.querySelector('.toast-close').addEventListener('click', () => {
      toast.remove();
    });

    toastContainer.appendChild(toast);

    setTimeout(() => {
      if (toast.parentElement) {
        toast.style.opacity = '0';
        toast.style.transform = 'translateX(100%)';
        toast.style.transition = 'all 0.3s ease';
        setTimeout(() => toast.remove(), 300);
      }
    }, duration);
  }

  // --------------------------------------------------------------------------
  // Utility: Date Format & Defaulting
  // --------------------------------------------------------------------------
  function formatDate(dateStr) {
    if (!dateStr) return 'N/A';
    try {
      const parts = dateStr.split('T')[0].split('-');
      if (parts.length === 3) {
        const d = new Date(parts[0], parts[1] - 1, parts[2]);
        return d.toLocaleDateString('en-US', { year: 'numeric', month: 'short', day: 'numeric' });
      }
      return dateStr;
    } catch {
      return dateStr;
    }
  }

  function getTodayString() {
    const d = new Date();
    return d.toISOString().split('T')[0];
  }

  function getTomorrowString() {
    const d = new Date();
    d.setDate(d.getDate() + 1);
    return d.toISOString().split('T')[0];
  }

  // Set default dates on load
  const today = getTodayString();
  const tomorrow = getTomorrowString();

  const searchCheckIn = document.getElementById('search-check-in');
  const searchCheckOut = document.getElementById('search-check-out');
  const bookingCheckIn = document.getElementById('booking-check-in');
  const bookingCheckOut = document.getElementById('booking-check-out');

  if (searchCheckIn) searchCheckIn.value = today;
  if (searchCheckOut) searchCheckOut.value = tomorrow;
  if (bookingCheckIn) bookingCheckIn.value = today;
  if (bookingCheckOut) bookingCheckOut.value = tomorrow;

  // --------------------------------------------------------------------------
  // API Fetch Wrappers
  // --------------------------------------------------------------------------
  async function fetchAPI(endpoint, options = {}) {
    try {
      const response = await fetch(endpoint, {
        headers: {
          'Content-Type': 'application/json',
          'Accept': 'application/json',
          ...(options.headers || {})
        },
        ...options
      });

      const data = await response.json().catch(() => ({
        success: false,
        message: 'Non-JSON server response',
        error: 'INVALID_RESPONSE'
      }));

      return { ok: response.ok, status: response.status, data };
    } catch (err) {
      console.error('Network request failed:', err);
      return {
        ok: false,
        status: 0,
        data: {
          success: false,
          message: 'Network error or server unreachable. Please verify server is running.',
          error: 'NETWORK_ERROR'
        }
      };
    }
  }

  // --------------------------------------------------------------------------
  // Data Loading & Dashboard Metrics
  // --------------------------------------------------------------------------
  async function loadRooms() {
    const res = await fetchAPI('/api/rooms');
    if (res.ok && res.data.success) {
      rooms = res.data.data;
      renderRoomsTable();
      populateRoomDropdown();
      updateDashboardMetrics();
    } else {
      showToast(res.data.message || 'Failed to fetch rooms', 'error');
    }
  }

  async function loadBookings() {
    const res = await fetchAPI('/api/bookings');
    if (res.ok && res.data.success) {
      bookings = res.data.data;
      renderBookingsTable();
      updateDashboardMetrics();
    } else {
      showToast(res.data.message || 'Failed to fetch bookings', 'error');
    }
  }

  async function refreshAllData() {
    await Promise.all([loadRooms(), loadBookings()]);
  }

  function updateDashboardMetrics() {
    const total = rooms.length;
    const maintenanceCount = rooms.filter(r => r.availability_status === 'MAINTENANCE').length;
    const bookedStatusCount = rooms.filter(r => r.availability_status === 'BOOKED').length;
    const activeBookingsCount = bookings.filter(b => b.booking_status === 'CONFIRMED').length;
    
    // Rooms that are available (status is AVAILABLE)
    const availableCount = rooms.filter(r => r.availability_status === 'AVAILABLE').length;

    statTotalRooms.textContent = total;
    statAvailableRooms.textContent = availableCount;
    statBookedRooms.textContent = bookedStatusCount;
    statActiveBookings.textContent = activeBookingsCount;
  }

  function populateRoomDropdown() {
    if (!bookingRoomSelect) return;
    const currentVal = bookingRoomSelect.value;
    bookingRoomSelect.innerHTML = '<option value="">-- Choose a Room --</option>';

    rooms.forEach(room => {
      const option = document.createElement('option');
      option.value = room.id;
      const isMaint = room.availability_status === 'MAINTENANCE';
      option.disabled = isMaint;
      option.textContent = `Room ${room.room_number} - ${room.room_type} (₹${room.price.toFixed(2)}/night)${isMaint ? ' [MAINTENANCE]' : ''}`;
      bookingRoomSelect.appendChild(option);
    });

    if (currentVal) {
      bookingRoomSelect.value = currentVal;
    }
  }

  // --------------------------------------------------------------------------
  // Table Renderers
  // --------------------------------------------------------------------------
  function renderRoomsTable() {
    const filterText = (filterRoomInput ? filterRoomInput.value : '').toLowerCase().trim();
    const filteredRooms = rooms.filter(room => {
      if (!filterText) return true;
      return room.room_number.toLowerCase().includes(filterText) ||
             room.room_type.toLowerCase().includes(filterText) ||
             room.availability_status.toLowerCase().includes(filterText);
    });

    if (filteredRooms.length === 0) {
      roomsTableBody.innerHTML = `
        <tr>
          <td colspan="6">
            <div class="empty-state">
              <div class="empty-state-icon">🛏️</div>
              <div class="empty-state-text">No rooms found. Add a room to get started.</div>
            </div>
          </td>
        </tr>
      `;
      return;
    }

    roomsTableBody.innerHTML = filteredRooms.map(room => {
      const statusBadge = `<span class="badge badge-${room.availability_status.toLowerCase()}">${room.availability_status}</span>`;
      return `
        <tr data-room-id="${room.id}">
          <td style="font-weight: 600;">Room ${escapeHtml(room.room_number)}</td>
          <td>${escapeHtml(room.room_type)}</td>
          <td>₹${room.price.toFixed(2)}</td>
          <td>${statusBadge}</td>
          <td style="color: var(--text-muted); font-size: 0.85rem;">${formatDate(room.created_at)}</td>
          <td>
            <div style="display: flex; gap: 0.5rem;">
              <button class="btn btn-secondary btn-sm btn-edit-room" data-id="${room.id}">✏️ Edit</button>
              <button class="btn btn-danger btn-sm btn-delete-room" data-id="${room.id}" data-num="${escapeHtml(room.room_number)}">🗑️ Delete</button>
            </div>
          </td>
        </tr>
      `;
    }).join('');
  }

  function renderBookingsTable() {
    const filterStatus = filterBookingStatus ? filterBookingStatus.value : '';
    const filteredBookings = bookings.filter(b => {
      if (!filterStatus) return true;
      return b.booking_status === filterStatus;
    });

    if (filteredBookings.length === 0) {
      bookingsTableBody.innerHTML = `
        <tr>
          <td colspan="7">
            <div class="empty-state">
              <div class="empty-state-icon">📋</div>
              <div class="empty-state-text">No bookings recorded yet.</div>
            </div>
          </td>
        </tr>
      `;
      return;
    }

    bookingsTableBody.innerHTML = filteredBookings.map(b => {
      const statusBadge = `<span class="badge badge-${b.booking_status.toLowerCase()}">${b.booking_status}</span>`;
      const isConfirmed = b.booking_status === 'CONFIRMED';
      
      const actionButton = isConfirmed
        ? `<button class="btn btn-danger btn-sm btn-cancel-booking" data-id="${b.id}">❌ Cancel Booking</button>`
        : `<span style="color: var(--text-muted); font-size: 0.8rem;">No actions</span>`;

      return `
        <tr data-booking-id="${b.id}">
          <td style="font-weight: 600;">#${b.id}</td>
          <td>
            <div style="font-weight: 500;">${escapeHtml(b.guest_name)}</div>
            <div style="font-size: 0.8rem; color: var(--text-muted);">${escapeHtml(b.guest_email)}</div>
          </td>
          <td>
            <span style="font-weight: 500;">Room ${escapeHtml(b.room_number || String(b.room_id))}</span>
            ${b.room_type ? `<div style="font-size: 0.8rem; color: var(--text-muted);">${escapeHtml(b.room_type)}</div>` : ''}
          </td>
          <td>${formatDate(b.check_in)}</td>
          <td>${formatDate(b.check_out)}</td>
          <td>${statusBadge}</td>
          <td>${actionButton}</td>
        </tr>
      `;
    }).join('');
  }

  // --------------------------------------------------------------------------
  // Search & Dynamic Availability
  // --------------------------------------------------------------------------
  if (searchAvailabilityForm) {
    searchAvailabilityForm.addEventListener('submit', async (e) => {
      e.preventDefault();
      const checkIn = searchCheckIn.value;
      const checkOut = searchCheckOut.value;
      const type = document.getElementById('search-room-type').value;

      if (!checkIn || !checkOut) {
        showToast('Please select both check-in and check-out dates', 'error');
        return;
      }

      if (checkIn >= checkOut) {
        showToast('Check-in date must be strictly before check-out date', 'error');
        return;
      }

      let url = `/api/rooms/available?check_in=${encodeURIComponent(checkIn)}&check_out=${encodeURIComponent(checkOut)}`;
      if (type) {
        url += `&type=${encodeURIComponent(type)}`;
      }

      availabilityResultsContainer.style.display = 'block';
      availabilityResultsGrid.innerHTML = `
        <div style="grid-column: 1 / -1;" class="loading-indicator">
          <div class="spinner"></div> Checking live room availability...
        </div>
      `;

      const res = await fetchAPI(url);
      if (res.ok && res.data.success) {
        const availList = res.data.data;
        availabilityResultsHeading.textContent = `Available Rooms from ${checkIn} to ${checkOut} (${availList.length} found)`;

        if (availList.length === 0) {
          availabilityResultsGrid.innerHTML = `
            <div style="grid-column: 1 / -1;" class="empty-state">
              <div class="empty-state-icon">🏨</div>
              <div class="empty-state-text">No rooms are available for the selected dates and filters. Try another date range.</div>
            </div>
          `;
          return;
        }

        availabilityResultsGrid.innerHTML = availList.map(r => `
          <div class="avail-card">
            <div>
              <div class="avail-card-title">
                <h4>Room ${escapeHtml(r.room_number)}</h4>
                <span class="badge badge-available">Available</span>
              </div>
              <div style="color: var(--text-muted); font-size: 0.9rem;">Type: ${escapeHtml(r.room_type)}</div>
              <div class="avail-price">₹${r.price.toFixed(2)} <span>/ night</span></div>
            </div>
            <button class="btn btn-primary btn-sm btn-quick-book" style="margin-top: 1rem;"
              data-id="${r.id}"
              data-number="${escapeHtml(r.room_number)}"
              data-type="${escapeHtml(r.room_type)}"
              data-price="${r.price}"
              data-in="${checkIn}"
              data-out="${checkOut}">
              ⚡ Book Now
            </button>
          </div>
        `).join('');
      } else {
        availabilityResultsGrid.innerHTML = `
          <div style="grid-column: 1 / -1; color: var(--danger-text);" class="empty-state">
            ${escapeHtml(res.data.message || 'Error checking availability')}
          </div>
        `;
        showToast(res.data.message || 'Failed to search availability', 'error');
      }
    });
  }

  if (btnClearSearch) {
    btnClearSearch.addEventListener('click', () => {
      availabilityResultsContainer.style.display = 'none';
      availabilityResultsGrid.innerHTML = '';
    });
  }

  // --------------------------------------------------------------------------
  // Create Room Handler
  // --------------------------------------------------------------------------
  if (createRoomForm) {
    createRoomForm.addEventListener('submit', async (e) => {
      e.preventDefault();
      const roomNumber = document.getElementById('add-room-number').value.trim();
      const roomType = document.getElementById('add-room-type').value;
      const price = parseFloat(document.getElementById('add-room-price').value);
      const status = document.getElementById('add-room-status').value;

      if (!roomNumber) {
        showToast('Room number is required', 'error');
        return;
      }
      if (isNaN(price) || price <= 0) {
        showToast('Price must be greater than 0', 'error');
        return;
      }

      const submitBtn = document.getElementById('btn-submit-room');
      submitBtn.disabled = true;
      submitBtn.textContent = 'Adding...';

      const res = await fetchAPI('/api/rooms', {
        method: 'POST',
        body: JSON.stringify({
          room_number: roomNumber,
          room_type: roomType,
          price: price,
          availability_status: status
        })
      });

      submitBtn.disabled = false;
      submitBtn.textContent = 'Add Room';

      if (res.ok && res.data.success) {
        showToast(`Room ${roomNumber} created successfully!`, 'success');
        createRoomForm.reset();
        await loadRooms();
      } else {
        showToast(res.data.message || 'Failed to create room', 'error');
      }
    });
  }

  // --------------------------------------------------------------------------
  // Create Booking Handler
  // --------------------------------------------------------------------------
  if (createBookingForm) {
    createBookingForm.addEventListener('submit', async (e) => {
      e.preventDefault();
      const roomId = parseInt(bookingRoomSelect.value, 10);
      const guestName = document.getElementById('booking-guest-name').value.trim();
      const guestEmail = document.getElementById('booking-guest-email').value.trim();
      const checkIn = bookingCheckIn.value;
      const checkOut = bookingCheckOut.value;

      if (!roomId) {
        showToast('Please select a room', 'error');
        return;
      }
      if (!guestName) {
        showToast('Guest name is required', 'error');
        return;
      }
      if (!guestEmail || !validateEmail(guestEmail)) {
        showToast('Valid guest email is required', 'error');
        return;
      }
      if (!checkIn || !checkOut) {
        showToast('Check-in and check-out dates are required', 'error');
        return;
      }
      if (checkIn >= checkOut) {
        showToast('Check-in date must be strictly before check-out date', 'error');
        return;
      }

      const submitBtn = document.getElementById('btn-submit-booking');
      submitBtn.disabled = true;
      submitBtn.textContent = 'Processing Booking...';

      const res = await fetchAPI('/api/bookings', {
        method: 'POST',
        body: JSON.stringify({
          room_id: roomId,
          guest_name: guestName,
          guest_email: guestEmail,
          check_in: checkIn,
          check_out: checkOut
        })
      });

      submitBtn.disabled = false;
      submitBtn.textContent = 'Confirm & Book Room';

      if (res.ok && res.data.success) {
        showToast('Room booked successfully!', 'success');
        createBookingForm.reset();
        bookingCheckIn.value = today;
        bookingCheckOut.value = tomorrow;
        await refreshAllData();
        // If availability was open, refresh it as well
        if (availabilityResultsContainer.style.display !== 'none') {
          searchAvailabilityForm.dispatchEvent(new Event('submit'));
        }
      } else {
        showToast(res.data.message || 'Failed to book room', 'error');
      }
    });
  }

  // --------------------------------------------------------------------------
  // Edit & Delete Room Actions
  // --------------------------------------------------------------------------
  document.addEventListener('click', async (e) => {
    // Delete room
    if (e.target.closest('.btn-delete-room')) {
      const btn = e.target.closest('.btn-delete-room');
      const roomId = btn.dataset.id;
      const roomNum = btn.dataset.num;

      if (confirm(`Are you sure you want to delete Room ${roomNum}? This action cannot be undone.`)) {
        btn.disabled = true;
        const res = await fetchAPI(`/api/rooms/${roomId}`, { method: 'DELETE' });
        if (res.ok && res.data.success) {
          showToast(`Room ${roomNum} deleted successfully`, 'success');
          await loadRooms();
        } else {
          showToast(res.data.message || 'Could not delete room', 'error');
          btn.disabled = false;
        }
      }
    }

    // Open Edit room modal
    if (e.target.closest('.btn-edit-room')) {
      const btn = e.target.closest('.btn-edit-room');
      const roomId = parseInt(btn.dataset.id, 10);
      const room = rooms.find(r => r.id === roomId);
      if (room) {
        document.getElementById('edit-room-id').value = room.id;
        document.getElementById('edit-room-number').value = room.room_number;
        document.getElementById('edit-room-type').value = room.room_type;
        document.getElementById('edit-room-price').value = room.price;
        document.getElementById('edit-room-status').value = room.availability_status;
        editRoomModal.classList.add('active');
      }
    }

    // Cancel booking
    if (e.target.closest('.btn-cancel-booking')) {
      const btn = e.target.closest('.btn-cancel-booking');
      const bookingId = btn.dataset.id;

      if (confirm(`Cancel Booking #${bookingId}? This will free up the room for other guests.`)) {
        btn.disabled = true;
        const res = await fetchAPI(`/api/bookings/${bookingId}`, { method: 'DELETE' });
        if (res.ok && res.data.success) {
          showToast(`Booking #${bookingId} cancelled successfully`, 'success');
          await refreshAllData();
          // If availability search was visible, refresh it dynamically
          if (availabilityResultsContainer.style.display !== 'none') {
            searchAvailabilityForm.dispatchEvent(new Event('submit'));
          }
        } else {
          showToast(res.data.message || 'Failed to cancel booking', 'error');
          btn.disabled = false;
        }
      }
    }

    // Quick Book from Availability Search Card
    if (e.target.closest('.btn-quick-book')) {
      const btn = e.target.closest('.btn-quick-book');
      document.getElementById('quick-book-room-id').value = btn.dataset.id;
      document.getElementById('quick-book-room-display').value = `Room ${btn.dataset.number} (${btn.dataset.type}) - ₹${btn.dataset.price}/night`;
      document.getElementById('quick-check-in').value = btn.dataset.in;
      document.getElementById('quick-check-out').value = btn.dataset.out;
      quickBookModal.classList.add('active');
    }
  });

  // Modal Closers
  const btnCloseEditRoom = document.getElementById('btn-close-edit-room');
  const btnCancelEditRoom = document.getElementById('btn-cancel-edit-room');
  if (btnCloseEditRoom) btnCloseEditRoom.onclick = () => editRoomModal.classList.remove('active');
  if (btnCancelEditRoom) btnCancelEditRoom.onclick = () => editRoomModal.classList.remove('active');

  const btnCloseQuickBook = document.getElementById('btn-close-quick-book');
  const btnCancelQuickBook = document.getElementById('btn-cancel-quick-book');
  if (btnCloseQuickBook) btnCloseQuickBook.onclick = () => quickBookModal.classList.remove('active');
  if (btnCancelQuickBook) btnCancelQuickBook.onclick = () => quickBookModal.classList.remove('active');

  // Submit Edit Room
  if (editRoomForm) {
    editRoomForm.addEventListener('submit', async (e) => {
      e.preventDefault();
      const roomId = document.getElementById('edit-room-id').value;
      const roomNumber = document.getElementById('edit-room-number').value.trim();
      const roomType = document.getElementById('edit-room-type').value;
      const price = parseFloat(document.getElementById('edit-room-price').value);
      const status = document.getElementById('edit-room-status').value;

      if (!roomNumber) {
        showToast('Room number is required', 'error');
        return;
      }
      if (isNaN(price) || price <= 0) {
        showToast('Price must be greater than 0', 'error');
        return;
      }

      const res = await fetchAPI(`/api/rooms/${roomId}`, {
        method: 'PUT',
        body: JSON.stringify({
          room_number: roomNumber,
          room_type: roomType,
          price: price,
          availability_status: status
        })
      });

      if (res.ok && res.data.success) {
        showToast(`Room ${roomNumber} updated successfully`, 'success');
        editRoomModal.classList.remove('active');
        await loadRooms();
      } else {
        showToast(res.data.message || 'Failed to update room', 'error');
      }
    });
  }

  // Submit Quick Book Form
  if (quickBookForm) {
    quickBookForm.addEventListener('submit', async (e) => {
      e.preventDefault();
      const roomId = parseInt(document.getElementById('quick-book-room-id').value, 10);
      const guestName = document.getElementById('quick-guest-name').value.trim();
      const guestEmail = document.getElementById('quick-guest-email').value.trim();
      const checkIn = document.getElementById('quick-check-in').value;
      const checkOut = document.getElementById('quick-check-out').value;

      if (!guestName || !guestEmail || !checkIn || !checkOut) {
        showToast('Please fill all required fields', 'error');
        return;
      }
      if (!validateEmail(guestEmail)) {
        showToast('Please enter a valid email address', 'error');
        return;
      }
      if (checkIn >= checkOut) {
        showToast('Check-in date must be strictly before check-out date', 'error');
        return;
      }

      const res = await fetchAPI('/api/bookings', {
        method: 'POST',
        body: JSON.stringify({
          room_id: roomId,
          guest_name: guestName,
          guest_email: guestEmail,
          check_in: checkIn,
          check_out: checkOut
        })
      });

      if (res.ok && res.data.success) {
        showToast('Room booked successfully!', 'success');
        quickBookModal.classList.remove('active');
        quickBookForm.reset();
        await refreshAllData();
        // Refresh availability grid
        if (searchAvailabilityForm) {
          searchAvailabilityForm.dispatchEvent(new Event('submit'));
        }
      } else {
        showToast(res.data.message || 'Booking conflict or error', 'error');
      }
    });
  }

  // Filter input listeners
  if (filterRoomInput) {
    filterRoomInput.addEventListener('input', renderRoomsTable);
  }
  if (filterBookingStatus) {
    filterBookingStatus.addEventListener('change', renderBookingsTable);
  }
  if (btnRefreshAll) {
    btnRefreshAll.addEventListener('click', async () => {
      await refreshAllData();
      showToast('Data refreshed', 'info', 2000);
    });
  }
  if (btnOpenAddRoomModal) {
    btnOpenAddRoomModal.addEventListener('click', () => {
      const roomNumInput = document.getElementById('add-room-number');
      if (roomNumInput) {
        roomNumInput.scrollIntoView({ behavior: 'smooth', block: 'center' });
        roomNumInput.focus();
      }
    });
  }

  // Helper validation
  function validateEmail(email) {
    return /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email);
  }

  function escapeHtml(str) {
    if (!str) return '';
    return String(str)
      .replace(/&/g, '&amp;')
      .replace(/</g, '&lt;')
      .replace(/>/g, '&gt;')
      .replace(/"/g, '&quot;')
      .replace(/'/g, '&#039;');
  }

  // Initial load
  refreshAllData();
});
