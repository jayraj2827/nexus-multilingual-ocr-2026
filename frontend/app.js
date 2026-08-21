// NexusOCR Frontend Application Logic (KISS Architecture)

let currentDocResult = null;
let currentPageIdx = 0;
let selectedFile = null;

document.addEventListener('DOMContentLoaded', () => {
    setupDropzone();
    setupProcessButton();
    setupPagination();
    window.addEventListener('resize', handleResize);
});

function handleResize() {
    if (currentDocResult && currentDocResult.pages[currentPageIdx]) {
        const imgEl = document.getElementById('pageImage');
        if (imgEl && imgEl.complete) {
            renderBBoxes(currentDocResult.pages[currentPageIdx], imgEl);
        }
    }
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
    const outputBox = document.getElementById('markdownContent');

    btn.addEventListener('click', async () => {
        if (!selectedFile) {
            alert('Please select a PDF document first.');
            return;
        }

        btn.disabled = true;
        btn.innerText = 'Extracting Text (Processing...)...';
        outputBox.innerText = 'Processing document through NexusOCR 3-Pillar Engine...\n\n- Pillar 1: Digital Text & Table extraction...\n- Pillar 2: Docling Layout intelligence...\n- Pillar 3: Local Ollama Vision VLM...\n\nPlease wait a moment.';

        const formData = new FormData();
        formData.append('file', selectedFile);

        try {
            const response = await fetch('/api/process', {
                method: 'POST',
                body: formData
            });

            if (!response.ok) {
                const errData = await response.json().catch(() => ({}));
                throw new Error(errData.detail || `Server returned status ${response.status}`);
            }

            currentDocResult = await response.json();
            currentPageIdx = 0;
            renderDocumentResult(currentDocResult);
        } catch (err) {
            outputBox.innerText = `OCR Processing Error: ${err.message}`;
            alert(`OCR Processing Error: ${err.message}`);
        } finally {
            btn.disabled = false;
            btn.innerText = 'Extract Text';
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
    document.getElementById('totalLatency').innerText = `${doc.total_execution_time_ms.toFixed(1)} ms`;
    document.getElementById('totalPages').innerText = `${doc.total_pages}`;
    document.getElementById('markdownContent').innerText = doc.full_markdown || 'No text extracted.';

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

    const imgEl = document.getElementById('pageImage');
    imgEl.src = `/api/page_image/${encodeURIComponent(currentDocResult.file_name)}/${page.page_number}`;

    imgEl.onload = () => {
        renderBBoxes(page, imgEl);
    };
}

function renderBBoxes(page, imgEl) {
    const overlay = document.getElementById('bboxOverlay');
    overlay.innerHTML = '';

    const natW = imgEl.naturalWidth || page.width || 1;
    const natH = imgEl.naturalHeight || page.height || 1;
    const scaleX = imgEl.clientWidth / natW;
    const scaleY = imgEl.clientHeight / natH;

    // 1. Render Table Bounding Boxes (Orange)
    if (page.tables) {
        page.tables.forEach(t => {
            const box = document.createElement('div');
            box.className = 'bbox-box bbox-table';
            box.style.left = `${t.bbox.xmin * scaleX}px`;
            box.style.top = `${t.bbox.ymin * scaleY}px`;
            box.style.width = `${(t.bbox.xmax - t.bbox.xmin) * scaleX}px`;
            box.style.height = `${(t.bbox.ymax - t.bbox.ymin) * scaleY}px`;
            box.title = `[Table] ${t.num_rows} rows x ${t.num_cols} cols`;
            overlay.appendChild(box);
        });
    }

    // 2. Render Line/Region Bounding Boxes
    if (page.regions) {
        page.regions.forEach(r => {
            const box = document.createElement('div');
            box.className = 'bbox-box';
            if (r.category === 'header') box.classList.add('bbox-header');
            if (r.category === 'figure') box.classList.add('bbox-figure');

            box.style.left = `${r.bbox.xmin * scaleX}px`;
            box.style.top = `${r.bbox.ymin * scaleY}px`;
            box.style.width = `${Math.max(2, (r.bbox.xmax - r.bbox.xmin) * scaleX)}px`;
            box.style.height = `${Math.max(2, (r.bbox.ymax - r.bbox.ymin) * scaleY)}px`;

            box.title = `[${r.category}] ${r.text}`;
            overlay.appendChild(box);
        });
    }
}

function copyExtractedText() {
    const text = document.getElementById('markdownContent').innerText;
    navigator.clipboard.writeText(text).then(() => {
        alert('Extracted text copied to clipboard!');
    });
}
