from selenium import webdriver
from selenium.webdriver.common.desired_capabilities import DesiredCapabilities
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
import csv, sys
import pprint
import time
import unicodedata

def strip_accents(s):
    return ''.join(c for c in unicodedata.normalize('NFD', s) if unicodedata.category(c) != 'Mn')

def clean_text(text):
    '''
    input: "Nome da Escola: ADAMANTINA CENTRO DE RECREACAO INFANTIL DE"
    return: "ADAMANTINA CENTRO DE RECREACAO INFANTIL DE"
    '''
    if not text:
        return ''

    if ':' in text:
        text = text.split(':')[1].strip()
    else:
        text = text.strip()
    return text

def extract_text_to_dict(text):
    '''
    input: "Tipo de ensino: PRIVADA - FILANTRÓPICA | Município: ADAMANTINA | Diretoria de Ensino: ADAMANTINA | Rede de Ensino: PARTICULAR'""
    return: {
                
                'tipo_de_ensino': "PRIVADA - FILANTRÓPICA",
                'municipio': "ADAMANTINA",
                'municipio': "ADAMANTINA",
                'diretoria_de_ensino': "ADAMANTINA",
                'rede_de_ensino: "PARTICULAR"
                ...
            }
    '''
    return_dict = {}

    # eliminate break line '\n'
    # text = text.replace('\n', ' ')

    if '\n' in text:
        splitted_text = text.split('\n')
    else:
        splitted_text = text.split('|')

    # format keys
    for fragment in splitted_text:
        key = strip_accents(fragment.split(':')[0].strip().lower().replace(' ', '_').replace('-', '_'))

        if 'e_mail' in key:
            value = fragment.split(':')[1].strip().lower()
        elif 'cep' in key:
            value = fragment.split(':')[1].strip().lower().replace(' ', '')
        else:
            value = fragment.split(':')[1].strip()

        if key:
            return_dict[key] = value

    return return_dict

driver = webdriver.Chrome(executable_path="C:\Chrome.exe")
driver.implicitly_wait(1.5)
# abre a URL

# page_count = 514
page_count = 1196
driver.get("https://pesquisaseduc.fde.sp.gov.br/localize_escola?pageNumber={}&idRedeEnsino=3&inicial=False".format(page_count))
write_header = False

time.sleep(0.2)

# CSV initialization 
f = open('/Users/fabio/Downloads/secretaria_educacao_colegios.csv', 'w')


# carregaárea onde estão os dados
#driver.get("http://www.educacao.sp.gov.br/central-de-atendimento/index_escolas.asp")
#frame = driver.find_element(By.XPATH, '/html/frameset/frame[2]')
#time.sleep(1)
#driver.switch_to.frame(frame)

## setar apenas colégios particulares
#driver.find_element(By.XPATH, "/html/body/div/main/div/div/form/article/div/div/div[3]/select/option[text()='Particular          ']").click()
#time.sleep(1)

## click no botão
#driver.find_element(By.XPATH, "/html/body/div/main/div/div/form/article/div/div/div[6]").click()
#time.sleep(8)

print('Verificando a página {}'.format(page_count))

has_next_page_button = driver.find_element(By.XPATH, '//*[@id="conteudo"]/div/nav[2]/div/ul/li[contains(@class, "PagedList-skipToNext")]')

while has_next_page_button:
    # Lista de colégios
    articles = driver.find_elements(By.XPATH, '//*[@id="conteudo"]/div/article')
    count_token = 2
    for article in articles:
        row = {}
        # Carrega as informações do colégios

        try:
            school_name = clean_text(driver.find_element(By.XPATH, '//*[@id="conteudo"]/div/article[{}]/h4'.format(count_token)).text)
            header_dict = extract_text_to_dict(driver.find_element(By.XPATH, '//*[@id="conteudo"]/div/article[{}]//*[@class="data_res"]'.format(count_token)).text)
            data = extract_text_to_dict(driver.find_element(By.XPATH, '//*[@id="conteudo"]/div/article[{}]//*[@class="assunto_esc"]'.format(count_token)).text)

            row.update({'school_name': school_name})
            row.update(header_dict)
            row.update(data)
            print('\n')
            pprint.pprint(row)

        except Exception as e:
            continue
        else:
            if not write_header:
                # create the csv writer
                writer = csv.DictWriter(f, fieldnames = row.keys())
                write_header = True
            # write a row to the csv file
            writer.writerow(row)
            count_token += 1

    while has_next_page_button:
        
        page_count += 1
        has_next_page_button.click()
        time.sleep(30)
        print('Carregando a próxima página [{}].'.format(page_count + 1))
        time.sleep(10)
        print('Carregando a próxima página [{}]..'.format(page_count + 1))
        time.sleep(10)
        print('Carregando a próxima página [{}]...'.format(page_count + 1))

        try:
            has_next_page_button = driver.find_element(By.XPATH, '//*[@id="conteudo"]/div/nav[2]/div/ul/li[contains(@class, "PagedList-skipToNext")]')
        except Exception as e:
            print(e)
        else:
            if not has_next_page_button:
                has_next_page_button = False
            break

    if not has_next_page_button:
        # última página
        print('última página bye bye')
        break

# close the file
f.close()