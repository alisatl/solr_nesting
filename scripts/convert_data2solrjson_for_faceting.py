#!/usr/bin/python

import sys, os, getopt
import json
import codecs
import uuid
import time

###############################
##Sample of the output format:
## [
##  {id : book2, type_s:book, title_t : "Snow Crash", author_s : "Neal Stephenson",
## cat_s:sci-fi, pubyear_i:1992, publisher_s:Bantam,
## _childDocuments_ : [
##   { id: book2_c1, type_s:review, review_dt:"N15-01-03T14:30:00Z",
##     stars_i:5, author_s:yonik,
##     comment_t:"Ahead of its time... I wonder if it helped inspire The Matrix?",
##     _childDocuments_:[
##       {id: book2_c1_e1, type_s:entity, text:"The Matrix", type:"movie" }
##     ]
##   }, ...
## ]
##
##
#####################################

TYPE_FIELD_NAME = "path"


def make_uid():
    return str(uuid.uuid4().fields[-1])[:5]

## load from .json
def load_from_json(fname):
    obj = {}
    # if file exists
    if os.path.isfile(fname):
       fin = codecs.open(fname, encoding = 'utf-8')
       obj = json.load(fin)
    else:
       print "No .json file  found... Exiting"
       sys.stderr.write("No .json file  found... Exiting\n")
       sys.exit(-1)
    return obj
##eof load_from_json()

## dump to .json
def dump_to_json(obj, fname):
    fout = codecs.open(fname, encoding = 'utf-8', mode = 'w')
    json.dump(obj, fout, ensure_ascii = False, indent=4, separators=(',', ': '))
    fout.close()
##eof dump_to_json()

def path_to_str(path):
    path_str = ""
    level = len(path)+1
    for e in path:
        path_str+=e+"."
    return str(level)+"."+path_str


#global var for tracking unique fields from upper levels

unique_fields_map={}
## generates unique field and adda parent field for faceting
def add_unique_and_parent_fields(d_solr, n, path, k, top_type):
    global unique_fields_map
    if top_type !="":
        uid = make_uid()
        unique_field_name = path_to_str(path)+k+"-id"
        d_solr["_childDocuments_"][n][unique_field_name] =  uid
        #if it is on the 2nd level, update the map
        if unique_field_name.find("2.blog-posts.") > -1:
            unique_fields_map[unique_field_name] = uid
        #else, propagate the unique field for the branch stemming from level 2
        else:
            second_level_part = unique_field_name[1: unique_field_name.find(".", 13)]
            second_level_unique_filed_name = "2"+second_level_part+"-id"
            d_solr["_childDocuments_"][n][second_level_unique_filed_name] =  unique_fields_map[second_level_unique_filed_name]
    else:
        unique_fields_map = {}



print_flag = False
N = 10
def reformat_to_solr_with_path(d_original, d_solr, top_id, top_type, path):
    #print "top_type = ", top_type

    path.append(top_type)
    if len(path) < N and print_flag:
        print path


    for k, v in d_original.iteritems():
        #for dicts, i.e., objects
        if path[-1] in d_original.keys() and path[-1] != "text":
            popped = path.pop()
            if len(path) < N and print_flag:
                print "popped at the beginning =", popped

        if isinstance(v, dict):
            #print "k = ", k
            #print k, " : dict"
            if "_childDocuments_" in d_solr:
                if top_type !="":
                    #d_solr["_childDocuments_"].append({"type_s":top_type+"."+k})
                    d_solr["_childDocuments_"].append({TYPE_FIELD_NAME:path_to_str(path)+k})
                    #top_type = top_type+"."+k
                else:
                    d_solr["_childDocuments_"].append({TYPE_FIELD_NAME:k})
                n = len(d_solr["_childDocuments_"])
                uid = make_uid()
                d_solr["_childDocuments_"][n-1]["id"] = top_id+"-"+uid
                add_unique_and_parent_fields(d_solr, n-1, path, k, top_type)

                reformat_to_solr_with_path(v, d_solr["_childDocuments_"][n-1], top_id, k, path)
            else:
                d_solr["_childDocuments_"] = []
                if top_type !="":
                    d_solr["_childDocuments_"].append({TYPE_FIELD_NAME:path_to_str(path)+k})
                else:
                    d_solr["_childDocuments_"].append({TYPE_FIELD_NAME:k})
                uid = make_uid()
                d_solr["_childDocuments_"][0]["id"] = top_id+"-"+uid
                add_unique_and_parent_fields(d_solr, 0, path, k, top_type)
                reformat_to_solr_with_path(v, d_solr["_childDocuments_"][0], top_id, k, path)

            if path[-1] in v.keys():
                popped = path.pop()
                if len(path) < N and print_flag:
                    print "popped child at the end =", popped
            if path[-1] == k :
                popped = path.pop()
                if len(path) < N and print_flag:
                    print "popped k at the end =", popped

        #for list of dicts, i.e., objects
        elif isinstance(v, list) and len(v) > 0 and isinstance(v[0], dict):
            for d_obj in v:
                if path[-1] == k:
                    popped = path.pop()
                    if len(path) < N and print_flag:
                        print "popped on cycle =", popped

                if "_childDocuments_" in d_solr:
                    if top_type !="":
                        d_solr["_childDocuments_"].append({TYPE_FIELD_NAME:path_to_str(path)+k})
                    else:
                        d_solr["_childDocuments_"].append({TYPE_FIELD_NAME:k})
                    n = len(d_solr["_childDocuments_"])
                    uid = make_uid()
                    d_solr["_childDocuments_"][n-1]["id"] = top_id+"-"+uid
                    add_unique_and_parent_fields(d_solr, n-1, path, k, top_type)
                    reformat_to_solr_with_path(d_obj, d_solr["_childDocuments_"][n-1], top_id, k, path)
                else:
                    d_solr["_childDocuments_"] = []
                    if top_type !="":
                        d_solr["_childDocuments_"].append({TYPE_FIELD_NAME:path_to_str(path)+k})
                    else:
                        d_solr["_childDocuments_"].append({TYPE_FIELD_NAME:k})
                    uid = make_uid()
                    d_solr["_childDocuments_"][0]["id"] = top_id+"-"+uid
                    add_unique_and_parent_fields(d_solr, 0, path, k, top_type)
                    reformat_to_solr_with_path(d_obj, d_solr["_childDocuments_"][0], top_id, k, path)

        else:
            # PREPROCESSING OF THE LEAF FIELDS #

            #adds "raw" (not tokenized) field just for the "text" field
            # only for Query 2
            #if k == "text":
            #    k1 = "text_s"

            #conversion of date
            #if k == "date":
                ## Date in Solr:
                ## 1972-05-NT17:33:18Z
                #k = "date_tdt"
                #v = long(v)
                #v = time.strftime('%Y-%m-%dT%H:%M:%SZ',  time.gmtime(v/1000.))
            #elif k == "path":
                #k = k+"_s"
            #else:
                #add "raw" field for every field
                #k1 = k+"_ss"
                #d_solr[k1] = v

                #adding "_t_s" suffix
                #for further conversion into *_t and *_s through CopyField rules
                #k = k+"_ts"

            d_solr[k] = v
            #print "{0} : {1}".format(k, v)
#eo reformat_to_solr_with_path



#wraps the format conversion process
def convert_to_solr(fin_nm, fout_nm):
    obj = load_from_json(fin_nm)

    #types of top-level documents
    top_doctypes = obj.keys()

    data_solr = []
    for top_doctype in top_doctypes:
        for top_doc in obj[top_doctype]:

            top_doc_solr = {TYPE_FIELD_NAME:"1."+top_doctype}
            top_id = make_uid()
            top_doc_solr["id"] = top_id
            path = []
            reformat_to_solr_with_path(top_doc, top_doc_solr, top_id, top_doctype, path)
            print_flag = False
            data_solr.append(top_doc_solr)

    dump_to_json(data_solr, fout_nm)
#eo convert_to_solr(fin_nm, fout_nm)

def main(argv):
    inputfile_nm = ''
    outputfile_nm = ''
    fin = sys.stdin
    fout = sys.stdout

    try:
        opts, args = getopt.getopt(argv[1:],"hi:o:",["ifile=","ofile="])
    except getopt.GetoptError:
        print 'Usage {script} -i <inputfile> -o <outputfile>'.format(script = argv[0])
        sys.exit(2)
    for opt, arg in opts:
        if opt == '-h':
            print 'Usage {script} -i <inputfile> -o <outputfile>'.format(script = argv[0])
            sys.exit()
        elif opt in ('-i', "--ifile"):
            inputfile_nm = arg
        elif opt in ("-o", "--ofile"):
            outputfile_nm = arg

    print 'Input file is "', inputfile_nm
    print 'Output file is "', outputfile_nm

    convert_to_solr(inputfile_nm, outputfile_nm)


if __name__ == "__main__":
   main(sys.argv)
