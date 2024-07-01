import os

from flask import Flask, request, jsonify, Response
from icecream import ic
import requests
from .settings import (
    DEFAULT_PORT,
    DEFAULT_DESCRIPTION,
    DEFAULT_SEVERITY,
    DEFAULT_CODE,
    DEFAULT_STATUS_CODE,
    REQUIRED_PARAMETERS,
    DEFAULT_FHIR_STORE_PORT
)
from .classes import OperationOutcomeException
from .datavalidation import unique_match_on_coverage, load_parameters, evaluate_consent, get_metadata

import json
import uuid

debug_mode = True
app = Flask(__name__)


def validated_data(data={}):
    '''
    check for data validity
    :return:
    '''

    validated = True
    error = {'status_code': DEFAULT_STATUS_CODE,
             'code': DEFAULT_CODE,
             'severity': DEFAULT_SEVERITY,
             'description': DEFAULT_DESCRIPTION}

    if (data.get('resourceType') and data.get('id')):
        if not (data['resourceType'] == "Parameters" and data['id'] == 'member-match-in'):
            validated = False
            error['description'] = "member-match-in parameters not submitted in POST body"
            error['status_code'] = 422
            raise OperationOutcomeException(status_code=error['status_code'],
                                            description=error['description'])

    else:
        validated = False
        error['description'] = "badly formatted parameters in POST body"
        error['status_code'] = 422
        raise OperationOutcomeException(status_code=error['status_code'],
                                        description=error['description'])

    if data.get('parameter'):
        ic(f"Number of Parameters:{len(data['parameter'])}")
        if len(data['parameter']) > 2:
            pass
        else:
            validated = False
            error['description'] = "insufficient parameters in POST body"
            error['status_code'] = 422
            raise OperationOutcomeException(status_code=error['status_code'],
                                            description=error['description'])
        required_parameters = []
        for i in data['parameter']:
            if i.get('name'):
                if i['name'] in REQUIRED_PARAMETERS:
                    required_parameters.append(i['name'])
        ic(len(required_parameters))
        ic(required_parameters)
        ic(len(REQUIRED_PARAMETERS))
        if (len(required_parameters) != len(REQUIRED_PARAMETERS)):
            validated = False
            error['description'] = "Required parameters are missing check for " + ', '.join(map(str, REQUIRED_PARAMETERS))
            error['status_code'] = 422
            raise OperationOutcomeException(status_code=error['status_code'],
                                            description=error['description'])

    else:
        validated = False
        error['description'] = "no parameter element in POST body"
        error['status_code'] = 422
        raise OperationOutcomeException(status_code=error['status_code'],
                                        description=error['description'])
    ic(f"data is good")
    return data


def build_operation_outcome(error, ooid=uuid.uuid4()):
    '''
    Create an Operation Outcome dict
    :param error:
    :param id:
    :return:
    '''
    ic(f"Executing OO Build:{error}")
    oo = {
  "resourceType" : "OperationOutcome",
  "id" : str(ooid),
  "text" : {
    "status" : "generated",
    "div" : "<div xmlns=\"http://www.w3.org/1999/xhtml\">\n      <p>" + error['description'] + "</p>\n    </div>"
  },
  "issue" : [{
    "severity" : error['severity'],
    "code" : error['code'] + ":" + str(error['status_code']),
    "details" : {
      "text" : error['description']
    }
  }]
}
    return oo


@app.errorhandler(OperationOutcomeException)
def handle_operation_outcomes_exception(error):
    ic(f"error:{type(error)}")
    response = Response(json.dumps(build_operation_outcome(vars(error)), indent=4),
                        status=error.status_code,
                        mimetype='application/json')
    ic(response)
    return response


@app.errorhandler(OperationOutcomeException)
def handle_operation_outcomes_exception(error):
    ic(f"error:{type(error)}")
    response = Response(json.dumps(build_operation_outcome(vars(error)), indent=4),
                        status=error.status_code,
                        mimetype='application/json')
    ic(response)
    return response


@app.route('/')
def hello_world():
    '''
    Test the matcher works
    '''
    return 'Hello, World!'


@app.route('/metadata')
def metadata():
    '''
    Test the HAPI Server access
    :return:
    '''

    status_code, response = get_metadata()
    ic(status_code)
    # ic(response)
    # return "hello! I'm HAPI"
    return jsonify(response)


@app.route('/$member-match', methods=['POST'])
def member_match():
    '''
    process a member-match operation
    :return:
    '''

    data = request.get_json()

    v_data = validated_data(data)
    # if v_data:
    #     result = True
    # else:
    #     result = False
    member, coverage, consent = load_parameters(data)
    m_data = unique_match_on_coverage(coverage, member)
    ic(m_data)
    ic(m_data[0])
    ic(m_data[1])
    m_data1 = m_data[1]
    member_id = ""
    if 'entry' not in m_data1:
        raise OperationOutcomeException(status_code=422,
                                        description="No match")

    if len(m_data1['entry']) == 1:
        member_id = m_data1['entry'][0]['resource']['beneficiary']['reference']
        ic(member_id)
        # We have a unique member. Now check Consent
        comply = evaluate_consent(consent, member_id)
        return jsonify({'member_id': member_id})


# Reverse proxy everything else to the HAPI FHIR server
# Taken from: https://github.com/0xe2d0/Flask-Reverse-Proxy/blob/main/proxy.py
@app.route("/<path:path>",methods=["GET","POST"])
def proxy(path):
    # global SITE_NAME
    SITE_NAME = f"http://localhost:{DEFAULT_FHIR_STORE_PORT}/"
    if request.method=="GET":
        resp = requests.get(f"{SITE_NAME}{path}")
        excluded_headers = ["content-encoding", "content-length", "transfer-encoding", "connection"]
        headers = [(name, value) for (name, value) in  resp.raw.headers.items() if name.lower() not in excluded_headers]
        response = Response(resp.content, resp.status_code, headers)
        return response
    elif request.method=="POST":
        resp = requests.post(f"{SITE_NAME}{path}",data=request.form)
        excluded_headers = ["content-encoding", "content-length", "transfer-encoding", "connection"]
        headers = [(name, value) for (name, value) in resp.raw.headers.items() if name.lower() not in excluded_headers]
        response = Response(resp.content, resp.status_code, headers)
        return response


if __name__ == '__main__':

    app.run(port=DEFAULT_PORT, debug=debug_mode)

