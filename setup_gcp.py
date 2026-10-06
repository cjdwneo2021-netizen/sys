"""Run in Colab after google.colab.auth.authenticate_user(project_id=...).
Creates a dedicated service account and repository-restricted WIF provider.
No private key is generated.
"""
import json
import re
import subprocess

def gcloud(*args, json_result=False, optional=False):
    command = ["gcloud", *args, "--quiet"]
    if json_result:
        command.append("--format=json")
    result = subprocess.run(command, text=True, capture_output=True)
    if result.returncode:
        if optional and ("NOT_FOUND" in result.stderr or "not found" in result.stderr.lower()):
            return None
        raise RuntimeError(result.stderr.strip())
    return json.loads(result.stdout) if json_result and result.stdout.strip() else result.stdout.strip()

def setup(project_id, repository_id, owner_id, branch="main"):
    if not re.fullmatch(r"[a-z][a-z0-9-]{4,28}[a-z0-9]", project_id):
        raise ValueError("Enter an existing Google Cloud project ID")
    if not str(repository_id).isdigit() or not str(owner_id).isdigit():
        raise ValueError("Repository and owner IDs must be numeric")
    if not re.fullmatch(r"[A-Za-z0-9._/-]+", branch):
        raise ValueError("Invalid branch name")
    project = gcloud("projects", "describe", project_id, json_result=True)
    number = str(project["projectNumber"])
    gcloud("services", "enable", "drive.googleapis.com", "iam.googleapis.com",
           "iamcredentials.googleapis.com", "sts.googleapis.com", "--project", project_id)
    account_id = "studybot-drive"
    account = account_id + "@" + project_id + ".iam.gserviceaccount.com"
    if gcloud("iam", "service-accounts", "describe", account, "--project", project_id,
              json_result=True, optional=True) is None:
        gcloud("iam", "service-accounts", "create", account_id, "--display-name", "StudyBot Drive reader",
               "--project", project_id)
    pool_id = "studybot"
    pool = f"projects/{number}/locations/global/workloadIdentityPools/{pool_id}"
    existing_pool = gcloud("iam", "workload-identity-pools", "describe", pool_id, "--location", "global",
                          "--project", project_id, json_result=True, optional=True)
    if existing_pool is None:
        gcloud("iam", "workload-identity-pools", "create", pool_id, "--location", "global",
               "--display-name", "StudyBot GitHub", "--project", project_id)
    elif existing_pool.get("state") != "ACTIVE" or existing_pool.get("disabled"):
        raise ValueError("Existing Workload Identity Pool is not active")
    mapping = {"google.subject": "assertion.sub", "attribute.repository_id": "assertion.repository_id",
               "attribute.repository_owner_id": "assertion.repository_owner_id", "attribute.ref": "assertion.ref"}
    condition = (f"assertion.repository_id == '{repository_id}' && assertion.repository_owner_id == '{owner_id}'"
                 f" && assertion.ref == 'refs/heads/{branch}'")
    provider_id = "repo-" + str(repository_id)
    existing = gcloud("iam", "workload-identity-pools", "providers", "describe", provider_id,
                      "--workload-identity-pool", pool_id, "--location", "global",
                      "--project", project_id, json_result=True, optional=True)
    if existing is None:
        gcloud("iam", "workload-identity-pools", "providers", "create-oidc", provider_id,
               "--workload-identity-pool", pool_id, "--location", "global", "--project", project_id,
               "--issuer-uri", "https://token.actions.githubusercontent.com",
               "--attribute-mapping", ",".join(key + "=" + value for key, value in mapping.items()),
               "--attribute-condition", condition)
    elif (existing.get("attributeCondition") != condition or existing.get("attributeMapping") != mapping
          or existing.get("oidc", {}).get("issuerUri") != "https://token.actions.githubusercontent.com"
          or existing.get("disabled") or existing.get("state") != "ACTIVE"):
        raise ValueError("Existing provider differs from expected configuration; inspect before reuse")
    member = "principalSet://iam.googleapis.com/" + pool + "/attribute.repository_id/" + str(repository_id)
    gcloud("iam", "service-accounts", "add-iam-policy-binding", account,
           "--project", project_id, "--role", "roles/iam.workloadIdentityUser", "--member", member,
           "--condition=None")
    return {"GCP_WORKLOAD_IDENTITY_PROVIDER": pool + "/providers/" + provider_id,
            "GCP_SERVICE_ACCOUNT": account}
