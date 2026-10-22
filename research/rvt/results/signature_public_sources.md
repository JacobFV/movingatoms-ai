# Public sources: foreign RVT acceptance and SignatureMarker

Research date: 2026-10-22. This is a bounded search of Autodesk documentation,
ODA product documentation and a published Autodesk patent application. No
proprietary implementation was inspected. Source URLs, dates, search terms and
claim boundaries are recorded in [signature_public_sources.json](signature_public_sources.json).

## A significant correction to the blocker assessment

Autodesk explicitly documents opening third-party-produced RVT files. Its
Revit 2023 help describes an origin warning that permits the user to continue,
while saying Autodesk does not support those files. Origin notices also track
foreign content introduced into other projects. The corresponding 2024, 2025
and 2026 pages describe the same behavior. This rules out the blanket claim
that an Autodesk-origin file is always required to open in desktop Revit.
[Autodesk 2023 help](https://help.autodesk.com/cloudhelp/2023/ENU/Revit-GetStarted/files/GUID-7CEDA377-9C1B-4486-B127-492922233759.htm),
[2024](https://help.autodesk.com/cloudhelp/2024/ENU/Revit-GetStarted/files/GUID-7CEDA377-9C1B-4486-B127-492922233759.htm),
[2025](https://help.autodesk.com/cloudhelp/2025/ENU/Revit-GetStarted/files/GUID-7CEDA377-9C1B-4486-B127-492922233759.htm),
[2026](https://help.autodesk.com/cloudhelp/2026/ENU/Revit-GetStarted/files/GUID-7CEDA377-9C1B-4486-B127-492922233759.htm).

Autodesk separately documents a filename-based preference for suppressing the
foreign-file opening dialog. This is a user-interface setting, not a recipe
for changing RVT bytes or disabling integrity validation.
[Autodesk Revit.ini documentation](https://help.autodesk.com/cloudhelp/2023/ENU/Revit-Customize/files/GUID-1C00E999-B157-4640-90BC-75AFA0AB56B3.htm).

ODA states that BimRv provides compatible full and incremental RVT writes
without requiring Revit. Its FAQ says new project/family creation begins with
a template. These are the vendor's product claims, not validation of this
repository's writer; neither page publishes the footer representation.
[ODA BimRv product page](https://www.opendesign.com/products/bimrv),
[ODA BimRv FAQ](https://www.opendesign.com/faq/bimrv).

## What this means for the 64-byte field

**Inference, not identification:** the field's embedded `SignatureMarker`
name and Autodesk producer text are consistent with a producer-authentication
role that could feed the documented foreign-file warning. This interpretation
is now more useful than assuming every non-Autodesk signature is fatal. But
none of the primary sources ties the warning to this exact 64-byte field,
identifies a crypto algorithm, or specifies a valid foreign-producer encoding.
A producer marker can itself use a cryptographic signature; these explanations
are not mutually exclusive.

In particular, the documentation does **not** prove that clearing private and
public fields on a nonempty group is sufficient, nor that a stale private
field is harmless. The source corpus has only empty-element groups with empty
fields. Existing unsigned controls remain experiments. A technically valid
foreign file and a structurally corrupted file must not be conflated.

Cloud acceptance is a separate question. Autodesk's support article dated
2026-07-29 lists third-party-exported or invalid models and an origin-warning
example among potential causes of failed cloud extraction. It supplies no
universal pass/fail rule for our candidates. Desktop foreign-file opening
therefore does not establish Viewer, BIM 360 or Forma extraction success.
[Autodesk extraction troubleshooting](https://www.autodesk.com/support/technical/article/caas/sfdcarticles/sfdcarticles/BIM-360-Docs-Processing-failed-when-trying-to-upload-a-Revit-file.html).

## Published algorithm search

The bounded searches found no primary technical description of
`SignatureMarker`, `m_privateSignature`, the exact embedded producer text's
wire role, or an unsigned nonempty-group encoding. This is a search result,
not proof that such material does not exist.

Autodesk's application US20030221105A1, published 2003-11-27, describes generic
file-specific signature components and shared certificate services. Its text
does not mention Revit or SignatureMarker and provides no mapping to our
observed 64-byte field. It cannot justify selecting its scheme for RVT or
claiming a signing implementation has been recovered.
[Published patent application](https://patents.google.com/patent/US20030221105A1/en).

The next practical objective is a correctly framed, correctly linked foreign
RVT candidate with honest producer handling, preserving untouched source
content. Signing as Autodesk is not established as a prerequisite. Actual
candidate acceptance, including save/reopen and any cloud-specific handling,
remains untested.
