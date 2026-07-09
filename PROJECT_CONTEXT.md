# PROJECT_CONTEXT

## Project Overview
AI Artifact Identifier is a BE final year project that identifies archaeological and museum artifacts from images using a deep learning model and displays curated historical information offline.

## Objective
- Identify Goan heritage artifacts from uploaded images.
- Display reliable information from a local knowledge base.
- Generate a PDF report (planned).
- Work offline after deployment.

## Problem Statement
Museum visitors and students often cannot identify artifacts. Existing solutions depend on internet access or manual searching. This project provides AI-assisted identification with an offline information database.

## Current Implementation Status
### Completed
- Dataset collection (~400+ images, 38 classes)
- Image cropping and resizing to 224×224
- Train/validation split
- EfficientNetB0 transfer learning model
- Flask backend
- HTML/CSS/JavaScript frontend
- Image upload and prediction
- Top-K predictions
- Confidence display
- Local labels.json
- Museums of India scraping pipeline completed for Goa sculpture collection
- Local artifact metadata database prepared
- Model saved as `.keras`

### In Progress
- Integrate local metadata into UI
- PDF generation
- Confidence threshold for "Unknown Artifact"
- Database lookup after prediction

### Pending
- Grad-CAM visualization
- Confusion matrix page
- Final UI polishing
- Final report and viva preparation

## Architecture
Image Upload
→ Preprocessing
→ EfficientNetB0 CNN
→ Softmax Prediction
→ Confidence Check
→ Local Knowledge Base
→ Display Information
→ PDF Generation (future)

## Technologies
### Languages
- Python
- JavaScript
- HTML5
- CSS3

### AI
- Artificial Intelligence
- Machine Learning
- Deep Learning
- Computer Vision
- CNN
- Transfer Learning

### Frameworks
- TensorFlow
- Keras
- Flask
- Bootstrap

### Libraries
- numpy
- Pillow
- matplotlib
- flask-cors
- json
- os
- pathlib
- shutil
- random

## Folder Structure
artifact_identifier/
- dataset/
- dataset_224/
- dataset_split/
- models/
  - final_model.keras
  - best_model.keras
  - labels.json
- app.py
- train.py
- preprocess.py
- sample_app.html
- sample_app.js
- requirements.txt

## Dataset
- 38 artifact classes
- 400+ manually curated images
- Museum photographs + carefully selected online images
- 224×224 RGB
- Manual labels
- Train/Validation split

## AI Model
- EfficientNetB0 (ImageNet pretrained)
- Transfer learning
- Fine tuning
- Softmax classifier
- Adam optimizer
- Categorical Crossentropy
- EarlyStopping
- ReduceLROnPlateau
- ModelCheckpoint

## Training Pipeline
Dataset → Resize → Split → Augmentation → Head Training → Fine Tuning → Save Model → Save Labels

## Scraping Pipeline
See SCRAPING_PHASE_SUMMARY.md. Official Goa Museum metadata is scraped and stored locally for offline retrieval.

## Flask Workflow
Frontend uploads image → Flask preprocesses → CNN predicts → Returns Top-1 + Top-K JSON → Frontend displays results.

## Database Workflow
Prediction class → Lookup local JSON → Return artifact metadata → Future PDF generation.

## Confidence Threshold
Planned: if confidence < configurable threshold (default around 45–65%), classify as Unknown Artifact.

## Design Decisions
- Offline-first system
- Local metadata preferred over LLM
- Separate classifier and knowledge base
- Simple maintainable architecture
- EfficientNetB0 chosen as accuracy/complexity balance

## Coding Conventions
- Keep preprocessing identical in training and inference.
- Store models under models/.
- Use JSON for labels and metadata.
- Modular Flask routes.
- Avoid hard-coded class names.

## Important Rules
- Do NOT replace EfficientNetB0 without approval.
- Do NOT change image preprocessing pipeline unless retraining.
- Do NOT mix training and validation images.
- Prefer local database over online responses.
- Add new artifact classes only with retraining.

## Future Roadmap
- Offline PDF generation
- Unknown artifact workflow
- Human-approved AI metadata expansion
- Grad-CAM
- Mobile application
- Museum kiosk deployment
- Incremental dataset expansion
