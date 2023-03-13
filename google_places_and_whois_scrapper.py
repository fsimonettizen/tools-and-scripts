# coding=utf-8

import whois
import googlemaps
import pprint
import time
import xlsxwriter
import subprocess
import re
import time
import json
import os
from urllib.parse import urlparse
from subprocess import Popen, PIPE, STDOUT
import csv, sys, getopt, time, datetime

def extract_domain(url, remove_http=True):
    uri = urlparse(url)
    if remove_http:
        domain_name = f"{uri.netloc}"
    else:
        domain_name = f"{uri.netloc}://{uri.netloc}"
    return domain_name

def whois(ip,name):
    p = subprocess.Popen(['whois', ip], stdout=subprocess.PIPE)
    out, err = p.communicate()
    m = re.search('{}:\s+[\d\w\@\.\ ]+'.format(name), out)
    return m.group(0)

def question_yes_or_no(question, default="not"):
    """
    An "answer" return value is True for "yes" or False for "not".
    """
    valid = {"yes": True, "y": True,
             "not": False, "n": False}
    if default is None:
        prompt = " [Y/n] "
    elif default == "nao":
        prompt = " [Y/n] "
    elif default == "no":
        prompt = " [y/N] "
    else:
        raise ValueError("Invalid Answer: '%s'" % default)

    while True:
        sys.stdout.write(question + prompt + "\n")
        choice = input().lower()
        if default is not None and choice == '':
            return valid[default]
        elif choice in valid:
            return valid[choice]
        else:
            sys.stdout.write("Answer with 'yes' or 'not' "
                             "(ou 'y' or 'n').\n")
def main(argv):
    """Função principal
    """
    print('Excel Workbook Script')
    
    try:
        opts, args = getopt.getopt(argv,"h:f:b:e:",["f=","b=","e="])
    
        if not opts:
            print('Nenhum parâmetro foi enviado')
            usage()
            sys.exit(2)
    
    except getopt.GetoptError:
        usage()
        sys.exit(2)
    
    for opt, arg in opts:
        if opt == '-h':
            usage()
            sys.exit(2)
        elif opt in ("-f", "--f"):
            filename = arg
        if opt in ("-e", "--e"):
            print(arg)
            e = int(arg)
    
    # Define the API Key from ENV variable
    API_KEY = os.environ.get('GOOGLE_APIKEY')

    gmaps = googlemaps.Client(key = API_KEY)
    stored_results = []

    # Transform the file into a dictionary
    reader = csv.DictReader(open(filename), delimiter=';')
    print(reader.fieldnames)
    
    if question_yes_or_no("The file {} owns {} rows, do you want to upload the file?".format(filename, sum(1 for count in reader))):

        reader = csv.DictReader(open(filename), delimiter=';')

        line = 2 # controle de execucao do arquivo
        for row in reader:
            print("Processando linha: {} Cliente: {}".format(line,row["CUSTOMER"]))
            print("Processing row: {} Client: {}".format(line,row["CUSTOMER"]))
            

            query_string = u'{}'.format(row["CUSTOMER"])
            print('================')
            print("Querying: " + query_string)
            first_query_result  = gmaps.places(query = query_string)
            time.sleep(3)

            if first_query_result.get('next_page_token'):
                # pprint.pprint(first_query_result.get('next_page_token'))
                places_result  = gmaps.places(query = query_string, page_token = first_query_result['next_page_token'])
                time.sleep(3)
            else:
                places_result = first_query_result
            # pprint.pprint(places_result.get('next_page_token'))
            next_page_token = places_result.get('next_page_token')

            count = 0
            while (count < 30):

                # loop through each of the places in the results, and get the place details.      

                print('total de places: {}'.format(len(places_result['results'])))
                for place in places_result['results']:
                    # pprint.pprint(place)
                    
                    # define the place id, needed to get place details. Formatted as a string.
                    my_place_id = place['place_id']

                    # define the fields you would liked return. Formatted as a list.
                    my_fields = ['name','formatted_address','formatted_phone_number','website','rating', 'geometry']
                    
                    # make a request for the details.
                    places_details  = gmaps.place(place_id= my_place_id , fields= my_fields)

                    if 'formatted_address' not in places_details['result']:
                        places_details['result']['formatted_address'] = ''
                    if 'formatted_phone_number' not in places_details['result']:
                        places_details['result']['formatted_phone_number'] = ''
                    if 'name' not in places_details['result']:
                        places_details['result']['name'] = ''
                    if 'rating' not in places_details['result']:
                        places_details['result']['rating'] = ''
                    if 'website' not in places_details['result']:
                        places_details['result']['website'] = ''
                    if 'person' not in places_details['result']:
                        places_details['result']['person'] = ''
                    if 'owner' not in places_details['result']:
                        places_details['result']['owner'] = ''
                    if 'location' not in places_details['result']:
                        places_details['result']['location'] = ''
                    if 'lat' not in places_details['result']:
                        places_details['result']['lat'] = ''
                    if 'lng' not in places_details['result']:
                        places_details['result']['lng'] = ''

                    places_details['result']['CUSTOMER'] = row['CUSTOMER']

                    # 
                    if places_details.get('result').get('website'):
                        # domain = places_details.get('result').get('website').replace('https://', '').replace('http://', '').replace('www.', '').replace('/', '')
                        # domain = extract_domain(places_details.get('result').get('website'))
                        domain = re.sub(r'(.*://)?([^/?]+).*', '\g<1>\g<2>', places_details.get('result').get('website'))
                        domain = domain.replace('https://', '').replace('http://', '').replace('www.', '').replace('/', '')

                        whois_result = subprocess.Popen(['whois', domain], stdout=PIPE, stderr=STDOUT).communicate()[0]
                        time.sleep(2)
                        
                        if whois_result:
                            results = re.findall( r'person(.*?)country', str(whois_result))
                            text_person = ""
                            for result in results:
                                if result:
                                    text_person = text_person + result
                            
                            if text_person:
                                places_details['result'].update({'person': text_person})

                            results = re.findall( r'ownerid(.*?)country', str(whois_result))
                            text_person = ""
                            for result in results:
                                if result:
                                    text_person = text_person + result
                            
                            if text_person:
                                places_details['result'].update({'owner': text_person})

                    # store the results in a list object.
                    places_details['result']['location'] = json.dumps(places_details['result']['geometry']['location'])
                    places_details['result']['lat'] = json.dumps(places_details['result']['geometry']['location']['lat'])
                    places_details['result']['lng'] = json.dumps(places_details['result']['geometry']['location']['lng'])

                    places_details['result']['business_status'] = place.get('business_status', None)
                    places_details['result']['user_ratings_total'] = place.get('user_ratings_total', None)
                    places_details['result']['permanently_closed'] = place.get('permanently_closed', None)
                    
                    del places_details['result']['geometry']
                    stored_results.append(places_details['result'])

                if not next_page_token:
                    break

                places_result  = gmaps.places(query = query_string, page_token = next_page_token)
                time.sleep(3)
                # pprint.pprint(places_result.get('next_page_token'))
                next_page_token = places_result.get('next_page_token')
                count = count + 1

            line += 1

        # -------------- DUMPING VALUES IN EXCEL -----------------------
        # define the headers, that is just the key of each result dictionary.
        row_headers = stored_results[0].keys()

        # create a new workbook and a new worksheet.
        workbook = xlsxwriter.Workbook(r'{}{}{}{}'.format(filename.split('.')[0],'_processed','.',filename.split('.')[1]))

        worksheet = workbook.add_worksheet()

        # populate the header row
        col = 0
        for header in row_headers:
            worksheet.write(0, col, header)
            col += 1

        row = 1
        col = 0
        # populate the other rows

        # get each result from the list.
        for result in stored_results:

            # get the values from each result.
            result_values = result.values()

            # loop through each value in the values component.
            for value in result_values:
                worksheet.write(row, col, value)
                col += 1
            
            # make sure to go to the next row & reset the column.
            row += 1
            col = 0

        # close the workbook
        workbook.close()

def usage():
    """Verifica o header do arquivo
    """
    print('usage: scrapper_places_whois.py -f <path_filename>\n')

if __name__ == "__main__":
     main(sys.argv[1:])