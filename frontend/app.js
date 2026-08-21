// NexusOCR Frontend Application Logic

let currentDocResult = null;
let currentPageIdx = 0;
let selectedFile = null;

document.addEventListener('DOMContentLoaded', () => {
    setupTabs();
    setupDropzone();
    setupProcessButton();
    setupPagination();
});

function setupTabs() {
    const tabBtns = document.querySelectorAll('.tab-btn');
    tabBtns.forEach(btn => {
        btn.addEventListener('click', () => {
            tabBtns.forEach(b => b.classList.remove('active'));
            document.querySelectorAll('.tab-content').forEach(c => c.classList.remove('active'));

            btn.classList.add('active');
            const targetId = `tab${btn.dataset.tab.charAt(0).toUpperCase() + btn.dataset.tab.slice(1)}`;
            const targetContent = document.getElementById(targetId);
            if (targetContent) targetContent.classList.add('active');
        });
    });
}

function setupDropzone() {
    const dropzone = document.getElementById('dropzone');
    const fileInput = document.getElementById('fileInput');
    const fileInfo = document.getElementById('selectedFileInfo');

    fileInput.addEventListener('change', (e) => {
        if (e.target.files.length > 0) {
            selectedFile = e.target.files[0];
            fileInfo.innerHTML = `Selected: <strong>${selectedFile.name}</strong> (${(selectedFile.size / 1024).toFixed(1)} KB)`;
        }
    });

    dropzone.addEventListener('dragover', (e) => {
        e.preventDefault();
        dropzone.style.borderColor = 'var(--accent-blue)';
    });

    dropzone.addEventListener('dragleave', () => {
        dropzone.style.borderColor = 'var(--border-color)';
    });

    dropzone.addEventListener('drop', (e) => {
        e.preventDefault();
        dropzone.style.borderColor = 'var(--border-color)';
        if (e.dataTransfer.files.length > 0) {
            selectedFile = e.dataTransfer.files[0];
            fileInput.files = e.dataTransfer.files;
            fileInfo.innerHTML = `Selected: <strong>${selectedFile.name}</strong> (${(selectedFile.size / 1024).toFixed(1)} KB)`;
        }
    });
}

function setupProcessButton() {
    const btn = document.getElementById('processBtn');
    btn.addEventListener('click', async () => {
        if (!selectedFile) {
            alert('Please select a PDF document first.');
            return;
        }

        btn.disabled = true;
        btn.innerText = 'Processing Adaptive OCR...';

        const formData = new FormData();
        formData.append('file', selectedFile);

        const schemaKeys = document.getElementById('schemaKeys').value;
        if (schemaKeys.trim()) {
            formData.append('schema_keys', schemaKeys);
        }

        try {
            const response = await fetch('/api/process', {
                method: 'POST',
                body: formData
            });

            if (!response.ok) {
                throw new Error(`Server returned status ${response.status}`);
            }

            currentDocResult = await response.json();
            currentPageIdx = 0;
            renderDocumentResult(currentDocResult);
        } catch (err) {
            alert(`OCR Processing Error: ${err.message}`);
        } finally {
            btn.disabled = false;
            btn.innerText = 'Run Adaptive OCR';
        }
    });
}

function setupPagination() {
    document.getElementById('prevPageBtn').addEventListener('click', () => {
        if (currentDocResult && currentPageIdx > 0) {
            currentPageIdx--;
            renderCurrentPage();
        }
    });

    document.getElementById('nextPageBtn').addEventListener('click', () => {
        if (currentDocResult && currentPageIdx < currentDocResult.pages.length - 1) {
            currentPageIdx++;
            renderCurrentPage();
        }
    });
}

function renderDocumentResult(doc) {
    // 1. Update Header Metrics
    document.getElementById('totalLatency').innerText = `${doc.total_execution_time_ms.toFixed(1)} ms`;
    document.getElementById('avgTrustScore').innerText = `${(doc.average_trust_score * 100).toFixed(0)}%`;
    document.getElementById('vlmRate').innerText = `${(doc.vlm_escalation_rate * 100).toFixed(1)}%`;

    // 2. Update Output Previews
    document.getElementById('markdownContent').innerText = doc.full_markdown || 'No text extracted.';
    document.getElementById('jsonContent').innerText = JSON.stringify(doc.structured_json, null, 2);

    // 3. Render Key-Value Fields Grid
    renderFieldsGrid(doc.structured_json.extracted_fields || {});

    // 4. Show Page Navigator & Render Page
    if (doc.pages && doc.pages.length > 0) {
        document.getElementById('pageNavigator').style.display = 'flex';
        document.getElementById('previewContainer').style.display = 'flex';
        renderCurrentPage();
    }
}

function renderCurrentPage() {
    if (!currentDocResult || !currentDocResult.pages[currentPageIdx]) return;

    const page = currentDocResult.pages[currentPageIdx];
    document.getElementById('pageIndicator').innerText = `Page ${page.page_number} / ${currentDocResult.pages.length}`;

    // Request page image render from backend
    const imgEl = document.getElementById('pageImage');
    imgEl.src = `/api/page_image/${encodeURIComponent(currentDocResult.file_name)}/${page.page_number}`;

    imgEl.onload = () => {
        renderBBoxes(page, imgEl);
    };
}

function renderBBoxes(page, imgEl) {
    const overlay = document.getElementById('bboxOverlay');
    overlay.innerHTML = '';

    const scaleX = imgEl.clientWidth / page.width;
    const scaleY = imgEl.clientHeight / page.height;

    page.regions.forEach(r => {
        const box = document.createElement('div');
        box.className = 'bbox-box';
        if (r.text_type === 'handwritten') box.classList.add('handwriting');
        if (r.engine_used.includes('vlm')) box.classList.add('vlm');

        box.style.left = `${r.bbox.xmin * scaleX}px`;
        box.style.top = `${r.bbox.ymin * scaleY}px`;
        box.style.width = `${(r.bbox.xmax - r.bbox.xmin) * scaleX}px`;
        box.style.height = `${(r.bbox.ymax - r.bbox.ymin) * scaleY}px`;

        box.title = `[${r.script}] ${r.text} (${(r.composite_confidence * 100).toFixed(0)}%)`;
        overlay.appendChild(box);
    });
}

function renderFieldsGrid(fields) {
    const grid = document.getElementById('fieldsGrid');
    grid.innerHTML = '';

    const keys = Object.keys(fields);
    if (keys.length === 0) {
        grid.innerHTML = '<p class="placeholder-text">No target fields identified.</p>';
        return;
    }

    keys.forEach(k => {
        const card = document.createElement('div');
        card.className = 'field-card';
        card.innerHTML = `
            <div class="field-key">${k}</div>
            <div class="field-val">${fields[k]}</div>
        `;
        grid.appendChild(card);
    });
}

function copyContent(elementId) {
    const text = document.getElementById(elementId).innerText;
    navigator.clipboard.writeText(text).then(() => {
        alert('Copied to clipboard!');
    });
}
