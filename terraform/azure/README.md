# Azure Speech Services Terraform Configuration

This Terraform configuration creates Azure Cognitive Services Speech resource for TTS (Text-to-Speech) and STT (Speech-to-Text) functionality.

## Prerequisites

1. **Azure CLI** installed and logged in:
   ```bash
   az login
   ```

2. **Terraform** >= 1.6.0 installed

3. **Azure subscription** with permissions to create Cognitive Services resources

## Quick Start

### 1. Initialize Terraform

```bash
cd terraform/azure
terraform init
```

### 2. Configure Variables

```bash
# Copy example configuration
cp terraform.tfvars.example terraform.tfvars

# Edit with your values
vim terraform.tfvars
```

### 3. Deploy

```bash
# Preview changes
terraform plan

# Apply changes
terraform apply
```

### 4. Get API Keys (via Azure CLI)

```bash
# Get both keys
az cognitiveservices account keys list \
    --name voice-lab-speech \
    --resource-group voice-lab-speech-rg

# Get only key1
az cognitiveservices account keys list \
    --name voice-lab-speech \
    --resource-group voice-lab-speech-rg \
    --query key1 -o tsv
```

Or use the Terraform output helper command:
```bash
$(terraform output -raw get_key1_command)
```

### 5. Configure Voice Lab Backend

Add to your `.env` file:
```bash
AZURE_SPEECH_KEY=<key-from-step-4>
AZURE_SPEECH_REGION=eastasia
```

## SKU Comparison

| SKU | Use Case | Limits | Cost |
|-----|----------|--------|------|
| F0 (Free) | Development, testing | 500K chars/month for neural TTS, 5 hours audio/month for STT | Free |
| S0 (Standard) | Production | Adjustable quotas, higher limits | Pay-as-you-go |

**Note**: F0 tier quotas are **not adjustable**. Once limits are reached, requests will fail until the next month.

## Network Security (Production)

For production deployments, restrict network access:

```hcl
# In terraform.tfvars
allowed_ip_ranges = [
  "203.0.113.0/24",    # Office IP range
  "198.51.100.1"       # CI/CD server
]
```

## Outputs

| Output | Description |
|--------|-------------|
| `speech_endpoint` | REST API endpoint URL |
| `speech_region` | Deployed region (use for SDK) |
| `get_api_keys_command` | Azure CLI command to retrieve keys |

## Key Management Best Practices

1. **Rotate keys regularly**:
   ```bash
   az cognitiveservices account keys regenerate \
       --name voice-lab-speech \
       --resource-group voice-lab-speech-rg \
       --key-name key1
   ```

2. **Use key2 during rotation**: Configure your app to use key2, then regenerate key1

3. **Store in secrets manager**: For GCP deployment, store in Secret Manager (handled by main Terraform config)

## Destroy Resources

```bash
terraform destroy
```

## References

- [Azure Speech Service Documentation](https://learn.microsoft.com/en-us/azure/ai-services/speech-service/)
- [Speech Service Pricing](https://azure.microsoft.com/en-us/pricing/details/cognitive-services/speech-services/)
- [azurerm_cognitive_account](https://registry.terraform.io/providers/hashicorp/azurerm/latest/docs/resources/cognitive_account)
