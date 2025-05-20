# DRAFT
This is the _DRAFT_ FedRAMP 20x Package for the SunStone Artemis™ Platform. 
The contents of this, and any materials in this repository are subject to change until this DRAFT notice is removed.

# Lightweight Summary of the Cloud Service Provider (CSP) and Cloud Service Offering (CSO)
These can be found in CSP.md and CSO.md respectively in the root of this repository.

# Key Security Indicators and Validations
This package submission is a _DRAFT_ approach to describing implementation of the proposed RFC FedRAMP Key Security Indicators. Each KSI defines a security objective and lists multiple KSI Validations which, when met, demonstrate that a system has achieved the security objective. The CSP will provide in this repository both a summary machine-readable PASS (boolean true) or FAIL (boolean false) assertion to each KSI Validation, and a percentage score for each KSI validation representing an aggregate compliance score for each KSI, along with a threshold value that defines what is considered to be PASS.

# Validation Evidence
The CSP intends to provide publicly available, continuously generated, machine readable supporting evidence for each Key Security Indicator 
Validation (whether PASS or FAIL). The evidence will be defined as a set of metrics, and each will contain a high level description of the metric 
and the formula for calculating the metric.  The formula will refer to cloud native "classes" of things, not specific "type" details that 
might aid a malicious actor. For example, a formula might define a metric such as:

```
Percentage of all Data Stores Encrypted at Rest:  # Data Stores Configured with FIPS 140-2 Validated Encryption / # Total Data Stores
```

and not a specific formula that provides hints to possible bad actors:

```
Percentage of S3 Buckets Encrypted at Rest: # S3 Buckets Configured with KMS Keys / # Total S3 Buckets
```

## Audit Evidence
The CSP intends to provide continuously generated, machine readable *audit* evidence only to the 3PAO, CSO customers - whether other CSPs or Agencies,
and authorized representatives of those customers and authorized regulatory agents, investigators and when legally required by subpoena or other lawful means. This underlying audit data, for instance, will allow the CSP's 3PAO to assess the service offering and validate that the KSI Validation is implemented correctly by fully automated means. ONLY machine readable audit evidence will be provided.  Screenshots and documents MAY be processed and analyzed for derivative information, so long as that processing is fully automated.  Using the example above, this might be the raw inventory JSON of the AWS S3 buckets, along with all properties from the AWS S3 API responses for each of these buckets.  As this contains potentially useful information for malicious actors, especially in cases where the KSI is NOT being met (hopefully a rare case), we feel this is too much information to make publicly available, and violates the spirit of this pilot. In short - if the 3PAO (and Agency and Customer AOs/ISSOs/CISOs) can verify that the underlying data accurately and precisely represents the metrics reported in a reliable and explainable way, and thus the summary KSI reported is trustworthy - this should be sufficient. The public data can concisely communicate these (audited) metric results.

As such, a private repository with all available audit data, and a full "test case workbook" of automated 3PAO tests for the underlying data for each KSI and supprting metrics will be availabe for the 3PAO, CSP CSO customers and Agency CSO customers, and other authorized users as described above on an as-needed basis.

## KSI Location
The automated metrics are to be provided under the following folder structure for easy human or machine discovery and consumption:

/KSIs/assessment-plan-KSI-ID.json 

/KSIs/assessment-result-KSI-ID.json

/KSIs/summary-KSI-ID.json

Where ID represents each of the KSIs (eg. CNA, IAM, SC, MLA, etc.)

## Supporting Artifacts

To make it possible for GRC and other tools to consume the definition of the KSI metrics definitions, we provide OSCAL catalogs for each KSI located in:

/lib/catalog-KSI-ID.json

## 3PAO Audit of the KSI Methodology and Reported Results
The assessment tasks and methods for the 3PAO are provided for each KSI "aggregate" metric, as well as the supporting evidence metrics. These will be made publicly available in this repository under the following folder structure:

/3PAO/assessment-plan-KSI-ID.json

# Automation and Machine Readable Data Requirements
The assessment-result-KSI-ID.json files are machine-readable OSCAL 1.1.3 Assessment Result files that provide results for each Key Security Indicator Validation. This file includes the overall KSI Validation metric, and associated supporting metrics for the supporting RFC required characteristics. An accompanying assessment-plan-KSI-ID.json file will provide additional details of how the metrics are defined and can be executed (at a high level.) We will supplement the files with additional OSCAL 1.1.3 component defs and catalogs and profiles as/when useful. For the simple examples for draft, we omit those for brevity.

A Github action will automatically produce this file in OSCAL 1.1.3 format. Given that the action will run on a trigger when new assessment-result-KSI-ID.json files are committed from in-boundary sources, the KSI "SAR" will not be generated "on demand" so much as "continuously".

As the KSI "SAR" is a validated OSCAL 1.1.3 Assessment Result file - the reader is encouraged to read the official NIST OSCAL 1.1.3 schemas. However, to assist explaining how the KSI "SAR" maps to the KSI elements here is a short example:

```
{
  "assessment-results": {
    "uuid": "6726f839-0b57-4799-8acd-98d3899a75d3",
    "metadata": {
      "title": "Assessment Results for Cloud Security Continuous Measurement - KSI-CNA based on AWS LZA Deployment",
      "last-modified": "2025-05-20T14:30:00.000Z",
      "version": "1.0.0",
      "oscal-version": "1.1.3",
      ...
     
      "remarks": "Assessment results for the system deployed using Landing Zone Accelerator on AWS, focusing on Key Security Indicators for Cloud Native Architecture (KSI-CNA)."
    },

    "results": [
      {
        "uuid": "res-uuid-ksi-cna-aggregate-01",
        "title": "Assessment Results for KSI-CNA-AGGREGATE",
        "description": "This result set details the assessment of the Key Security Indicator for Cloud Native Architecture (KSI-CNA-AGGREGATE), including observations and findings for its constituent CNA metrics. The assessed system is built upon the Landing Zone Accelerator on AWS foundation, which is architected to align with AWS best practices and multiple global compliance frameworks. [cite: 17]",
        "start": "2025-05-20T09:00:00.000Z",
        "end": "2025-05-24T17:00:00.000Z",
        "reviewed-controls": {
          "description": "Controls reviewed as part of the KSI-CNA-AGGREGATE assessment, referencing the assessment plan.",
          "control-selections": [
            {
              "description": "Aggregate Key Security Indicator for Cloud Native Architecture.",
              "include-controls": [
                { "control-id": "KSI-CNA-AGGREGATE" }
              ]
            },
            {
              "description": "Constituent Custom Cloud Native Audit (CNA) metrics.",
              "include-controls": [
                { "control-id": "CNA-DOS-M1" },
                { "control-id": "CNA-BTC-M1" },
                { "control-id": "CNA-ILP-M1" },
                { "control-id": "CNA-MSE-M1" },
                { "control-id": "CNA-NCE-M1" },
                { "control-id": "CNA-CSC-M1" },
                { "control-id": "CNA-HAR-M1" }
              ]
            }
          ]
        },
        "observations": [
          {
            "uuid": "obs-uuid-cna-dos-m1-01",
            "title": "Observation for CNA-DOS-M1 (Denial of Service Resilience and Control Conformance)",
            "description": "Ingested AWS Shield Advanced logs, AWS WAF configurations, and network flow logs for the period May 1-15, 2025. The system, leveraging LZA-provisioned DoS mitigation capabilities, demonstrated 100% DoS resilience against simulated volumetric and protocol-based attack vectors targeting critical API endpoints. 100% of defined DoS protection controls (e.g., rate limits, geo-blocking, known bad IP lists) were found to be configured and active per organizational policy. This aligns with LZA's objective to provide a secure foundation.",
            "methods": [ "MEASURE" ],
            ...
            "collected": "2025-05-21T10:00:00.000Z"
          },
          {
            "uuid": "obs-uuid-cna-btc-m1-01",
            "title": "Observation for CNA-BTC-M1 (Boundary Traffic Control)",
            "description": "Examined firewall logs (AWS Network Firewall deployed via LZA [cite: 24]), proxy server logs, and cloud-native network security group (NSG) configurations for May 1-15, 2025. 99.95% of observed traffic flows were compliant with firewall/proxy rules. LZA's structured network deployment facilitates this. ",
            "methods": [ "MEASURE" ],
            ...

            "collected": "2025-05-21T14:00:00.000Z"
          },
          {
            "uuid": "obs-uuid-cna-ilp-m1-01",
            "title": "Observation for CNA-ILP-M1 (Immutability and Least Privilege)",
            "description": "Deployment manifests for containerized applications (on LZA-managed container platform) and IAM policies for serverless functions were reviewed. 100% of production container deployments utilized immutable images from approved registries without runtime modifications. 99% of serverless functions adhered to defined minimal privilege sets. LZA's account structure and IAM guidelines support least privilege.",
            "methods": [ "MEASURE" ],
           ...
            "collected": "2025-05-22T11:00:00.000Z"
          },
          {
            "uuid": "obs-uuid-cna-mse-m1-01",
            "title": "Observation for CNA-MSE-M1 (Microservice Segmentation)",
            "description": "Network traffic logs from the LZA-managed virtual network and service mesh configurations were analyzed for May 1-15, 2025. 99.8% of observed inter-service network flows adhered to defined segmentation policies, utilizing capabilities like security groups and NACLs configured by LZA. ",
            "methods": [ "MEASURE" ],
            ...
            "collected": "2025-05-22T15:00:00.000Z"
          },
          {
            "uuid": "obs-uuid-cna-nce-m1-01",
            "title": "Observation for CNA-NCE-M1 (Cloud Native Enforcement)",
            "description": "Cloud provider configurations for virtual networks (VPCs, security groups, NACLs, VPC endpoints) were audited. 100% of network segments/VPCs/subnets had correctly configured cloud-native flow controls as per LZA design patterns and organizational policies. LZA extensively uses these native services for network architecture. ",
            "methods": [ "MEASURE" ],
          ...
            "collected": "2025-05-23T09:30:00.000Z"
          },
          {
            "uuid": "obs-uuid-cna-csc-m1-01",
            "title": "Observation for CNA-CSC-M1 (Continuous Scanning Coverage)",
            "description": "Reviewed reports from continuous scanning tools (e.g., AWS Security Hub, Amazon GuardDuty, Amazon Macie, which LZA can configure) and asset inventories. 98% of defined cloud-native components were scanned within the defined frequency (target: >99%). All (100%) critical/high findings were remediated within policy timeframes (target: >95%). The slight dip in scanning coverage was for newly provisioned, non-critical development resources; an automated onboarding process refinement is underway.",
            "methods": [ "MEASURE" ],
         ...
            "collected": "2025-05-23T11:30:00.000Z"
          },
         ...
          {
            "uuid": "obs-uuid-ksi-cna-calc-01",
            "title": "Observation for KSI-CNA-AGGREGATE Score Calculation",
            "description": "Calculated the KSI-CNA-AGGREGATE score based on the normalized (0-100) assessment outcomes of the 7 constituent CNA metrics as per the method in 'activity-measure-ksi-cna-aggregate-uuid'. Scores: CNA-DOS-M1 (100), CNA-BTC-M1 (100), CNA-ILP-M1 (99), CNA-MSE-M1 (99), CNA-NCE-M1 (100), CNA-CSC-M1 (95 - normalized due to 98% coverage vs 99% SLO), CNA-HAR-M1 (100). Arithmetic mean: (100+100+99+99+100+95+100) / 7 = 693 / 7 = 99.00.",
            "methods": [ "MEASURE" ],
            ...
            "collected": "2025-05-24T10:00:00.000Z"
          }
        ],
        "findings": [
          {
            "uuid": "find-uuid-cna-dos-m1-01",
            "title": "Finding for CNA-DOS-M1 (Denial of Service)",
            "description": "Assessment of CNA-DOS-M1 metric related to Denial of Service resilience and control conformance.",
            "origins": [ { "actors": [ { "type": "party", "actor-uuid": "p1-assessor-org-uuid", "role-id": "assessor" } ] } ],
            "target": {
              "type": "objective-id", "target-id": "CNA-DOS-M1",
              "title": "CNA-DOS-M1 Status",
              "status": { "state": "satisfied", "reason": "pass", "remarks": "DoS resilience (>99.99%) and control conformance (100%) met SLOs. Score: 100/100."}
            },
            "related-observations": [ { "observation-uuid": "obs-uuid-cna-dos-m1-01" } ]
          },
          {
            "uuid": "find-uuid-cna-btc-m1-01",
            "title": "Finding for CNA-BTC-M1 (Boundary Traffic Control)",
            "description": "Assessment of CNA-BTC-M1 metric related to compliant traffic flows and policy-defined interfaces.",
            "origins": [ { "actors": [ { "type": "party", "actor-uuid": "p1-assessor-org-uuid", "role-id": "assessor" } ] } ],
            "target": {
              "type": "objective-id", "target-id": "CNA-BTC-M1",
              "title": "CNA-BTC-M1 Status",
              "status": { "state": "satisfied", "reason": "pass", "remarks": "Compliant traffic flows (>99.9%) and policy-defined interfaces (100%) met SLOs. Score: 100/100."}
            },
            "related-observations": [ { "observation-uuid": "obs-uuid-cna-btc-m1-01" } ]
          },
          {
            "uuid": "find-uuid-cna-ilp-m1-01",
            "title": "Finding for CNA-ILP-M1 (Immutability and Least Privilege)",
            "description": "Assessment of CNA-ILP-M1 metric for immutable deployments and least-privilege functions.",
            "origins": [ { "actors": [ { "type": "party", "actor-uuid": "p1-assessor-org-uuid", "role-id": "assessor" } ] } ],
            "target": {
              "type": "objective-id", "target-id": "CNA-ILP-M1",
              "title": "CNA-ILP-M1 Status",
              "status": { "state": "satisfied", "reason": "pass", "remarks": "Immutable deployments (100%) and Least-Privilege functions (>98%) met SLOs. Score: 99/100 (based on 99% adherence for least privilege)." }
            },
            "related-observations": [ { "observation-uuid": "obs-uuid-cna-ilp-m1-01" } ]
          },
           {
            "uuid": "find-uuid-cna-mse-m1-01",
            "title": "Finding for CNA-MSE-M1 (Microservice Segmentation)",
            "description": "Assessment of CNA-MSE-M1 metric for compliant inter-service communication.",
            "origins": [ { "actors": [ { "type": "party", "actor-uuid": "p1-assessor-org-uuid", "role-id": "assessor" } ] } ],
            "target": {
              "type": "objective-id", "target-id": "CNA-MSE-M1",
              "title": "CNA-MSE-M1 Status",
              "status": { "state": "satisfied", "reason": "pass", "remarks": "Compliant inter-service communication (>99.5%) met SLO. Score: 99/100 (based on 99.8% actual)."}
            },
            "related-observations": [ { "observation-uuid": "obs-uuid-cna-mse-m1-01" } ]
          },
          {
            "uuid": "find-uuid-cna-nce-m1-01",
            "title": "Finding for CNA-NCE-M1 (Cloud Native Enforcement)",
            "description": "Assessment of CNA-NCE-M1 metric for enforced flow control in network segments.",
            "origins": [ { "actors": [ { "type": "party", "actor-uuid": "p1-assessor-org-uuid", "role-id": "assessor" } ] } ],
            "target": {
              "type": "objective-id", "target-id": "CNA-NCE-M1",
              "title": "CNA-NCE-M1 Status",
              "status": { "state": "satisfied", "reason": "pass", "remarks": "Network segments with enforced flow control (100%) met SLO. Score: 100/100."}
            },
            "related-observations": [ { "observation-uuid": "obs-uuid-cna-nce-m1-01" } ]
          },
          {
            "uuid": "find-uuid-cna-csc-m1-01",
            "title": "Finding for CNA-CSC-M1 (Continuous Scanning Coverage)",
            "description": "Assessment of CNA-CSC-M1 metric for component scanning coverage and timely remediation.",
            "origins": [ { "actors": [ { "type": "party", "actor-uuid": "p1-assessor-org-uuid", "role-id": "assessor" } ] } ],
            "target": {
              "type": "objective-id", "target-id": "CNA-CSC-M1",
              "title": "CNA-CSC-M1 Status",
              "status": { "state": "not-satisfied", "reason": "other", "remarks": "Component scanning coverage (98%) was slightly below SLO (>99%). Critical/High finding remediation (100%) met SLO (>95%). Action plan in place for coverage. Normalized Score: 95/100."}
            },
            "related-observations": [ { "observation-uuid": "obs-uuid-cna-csc-m1-01" } ]
          },
          {
            "uuid": "find-uuid-cna-har-m1-01",
            "title": "Finding for CNA-HAR-M1 (High Availability and Resilience)",
            "description": "Assessment of CNA-HAR-M1 metric for system uptime and failover success.",
            "origins": [ { "actors": [ { "type": "party", "actor-uuid": "p1-assessor-org-uuid", "role-id": "assessor" } ] } ],
            "target": {
              "type": "objective-id", "target-id": "CNA-HAR-M1",
              "title": "CNA-HAR-M1 Status",
              "status": { "state": "satisfied", "reason": "pass", "remarks": "System uptime percentage (target >99.99%) and Failover Test Success Rate (100%) met SLOs. Score: 100/100."}
            },
            "related-observations": [ { "observation-uuid": "obs-uuid-cna-har-m1-01" } ]
          },
          {
            "uuid": "find-uuid-ksi-cna-aggregate-01",
            "title": "Finding for KSI-CNA-AGGREGATE Overall Score",
            "description": "The overall Key Security Indicator for Cloud Native Architecture (KSI-CNA-AGGREGATE) score is 99.00 based on the arithmetic mean of 7 constituent CNA metrics.",
            "origins": [ { "actors": [ { "type": "party", "actor-uuid": "p1-assessor-org-uuid", "role-id": "assessor" } ] } ],
            "target": {
              "type": "objective-id", "target-id": "KSI-CNA-AGGREGATE",
              "title": "KSI-CNA-AGGREGATE Status",
              "status": { "state": "satisfied", "reason": "pass", "remarks": "Aggregate score of 99.00 exceeds the SLO target of >75. One constituent metric (CNA-CSC-M1) noted with minor deviation under remediation."}
            },
            "related-observations": [ { "observation-uuid": "obs-uuid-ksi-cna-calc-01" } ]
          }
        ],
        ...
}
```

The Github action will digitally sign each KSI "SAR". At a future date we may provide a container image that includes the KSI "SAR" and code to validate the signature and also visualize the KSI "SAR" for convenience.

A summary shorter non-OSCAL JSON may also be produced - see the utils/ folder for an example notebook to generate this.

# 3PAO Review
During this DRAFT phase, the CSP has engaged several 3PAOs on how to perform the assessment.  As noted, we will provide pro forma assessment plans:
- The KSI "SAP" which details publicly how each metric was defined (using "classes") and how the KSI attestation meets the threshold for PASS.
- The 3PAO "SAP" which details privately how the 3PAO can use automated tools to validate that the metrics reported match the underlying CSO actual 
  state. We encourage all 3PAOs to provide a summary based on the approach defined in these assessment plans.
  - In addition the CSP will provide a bespoke, pro forma "test case workbook" artifact to the 3PAO privately that contains each and every automated test 
    detail and the acceptance criteria. In this way, the 3PAO can quickly review that each test is valid, accurate, precise, reliable, repeatable, and 
    explainable.

The result of the 3PAO process will be a 3PAO "SAR" - ie the assessment results from the running of all the automated tests in the 3PAO "SAP" and accompanying test case workbook.  That 3PAO "SAR" will be made available in summary form in this public repository, but POA&Ms or RETs will be redacted and shared only in a private repository.

It is our intent that the 3PAO SAR will be delivered by the 3PAO in valid OSCAL 1.1.3 or later.

# Continuous Reporting Indication
All CSO Key Security Indicator Validations (the KSI "SAR") can be reported continuously. All KSI Validation metrics in the KSI "SAR" are generated by an automated Github Action that executes continuously without human intervention as triggered by PR/commit of new underying data. The underlying infrastructue and app auditable data from the CSO is also produced continuously by automation. This will be made available privately as described above.

The KSI "SAR" will include meta-data of where and when the evidence was produced, and from which underlying sources for traceability.

# Prototype for Continuous Reporting
In this DRAFT phase, an API was deemed to be overkill.  Instead using the above files, at the static URL endpoint noted, the latest security status (KSI "SAR") will always be available.

# CSP Rationale and Summary

To summarize our approach:

1. Our interpretation of the 20x Pilot is to discover if data > checklists. (our words) As such, metrics and measurements of how effectively the system has been secured viz-a-viz the RFC KSIs is far more useful than evidence of "potential" security or capabilities for secure operation represented by point-in-time snapshot evidence from traditonal controls. If a CSO customer can see that a system is continuously reporting measurements of security - they should be able to trust that the supporting controls used are comprehensive and operating effectively.  While there might be POA&Ms, as long as the overall KSI metrics don't drop below the defined threshold, the CSO customer can use the service safely.
2. We use OSCAL.  While we have previously invested a lot in OSCAL, having participated in NIST events and GSA OSCAL digital package testing, we did genuinely revisit whether OSCAL was the right fit for this 20x pilot.  We decided that anything else, or anything we invented de novo, would ultimately start looking like OSCAL.  We agree that OSCAL can and should be simplified, and we have spent [time and treasure](https://github.com/SunStone-Secure-LLC/OSCAL-Plugfest-2025/) to ensure there is greater interoperability across vendors and GRC tools. As such we would continue to encourage all 20x participants to pool resources to build a BETTER FASTER EASIER OSCAL, vs reinventing a new wheel.  But we are of course biased. That said, we added a simplified summary example that we extract from the SAR, and a notebook with simple python code to demonstrate how such a summary can easily be created.
3. We do not provide "raw" control or system config evidence to the public. We will make that available to the 3PAOs and AOs, etc. in a private repository. We define the public supporting measurements of the CSO (and CSP activities) that inherently MUST reflect the underlying controls and system configs.  Thus when we report a metric, we are reporting on the efficacy and current state of those controls and system configs, without sharing too much info with potential attackers.  We feel this is the right balance between transparency and public good and the security of the CSO and our future customer (Federal) data.  No system is 100% secure - and while "security by obscurity" is not a solution, we need to hear from our future customers about what they are comfortable sharing with the public.  We hope we found a good balance.
4. We provide the raw audit data to 3PAOs so they can validate and attest to the accuracy, precision, reliability, and explainability of our metrics as related to the actual state of the CSO infrastructure and application configuration, vulnerabilities and risks.

# Submission
This repository will be the package. No accounts will be required to access the package.
The audit evidence, and supporting 3PAO assessment plans and test case workbooks will be limited to a private repository.

For that private repository we will consider options for accesing Github:
- An API that grants access to the package with an API key
- A time-limited url token with a separate encrypted passcode
- Other ideas TBD

# License Rules For This Content

## Permissions

* `commercial-use` - Any documentation, software and derivatives contained in this repository MAY NOT be used for commercial purposes.
* `modifications` - This documentation and software MAY NOT be modified.
* `distribution` - This documentation and software MAY be distributed for non-commerical use.
* `private-use` - This documentation and software MAY be used and modified in private.
* `patent-use` - This license provides NO grant of patent or other rights from contributors.

## Conditions

* `include-copyright` - A copy of the license rules and copyright notice MUST be included with copies or distribution of the documentation and software.
* `include-copyright--source` - A copy of the license and copyright notice MUST be included with the software in source form, but is not required for binaries.
* `document-changes` - Changes made to the code MUST be documented.
* `disclose-source` - Source code MUST be made available when the documentation or software is distributed.
* `same-license` - Modifications MUST be released under the same license when distributing the documentation or software. 
* `same-license--file` - Modifications of existing files MUST be released under the same license when distributing the documentation or software. 
* `same-license--component` - Modifications must be released under the same license when distributing the documentation or software as a component of other works. 

## Limitations

* `trademark-use` - This license explicitly states that it does NOT grant trademark rights, even though licenses without such a statement probably do not grant any implicit trademark rights.
* `liability` - This license includes a limitation of liability.
* `patent-use` - This license explicitly states that it does NOT grant any rights in the patents of contributors.
* `warranty` - The license explicitly states that it does NOT provide any warranty.
