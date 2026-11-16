let vocabItems = [];
let currentFilterImportant = false;
let currentModalItem = null;
let searchDebounceTimer = null;

function setImportantFilter(isImportant) {
    currentFilterImportant = isImportant;
    const tabAll = document.getElementById('tab-all');
    const tabImportant = document.getElementById('tab-important');

    if (isImportant) {
        tabImportant.className = 'px-4 py-2 text-xs font-bold rounded-lg transition-all shadow-xs bg-white text-amber-800 flex items-center space-x-1.5';
        tabAll.className = 'px-4 py-2 text-xs font-bold rounded-lg transition-all text-ink-500 hover:text-ink-900 flex items-center space-x-1.5';
    } else {
        tabAll.className = 'px-4 py-2 text-xs font-bold rounded-lg transition-all shadow-xs bg-white text-ink-900 flex items-center space-x-1.5';
        tabImportant.className = 'px-4 py-2 text-xs font-bold rounded-lg transition-all text-ink-500 hover:text-ink-900 flex items-center space-x-1.5';
    }
    loadVocabList();
}

function debounceVocabSearch() {
    clearTimeout(searchDebounceTimer);
    searchDebounceTimer = setTimeout(() => {
        loadVocabList();
    }, 250);
}

async function loadVocabList() {
    const query = document.getElementById('vocab-search-input')?.value.trim() || '';
    const lang = document.getElementById('vocab-lang-filter')?.value || 'all';
    const sortBy = document.getElementById('vocab-sort')?.value || 'recent';

    const params = new URLSearchParams({
        important: currentFilterImportant ? 'true' : 'false',
        sort_by: sortBy
    });
    if (query) params.append('query', query);
    if (lang && lang !== 'all') params.append('lang', lang);

    try {
        const res = await fetch(`/api/vocab?${params.toString()}`);
        if (!res.ok) throw new Error('Could not load vocabulary.');

        const data = await res.json();
        vocabItems = data.items || [];
        updateStatsUI(data.stats);
        renderVocabGrid(vocabItems);
    } catch (e) {
        showToast('Error loading vocabulary', 'error');
    }
}

function updateStatsUI(stats) {
    if (!stats) return;
    const totalEl = document.getElementById('stat-total');
    const importantEl = document.getElementById('stat-important');
    const tabAllCount = document.getElementById('tab-all-count');
    const tabImpCount = document.getElementById('tab-important-count');

    if (totalEl) totalEl.textContent = stats.total_words || 0;
    if (importantEl) importantEl.textContent = stats.important_words || 0;
    if (tabAllCount) tabAllCount.textContent = stats.total_words || 0;
    if (tabImpCount) tabImpCount.textContent = stats.important_words || 0;

    // Update language filter options
    const langSelect = document.getElementById('vocab-lang-filter');
    if (langSelect && stats.languages) {
        const currentVal = langSelect.value;
        let optionsHtml = '<option value="all">All Languages</option>';
        stats.languages.forEach(l => {
            optionsHtml += `<option value="${l}" ${currentVal === l ? 'selected' : ''}>${l}</option>`;
        });
        langSelect.innerHTML = optionsHtml;
    }
    updateNavBadge();
}

function renderVocabGrid(items) {
    const grid = document.getElementById('vocab-grid');
    const emptyState = document.getElementById('vocab-empty');

    if (items.length === 0) {
        grid.innerHTML = '';
        emptyState.classList.remove('hidden');
        lucide.createIcons({ root: emptyState });
        return;
    }

    emptyState.classList.add('hidden');
    grid.innerHTML = items.map(item => {
        const word = item.word || item.clean_word;
        const meanings = item.meanings || [];
        const firstPos = meanings.length > 0 ? meanings[0].part_of_speech : 'term';
        const firstDef = meanings.length > 0 && meanings[0].definitions ? meanings[0].definitions[0] : '';
        const isImp = item.is_important;

        return `
            <div class="bg-white rounded-2xl p-5 border border-[#E7E2D8] shadow-xs hover:border-cognac-600/50 transition-all duration-200 flex flex-col justify-between group">
                <div>
                    <!-- Header -->
                    <div class="flex items-start justify-between gap-2 mb-2">
                        <div class="cursor-pointer" onclick="openModal('${item.id}')">
                            <h3 class="text-xl font-bold font-serif-title text-ink-900 capitalize group-hover:text-cognac-700 transition">
                                ${word}
                            </h3>
                            ${item.phonetic ? `<span class="text-xs font-mono text-cognac-700">${item.phonetic}</span>` : ''}
                        </div>
                        <button 
                            onclick="toggleCardStar(event, '${item.id}')"
                            class="p-2 rounded-xl transition ${isImp ? 'bg-amber-50 text-amber-700' : 'text-stone-300 hover:text-amber-700 hover:bg-stone-50'}"
                            title="${isImp ? 'Bookmarked' : 'Bookmark'}"
                        >
                            <i data-lucide="bookmark" class="w-4 h-4 ${isImp ? 'fill-amber-600 text-amber-600' : ''}"></i>
                        </button>
                    </div>

                    <!-- Translation banner -->
                    <div class="mb-3 px-3 py-2 rounded-xl bg-[#FAF7F2] border border-[#E7E2D8] flex items-center justify-between">
                        <div class="text-sm font-serif font-bold text-ink-900 truncate">${item.translation}</div>
                        <span class="text-[9px] font-bold px-2 py-0.5 rounded-md bg-white border border-[#E7E2D8] text-ink-600 uppercase tracking-widest">
                            ${item.target_lang}
                        </span>
                    </div>

                    <!-- Snippet Definition -->
                    ${firstDef ? `
                        <p class="text-xs text-ink-500 line-clamp-2 leading-relaxed mb-4 font-sans">
                            <span class="font-serif italic font-bold text-ink-700">${firstPos}:</span> ${firstDef}
                        </p>
                    ` : ''}
                </div>

                <!-- Footer buttons -->
                <div class="pt-3 border-t border-[#E7E2D8] flex items-center justify-between text-xs text-ink-400">
                    <span>Looked up: <strong>${item.search_count}x</strong></span>
                    <div class="flex items-center space-x-1.5">
                        <button 
                            onclick="deleteCardWord(event, '${item.id}', '${word.replace(/'/g, "\\'")}')" 
                            class="p-1.5 rounded-lg text-ink-400 hover:text-rose-700 hover:bg-rose-50 border border-transparent hover:border-rose-200 transition"
                            title="Delete word"
                        >
                            <i data-lucide="trash-2" class="w-4 h-4"></i>
                        </button>
                        <button onclick="openModal('${item.id}')" class="px-2.5 py-1.5 rounded-lg bg-[#FAF7F2] hover:bg-ink-900 hover:text-white border border-[#E7E2D8] text-ink-700 font-semibold transition flex items-center space-x-1">
                            <span>Details</span>
                            <i data-lucide="chevron-right" class="w-3.5 h-3.5"></i>
                        </button>
                    </div>
                </div>
            </div>
        `;
    }).join('');

    lucide.createIcons({ root: grid });
}

async function toggleCardStar(e, vocabId) {
    e.stopPropagation();
    try {
        const res = await fetch(`/api/vocab/${vocabId}/important`, { method: 'PATCH' });
        if (res.ok) {
            const data = await res.json();
            showToast(data.is_important ? 'Bookmarked as Important' : 'Removed from Bookmarks', 'info');
            loadVocabList();
        }
    } catch (err) {
        showToast('Could not update status', 'error');
    }
}

async function deleteCardWord(e, vocabId, wordName) {
    e.stopPropagation();
    if (!confirm(`Are you sure you want to delete "${wordName}" from your vocabulary?`)) {
        return;
    }
    try {
        const res = await fetch(`/api/vocab/${vocabId}`, { method: 'DELETE' });
        if (res.ok) {
            showToast(`Deleted "${wordName}" from vocabulary`, 'info');
            loadVocabList();
        } else {
            showToast('Error deleting word', 'error');
        }
    } catch (err) {
        showToast('Error deleting word', 'error');
    }
}

// Modal Logic
async function openModal(vocabId) {
    try {
        const res = await fetch(`/api/vocab/${vocabId}`);
        if (!res.ok) throw new Error('Word not found');
        currentModalItem = await res.json();

        // Populate fields
        document.getElementById('modal-word').textContent = currentModalItem.word || currentModalItem.clean_word;
        document.getElementById('modal-phonetic').textContent = currentModalItem.phonetic || '';
        document.getElementById('modal-source-lang').textContent = currentModalItem.source_lang || 'Source';
        document.getElementById('modal-target-lang').textContent = currentModalItem.target_lang || 'Target';
        document.getElementById('modal-translation').textContent = currentModalItem.translation || '';
        document.getElementById('modal-search-count').textContent = `Looked up ${currentModalItem.search_count} time(s)`;
        document.getElementById('modal-date').textContent = `Preserved: ${new Date(currentModalItem.created_at).toLocaleDateString()}`;
        document.getElementById('modal-notes').value = currentModalItem.notes || '';

        // Star button state
        updateModalStarIcon(currentModalItem.is_important);

        // Explanation
        const expContainer = document.getElementById('modal-explanation-container');
        const expText = document.getElementById('modal-explanation');
        if (currentModalItem.explanation) {
            expText.textContent = currentModalItem.explanation;
            expContainer.classList.remove('hidden');
        } else {
            expContainer.classList.add('hidden');
        }

        // Meanings
        const meaningsContainer = document.getElementById('modal-meanings');
        const meanings = currentModalItem.meanings || [];
        if (meanings.length > 0) {
            meaningsContainer.innerHTML = meanings.map(m => `
                <div class="p-4 rounded-xl bg-[#FAF7F2] border border-[#E7E2D8] space-y-1.5">
                    <span class="inline-block text-xs font-serif italic font-bold text-ink-800">
                        ${m.part_of_speech || 'Definition'}
                    </span>
                    <ul class="space-y-1 pl-1">
                        ${(m.definitions || []).map(d => `
                            <li class="text-xs text-ink-800 leading-relaxed">• ${d}</li>
                        `).join('')}
                    </ul>
                    ${(m.examples && m.examples.length > 0) ? `
                        <div class="pt-1.5 space-y-1">
                            ${m.examples.map(ex => `
                                <p class="text-xs text-ink-500 font-serif italic pl-2 border-l border-cognac-600/40">"${ex}"</p>
                            `).join('')}
                        </div>
                    ` : ''}
                </div>
            `).join('');
        } else {
            meaningsContainer.innerHTML = `<p class="text-xs text-ink-500">No definitions listed.</p>`;
        }

        // Synonyms
        const synContainer = document.getElementById('modal-synonyms');
        const synSection = document.getElementById('modal-synonyms-section');
        const synonyms = currentModalItem.synonyms || [];
        if (synonyms.length > 0) {
            synSection.classList.remove('hidden');
            synContainer.innerHTML = synonyms.map(s => `
                <a href="/?search=${encodeURIComponent(s)}" class="px-2.5 py-1 rounded-lg text-xs font-medium bg-[#FAF7F2] text-ink-800 border border-[#E7E2D8] hover:border-cognac-600 transition">
                    ${s}
                </a>
            `).join('');
        } else {
            synSection.classList.add('hidden');
        }

        // Antonyms
        const antContainer = document.getElementById('modal-antonyms');
        const antSection = document.getElementById('modal-antonyms-section');
        const antonyms = currentModalItem.antonyms || [];
        if (antonyms.length > 0) {
            antSection.classList.remove('hidden');
            antContainer.innerHTML = antonyms.map(a => `
                <a href="/?search=${encodeURIComponent(a)}" class="px-2.5 py-1 rounded-lg text-xs font-medium bg-[#FAF7F2] text-ink-800 border border-[#E7E2D8] hover:border-rose-400 transition">
                    ${a}
                </a>
            `).join('');
        } else {
            antSection.classList.add('hidden');
        }

        document.getElementById('vocab-modal').classList.remove('hidden');
        lucide.createIcons({ root: document.getElementById('vocab-modal') });
    } catch (e) {
        showToast('Error opening word details', 'error');
    }
}

function updateModalStarIcon(isImportant) {
    const btn = document.getElementById('modal-star-btn');
    const icon = document.getElementById('modal-star-icon');
    if (isImportant) {
        btn.className = 'p-2 rounded-xl border border-amber-300 bg-amber-50 text-amber-800 transition shadow-xs';
        icon.classList.add('fill-amber-600', 'text-amber-600');
    } else {
        btn.className = 'p-2 rounded-xl border border-[#E7E2D8] bg-white hover:bg-amber-50 text-ink-400 hover:text-amber-800 transition shadow-xs';
        icon.classList.remove('fill-amber-600', 'text-amber-600');
    }
}

async function toggleModalStar() {
    if (!currentModalItem) return;
    try {
        const res = await fetch(`/api/vocab/${currentModalItem.id}/important`, { method: 'PATCH' });
        const data = await res.json();
        if (res.ok) {
            currentModalItem.is_important = data.is_important;
            updateModalStarIcon(data.is_important);
            showToast(data.is_important ? 'Bookmarked as Important' : 'Removed from Bookmarks', 'info');
            loadVocabList();
        }
    } catch (e) {
        showToast('Error toggling bookmark', 'error');
    }
}

function speakModalWord() {
    if (currentModalItem) {
        speakText(currentModalItem.word || currentModalItem.clean_word);
    }
}

async function saveModalNotes() {
    if (!currentModalItem) return;
    const notes = document.getElementById('modal-notes').value;
    const status = document.getElementById('notes-status');
    try {
        const res = await fetch(`/api/vocab/${currentModalItem.id}/notes`, {
            method: 'PATCH',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ notes })
        });
        if (res.ok) {
            currentModalItem.notes = notes;
            status.classList.remove('hidden');
            setTimeout(() => status.classList.add('hidden'), 2000);
            showToast('Notes saved successfully!', 'success');
        }
    } catch (e) {
        showToast('Could not save notes', 'error');
    }
}

async function deleteCurrentModalWord() {
    if (!currentModalItem) return;
    if (!confirm(`Are you sure you want to delete "${currentModalItem.word}" from your vocabulary?`)) {
        return;
    }
    try {
        const res = await fetch(`/api/vocab/${currentModalItem.id}`, { method: 'DELETE' });
        if (res.ok) {
            showToast('Word deleted from vocabulary', 'info');
            closeModal();
            loadVocabList();
        }
    } catch (e) {
        showToast('Error deleting word', 'error');
    }
}

function closeModal() {
    document.getElementById('vocab-modal').classList.add('hidden');
    currentModalItem = null;
}

// Close on escape key
document.addEventListener('keydown', (e) => {
    if (e.key === 'Escape') closeModal();
});

document.addEventListener('DOMContentLoaded', () => {
    loadVocabList();
});
