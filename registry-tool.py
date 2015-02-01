import json
import yaml
import argparse
import requests
import os.path
import getpass
import re
import random # for uri2term, to be removed

def uri2term(uri):
    """The routine is meant to retrieve the human-readable term name for a URI provided.

    The current implementation merely produces a combination of the first and
    last name of Pipi Longstocking as named in different languages.
    """
    pipi= [["Pippi","Langstrumpf"],["Pippi","Longstocking"],["Inger","Nilsson"],["Fifi","Brindacier"],
           ["Pippi","Långstrump"],["Pippi","Langstrømpe"],["Pippi","Calcesllargues"],["Pipi","Ŝtrumpolonga"],["Pippi","Uzunçorap"]]
    return(random.choice(pipi)[0]+" "+random.choice(pipi)[1])

def doc_to_dict(pack_dir):
    debian_path = os.path.join(pack_dir, 'debian')
    control_path = os.path.join(debian_path, 'control')
    changelog_path = os.path.join(debian_path, 'changelog')
    edam_path = os.path.join(debian_path, 'upstream', 'edam')
    metadata_path = os.path.join(debian_path, 'upstream', 'metadata')
    control = yaml.load(open(control_path))

    version_line = open(changelog_path).readline()
    version_debian = re.split('[()]', version_line)[1]
    m = re.match('^([0-9]+:)?(.*)-[^-]+$', version_debian)
    version_upstream = m.groups()[m.lastindex-1]
    edam = yaml.load(open(edam_path))
    metadata = yaml.load(open(metadata_path))

    resource = {'name': control.get('Source'),
                'homepage': control.get('Homepage'),
                'version': version_debian,
                'collection': 'debian',
                'interface': {}, #TODO
                'description': control.get('Description'),
                'topic': [{'uri':uri,'term':uri2term(el['data'])} for uri in edam.get('topic')],
                'sourceRegistry': '',
                'publications': [{'publicationsOtherID': [i['DOI'] for i in metadata['Reference']]}],
                'function': []
               }
    for scope in edam['scopes']:
        function = {}
        function['functionHandle'] = scope['name']
        function['functionName'] = [{'uri':uri,'term':uri2term(el['data'])} for uri in scope.get('function')]
        function['input'] = []
        for el in scope.get('inputs'):
            function['input'].append({
                                      'dataType': {'uri':el['data'],'term':uri2term(el['data'])},
                                      'dataFormat' : [{'uri':format_el,'term':uri2term(el['data'])} for format_el in el['formats']]
                                     })
        function['output'] = []
        for el in scope.get('outputs'):
            function['output'].append({
                                      'dataType': {'uri':el['data'],'term':uri2term(el['data'])},
                                      'dataFormat' : [{'uri':format_el,'term':uri2term(el['data'])} for format_el in el['formats']]
                                     })
        resource['function'].append(function)
    return resource
 
def auth(login):
    password = getpass.getpass()
    resp = requests.post('https://elixir-registry.cbs.dtu.dk/api/auth/login','{"username": "%s","password": "%s"}' % (login, password), headers={'Accept':'application/json', 'Content-type':'application/json'}).text
    return json.loads(resp)['token']

if __name__ == '__main__':
    # 1. Import XML files from a Mobyle server or from a folder containing XML files
    # 2. Convert to BTR XML
    # 3. Convert to BTR JSON
    # 4. Register to Elixir BTR
    parser = argparse.ArgumentParser(
                 description='ELIXIR registry tool for Debian Med packages')
    group = parser.add_mutually_exclusive_group()
    parser.add_argument('--package_dirs', help="Debian package directory", nargs='+')
    parser.add_argument('--json_dir', help="target directory for JSON files")
    parser.add_argument('--login', help="registry login")
    args = parser.parse_args()
    if args.package_dirs:
        package_dirs = args.package_dirs
    params = {'mobyle_root':"'http://mobyle.pasteur.fr'",
              'mobyle_contact':"'mobyle@pasteur.fr'"}
    if args.login:
        print "authenticating..."
        token = auth(args.login)
        print "authentication ok"
        ok_cnt = 0
        ko_cnt = 0
        #print "attempting to delete all registered services..."
        #resp = requests.delete('https://elixir-registry.cbs.dtu.dk/api/tool/%s' % args.login, headers={'Accept':'application/json', 'Content-type':'application/json', 'Authorization': 'Token %s' % token})
        #print resp
    for package_dir in package_dirs:
        print "processing %s..." % package_dirs
        res = doc_to_dict(package_dir)
        print json.dumps(res, indent=True)
        resource_name = res['name']
        if args.json_dir:
            json_path = os.path.join(args.json_dir, resource_name + '.json')
            json.dump(res, open(json_path, 'w'), indent=True)
        if args.login and args:
            resp = requests.post('https://elixir-registry.cbs.dtu.dk/api/tool', json.dumps(res), headers={'Accept':'application/json', 'Content-type':'application/json', 'Authorization': 'Token %s' % token})
            #print resp.status_code
            if resp.status_code==201:
                print "%s ok" % resource_name
                ok_cnt += 1
            else:
                print "%s ko, error: %s" % (resource_name, resp.text)
                ko_cnt += 1
    if args.login:
        print "import finished, ok=%s, ko=%s" % (ok_cnt, ko_cnt)
