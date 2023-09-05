# Da Vinci Payer Data Exchange (PDex) Member-Match Operation

The purpose of this operation is to receive a parameter bundle, following the definition in the Da Vinci Health Record Exchange (HRex) IG.

The content of the bundle are used to perform a member-match. if a 
successful match is made the operation returns a FHIR Patient ID.

The order of processing logic is as follows:

1. Match using Coverage resource.
2. Match using Coverage resource and patient Demographics.

A match can fail for the following reasons:

- No match found
- Too many matches

An operation Outcome should be returned with an Unproccessable Entity status code (422).

## Consent Handling

If a match is made it is then necessary to check the Consent resource. The 
Consent resource hastwo options for data sensitivity.

- Share all data
- Share non-sensitive data

Whether data can be shared with the requesting Payer will
depend upon how and what data is available in the FHIR API. There are 
three scenarios:

- No sensitive data is available via the FHIR API
- Sensitive data is available in the FHIR API and is labelled as sensitive
- Sensitive data is available in the FHIR API but is NOT labelled.

The Member Match function will have a setting to identify which category the FHIR Store supports:
# Values = "EXCLUDED" | "INCLUDED_LABELLED" | "INCLUDED_NOLABEL"
FHIR_STORE_SENSITIVITY = "EXCLUDED"  

In the first two scenarios the Payer can comply with the Censent and release data.
In the last scenario the Payer will have to decline to share data
if the member requested that only non-sensitive data be shared.

If Consent can't be complied with an unprocessable entity (422) status code
is returned with an operation outcome message.

## Consent values

- Allow non-sensitive:

         "policy": [
          {
            "uri": "http://hl7.org/fhir/us/davinci-hrex/StructureDefinition-hrex-consent.html#regular"
          }
        ],

- Allow Sensitive and Non-Sensitive:

         "policy": [
          {
            "uri": "http://hl7.org/fhir/us/davinci-hrex/StructureDefinition-hrex-consent.html#sensitive"
          }
        ],


## Test Environment

- Create a server (using HAPI)
- load sample coverage and patient resources
- create new parameter bundles that will enable matches to Patient and Coverage resources
- create new parameter bundles and patient and coverage resources that will fail
- 