import json
from flask import Flask
from google.api_core import retry
from google.cloud import pubsub_v1
from google.cloud import storage

app = Flask(__name__)

project_id = "your-project-id"
subscription_id = "your-subscription-id"
# project_id = "tdelazzari-argolis"
# subscription_id = "sub-organization-audit-log-sink-storage-only"
num_messages = 3  # Number of messages to pull at once
retention_duration_seconds = "0"

def manage_soft_delete(json_message):
    if json_message['methodName'] == 'storage.buckets.create':
        bucket_name = json_message['resourceName'].split('/')[-1]
        storage_client = storage.Client()
        bucket = storage_client.get_bucket(bucket_name)
        bucket.soft_delete_policy.retention_duration_seconds = retention_duration_seconds
        bucket.patch()
        print(f"New soft-delete policy applied for bucket: {bucket.name}")

@app.route("/", methods=["POST"])
def index():
    print(f"Detected creation of Cloud Storage bucket")
    subscriber = pubsub_v1.SubscriberClient()
    # The `subscription_path` method creates a fully qualified identifier
    # in the form `projects/{project_id}/subscriptions/{subscription_id}`
    subscription_path = subscriber.subscription_path(project_id, subscription_id)
    with subscriber:
        # The subscriber pulls a specific number of messages. 
        # The actual number of messages pulled may be smaller than max_messages.
        response = subscriber.pull(
            request={"subscription": subscription_path, "max_messages": num_messages},
            retry=retry.Retry(deadline=300),
        )
        if len(response.received_messages) == 0:
            return
        ack_ids = []
        for received_message in response.received_messages:
            print(f"Received message: {received_message.message.data}.")
            data = received_message.message.data.decode('utf-8')
            json_data = json.loads(data)['protoPayload']
            print(f"Received message in JSON: {json_data}")
            manage_soft_delete(json_data)
            ack_ids.append(received_message.ack_id)
        
        # Acknowledges the received messages so they will not be sent again.
        subscriber.acknowledge(request={"subscription": subscription_path, "ack_ids": ack_ids})
        print(f"Received and acknowledged {len(response.received_messages)} messages from {subscription_path}.")
    return (f"Success!", 200)

if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=int(os.environ.get("PORT", 8080)))
