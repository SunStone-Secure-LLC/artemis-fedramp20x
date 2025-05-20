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

The CSO is [SLSA Level 3](https://slsa.dev/spec/v1.1/levels).

Currently, only AWS services are used to deliver the CSO, with 2 exceptions - a FedRAMP ATO'd DAST scanner and Github Enterprise. Corporate services used by CSP staff are not scoped in.  Federal data - apart from procurement or technical support emails, etc - will never egress the CSO AWS environment and ingress the Corporate environment.  CSP staff will never have Federal data on their endpoint devices; since all activity is 100% "gitops" staff only ever use Git(hub) to make changes and native AWS browser based tools and APIs for incident response, disaster recovery, SRE.  Even in the case of a "break glass" scenario - only AWS native browser based tools will be utilized. Data never exists on CSP user endpoints.

Customers MUST use an Identity Provider with a SAML or OIDC federated login. There is no other supported identity mechanism. CSP staff use a FedRAMP High Authorized Identity Provider and AWS Identity Center SSO for all access to web based tools and APIs using Zero Trust, ephemeral, IAM capabilities.

All SecOps use automated playbooks for investigation and remediation. There is no manual SOC.

## Threat Model

Under a Zero Trust model, we always assume breach. As such we are continuously verifying that the API calls in the AWS environment (everything - data flows, processing activities, etc., is an API call) match the expected activity in the environment.  As such we can frame the threats more simply as these simple questions:

_Can we "diff" the expected (API) behavior of the CSO against the continuous stream of API activity?_

_Can we detect "drift" between the expected sources of API activity and the actual sources of API activity?_

From that perspectice - we can model:
* Is the CSO expected state complete and correct as expressed in code sufficient to achieve breach resilience? Since everything is IaC, we can determine "coverage", and  "fuzz" whether the IaC satisfies all possible inputs and always produces acceptable outputs.
  - As a secondary "runtime" test - we can continuously attack the system from inside, and from outside.
    - If any attack is succesful, we can conclude our above static analysis was incomplete in some way so it needs to be revised and improved. Repeat.
*  Once satisfied by that testing, what are the ways that an insider or external threat actor can modify or break the API clients in the CSO,
   which would change the API activitiy, representing a violation of the tested and "fuzzed" behavior above?
   
This breaks down into these threat vector buckets:
  - Can someone authenticate outside of the [IdP and Federated login](https://devici.com/resources/blog/zero-trust-threat-modeling)?
  - Or in any way sidestep the authentication process?
  - Can someone impersonate a valid identity?
  - Can someone sidestep the SLSA [CI/CD process](https://slsa.dev/spec/v1.1/threats) that realizes the actual CSO components
    and state from the underlying Iac?
  - Can an authenticated identity modify the tested/fuzzed Infrastructure Code to delete or disable or in any way modify
    the components that generate VALID API activity that represents correct and expecte data flows and processing activities?
  - Does the IaC rely on external components that can be modified or tampered with?
  - Can someone stealthily hide API calls in the CSO over time to make detection of "drift" harder?
  - Can the CSP itself act maliciously to subvert any/all of the above?
  - Can one CSO user act malciously to subvert any/all of the above?
    
No other threats are currently in scope.  However new threats will be added in an agile way as new information surfaces.
