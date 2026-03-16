# Google Cloud Run Deployment Guide

To deploy this application to Google Cloud Run and satisfy the hackathon's cloud hosting requirement, follow these steps:

1. **Install Google Cloud SDK**
   Make sure `gcloud` CLI is installed and you are logged in.
   ```bash
   gcloud auth login
   ```

2. **Set your Project ID**
   ```bash
   gcloud config set project YOUR_PROJECT_ID
   ```

3. **Deploy using Cloud Run source-based deployment**
   Run the following command in the same directory as this file (where `app.py` and `Dockerfile` are located):
   ```bash
   gcloud run deploy prayer-app \
     --source . \
     --region us-central1 \
     --allow-unauthenticated \
     --set-env-vars="GEMINI_API_KEY=YOUR_GEMINI_API_KEY_HERE"
   ```

4. **Verify**
   Once deployment finishes, `gcloud` will provide a URL (e.g., `https://prayer-app-xyz.a.run.app`). Visit this URL to view your live app!
   
*Note for Hackathon Submission:* Don't forget to take a brief screen recording of your Google Cloud Console showing the deployed Cloud Run service as proof of architecture for the judges.
