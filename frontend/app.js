/**
 * NexusOCR Studio Application Logic
 * Clean Document Intelligence Client with Real-Time Loading State
 */

let currentDocumentResult = null;
let currentPageIndex = 0;
let currentZoom = 1.0;
let showBBoxes = true;
let currentActiveTab = "markdown";

// DOM Elements
const fileInput = document.getElementById("fileInput");
const dropzone = document.getElementById("dropzone");
const uploadActionRow = document.getElementById("uploadActionRow");
const pillFileName = document.getElementById("pillFileName");
const pillFileSize = document.getElementById("pillFileSize");
const changeFileBtn = document.getElementById("changeFileBtn");
const reProcessBtn = document.getElementById("reProcessBtn");

const sampleSelect = document.getElementById("sampleSelect");
const canvasToolbar = document.getElementById("canvasToolbar");
const emptyCanvasState = document.getElementById("emptyCanvasState");
const canvasStage = document.getElementById("canvasStage");
const pageImage = document.getElementById("pageImage");
const bboxOverlay = document.getElementById("bboxOverlay");

const loadingOverlay = document.getElementById("loadingOverlay");
const loadingTitle = document.getElementById("loadingTitle");
const loadingSubtitle = document.getElementById("loadingSubtitle");

const prevPageBtn = document.getElementById("prevPageBtn");
const nextPageBtn = document.getElementById("nextPageBtn");
const pageIndicator = document.getElementById("pageIndicator");
const pageTierPill = document.getElementById("pageTierPill");
const toggleBBoxCheckbox = document.getElementById("toggleBBoxCheckbox");
const zoomInBtn = document.getElementById("zoomInBtn");
const zoomOutBtn = document.getElementById("zoomOutBtn");
const zoomFitBtn = document.getElementById("zoomFitBtn");
const zoomLevelText = document.getElementById("zoomLevelText");

const totalLatencyEl = document.getElementById("totalLatency");
const trustScoreEl = document.getElementById("trustScore");
const totalPagesEl = document.getElementById("totalPages");
const statusTextEl = document.getElementById("statusText");
const charCountTag = document.getElementById("charCountTag");
const langDetectTag = document.getElementById("langDetectTag");

const markdownRendered = document.getElementById("markdownRendered");
const tablesContainer = document.getElementById("tablesContainer");
const jsonCodeViewer = document.getElementById("jsonCodeViewer");
const rawTextViewer = document.getElementById("rawTextViewer");

const copyCurrentTabBtn = document.getElementById("copyCurrentTabBtn");
const downloadMdBtn = document.getElementById("downloadMdBtn");
const downloadJsonBtn = document.getElementById("downloadJsonBtn");
const bboxTooltip = document.getElementById("bboxTooltip");
const ttType = document.getElementById("ttType");
const ttConf = document.getElementById("ttConf");
const ttText = document.getElementById("ttText");
const toast = document.getElementById("toast");

// ==========================================================================
// Initialization & Samples Loading
// ==========================================================================
let currentHardwareName = "CPU";

document.addEventListener("DOMContentLoaded", async () => {
    initTabs();
    initUploadEvents();
    initCanvasControls();
    initExportButtons();
    await loadTelemetry();
    await loadSampleOptions();
});

async function loadTelemetry() {
    try {
        const res = await fetch("/api/health");
        if (res.ok) {
            const data = await res.json();
            currentHardwareName = data.device_name || data.hardware || (data.is_amd_hardware ? "AMD CPU" : "CPU");
        }
    } catch (e) {
        currentHardwareName = "CPU";
    }
}

async function loadSampleOptions() {
    try {
        const res = await fetch("/api/samples");
        if (res.ok) {
            const samples = await res.json();
            sampleSelect.innerHTML = '<option value="">Load Preset Document...</option>';
            samples.forEach(s => {
                const opt = document.createElement("option");
                opt.value = s.name;
                opt.textContent = s.display;
                sampleSelect.appendChild(opt);
            });
        }
    } catch (e) {
        console.warn("Could not load demo samples:", e);
    }

    sampleSelect.addEventListener("change", async (e) => {
        const val = e.target.value;
        if (!val) return;
        await processSampleFile(val);
    });
}

// ==========================================================================
// Loading States
// ==========================================================================
function showLoading(title = "Processing document...", subtitle = "Running tiered extraction") {
    if (loadingOverlay) {
        loadingTitle.textContent = title;
        loadingSubtitle.textContent = subtitle;
        loadingOverlay.style.display = "flex";
    }
    if (markdownRendered) markdownRendered.style.opacity = "0.35";
    if (jsonCodeViewer) jsonCodeViewer.style.opacity = "0.35";
    if (rawTextViewer) rawTextViewer.style.opacity = "0.35";
}

function hideLoading() {
    if (loadingOverlay) {
        loadingOverlay.style.display = "none";
    }
    if (markdownRendered) markdownRendered.style.opacity = "1";
    if (jsonCodeViewer) jsonCodeViewer.style.opacity = "1";
    if (rawTextViewer) rawTextViewer.style.opacity = "1";
}

// ==========================================================================
// Upload & Drag-Drop Handling
// ==========================================================================
function initUploadEvents() {
    fileInput.addEventListener("change", (e) => {
        if (e.target.files && e.target.files[0]) {
            handleSelectedFile(e.target.files[0]);
        }
    });

    // Multi-target drag & drop so dropping an image anywhere replaces/loads document
    const dropZones = [dropzone, uploadBar, viewportWrapper];
    dropZones.forEach(elem => {
        if (!elem) return;
        elem.addEventListener("dragover", (e) => {
            e.preventDefault();
            dropzone.classList.add("dragover");
        });
        elem.addEventListener("dragleave", () => {
            dropzone.classList.remove("dragover");
        });
        elem.addEventListener("drop", (e) => {
            e.preventDefault();
            dropzone.classList.remove("dragover");
            if (e.dataTransfer.files && e.dataTransfer.files[0]) {
                handleSelectedFile(e.dataTransfer.files[0]);
            }
        });
    });

    // 1-Click to trigger native file dialog (reset value so same or new file triggers change)
    changeFileBtn.addEventListener("click", () => {
        fileInput.value = "";
        fileInput.click();
    });

    reProcessBtn.addEventListener("click", async () => {
        if (fileInput.files && fileInput.files[0]) {
            await uploadAndProcess(fileInput.files[0]);
        } else if (pillFileName.textContent) {
            await processSampleFile(pillFileName.textContent);
        }
    });
}

const SUPPORTED_EXTS = [
    ".pdf", ".png", ".jpg", ".jpeg", ".tiff", ".tif", ".bmp", ".webp", ".gif",
    ".docx", ".xlsx", ".csv", ".tsv", ".pptx", ".txt", ".md", ".html", ".htm", ".epub"
];
const AUDIO_VIDEO_EXTS = [
    ".mp3", ".wav", ".aac", ".flac", ".ogg", ".m4a", ".mp4", ".avi", ".mov", ".mkv", ".flv", ".webm"
];

function handleSelectedFile(file) {
    const ext = "." + file.name.split(".").pop().toLowerCase();

    if (AUDIO_VIDEO_EXTS.includes(ext)) {
        showToast(`Audio & Video files (${ext}) are not supported. NexusOCR is a document and image intelligence engine.`, true);
        return;
    }

    if (!SUPPORTED_EXTS.includes(ext)) {
        showToast(`Unsupported format '${ext}'. Please upload a document or image (PDF, PNG, JPG, TIFF, DOCX, XLSX, etc.).`, true);
        return;
    }

    // Instantly update file pill
    pillFileName.textContent = file.name;
    pillFileSize.textContent = formatBytes(file.size);
    dropzone.style.display = "none";
    uploadActionRow.style.display = "flex";

    // Instantly show loading state
    showLoading(`Processing ${file.name}...`, "Extracting document content and structure");
    uploadAndProcess(file);
}

async function uploadAndProcess(file) {
    setStatus("Extracting document...", true);
    showLoading(`Uploading & Processing ${file.name}...`, "Running pipeline");

    const formData = new FormData();
    formData.append("file", file);

    try {
        const response = await fetch("/api/process", {
            method: "POST",
            body: formData
        });

        if (!response.ok) {
            const err = await response.json();
            throw new Error(err.detail || "Extraction failed");
        }

        const data = await response.json();
        handleExtractionSuccess(data);
    } catch (err) {
        console.error("Extraction error:", err);
        hideLoading();
        setStatus("Error: " + err.message, false);
        showToast(err.message, true);
    }
}

async function processSampleFile(filename) {
    pillFileName.textContent = filename;
    pillFileSize.textContent = "Preset";
    dropzone.style.display = "none";
    uploadActionRow.style.display = "flex";

    setStatus(`Processing '${filename}'...`, true);
    showLoading(`Processing preset '${filename}'...`, "Running tiered extraction");

    try {
        const response = await fetch(`/api/process_sample/${encodeURIComponent(filename)}`, {
            method: "POST"
        });

        if (!response.ok) {
            const err = await response.json();
            throw new Error(err.detail || "Failed to process sample");
        }

        const data = await response.json();
        handleExtractionSuccess(data);
    } catch (err) {
        console.error("Sample processing error:", err);
        hideLoading();
        setStatus("Error: " + err.message, false);
        showToast(err.message, true);
    }
}

// ==========================================================================
// Success & Viewport Rendering
// ==========================================================================
function handleExtractionSuccess(data) {
    hideLoading();
    currentDocumentResult = data;
    currentPageIndex = 0;
    currentZoom = 1.0;

    // Update KPIs
    totalLatencyEl.textContent = `${data.total_execution_time_ms.toFixed(0)} ms`;
    const avgConf = (data.average_trust_score * 100).toFixed(0);
    trustScoreEl.textContent = `${avgConf}%`;
    totalPagesEl.textContent = data.total_pages;

    // Show Viewports
    emptyCanvasState.style.display = "none";
    canvasStage.style.display = "inline-block";
    canvasToolbar.style.display = "flex";

    renderCurrentPage();
    renderStudioViews();

    setStatus(`Extracted ${data.total_pages} page(s) in ${data.total_execution_time_ms.toFixed(0)}ms`, false);
    showToast(`Processed in ${data.total_execution_time_ms.toFixed(0)}ms`);
}

function renderCurrentPage() {
    if (!currentDocumentResult || !currentDocumentResult.pages) return;
    const page = currentDocumentResult.pages[currentPageIndex];
    if (!page) return;

    pageIndicator.textContent = `Page ${currentPageIndex + 1} / ${currentDocumentResult.total_pages}`;
    prevPageBtn.disabled = currentPageIndex === 0;
    nextPageBtn.disabled = currentPageIndex >= currentDocumentResult.total_pages - 1;

    // Tier badge update
    if (page.is_digital) {
        pageTierPill.textContent = `Tier 1: Digital Native (${page.execution_time_ms.toFixed(0)}ms)`;
    } else {
        pageTierPill.textContent = `Tier 2: PaddleOCR [${currentHardwareName}] (${page.execution_time_ms.toFixed(0)}ms)`;
    }

    // Load page image
    const imgUrl = `/api/page_image/${encodeURIComponent(currentDocumentResult.file_name)}/${page.page_number}`;
    pageImage.src = imgUrl;

    pageImage.onload = () => {
        renderBoundingBoxes(page);
    };
}

function renderBoundingBoxes(page) {
    bboxOverlay.innerHTML = "";
    if (!showBBoxes || !page.regions || page.regions.length === 0) return;

    const imgW = pageImage.clientWidth || page.width;
    const imgH = pageImage.clientHeight || page.height;
    const scaleX = imgW / page.width;
    const scaleY = imgH / page.height;

    page.regions.forEach(region => {
        const box = region.bbox || region.bounding_box;
        if (!box) return;

        const x0 = box.xmin !== undefined ? box.xmin : (box.x0 !== undefined ? box.x0 : 0);
        const y0 = box.ymin !== undefined ? box.ymin : (box.y0 !== undefined ? box.y0 : 0);
        const x1 = box.xmax !== undefined ? box.xmax : (box.x1 !== undefined ? box.x1 : 0);
        const y1 = box.ymax !== undefined ? box.ymax : (box.y1 !== undefined ? box.y1 : 0);

        const el = document.createElement("div");
        el.className = "bbox-rect";
        el.style.left = `${x0 * scaleX}px`;
        el.style.top = `${y0 * scaleY}px`;
        el.style.width = `${(x1 - x0) * scaleX}px`;
        el.style.height = `${(y1 - y0) * scaleY}px`;

        el.addEventListener("mouseenter", (e) => {
            ttType.textContent = region.category || "Text";
            ttConf.textContent = `${((region.confidence || 0.95) * 100).toFixed(0)}%`;
            ttText.textContent = region.text || "";
            bboxTooltip.style.display = "block";
            positionTooltip(e);
        });

        el.addEventListener("mousemove", (e) => {
            positionTooltip(e);
        });

        el.addEventListener("mouseleave", () => {
            bboxTooltip.style.display = "none";
        });

        bboxOverlay.appendChild(el);
    });
}

function positionTooltip(e) {
    const x = e.clientX + 12;
    const y = e.clientY + 12;
    bboxTooltip.style.left = `${Math.min(x, window.innerWidth - 320)}px`;
    bboxTooltip.style.top = `${Math.min(y, window.innerHeight - 100)}px`;
}

// ==========================================================================
// Studio Tab Views (Markdown, Table, JSON, Raw)
// ==========================================================================
function initTabs() {
    document.querySelectorAll(".tab-item").forEach(btn => {
        btn.addEventListener("click", () => {
            document.querySelectorAll(".tab-item").forEach(b => b.classList.remove("active"));
            document.querySelectorAll(".content-view").forEach(p => p.classList.remove("active"));

            btn.classList.add("active");
            const tabId = btn.getAttribute("data-tab");
            currentActiveTab = tabId;
            const target = document.getElementById(`tab-${tabId}`);
            if (target) target.classList.add("active");
        });
    });
}

function renderStudioViews() {
    if (!currentDocumentResult) return;

    const fullMd = currentDocumentResult.full_markdown || "";

    // 1. Formatted Markdown Tab
    if (window.marked) {
        markdownRendered.innerHTML = marked.parse(fullMd);
    } else {
        markdownRendered.innerHTML = `<pre>${escapeHtml(fullMd)}</pre>`;
    }

    // 2. Table Explorer Tab
    renderTablesView();

    // 3. JSON Tab
    jsonCodeViewer.textContent = JSON.stringify(currentDocumentResult, null, 2);

    // 4. Raw Text Tab
    rawTextViewer.value = fullMd;

    // Meta footer tags
    charCountTag.textContent = `${fullMd.length.toLocaleString()} chars`;
    const hasGujarati = /[\u0A80-\u0AFF]/.test(fullMd);
    const hasHindi = /[\u0900-\u097F]/.test(fullMd);
    let langDesc = "English";
    if (hasGujarati && hasHindi) langDesc = "English, Gujarati, Hindi";
    else if (hasGujarati) langDesc = "English, Gujarati";
    else if (hasHindi) langDesc = "English, Hindi";
    langDetectTag.textContent = `Scripts: ${langDesc}`;
}

function renderTablesView() {
    tablesContainer.innerHTML = "";
    let tableFound = false;

    if (currentDocumentResult && currentDocumentResult.pages) {
        currentDocumentResult.pages.forEach((page, pIdx) => {
            if (page.tables && page.tables.length > 0) {
                tableFound = true;
                page.tables.forEach((t, tIdx) => {
                    const card = document.createElement("div");
                    card.className = "table-card";
                    card.innerHTML = `
                        <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:6px;">
                            <span style="font-weight:600; font-size:0.78rem; color:var(--text-medium);">Page ${page.page_number} — Table #${tIdx + 1} (${t.rows}×${t.cols})</span>
                            <button class="btn-subtle" onclick="copyTableCsv(${pIdx}, ${tIdx})">CSV</button>
                        </div>
                        ${t.html || `<pre>${escapeHtml(t.markdown)}</pre>`}
                    `;
                    tablesContainer.appendChild(card);
                });
            }
        });
    }

    if (!tableFound) {
        const fullMd = currentDocumentResult.full_markdown || "";
        if (fullMd.includes("|")) {
            tablesContainer.innerHTML = marked.parse(fullMd);
        } else {
            tablesContainer.innerHTML = `
                <div class="empty-content-prompt">No structured tables detected in this document</div>
            `;
        }
    }
}

window.copyTableCsv = function(pIdx, tIdx) {
    try {
        const table = currentDocumentResult.pages[pIdx].tables[tIdx];
        if (table && table.cells) {
            let csv = "";
            for (let r = 0; r < table.rows; r++) {
                const rowCells = table.cells.filter(c => c.row_idx === r);
                csv += rowCells.map(c => `"${(c.text || "").replace(/"/g, '""')}"`).join(",") + "\n";
            }
            navigator.clipboard.writeText(csv);
            showToast("Table CSV copied");
        }
    } catch (e) {
        showToast("Could not copy table", true);
    }
};

// ==========================================================================
// Canvas Zoom & Page Controls
// ==========================================================================
function initCanvasControls() {
    prevPageBtn.addEventListener("click", () => {
        if (currentPageIndex > 0) {
            currentPageIndex--;
            renderCurrentPage();
        }
    });

    nextPageBtn.addEventListener("click", () => {
        if (currentDocumentResult && currentPageIndex < currentDocumentResult.total_pages - 1) {
            currentPageIndex++;
            renderCurrentPage();
        }
    });

    toggleBBoxCheckbox.addEventListener("change", (e) => {
        showBBoxes = e.target.checked;
        if (currentDocumentResult && currentDocumentResult.pages) {
            renderBoundingBoxes(currentDocumentResult.pages[currentPageIndex]);
        }
    });

    zoomInBtn.addEventListener("click", () => {
        currentZoom = Math.min(currentZoom + 0.15, 2.5);
        applyZoom();
    });

    zoomOutBtn.addEventListener("click", () => {
        currentZoom = Math.max(currentZoom - 0.15, 0.5);
        applyZoom();
    });

    zoomFitBtn.addEventListener("click", () => {
        currentZoom = 1.0;
        applyZoom();
    });
}

function applyZoom() {
    canvasStage.style.transform = `scale(${currentZoom})`;
    zoomLevelText.textContent = `${Math.round(currentZoom * 100)}%`;
}

// ==========================================================================
// Export Suite
// ==========================================================================
function initExportButtons() {
    copyCurrentTabBtn.addEventListener("click", () => {
        if (!currentDocumentResult) return;
        let content = "";
        if (currentActiveTab === "markdown" || currentActiveTab === "raw") {
            content = currentDocumentResult.full_markdown;
        } else if (currentActiveTab === "json") {
            content = JSON.stringify(currentDocumentResult, null, 2);
        } else if (currentActiveTab === "tables") {
            content = tablesContainer.innerText;
        }
        navigator.clipboard.writeText(content);
        showToast("Copied to clipboard");
    });

    downloadMdBtn.addEventListener("click", () => {
        if (!currentDocumentResult) return;
        downloadFile(`${getDocBaseName()}_extracted.md`, currentDocumentResult.full_markdown, "text/markdown");
    });

    downloadJsonBtn.addEventListener("click", () => {
        if (!currentDocumentResult) return;
        downloadFile(`${getDocBaseName()}_extracted.json`, JSON.stringify(currentDocumentResult, null, 2), "application/json");
    });
}

function downloadFile(filename, content, mimeType) {
    const blob = new Blob([content], { type: mimeType });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = filename;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
    showToast(`Downloaded ${filename}`);
}

function getDocBaseName() {
    if (!currentDocumentResult || !currentDocumentResult.file_name) return "document";
    return currentDocumentResult.file_name.replace(/\.[^/.]+$/, "");
}

// ==========================================================================
// Helpers & Toast
// ==========================================================================
function setStatus(msg, isBusy = false) {
    statusTextEl.textContent = msg;
    const dot = document.querySelector(".pulse-dot");
    if (dot) {
        dot.style.background = isBusy ? "var(--accent)" : "var(--success)";
    }
}

function showToast(msg, isError = false) {
    toast.textContent = msg;
    toast.style.background = isError ? "var(--accent-hover)" : "var(--text-high)";
    toast.style.color = isError ? "#ffffff" : "#000000";
    toast.classList.add("show");
    setTimeout(() => {
        toast.classList.remove("show");
    }, 2400);
}

function formatBytes(bytes) {
    if (bytes === 0) return "0 B";
    const k = 1024;
    const sizes = ["B", "KB", "MB", "GB"];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(1)) + " " + sizes[i];
}

function escapeHtml(str) {
    return (str || "").replace(/[&<>"']/g, function(m) {
        return {
            "&": "&amp;",
            "<": "&lt;",
            ">": "&gt;",
            '"': "&quot;",
            "'": "&#039;"
        }[m];
    });
}
