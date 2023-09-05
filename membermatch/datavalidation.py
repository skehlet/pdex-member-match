from datetime import date
from icecream import ic
from .settings import FHIR_BASE_URL, CLIENT_ID, CLIENT_SECRET, TENANT, AUTH_URL, SECURE_URL
from .settings import FHIR_STORE_SENSITIVITY
from . import OperationOutcomeException, DEFAULT_CODE,DEFAULT_STATUS_CODE, DEFAULT_SEVERITY, DEFAULT_DESCRIPTION
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
    access_period = {}
    today = date.today()

    if consent.has_key("policy"):
        for i in consent['policy']:
            if i.has_key("uri"):
                if i['uri'] in [REGULAR, SENSITIVE]:
                    access_mode = i["uri"]
    if consent.has_key("provision"):
        if consent['provision'].has_key("type"):
            if consent['provision']['type'] == "permit":
                if consent['provision'].has_key("period"):
                    access_period = consent['provision']['period']
    start = ""
    end = ""
    if not access_period.has_key("start"):
        start = access_period['start']
    if not access_period.has_key("end"):
        end = access_period['end']

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
    else:
        # FHIR_STORE_SENSITIVITY =  "INCLUDED_NOLABEL"
        accepted = False
        if access_mode == REGULAR:
            accepted = True
    if accepted:
        # Write the Consent record for the member_id
        # it will be needed when an access token is requested
        # TODO Write FHIR Consent
        requesting_patient = ""
        if consent.has_key("patient"):
            requesting_patient = consent['patient']['reference']
            consent['patient']['reference'] = member
        if consent.has_key("performer"):
            if consent['performer']['reference'] == requesting_patient:
                consent['patient']['reference'] = member

        status_code, resp = write_fhir(calltype="POST", data=consent)
        if status_code in [200, 201, 204]:
            return accepted
        else:
            error = {'status_code': 422,
                     'code': DEFAULT_CODE, 'severity': DEFAULT_SEVERITY,
                     'description': "problem storing consent"}

            raise OperationOutcomeException(status_code=error['status_code'],
                                            description=error['description'])


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
    if SECURE_URL:
        access_token = TOKEN.get_token()
        headers ={"Accept": "application/json",
                  "Authorization": "Bearer %s" %access_token,
                  "Content-Type": "application/json"}
    else:
        headers = {"Accept": "application/json",
                   "Content-Type": "application/json"}
    if data.has_key("resourceType"):
        resource = data['resourceType']
        url = FHIR_BASE_URL + "/" + resource
    else:
        error = {'status_code': 406,
                 'code': DEFAULT_CODE, 'severity': DEFAULT_SEVERITY,
                 'description': "resourceType not specified"}

        raise OperationOutcomeException(status_code=error['status_code'],
                                        description=error['description'])

    response = requests.post(url, data=data, headers=headers)
    try:
        resp = response.json()
    except ValueError:
        resp = {}
    if response.status_code not in [200,201, 204]:
        logging.info(f"{response.status_code}:Problem with {calltype} call to FHIR Store")
        logging.info(response.content)
    logging.debug(resp)

    return response.status_code, resp


def valid_period(start="", end=""):

    today = date.today()
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
