# Nanage Soft Delete

Cloud Run service that can be triggered automatically (using Eventarc) each time an Audit Log entry for GCS bucket creation is generated within your GCP organization.
The service can then manage the soft delete duration for the newly created bucket.

## Deployment

### Route Audit Logs
At the Organization level in the GCP Cloud Console, navigate to Logging > Log router > Create sink (requires Org Admin permission)
- Sink destination: Cloud Pub/Sub topic && create a new Pub/Sub topic and subscription in your GCP Project where you will run this service
- Select: Include logs ingested by this organization and all child resources
- Filter:
```
resource.type="gcs_bucket" AND
log_id("cloudaudit.googleapis.com/activity") AND
protoPayload.method_name="storage.buckets.create"
```

### Create Service Account
In your GCP Project, create a new Service Account and give it the following permissions:
- Cloud Run Invoker
- Eventarc Event Receiver
- Pub/Sub Subscriber

At the org level, give it the following permission (to be able to edit Soft Delete retention on all buckets org-wide):
- Storage Admin

### Build & Deploy the 'manage-soft-delete' Cloud Run Service

**Setting up your environment:**

Follow the steps at: 
- https://cloud.google.com/run/docs/setup
- https://cloud.google.com/run/docs/quickstarts/build-and-deploy/deploy-python-service

**Configuration**

In `main.py`, change project_id, subscription_id, mum_messages, retention_duration_seconds with your values

**Build the Container Image && Deploy to Cloud Run**

```
gcloud builds submit --tag gcr.io/[YOUR_PROJECT_ID]/manage-soft-delete
gcloud run deploy manage-soft-delete --image gcr.io/[YOUR_PROJECT_ID]/manage-soft-delete --platform managed --region [YOUR_REGION] --service-account=[YOUR_SERVICE_ACCOUNT]
```

Note: Replace [YOUR_PROJECT_ID] and [YOUR_REGION] and [YOUR_SERVICE_ACCOUNT] with your values

### Create an Eventarc trigger
At the GCP Project level in the Cloud Console, navigate to Eventarc > Triggers > Create trigger
- Event provider: Cloud Pub/Sub
- Event type: google.cloud.pubsub.v1.messagePublished
- Cloud Pub/Sub topic: select the topic created earlier
- Service account: select the service account created eatlier
- Event destination: Cloud Run && select the 'manage-soft-delete' service you just deployed