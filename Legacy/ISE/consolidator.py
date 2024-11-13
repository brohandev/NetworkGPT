import logging
from pprint import pprint as pp

from Auxiliary.shared_functions import clean_json, write_to_json
from ISE.API_methods.policies_methods import get_ise_authentication_policies, get_ise_authorization_policies, get_ise_authorization_profiles, get_ise_local_exceptions
from Excel.excel_controller import ISE_KB_PATH


log = logging.getLogger(__name__)


def consolidate_authentication_policy_information():
    """
    1. Retrieve authentication policy list and policy-associated fields
    2.
    :return: (list[]) list containing authentication policy information represented as nested dict() objects
    """
    # Retrieve list of authentication policies and trim irrelevant fields
    auth_policy_list = get_ise_authentication_policies()
    policy_list = []
    for policy in auth_policy_list:
        stripped_policy_dict = {k: policy[k] for k in policy.keys() & {
            'rule',
            'identitySourceName'
        }}

        policy_rule = stripped_policy_dict['rule']
        stripped_rule_dict = {k: policy_rule[k] for k in policy_rule.keys() & {
            'name',
            'hitCounts',
            'state',
            'condition'
        }}

        # Move onto next authentication policy if current policy is disabled -> only account for enabled ones
        if stripped_rule_dict['state'] == 'disabled':
            continue

        conditions = []
        rule_condition = stripped_rule_dict['condition']
        condition_type = "ConditionReference"
        if rule_condition is not None:
            stripped_condition_dict = {k: rule_condition[k] for k in rule_condition.keys() & {
                'conditionType',
                'name',
                'description',
                'children'
            }}

            if 'children' in stripped_condition_dict.keys():
                condition_type = stripped_condition_dict['conditionType']
                for child_condition in stripped_condition_dict['children']:
                    conditions.append({
                        'name': child_condition['name'],
                        'description': child_condition['description']
                    })
            else:
                conditions.append({
                    'name': stripped_condition_dict['name'],
                    'description': stripped_condition_dict['description']
                })
        else:
            conditions.append({
                'name': 'Default',
                'description': 'Default'
            })

        revised_policy = {
            'name': stripped_rule_dict['name'],
            'state': stripped_rule_dict['state'],
            'hits': stripped_rule_dict['hitCounts'],
            'identitySources': stripped_policy_dict['identitySourceName'],
            'conditionType': condition_type,
            'conditions': conditions
        }

        policy_list.append(revised_policy)

    return policy_list


def consolidate_authorization_policy_information():
    # Retrieve list of authorization policies and trim irrelevant fields
    auth_policy_list = get_ise_authorization_policies()
    auth_profile_list = get_ise_authorization_profiles()
    policy_list = []
    for policy in auth_policy_list:
        stripped_policy_dict = {k: policy[k] for k in policy.keys() & {
            'rule',
            'profile',
            'securityGroup'
        }}

        policy_rule = stripped_policy_dict['rule']
        stripped_rule_dict = {k: policy_rule[k] for k in policy_rule.keys() & {
            'name',
            'hitCounts',
            'state',
            'condition'
        }}

        # Move onto next authorization policy if current policy is disabled -> only account for enabled ones
        if stripped_rule_dict['state'] == 'disabled':
            continue

        conditions = []
        rule_condition = stripped_rule_dict['condition']
        condition_type = "ConditionReference"
        if rule_condition is not None:
            stripped_condition_dict = {k: rule_condition[k] for k in rule_condition.keys() & {
                'name',
                'conditionType',
                'children',
                'dictionaryName',
                'attributeName',
                'operator',
                'attributeValue',
                'description'
            }}

            if 'children' in stripped_condition_dict.keys():
                condition_type = stripped_condition_dict['conditionType']
                for child_condition in stripped_condition_dict['children']:
                    if child_condition['conditionType'] == 'ConditionReference':
                        conditions.append({
                            'name': child_condition['name'],
                            'description': child_condition['description']
                        })
                    elif child_condition['conditionType'] == 'ConditionAttributes':
                        conditions.append({
                            'name': child_condition['dictionaryName'],
                            'description': child_condition['attributeName'] + " " + child_condition['operator'] + " " + child_condition['attributeValue']
                        })
            else:
                condition_type = stripped_condition_dict['conditionType']
                if condition_type == 'ConditionReference':
                    conditions.append({
                        'name': stripped_condition_dict['name'],
                        'description': stripped_condition_dict['description']
                    })
                elif condition_type == 'ConditionAttributes':
                    conditions.append({
                        'name': stripped_condition_dict['dictionaryName'],
                        'description': stripped_condition_dict['attributeName'] + " " + stripped_condition_dict['operator'] + " " + stripped_condition_dict['attributeValue']
                    })

        else:
            conditions.append({
                'name': 'Default',
                'description': 'Default'
            })

        # Retrieve list of authorization profiles
        profile_list = stripped_policy_dict['profile']
        revised_profile_list = []
        for profile in profile_list:
            for auth_profile in auth_profile_list:
                if profile == auth_profile['name']:
                    revised_profile_list.append(
                        {
                            'profileName': profile,
                            'vlan': auth_profile['vlan']
                        }
                    )
                    break

        revised_policy = {
            'name': stripped_rule_dict['name'],
            'state': stripped_rule_dict['state'],
            'hits': stripped_rule_dict['hitCounts'],
            'conditionType': condition_type,
            'conditions': conditions,
            'profile': revised_profile_list,
            'securityGroupTag (SGT)': stripped_policy_dict['securityGroup']
        }

        policy_list.append(revised_policy)

    return policy_list


def consolidate_authorization_exceptions():
    # Retrieve list of exceptions and trim irrelevant fields
    exception_list = get_ise_local_exceptions()
    auth_profile_list = get_ise_authorization_profiles()
    final_exception_list = []
    for exception in exception_list:
        stripped_policy_dict = {k: exception[k] for k in exception.keys() & {
            'rule',
            'profile',
            'securityGroup'
        }}

        policy_rule = stripped_policy_dict['rule']
        stripped_rule_dict = {k: policy_rule[k] for k in policy_rule.keys() & {
            'name',
            'hitCounts',
            'state',
            'condition'
        }}

        # Move onto next exception if current exception is disabled -> only account for enabled ones
        if stripped_rule_dict['state'] == 'disabled':
            continue

        conditions = []
        rule_condition = stripped_rule_dict['condition']
        condition_type = "ConditionReference"
        if rule_condition is not None:
            stripped_condition_dict = {k: rule_condition[k] for k in rule_condition.keys() & {
                'name',
                'conditionType',
                'children',
                'dictionaryName',
                'attributeName',
                'operator',
                'attributeValue',
                'description'
            }}

            if 'children' in stripped_condition_dict.keys():
                condition_type = stripped_condition_dict['conditionType']
                for child_condition in stripped_condition_dict['children']:
                    if child_condition['conditionType'] == 'ConditionReference':
                        conditions.append({
                            'name': child_condition['name'],
                            'description': child_condition['description']
                        })
                    elif child_condition['conditionType'] == 'ConditionAttributes':
                        conditions.append({
                            'name': child_condition['dictionaryName'],
                            'description': child_condition['attributeName'] + " " + child_condition['operator'] + " " + child_condition['attributeValue']

                        })
            else:
                condition_type = stripped_condition_dict['conditionType']
                if condition_type == 'ConditionReference':
                    conditions.append({
                        'name': stripped_condition_dict['name'],
                        'description': stripped_condition_dict['description']
                    })
                elif condition_type == 'ConditionAttributes':
                    conditions.append({
                        'name': stripped_condition_dict['dictionaryName'],
                        'description': stripped_condition_dict['attributeName'] + " " + stripped_condition_dict['operator'] + " " + stripped_condition_dict['attributeValue']
                    })

        else:
            conditions.append({
                'name': 'Default',
                'description': 'Default'
            })

        # Retrieve list of authorization profiles
        profile_list = stripped_policy_dict['profile']
        revised_profile_list = []
        for profile in profile_list:
            for auth_profile in auth_profile_list:
                if profile == auth_profile['name']:
                    revised_profile_list.append(
                        {
                            'profileName': profile,
                            'vlan': auth_profile['vlan']
                        }
                    )
                    break

        revised_exception = {
            'name': stripped_rule_dict['name'],
            'state': stripped_rule_dict['state'],
            'hits': stripped_rule_dict['hitCounts'],
            'conditionType': condition_type,
            'conditions': conditions,
            'profile': revised_profile_list,
            'securityGroupTag (SGT)': stripped_policy_dict['securityGroup']
        }

        final_exception_list.append(revised_exception)

    return final_exception_list


def consolidate_ise_information():
    """
    Generate a single json object containing all information about the WAN from vManage
    :return:
    """

    ise_information = {
        "AUTHENTICATION_POLICIES": consolidate_authentication_policy_information(),
        "AUTHORIZATION_POLICIES": consolidate_authorization_policy_information(),
        "EXCEPTION_RULES": consolidate_authorization_exceptions()
    }

    cleaned_ise_information = clean_json(ise_information)
    return cleaned_ise_information


def generate_ISE_KB():
    try:
        ise_information = consolidate_ise_information()
        write_to_json(document=ISE_KB_PATH, content=ise_information)
        log.info("ISE KB Update: Update Successful")
    except:
        log.info("ISE KB Update: Update Unuccessful")


if __name__ == '__main__':
    generate_ISE_KB()
