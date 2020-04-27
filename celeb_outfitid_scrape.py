"""
Created on Mon Apr  6 10:46:42 2020

@author: Admin001
"""

''' Various required imports '''

import pandas as pd
import requests
import shutil
import os

from fake_useragent import UserAgent
from bs4 import BeautifulSoup
from datetime import datetime
from time import sleep

from selenium import webdriver
from selenium.webdriver.chrome.options import Options

''' Function for scraping data from a webpage '''
def scrape_func(page,link,celeb_folder_path):
    
    ''' DataFrame for storing and exporting the extracted data '''

    df = pd.DataFrame(columns=['Post_Date','Celebrity_Name','Post_Name','Photo','Product_Info','Product_Name','Product_Links'])
    
    celeb_name = str(link).split('/')[-4].upper()
    print('\nWorking on page: {} for Celebrity: {}'.format(page,celeb_name))
    
    ''' Extracting links of available posts on the page '''
    page_data = requests.request("GET", url=link,headers=header)
    page_soup = BeautifulSoup(page_data.text,'html.parser')
    
    page_links = page_soup.find_all("h2",attrs={'class':'entry-title'})
    page_links = [i.find('a').get('href') for i in page_links if i.find('a') != None]
    page_links = [i for i in page_links if 'http' in i]
    print('Total number of post links: ',len(page_links))
    
    ''' Creating hierarchy of folders for storing data '''
    main_folder_path = os.path.join(celeb_folder_path, "page_"+str(page)+"_data")
    if not os.path.exists(main_folder_path):
        os.mkdir(main_folder_path)
        
    pic_folder_path = os.path.join(main_folder_path, 'page_'+str(page)+"_images")
    if not os.path.exists(pic_folder_path):
        os.mkdir(pic_folder_path)
    
    ''' Iterating over each post link to scrape data '''     
    
    for i in range(len(page_links)):
        
        post_folder_path = os.path.join(pic_folder_path, 'post_'+str(i)+"_images")
        if not os.path.exists(post_folder_path):
            os.mkdir(post_folder_path)
        print('\n')
        print('Extracting data for post: ',i)
            
        link_data = requests.request("GET", url=str(page_links[i]),headers=header)
        
        soup_link = BeautifulSoup(link_data.text,'html.parser')
        
        try:
            date = soup_link.find("time").text
        except:
            date = None
            
        try:
            post_name = soup_link.find("h1",attrs={'class':'entry-title'}).text
        except:
            post_name = None
        
        try:
            celebrity = post_name.split("’")[0].split(" ",2)[2].strip()
        except:
            celebrity = None
        
        try:
            try:
                photo = soup_link.find('figure',attrs={'class':'wp-block-image size-large'}).find('img').get('src')
            except:
                photo = soup_link.find('figure',attrs={'class':'alignleft'}).find('img').get('src')
            
            filename = 'main_image.jpg'
            image_path = os.path.join(post_folder_path, filename)    
            print('Downloading main post image')
            
            response = requests.get(str(photo), stream=True) 
            try:
                with open(image_path, 'wb') as file:
                    shutil.copyfileobj(response.raw, file)  # source -  destination
            except Exception as e:
                print('Error in downloading main image')
                print(e)    
        except:
            photo =None
            print('No celebrity image to download')
        
        try:
            try:
                clothing_data = soup_link.find('figure',attrs={'class':'wp-block-image size-large'}).find_next_siblings('p')
                product_info = [i.text for i in clothing_data if i.text != '']
            
            except:
                clothing_data = soup_link.find('div',attrs={'class':'entry-content'}).findChildren('p')
                product_info = [i.text for i in clothing_data if i.text != '']
        except:
            product_info = None
            
        try:
            product_name = post_name.split("’")[1][2:-1]
        except:
            product_name = None
            
        try:
            try:
                driver = webdriver.Chrome(executable_path=driver_path,options=options)
                driver.get(str(page_links[i]))
                sleep(3)
                div = driver.find_elements_by_class_name(name='sc-products')
                pic_links = [i.find_elements_by_tag_name('a') for i in div]
                product_links=[]
                for i in pic_links:
                    for v in i:
                        product_links.append(v.find_element_by_tag_name('link').get_attribute('href'))

                driver.close()
            except:
                table_tags = soup_link.find_all('table')
                product_links = [i.find('a').find('img').get('src') for i in table_tags]
                
            
            if len(product_links) == 0:
                try:
                    table_tags = soup_link.find_all('table')
                    product_links = [i.find('a').find('img').get('src') for i in table_tags]
                except:
                    product_links = []
                    
            print('Total products: ',len(product_links))
                
            if len(product_links) != 0:
                            
                for index, image in enumerate(product_links):
                    file_name = 'product_'+str(index)+'.jpg'
                    image_path = os.path.join(post_folder_path, file_name)        
                    print('Downloading product image: ', index)
                    
                    response = requests.get(image, stream=True) 
                    try:
                        with open(image_path, 'wb') as file:
                            shutil.copyfileobj(response.raw, file)  # source -  destination
                    except Exception as e:
                        print(e)
            else:
                print('No product images to download')
            
        except:
            print('No product images to download')
            product_links=[]
            
        if photo == None and product_links == []:
        	os.rmdir(post_folder_path)
        
        df = df.append({'Post_Date':date,'Celebrity_Name':celebrity,'Post_Name':post_name,'Photo':photo,'Product_Info':product_info,'Product_Name':product_name,'Product_Links':product_links},ignore_index=True)

    ''' Dropping empty rows and exporting data to csv file '''
    
    df.dropna(how='all',inplace=True)
    scrape_file = str(main_folder_path) +"/page_"+str(page)+"_content" +".csv"
    df.to_csv(scrape_file,index=False,encoding='utf-8-sig')
    
    try:
        next_page_link = page_soup.find('nav',attrs={'class':'navigation pagination'}).find('a',attrs={'class':'next page-numbers'}).get('href')
    except:
        next_page_link = None
        
    return next_page_link

''' Initialising variables and creating main folder for storing downloaded images in a structured manner '''

options = Options()
options.headless = True
driver_path ='C:\\Users\\Admin001\\Downloads\\chromedriver.exe'
# NOTE : Replace this string with the path of chrome driver exe file on your system.

path = os.getcwd()

new_folder_path = os.path.join(path, 'OutfitId_Scraped_data')
if not os.path.exists(new_folder_path):
    os.mkdir(new_folder_path)    

''' Starting the process to fetch all available celebrity profile links on webpage '''

agent = UserAgent()
header = {'user_agent':agent.chrome}

url = "https://www.outfitidentifier.com/"
data = requests.request("GET", url=url,headers=header)
soup = BeautifulSoup(data.text,'html.parser')

all_li_tags = soup.find("section",attrs={'class':'widget widget_categories'}).find_all('li')
all_celeb_links = [i.find('a').get('href') for i in all_li_tags]
all_celeb_info = [i.text for i in all_li_tags]

''' Iterating over each celebrity profile to scrape all the data '''

for i in range(len(all_celeb_links)):
    
    ''' Creating folder with celebrity name for storing data '''
    time_stamp = str(datetime.now().strftime("%d-%m-%Y_%H:%M:%S").replace(':','_'))
    
    celeb_name = str(all_celeb_links[i]).split('/')[-2]
    
    celeb_folder_path = os.path.join(new_folder_path, celeb_name+'_'+time_stamp)
    if not os.path.exists(celeb_folder_path):
        os.mkdir(celeb_folder_path)
    
    count = 1    
    profile_link = all_celeb_links[i] + str('page/') + str(count) + str('/')    
            
    profile_link_data = scrape_func(count,profile_link,celeb_folder_path)
    print("\n",profile_link_data,end='\n')
    
    ''' Using while loop to scarpe data from all pages available for a celebrity '''
    tag_check = True
    
    while tag_check:
        
        if profile_link_data != None or profile_link_data == '':
    
            profile_link = profile_link_data
            
            count += 1
            
            profile_link_data = scrape_func(count,profile_link,celeb_folder_path)
            
            print("\n",profile_link_data,end='\n')
            
        else:
            tag_check = False
            
print("Process completed for all celebrities. ")

