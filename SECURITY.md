# Security

Do not include API keys, bearer tokens, or provider secrets in issues, pull requests, logs, or configuration files.

The evaluation runner reads credentials only from environment variables. If a secret is accidentally committed, rotate it immediately and remove it from the repository history before publishing.
