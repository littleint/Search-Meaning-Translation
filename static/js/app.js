// Toast Notifications with Oxford Editorial styling
function showToast(message, type = 'info') {
    const container = document.getElementById('toast-container');
    if (!container) return;

    const toast = document.createElement('div');
    toast.className = `pointer-events-auto flex items-center space-x-2 px-4 py-3 rounded-2xl shadow-md border text-xs font-semibold tracking-wide transition-all duration-300 transform translate-y-2 opacity-0 ${
        type === 'success' ? 'bg-[#1C1917] text-[#FAF7F2] border-stone-800 shadow-stone-900/10' :
        type === 'error' ? 'bg-rose-900 text-rose-50 border-rose-800 shadow-rose-900/10' :
        'bg-[#FAF7F2] text-stone-900 border-[#E7E2D8] shadow-stone-900/10'
    }`;

    const iconName = type === 'success' ? 'check' : type === 'error' ? 'alert-circle' : 'info';
    toast.innerHTML = `
        <i data-lucide="${iconName}" class="w-4 h-4 flex-shrink-0 ${type === 'success' ? 'text-amber-400' : ''}"></i>
        <span>${message}</span>
    `;

    container.appendChild(toast);
    lucide.createIcons({ root: toast });

    // Animate in
    setTimeout(() => {
        toast.classList.remove('translate-y-2', 'opacity-0');
    }, 10);

    // Auto remove
    setTimeout(() => {
        toast.classList.add('opacity-0', 'translate-y-2');
        setTimeout(() => toast.remove(), 300);
    }, 3200);
}

// Pronounce text using Web Speech API
function speakText(text, lang = 'en-US') {
    if (!('speechSynthesis' in window)) {
        showToast('Audio pronunciation not supported in this browser.', 'error');
        return;
    }
    window.speechSynthesis.cancel();
    const utterance = new SpeechSynthesisUtterance(text);
    utterance.rate = 0.85;
    window.speechSynthesis.speak(utterance);
}

// Fetch & Update Navbar Count
async function updateNavBadge() {
    const badge = document.getElementById('nav-vocab-badge');
    if (!badge) return;
    try {
        const res = await fetch('/api/auth/me');
        if (res.ok) {
            const data = await res.json();
            const total = data.stats?.total_words || 0;
            badge.textContent = total;
        }
    } catch (e) {
        // ignore
    }
}

// Logout handler
async function handleLogout() {
    try {
        const res = await fetch('/api/auth/logout', { method: 'POST' });
        if (res.ok) {
            window.location.href = '/login';
        }
    } catch (e) {
        showToast('Error signing out', 'error');
    }
}

document.addEventListener('DOMContentLoaded', () => {
    updateNavBadge();
});
