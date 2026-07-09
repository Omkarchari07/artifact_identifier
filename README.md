# AI Artifact Identifier

AI Artifact Identifier is a Flask + TensorFlow project that identifies archaeological and museum artifacts from images and shows curated offline metadata.

## Deployment

- Frontend: Vercel
- Backend: Render

## Frontend Entry

The frontend entry file is `index.html`, which is the standard static entry point for Vercel.

## Backend

Run the Flask backend with `app.py`. The backend loads the TensorFlow model, predicts the artifact class, and returns JSON responses for the frontend.

## Local Metadata

Verified artifact metadata is loaded from `dataset_split/val`.

## Project Files

- `index.html`
- `sample_app.js`
- `app.py`
- `train.py`
- `preprocess.py`
- `requirements.txt`
- `requirements-dev.txt`

## Notes

- Do not change the model or preprocessing pipeline unless retraining.
- Keep `dataset_split/val` as the source of truth for artifact metadata.