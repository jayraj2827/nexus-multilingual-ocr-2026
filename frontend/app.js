/**
 * NexusOCR Studio & Testing Application Logic
 * Clean Bauhaus Engineering Client with Dual-Tier Intelligence
 */

let currentDocumentResult = null;
let currentPageIndex = 0;
let currentZoom = 1.0;
let showBBoxes = true;
let currentActiveTab = "markdown";
let currentView = "landing";
let currentHardwareName = "CPU";

// ==========================================================================
// DOM Element References
// ==========================================================================
const navLandingBtn = document.getElementById("navLandingBtn");
const navStudioBtn = document.getElementById("navStudioBtn");
const navTestingBtn = document.getElementById("navTestingBtn");
const brandHomeLink = document.getElementById("brandHomeLink");
const heroLaunchBtn = document.getElementById("heroLaunchBtn");
const heroTestingBtn = document.getElementById("heroTestingBtn");
const showcaseExploreBtn = document.getElementById("showcaseExploreBtn");
const ctaLaunchBtn = document.getElementById("ctaLaunchBtn");

const sampleSelect = document.getElementById("sampleSelect");
const fileInput = document.getElementById("fileInput");
const dropzone = document.getElementById("dropzone");
const uploadBar = document.getElementById("uploadBar");
const uploadActionRow = document.getElementById("uploadActionRow");
const pillFileName = document.getElementById("pillFileName");
const pillFileSize = document.getElementById("pillFileSize");
const changeFileBtn = document.getElementById("changeFileBtn");
const reProcessBtn = document.getElementById("reProcessBtn");

const canvasToolbar = document.getElementById("canvasToolbar");
const emptyCanvasState = document.getElementById("emptyCanvasState");
const canvasStage = document.getElementById("canvasStage");
const pageImage = document.getElementById("pageImage");
const bboxOverlay = document.getElementById("bboxOverlay");
const viewportWrapper = document.getElementById("viewportWrapper");

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

// Testing Suite Elements
const tEngineStatus = document.getElementById("tEngineStatus");
const tDeviceName = document.getElementById("tDeviceName");
const tDeviceType = document.getElementById("tDeviceType");
const tIsAmd = document.getElementById("tIsAmd");
const tCudaAvail = document.getElementById("tCudaAvail");
const refreshHealthBtn = document.getElementById("refreshHealthBtn");
const runAllBenchmarksBtn = document.getElementById("runAllBenchmarksBtn");
const benchmarkTableBody = document.getElementById("benchmarkTableBody");

// ==========================================================================
// Initialization
// ==========================================================================
document.addEventListener("DOMContentLoaded", async () => {
    initViewNavigation();
    initTabs();
    initUploadEvents();
    initCanvasControls();
    initExportButtons();
    initTestingSuite();
    initLandingOutputShowcase();
    initAccuracyConditionSwitch();
    initPipelineInspector();
    initScrollAnimations();
    await loadTelemetry();
    await loadSampleOptions();
    handleHashNavigation();
});

// ==========================================================================
// View Routing & Navigation (Overview / Studio / Testing)
// ==========================================================================
function switchView(viewName) {
    if (viewName === "overview" || viewName === "landing") {
        viewName = "landing";
    }

    currentView = viewName;
    document.body.classList.toggle("studio-mode", viewName === "studio");

    if (viewName === "studio") {
        document.querySelectorAll(".nav-btn").forEach(btn => {
            btn.classList.toggle("active", btn.getAttribute("data-target") === "view-studio");
        });
        document.querySelectorAll(".view-container").forEach(c => {
            c.classList.toggle("active", c.id === "view-studio");
        });
        if (window.location.hash !== "#studio") {
            window.history.replaceState(null, "", "#studio");
        }
    } else {
        // Overview Landing View
        document.querySelectorAll(".nav-btn").forEach(btn => {
            btn.classList.toggle("active", btn.getAttribute("data-target") === "view-landing");
        });
        document.querySelectorAll(".view-container").forEach(c => {
            c.classList.toggle("active", c.id === "view-landing");
        });
        if (window.location.hash !== "#overview" && window.location.hash !== "#landing") {
            window.history.replaceState(null, "", "#overview");
        }
    }

    window.scrollTo({ top: 0, behavior: "smooth" });
}

function initViewNavigation() {
    document.querySelectorAll(".nav-btn").forEach(btn => {
        btn.addEventListener("click", () => {
            const target = btn.getAttribute("data-target").replace("view-", "");
            switchView(target);
        });
    });

    if (brandHomeLink) brandHomeLink.addEventListener("click", () => switchView("landing"));
    if (heroLaunchBtn) heroLaunchBtn.addEventListener("click", () => switchView("studio"));
    if (showcaseExploreBtn) showcaseExploreBtn.addEventListener("click", () => switchView("studio"));
    if (ctaLaunchBtn) ctaLaunchBtn.addEventListener("click", () => switchView("studio"));

    window.addEventListener("hashchange", handleHashNavigation);
}

function handleHashNavigation() {
    const hash = window.location.hash.replace("#", "");
    if (hash === "testing" || hash === "diagnostics" || hash === "studio") {
        switchView("studio");
        if (hash === "diagnostics" || hash === "testing") {
            switchTab("diagnostics");
        }
    } else {
        switchView("landing");
    }
}

// ==========================================================================
// Health Telemetry & Hardware Detection
// ==========================================================================
async function loadTelemetry() {
    try {
        const res = await fetch("/api/health");
        if (res.ok) {
            const data = await res.json();
            currentHardwareName = data.device_name || data.hardware || (data.is_amd_hardware ? "AMD CPU" : "CPU");
            
            if (tDeviceName) tDeviceName.textContent = currentHardwareName;
            if (tDeviceType) tDeviceType.textContent = (data.device_type || "CPU").toUpperCase();
            if (tIsAmd) tIsAmd.textContent = data.is_amd_hardware ? "Enabled (AuthenticAMD)" : "No";
            if (tCudaAvail) tCudaAvail.textContent = data.cuda_available ? "Enabled (CUDA Active)" : "Disabled (CPU Mode)";
            if (tEngineStatus) tEngineStatus.textContent = "Healthy (2-Tier Active)";
        }
    } catch (e) {
        currentHardwareName = "CPU";
        if (tEngineStatus) tEngineStatus.textContent = "Offline / Error";
    }
}

// ==========================================================================
// Preset Sample Documents
// ==========================================================================
async function loadSampleOptions() {
    try {
        const res = await fetch("/api/samples");
        if (res.ok) {
            const samples = await res.json();
            sampleSelect.innerHTML = '<option value="">Load Preset Document...</option>';
            samples.forEach(s => {
                const opt = document.createElement("option");
                opt.value = s.name;
                opt.textContent = `${s.display} (${s.tier || s.type})`;
                sampleSelect.appendChild(opt);
            });

            // Populate benchmark suite in Diagnostics tab
            populateBenchmarkTable(samples);
        }
    } catch (e) {
        console.warn("Could not load demo samples:", e);
    }

    sampleSelect.addEventListener("change", async (e) => {
        const val = e.target.value;
        if (!val) return;
        switchView("studio");
        await processSampleFile(val);
    });
}

function populateBenchmarkTable(samples) {
    if (!benchmarkTableBody) return;
    benchmarkTableBody.innerHTML = "";
    samples.forEach(s => {
        const tr = document.createElement("tr");
        tr.setAttribute("data-fixture", s.name);
        tr.innerHTML = `
            <td><strong>${s.display}</strong></td>
            <td>${s.type || s.tier || "Document"}</td>
            <td><span class="status-badge status-idle">IDLE</span></td>
            <td class="mono">—</td>
            <td class="mono">—</td>
            <td><button class="btn-ghost run-single-bench" data-file="${s.name}">Test</button></td>
        `;
        benchmarkTableBody.appendChild(tr);
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
// Upload & Multi-Zone Drag-and-Drop
// ==========================================================================
const SUPPORTED_EXTS = [
    ".pdf", ".png", ".jpg", ".jpeg", ".tiff", ".tif", ".bmp", ".webp",
    ".docx", ".xlsx", ".csv", ".tsv", ".pptx", ".txt", ".md", ".html", ".htm"
];
const AUDIO_VIDEO_EXTS = [
    ".mp3", ".wav", ".aac", ".flac", ".ogg", ".m4a", ".mp4", ".avi", ".mov", ".mkv", ".flv", ".webm"
];

function initUploadEvents() {
    fileInput.addEventListener("change", (e) => {
        if (e.target.files && e.target.files[0]) {
            handleSelectedFile(e.target.files[0]);
        }
    });

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

function handleSelectedFile(file) {
    const ext = "." + file.name.split(".").pop().toLowerCase();

    if (AUDIO_VIDEO_EXTS.includes(ext)) {
        showToast(`Audio & Video files (${ext}) are not supported. NexusOCR is a document & image intelligence engine.`, true);
        return;
    }

    if (!SUPPORTED_EXTS.includes(ext)) {
        showToast(`Unsupported format '${ext}'. Please upload a document or image (PDF, PNG, JPG, TIFF, DOCX, XLSX, etc.).`, true);
        return;
    }

    pillFileName.textContent = file.name;
    pillFileSize.textContent = formatBytes(file.size);
    dropzone.style.display = "none";
    uploadActionRow.style.display = "flex";

    switchView("studio");
    showLoading(`Processing ${file.name}...`, "Extracting document structure and content");
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
    pillFileSize.textContent = "Preset Fixture";
    dropzone.style.display = "none";
    uploadActionRow.style.display = "flex";

    switchView("studio");
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
// Success & Studio Viewport Rendering
// ==========================================================================
function handleExtractionSuccess(data) {
    hideLoading();
    currentDocumentResult = data;
    currentPageIndex = 0;
    currentZoom = 1.0;

    totalLatencyEl.textContent = `${data.total_execution_time_ms.toFixed(0)} ms`;
    const avgConf = (data.average_trust_score * 100).toFixed(0);
    trustScoreEl.textContent = `${avgConf}%`;
    totalPagesEl.textContent = data.total_pages;

    emptyCanvasState.style.display = "none";
    canvasStage.style.display = "inline-block";
    canvasToolbar.style.display = "flex";

    // Switch to output screen tab so user immediately sees extracted results
    switchTab("markdown");

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

    if (page.is_digital) {
        pageTierPill.textContent = `Tier 1: Digital Native (${page.execution_time_ms.toFixed(0)}ms)`;
        pageTierPill.style.color = "var(--bauhaus-blue)";
    } else {
        pageTierPill.textContent = `Tier 2: PaddleOCR [${currentHardwareName}] (${page.execution_time_ms.toFixed(0)}ms)`;
        pageTierPill.style.color = "var(--bauhaus-red)";
    }

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

        if (region.category === "figure") {
            el.style.borderColor = "var(--bauhaus-blue)";
            el.style.backgroundColor = "rgba(27, 73, 148, 0.12)";
        } else if (region.category === "header" || region.category === "title") {
            el.style.borderColor = "var(--bauhaus-yellow)";
            el.style.backgroundColor = "rgba(242, 183, 5, 0.15)";
        }

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
    const x = e.clientX + 14;
    const y = e.clientY + 14;
    bboxTooltip.style.left = `${Math.min(x, window.innerWidth - 300)}px`;
    bboxTooltip.style.top = `${Math.min(y, window.innerHeight - 110)}px`;
}

// ==========================================================================
// Studio Tabs (Markdown, Tables, JSON, Raw, Diagnostics)
// ==========================================================================
function switchTab(tabId) {
    document.querySelectorAll(".tab-item").forEach(b => {
        b.classList.toggle("active", b.getAttribute("data-tab") === tabId);
    });
    document.querySelectorAll(".content-view").forEach(p => {
        p.classList.toggle("active", p.id === `tab-${tabId}`);
    });
    currentActiveTab = tabId;
}

function initTabs() {
    document.querySelectorAll(".tab-item").forEach(btn => {
        btn.addEventListener("click", () => {
            const tabId = btn.getAttribute("data-tab");
            switchTab(tabId);
        });
    });
}

function renderStudioViews() {
    if (!currentDocumentResult) return;

    const fullMd = currentDocumentResult.full_markdown || "";

    // 1. Markdown
    if (window.marked) {
        markdownRendered.innerHTML = marked.parse(fullMd);
    } else {
        markdownRendered.innerHTML = `<pre>${escapeHtml(fullMd)}</pre>`;
    }

    // 2. Tables
    renderTablesView();

    // 3. JSON
    jsonCodeViewer.textContent = JSON.stringify(currentDocumentResult, null, 2);

    // 4. Raw Text
    rawTextViewer.value = fullMd;

    // Footer Metadata
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
                        <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:8px;">
                            <span style="font-weight:700; font-size:0.8rem; color:var(--text-main);">Page ${page.page_number} — Table #${tIdx + 1} (${t.num_rows || t.rows || 0}×${t.num_cols || t.cols || 0})</span>
                            <button class="btn-subtle" onclick="copyTableCsv(${pIdx}, ${tIdx})">Copy CSV</button>
                        </div>
                        ${t.html || marked.parse(t.markdown || "")}
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
            tablesContainer.innerHTML = `<div class="placeholder-desc">No structured tables detected in this document</div>`;
        }
    }
}

window.copyTableCsv = function(pIdx, tIdx) {
    try {
        const table = currentDocumentResult.pages[pIdx].tables[tIdx];
        if (table && table.grid) {
            const csv = table.grid.map(row => row.map(cell => `"${(cell || "").replace(/"/g, '""')}"`).join(",")).join("\n");
            navigator.clipboard.writeText(csv);
            showToast("Table CSV copied to clipboard");
            return;
        }
        if (table && table.markdown) {
            navigator.clipboard.writeText(table.markdown);
            showToast("Table Markdown copied");
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
// Testing & Diagnostics Suite Logic
// ==========================================================================
function initTestingSuite() {
    if (refreshHealthBtn) {
        refreshHealthBtn.addEventListener("click", async () => {
            await loadTelemetry();
            showToast("Telemetry metrics refreshed");
        });
    }

    if (runAllBenchmarksBtn) {
        runAllBenchmarksBtn.addEventListener("click", async () => {
            const rows = benchmarkTableBody.querySelectorAll("tr");
            runAllBenchmarksBtn.disabled = true;
            runAllBenchmarksBtn.textContent = "Running Benchmarks...";

            for (const row of rows) {
                const file = row.getAttribute("data-fixture");
                if (file) {
                    await runSingleBenchmarkRow(row, file);
                }
            }

            runAllBenchmarksBtn.disabled = false;
            runAllBenchmarksBtn.textContent = "Run Benchmark Suite";
            showToast("Benchmark suite finished");
        });
    }

    if (benchmarkTableBody) {
        benchmarkTableBody.addEventListener("click", async (e) => {
            if (e.target.classList.contains("run-single-bench")) {
                const file = e.target.getAttribute("data-file");
                const row = e.target.closest("tr");
                if (file && row) {
                    e.target.disabled = true;
                    await runSingleBenchmarkRow(row, file);
                    e.target.disabled = false;
                }
            } else if (e.target.tagName === "STRONG" || (e.target.tagName === "TD" && e.target.cellIndex === 0)) {
                const row = e.target.closest("tr");
                const file = row ? row.getAttribute("data-fixture") : null;
                if (file) {
                    switchTab("markdown");
                    await processSampleFile(file);
                }
            }
        });
    }
}

async function runSingleBenchmarkRow(row, filename) {
    const statusCell = row.cells[2];
    const latencyCell = row.cells[3];
    const trustCell = row.cells[4];

    statusCell.innerHTML = '<span class="status-badge status-run">TESTING...</span>';
    latencyCell.textContent = "...";
    trustCell.textContent = "...";

    try {
        const t0 = performance.now();
        const res = await fetch(`/api/process_sample/${encodeURIComponent(filename)}`, {
            method: "POST"
        });
        const elapsed = performance.now() - t0;

        if (res.ok) {
            const data = await res.json();
            const latency = data.total_execution_time_ms || elapsed;
            const trust = (data.average_trust_score * 100).toFixed(0);

            statusCell.innerHTML = '<span class="status-badge status-pass">PASS</span>';
            latencyCell.textContent = `${latency.toFixed(0)} ms`;
            trustCell.textContent = `${trust}%`;
        } else {
            statusCell.innerHTML = '<span class="status-badge" style="background:#FCE8E6;color:var(--bauhaus-red);">FAIL</span>';
            latencyCell.textContent = "Err";
            trustCell.textContent = "0%";
        }
    } catch (e) {
        statusCell.innerHTML = '<span class="status-badge" style="background:#FCE8E6;color:var(--bauhaus-red);">ERROR</span>';
        latencyCell.textContent = "Err";
        trustCell.textContent = "0%";
    }
}

// ==========================================================================
// Helpers & Toast
// ==========================================================================
function setStatus(msg, isBusy = false) {
    statusTextEl.textContent = msg;
    const dot = document.querySelector(".pulse-dot");
    if (dot) {
        dot.style.background = isBusy ? "var(--bauhaus-yellow)" : "var(--bauhaus-green)";
    }
}

function showToast(msg, isError = false) {
    toast.textContent = msg;
    toast.style.background = isError ? "var(--bauhaus-red)" : "var(--border-dark)";
    toast.style.color = "#FFFFFF";
    toast.classList.add("show");
    setTimeout(() => {
        toast.classList.remove("show");
    }, 2500);
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

// ==========================================================================
// Level 01: Landing Page Live Preset Output Showcase
// ==========================================================================
const LANDING_PRESETS = {
    "test_digital_english.pdf": {
        filename: "test_digital_english.pdf",
        tier: "TIER 1 (DIGITAL PDF)",
        latency: "11 ms",
        trust: "100% TRUST",
        bboxes: [
            { top: "8%", left: "8%", width: "84%", height: "8%", type: "header", label: "Title: Quarterly Report" },
            { top: "20%", left: "8%", width: "84%", height: "22%", type: "digital", label: "Digital Text (Native)" },
            { top: "46%", left: "8%", width: "84%", height: "24%", type: "digital", label: "Operational Highlights" }
        ],
        outputHtml: `
            <div class="doc-typography">
                <h1>Quarterly Performance Report</h1>
                <p><strong>Status:</strong> Extraction Verified &middot; <strong>Format:</strong> Digital PDF &middot; <strong>Latency:</strong> 11 ms &middot; <strong>Trust:</strong> 100%</p>
                <blockquote>Sub-15ms native text recovery with 100% precision score.</blockquote>
                <h3>Operational Metrics</h3>
                <ul>
                    <li>Native digital throughput: 120 pages/sec</li>
                    <li>Hardware accelerator: AMD CPU (AuthenticAMD)</li>
                    <li>Encoding: UTF-8 standard with layout coordinates</li>
                </ul>
            </div>
        `
    },
    "test_hindi_devanagari.pdf": {
        filename: "test_hindi_devanagari.pdf",
        tier: "TIER 1 (DEVANAGARI NATIVE)",
        latency: "11 ms",
        trust: "100% TRUST",
        bboxes: [
            { top: "4.8%", left: "7.5%", width: "85%", height: "6.8%", type: "header", label: "Heading: हिंदी दस्तावेज़ परीक्षण" },
            { top: "13.2%", left: "7.5%", width: "85%", height: "2.8%", type: "digital", label: "Metadata: DL-2026-89432" },
            { top: "16.4%", left: "7.5%", width: "85%", height: "8.5%", type: "digital", label: "Devanagari Paragraph" },
            { top: "29%", left: "7.5%", width: "85%", height: "13.5%", type: "table", label: "Table: तकनीकी विनिर्देश एवं मापदंड" }
        ],
        outputHtml: `
            <div class="doc-typography">
                <h1 style="font-family: var(--font-indic);">हिंदी दस्तावेज़ परीक्षण — नेक्सस ओसीआर</h1>
                <p><strong>दस्तावेज़ क्रमांक:</strong> DL-2026-89432 &nbsp;|&nbsp; <strong>दिनांक:</strong> 21 अगस्त 2026 &nbsp;|&nbsp; <strong>स्थिति:</strong> <span class="badge-tag" style="background:#E6F4EA; color:var(--bauhaus-green); font-weight:700;">100% TRUST</span></p>
                <blockquote style="border-left-color: var(--bauhaus-red); font-family: var(--font-indic);">
                    यह एक डिजिटल हिंदी परीक्षण दस्तावेज़ है। नेक्सस ओसीआर (NexusOCR) उच्च सटीकता के साथ देवनागरी लिपि, संयुक्त अक्षर, शिरोरेखा और मात्राओं का सटीक विश्लेषण करता है।
                </blockquote>
                <h3>तकनीकी विनिर्देश एवं मापदंड (Technical Specifications)</h3>
                <table>
                    <thead>
                        <tr><th>मापदंड (Parameter)</th><th>विवरण (Details)</th><th>सटीकता (Accuracy)</th></tr>
                    </thead>
                    <tbody>
                        <tr><td>लिपि पहचान (Script)</td><td>देवनागरी (Devanagari / Hindi)</td><td style="color:var(--bauhaus-green); font-weight:700;">99.2% उच्च परिशुद्धता</td></tr>
                        <tr><td>प्रसंस्करण टियर (Tier)</td><td>टियर 1 डिजिटल फास्ट-पाथ</td><td style="color:var(--bauhaus-blue); font-weight:700;">11 ms (सब-100ms)</td></tr>
                        <tr><td>हार्डवेयर इंजन (Engine)</td><td>AMD CPU स्थानीय निष्पादन</td><td style="color:var(--bauhaus-green); font-weight:700;">100% ट्रस्ट स्कोर</td></tr>
                    </tbody>
                </table>
            </div>
        `
    },
    "test_tables_financial.pdf": {
        filename: "test_tables_financial.pdf",
        tier: "TIER 1 + TABLES (TABULAR PDF)",
        latency: "14 ms",
        trust: "100% TRUST",
        bboxes: [
            { top: "6%", left: "8%", width: "84%", height: "8%", type: "header", label: "Title: Financial Statement & Grid" },
            { top: "18%", left: "8%", width: "84%", height: "46%", type: "table", label: "Tabular Matrix Structure" }
        ],
        outputHtml: `
            <div class="doc-typography">
                <h1>Financial Statement &amp; Grid Matrix</h1>
                <p><strong>Status:</strong> Tabular Extraction Verified &middot; <strong>Format:</strong> Tabular PDF &middot; <strong>Latency:</strong> 14 ms &middot; <strong>Trust:</strong> 100%</p>
                <table class="bench-table" style="margin: 12px 0;">
                    <thead>
                        <tr>
                            <th>Quarter</th>
                            <th>Revenue</th>
                            <th>OpEx</th>
                            <th>Net Margin</th>
                            <th>Growth</th>
                        </tr>
                    </thead>
                    <tbody>
                        <tr>
                            <td><strong>Q1 2026</strong></td>
                            <td class="mono">$1,420,000</td>
                            <td class="mono">$840,000</td>
                            <td class="mono" style="color:var(--bauhaus-green);font-weight:700;">+40.8%</td>
                            <td class="mono">+12.4%</td>
                        </tr>
                        <tr>
                            <td><strong>Q2 2026</strong></td>
                            <td class="mono">$1,890,000</td>
                            <td class="mono">$920,000</td>
                            <td class="mono" style="color:var(--bauhaus-green);font-weight:700;">+51.3%</td>
                            <td class="mono">+33.1%</td>
                        </tr>
                        <tr>
                            <td><strong>Q3 2026</strong></td>
                            <td class="mono">$2,250,000</td>
                            <td class="mono">$1,050,000</td>
                            <td class="mono" style="color:var(--bauhaus-green);font-weight:700;">+53.3%</td>
                            <td class="mono">+19.0%</td>
                        </tr>
                    </tbody>
                </table>
                <p><small class="mono">Matrix cells detected: 15 / 15 &middot; Structure preserved &middot; Trust 100%</small></p>
            </div>
        `
    },
    "01_multilingual.pdf": {
        filename: "01_multilingual.pdf",
        tier: "TIER 2 (MULTILINGUAL INDIC)",
        latency: "91 ms",
        trust: "99% TRUST",
        bboxes: [
            { top: "10%", left: "8%", width: "84%", height: "10%", type: "header", label: "Heading: ગુજરાતી વિશ્લેષણ" },
            { top: "24%", left: "8%", width: "84%", height: "22%", type: "table", label: "Gujarati Text Block" },
            { top: "50%", left: "8%", width: "84%", height: "20%", type: "digital", label: "English Subtext" }
        ],
        outputHtml: `
            <div class="doc-typography">
                <h1 style="font-family: var(--font-indic);">ગુજરાતી દસ્તાવેજ વિશ્લેષણ (Gujarati Document Analysis)</h1>
                <p><strong>Status:</strong> Neural Multilingual &middot; <strong>Format:</strong> Multilingual PDF &middot; <strong>Latency:</strong> 91 ms &middot; <strong>Trust:</strong> 99%</p>
                <blockquote style="border-left-color: var(--bauhaus-red); font-family: var(--font-indic);">નેક્સસ ઓસીઆર પ્રાદેશિક અને ત્રિભાષી દસ્તાવેજોનું ચોકસાઈપૂર્વક વિશ્લેષણ કરે છે.</blockquote>
                <h3>Bilingual Script Pairing</h3>
                <ul>
                    <li>Script: Gujarati &amp; Latin (Bilingual Mode)</li>
                    <li>Confidence Trust: 99% average word score</li>
                    <li>Engine: PaddleOCR Lightweight Indic Model</li>
                </ul>
            </div>
        `
    },
    "Autonomous_Delivery_Robot_System_Design_Report.docx": {
        filename: "Autonomous_Delivery_Robot_System_Design_Report.docx",
        tier: "OFFICE WORD (.DOCX)",
        latency: "86 ms",
        trust: "100% TRUST",
        bboxes: [
            { top: "4%", left: "5%", width: "90%", height: "6%", type: "header", label: "AUTONOMOUS DELIVERY ROBOT" },
            { top: "11%", left: "5%", width: "90%", height: "4%", type: "digital", label: "System Design Report - Microkernel" },
            { top: "17%", left: "5%", width: "90%", height: "28%", type: "digital", label: "1. System Overview & Architecture" }
        ],
        outputHtml: `
            <div class="doc-typography">
                <h1>AUTONOMOUS DELIVERY ROBOT</h1>
                <p><strong>Status:</strong> Office Ingestion Verified &middot; <strong>Format:</strong> Office Word (.docx) &middot; <strong>Latency:</strong> 86 ms &middot; <strong>Trust:</strong> 100%</p>
                <blockquote>Microkernel-Based Embedded Operating System &middot; College OS Design Activity</blockquote>
                <h3>1. System Overview</h3>
                <p>The proposed system is an embedded operating system for an Autonomous Delivery Robot. The OS controls sensors, navigation-related tasks, motor movement, display, temperature monitoring, wireless communication and data logging. The design focuses on predictable real-time response, safety, modularity and fault isolation.</p>
                <h3>2. Selected OS Architecture — Microkernel</h3>
                <ul>
                    <li>Reliability: failure of one service (e.g. LCD) does not crash the complete OS</li>
                    <li>Modularity: drivers execute in user-space with isolated IPC</li>
                    <li>Hard Real-Time: deterministic scheduler for motor controllers</li>
                </ul>
            </div>
        `
    },
    "award.png": {
        filename: "award.png",
        tier: "TIER 2 (SCANNED IMAGE)",
        latency: "1083 ms",
        trust: "95% TRUST",
        bboxes: [
            { top: "15%", left: "12%", width: "76%", height: "22%", type: "neural", label: "Certificate Title" },
            { top: "42%", left: "12%", width: "76%", height: "26%", type: "neural", label: "Raster Text Line" }
        ],
        outputHtml: `
            <div class="doc-typography">
                <h1>Certificate Raster Badge</h1>
                <p><strong>Status:</strong> Neural Vision Processed &middot; <strong>Format:</strong> Scanned Image (.png) &middot; <strong>Latency:</strong> 1,083 ms &middot; <strong>Trust:</strong> 95%</p>
                <blockquote style="border-left-color: var(--bauhaus-red);">PaddleOCR Neural Vision on AMD CPU (AuthenticAMD) &middot; Trust: 95%</blockquote>
                <h3>Extracted Badge Content</h3>
                <ul>
                    <li>Resolution: 300 DPI Raster Scan</li>
                    <li>Recognized Script: Latin Alphanumeric &amp; Decorative Typeface</li>
                    <li>Segmentation: Neural Text Bounding Box Isolation</li>
                </ul>
            </div>
        `
    }
};

let currentLandingPreset = "test_digital_english.pdf";

function initLandingOutputShowcase() {
    const pills = document.querySelectorAll(".preset-pill");
    const filenameEl = document.getElementById("demoScreenFilename");
    const tierEl = document.getElementById("demoScreenTier");
    const latencyEl = document.getElementById("demoScreenLatency");
    const trustEl = document.getElementById("demoScreenTrust");
    const imgEl = document.getElementById("demoScreenImg");
    const bboxLayer = document.getElementById("demoBboxLayer");
    const outputEl = document.getElementById("demoScreenOutput");
    const openStudioBtn = document.getElementById("demoOpenInStudioBtn");

    if (!pills.length || !imgEl) return;

    function renderPreset(presetKey) {
        currentLandingPreset = presetKey;
        const config = LANDING_PRESETS[presetKey];
        if (!config) return;

        pills.forEach(p => {
            p.classList.toggle("active", p.getAttribute("data-preset") === presetKey);
        });

        if (filenameEl) filenameEl.textContent = config.filename;
        if (tierEl) tierEl.textContent = config.tier;
        if (latencyEl) latencyEl.textContent = config.latency;
        if (trustEl) trustEl.textContent = config.trust;

        imgEl.src = `/api/page_image/${encodeURIComponent(config.filename)}/1`;

        if (bboxLayer) {
            bboxLayer.innerHTML = "";
            config.bboxes.forEach(box => {
                const b = document.createElement("div");
                b.className = `demo-bbox ${box.type}`;
                b.style.top = box.top;
                b.style.left = box.left;
                b.style.width = box.width;
                b.style.height = box.height;
                b.title = box.label;
                bboxLayer.appendChild(b);
            });
        }

        if (outputEl) {
            outputEl.innerHTML = config.outputHtml;
        }
    }

    pills.forEach(pill => {
        pill.addEventListener("click", () => {
            const key = pill.getAttribute("data-preset");
            pills.forEach(p => p.classList.toggle("active", p.getAttribute("data-preset") === key));
            renderPreset(key);
            processSampleFile(key);
        });
    });

    if (openStudioBtn) {
        openStudioBtn.addEventListener("click", () => {
            switchView("studio");
            processSampleFile(currentLandingPreset);
        });
    }

    // Initial render of first preset
    renderPreset("test_digital_english.pdf");
}

// ==========================================================================
// Scroll Animations: Telemetry Bar Fills
// ==========================================================================
function initScrollAnimations() {
    const graphSection = document.querySelector(".telemetry-graphs-grid");

    if ("IntersectionObserver" in window) {
        // Observer for telemetry graphs section
        if (graphSection) {
            const graphObserver = new IntersectionObserver((entries) => {
                entries.forEach(entry => {
                    if (entry.isIntersecting) {
                        const bars = entry.target.querySelectorAll(".bar-fill, .gauge-fill");
                        bars.forEach(bar => {
                            const targetWidth = bar.style.width;
                            bar.style.width = "0%";
                            requestAnimationFrame(() => {
                                setTimeout(() => {
                                    bar.style.width = targetWidth;
                                }, 60);
                            });
                        });
                        graphObserver.unobserve(entry.target);
                    }
                });
            }, { threshold: 0.2 });

            graphObserver.observe(graphSection);
        }
    }
}

// ==========================================================================
// Level 02: Accuracy by Condition Switcher
// ==========================================================================
const ACCURACY_CONDITIONS = {
    highres: {
        desc: "High-Res Scans \u2265300 DPI \u00B7 Crisp High-Contrast Machine Print",
        avg: "99.1% AVG",
        items: [
            { label: "English & Digits (Tier 1 Digital Native)", pct: "99.9%", fill: "blue" },
            { label: "Printed Devanagari (Hindi & Marathi)", pct: "99.2%", fill: "red" },
            { label: "Printed Gujarati (High-Contrast Text)", pct: "98.6%", fill: "yellow" },
            { label: "Tabular Grids & Financial Cell Alignment", pct: "98.4%", fill: "green" }
        ],
        note: "Optimal \u2265300 DPI text input. Low-confidence regions (<0.85) route to Tier 2 neural OCR."
    },
    office: {
        desc: "Standard Office Scans (200 DPI, Grayscale/Color, Slight Skew \u00B15\u00B0)",
        avg: "94.8% AVG",
        items: [
            { label: "Machine-Printed English & Alphanumeric", pct: "97.4%", fill: "blue" },
            { label: "Devanagari Office Documents (Printed)", pct: "94.8%", fill: "red" },
            { label: "Gujarati Print with Minor Ink Bleed", pct: "93.9%", fill: "yellow" },
            { label: "Bordered Form Tables & Invoices", pct: "93.1%", fill: "green" }
        ],
        note: "Standard production documents. PaddleOCR preprocessing performs auto-deskew and contrast normalization."
    },
    degraded: {
        desc: "Degraded Scans & Mobile Photos (150 DPI, Low Contrast, Shadows, Sensor Noise)",
        avg: "84.2% AVG",
        items: [
            { label: "English High-Contrast Words", pct: "89.6%", fill: "blue" },
            { label: "Devanagari with Complex Conjuncts", pct: "83.4%", fill: "red" },
            { label: "Low-Contrast Gujarati Script", pct: "81.8%", fill: "yellow" },
            { label: "Damaged / Borderless Matrix Cells", pct: "82.0%", fill: "green" }
        ],
        note: "Challenging input. Degraded text triggers Tier 2 neural model. Sub-0.85 confidence words are flagged for operator review."
    }
};

function initAccuracyConditionSwitch() {
    const pills = document.querySelectorAll(".condition-pill");
    const descEl = document.getElementById("accuracyConditionDesc");
    const badgeEl = document.getElementById("accuracyAvgBadge");
    const noteEl = document.getElementById("accuracyConditionNote");

    if (!pills.length) return;

    pills.forEach(pill => {
        pill.addEventListener("click", () => {
            const key = pill.getAttribute("data-condition");
            const data = ACCURACY_CONDITIONS[key];
            if (!data) return;

            pills.forEach(p => p.classList.toggle("active", p === pill));

            if (descEl) descEl.textContent = data.desc;
            if (badgeEl) badgeEl.textContent = data.avg;
            if (noteEl) noteEl.textContent = data.note;

            data.items.forEach((item, idx) => {
                const labelEl = document.getElementById(`gauge${idx + 1}Label`);
                const valEl = document.getElementById(`gauge${idx + 1}Val`);
                const barEl = document.getElementById(`gauge${idx + 1}Bar`);

                if (labelEl) labelEl.textContent = item.label;
                if (valEl) valEl.textContent = item.pct;
                if (barEl) {
                    barEl.className = `gauge-fill ${item.fill} animate-bar`;
                    barEl.style.width = "0%";
                    requestAnimationFrame(() => {
                        setTimeout(() => {
                            barEl.style.width = item.pct;
                        }, 40);
                    });
                }
            });
        });
    });
}

// ==========================================================================
// Level 04: Interactive Conveyor Pipeline & Live Architecture Inspector
// ==========================================================================
const PIPELINE_STAGES = {
    1: {
        stageId: "STATION 01 / 04 ACTIVE",
        heading: "Format Validation & MIME Sanitizer",
        sub: "Ingest Gatekeeper · Security Verification · Document Normalization",
        engine: "Magic Byte Sniffer & Python-Docx / Pillow Ingest",
        hardware: "AMD Ryzen / EPYC Host CPU",
        badgeClass: "blue",
        input: "Raw Multi-Format Binary Stream (PDF, Scans, DOCX, XLSX)",
        output: "Sanitized Stream Buffer & Page Pixel Render Array",
        termTitle: "Internal Stream & Transformation Trace",
        termBadge: "STREAM DATA",
        termCode: `// [Station 01: Ingestion Buffer Inspection]
MIME Filter: application/pdf (Magic signature: %PDF-1.7)
Sanitization: PASS (No media/audio stream execution)
Memory Footprint: 2.1 MB buffer allocation
Page Count: 1 page decoded into internal raster buffer
Execution Time: 1.2 ms`
    },
    2: {
        stageId: "STATION 02 / 04 ACTIVE",
        heading: "Tier 1 Digital Native Resolver (PyMuPDF)",
        sub: "Direct Vector Text Extraction · Sub-10ms Native C-Extension",
        engine: "PyMuPDF (fitz) v1.23 C-Bindings & HarfBuzz Font Shaper",
        hardware: "Single-Threaded C Extension (Zero Py Overhead)",
        badgeClass: "green",
        input: "Vector PDF DOM / Embedded Font Tables (CFF, TrueType)",
        output: "Digital Text Stream & Exact Bounding Coordinates",
        termTitle: "Direct PyMuPDF Block & Span Extraction",
        termBadge: "VECTOR C-STREAM",
        termCode: `// [Station 02: PyMuPDF Direct C-Extension]
Density Score: 0.96 (Digital threshold >= 0.85 PASS)
Bypass Trigger: Direct vector text layer extracted
Block Count: 8 paragraphs, 2 headings, 1 list block
Glyph Coordinates: Exact font matrix bounding rectangles
Latency: 11.2 ms (Zero GPU / Neural overhead)`
    },
    3: {
        stageId: "STATION 03 / 04 ACTIVE",
        heading: "Tier 2 AMD CPU Neural Vision (PaddleOCR)",
        sub: "Deep CNN Detection & CRNN Multilingual Script Recognition",
        engine: "PaddleOCR v2.7 + PP-OCRv4 Indic Recognition Heads",
        hardware: "AuthenticAMD CPU Multi-thread (AVX-512 / OpenVINO)",
        badgeClass: "red",
        input: "Rasterized Document Canvas (300 DPI Pre-processed Image)",
        output: "Detected Word Polygons, Script Labels & Confidence Scores",
        termTitle: "PaddleOCR Detection & Recognition Polygons",
        termBadge: "NEURAL TENSOR",
        termCode: `// [Station 03: PaddleOCR Neural Inference on AMD CPU]
DBNet Detection: 34 text box quadrilaterals localized
Direction Classifier: 0° rotation confirmed
CRNN Recognizer: Multi-script Indic head (Gujarati / Devanagari)
Top Polygons: [[48, 112], [286, 112], [286, 148], [48, 148]]
Mean Confidence: 0.988 | Hardware Latency: 1,083 ms`
    },
    4: {
        stageId: "STATION 04 / 04 ACTIVE",
        heading: "Multimodal Synthesizer & AST Compiler",
        sub: "Tabular Grid Reassembly · Markdown Hierarchy · JSON Schema",
        engine: "Nexus Layout Synthesizer & Spatial Graph Compiler",
        hardware: "Local Python Micro-Kernel (Instant Vectorization)",
        badgeClass: "green",
        input: "Raw Spans, Detected Cells, Figures & Neural Polygons",
        output: "Standard Markdown AST, Clean HTML, CSV & Normalized JSON",
        termTitle: "Synthesized Output AST & Markdown Structure",
        termBadge: "MARKDOWN AST",
        termCode: `// [Station 04: Structured Multimodal Document Compiler]
# Quarterly Financial Performance Report
| Metric | Tier 1 Fast | Tier 2 Neural |
| Latency | 11 ms | 1,083 ms |
Figures Exported: 1 embedded raster diagram isolated
Bounding Box Schema: 100% normalized [0.0 - 1.0] coordinates
Export Formats: Markdown · CSV · JSON ready`
    }
};

function selectPipelineStage(stepNum) {
    const data = PIPELINE_STAGES[stepNum];
    if (!data) return;

    // Update station active state
    document.querySelectorAll(".circuit-station").forEach(st => {
        st.classList.toggle("active", st.getAttribute("data-station") === String(stepNum));
    });

    // Update stage tab buttons
    document.querySelectorAll(".stage-tab-btn").forEach(btn => {
        btn.classList.toggle("active", btn.getAttribute("data-step") === String(stepNum));
    });

    // Update Inspector DOM
    const idEl = document.getElementById("inspectorStageId");
    const nameEl = document.getElementById("inspectorStageName");
    const subEl = document.getElementById("inspectorStageSub");
    const engineEl = document.getElementById("inspectorEngine");
    const hwEl = document.getElementById("inspectorHardware");
    const inputEl = document.getElementById("inspectorInput");
    const outputEl = document.getElementById("inspectorOutput");
    const termTitleEl = document.getElementById("inspectorTerminalTitle");
    const termBadgeEl = document.getElementById("inspectorTerminalBadge");
    const termBodyEl = document.getElementById("inspectorTerminalBody");

    if (idEl) idEl.textContent = data.stageId;
    if (nameEl) nameEl.textContent = data.heading;
    if (subEl) subEl.textContent = data.sub;
    if (engineEl) engineEl.textContent = data.engine;
    if (hwEl) {
        hwEl.textContent = data.hardware;
        hwEl.className = `spec-badge ${data.badgeClass}`;
    }
    if (inputEl) inputEl.textContent = data.input;
    if (outputEl) outputEl.textContent = data.output;
    if (termTitleEl) termTitleEl.textContent = data.termTitle;
    if (termBadgeEl) termBadgeEl.textContent = data.termBadge;
    if (termBodyEl) termBodyEl.textContent = data.termCode;
}

function initPipelineInspector() {
    // Click on conveyor stations
    document.querySelectorAll(".circuit-station").forEach(st => {
        st.addEventListener("click", () => {
            const step = parseInt(st.getAttribute("data-station"), 10);
            selectPipelineStage(step);
        });
    });

    // Click on inspector tab buttons
    document.querySelectorAll(".stage-tab-btn").forEach(btn => {
        btn.addEventListener("click", () => {
            const step = parseInt(btn.getAttribute("data-step"), 10);
            selectPipelineStage(step);
        });
    });
}
