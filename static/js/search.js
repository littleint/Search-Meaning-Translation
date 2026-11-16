let currentResult = null;

function swapLanguages() {
    const src = document.getElementById('source-lang');
    const tgt = document.getElementById('target-lang');
    if (src.value === 'auto') {
        showToast('Cannot swap with Auto-Detect as target language.', 'info');
        return;
    }
    const temp = src.value;
    src.value = tgt.value;
    tgt.value = temp;
}

function quickSearch(word, src = 'auto', tgt = null) {
    document.getElementById('search-input').value = word;
    if (src) document.getElementById('source-lang').value = src;
    if (tgt) document.getElementById('target-lang').value = tgt;
    executeSearch(word);
}

async function handleSearch(e) {
    e.preventDefault();
    const query = document.getElementById('search-input').value.trim();
    if (!query) return;
    executeSearch(query);
}

async function executeSearch(query) {
    const srcLang = document.getElementById('source-lang').value;
    const tgtLang = document.getElementById('target-lang').value;
    const loading = document.getElementById('search-loading');
    const container = document.getElementById('result-container');
    const searchBtn = document.getElementById('search-btn');

    loading.classList.remove('hidden');
    container.classList.add('hidden');
    searchBtn.disabled = true;

    try {
        const res = await fetch('/api/lookup', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                query: query,
                source_lang: srcLang,
                target_lang: tgtLang
            })
        });

        const json = await res.json();
        if (!res.ok) {
            throw new Error(json.detail || 'Could not fetch word details.');
        }

        currentResult = json.data;
        renderResult(currentResult);
        updateNavBadge();
        showToast(`Preserved "${currentResult.clean_word || currentResult.word}" in your collection.`, 'success');
    } catch (err) {
        showToast(err.message, 'error');
    } finally {
        loading.classList.add('hidden');
        searchBtn.disabled = false;
    }
}

function renderResult(data) {
    const container = document.getElementById('result-container');
    const word = data.word || data.clean_word;
    const phonetic = data.phonetic || '';
    const translation = data.translation || '';
    const sourceLang = data.source_lang || 'Detected';
    const targetLang = data.target_lang || 'English';
    const isImportant = data.is_important;
    const meanings = data.meanings || [];
    const synonyms = data.synonyms || [];
    const antonyms = data.antonyms || [];
    const explanation = data.explanation || '';

    let meaningsHtml = '';
    if (meanings.length > 0) {
        meaningsHtml = meanings.map((m, idx) => `
            <div class="py-4 border-b border-[#E7E2D8] last:border-b-0 space-y-2">
                <div class="flex items-center space-x-2">
                    <span class="font-serif italic font-bold text-ink-800 text-sm">
                        ${m.part_of_speech || 'Definition'}
                    </span>
                    <span class="text-xs text-ink-400">—</span>
                </div>
                <ul class="space-y-2 pl-3">
                    ${(m.definitions || []).map((d, dIdx) => `
                        <li class="text-ink-800 text-base leading-relaxed flex items-start space-x-2">
                            <span class="text-cognac-700 font-serif font-bold text-sm mt-0.5">${dIdx + 1}.</span>
                            <span>${d}</span>
                        </li>
                    `).join('')}
                </ul>
                ${(m.examples && m.examples.length > 0) ? `
                    <div class="pt-2 pl-5 space-y-1.5">
                        ${m.examples.map(ex => `
                            <p class="text-sm text-ink-500 font-serif italic border-l-2 border-cognac-600/40 pl-3">
                                "${ex}"
                            </p>
                        `).join('')}
                    </div>
                ` : ''}
            </div>
        `).join('');
    } else {
        meaningsHtml = `<p class="text-sm text-ink-500">No definitions recorded.</p>`;
    }

    let synonymsHtml = '';
    if (synonyms.length > 0) {
        synonymsHtml = `
            <div class="space-y-2">
                <div class="text-[11px] font-bold text-ink-500 uppercase tracking-widest flex items-center space-x-1.5">
                    <span>Synonyms</span>
                </div>
                <div class="flex flex-wrap gap-2">
                    ${synonyms.map(s => `
                        <button onclick="quickSearch('${s}')" class="px-3 py-1 rounded-lg text-xs font-medium bg-[#FAF7F2] text-ink-800 border border-[#E7E2D8] hover:border-cognac-600 hover:text-cognac-700 transition">
                            ${s}
                        </button>
                    `).join('')}
                </div>
            </div>
        `;
    }

    let antonymsHtml = '';
    if (antonyms.length > 0) {
        antonymsHtml = `
            <div class="space-y-2">
                <div class="text-[11px] font-bold text-ink-500 uppercase tracking-widest flex items-center space-x-1.5">
                    <span>Antonyms</span>
                </div>
                <div class="flex flex-wrap gap-2">
                    ${antonyms.map(a => `
                        <button onclick="quickSearch('${a}')" class="px-3 py-1 rounded-lg text-xs font-medium bg-[#FAF7F2] text-ink-800 border border-[#E7E2D8] hover:border-rose-400 hover:text-rose-700 transition">
                            ${a}
                        </button>
                    `).join('')}
                </div>
            </div>
        `;
    }

    let explanationHtml = '';
    if (explanation) {
        explanationHtml = `
            <div class="p-4 rounded-2xl bg-amber-50/60 border border-amber-200/60 space-y-1">
                <div class="text-[11px] font-bold text-amber-800 uppercase tracking-widest flex items-center space-x-1.5">
                    <i data-lucide="feather" class="w-3.5 h-3.5 text-amber-700"></i>
                    <span>Editorial Commentary</span>
                </div>
                <p class="text-sm text-amber-900 leading-relaxed font-sans">${explanation}</p>
            </div>
        `;
    }

    container.innerHTML = `
        <div class="bg-white rounded-3xl p-6 sm:p-10 border border-[#E7E2D8] shadow-xs space-y-7 animate-in fade-in duration-200">
            <!-- Header: Word, Phonetics & Actions -->
            <div class="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-6 border-b border-[#E7E2D8]">
                <div>
                    <div class="flex items-center space-x-3">
                        <h2 class="text-3xl sm:text-4xl font-extrabold font-serif-title text-ink-900 tracking-tight capitalize">${word}</h2>
                        <button onclick="speakText('${word}')" class="p-2 text-ink-400 hover:text-cognac-700 hover:bg-[#FAF7F2] rounded-xl border border-transparent hover:border-[#E7E2D8] transition" title="Pronounce">
                            <i data-lucide="volume-2" class="w-5 h-5"></i>
                        </button>
                    </div>
                    ${phonetic ? `<div class="text-sm font-mono text-cognac-700 mt-1">${phonetic}</div>` : ''}
                </div>

                <!-- Star button & Auto-saved badge -->
                <div class="flex items-center space-x-2.5">
                    <button 
                        id="star-btn-${data.id}" 
                        onclick="toggleStar('${data.id}')"
                        class="px-3.5 py-2 rounded-xl text-xs font-bold border transition flex items-center space-x-1.5 ${
                            isImportant 
                            ? 'bg-amber-50 border-amber-300 text-amber-800' 
                            : 'bg-[#FAF7F2] border-[#E7E2D8] text-ink-700 hover:border-amber-300 hover:text-amber-700'
                        }"
                    >
                        <i data-lucide="bookmark" class="w-3.5 h-3.5 ${isImportant ? 'fill-amber-600 text-amber-600' : ''}"></i>
                        <span>${isImportant ? 'Important' : 'Bookmark'}</span>
                    </button>

                    <div class="flex items-center space-x-1.5 px-3 py-2 rounded-xl bg-stone-100 text-ink-700 text-xs font-semibold border border-stone-200">
                        <i data-lucide="check" class="w-3.5 h-3.5 text-emerald-600"></i>
                        <span>Preserved in Vault</span>
                    </div>
                </div>
            </div>

            <!-- Translation Card (Editorial Style) -->
            <div class="p-5 rounded-2xl bg-[#FAF7F2] border border-[#E7E2D8] flex flex-col sm:flex-row sm:items-center justify-between gap-3">
                <div>
                    <div class="text-[11px] font-bold uppercase tracking-widest text-cognac-700 flex items-center space-x-1.5">
                        <span>${sourceLang}</span>
                        <i data-lucide="arrow-right" class="w-3 h-3"></i>
                        <span>${targetLang} Translation</span>
                    </div>
                    <div class="text-2xl font-bold font-serif-title text-ink-900 mt-1">${translation}</div>
                </div>
                <button onclick="speakText('${translation}')" class="self-start sm:self-auto px-3 py-1.5 bg-white text-ink-700 hover:text-cognac-700 border border-[#E7E2D8] rounded-xl transition text-xs font-semibold flex items-center space-x-1.5">
                    <i data-lucide="volume-2" class="w-3.5 h-3.5"></i>
                    <span>Listen</span>
                </button>
            </div>

            <!-- Commentary if present -->
            ${explanationHtml}

            <!-- Meanings Section -->
            <div class="space-y-2">
                <h3 class="text-[11px] font-bold text-ink-400 uppercase tracking-widest">Definitions & Context</h3>
                <div>${meaningsHtml}</div>
            </div>

            <!-- Synonyms & Antonyms Grid -->
            <div class="grid grid-cols-1 md:grid-cols-2 gap-6 pt-5 border-t border-[#E7E2D8]">
                ${synonymsHtml}
                ${antonymsHtml}
            </div>

            <!-- Footer info -->
            <div class="pt-4 border-t border-[#E7E2D8] flex justify-between items-center text-xs text-ink-400">
                <span>Frequency: looked up <strong>${data.search_count || 1}</strong> time(s)</span>
                <a href="/vocab" class="text-cognac-700 font-semibold hover:underline flex items-center space-x-1">
                    <span>Review in My Vocab</span>
                    <i data-lucide="arrow-right" class="w-3.5 h-3.5"></i>
                </a>
            </div>
        </div>
    `;

    container.classList.remove('hidden');
    lucide.createIcons({ root: container });
}

async function toggleStar(vocabId) {
    try {
        const res = await fetch(`/api/vocab/${vocabId}/important`, { method: 'PATCH' });
        const data = await res.json();
        if (res.ok) {
            const btn = document.getElementById(`star-btn-${vocabId}`);
            if (btn) {
                if (data.is_important) {
                    btn.className = 'px-3.5 py-2 rounded-xl text-xs font-bold border transition flex items-center space-x-1.5 bg-amber-50 border-amber-300 text-amber-800';
                    btn.innerHTML = `<i data-lucide="bookmark" class="w-3.5 h-3.5 fill-amber-600 text-amber-600"></i><span>Important</span>`;
                    showToast('Bookmarked as Important', 'success');
                } else {
                    btn.className = 'px-3.5 py-2 rounded-xl text-xs font-bold border transition flex items-center space-x-1.5 bg-[#FAF7F2] border-[#E7E2D8] text-ink-700 hover:border-amber-300 hover:text-amber-700';
                    btn.innerHTML = `<i data-lucide="bookmark" class="w-3.5 h-3.5"></i><span>Bookmark</span>`;
                    showToast('Removed from Important', 'info');
                }
                lucide.createIcons({ root: btn });
            }
        }
    } catch (e) {
        showToast('Error toggling bookmark', 'error');
    }
}

// Auto-execute if query in URL parameter
document.addEventListener('DOMContentLoaded', () => {
    const params = new URLSearchParams(window.location.search);
    const searchParam = params.get('search');
    if (searchParam) {
        document.getElementById('search-input').value = searchParam;
        executeSearch(searchParam);
    }
});
