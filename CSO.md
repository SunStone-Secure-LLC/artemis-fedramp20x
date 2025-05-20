# SunStone Artemis™ Platform Overview

Artemis is SunStone’s Federal Platform running on AWS, both GovCloud and Commercial AWS. 

# Features 
The Apollo Digital Twin Engine can ingest and process any of the OSCAL (currently 1.1.3) models, 
inclusive of the prototype models and extensions (eg. FedRAMP extensions, CNCF Extensions, OSCAL Foundation extensions, etc.). 
It can also ingest markdown and other document content.

(Artemis and Apollo were twin gods in Greek mythology.)

An Agency AO or ISSO (or team) would use Artemis and Apollo to do any of the following tasks:

- Analyze a CSO inventory and analyze all data flows that can be exploited to exfiltrate Federal data.
- Analyze CSO POA&Ms with respect to criticality and impact and provide specific actionable remediation steps, acceptance criteria, and automated verification tests specific to the CSO.
- Analyze CSO/CSP incidents for impact to Agency controls and system infrastructure.
- Create a threat model for a CSO relative to the Agency, and use that to evaluate CSP risks.
- Generate a CSO-specific Pen Test exercise for the Agency or as a required test specification for the CSP.
- Generate a CSO-specific Red Team Exercise for the Agency or as a required exercise for the CSP.
- Analyze a Significant Change Request from the CSP.
- Analyze a Security Impact Assessment from the CSP.
- Analzye or generate a Business Impact Assessment for a CSP change.
- Analyze a Deviation Request and Rationale from the CSP.
- Ensure that a CSP's policies, procedures and plans have content based on the actual state of the CSO in support of all NIST 800-53 Rev 5 baseline controls.
- And much more!

# Security Posture

The CSO is deployed using a FedRAMP High Baseline implementation of the [AWS Security Reference Architecture](https://docs.aws.amazon.com/prescriptive-guidance/latest/security-reference-architecture/welcome.html). The security controls recommended here, and in the [AWS Well Architected Framework](https://docs.aws.amazon.com/wellarchitected/latest/framework/welcome.html) have been implemented using Infrastructure-as-Code.
All changes to the CSO are fully automated and use "gitops", ie no manual operations are required, except for security incident responses and audit activities that necessarily require human SMEs.

The CSO is [SLSA Level 3+](https://slsa.dev/spec/v0.1/requirements).

Currently, only AWS services are used to deliver the CSO, with 2 exceptions - a FedRAMP ATO'd DAST scanner and Github Enterprise. Corporate services used by CSP staff are not scoped in.  Federal data - apart from procurement or technical support emails, etc - will never egress the CSO AWS environment and ingress the Corporate environment.  CSP staff will never have Federal data on their endpoint devices; since all activity is 100% "gitops" staff only ever use Git(hub) to make changes and native AWS browser based tools and APIs for incident response, disaster recovery, SRE.  Even in the case of a "break glass" scenario - only AWS native browser based tools will be utilized. Data never exists on CSP user endpoints.

Customers MUST use an Identity Provider with a SAML or OIDC federated login. There is no other supported identity mechanism. CSP staff use a FedRAMP High Authorized Identity Provider and AWS Identity Center SSO for all access to web based tools and APIs using Zero Trust, ephemeral, IAM capabilities.

All SecOps use automated playbooks for investigation and remediation. There is no manual SOC.
