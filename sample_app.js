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

    let currentImageFile = null;
    let cameraStream = null;
    const predictEndpoint = window.location.protocol === "file:"
        ? "http://127.0.0.1:5000/predict"
        : "/predict";

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

    uploadForm.addEventListener("submit", async (event) => {
        event.preventDefault();

        if (!currentImageFile) {
            alert("Please choose or capture an image.");
            return;
        }

        loadingSpinner.style.display = "block";
        resultStack.classList.remove("is-visible");
        resultSection.style.display = "none";

        const formData = new FormData();
        formData.append("image", currentImageFile);

        try {
            const response = await fetch(predictEndpoint, {
                method: "POST",
                body: formData
            });

            const data = await response.json();

            loadingSpinner.style.display = "none";

            if (!response.ok || data.error) {
                alert(data.error || "Prediction request failed.");
                return;
            }

            displayPrimaryResult(data.top1);
            displayArtifactInfo(data.top1.artifact_info);

            resultStack.classList.add("is-visible");
            resultSection.style.display = "block";
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
});
