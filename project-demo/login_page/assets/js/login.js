/**
 * Login Page - Vanilla JavaScript
 *
 * Handles form validation, password toggle, and submission.
 * Uses modern ES6+ syntax with async/await pattern.
 */

// ===== DOM Element References =====
const form = document.getElementById('loginForm');
const usernameInput = document.getElementById('username');
const passwordInput = document.getElementById('password');
const togglePasswordBtn = document.getElementById('togglePassword');
const submitBtn = document.getElementById('submitBtn');
const errorAlert = document.querySelector('.login-card__alert--error');
const successAlert = document.querySelector('.login-card__alert--success');

// ===== Utility Functions =====

/**
 * Show alert message
 * @param {HTMLElement} alertElement - Alert element to show
 * @param {string} message - Message text
 */
const showAlert = (alertElement, message) => {
    const icon = alertElement.querySelector('.login-card__alert-icon');
    const text = alertElement.querySelector('.login-card__alert-text');

    icon.textContent = alertElement.classList.contains('login-card__alert--error')
        ? '⚠️'
        : '✅';
    text.textContent = message;
    alertElement.hidden = false;

    // Auto-hide after 4 seconds
    setTimeout(() => {
        hideAlert(alertElement);
    }, 4000);
};

/**
 * Hide alert element
 * @param {HTMLElement} alertElement - Alert element to hide
 */
const hideAlert = (alertElement) => {
    alertElement.hidden = true;
};

/**
 * Validate form inputs
 * @returns {Object} - Validation result with isValid and errors
 */
const validateForm = () => {
    const errors = [];
    const username = usernameInput.value.trim();
    const password = passwordInput.value.trim();

    if (!username) {
        errors.push('请输入用户名或邮箱');
    }

    if (!password) {
        errors.push('请输入密码');
    } else if (password.length < 6) {
        errors.push('密码长度不能少于6位');
    }

    return {
        isValid: errors.length === 0,
        errors
    };
};

/**
 * Set loading state on form submission
 * @param {boolean} isLoading - Whether form is loading
 */
const setLoadingState = (isLoading) => {
    if (isLoading) {
        submitBtn.classList.add('is-loading');
        submitBtn.disabled = true;
    } else {
        submitBtn.classList.remove('is-loading');
        submitBtn.disabled = false;
    }
};

// ===== Event Handlers =====

/**
 * Toggle password visibility
 * @param {Event} e - Click event
 */
const handleTogglePassword = (e) => {
    const isPasswordVisible = passwordInput.type === 'text';
    const eyeIcon = togglePasswordBtn.querySelector('.login-form__toggle-icon');

    if (isPasswordVisible) {
        passwordInput.type = 'password';
        // Eye closed icon (default)
        eyeIcon.innerHTML = `
            <path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z"></path>
            <circle cx="12" cy="12" r="3"></circle>
        `;
        togglePasswordBtn.setAttribute('aria-label', '显示密码');
    } else {
        passwordInput.type = 'text';
        // Eye open icon (slashed)
        eyeIcon.innerHTML = `
            <path d="M17.94 17.94A10.07 10.07 0 0 1 12 20c-7 0-11-8-11-8a18.45 18.45 0 0 1 5.06-5.94M9.9 4.24A9.12 9.12 0 0 1 12 4c7 0 11 8 11 8a18.5 18.5 0 0 1-2.16 3.19m-6.72-1.07a3 3 0 1 1-4.24-4.24"></path>
            <line x1="1" y1="1" x2="23" y2="23"></line>
        `;
        togglePasswordBtn.setAttribute('aria-label', '隐藏密码');
    }
};

/**
 * Handle form submission
 * @param {Event} e - Submit event
 */
const handleSubmit = async (e) => {
    e.preventDefault();

    // Clear previous alerts
    hideAlert(errorAlert);
    hideAlert(successAlert);

    // Validate form
    const validation = validateForm();
    if (!validation.isValid) {
        showAlert(errorAlert, validation.errors[0]);
        // Focus first invalid field
        if (!usernameInput.value.trim()) {
            usernameInput.focus();
        } else if (!passwordInput.value.trim() || passwordInput.value.length < 6) {
            passwordInput.focus();
        }
        return;
    }

    // Collect form data
    const formData = {
        username: usernameInput.value.trim(),
        password: passwordInput.value.trim(),
        remember: document.getElementById('remember').checked
    };

    console.log('Login attempt:', formData);

    // Set loading state
    setLoadingState(true);

    try {
        // Replace this URL with your actual backend endpoint
        // Example: const response = await fetch('/api/login', { ... });

        // Simulate network delay for demonstration
        await new Promise(resolve => setTimeout(resolve, 1500));

        // Mock successful login (replace with real authentication logic)
        if (formData.username && formData.password) {
            showAlert(successAlert, '登录成功！正在跳转...');

            // Redirect after success
            setTimeout(() => {
                // window.location.href = '/dashboard';
                console.log('Redirecting to dashboard...');
            }, 1000);
        }
    } catch (error) {
        console.error('Login failed:', error);
        showAlert(errorAlert, '登录失败，请稍后重试');
    } finally {
        // Reset loading state
        setLoadingState(false);
    }
};

// ===== Event Listeners =====

togglePasswordBtn.addEventListener('click', handleTogglePassword);
form.addEventListener('submit', handleSubmit);

// Log initialization
console.log('Login page initialized');
