/**
 * KAUMITA - Client Logic & Interactivity
 * Mengontrol navigasi tab, pilihan formulir, pengiriman API, serta visualisasi BFS Tree.
 */

// State Global Aplikasi
let appState = {
    activeTab: 'chat',
    selectedGender: 'rahasiakan', // default
    selectedCategories: new Set(),
    specialNeeds: {
        disabilitas: false,
        anak: false
    },
    chatCount: 0
};

// Modul 1: Manajemen Tab & Navigasi
function switchTab(tabId) {
    appState.activeTab = tabId;
    
    // Update Menu Items Active Style
    const tabChatBtn = document.getElementById('tab-btn-chat');
    const tabResourcesBtn = document.getElementById('tab-btn-resources');
    
    // Update Tab Panes
    const tabChatPane = document.getElementById('tab-chat');
    const tabResourcesPane = document.getElementById('tab-resources');
    
    if (tabId === 'chat') {
        tabChatBtn.classList.add('active');
        tabResourcesBtn.classList.remove('active');
        
        tabChatPane.classList.add('active');
        tabResourcesPane.classList.remove('active');
    } else if (tabId === 'resources') {
        tabChatBtn.classList.remove('active');
        tabResourcesBtn.classList.add('active');
        
        tabChatPane.classList.remove('active');
        tabResourcesPane.classList.add('active');
        
        // Load data lembaga dari API jika pertama kali dibuka atau diperbarui
        loadLembagaResources();
    }
}

// Modul 2: Pilihan Kategori Bantuan
function toggleCategoryCard(element) {
    const category = element.getAttribute('data-category');
    
    if (appState.selectedCategories.has(category)) {
        appState.selectedCategories.delete(category);
        element.classList.remove('active');
    } else {
        appState.selectedCategories.add(category);
        element.classList.add('active');
    }
}

// Modul 3: Pilihan Gender (Single Select)
function selectGender(element, genderValue) {
    // Nonaktifkan semua pill gender
    const pills = document.querySelectorAll('.gender-pill');
    pills.forEach(pill => pill.classList.remove('active'));
    
    // Aktifkan yang dipilih
    element.classList.add('active');
    appState.selectedGender = genderValue;
}

// Modul 4: Kebutuhan Khusus / Disabilitas (Styling Checkbox)
function updateSpecialNeedsStyle(element) {
    const isChecked = element.checked;
    const parentCard = element.closest('.condition-checkbox-card');
    
    if (isChecked) {
        parentCard.classList.add('active');
    } else {
        parentCard.classList.remove('active');
    }
    
    if (element.id === 'chk-disabilitas') {
        appState.specialNeeds.disabilitas = isChecked;
    } else if (element.id === 'chk-anak') {
        appState.specialNeeds.anak = isChecked;
    }
}

// Modul 5: Start New Request (Reset Form)
function startNewRequest() {
    // Reset state
    appState.selectedGender = 'rahasiakan';
    appState.selectedCategories.clear();
    appState.specialNeeds.disabilitas = false;
    appState.specialNeeds.anak = false;
    appState.chatCount = 0;
    
    // Reset kategori di UI
    const catCards = document.querySelectorAll('.category-card');
    catCards.forEach(card => card.classList.remove('active'));
    
    // Reset gender di UI
    const pills = document.querySelectorAll('.gender-pill');
    pills.forEach(pill => {
        if (pill.textContent.trim().toLowerCase() === 'rahasiakan') {
            pill.classList.add('active');
        } else {
            pill.classList.remove('active');
        }
    });
    
    // Reset checkbox di UI
    const chkDisabilitas = document.getElementById('chk-disabilitas');
    const chkAnak = document.getElementById('chk-anak');
    chkDisabilitas.checked = false;
    chkAnak.checked = false;
    updateSpecialNeedsStyle(chkDisabilitas);
    updateSpecialNeedsStyle(chkAnak);
    
    // Reset input text
    document.getElementById('chat-input-text').value = '';
    
    // Sembunyikan riwayat chat & tampilkan form formulir awal
    document.getElementById('chat-history').style.display = 'none';
    document.getElementById('chat-history').innerHTML = '';
    
    const welcomeContainer = document.querySelector('.welcome-container');
    if (welcomeContainer) welcomeContainer.style.display = 'block';
    
    const assistantFlow = document.querySelector('.assistant-flow');
    if (assistantFlow) assistantFlow.style.display = 'flex';
    
    // Pindah ke tab chat
    switchTab('chat');
    
    showToast('Form konsultasi telah direset.');
}

// Modul 6: Mengirim Permintaan Konsultasi Ke API
async function submitChatRequest() {
    const inputElement = document.getElementById('chat-input-text');
    const message = inputElement.value.trim();
    
    if (!message) {
        showToast('Silakan ketik cerita atau keluhan Anda terlebih dahulu.', 'warning');
        return;
    }
    
    // Tambahkan input text ke form submit & bersihkan form input
    inputElement.value = '';
    
    // Ambil data form untuk dikirim
    const payload = {
        message: message,
        gender: appState.selectedGender,
        disabilitas: appState.specialNeeds.disabilitas,
        anak: appState.specialNeeds.anak,
        kategori: Array.from(appState.selectedCategories)
    };
    
    // Tampilkan panel riwayat chat, sembunyikan form awal
    const chatHistory = document.getElementById('chat-history');
    chatHistory.style.display = 'flex';
    
    const welcomeContainer = document.querySelector('.welcome-container');
    if (welcomeContainer) welcomeContainer.style.display = 'none';
    
    const assistantFlow = document.querySelector('.assistant-flow');
    if (assistantFlow) assistantFlow.style.display = 'none';
    
    // Render Bubble Chat User
    renderUserBubble(message);
    
    // Render Loading Bubble
    const loadingBubbleId = renderLoadingBubble();
    
    // Scroll ke bawah
    scrollToBottom(chatHistory);
    
    try {
        const response = await fetch('/api/chat', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(payload)
        });
        
        const data = await response.json();
        
        // Hapus bubble loading
        removeBubble(loadingBubbleId);
        
        if (response.ok) {
            // Render Respon AI
            renderAssistantBubble(data);
        } else {
            renderErrorBubble(data.error || 'Terjadi kesalahan sistem.');
        }
    } catch (error) {
        removeBubble(loadingBubbleId);
        renderErrorBubble('Gagal terhubung dengan server. Pastikan Flask server menyala.');
        console.error(error);
    }
    
    // Scroll ke bawah lagi
    scrollToBottom(chatHistory);
}

// Menangani Enter Key di Input Text
function handleInputKeyDown(event) {
    if (event.key === 'Enter') {
        submitChatRequest();
    }
}

// Modul 7: Merender Elemen-Elemen Chat Bubbles
function renderUserBubble(text) {
    const chatHistory = document.getElementById('chat-history');
    
    const wrapper = document.createElement('div');
    wrapper.className = 'chat-bubble-wrapper user';
    
    const bubble = document.createElement('div');
    bubble.className = 'chat-bubble';
    
    const textNode = document.createElement('p');
    textNode.textContent = text;
    
    const timeNode = document.createElement('span');
    timeNode.className = 'chat-meta';
    timeNode.textContent = getCurrentTimeString();
    
    bubble.appendChild(textNode);
    bubble.appendChild(timeNode);
    wrapper.appendChild(bubble);
    chatHistory.appendChild(wrapper);
}

function renderLoadingBubble() {
    const chatHistory = document.getElementById('chat-history');
    const bubbleId = 'loading-' + Date.now();
    
    const wrapper = document.createElement('div');
    wrapper.className = 'chat-bubble-wrapper assistant';
    wrapper.id = bubbleId;
    
    const bubble = document.createElement('div');
    bubble.className = 'chat-bubble';
    
    const textNode = document.createElement('p');
    textNode.innerHTML = '<i class="fa-solid fa-circle-notch fa-spin"></i> KAUMITA sedang menganalisis cerita Anda...';
    
    bubble.appendChild(textNode);
    wrapper.appendChild(bubble);
    chatHistory.appendChild(wrapper);
    
    return bubbleId;
}

function removeBubble(id) {
    const el = document.getElementById(id);
    if (el) el.remove();
}

function renderErrorBubble(errorText) {
    const chatHistory = document.getElementById('chat-history');
    
    const wrapper = document.createElement('div');
    wrapper.className = 'chat-bubble-wrapper assistant';
    
    const bubble = document.createElement('div');
    bubble.className = 'chat-bubble';
    bubble.style.borderLeft = '4px solid var(--color-danger)';
    
    const textNode = document.createElement('p');
    textNode.innerHTML = `<span style="color: var(--color-danger); font-weight: bold;"><i class="fa-solid fa-triangle-exclamation"></i> Error:</span> ${errorText}`;
    
    bubble.appendChild(textNode);
    wrapper.appendChild(bubble);
    chatHistory.appendChild(wrapper);
}

function renderAssistantBubble(data) {
    const chatHistory = document.getElementById('chat-history');
    
    const wrapper = document.createElement('div');
    wrapper.className = 'chat-bubble-wrapper assistant';
    
    const bubble = document.createElement('div');
    bubble.className = 'chat-bubble';
    
    // 1. Respon Sapaan Empati
    const sapaanP = document.createElement('p');
    sapaanP.innerHTML = `<strong>KAUMITA:</strong> "${data.sapaan}"`;
    sapaanP.style.marginBottom = '12px';
    bubble.appendChild(sapaanP);
    
    // Info Ekstraksi Tag Kebutuhan & Kota
    const extractionDiv = document.createElement('div');
    extractionDiv.style.fontSize = '12px';
    extractionDiv.style.color = 'var(--color-secondary)';
    extractionDiv.style.backgroundColor = 'var(--color-primary-light)';
    extractionDiv.style.padding = '8px 12px';
    extractionDiv.style.borderRadius = '8px';
    extractionDiv.style.marginBottom = '16px';
    
    let kebutuhanTeks = data.kebutuhan && data.kebutuhan.length > 0 
        ? data.kebutuhan.map(t => `#${t}`).join(', ') 
        : 'Tidak ada tag khusus';
    extractionDiv.innerHTML = `
        <div style="margin-bottom: 2px;"><strong>Analisis Kebutuhan:</strong> ${kebutuhanTeks}</div>
        <div><strong>Wilayah Rujukan:</strong> ${data.kota}</div>
    `;
    bubble.appendChild(extractionDiv);

    // 2. Daftar Lembaga Hasil BFS
    if (data.hasil && data.hasil.length > 0) {
        const titleRec = document.createElement('div');
        titleRec.className = 'chat-recommendation-title';
        titleRec.innerHTML = `<i class="fa-solid fa-list-check"></i> Rekomendasi Rujukan Lembaga (${data.hasil.length})`;
        bubble.appendChild(titleRec);
        
        const recGrid = document.createElement('div');
        recGrid.className = 'chat-rec-grid';
        
        data.hasil.forEach((lbg, index) => {
            const card = document.createElement('div');
            card.className = 'chat-rec-card';
            
            // Header card
            const header = document.createElement('div');
            header.className = 'chat-rec-card-header';
            
            const name = document.createElement('div');
            name.className = 'chat-rec-name';
            name.textContent = `${index + 1}. ${lbg.nama}`;
            
            const city = document.createElement('span');
            city.className = 'chat-rec-city';
            city.textContent = lbg.kota;
            
            header.appendChild(name);
            header.appendChild(city);
            card.appendChild(header);
            
            // Kategori
            const cat = document.createElement('div');
            cat.className = 'chat-rec-cat';
            cat.innerHTML = `<i class="fa-regular fa-folder-open"></i> ${lbg.kategori}`;
            card.appendChild(cat);
            
            // Tags
            const tagsDiv = document.createElement('div');
            tagsDiv.className = 'chat-rec-tags';
            lbg.tags.forEach(t => {
                const tagSpan = document.createElement('span');
                tagSpan.className = 'chat-rec-tag';
                tagSpan.textContent = t;
                tagsDiv.appendChild(tagSpan);
            });
            card.appendChild(tagsDiv);
            
            // Kontak & Badge Disabilitas
            const contactDiv = document.createElement('div');
            contactDiv.className = 'chat-rec-contacts';
            
            if (lbg.wa) {
                const waBtn = document.createElement('a');
                waBtn.className = 'chat-rec-btn wa';
                waBtn.href = `https://wa.me/62${lbg.wa.replace(/^0/, '')}`;
                waBtn.target = '_blank';
                waBtn.innerHTML = `<i class="fa-brands fa-whatsapp"></i> WhatsApp`;
                contactDiv.appendChild(waBtn);
            }
            
            if (lbg.email) {
                const emailBtn = document.createElement('a');
                emailBtn.className = 'chat-rec-btn email';
                emailBtn.href = `mailto:${lbg.email}`;
                emailBtn.innerHTML = `<i class="fa-regular fa-envelope"></i> Email`;
                emailBtn.onclick = (e) => {
                    e.stopPropagation();
                    navigator.clipboard.writeText(lbg.email);
                    showToast(`Email ${lbg.email} disalin ke clipboard!`);
                };
                contactDiv.appendChild(emailBtn);
            }
            
            if (lbg.kontak) {
                const phoneBtn = document.createElement('a');
                phoneBtn.className = 'chat-rec-btn phone';
                phoneBtn.href = `tel:${lbg.kontak}`;
                phoneBtn.innerHTML = `<i class="fa-solid fa-phone"></i> Telp`;
                contactDiv.appendChild(phoneBtn);
            }
            
            if (lbg.disabilitas_friendly) {
                const disBadge = document.createElement('span');
                disBadge.className = 'chat-rec-badge-disabilitas';
                disBadge.innerHTML = `<i class="fa-solid fa-wheelchair"></i> Aksesibel`;
                contactDiv.appendChild(disBadge);
            }
            
            card.appendChild(contactDiv);
            recGrid.appendChild(card);
        });
        
        bubble.appendChild(recGrid);
    } else {
        const noResultDiv = document.createElement('div');
        noResultDiv.style.padding = '14px';
        noResultDiv.style.backgroundColor = '#FFFBEB';
        noResultDiv.style.border = '1px solid #FEF3C7';
        noResultDiv.style.borderRadius = '10px';
        noResultDiv.style.fontSize = '13px';
        noResultDiv.style.color = '#B45309';
        noResultDiv.style.marginBottom = '16px';
        noResultDiv.innerHTML = `<i class="fa-solid fa-circle-info"></i> Tidak ditemukan lembaga rujukan yang sepenuhnya memenuhi kombinasi kriteria filter dan cerita Anda. Silakan coba kurangi filter kategori atau ganti kata kunci kota Anda.`;
        bubble.appendChild(noResultDiv);
    }
    
    // 3. Visualisasi BFS Tree
    if (data.bfs_tree && Object.keys(data.bfs_tree).length > 0) {
        const treeTitle = document.createElement('div');
        treeTitle.className = 'bfs-tree-title';
        treeTitle.innerHTML = `<i class="fa-solid fa-diagram-project"></i> Jaringan Penelusuran Rujukan (BFS Tree)`;
        bubble.appendChild(treeTitle);
        
        const treeContainer = document.createElement('div');
        treeContainer.className = 'bfs-tree-container';
        
        const treeFlow = document.createElement('div');
        treeFlow.className = 'bfs-tree-flow';
        
        // Kelompokkan node berdasarkan level
        const levelMap = {};
        Object.keys(data.bfs_tree).forEach(nodeId => {
            const node = data.bfs_tree[nodeId];
            if (!levelMap[node.level]) {
                levelMap[node.level] = [];
            }
            levelMap[node.level].push({
                id: nodeId,
                nama: node.nama,
                parent_id: node.parent_id,
                parent_nama: node.parent_nama
            });
        });
        
        // Urutkan level & render ke UI
        const sortedLevels = Object.keys(levelMap).sort((a, b) => parseInt(a) - parseInt(b));
        sortedLevels.forEach(lvl => {
            const lvlGroup = document.createElement('div');
            lvlGroup.className = 'bfs-tree-level-group';
            
            const lvlHeader = document.createElement('div');
            lvlHeader.className = 'bfs-tree-level-header';
            lvlHeader.textContent = `Pencarian Level ${lvl} (${levelMap[lvl].length} Lembaga)`;
            lvlGroup.appendChild(lvlHeader);
            
            const nodesList = document.createElement('div');
            nodesList.className = 'bfs-tree-nodes-list';
            
            levelMap[lvl].forEach(node => {
                const nodeDiv = document.createElement('div');
                nodeDiv.className = 'bfs-tree-node';
                
                const nodeName = document.createElement('span');
                nodeName.style.fontWeight = 'bold';
                nodeName.textContent = node.nama;
                nodeDiv.appendChild(nodeName);
                
                if (node.parent_nama) {
                    const nodeParent = document.createElement('span');
                    nodeParent.className = 'bfs-tree-node-parent';
                    nodeParent.innerHTML = `<i class="fa-solid fa-arrow-turn-up" style="transform: rotate(90deg); margin-right: 4px;"></i>Rujukan dari: <strong>${node.parent_nama}</strong>`;
                    nodeDiv.appendChild(nodeParent);
                } else {
                    const nodeParent = document.createElement('span');
                    nodeParent.className = 'bfs-tree-node-parent';
                    nodeParent.textContent = 'Node Awal (Root)';
                    nodeDiv.appendChild(nodeParent);
                }
                
                nodesList.appendChild(nodeDiv);
            });
            
            lvlGroup.appendChild(nodesList);
            treeFlow.appendChild(lvlGroup);
        });
        
        treeContainer.appendChild(treeFlow);
        bubble.appendChild(treeContainer);
    }
    
    // Waktu respons
    const timeNode = document.createElement('span');
    timeNode.className = 'chat-meta';
    timeNode.textContent = getCurrentTimeString();
    bubble.appendChild(timeNode);
    
    wrapper.appendChild(bubble);
    chatHistory.appendChild(wrapper);
}

// Modul 8: Memuat Daftar Lembaga di Tab Resource Map secara Dinamis
let isLembagaLoaded = false;
async function loadLembagaResources() {
    if (isLembagaLoaded) return; // hindari load berulang
    
    const container = document.getElementById('resources-grid-container');
    container.innerHTML = `
        <div class="loading-spinner">
            <i class="fa-solid fa-circle-notch fa-spin"></i> Memuat data rujukan...
        </div>
    `;
    
    try {
        const response = await fetch('/api/lembaga');
        const data = await response.json();
        
        container.innerHTML = ''; // bersihkan loader
        
        if (data && data.length > 0) {
            data.forEach(lbg => {
                const card = document.createElement('div');
                card.className = 'resource-card';
                
                // Header
                const header = document.createElement('div');
                header.className = 'resource-card-header';
                
                const name = document.createElement('h3');
                name.className = 'resource-card-name';
                name.textContent = lbg.nama;
                
                const city = document.createElement('span');
                city.className = 'resource-card-city';
                city.textContent = lbg.kota;
                
                header.appendChild(name);
                header.appendChild(city);
                card.appendChild(header);
                
                // Kategori
                const cat = document.createElement('div');
                cat.className = 'resource-card-cat';
                cat.textContent = lbg.kategori;
                card.appendChild(cat);
                
                // Tags
                const tagsDiv = document.createElement('div');
                tagsDiv.className = 'resource-card-tags';
                lbg.tags.forEach(t => {
                    const tag = document.createElement('span');
                    tag.className = 'resource-card-tag';
                    tag.textContent = t;
                    tagsDiv.appendChild(tag);
                });
                card.appendChild(tagsDiv);
                
                // Footer (Kontak)
                const footer = document.createElement('div');
                footer.className = 'resource-card-footer';
                
                const contactsDiv = document.createElement('div');
                contactsDiv.className = 'resource-card-contacts';
                
                if (lbg.wa) {
                    const waBtn = document.createElement('a');
                    waBtn.className = 'chat-rec-btn wa';
                    waBtn.href = `https://wa.me/62${lbg.wa.replace(/^0/, '')}`;
                    waBtn.target = '_blank';
                    waBtn.innerHTML = `<i class="fa-brands fa-whatsapp"></i> WA`;
                    contactsDiv.appendChild(waBtn);
                }
                
                if (lbg.email) {
                    const emailBtn = document.createElement('a');
                    emailBtn.className = 'chat-rec-btn email';
                    emailBtn.href = `mailto:${lbg.email}`;
                    emailBtn.innerHTML = `<i class="fa-regular fa-envelope"></i> Email`;
                    emailBtn.onclick = (e) => {
                        e.stopPropagation();
                        navigator.clipboard.writeText(lbg.email);
                        showToast(`Email ${lbg.email} disalin ke clipboard!`);
                    };
                    contactsDiv.appendChild(emailBtn);
                }
                
                if (lbg.kontak) {
                    const phoneBtn = document.createElement('a');
                    phoneBtn.className = 'chat-rec-btn phone';
                    phoneBtn.href = `tel:${lbg.kontak}`;
                    phoneBtn.innerHTML = `<i class="fa-solid fa-phone"></i>`;
                    contactsDiv.appendChild(phoneBtn);
                }
                
                footer.appendChild(contactsDiv);
                
                if (lbg.disabilitas_friendly) {
                    const disBadge = document.createElement('div');
                    disBadge.className = 'resource-disabilitas-badge';
                    disBadge.innerHTML = `<span class="chat-rec-badge-disabilitas"><i class="fa-solid fa-wheelchair"></i> Aksesibel</span>`;
                    footer.appendChild(disBadge);
                }
                
                card.appendChild(footer);
                container.appendChild(card);
            });
            
            isLembagaLoaded = true;
            
            // Perbarui sub-header dengan jumlah lembaga yang valid
            const subHeader = document.querySelector('.resources-subtitle');
            if (subHeader) {
                subHeader.textContent = `Menampilkan seluruh daftar ${data.length} lembaga bantuan sosial dan perlindungan inklusif terdaftar.`;
            }
        } else {
            container.innerHTML = '<div class="loading-spinner">Tidak ada data lembaga bantuan sosial.</div>';
        }
    } catch (error) {
        container.innerHTML = `
            <div class="loading-spinner" style="color: var(--color-danger);">
                <i class="fa-solid fa-triangle-exclamation"></i> Gagal memuat data lembaga. Silakan muat ulang halaman.
            </div>
        `;
        console.error(error);
    }
}

// Modul 9: Trigger Emergency & Alert Lainnya
function triggerEmergencyAlert() {
    alert(`🚨 MODUL BANTUAN DARURAT (EMERGENCY) 🚨\n\nJika Anda atau orang di sekitar Anda berada dalam bahaya mendesak, silakan hubungi rujukan darurat nasional:\n\n1. SAPA KemenPPPA: Hubungi Telp 129 / WhatsApp 08111-129-129\n2. Layanan Kepolisian: Hubungi 110\n3. Ambulans/Kesehatan: Hubungi 118 atau 119\n4. Komnas Perempuan (Pengaduan): Hubungi 021-3903963\n\nKami siap melindungi Anda. Identitas Anda terenkripsi.`);
}

function showFeatureAlert(featureName) {
    showToast(`Fitur "${featureName}" sedang dipersiapkan dan akan segera hadir!`);
}

function startVoiceInput() {
    showToast('Input Suara (Speech-to-Text) sedang diinisialisasi...');
}

// Modul 10: Utilitas Pembantu (Scroll, Time, Toast)
function scrollToBottom(element) {
    element.scrollTo({
        top: element.scrollHeight,
        behavior: 'smooth'
    });
}

function getCurrentTimeString() {
    const now = new Date();
    const hrs = String(now.getHours()).padStart(2, '0');
    const mins = String(now.getMinutes()).padStart(2, '0');
    return `${hrs}:${mins}`;
}

// Membuat Custom Toast Notification yang cantik
function showToast(message, type = 'info') {
    const toast = document.createElement('div');
    toast.style.position = 'fixed';
    toast.style.bottom = '90px';
    toast.style.left = '50%';
    toast.style.transform = 'translateX(-50%)';
    toast.style.backgroundColor = type === 'warning' ? '#B45309' : '#10567A';
    toast.style.color = '#FFFFFF';
    toast.style.padding = '12px 24px';
    toast.style.borderRadius = '30px';
    toast.style.fontSize = '13px';
    toast.style.fontWeight = '600';
    toast.style.zIndex = '1000';
    toast.style.boxShadow = '0 10px 25px rgba(0,0,0,0.15)';
    toast.style.opacity = '0';
    toast.style.transition = 'opacity 0.3s ease, bottom 0.3s ease';
    toast.innerHTML = `<i class="fa-solid fa-circle-info" style="margin-right: 8px;"></i> ${message}`;
    
    document.body.appendChild(toast);
    
    // Tampilkan secara perlahan
    setTimeout(() => {
        toast.style.opacity = '1';
        toast.style.bottom = '100px';
    }, 50);
    
    // Hilangkan setelah 3 detik
    setTimeout(() => {
        toast.style.opacity = '0';
        toast.style.bottom = '90px';
        setTimeout(() => {
            toast.remove();
        }, 300);
    }, 3000);
}

// Inisialisasi Floating Headset Support Button secara dinamis
// Toggle Sidebar minimize / expand
function toggleSidebar() {
    const appContainer = document.querySelector('.app-container');
    appContainer.classList.toggle('sidebar-collapsed');
    
    const isCollapsed = appContainer.classList.contains('sidebar-collapsed');
    localStorage.setItem('sidebar-collapsed', isCollapsed);
}

// Inisialisasi Floating Headset Support Button secara dinamis
document.addEventListener('DOMContentLoaded', () => {
    // Restore sidebar state dari localStorage
    const isCollapsed = localStorage.getItem('sidebar-collapsed') === 'true';
    if (isCollapsed) {
        document.querySelector('.app-container').classList.add('sidebar-collapsed');
    }

    const supportBtn = document.createElement('button');
    supportBtn.className = 'floating-support-btn';
    supportBtn.innerHTML = '<i class="fa-solid fa-headset"></i>';
    supportBtn.title = 'Bantuan Langsung / Customer Service';
    supportBtn.onclick = () => {
        alert('KAUMITA Customer Service:\nHubungi relawan pendamping kami di layanan krisis: 129 (SAPA) atau kirimkan email ke bantuan@kaumita.org.');
    };
    document.body.appendChild(supportBtn);
});
