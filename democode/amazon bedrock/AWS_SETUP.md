# GenAI Training — AWS Setup Guide

This document contains the credentials and steps participants need to validate Amazon Bedrock model access before the training session.

---

## AWS Account Details

Make sure  you have the following details from your AWS Cloud Admin team:

| Field |
|-------|
| **AWS Region** |
| **Console Login URL** |
| **Console Login Email** |
| **Console Password** |
| **AWS Access Key ID** | 
| **AWS Secret Access Key** | 

If you were not provided an Access Key ID and Secret Access Key, follow these steps to create them.

## Step 1 — Log in to the AWS Console

1. Open the Console Login URL above in your browser.
2. Enter the email and password provided in the table above.
3. If prompted for MFA, enter the code from your authenticator app.

### Step 2 - Navigate to IAM

1. In the AWS Console search bar, type **IAM** and click **IAM**.
2. In the left sidebar, click **Users**.
3. Click on your username in the list.

### Step 3 - Create an Access Key

1. Click the **Security credentials** tab.
2. Scroll down to the **Access keys** section.
3. Click **Create access key**.
4. On the *Use case* screen, select **Command Line Interface (CLI)** and check the confirmation checkbox at the bottom, then click **Next**.
5. Optionally add a description tag (e.g., `genai-training`), then click **Create access key**.
6. **Important:** Copy or download the credentials now — the Secret Access Key is only shown once.
   - **Access Key ID** — starts with `AKIA…`
   - **Secret Access Key** — a long alphanumeric string
7. Click **Done**.


---

## Step 2 — Validate Amazon Bedrock Model Access

1. In the AWS Console search bar, type **Bedrock** and click **Amazon Bedrock**.
2. In the left sidebar, click **Models** 
3. Confirm that the models listed below show a status of **Access granted**:

   | Model | Provider |
   |-------|----------|
   | Claude 3 Sonnet | Anthropic |
   | Claude 3 Haiku | Anthropic |
   | Titan Text G1 - Express | Amazon |

4. Choose the model and select "Open in Playground"

5. Chat with the model by asking any question such as "What is the capital of France?"

---


## Step 4 — Install the AWS CLI

Download and install the AWS CLI for your operating system:

| OS | Download | Install |
|----|----------|---------|
| **Windows** | [aws AWSCLIV2.msi](https://awscli.amazonaws.com/AWSCLIV2.msi) | Run the downloaded `.msi` installer and follow the prompts |
| **macOS** | [aws AWSCLIV2.pkg](https://awscli.amazonaws.com/AWSCLIV2.pkg) | Run the downloaded `.pkg` installer and follow the prompts |

After installation, verify it worked by opening a new terminal and running:

```bash
aws --version
```

Expected output (version numbers may differ):

```
aws-cli/2.x.x Python/3.x.x Linux/Windows/Darwin
```
---

## Step 5 — Configure the AWS CLI

Open a terminal and run:

```bash
aws configure
```

Enter the values when prompted:

```
AWS Access Key ID [None]: <your Access Key ID>
AWS Secret Access Key [None]: <your Secret Access Key>
Default region name [None]: us-east-1
Default output format [None]: json
```

### Verify the configuration

```bash
aws sts get-caller-identity
```

Expected output (values will differ):

```json
{
    "UserId": "AIDA...",
    "Account": "123456789012",
    "Arn": "arn:aws:iam::123456789012:user/your-username"
}
```

---

## Step 6 — Test Bedrock Access from the CLI

Run the following command to invoke a Bedrock model and confirm end-to-end access:

```bash
aws bedrock-runtime invoke-model \
  --model-id anthropic.claude-3-haiku-20240307-v1:0 \
  --body '{"anthropic_version":"bedrock-2023-05-31","max_tokens":64,"messages":[{"role":"user","content":"Say hello!"}]}' \
  --cli-binary-format raw-in-base64-out \
  --region us-east-1 \
  output.json && cat output.json
```

A successful response contains a `content` field with the model's reply. If you see an `AccessDeniedException`, revisit Step 2 to ensure model access has been granted.

---

## Troubleshooting

| Error | Likely Cause | Fix |
|-------|-------------|-----|
| `AccessDeniedException` | Model access not granted | Complete Step 2 |
| `InvalidClientTokenId` | Wrong Access Key ID | Re-run `aws configure` |
| `SignatureDoesNotMatch` | Wrong Secret Access Key | Re-run `aws configure` |
| `Could not connect to the endpoint URL` | Wrong region | Ensure region is `us-east-1` |
