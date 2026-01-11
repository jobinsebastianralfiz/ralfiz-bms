/**
 * Ralfiz BMS - JavaScript Application
 */

// ==================== Sidebar Toggle ====================
const sidebar = document.getElementById('sidebar');
const sidebarToggle = document.getElementById('sidebarToggle');

if (sidebarToggle) {
  sidebarToggle.addEventListener('click', () => {
    sidebar.classList.toggle('show');
  });

  // Close sidebar when clicking outside on mobile
  document.addEventListener('click', (e) => {
    if (window.innerWidth <= 1024) {
      if (!sidebar.contains(e.target) && !sidebarToggle.contains(e.target)) {
        sidebar.classList.remove('show');
      }
    }
  });
}

// ==================== Dropdown Toggle ====================
document.querySelectorAll('.dropdown').forEach(dropdown => {
  const toggle = dropdown.querySelector('[id$="Dropdown"], .dropdown-toggle, .user-dropdown-toggle');

  if (toggle) {
    toggle.addEventListener('click', (e) => {
      e.stopPropagation();

      // Close other dropdowns
      document.querySelectorAll('.dropdown.open').forEach(d => {
        if (d !== dropdown) d.classList.remove('open');
      });

      dropdown.classList.toggle('open');
    });
  }
});

// Close dropdowns when clicking outside
document.addEventListener('click', () => {
  document.querySelectorAll('.dropdown.open').forEach(d => {
    d.classList.remove('open');
  });
});

// ==================== Modal Functions ====================
function openModal(modalId) {
  const modal = document.getElementById(modalId);
  if (modal) {
    modal.classList.add('show');
    document.body.style.overflow = 'hidden';
  }
}

function closeModal(modalId) {
  const modal = document.getElementById(modalId);
  if (modal) {
    modal.classList.remove('show');
    document.body.style.overflow = '';
  }
}

// Close modal when clicking backdrop
document.querySelectorAll('.modal-backdrop').forEach(backdrop => {
  backdrop.addEventListener('click', (e) => {
    if (e.target === backdrop) {
      backdrop.classList.remove('show');
      document.body.style.overflow = '';
    }
  });
});

// Close modal with Escape key
document.addEventListener('keydown', (e) => {
  if (e.key === 'Escape') {
    document.querySelectorAll('.modal-backdrop.show').forEach(modal => {
      modal.classList.remove('show');
      document.body.style.overflow = '';
    });
  }
});

// ==================== Toast Notifications ====================
function showToast(message, type = 'success') {
  const container = document.getElementById('toastContainer');
  if (!container) return;

  const toast = document.createElement('div');
  toast.className = `toast ${type}`;
  toast.innerHTML = `
    <i class="fas fa-${type === 'success' ? 'check-circle' : type === 'danger' ? 'times-circle' : type === 'warning' ? 'exclamation-circle' : 'info-circle'}"></i>
    <span>${message}</span>
    <button class="btn btn-ghost btn-sm btn-icon" onclick="this.parentElement.remove()" style="margin-left: auto;">
      <i class="fas fa-times"></i>
    </button>
  `;

  container.appendChild(toast);

  // Auto remove after 5 seconds
  setTimeout(() => {
    toast.style.animation = 'slideIn 0.3s ease reverse';
    setTimeout(() => toast.remove(), 300);
  }, 5000);
}

// ==================== Password Toggle ====================
function togglePasswordVisibility(inputId, iconId) {
  const input = document.getElementById(inputId);
  const icon = document.getElementById(iconId);

  if (input.type === 'password') {
    input.type = 'text';
    icon.classList.remove('fa-eye');
    icon.classList.add('fa-eye-slash');
  } else {
    input.type = 'password';
    icon.classList.remove('fa-eye-slash');
    icon.classList.add('fa-eye');
  }
}

// ==================== Copy to Clipboard ====================
function copyToClipboard(text, button) {
  navigator.clipboard.writeText(text).then(() => {
    const originalIcon = button.innerHTML;
    button.innerHTML = '<i class="fas fa-check"></i>';
    button.classList.add('text-success');

    setTimeout(() => {
      button.innerHTML = originalIcon;
      button.classList.remove('text-success');
    }, 2000);

    showToast('Copied to clipboard!', 'success');
  });
}

// ==================== Dynamic Line Items ====================
let lineItemCounter = 0;

function addLineItem(tableBodyId) {
  const tbody = document.getElementById(tableBodyId);
  if (!tbody) return;

  lineItemCounter++;

  const row = document.createElement('tr');
  row.id = `lineItem${lineItemCounter}`;
  row.innerHTML = `
    <td>
      <input type="text" class="form-control" placeholder="Item description" name="items[${lineItemCounter}][description]">
    </td>
    <td style="width: 100px;">
      <input type="number" class="form-control text-right" value="1" min="1" name="items[${lineItemCounter}][quantity]" onchange="calculateLineTotal(${lineItemCounter})">
    </td>
    <td style="width: 150px;">
      <input type="number" class="form-control text-right" placeholder="0.00" name="items[${lineItemCounter}][price]" onchange="calculateLineTotal(${lineItemCounter})">
    </td>
    <td style="width: 150px;">
      <input type="text" class="form-control text-right" readonly value="0.00" id="lineTotal${lineItemCounter}">
    </td>
    <td style="width: 50px;">
      <button type="button" class="btn btn-ghost btn-sm btn-icon text-danger" onclick="removeLineItem(${lineItemCounter})">
        <i class="fas fa-trash"></i>
      </button>
    </td>
  `;

  tbody.appendChild(row);
}

function removeLineItem(id) {
  const row = document.getElementById(`lineItem${id}`);
  if (row) {
    row.remove();
    calculateTotals();
  }
}

function calculateLineTotal(id) {
  const row = document.getElementById(`lineItem${id}`);
  if (!row) return;

  const quantity = parseFloat(row.querySelector('[name$="[quantity]"]').value) || 0;
  const price = parseFloat(row.querySelector('[name$="[price]"]').value) || 0;
  const total = quantity * price;

  document.getElementById(`lineTotal${id}`).value = formatNumber(total);
  calculateTotals();
}

function calculateTotals() {
  const lineTotals = document.querySelectorAll('[id^="lineTotal"]');
  let subtotal = 0;

  lineTotals.forEach(input => {
    subtotal += parseFloat(input.value.replace(/,/g, '')) || 0;
  });

  const discount = parseFloat(document.getElementById('discount')?.value) || 0;
  const taxRate = parseFloat(document.getElementById('taxRate')?.value) || 18;

  const discountedAmount = subtotal - discount;
  const taxAmount = discountedAmount * (taxRate / 100);
  const total = discountedAmount + taxAmount;

  if (document.getElementById('subtotal')) {
    document.getElementById('subtotal').textContent = formatCurrency(subtotal);
  }
  if (document.getElementById('taxAmount')) {
    document.getElementById('taxAmount').textContent = formatCurrency(taxAmount);
  }
  if (document.getElementById('totalAmount')) {
    document.getElementById('totalAmount').textContent = formatCurrency(total);
  }
}

// ==================== Formatting Helpers ====================
function formatNumber(num) {
  return num.toLocaleString('en-IN', { minimumFractionDigits: 2, maximumFractionDigits: 2 });
}

function formatCurrency(num) {
  return '₹' + formatNumber(num);
}

// ==================== Form Validation ====================
function validateForm(formId) {
  const form = document.getElementById(formId);
  if (!form) return false;

  let isValid = true;

  // Remove previous error states
  form.querySelectorAll('.is-invalid').forEach(el => {
    el.classList.remove('is-invalid');
  });
  form.querySelectorAll('.form-error').forEach(el => {
    el.remove();
  });

  // Check required fields
  form.querySelectorAll('[required]').forEach(field => {
    if (!field.value.trim()) {
      isValid = false;
      field.classList.add('is-invalid');

      const error = document.createElement('div');
      error.className = 'form-text form-error';
      error.textContent = 'This field is required';
      field.parentNode.appendChild(error);
    }
  });

  // Check email fields
  form.querySelectorAll('input[type="email"]').forEach(field => {
    if (field.value && !isValidEmail(field.value)) {
      isValid = false;
      field.classList.add('is-invalid');

      const error = document.createElement('div');
      error.className = 'form-text form-error';
      error.textContent = 'Please enter a valid email address';
      field.parentNode.appendChild(error);
    }
  });

  return isValid;
}

function isValidEmail(email) {
  return /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email);
}

// ==================== Confirm Delete ====================
function confirmDelete(itemName, callback) {
  if (confirm(`Are you sure you want to delete "${itemName}"? This action cannot be undone.`)) {
    if (callback) callback();
  }
}

// ==================== Table Row Selection ====================
function toggleSelectAll(checkbox, tableId) {
  const table = document.getElementById(tableId);
  if (!table) return;

  const checkboxes = table.querySelectorAll('tbody input[type="checkbox"]');
  checkboxes.forEach(cb => {
    cb.checked = checkbox.checked;
  });

  updateBulkActions(tableId);
}

function updateBulkActions(tableId) {
  const table = document.getElementById(tableId);
  if (!table) return;

  const checked = table.querySelectorAll('tbody input[type="checkbox"]:checked');
  const bulkActions = document.getElementById('bulkActions');
  const selectedCount = document.getElementById('selectedCount');

  if (bulkActions) {
    if (checked.length > 0) {
      bulkActions.classList.remove('d-none');
      if (selectedCount) {
        selectedCount.textContent = checked.length;
      }
    } else {
      bulkActions.classList.add('d-none');
    }
  }
}

// ==================== Search & Filter ====================
function filterTable(searchInputId, tableId) {
  const searchInput = document.getElementById(searchInputId);
  const table = document.getElementById(tableId);

  if (!searchInput || !table) return;

  const searchTerm = searchInput.value.toLowerCase();
  const rows = table.querySelectorAll('tbody tr');

  rows.forEach(row => {
    const text = row.textContent.toLowerCase();
    row.style.display = text.includes(searchTerm) ? '' : 'none';
  });
}

// ==================== Tab Switching ====================
function switchTab(tabId) {
  // Update tab buttons
  document.querySelectorAll('.tab-item').forEach(tab => {
    tab.classList.remove('active');
  });
  document.querySelector(`[data-tab="${tabId}"]`)?.classList.add('active');

  // Update tab content
  document.querySelectorAll('.tab-content').forEach(content => {
    content.classList.add('d-none');
  });
  document.getElementById(tabId)?.classList.remove('d-none');
}

// ==================== Initialize ====================
document.addEventListener('DOMContentLoaded', () => {
  // Add any initialization code here
  console.log('Ralfiz BMS initialized');
});
