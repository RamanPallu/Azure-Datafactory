import requests
from pprint import pprint


class WikiApiException(Exception):
    pass


class WikidataApi:

    def __init__(self):
        self.base_url = 'https://www.wikidata.org/w/api.php'

    def get_data(self, payload):
        resp = requests.get(self.base_url, params=payload).json()
        if resp["success"] == 1:
            return resp
        else:
            raise WikiApiException("Failure in wikidata API call")


class WikidataParser:

    def __init__(self, properties, corporate_company_props):
        self.api_client = WikidataApi()
        self.properties = properties
        self.corporate_company_props = corporate_company_props

    def extract_corporate_entity_details(self, name):
        search_result = self.search_for_corporate_entities(name)
        if search_result:
            qid, corporate_entity = search_result
            entity_claims = corporate_entity['entities'][qid]['claims']
            entity_dict = {"_id": qid, 'label': {}}
            for lang in corporate_entity['entities'][qid]['labels']:
                # if  r['entities'][qid]['labels'][lang]['value']:
                entity_dict['label'][lang] = corporate_entity['entities'][qid]['labels'][lang]['value']
            entity_dict['descriptions'] = {}
            for lang in corporate_entity['entities'][qid]['descriptions']:
                # entity_dict["description_"+lang] = corporate_entity['entities'][qid]['descriptions'][lang]['value']
                entity_dict['descriptions'][lang] = corporate_entity['entities'][qid]['descriptions'][lang]['value']

            entity_dict['aliases'] = {}
            for lang in corporate_entity['entities'][qid]['aliases']:
                entity_dict['aliases'][lang] = ",".join(
                    [alias['value'] for alias in corporate_entity['entities'][qid]['aliases'][lang]])

            props = self.parse_props(entity_claims)

            entity_dict.update(props)

            return entity_dict

    def extract_subsidary_entity_details(self, name):
        search_result = self.search_for_corporate_entities(name)
        if search_result:
            qid, corporate_entity = search_result
            entity_claims = corporate_entity['entities'][qid]['claims']
            entity_dict = {"_id": qid, 'label': {}}
            for lang in corporate_entity['entities'][qid]['labels']:
                # if  r['entities'][qid]['labels'][lang]['value']:
                entity_dict['label'][lang] = corporate_entity['entities'][qid]['labels'][lang]['value']
            entity_dict['descriptions'] = {}
            for lang in corporate_entity['entities'][qid]['descriptions']:
                # entity_dict["description_"+lang] = corporate_entity['entities'][qid]['descriptions'][lang]['value']
                entity_dict['descriptions'][lang] = corporate_entity['entities'][qid]['descriptions'][lang]['value']

            entity_dict['aliases'] = {}
            for lang in corporate_entity['entities'][qid]['aliases']:
                entity_dict['aliases'][lang] = ",".join(
                    [alias['value'] for alias in corporate_entity['entities'][qid]['aliases'][lang]])

            props = self.parse_props(entity_claims)

            entity_dict.update(props)

            return entity_dict

    def search_for_corporate_entities(self, name):
        search_results = self.search_entities(name)
        matched_entity = None
        for search_result in search_results['search']:
            qid = search_result['id']
            entity = self.get_entity(qid)
            entity_claims = entity['entities'][qid]['claims']
            if self.is_corporate_entity(entity_claims):
                matched_entity = (qid, entity)
                break
        return matched_entity

    def search_for_subsidary_entities(self, name):
        search_results = self.search_entities(name)
        matched_entity = None
        for search_result in search_results['search']:
            qid = search_result['id']
            entity = self.get_entity(qid)
            entity_claims = entity['entities'][qid]['claims']
            matched_entity = (qid, entity)
        return matched_entity

    def parse_props(self, prop_claims, props_to_parse=None):
        if props_to_parse is None:
            props_to_parse = self.properties
        out = {}

        for prop in props_to_parse:
            if prop in prop_claims:
                prop_claim = prop_claims[prop]
                out[prop] = self.parse_prop_claim(prop_claim)
            else:
                print("Property %s not found on wikidata" % (prop))
        return out

    def parse_prop_claim(self, prop_claim):
        value_list = []
        for _item in prop_claim:
            datatype = _item['mainsnak']['datatype']
            if datatype == "wikibase-item":
                value_list.extend(self.parse_base_item(_item))
            elif datatype == "url":
                value_list.extend(self.parse_url_item(_item))
            elif datatype == "monolingualtext":
                value_list.extend(self.parse_monolingual_text(_item))
        return value_list

    def parse_base_item(self, _item):
        value_list = []
        if self.is_latest_time_prop(_item):
            value_id = _item['mainsnak']['datavalue']['value']['id']
            label_req = self.api_client.get_data(self.get_label_query_params([value_id]))
            if 'en' in label_req['entities'][value_id]['labels']:
                value_label = label_req['entities'][value_id]['labels']['en']['value']
                value_list.append((value_id, value_label))
            else:
                print('en not present')
                print(label_req)
        return value_list

    def parse_url_item(self, _item):
        value_list = []
        if _item['mainsnak']['datatype'] == 'url':
            value = _item['mainsnak']['datavalue']['value']
            value_list.append(value)
        return value_list

    def parse_monolingual_text(self, _item):
        return [_item['mainsnak']['datavalue']['value']['text']]

    def get_entity_params(self, qid, action='wbgetentities', langs=['en']):
        params = {
            'action': action,
            'format': 'json',
            # 'property': 'claims',
            'languages': "|".join(langs),
            'ids': qid
        }
        return params

    def get_label_query_params(self, q_list, action='wbgetentities'):
        params = {
            'action': action,
            'format': 'json',
            'props': 'labels',
            'languages': "en",
            'ids': "|".join(q_list)
        }
        return params

    def is_latest_time_prop(self, claim_dict):
        if not 'qualifiers' in claim_dict:
            return True
        else:
            # P580 - start time, P582 - end time
            # if end time is there then info is old
            if 'P582' in claim_dict['qualifiers']:
                return False
            else:
                return True

    def search_entities(self, name):
        payload = {'action': 'wbsearchentities',
                   'search': name,
                   'language': 'en',
                   'format': 'json',
                   'limit': 3,
                   }
        return self.api_client.get_data(payload)

    def get_entity(self, qid):
        return self.api_client.get_data(self.get_entity_req_params(qid))

    def is_corporate_entity(self, entity_claims):
        return any(prop in entity_claims for prop in self.corporate_company_props)

    def get_entity_req_params(self, qid, action='wbgetentities', langs=None):
        if langs is None:
            langs = ['en']
        params = {
            'action': action,
            'format': 'json',
            'languages': "|".join(langs),
            'ids': qid
        }
        return params

    def rename_propsId_to_props_name(self, propsNameMap, data):
        for propsId in propsNameMap:
            if propsId in data.keys():
                data[propsNameMap[propsId]] = data[propsId]
                data.pop(propsId)
        return data

    def generate_new_dataset(self, propsNameMap, data):
        temp_data = {}
        label_list = []
        description_list = []
        aliases_list = []
        industry_dict = {}
        found_dict = {}
        headquarters_list = []
        country_list = []
        official_list = []
        subsidiary_dict = {}
        for each in propsNameMap:
            if each in data.keys():
                temp_data["source_wikidata_id"] = data["_id"]
                temp_data["corp_id"] = "corp_ "
                if not label_list:
                    lang, = data["label"]
                    label_list.append({"lang": lang, "value": data["label"][lang]})
                if not description_list:
                    description, = data["descriptions"]
                    description_list.append({"lang": description, "value": data["descriptions"][description]})
                if not aliases_list:
                    alias, = data["aliases"]
                    aliases_list.append({"lang": alias, "value": [data["aliases"][alias]]})
            if each in data.keys() and propsNameMap[each] == 'industry':
                industry_dict.update({'source': [each], 'value': [{'wikidata_id':data[each][0][0],'label':data[each][
                    0][1]}]})
            if each in data.keys() and propsNameMap[each] == 'founded by':
                found_dict.update({'source': [each], 'value': [{'wikidata_id':data[each][0][0], 'label':data[each][
                    0][1]}]})
            if each in data.keys() and propsNameMap[each] == 'headquarters location':
                headquarters_tuple = list(data[each][0])
                headquarters_list.append(headquarters_tuple)
            if each in data.keys() and propsNameMap[each] == 'country':
                country_tuple = list(data[each][0])
                country_list.append(country_tuple)
            if each in data.keys() and propsNameMap[each] == 'official website':
                official_list.append(data[each][0])
            if each in data.keys() and propsNameMap[each] == 'has part(s)':
                subsidiary_dict.update({'source': [each], 'value': []})
        temp_data.update({'label': label_list,
                          'descriptions': description_list,
                          'aliases': aliases_list,
                          'industry': industry_dict,
                          'founded by': found_dict,
                          'headquarters location': headquarters_list,
                          'country': country_list,
                          'official website': official_list,
                          'subsidiary': subsidiary_dict})
        return temp_data

