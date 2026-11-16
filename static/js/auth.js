let currentTab = 'login';

function switchAuthTab(tab) {
    currentTab = tab;
    const tabLogin = document.getElementById('tab-login');
    const tabRegister = document.getElementById('tab-register');
    const title = document.getElementById('auth-title');
    const subtitle = document.getElementById('auth-subtitle');
    const submitText = document.getElementById('auth-submit-text');
    const passwordHint = document.getElementById('password-hint');
    const errorBox = document.getElementById('auth-error');

    errorBox.classList.add('hidden');

    if (tab === 'login') {
        tabLogin.className = 'flex-1 py-2 text-sm font-semibold rounded-lg transition-all shadow-sm bg-white text-indigo-600';
        tabRegister.className = 'flex-1 py-2 text-sm font-semibold rounded-lg transition-all text-slate-500 hover:text-slate-800';
        title.textContent = 'Welcome Back';
        subtitle.textContent = 'Sign in to access your private vocabulary library';
        submitText.textContent = 'Sign In';
        passwordHint.classList.add('hidden');
    } else {
        tabRegister.className = 'flex-1 py-2 text-sm font-semibold rounded-lg transition-all shadow-sm bg-white text-indigo-600';
        tabLogin.className = 'flex-1 py-2 text-sm font-semibold rounded-lg transition-all text-slate-500 hover:text-slate-800';
        title.textContent = 'Create an Account';
        subtitle.textContent = 'Keep your searched words, meanings & translations private';
        submitText.textContent = 'Create Account';
        passwordHint.classList.remove('hidden');
    }
}

async function handleAuthSubmit(e) {
    e.preventDefault();
    const email = document.getElementById('email').value.trim();
    const password = document.getElementById('password').value;
    const submitBtn = document.getElementById('auth-submit-btn');
    const errorBox = document.getElementById('auth-error');
    const errorMsg = document.getElementById('auth-error-msg');

    errorBox.classList.add('hidden');
    submitBtn.disabled = true;
    submitBtn.classList.add('opacity-70');

    const endpoint = currentTab === 'login' ? '/api/auth/login' : '/api/auth/register';

    try {
        const res = await fetch(endpoint, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ email, password })
        });

        const data = await res.json();
        if (!res.ok) {
            throw new Error(data.detail || 'Authentication failed. Please try again.');
        }

        // Successfully logged in / registered
        showToast(currentTab === 'login' ? 'Logged in successfully!' : 'Account created!', 'success');
        setTimeout(() => {
            window.location.href = '/';
        }, 500);
    } catch (err) {
        errorMsg.textContent = err.message;
        errorBox.classList.remove('hidden');
        lucide.createIcons({ root: errorBox });
    } finally {
        submitBtn.disabled = false;
        submitBtn.classList.remove('opacity-70');
    }
}

// Check URL params on load (e.g., ?tab=register)
document.addEventListener('DOMContentLoaded', () => {
    const urlParams = new URLSearchParams(window.location.search);
    if (urlParams.get('tab') === 'register') {
        switchAuthTab('register');
    }
});
