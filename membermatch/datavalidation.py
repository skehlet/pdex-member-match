from datetime import date
from icecream import ic
from .settings import FHIR_BASE_URL, CLIENT_ID, CLIENT_SECRET, TENANT, AUTH_URL, SECURE_URL
from .settings import FHIR_STORE_SENSITIVITY
from .classes import OperationOutcomeException, DEFAULT_CODE,DEFAULT_STATUS_CODE, DEFAULT_SEVERITY, DEFAULT_DESCRIPTION
from requests import request
from .accesstoken import AccessToken
import logging
import requests

REGULAR = "http://hl7.org/fhir/us/davinci-hrex/StructureDefinition-hrex-consent.html#regular"
SENSITIVE = "http://hl7.org/fhir/us/davinci-hrex/StructureDefinition-hrex-consent.html#sensitive"

TOKEN = AccessToken(CLIENT_ID, CLIENT_SECRET, FHIR_BASE_URL, TENANT, AUTH_URL)


def unique_match_on_coverage(coverage={}, member={}):
    '''
    match on coverage
    '''
    msg = "we are in the unique match on coverage function (datavalidation.py)"
    ic(f"msg:{msg}")
    ic(coverage)
    ic(member)

    # build search query to FHIR Server
    coverage_response = coverage_query(coverage, member)

    ic(coverage_response)
    return coverage_response


def load_parameters(data={}):
    '''
    Load the parameters into dictionaries
    :param data:
    :return:
    '''

    member = {}
    coverage = {}
    consent = {}

    for param in data['parameter']:
        if param['name'] == "MemberPatient":
            member = param['resource']
        elif param['name'] == "CoverageToMatch":
            coverage = param['resource']
        elif param['name'] == "Consent":
            consent = param['resource']

    return member, coverage, consent


def coverage_query(coverage={}, member={}):
    """
    search coverage and return bundle.entry

    :param coverage:
    :return:
    """
    if SECURE_URL:
        access_token = TOKEN.get_token()
        headers = {"Accept": "application/json",
                   "Authorization": "Bearer %s" % access_token,
                   "Content-Type": "application/json"}
    else:
        headers = {"Accept": "application/json",
                   "Content-Type": "application/json"}

    # build search query to FHIR Server
    query = FHIR_BASE_URL + "/Coverage?identifier=" + coverage['identifier'][0]['value']
    query = query + "&beneficiary.name=" + member['name'][0]['given'][0]
    query = query + "&beneficiary.birthdate=" + member['birthDate']
    # query = query + "&beneficiary.family=" + member['name']['family']
    query = query + "&beneficiary.gender=" + member['gender']

    query_result = call_fhir(calltype="SEARCH", query=query)
    return query_result


def evaluate_consent(consent={}, member=""):
    """
    Evaluate Consent request against FHIR Store capability

        "policy": [
          {
            "uri": "http://hl7.org/fhir/us/davinci-hrex/StructureDefinition-hrex-consent.html#regular"
          }
        ],
        "provision": {
          "type": "permit",
          "period": {
            "start": "2022-01-01",
            "end": "2022-01-31"
          },

    :param consent:
    :param member:
    :return accepted = True | False:
    """
    access_mode = ""
    ic(member)
    access_period = {}
    today = date.today().isoformat()
    ic("Evaluating consent")
    ic(consent)
    ic(today)
    if "policy" in consent.keys():
        ic("checking consent policy")
        for i in consent['policy']:
            ic(consent['policy'])
            if "uri" in i.keys():
                ic(i['uri'])
                if i['uri'] in [REGULAR, SENSITIVE]:
                    access_mode = i["uri"]
    if "provision" in consent.keys():
        ic("checking provision")
        if "type" in consent['provision'].keys():
            if consent['provision']['type'] == "permit":
                if "period" in consent['provision'].keys():
                    access_period = consent['provision']['period']
    ic(access_period)
    start = ""
    end = ""
    if "start" in access_period.keys():
        start = access_period['start']
    if "end" in access_period.keys():
        end = access_period['end']
    ic(access_period)
    ic(start)
    ic(end)
    if not valid_period(start, end):
        # write an error
        # operation outcome = 422
        error = {'status_code': 422,
                 'code': DEFAULT_CODE, 'severity': DEFAULT_SEVERITY,
                 'description': "Consent period is not valid"}

        raise OperationOutcomeException(status_code=error['status_code'],
                                        description=error['description'])

    if FHIR_STORE_SENSITIVITY in ["EXCLUDED", "INCLUDED_LABELLED"]:
        accepted = True
        ic(FHIR_STORE_SENSITIVITY)
    else:
        # FHIR_STORE_SENSITIVITY =  "INCLUDED_NOLABEL"
        ic(FHIR_STORE_SENSITIVITY)
        accepted = False
        if access_mode == REGULAR:
            accepted = True
    if accepted:
        # Write the Consent record for the member_id
        # it will be needed when an access token is requested
        ic("attempting to write consent")
        requesting_patient = ""
        if "patient" in consent.keys():
            requesting_patient = consent['patient']['reference']
            ic(requesting_patient)
            ic(member)
            consent['patient']['reference'] = member
        if "performer" in consent.keys():
            if consent['performer'][0]['reference'] == requesting_patient:
                consent['performer'][0]['reference'] = member
        if "sourceReference" in consent.keys():
            if "reference" in consent['sourceReference'].keys():
                consent['sourceReference']['display'] = consent['sourceReference']['reference']
                del consent['sourceReference']["reference"]
        ic("updated consent")
        ic(consent)
        print(consent)
        data = {}
        ic("calling write_fhir module")
        status_code, resp = write_fhir(calltype="POST", data=consent)
        if status_code in [200, 201, 204]:
            return accepted
            ic(status_code)
        else:
            ic("there was a problem")
            error = {'status_code': 422,
                     'code': DEFAULT_CODE, 'severity': DEFAULT_SEVERITY,
                     'description': "problem storing consent"}

            raise OperationOutcomeException(status_code=error['status_code'],
                                            description=error['description'])

    return accepted


def call_fhir(calltype="GET", query="", id=""):
    """
    calltype = GET OR SEARCH
    """
    if SECURE_URL:
        access_token = TOKEN.get_token()
        headers ={"Accept": "application/json",
                  "Authorization": "Bearer %s" %access_token,
                  "Content-Type": "application/json"}
    else:
        headers = {"Accept": "application/json",
                   "Content-Type": "application/json"}

    response = requests.get(query, headers=headers)
    try:
        resp = response.json()
    except ValueError:
        resp = {}
    if response.status_code not in [200,201, 204]:
        logging.info(f"{response.status_code}:Problem with {calltype} call to FHIR Store")
        logging.info(response.content)
    logging.debug(resp)
    return response.status_code, resp


def write_fhir(calltype="POST", data={}):
    """
    Write Consent record to FHIR Store
    :param calltype:
    :param data:
    :return status_code, resp:
    """
    ic("writing FHIR resource")
    if SECURE_URL:
        access_token = TOKEN.get_token()
        headers ={"Accept": "application/json",
                  "Authorization": "Bearer %s" %access_token,
                  "Content-Type": "application/json"}
    else:
        headers = {"Accept": "application/json",
                   "Content-Type": "application/json"}
    ic(data)
    if "resourceType" in data.keys():
        resource = data['resourceType']
        url = FHIR_BASE_URL + "/" + resource
        ic(url)
    else:
        ic("no resourceType")
        error = {'status_code': 406,
                 'code': DEFAULT_CODE, 'severity': DEFAULT_SEVERITY,
                 'description': "resourceType not specified"}

        raise OperationOutcomeException(status_code=error['status_code'],
                                        description=error['description'])
    ic(data)
    response = requests.post(url, json=data, headers=headers)
    try:
        resp = response.json()
    except ValueError:
        resp = {}
    ic(resp)
    if response.status_code not in [200,201, 204]:
        logging.info(f"{response.status_code}:Problem with {calltype} call to FHIR Store")
        logging.info(response.content)
    logging.debug(resp)

    return response.status_code, resp


def valid_period(start="", end=""):
    # ic(start)
    # ic(end)
    today = date.today().isoformat()
    ic(today)
    valid_start = False
    valid_end = False
    if start:
        if start <= today:
            valid_start = True
    else:
        valid_start = True
    if end:
        if end >= today:
            valid_end = True
    else:
        valid_end = True
    ic(valid_start)
    ic(valid_end)
    if valid_start and valid_end:
        valid = True
    else:
        valid = False
    ic(valid)
    return valid


def get_metadata():
    '''
    Check the HAPI Server
    :return:
    '''

    if SECURE_URL:
        access_token = TOKEN.get_token()
        headers ={"Accept": "application/json",
                  "Authorization": "Bearer %s" %access_token,
                  "Content-Type": "application/json"}
    else:
        headers = {"Accept": "application/json",
                   "Content-Type": "application/json"}
    url = FHIR_BASE_URL + "/metadata"
    # url = "http://0.0.0.0:8080/fhir" + "/metadata"
    ic(url)

    response = requests.get(url, headers=headers)
    try:
        resp = response.json()
    except ValueError:
        resp = {}
    # ic(resp)
    if response.status_code not in [200,201, 204]:
        logging.info(f"{response.status_code}:Problem with {calltype} call to FHIR Store")
        logging.info(response.content)
    # logging.debug(resp)

    return response.status_code, resp
