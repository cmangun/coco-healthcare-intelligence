# Security Policy

## Supported Versions

| Version | Supported          |
|---------|--------------------|
| 1.x.x   | :white_check_mark: |
| < 1.0   | :x:                |

## Reporting a Vulnerability

We take security vulnerabilities seriously, especially given our healthcare focus.

### For Non-Critical Issues

1. Open a GitHub Issue with the `security` label
2. Do NOT include exploit details in public issues
3. Describe the vulnerability type and affected component

### For Critical Issues (PHI Exposure, Authentication Bypass, etc.)

**Do NOT open a public issue.**

1. Email: security@healthcare-ai-consultant.com
2. Subject: `[SECURITY] CoCo - <Brief Description>`
3. Include:
   - Description of the vulnerability
   - Steps to reproduce
   - Potential impact
   - Suggested fix (if any)

### Response Timeline

| Severity | Initial Response | Resolution Target |
|----------|------------------|-------------------|
| Critical | 24 hours         | 72 hours          |
| High     | 48 hours         | 7 days            |
| Medium   | 5 business days  | 30 days           |
| Low      | 10 business days | 90 days           |

### What Happens Next

1. **Acknowledgment**: We'll confirm receipt and assign a tracking ID
2. **Assessment**: We'll evaluate severity and impact
3. **Remediation**: We'll develop and test a fix
4. **Disclosure**: We'll coordinate disclosure timing with you
5. **Credit**: We'll credit you in the security advisory (if desired)

## Security Design Principles

CoCo follows these security principles:

### Defense in Depth

- Multiple layers of security controls
- No single point of failure
- Assume breach mentality

### Least Privilege

- API keys scoped to minimum required permissions
- Role-based access control (RBAC)
- No shared credentials

### Zero Trust

- Verify every request
- Authenticate all services (mTLS)
- Encrypt all data in transit

### Secure by Default

- TLS required (no HTTP)
- Secrets never in code
- Audit logging always on

## Security Controls

### Authentication

| Control | Implementation |
|---------|----------------|
| API Keys | Per-service, rotatable |
| JWT Tokens | Short-lived (15 min) |
| Service Auth | mTLS between containers |
| Admin Access | MFA required |

### Authorization

| Control | Implementation |
|---------|----------------|
| RBAC | Role-based permissions |
| Resource Scoping | Patient-level access control |
| Policy Enforcement | Per-request validation |

### Encryption

| Data State | Method |
|------------|--------|
| In Transit | TLS 1.3 |
| At Rest | AES-256 |
| Secrets | HashiCorp Vault / AWS Secrets Manager |

### Audit

| Event | Logged |
|-------|--------|
| Authentication | All attempts |
| PHI Access | Every access with reason |
| Model Inference | Input/output hashes |
| Configuration Changes | Before/after |

## Dependency Management

### Scanning

- Dependabot enabled
- Snyk integration (optional)
- Weekly vulnerability scans

### Updates

- Security patches: within 7 days
- Minor updates: monthly review
- Major updates: quarterly review

### Pinning

- All dependencies version-pinned
- Lock files committed
- SBOM generated in CI

## Incident Response

See [RUNBOOK.md](RUNBOOK.md) for operational procedures.

### Security Incident Classification

| Severity | Examples |
|----------|----------|
| Critical | PHI exposure, auth bypass, RCE |
| High | Privilege escalation, injection |
| Medium | Information disclosure (non-PHI) |
| Low | Best practice deviation |

### Required Actions by Severity

**Critical:**
1. Immediate containment
2. Executive notification
3. Legal/compliance notification
4. Potential breach notification (HIPAA)

**High:**
1. Same-day remediation
2. Engineering leadership notification
3. Post-incident review

**Medium/Low:**
1. Track in issue system
2. Remediate within SLA
3. Include in regular security review

## Hardening Checklist

For production deployments:

- [ ] TLS certificates installed and valid
- [ ] API keys rotated from defaults
- [ ] Database credentials unique per environment
- [ ] Network segmentation configured
- [ ] WAF rules applied
- [ ] Rate limiting enabled
- [ ] Audit logging verified
- [ ] Backup encryption confirmed
- [ ] Penetration test completed
- [ ] HIPAA security assessment done

## Contact

- Security issues: security@healthcare-ai-consultant.com
- General questions: GitHub Issues
- Urgent matters: See escalation path in RUNBOOK.md
