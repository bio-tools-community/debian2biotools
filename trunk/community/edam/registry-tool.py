#!/usr/bin/env python
import json
import yaml
import argparse
import requests
import os.path
import getpass
import re

from lxml import etree

from debian import deb822

#parsing and declaring namespaces...
EDAM_NS = {'owl' : 'http://www.w3.org/2002/07/owl#',
           'rdf':"http://www.w3.org/1999/02/22-rdf-syntax-ns#",
           'rdfs':"http://www.w3.org/2000/01/rdf-schema#",
           'oboInOwl': "http://www.geneontology.org/formats/oboInOwl#"}

#EDAM_DOC = doc = etree.parse("/home/hmenager/edamontology/EDAM_1.13_dev.owl")
#EDAM_DOC = doc = etree.parse("EDAM.owl")
doc = etree.parse("/home/moeller/debian-med/community/edam/EDAM.owl")
EDAM_DOC = doc.getroot()

def check_id(label, axis):
    #xpath_query = "//owl:Class[translate(rdfs:label/text(),'abcdefghijklmnopqrstuvwxyz','ABCDEFGHIJKLMNOPQRSTUVWXYZ')=translate('" + label\
    #      + "','abcdefghijklmnopqrstuvwxyz','ABCDEFGHIJKLMNOPQRSTUVWXYZ') and starts-with(@rdf:about, 'http://edamontology.org/" + axis + "')]/@rdf:about"
    xpath_query = "//owl:Class[rdfs:label/text()='"+label+"' and starts-with(@rdf:about, 'http://edamontology.org/" + axis + "')]/@rdf:about"
    matching_terms = EDAM_DOC.xpath(xpath_query, namespaces=EDAM_NS)
    if len(matching_terms)==0:
        sys.stderr.write("\nE: No matching " + axis + " term for label " + label + "!"+"\n")
        # print(xpath_query)
    elif len(matching_terms)>1:
        sys.stderr.write("\nE: More than one " + axis + " term for label " + label + "!"+"\n")
    else:
        term_id = matching_terms[0]
        if len(EDAM_DOC.xpath("//owl:Class[@rdf:about='"+ term_id +"' and owl:deprecated='true']", namespaces=EDAM_NS))>0:
            sys.stderr.write("\nE: Term " + term_id + " term for label " + label + " is deprecated!\n")
        else:
            return term_id            

import re, sys
def getUpstreamName(changelogFile):
    p = re.compile("Upstream-Name: *([A-Za-z0-9]+) *")
    for l in open(changelogFile):
        m = p.findall(l)
        if m:
            return(m[0])
    return("")

        
def doc_to_dict(pack_dir):
    debian_path = os.path.join(pack_dir, 'debian')
    control_path = os.path.join(debian_path, 'control')
    changelog_path = os.path.join(debian_path, 'changelog')
    copyright_path = os.path.join(debian_path, 'copyright')
    edam_path = os.path.join(debian_path, 'upstream', 'edam')
    metadata_path = os.path.join(debian_path, 'upstream', 'metadata')
    control_iterator = deb822.Packages.iter_paragraphs(open(control_path))
    control_description=""
    control_homepage=""
    control_name=""
    for p in control_iterator:
        if p.has_key("Source"):
            control_source=p.get("Source")
        if p.has_key("Homepage"):
            control_homepage=p.get("Homepage")
        if p.has_key("Description"):
            control_description=p.get("Description")
            break;

    version_line = open(changelog_path).readline()
    version_debian = re.split('[()]', version_line)[1]
    m = re.match('^([0-9]+:)?(.*)-[^-]+$', version_debian)
    if (m is None):
        sys.stderr.write("E: Bad version in "+changelog_path+"\n")
	sys.exit(1)
    version_upstream = m.groups()[m.lastindex-1]

    resource_name=getUpstreamName(copyright_path)
    if "" == resource_name:
	resource_name=control_source

    
    resource = {'name': resource_name,
                'homepage': control_homepage,
                'version': version_debian,
                'collection': 'DebianMed',
                #'interface': {}, #TODO
                'description': control_description,
                'sourceRegistry': '',
                'function': []
               }
    resource['publications'] = {}

    try:
        metadata = yaml.load(open(metadata_path))
        #print metadata       
        try:
            resource['publications']['publicationsPrimaryID'] = metadata['Reference']['DOI'],
        except KeyError:
            resource['publications']['publicationsPrimaryID'] = metadata['Reference']['doi'],

    except TypeError:
        #sys.stderr.write("W: " + resource_name + "shows TypeError for DOI - presumed harmless")
        try:
            resource['publications']['publicationsPrimaryID'] = metadata['Reference'][0]['DOI'],
        except KeyError:
            resource['publications']['publicationsPrimaryID'] = metadata['Reference'][0]['doi'],
	if len( metadata['Reference'])>1:
            resource['publications']['publicationsOtherID'] = []
            for pos in range(1,len(metadata['Reference'])):
                try:
                    resource['publications']['publicationsOtherID'] = metadata['Reference'][pos]['DOI']
                except KeyError:
                    try:
                       resource['publications']['publicationsOtherID'] = metadata['Reference'][pos]['doi']
                    except KeyError:
                       sys.stderr.write("\nW: No DOI at pos %d in '%s'\n" % (pos,metadata_path))
    except KeyError:
        # already done - assignment of none to publication
        resource['publications']['publicationsPrimaryID'] = "None"
    except IOError:
        sys.stderr.write("\nW: No metadata file found (looked for "+metadata_path+")\n")
        resource['publications']['publicationsPrimaryID'] = "None"



    try:
        edam = yaml.load(open(edam_path))
	#print(edam)
        topicORtopics = []
        try:
            topicORtopics = edam['topics']
        except KeyError:
            topicORtopics = edam['topic']
    
        resource['topic']=[{'uri':check_id(topic_label,'topic')} for topic_label in topicORtopics]

        scopeORscopes = []
        try:
            scopeORscopes = edam['scopes']
        except KeyError:
            scopeORscopes = edam['scope']
    
        for scope in scopeORscopes:
            function = {}
            function['functionHandle'] = scope['name']
            function['functionName'] = [{'uri':check_id(function_label,'operation')} for function_label in scope.get('function')]
            function['input'] = []
            if not scope.get('inputs') is None:
               for el in scope.get('inputs'):
                   v={}
                   v['dataType']={'uri':check_id(el['data'],'data')}
                   if 'formats' in el:
                       v['dataFormat']=[{'uri':check_id(format_el,'format')} for format_el in el['formats']]
                   elif 'format' in el:
                       v['dataFormat']=[{'uri':check_id(format_el,'format')} for format_el in el['format']]
                   function['input'].append(v)
            function['output'] = []
            if not scope.get('outputs') is None:
               for el in scope.get('outputs'):
                   v={}
                   v['dataType'] = {'uri':check_id(el['data'],'data')}
                   if 'formats' in el:
                       v['dataFormat'] = [{'uri':check_id(format_el,'format')} for format_el in el['formats']]
                   elif 'format' in el:
                       v['dataFormat'] = [{'uri':check_id(format_el,'format')} for format_el in el['format']]
                   function['output'].append(v)
            resource['function'].append(function)
    except IOError:
        sys.stderr.write("\nW: No EDAM file found (looked for "+edam_path+")\n")
    return resource
 

if __name__ == '__main__':
    parser = argparse.ArgumentParser(
                 description='ELIXIR registry tool for Debian Med packages')
    parser.add_argument('package_dirs', help="Debian package directory", nargs='+')
    args = parser.parse_args()
    if args.package_dirs:
        package_dirs = args.package_dirs
    for package_dir in package_dirs:
        #print "processing %s..." % package_dir
        res = doc_to_dict(package_dir)
        print json.dumps(res, indent=True)
        #print "done processing %s..." % package_dir
