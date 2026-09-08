# Third-Party Notices

> [Doctrine](README.md) > Third-Party Notices

Doctrine's own guides, configurations and agents are licensed under the MIT
Licence (see [LICENSE](LICENSE)). Everything under `reference/` is third-party
material and is **NOT** covered by that grant. This file records, for every
vendored source: the upstream project, its URL, the exact licence and licence
URL, what Doctrine changed, and the attribution that **MUST** travel with the
material.

The key words "MUST", "MUST NOT", "REQUIRED", "SHALL", "SHALL NOT",
"SHOULD", "SHOULD NOT", "RECOMMENDED", "MAY", and "OPTIONAL" in this
document are to be interpreted as described in [RFC 2119](https://datatracker.ietf.org/doc/html/rfc2119).

All licence URLs in this file were fetched and read on 2026-09-08. Licence
texts that **MUST** be distributed with the material are stored next to it:
`reference/<vendor>/LICENSE*` for the style guides, and
`reference/security/LICENSES/` for the security references.

## Summary

| Source | Location | Licence | Commercial use | Modification |
| ------ | -------- | ------- | -------------- | ------------ |
| Google Style Guides | `reference/google/` | CC BY 3.0 (code samples Apache-2.0) | Yes | Yes, must be marked |
| Airbnb style guides | `reference/airbnb/` | MIT | Yes | Yes |
| SQL style guide (Holywell) | `reference/holywell/` | CC BY-SA 4.0 | Yes | Yes, ShareAlike |
| IETF RFC 2119 | `reference/ietf/` | Unlimited distribution (pre-TLP RFC) | Yes | No |
| RuboCop community guides | `reference/rubocop/` | CC BY 3.0 | Yes | Yes, must be marked |
| Rust API Guidelines | `reference/rust/` | MIT OR Apache-2.0 | Yes | Yes |
| Shopify Ruby Style Guide | `reference/shopify/` | MIT | Yes | Yes |
| Uber Go Style Guide | `reference/uber/` | Apache-2.0 | Yes | Yes, must be marked |
| MITRE ATT&CK | `reference/security/mitre/attack/` | MITRE ATT&CK Terms of Use | Yes | Yes |
| MITRE ATLAS | `reference/security/mitre/atlas/` | Apache-2.0 | Yes | Yes, must be marked |
| MITRE D3FEND | `reference/security/mitre/d3fend/` | MIT | Yes | Yes |
| MITRE CAPEC | `reference/security/mitre/capec/` | CAPEC Terms of Use | Yes | Yes |
| MITRE CWE | `reference/security/cwe/` | CWE Terms of Use | Yes | Yes |
| OWASP | `reference/security/owasp/` | CC BY-SA 4.0 | Yes | Yes, ShareAlike |
| SigmaHQ rules | `reference/security/sigma/` | Detection Rule License 1.1 | Yes | Yes |
| JA4 / JA4+ (FoxIO) | `reference/security/fingerprints/ja4/` | BSD-3-Clause (JA4) / FoxIO 1.1 (JA4+) | **JA4+ non-commercial only** | Yes |
| SLSA | `reference/security/slsa/` | Community Specification 1.0 | Yes | Yes, with attribution |
| OpenSSF Scorecard | `reference/security/openssf/` | Apache-2.0 | Yes | Yes, must be marked |
| SBOM formats | `reference/security/sbom/` | Apache-2.0 / Community Spec 1.0 | Yes | Yes |
| CIS Critical Security Controls | `reference/security/cis/` | CC BY-NC-ND 4.0 | **No, without CIS approval** | **No** |
| NIST | `reference/security/nist/`, `crypto/` | US Government work | Yes | Yes |
| CISA KEV | `reference/security/kev/` | US Government work | Yes | Yes |
| EPSS (FIRST) | `reference/security/epss/` | Free to use, attribution requested | Yes | Yes |

Two sources restrict commercial use: **CIS** and the **JA4+ variants**. Anyone
redistributing Doctrine commercially **MUST** exclude `reference/security/cis/`
and any JA4+ variant material, or obtain permission from the rights holders.

## Vendored style guides

### Google Style Guides

- **Upstream**: Google Style Guides — <https://github.com/google/styleguide>,
  <https://google.github.io/styleguide/>
- **Copyright**: Copyright (c) Google Inc. and the Google Style Guides authors
- **Licence**: Creative Commons Attribution 3.0 Unported (CC BY 3.0)
- **Licence URL**: <https://creativecommons.org/licenses/by/3.0/legalcode>
- **Licence text**: `reference/google/LICENSE` (verbatim copy of
  <https://raw.githubusercontent.com/google/styleguide/gh-pages/LICENSE>)
- **Code samples**: `reference/google/json.xml` carries the upstream statement
  that code samples are licensed under
  [Apache 2.0](https://www.apache.org/licenses/LICENSE-2.0), not CC BY 3.0.
  The README's blanket "Google style guides are licensed under CC-BY 3.0" is
  therefore incomplete for that file.
- **Doctrine's modifications**: prose reflowed to 100 columns, markdownlint
  directives added, files renamed (upstream `pyguide.md` is vendored as
  `python.md`). The vendoring revision was not recorded, so local changes
  cannot be separated from upstream drift. These are adaptations under CC BY
  3.0 section 3(b).
- **Required attribution**: "Google Style Guides, Copyright (c) Google Inc.,
  licensed under CC BY 3.0 (<https://creativecommons.org/licenses/by/3.0/>).
  Modified by Doctrine."

### Airbnb style guides

- **Upstream**: Airbnb JavaScript Style Guide —
  <https://github.com/airbnb/javascript> (`javascript.md`, `react.md`,
  `css-in-javascript.md`); Airbnb Ruby Style Guide —
  <https://github.com/airbnb/ruby> (`ruby.md`)
- **Copyright**: Copyright (c) 2012 Airbnb
- **Licence**: MIT Licence
- **Licence URL**:
  <https://github.com/airbnb/javascript/blob/master/LICENSE.md>,
  <https://github.com/airbnb/ruby/blob/master/LICENSE.md>
- **Licence text**: `reference/airbnb/LICENSE`. Both upstream repositories
  carry the same MIT text with the same copyright holder and year, differing
  only in line wrapping.
- **Doctrine's modifications**: renamed from upstream `README.md`, reflowed,
  and a small number of code samples requoted. MIT imposes no
  modification-marking duty.
- **Required attribution**: retain the MIT copyright and permission notice in
  all copies or substantial portions.

### SQL style guide (Simon Holywell)

- **Upstream**: SQL style guide — <https://www.sqlstyle.guide/>,
  <https://github.com/treffynnon/sqlstyle.guide>
- **Copyright**: SQL style guide (c) by Simon Holywell,
  <https://www.simonholywell.com/>
- **Licence**: Creative Commons Attribution-ShareAlike 4.0 International
  (CC BY-SA 4.0)
- **Licence URL**: <https://creativecommons.org/licenses/by-sa/4.0/legalcode>
- **Licence text**: `reference/holywell/LICENCE` (verbatim copy of the
  upstream `LICENCE`); full legal code at
  `reference/security/LICENSES/CC-BY-SA-4.0.txt`
- **Doctrine's modifications**: prose and lists reflowed to 100 columns, some
  headings altered.
- **ShareAlike**: because it is modified, `reference/holywell/sql.md` is
  Adapted Material and **MUST** stay under CC BY-SA 4.0 or a BY-SA compatible
  licence. Doctrine's MIT licence does **NOT** apply to it.
- **Required attribution**: "SQL style guide by Simon Holywell
  (<https://www.simonholywell.com/>) is licensed under a Creative Commons
  Attribution-ShareAlike 4.0 International License
  (<https://creativecommons.org/licenses/by-sa/4.0/>). Based on a work at
  <https://www.sqlstyle.guide/>. Modified by Doctrine."

### IETF RFC 2119

- **Upstream**: S. Bradner, "Key words for use in RFCs to Indicate Requirement
  Levels", BCP 14, RFC 2119, March 1997 —
  <https://www.rfc-editor.org/rfc/rfc2119.txt>
- **Rights holder**: The IETF Trust
- **Licence**: RFC 2119 carries no separate copyright statement; its Status of
  this Memo section states "Distribution of this memo is unlimited." It was
  published before 25 March 2015 and is a Pre-Existing IETF Document under
  section 2(c) of the IETF Trust Legal Provisions 5.0, so it remains subject
  to the IETF copyright policy in force at publication.
- **Licence URL**:
  <https://trustee.ietf.org/documents/trust-legal-provisions/tlp-5/>
- **Doctrine's modifications**: none of substance. Verified on 2026-09-08 by
  diffing `reference/ietf/rfc2119.txt` against the RFC Editor text: only
  form-feed and trailing-whitespace differences. RFC text **MUST NOT** be
  altered in substance.
- **Required attribution**: cite as S. Bradner, "Key words for use in RFCs to
  Indicate Requirement Levels", BCP 14, RFC 2119, March 1997,
  <https://www.rfc-editor.org/info/rfc2119>.

### RuboCop community style guides

- **Upstream**: Ruby Style Guide —
  <https://github.com/rubocop/ruby-style-guide>, <https://rubystyle.guide>;
  Rails Style Guide — <https://github.com/rubocop/rails-style-guide>,
  <https://rails.rubystyle.guide>
- **Copyright**: Bozhidar Batsov and the Ruby/Rails style guide contributors
- **Licence**: Creative Commons Attribution 3.0 Unported (CC BY 3.0), declared
  inline in the "License" section at the end of each upstream document.
  Neither upstream repository ships a licence file (verified: the GitHub
  licence API returns null for both).
- **Licence URL**: <https://creativecommons.org/licenses/by/3.0/>
- **Licence text**: `reference/rubocop/LICENSE` (CC BY 3.0 Unported legal
  code, included because upstream ships none)
- **Doctrine's modifications**: renamed from `README.adoc` and reflowed.
- **Required attribution**: "Ruby Style Guide / Rails Style Guide by Bozhidar
  Batsov and contributors, licensed under CC BY 3.0
  (<https://creativecommons.org/licenses/by/3.0/>). Modified by Doctrine."

### Rust API Guidelines

- **Upstream**: Rust API Guidelines —
  <https://github.com/rust-lang/api-guidelines>,
  <https://rust-lang.github.io/api-guidelines/>
- **Copyright**: Copyright (c) 2017 The Rust Project Developers
- **Licence**: dual licensed, at the recipient's option, under Apache-2.0 or
  MIT. Doctrine redistributes under the MIT option.
- **Licence URL**: <https://www.apache.org/licenses/LICENSE-2.0>,
  <https://opensource.org/license/mit>
- **Licence text**: `reference/rust/LICENSE-APACHE`,
  `reference/rust/LICENSE-MIT` (verbatim copies of the upstream files)
- **Doctrine's modifications**: upstream `src/` files flattened into one
  directory and reflowed. Upstream ships no `NOTICE` file (verified: contents
  API returns 404), so Apache-2.0 section 4(d) adds nothing.
- **Required attribution**: retain the MIT copyright and permission notice.

### Shopify Ruby Style Guide

- **Upstream**: <https://github.com/Shopify/ruby-style-guide>,
  <https://ruby-style-guide.shopify.dev/>
- **Copyright**: Copyright (c) 2015-2022 Shopify Inc.
- **Licence**: MIT Licence
- **Licence URL**:
  <https://github.com/Shopify/ruby-style-guide/blob/main/LICENSE.md>
- **Licence text**: `reference/shopify/LICENSE`
- **Doctrine's modifications**: renamed from `README.md` and reflowed.
- **Required attribution**: retain the MIT copyright and permission notice.

### Uber Go Style Guide

- **Upstream**: <https://github.com/uber-go/guide>
- **Copyright**: Copyright (c) Uber Technologies, Inc.
- **Licence**: Apache License, Version 2.0
- **Licence URL**: <https://www.apache.org/licenses/LICENSE-2.0>
- **Licence text**: `reference/uber/LICENSE`
- **Doctrine's modifications**: `reference/uber/go.md` is upstream `style.md`
  with prose reflowed, an extra `markdownlint-disable MD013` directive, and
  bare URLs wrapped in angle brackets. `reference/uber/NOTICE` is the
  "prominent notice stating that You changed the files" required by
  Apache-2.0 section 4(b). Upstream ships no `NOTICE` file (verified: contents
  API returns 404), so section 4(d) adds nothing.
- **Required attribution**: "Uber Go Style Guide, Copyright (c) Uber
  Technologies, Inc., licensed under the Apache License, Version 2.0.
  Modified by Doctrine."

## Security references

Every file under `reference/security/` is a Doctrine-authored summary, index
or cross-mapping rather than a verbatim upstream dump. That does not remove
the upstream terms: the summaries are derived from the sources below and
**MUST** carry their attribution. Machine-readable `license` and `license_url`
fields for each source are in `reference/security/manifest.json`.

### MITRE ATT&CK

- **Upstream**: MITRE ATT&CK — <https://attack.mitre.org/>,
  <https://github.com/mitre/cti>
- **Licence**: MITRE ATT&CK Terms of Use. MITRE grants a non-exclusive,
  royalty-free licence to use ATT&CK for research, development and commercial
  purposes, conditional on reproducing MITRE's copyright designation and the
  licence in any copy.
- **Licence URL**:
  <https://attack.mitre.org/resources/legal-and-branding/terms-of-use/>
- **Licence text**: `reference/security/LICENSES/MITRE-ATTACK-Terms-of-Use.txt`
- **Doctrine's modifications**: `mitre/attack/techniques-summary.json` is a
  curated subset of techniques with Doctrine-written prioritisation notes.
- **Required attribution**: "(c) 2026 The MITRE Corporation. This work is
  reproduced and distributed with the permission of The MITRE Corporation."
- **Previous label**: the manifest said CC-BY-4.0. That was wrong; ATT&CK has
  never been under a Creative Commons licence.

### MITRE ATLAS

- **Upstream**: <https://atlas.mitre.org/>,
  <https://github.com/mitre-atlas/atlas-data>
- **Copyright**: Copyright 2021-2026 MITRE
- **Licence**: Apache License, Version 2.0
- **Licence URL**:
  <https://github.com/mitre-atlas/atlas-data/blob/main/LICENSE>
- **Licence text**: `reference/security/LICENSES/Apache-2.0.txt`
- **Doctrine's modifications**: `mitre/atlas/atlas-summary.json` is a
  Doctrine-written summary of ATLAS tactics and techniques; this entry is the
  change notice required by Apache-2.0 section 4(b). Upstream ships no
  `NOTICE` file (verified: contents API returns 404).
- **Previous label**: the manifest said CC-BY-4.0. That was wrong.

### MITRE D3FEND

- **Upstream**: <https://d3fend.mitre.org/>,
  <https://github.com/d3fend/d3fend-ontology>
- **Copyright**: Copyright (c) 2022 The MITRE Corporation
- **Licence**: MIT Licence
- **Licence URL**:
  <https://github.com/d3fend/d3fend-ontology/blob/develop/LICENSE.md>
- **Licence text**: `reference/security/LICENSES/MIT-D3FEND.md`
- **Doctrine's modifications**: `mitre/d3fend/d3fend-summary.json` is a
  Doctrine-written summary of the defensive technique taxonomy.
- **Previous label**: the manifest said Apache-2.0. That was wrong.

### MITRE CAPEC

- **Upstream**: <https://capec.mitre.org/>
- **Copyright**: Copyright (c) 2007-2026, The MITRE Corporation
- **Licence**: CAPEC Terms of Use — non-exclusive, royalty-free licence for
  research, development and commercial purposes, conditional on reproducing
  MITRE's copyright designation and the licence.
- **Licence URL**: <https://capec.mitre.org/about/termsofuse.html>
- **Licence text**: `reference/security/LICENSES/MITRE-CAPEC-Terms-of-Use.txt`
- **Doctrine's modifications**: `mitre/capec/capec-summary.json` is a
  Doctrine-written summary of attack patterns.
- **Required attribution**: "Copyright (c) 2007-2026, The MITRE Corporation.
  CAPEC and the CAPEC logo are trademarks of The MITRE Corporation."

### MITRE CWE

- **Upstream**: <https://cwe.mitre.org/>
- **Copyright**: Copyright (c) 2006-2026, The MITRE Corporation
- **Licence**: CWE Terms of Use — same structure as CAPEC.
- **Licence URL**: <https://cwe.mitre.org/about/termsofuse.html>
- **Licence text**: `reference/security/LICENSES/MITRE-CWE-Terms-of-Use.txt`
- **Doctrine's modifications**: `cwe/cwe-top-25-2025.json` and
  `cwe/cwe-common.json` are Doctrine-written summaries of CWE entries.
- **Required attribution**: "Copyright (c) 2006-2026, The MITRE Corporation.
  CWE, CWSS, CWRAF, and the CWE logo are trademarks of The MITRE Corporation."

### OWASP (Top 10 families and ASVS)

- **Upstream**: <https://owasp.org/Top10/>,
  <https://github.com/OWASP/Top10>, <https://github.com/OWASP/API-Security>,
  <https://owasp.org/ASVS/>, <https://github.com/OWASP/ASVS>,
  <https://github.com/OWASP/www-project-top-10-for-large-language-model-applications>
- **Licence**: Creative Commons Attribution-ShareAlike 4.0 International
  (CC BY-SA 4.0), verified individually for the Top 10, API Security, LLM Top
  10 and ASVS repositories.
- **Licence URL**: <https://github.com/OWASP/Top10/blob/master/LICENSE>,
  <https://github.com/OWASP/ASVS/blob/master/LICENSE.md>
- **Licence text**: `reference/security/LICENSES/CC-BY-SA-4.0.txt`
- **Doctrine's modifications**: the `owasp/*.json` files are Doctrine-written
  condensations of the risk and requirement lists.
- **ShareAlike**: to the extent those files are Adapted Material, they
  **MUST** be redistributed under CC BY-SA 4.0 or a BY-SA compatible licence,
  not under Doctrine's MIT licence.
- **Required attribution**: "Based on the OWASP Top 10 / OWASP ASVS (c) the
  OWASP Foundation, licensed under CC BY-SA 4.0
  (<https://creativecommons.org/licenses/by-sa/4.0/>). Modified by Doctrine."

### SigmaHQ

- **Upstream**: <https://github.com/SigmaHQ/sigma>
- **Licence**: split. The Sigma specification
  (<https://github.com/SigmaHQ/sigma-specification>) and the Sigma logo are
  public domain; the rules in the SigmaHQ repository are under the
  **Detection Rule License (DRL) 1.1**.
- **Licence URL**: <https://github.com/SigmaHQ/sigma/blob/master/LICENSE>,
  <https://github.com/SigmaHQ/Detection-Rule-License>
- **Licence text**: `reference/security/LICENSES/DRL-1.1.md`
- **Doctrine's modifications**: `sigma/rules-summary.json` documents the rule
  format (public-domain specification material) and indexes rule categories.
- **Required attribution**: where rule content is reproduced, DRL 1.1 requires
  retaining the rule author, a link to the rule set, and a statement that the
  rules are under the Detection Rule License.
- **Previous label**: the manifest said LGPL-2.1. That was wrong; SigmaHQ has
  not used LGPL for the rules.

### JA4 and JA4+ (FoxIO)

- **Upstream**: <https://github.com/FoxIO-LLC/ja4>
- **Copyright**: Copyright (c) 2026 FoxIO, LLC
- **Licence**: split, and the split matters.
  - **JA4** (TLS client fingerprinting) is **BSD-3-Clause** —
    <https://github.com/FoxIO-LLC/ja4/blob/main/LICENSE-JA4>
  - **All other JA4+ variants** (JA4S, JA4H, JA4L, JA4LS, JA4X, JA4T, JA4TS,
    JA4TScan, JA4D, JA4D6, JA4SScan, JA4E, JA4SSH) are under the
    **FoxIO License 1.1**, which grants copyright and distribution rights
    **for non-commercial purposes only** —
    <https://github.com/FoxIO-LLC/ja4/blob/main/LICENSE>
- **Licence text**: `reference/security/LICENSES/BSD-3-Clause-JA4.txt`,
  `reference/security/LICENSES/FoxIO-License-1.1.txt`
- **Doctrine's modifications**: `fingerprints/ja4/malware-signatures.json`
  documents the fingerprint formats and lists signature examples.
- **Restriction**: commercial redistribution of the JA4+ variant material
  requires a licence from FoxIO. Doctrine's MIT licence does **NOT** grant it.
- **Previous label**: the manifest said BSD-3-Clause for all JA4+ content.
  That was wrong and understated the restriction.

### SLSA

- **Upstream**: <https://slsa.dev/>, <https://github.com/slsa-framework/slsa>
- **Licence**: **Community Specification License 1.0**
- **Licence URL**:
  <https://github.com/slsa-framework/slsa/blob/main/LICENSE.md>
- **Licence text**:
  `reference/security/LICENSES/Community-Specification-1.0.md`
- **Doctrine's modifications**: `slsa/slsa-levels.json` summarises the build
  and source track levels.
- **Required attribution**: section 1.2 requires attribution to the Working
  Group including the material's name, version number and source. Cite
  "SLSA v1.2, SLSA Working Group, <https://slsa.dev/>".
- **Previous label**: the manifest said Apache-2.0. That was wrong.

### OpenSSF Scorecard

- **Upstream**: <https://securityscorecards.dev/>,
  <https://github.com/ossf/scorecard>
- **Licence**: Apache License, Version 2.0
- **Licence URL**: <https://github.com/ossf/scorecard/blob/main/LICENSE>
- **Licence text**: `reference/security/LICENSES/Apache-2.0.txt`
- **Doctrine's modifications**: `openssf/scorecard.json` summarises the
  checks. Upstream ships no `NOTICE` file (verified: contents API returns
  404).

### SBOM formats

- **Upstream**: CycloneDX — <https://github.com/CycloneDX/specification>;
  SPDX — <https://github.com/spdx/spdx-spec>; SWID — ISO/IEC 19770-2
- **Licence**: CycloneDX specification is Apache-2.0. The SPDX specification
  is Community Specification License 1.0, with pre-existing portions under
  CC BY 3.0. SWID is an ISO standard and is **not** reproduced here.
- **Licence URL**:
  <https://github.com/CycloneDX/specification/blob/master/LICENSE>,
  <https://github.com/spdx/spdx-spec/blob/development/v3.0.1/LICENSE>
- **Licence text**: `reference/security/LICENSES/Apache-2.0.txt`,
  `reference/security/LICENSES/Community-Specification-1.0.md`
- **Doctrine's modifications**: `sbom/sbom-formats.json` is a
  Doctrine-written comparison of the formats.

### CIS Critical Security Controls

- **Upstream**: <https://www.cisecurity.org/controls/v8-1>
- **Copyright**: Copyright (c) Center for Internet Security, Inc. (CIS)
- **Licence**: Creative Commons Attribution-NonCommercial-NoDerivatives 4.0
  International (CC BY-NC-ND 4.0)
- **Licence URL**:
  <https://creativecommons.org/licenses/by-nc-nd/4.0/legalcode>
- **Licence text**: `reference/security/LICENSES/CC-BY-NC-ND-4.0.txt`;
  directory notice at `reference/security/cis/NOTICE`
- **Restrictions**: CIS's published clarification permits copying and
  redistributing the Controls as a framework for non-commercial purposes with
  credit and a licence link, forbids distributing modified materials, and
  makes commercial use subject to prior CIS approval.
- **Doctrine's position**: `cis/controls-v8.json` is kept under the owner's
  decision to retain and cite vendored material. It **MUST NOT** be edited,
  reformatted or extended. See the caveat below.
- **Required attribution**: "CIS Critical Security Controls v8.1, Copyright
  (c) Center for Internet Security, Inc., licensed under CC BY-NC-ND 4.0
  (<https://creativecommons.org/licenses/by-nc-nd/4.0/>). See
  <http://www.cisecurity.org/controls/> for the current guidance."

**Caveat**: `cis/controls-v8.json` is a restructured JSON rendering of the CIS
Controls safeguards, not a verbatim copy. If that restructuring is an
adaptation rather than a permitted reproduction of factual control
identifiers, redistributing it breaches the NoDerivatives condition. That
question has not been settled with CIS. The safe resolutions are to obtain
written CIS permission, or to replace the file with control identifiers and
titles plus links to the CIS publication.

### NIST

- **Upstream**: <https://csrc.nist.gov/> (CSF 2.0, SP 800-53 r5, SP 800-207,
  SP 800-131A, SP 800-57, PQC)
- **Licence**: works of the United States Government are not subject to
  domestic copyright protection (17 U.S.C. 105). NIST asks for appropriate
  credit.
- **Licence URL**: <https://www.nist.gov/copyrights-disclaimers>
- **Doctrine's modifications**: `nist/*.json` and
  `crypto/cryptographic-standards.json` are Doctrine-written summaries.
- **Required attribution**: credit NIST as the source of the underlying
  publications.

### CISA Known Exploited Vulnerabilities catalog

- **Upstream**:
  <https://www.cisa.gov/known-exploited-vulnerabilities-catalog>
- **Licence**: US Government work, not subject to domestic copyright
  protection (17 U.S.C. 105). CISA publishes no separate licence file.
- **Doctrine's modifications**: `kev/known-exploited-vulnerabilities.json` is
  a filtered snapshot of the catalog.
- **Required attribution**: credit CISA as the source.

### EPSS (FIRST)

- **Upstream**: <https://www.first.org/epss/>
- **Licence**: EPSS scores are published freely with no registration; FIRST
  requests attribution when EPSS data is used in publications or products.
  There is no Creative Commons grant.
- **Licence URL**: <https://www.first.org/epss/faq>
- **Doctrine's modifications**: `epss/exploit-prediction.json` describes the
  model and scoring bands.
- **Required attribution**: credit the EPSS SIG at FIRST.
- **Previous label**: the manifest said CC-BY-SA-4.0. That was wrong.

### Doctrine-authored security summaries

`compliance/*.json`, `containers/container-security.json` and
`exploits/exploit-availability.json` are Doctrine's own writing. They name
third-party frameworks and tools — ISO 27001, PCI DSS, SOC 2, the CIS Docker
and Kubernetes Benchmarks, the NSA/CISA Kubernetes Hardening Guidance,
Exploit-DB, Metasploit, Nuclei — but do not reproduce their text. Those
standards remain under their publishers' own terms. Doctrine's MIT licence
covers only Doctrine's expression in these files.

## Other third-party material outside `reference/`

### Contributor Covenant

- **Upstream**: Contributor Covenant 3.0 —
  <https://www.contributor-covenant.org/version/3/0/>
- **Steward**: the Organization for Ethical Source
- **Licence**: Creative Commons Attribution-ShareAlike 4.0 International
  (CC BY-SA 4.0)
- **Licence URL**: <https://creativecommons.org/licenses/by-sa/4.0/>
- **Location**: [CODE_OF_CONDUCT.md](CODE_OF_CONDUCT.md)
- **Doctrine's modifications**: the two `[NOTE: ...]` placeholders in the
  upstream template were replaced with Doctrine's actual reporting route and
  enforcement statement, and a markdownlint directive was added at the top of
  the file. The rest is verbatim.
- **ShareAlike**: `CODE_OF_CONDUCT.md` is Adapted Material and is offered
  under CC BY-SA 4.0, not under Doctrine's MIT licence. The Attribution
  section at the end of the file carries the required credit.

## Corrections applied

The following labels in `reference/security/manifest.json` were wrong before
this change and have been corrected:

| Source | Was | Is |
| ------ | --- | -- |
| MITRE ATT&CK | CC-BY-4.0 | MITRE ATT&CK Terms of Use |
| MITRE ATLAS | CC-BY-4.0 | Apache-2.0 |
| MITRE D3FEND | Apache-2.0 | MIT |
| SigmaHQ rules | LGPL-2.1 | DRL-1.1 |
| JA4 / JA4+ | BSD-3-Clause | BSD-3-Clause (JA4) and FoxIO-1.1 (JA4+) |
| SLSA | Apache-2.0 | Community-Spec-1.0 |
| EPSS | CC-BY-SA-4.0 | Free to use, attribution requested |
| CIS Controls | CC-BY-NC-ND 4.0 | CC-BY-NC-ND-4.0 (SPDX form, with restrictions spelled out) |

## See Also

- [LICENSE](LICENSE) — MIT licence for Doctrine-authored content
- [README](README.md#licence) — licence summary
- [reference/security/NOTICE](reference/security/NOTICE) — security tree notice
- [reference/security/cis/NOTICE](reference/security/cis/NOTICE) — CIS
  no-derivatives notice
