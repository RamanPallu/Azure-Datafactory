from WikiData import WikidataParser
import yaml
import json


def processParentChildData(company):
    company_details = wikidata.extract_corporate_entity_details(company)
    output = {}
    subsidiaryList = []
    if "P355" in company_details.keys():  # checks if company has subsidiaries
        subsidiary_details = company_details['P355']
        for subsidiary in subsidiary_details:
            subsidiaryList.append(subsidiary[1])
            subsidiaryOutput = wikidata.extract_subsidary_entity_details(subsidiary_details[1])
            subsidiaryOutput = wikidata.rename_propsId_to_props_name(propsNameMap, subsidiaryOutput)
            with open("subsidiary-" + subsidiary[1] + '.json', 'w') as f:
                f.write(json.dumps(subsidiaryOutput, indent=4))
    if "P527" in company_details.keys():  # checks if company has subsidiaries
        subsidiary_details = company_details['P527']
        for subsidiary in subsidiary_details:
            subsidiaryList.append(subsidiary[1])
            subsidiaryOutput = wikidata.extract_subsidary_entity_details(subsidiary_details[1])
            subsidiaryOutput = wikidata.rename_propsId_to_props_name(propsNameMap, subsidiaryOutput)
            with open("hasPart-" + subsidiary[1] + '.json', 'w') as f:
                f.write(json.dumps(subsidiaryOutput, indent=4))
    output[company] = company_details
    # output[company] = wikidata.rename_propsId_to_props_name(propsNameMap, output[company])
    output[company] = wikidata.generate_new_dataset(propsNameMap, output[company])
    with open('company-' + company + '.json', 'w') as f:
        f.write(json.dumps(output, indent=4))
    print('output written to ' + company + '.json')
    return subsidiaryList


def processCompany(company):
    subsidiaryListAsCompanies = processParentChildData(company)
    for subsidiary in subsidiaryListAsCompanies:
        processParentChildData(subsidiary)


def main():
    companies = cfg['config']['companies']
    for company in companies:
        print('fetching data for %s' % company)
        processCompany(company)


with open('config.yml', 'r') as f:
    cfg = yaml.load(f, Loader=yaml.FullLoader)
props = cfg['config']['props_to_fetch']
corporate_company_props = cfg['config']['corporate_company_props']
propsNameMap = cfg['config']['props-name-map']
wikidata = WikidataParser(props, corporate_company_props)
main()
