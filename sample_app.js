document.addEventListener("DOMContentLoaded", () => {
    const uploadBox = document.getElementById("uploadBox");
    const openCameraButton = document.getElementById("openCameraButton");
    const capturePhotoButton = document.getElementById("capturePhotoButton");
    const closeCameraButton = document.getElementById("closeCameraButton");
    const artifactImage = document.getElementById("artifactImage");
    const cameraImage = document.getElementById("cameraImage");
    const previewImage = document.getElementById("previewImage");
    const cameraPanel = document.getElementById("cameraPanel");
    const cameraPreview = document.getElementById("cameraPreview");
    const cameraCanvas = document.getElementById("cameraCanvas");
    const uploadForm = document.getElementById("uploadForm");
    const loadingSpinner = document.getElementById("loadingSpinner");
    const resultStack = document.getElementById("resultStack");
    const resultSection = document.getElementById("resultSection");
    const primaryClass = document.getElementById("primaryClass");
    const primaryConfidence = document.getElementById("primaryConfidence");
    const primaryConfidenceText = document.getElementById("primaryConfidenceText");
    const artifactMatchState = document.getElementById("artifactMatchState");
    const artifactTitle = document.getElementById("artifactTitle");
    const artifactPeriod = document.getElementById("artifactPeriod");
    const artifactType = document.getElementById("artifactType");
    const artifactMaterial = document.getElementById("artifactMaterial");
    const artifactProvenance = document.getElementById("artifactProvenance");
    const artifactStyleCulture = document.getElementById("artifactStyleCulture");
    const artifactDescription = document.getElementById("artifactDescription");
    const searchArtifactButton = document.getElementById("searchArtifactButton");
    const downloadPdfButton = document.getElementById("downloadPdfButton");

    let currentImageFile = null;
    let cameraStream = null;
    let latestPrediction = null;
    let latestReportDate = null;
    const predictEndpoint = "/api/predict";

    uploadBox.addEventListener("click", () => {
        artifactImage.click();
    });

    openCameraButton.addEventListener("click", async () => {
        if (navigator.mediaDevices && navigator.mediaDevices.getUserMedia) {
            await openLiveCamera();
            return;
        }

        cameraImage.click();
    });

    artifactImage.addEventListener("change", (event) => {
        handleFileSelection(event.target.files);
    });

    cameraImage.addEventListener("change", (event) => {
        handleFileSelection(event.target.files);
    });

    capturePhotoButton.addEventListener("click", capturePhotoFromCamera);
    closeCameraButton.addEventListener("click", closeLiveCamera);
    searchArtifactButton.addEventListener("click", searchArtifactInfo);
    downloadPdfButton.addEventListener("click", generateArtifactPdf);

    uploadForm.addEventListener("submit", async (event) => {
        event.preventDefault();

        if (!currentImageFile) {
            alert("Please choose or capture an image.");
            return;
        }

        loadingSpinner.style.display = "block";
        resultStack.classList.remove("is-visible");
        resultSection.style.display = "none";
        searchArtifactButton.classList.remove("is-visible");
        downloadPdfButton.classList.remove("is-visible");
        latestPrediction = null;
        latestReportDate = null;

        const formData = new FormData();
        formData.append("image", currentImageFile);

        try {
            const response = await fetch(predictEndpoint, {
                method: "POST",
                body: formData
            });

            const contentType = response.headers.get("content-type") || "";
            const responseText = await response.text();
            const data = contentType.includes("application/json") && responseText
                ? JSON.parse(responseText)
                : null;

            loadingSpinner.style.display = "none";

            if (!response.ok || data.error) {
                const backendError = data && data.error
                    ? data.error
                    : responseText.trim() || `Backend error (${response.status})`;

                alert(backendError);
                return;
            }

            displayPrimaryResult(data.top1);
            displayArtifactInfo(data.top1.artifact_info);
            latestPrediction = data.top1;
            latestReportDate = new Date();

            resultStack.classList.add("is-visible");
            resultSection.style.display = "block";
            searchArtifactButton.classList.add("is-visible");
            downloadPdfButton.classList.add("is-visible");
        } catch (error) {
            loadingSpinner.style.display = "none";
            console.error(error);
            alert("Backend connection failed. Ensure Flask backend is running.");
        }
    });

    async function openLiveCamera() {
        try {
            cameraStream = await navigator.mediaDevices.getUserMedia({
                video: {
                    facingMode: { ideal: "environment" }
                },
                audio: false
            });

            cameraPreview.srcObject = cameraStream;
            cameraPanel.style.display = "block";
        } catch (error) {
            console.warn("Live camera unavailable, falling back to camera file input.", error);
            cameraImage.click();
        }
    }

    function closeLiveCamera() {
        if (cameraStream) {
            cameraStream.getTracks().forEach((track) => track.stop());
            cameraStream = null;
        }

        cameraPreview.srcObject = null;
        cameraPanel.style.display = "none";
    }

    function capturePhotoFromCamera() {
        if (!cameraStream || !cameraPreview.videoWidth) {
            alert("Camera is not ready yet.");
            return;
        }

        cameraCanvas.width = cameraPreview.videoWidth;
        cameraCanvas.height = cameraPreview.videoHeight;

        const context = cameraCanvas.getContext("2d");
        context.drawImage(cameraPreview, 0, 0, cameraCanvas.width, cameraCanvas.height);

        cameraCanvas.toBlob((blob) => {
            if (!blob) {
                alert("Could not capture image from camera.");
                return;
            }

            currentImageFile = new File([blob], `artifact-photo-${Date.now()}.jpg`, {
                type: "image/jpeg"
            });

            previewImage.src = URL.createObjectURL(currentImageFile);
            previewImage.style.display = "block";
            resetResultState();
            closeLiveCamera();
        }, "image/jpeg", 0.92);
    }

    function handleFileSelection(files) {
        if (!files.length) return;

        currentImageFile = files[0];

        const reader = new FileReader();

        reader.onload = (readerEvent) => {
            previewImage.src = readerEvent.target.result;
            previewImage.style.display = "block";
        };

        reader.readAsDataURL(currentImageFile);
        resetResultState();
        closeLiveCamera();
    }

    function displayPrimaryResult(top1) {
        primaryClass.textContent = top1.class;

        const confidence = (top1.probability * 100).toFixed(2);

        primaryConfidence.style.width = `${confidence}%`;
        primaryConfidence.textContent = `${confidence}%`;
        primaryConfidenceText.textContent = `${confidence}% confidence`;
    }

    function displayArtifactInfo(info) {
        if (!info) {
            artifactMatchState.textContent = "Metadata unavailable";
            artifactMatchState.classList.add("not-matched");
            artifactTitle.textContent = "-";
            artifactPeriod.textContent = "-";
            artifactType.textContent = "-";
            artifactMaterial.textContent = "-";
            artifactProvenance.textContent = "-";
            artifactStyleCulture.textContent = "-";
            artifactDescription.textContent = "";
            return;
        }

        artifactMatchState.textContent = info.matched ? "Local metadata found" : "No metadata match";
        artifactMatchState.classList.toggle("not-matched", !info.matched);

        artifactTitle.textContent = info.title || "-";
        artifactPeriod.textContent = info.period || "-";
        artifactType.textContent = info.object_type || "-";
        artifactMaterial.textContent = info.main_material || "-";
        artifactProvenance.textContent = info.provenance || "-";

        const style = info.style || "";
        const culture = info.culture || "";
        artifactStyleCulture.textContent = [style, culture].filter(Boolean).join(" / ") || "-";

        const description = [info.brief_description, info.detailed_description]
            .filter(Boolean)
            .join(" ")
            .trim();

        artifactDescription.textContent = description || "No description available for this class yet.";
    }

    function resetResultState() {
        latestPrediction = null;
        latestReportDate = null;
        resultStack.classList.remove("is-visible");
        resultSection.style.display = "none";
        searchArtifactButton.classList.remove("is-visible");
        downloadPdfButton.classList.remove("is-visible");
    }

    function searchArtifactInfo() {
        if (!latestPrediction) {
            alert("Please analyze an artifact before searching for more information.");
            return;
        }

        const query = buildArtifactSearchQuery(latestPrediction);
        const searchUrl = `https://www.google.com/search?q=${encodeURIComponent(query)}`;
        window.open(searchUrl, "_blank", "noopener,noreferrer");
    }

    function buildArtifactSearchQuery(prediction) {
        const info = prediction.artifact_info || {};
        const description = [info.brief_description, info.detailed_description]
            .filter(Boolean)
            .join(" ");

        const descriptionKeywords = description
            .replace(/[^\w\s-]/g, " ")
            .split(/\s+/)
            .filter((word) => word.length > 3)
            .slice(0, 12)
            .join(" ");

        return [
            info.title || prediction.class,
            prediction.class,
            info.object_type,
            info.period,
            info.main_material,
            info.provenance,
            info.style,
            info.culture,
            descriptionKeywords,
            "Goa museum artifact"
        ]
            .filter(Boolean)
            .join(" ");
    }

    async function generateArtifactPdf() {
        if (!latestPrediction || !currentImageFile) {
            alert("Please analyze an artifact before downloading the PDF.");
            return;
        }

        if (!window.jspdf || !window.jspdf.jsPDF) {
            alert("PDF generator could not load. Please check your internet connection and try again.");
            return;
        }

        try {
            downloadPdfButton.disabled = true;
            downloadPdfButton.textContent = "Preparing PDF...";

            const imageDataUrl = await readFileAsDataUrl(currentImageFile);
            const { jsPDF } = window.jspdf;
            const doc = new jsPDF({ unit: "pt", format: "a4" });
            const pageWidth = doc.internal.pageSize.getWidth();
            const pageHeight = doc.internal.pageSize.getHeight();
            const margin = 48;
            const contentWidth = pageWidth - margin * 2;
            const info = latestPrediction.artifact_info || {};
            const predictedClass = latestPrediction.class || "Artifact";
            const confidence = Number.isFinite(latestPrediction.probability)
                ? `${(latestPrediction.probability * 100).toFixed(2)}%`
                : "-";

            let y = 42;

            doc.setFillColor(7, 63, 112);
            doc.rect(0, 0, pageWidth, 116, "F");
            doc.setTextColor(255, 255, 255);
            doc.setFont("helvetica", "bold");
            doc.setFontSize(22);
            y = addWrappedText(doc, "AI Artifact Identification Report", margin, y, contentWidth, 26);
            doc.setFontSize(15);
            y = addWrappedText(doc, predictedClass, margin, y + 8, contentWidth, 20);
            doc.setFont("helvetica", "normal");
            doc.setFontSize(10);
            doc.text(`Generated: ${formatReportDate(latestReportDate)}`, margin, 96);

            y = 146;
            doc.setTextColor(35, 28, 22);
            doc.setFont("helvetica", "bold");
            doc.setFontSize(14);
            doc.text("Uploaded Artifact Image", margin, y);
            y += 16;

            const imageBox = fitImageToBox(doc, imageDataUrl, contentWidth, 260);
            doc.addImage(imageDataUrl, getPdfImageType(currentImageFile), margin, y, imageBox.width, imageBox.height);
            y += imageBox.height + 28;

            doc.setFillColor(244, 237, 226);
            doc.roundedRect(margin, y, contentWidth, 48, 6, 6, "F");
            doc.setFont("helvetica", "bold");
            doc.setFontSize(11);
            doc.setTextColor(104, 88, 74);
            doc.text("Predicted Class", margin + 16, y + 18);
            doc.text("Confidence", margin + contentWidth / 2, y + 18);
            doc.setFontSize(13);
            doc.setTextColor(35, 28, 22);
            doc.text(predictedClass, margin + 16, y + 36, { maxWidth: contentWidth / 2 - 28 });
            doc.text(confidence, margin + contentWidth / 2, y + 36);
            y += 74;

            y = addSectionTitle(doc, "Artifact Metadata", margin, y);
            const fields = [
                ["Title", info.title || predictedClass],
                ["Period", info.period],
                ["Object Type", info.object_type],
                ["Material", info.main_material],
                ["Provenance", info.provenance],
                ["Style", info.style],
                ["Culture", info.culture],
                ["Tribe", info.tribe],
                ["Metadata Source", info.source_label],
                ["Metadata Match", info.matched ? "Local metadata found" : "No metadata match"]
            ];

            fields.forEach(([label, value]) => {
                y = ensureSpace(doc, y, 46, margin, pageHeight);
                y = addField(doc, label, value || "-", margin, y, contentWidth);
            });

            const description = [info.brief_description, info.detailed_description]
                .filter(Boolean)
                .join(" ")
                .trim() || "No description available for this class yet.";

            y = ensureSpace(doc, y, 84, margin, pageHeight);
            y = addSectionTitle(doc, "Description", margin, y + 8);
            addPagedWrappedText(doc, description, margin, y, contentWidth, 16, margin, pageHeight);

            addPageFooters(doc);
            doc.save(`${sanitizeFileName(predictedClass)}-artifact-report.pdf`);
        } catch (error) {
            console.error(error);
            alert("Could not generate the PDF report. Please try again.");
        } finally {
            downloadPdfButton.disabled = false;
            downloadPdfButton.textContent = "Download PDF";
        }
    }

    function readFileAsDataUrl(file) {
        return new Promise((resolve, reject) => {
            const reader = new FileReader();
            reader.onload = () => resolve(reader.result);
            reader.onerror = () => reject(reader.error);
            reader.readAsDataURL(file);
        });
    }

    function getPdfImageType(file) {
        return file.type && file.type.toLowerCase().includes("png") ? "PNG" : "JPEG";
    }

    function fitImageToBox(doc, imageDataUrl, maxWidth, maxHeight) {
        const props = doc.getImageProperties(imageDataUrl);
        const ratio = Math.min(maxWidth / props.width, maxHeight / props.height, 1);

        return {
            width: props.width * ratio,
            height: props.height * ratio
        };
    }

    function addSectionTitle(doc, title, x, y) {
        doc.setFont("helvetica", "bold");
        doc.setFontSize(14);
        doc.setTextColor(7, 63, 112);
        doc.text(title, x, y);
        return y + 20;
    }

    function addField(doc, label, value, x, y, maxWidth) {
        doc.setFont("helvetica", "bold");
        doc.setFontSize(10);
        doc.setTextColor(104, 88, 74);
        doc.text(label.toUpperCase(), x, y);

        doc.setFont("helvetica", "normal");
        doc.setFontSize(11);
        doc.setTextColor(35, 28, 22);

        return addWrappedText(doc, String(value), x, y + 15, maxWidth, 15) + 8;
    }

    function addWrappedText(doc, text, x, y, maxWidth, lineHeight) {
        const lines = doc.splitTextToSize(String(text), maxWidth);
        doc.text(lines, x, y);
        return y + lines.length * lineHeight;
    }

    function addPagedWrappedText(doc, text, x, y, maxWidth, lineHeight, margin, pageHeight) {
        const lines = doc.splitTextToSize(String(text), maxWidth);
        let currentY = y;

        lines.forEach((line) => {
            currentY = ensureSpace(doc, currentY, lineHeight, margin, pageHeight);
            doc.text(line, x, currentY);
            currentY += lineHeight;
        });

        return currentY;
    }

    function ensureSpace(doc, y, neededHeight, margin, pageHeight) {
        if (y + neededHeight <= pageHeight - margin) {
            return y;
        }

        doc.addPage();
        return margin;
    }

    function addPageFooters(doc) {
        const pageCount = doc.internal.getNumberOfPages();
        const pageWidth = doc.internal.pageSize.getWidth();
        const pageHeight = doc.internal.pageSize.getHeight();

        for (let pageNumber = 1; pageNumber <= pageCount; pageNumber += 1) {
            doc.setPage(pageNumber);
            doc.setFont("helvetica", "normal");
            doc.setFontSize(9);
            doc.setTextColor(120, 105, 90);
            doc.text("AI Artifact Identifier", 48, pageHeight - 28);
            doc.text(`Page ${pageNumber} of ${pageCount}`, pageWidth - 48, pageHeight - 28, { align: "right" });
        }
    }

    function formatReportDate(date) {
        return (date || new Date()).toLocaleString("en-IN", {
            year: "numeric",
            month: "short",
            day: "2-digit",
            hour: "2-digit",
            minute: "2-digit"
        });
    }

    function sanitizeFileName(name) {
        return String(name)
            .toLowerCase()
            .replace(/[^a-z0-9]+/g, "-")
            .replace(/^-+|-+$/g, "")
            .slice(0, 80) || "artifact";
    }
});
