import requests
import csv
import time
from math import floor
from numpy import nan
from bs4 import BeautifulSoup

class DataContainer:
    
    def __init__(self, name, html_object, name_access, list_type, element_type, labels = True):
        """
        Websites often have boxes with a list of features containing useful data.
        This class is a way to store that information and ensure that you are receiving
        the correct data when parsing the BeautifulSoup text. In essence, this is
        the expected template for data that you want to extract. [This assumes
        that the target webpages have been made consistent across other target webpages.]
        
        PARAMETERS:
        name: (String) None (If Not Applicable) or full name as shown in the site's HTML (Include relevant text such as :-,;/? etc.)
              Example: A real estate site has "Property Features:" as a box title in the HTML document, 
              so I would precisely use this as my name. Don't worry about whitespace, that will get cleaned up.
              
        html_object: (List of length 3) Information on how to access the BeautifulSoup for the Container.
                     1st entry: 'html type'
                     2nd Entry: 'html attributes'
                     3rd Entry: Index (Might not be unique)
        
        name_access: (List of length 3) Information on how to access the name. 
                     1st entry: 'html type'
                     2nd Entry: 'html attributes'
                     3rd Entry: Index (Might not be unique)
                     
        list_type: (String) We assume that the html box contains a list object of html type 'ul' or 'ol'.
        
        element_type: (String) This will typically be a list element 'li'.
        
        labels: (Boolean) Some data containers have a variable amount of information
                that you want to extract in some specific way. Often, they may neither have labels or
                the labels are irrelevant. Set this value to False if labels are irrelevant.
                
        ATTRIBUTES:
        if labels == True:
            elements: (List[Dictionary]) Where Dictionary = {'name': , 'type': , 'index': , 'value type': , 'value index': }
        else:
            elements: (List[Dictionary]) Where index in List[index] indicates depth of element in HTML tree relative to element_type provided.
            Let ValueDictionary = {'value type': , 'value index': }. Then Dictionary in List[Dictionary] can be a dictionary
            of ValueDictionaries to indicate that several elements at the same depth of the HTML tree require scraping. See main() for an example.
            
        """
        self.name = name
        self.details = {'type': html_object[0], 'attr': html_object[1], 'index': html_object[2]}
        self.name_access = {'type': name_access[0], 'attr': name_access[1], 'index': name_access[2]}
        self.list_type = list_type
        self.element_type = element_type
        
        self.elements = None
        self.labels = labels
        
    def set_elements(self, elements):
        
        self.elements = elements
        
    def compare_strings(self, string, string_html):
        
        if string == string_html.strip():
            return True
        else:
            return False
        
    def check_name(self, container_soup):
        """
        container_soup: (BeautifulSoup Object) This is the HTML data in bs4 format.
        """
        name_acc = self.name_access
        name_index = name_acc['index']
        try:
            html_name = container_soup.find_all(name_acc['type'], name_acc['attr'])[name_index].string
        except:
            print("ERROR (check_name): Index out of Range:" +  str(name_index))
            return 0
        else:
            if self.compare_strings(self.name, html_name):
                return True
            else:
                return False
    
        
class RealEstateCrawler:
    """
    CONVENTION: A return of 0 in the code typically signifies something went wrong.
                A return of 1 (if it appears) in the code signifies everything went correctly.
                
    !EXCEPTION: In some cases (such as computing storey_levels) this does not apply. As a heuristic,
                if a non-int object is normally returned, then the convention proceeds.
    """             
    def __init__(self, search_key, main_link, total_pages = None, limit_per_page = None, first_page = 1):
        """
        
        PARAMETERS:
        search_key: (String) Desired search word to specify the http address [See main_links].
        
        main_links: (List[String] of size 3) Format =
                    page_link = start_link[0] + search_key + start_link[1] + page + start_link[2]
        
        total_pages: (Int or None) Total number of pages to crawl over. If no limit desired, set to None.
        
        """
        self.search_key = search_key
        self.first_page = first_page
        self.main_http = [main_link[0] + search_key + main_link[1], main_link[2]]
        
        self.total_pages = total_pages
        self.limit_per_page = limit_per_page
        
        self.crawler_type = None
        self.crawler_attr = None
        
        self.scrap_particulars = None
        self.scrap_containers = None
        self.data = []
        
        self.total_count = total_pages*limit_per_page
        self.counter = 0
        self.start_time = time.time()
        
    def set_page_link(self, main_http, page):
        
        return main_http[0] + str(page) + main_http[1]
        
    def set_crawler_property(self, html_type, html_attr):
        """
        This specifies the HTML type and attributes for the buttons that contain
        the href links for the crawler to scrape over.
        
        PARAMETERS:
        html_type: (String) Specifies HTML type to search for
        html_attr: (Dictionary) Specifies HTML attributes to filter search
        """
        self.crawler_type = html_type
        self.crawler_attr = html_attr
    
    def set_scraper_particulars(self, particulars):
        
        self.scrap_particulars = particulars
    
    def set_scraper_containers(self, containers):
        
        self.scrap_containers = containers
        
    def crawl(self, headers = None, timeout = 5):
        
        if self.total_pages != None:
            for page in range(self.first_page, self.total_pages + self.first_page):
                page_crawl_result = self.page_crawl(page,headers,timeout)
                if page_crawl_result != 0:
                    page = page + 1
                else:
                    break        
        else:
            page = self.first_page
            while True:
                page_crawl_result = self.page_crawl(page,headers,timeout)
                if page_crawl_result != 0:
                    page = page + 1
                else:
                    break
                
    def page_crawl(self, page, headers, timeout):
        
        page_link = self.set_page_link(self.main_http, page)
                
        page_soup = self.soupify_request(page_link, headers, timeout)
        
        if page_soup != 0:
            crawl_list = self.set_crawl_list(page_soup)
            if crawl_list != 0:
                self.item_crawler(crawl_list)
                return 1
            else:
                return 0
        else:
            print("ERROR: Request made to page " + str(page) + " could not be completed")
            return 0
        
    def soupify_request(self, link, headers = None, timeout = 5):
        """
        Sends request to a webpage link and transforms the response into a 
        BeautifulSoup object.
        
        PARAMETERS:
        link: (String) The http target link
        headers: (Dictionary) Any headers to add
        """
        try:
            response = requests.get(link, headers = headers, timeout = timeout)
        except:
            status_code = response.status_code
            print("ERROR (soupify_request): Request to " + link + " failed with status code: " + str(status_code))
            
            return 0
        else:
            status_code = response.status_code
            print("(soupify_request) Request to " + link + " was successful with status code: " + str(status_code))
            if status_code == requests.codes.ok:
                return BeautifulSoup(response.text, "html.parser")
            else:
                return 0
            
    def set_crawl_list(self, soup):
        
        crawl_list = soup.find_all(self.crawler_type, self.crawler_attr)
        crawl_size = len(crawl_list)
        print("Crawl Size:" + str(crawl_size))
        
        if self.limit_per_page == None or 0 < crawl_size <= self.limit_per_page:
            #print(crawl_list)
            return crawl_list
        elif crawl_size == 0:
            print("ERROR (set_crawl_list): crawl_list has zero size")
            return 0
        else:
            crawl_list = crawl_list[0:self.limit_per_page]
            print(crawl_list)
            return crawl_list
        
    def scraper(self, soup, link):
        
        data_dict = {}
        
        for value in self.scrap_particulars:
            
            particular_value = self.access_string_particular(soup,value)
            
            if particular_value == 0:
                data_dict[value] = nan
            else:
                data_dict[value] = particular_value.strip()
            
        for data_container in self.scrap_containers:
            
            container_soup = self.soupify_container(soup, data_container)
            
            if data_container.labels:
                
                if container_soup == 0:
                    
                    for element in data_container.elements:
                        name = element['name'][0:-1]
                        
                        data_dict[name] = nan  
                else:
                    container_list = container_soup.find_all(data_container.element_type)
                    
                    for element in data_container.elements:
                        
                        name = element['name'][0:-1] #Take away colon : at the end of string
                        
                        data_dict[name] = self.access_string_container(container_list, data_container, element)
            else:
                # This is for the Room Data Container
                
                if container_soup == 0:
                    data_dict['Storeys'] = nan
                    data_dict['Floor Area (m^2)'] = nan
                else:              
                    storeys_area = self.compute_levels_and_space(container_soup, data_container, link)
                    data_dict['Storeys'] = storeys_area['Storeys']
                    data_dict['Floor Area (m^2)'] = storeys_area['Floor Area']
                    
        return data_dict
    
    def access_string_container(self, container_list, DataContainer, element):
        """
        Perform a linear search through container_list to find the relevant piece
        of data as provided by element and return it.
        """
        for item in container_list:
            #print("Type Soup: " + str(item))
            item_name = item.find_all(element['type'])[element['index']].string.strip()
            
            if DataContainer.compare_strings(element['name'], item_name):
                try:
                    string = item.find_all(element['value type'])[element['value index']].string.strip()
                except:
                    print("ERROR (access_string_container): Found 'NoneType' Object")
                    return nan
                else:
                    return string
            else:
                pass
        
        return nan
        
    def soupify_container(self, page_soup, DataContainer):
        """
        Extract the relevant BeautifulSoup associated with the DataContainer
        
        PARAMETERS:
        page_soup: (BeautifulSoup)
        DataContainer: (DataContainer)
        """
        try:
            container_soup = page_soup.find_all(DataContainer.details['type'], DataContainer.details['attr'])[DataContainer.details['index']]
        except:
            print("ERROR (soupify_container): Index out of range for " + DataContainer.name + ".")
        else:
            
            if DataContainer.check_name(container_soup) == 0:
                return 0
            else:
                if DataContainer.check_name(container_soup):
                    return container_soup
                else:
                    return 0
                
        
    def item_crawler(self, crawl_list):
        """
        For each item displayed on the webpage, find the associated http link
        and go to there to scrape data.
        
        """
        for access_button in crawl_list:
            
            href = access_button['href']
            print(href)
            soup = self.soupify_request(href)
            if soup != 0:
                
                data = self.scraper(soup, href)
        
            print(data)
            print("\n")
            
            self.data.append(data)
            self.counter = self.counter +1
            self.time_left()
            
    def access_string_particular(self, soup, value):
         """
         Tries to find the string text associated with the parameter 
         'value' in the BeautifulSoup object 'soup'.
         
         PARAMETERS:
         soup: (BeautifulSoup) 
         value: (String) A value in scrap_particulars
         """
         prop = self.scrap_particulars[value]
         
         soup_values = soup.find_all(prop['type'], prop['attr'])
         
         soup_size = len(soup_values)
         prop_index = prop['index']
                 
         if soup_size == 0:
             print("ERROR (access_string_particular): Failed Attempt at finding '" + value + "', found zero results.")
             return 0
         
         elif soup_size < prop_index:
             print("ERROR (access_string_particular): Desired argument (order) out of bounds for '" + value + "'. Only found " + str(soup_size) + " results.")
             return 0
         
         else:
             
             soup_value = soup_values[prop_index]
             
             if prop['sibling'] == None:
                 
                 child = prop['child']
                 
                 if child == None:
                     return soup_value.string
                 
                 else:
                     child_index = prop['child index']
                     value = soup_value.find_all(child)[child_index].text.strip()
                     #print(value)
                     return value
                 
             else:
                 print("Sibling Not NONE")
                 return 0
    
    def compute_levels_and_space(self, soup, DataContainer, link):
        """
        This function aims to compute the house storeys and total floor space.
        It will change, depending upon the target website being scraped as well as
        become irrelevant if this information is directly provided in some standardized
        way (It was not for RoyalLePage, the first website I chose for scraping).
        
        PARAMETERS:
        soup: (BeautifulSoup Object) Data relevant to DataContainer
        
        DataContainer: (DataContainer Object) Container relevant to computing levels and area
        """
        
        element_list = soup.find(DataContainer.list_type).find_all(DataContainer.element_type)
        element_tree = DataContainer.elements
        tot_depth = len(element_tree)
        
        storey_type = element_tree[tot_depth-1]['level']['value type'] # HTML Type
        storey_attr = element_tree[tot_depth-1]['level']['value attr'] # HTML Attributes
        storey_idx = element_tree[tot_depth-1]['level']['value index'] # Index
    
        area_type = element_tree[tot_depth-1]['area']['value type'] # HTML Type
        area_attr = element_tree[tot_depth-1]['area']['value attr'] # HTML Attributes
        area_idx = element_tree[tot_depth-1]['area']['value index'] # Index
        
        max_storey = 0
        tot_area = 0
        missing_area = False
        
        for element_soup in element_list:
            info_depth = self.tree_dig(element_soup, element_tree, tot_depth)
             
            try:
                level_info = info_depth.find_all(storey_type, storey_attr)[storey_idx].text.strip().split(" ")[0]
                #print("Level Info: " + str(level_info))
            except:
                print("ERROR (compute_levels_and_space): Attempt at extracting Room Level Info for '" + link + "' failed.")
                element_level = -1
            else:
                element_level = self.extract_storey_level(level_info)
             
            if element_level > max_storey:
                max_storey = element_level

            if element_level > 0:
                # We don't include basement level in our home square footage calculation
                try:
                    area_info = info_depth.find_all(area_type, area_attr)[area_idx].string
                except:
                    print("ERROR (compute_levels_and_space): Attempt at extracting Room Area Info for '" + link + "' failed.")
                    element_area = 0
                else:
                    element_area = self.extract_area(area_info, link)
                    
                if element_area == 0:
                    missing_area = True
                    
            else:
                element_area = 0
                
            tot_area = tot_area + element_area
        
        if missing_area:
            total_area = nan
        else:
            total_area = tot_area
            
        return {'Storeys': max_storey, 'Floor Area': total_area}
             
    def extract_area(self, area_info, link):
        """
        Finds the two values for the lengths of the area dimensions and 
        multiplies them together.
        
        PARAMETERS:
        area_info: (String) We assume that this has the format "float_1 m x float_2 m"
        """
        area_info_split = area_info.strip().split(" ")
        
        try:
            first_num = float(area_info_split[0])
            second_num = float(area_info_split[3])
        except:
            print("ERROR (extract_area): Attempted Area Float Conversion for '" + link + "' failed." )
            return 0
        else:
            return round(first_num*second_num,2)
        
    def tree_dig(self, element_soup, element_tree, tot_depth):
        """
        Dig through an HTML tree until you reach the last layer containing the 
        relevant information.
        
        PARAMETERS:
        element_soup: (BeautifulSoup Object)
        element_tree: (List[Dictionary])
        tot_depth: (Int) The 'depth' of the element_tree (Its Length)
        
        """
        depth = 0   
        
        while depth < tot_depth - 1:
            element_soup = element_soup.find_all(element_tree[depth]['value type'])[element_tree[depth]['value index']]
            depth = depth + 1
        
        info_depth = element_soup
        return info_depth
    
    def extract_storey_level(self, storey_string):
        """
        Modify floor according to target website format. RoyalLePage storey_strings
        take the form 'Lower Level'/'Basement Level' 'Sub-Basement Level', 'Main Level'/'Ground Level', 
        'Flat/Apartment Level', 'In-Between Level', '2nd Level', 'Upper Level', '3rd Level'.
        
        PARAMETERS:
        storey_string: (String) The string corresponding to html_object.string for storey_level
        """
        
        try: 
            floor = storey_string[0].upper()
        except:
            print("ERROR (extract_storey_level): Floor Index 0 out of range")
            return 0
        else:
            
            if floor in ["L", "B", "S"]:
                return 0
            elif floor in ["M", "G", "I", "F"]:
                return 1
            elif floor in ["U"]:
                return 2
            else:
                try:
                    floor_val = int(floor)
                except:
                    print("ERROR (extract_storey_level): New 'Level' String Found -> assigned Basement Value 0")
                    return 0
                else:
                    return floor_val
            
    def write(self, file_name, field_names):
        
        with open(file_name, 'w') as file:
            
            writer = csv.DictWriter(file, delimiter = ",", fieldnames = field_names)
            writer.writeheader()
            writer.writerows(self.data)
        
        print("\nWrote Data to " + file_name)
        
    def time_left(self):
        
        start_time = self.start_time
        
        time_now = time.time()
        counter = self.counter
        
        if counter % 10 == 0 and counter != 0:
            
            time_passed = time_now - start_time
            
            velocity = time_passed/counter
            
            total_time = velocity*self.total_count
            
            time_left = total_time - time_passed
            
            minutes, seconds = self.seconds_to_mins(time_left)
            print("Data Collected: " + str(counter) + "/" + str(self.total_count))
            print("\nAPPROX. TIME LEFT: " + str(minutes) + " MINS, " + str(seconds) + "s.\n")
    
    def seconds_to_mins(self, time_secs):
        
        minutes = floor(time_secs/60)
        
        seconds = round(time_secs) % 60
        
        return minutes, seconds
    
def main():
    
    total_pages = 22
    limit_per_page = 46
    
    # Building Features Data Container
    BF_name = "Building Features:"
    BF_html_obj = ["div", {'class': "details-row"}, 0]
    BF_name_acc = ["h4", None, 0]
    
    building_features = DataContainer(name = BF_name, html_object = BF_html_obj,
                                      name_access = BF_name_acc, list_type = "ul", 
                                      element_type = "li")
    
    BF_elements = [{'name': "Style:",               'type': 'span', 'index': 0, 'value type': 'span', 'value index': 1, 'value attr': None}, 
                   {'name': "Building Type:",       'type': 'span', 'index': 0, 'value type': 'span', 'value index': 1, 'value attr': None},
                   {'name': "Basement Development:",'type': 'span', 'index': 0, 'value type': 'span', 'value index': 1, 'value attr': None},
                   {'name': "Exterior Finish:",     'type': 'span', 'index': 0, 'value type': 'span', 'value index': 1, 'value attr': None},
                   {'name': "Fireplace:",           'type': 'span', 'index': 0, 'value type': 'span', 'value index': 1, 'value attr': None}]
    
    building_features.set_elements(BF_elements)
    
    # Property Features Data Container    
    PF_name = "Property Features:"
    PF_html_obj = ["div", {'class': "details-row"}, 1]
    PF_name_acc = ["h4", None, 0]

    property_features = DataContainer(name = PF_name, html_object = PF_html_obj,
                                      name_access = PF_name_acc, list_type = "ul", 
                                      element_type = "li")
    
    PF_elements = [{'name': "OwnershipType:",        'type': 'span', 'index': 0, 'value type': 'span', 'value index': 1, 'value attr': None}, 
                   {'name': "Property Type:",         'type': 'span', 'index': 0, 'value type': 'span', 'value index': 1, 'value attr': None},
                   {'name': "Bedrooms:",              'type': 'span', 'index': 0, 'value type': 'span', 'value index': 1, 'value attr': None},
                   {'name': "Bathrooms:",             'type': 'span', 'index': 0, 'value type': 'span', 'value index': 1, 'value attr': None},
                   {'name': "Amenities Nearby:",      'type': 'span', 'index': 0, 'value type': 'span', 'value index': 1, 'value attr': None},
                   {'name': "Lot Size:",              'type': 'span', 'index': 0, 'value type': 'span', 'value index': 1, 'value attr': None},
                   {'name': "Parking Type:",          'type': 'span', 'index': 0, 'value type': 'span', 'value index': 1, 'value attr': None},
                   {'name': "No. of Parking Spaces:", 'type': 'span', 'index': 0, 'value type': 'span', 'value index': 1, 'value attr': None},
                   {'name': "Condo Fees:",            'type': 'span', 'index': 0, 'value type': 'span', 'value index': 1, 'value attr': None},
                   {'name': "Features:",              'type': 'span', 'index': 0, 'value type': 'span', 'value index': 1, 'value attr': None},
                   {'name': "Community Features:",    'type': 'span', 'index': 0, 'value type': 'span', 'value index': 1, 'value attr': None}]
    
    property_features.set_elements(PF_elements)
    
    # Rooms Data Container
    room_name = "Rooms:"
    room_html_obj = ["div", {'class': "details-row"}, 2]
    room_name_acc = ["h4", None, 0]
    
    rooms = DataContainer(name = room_name, html_object = room_html_obj,
                                      name_access = room_name_acc, list_type = "ul", 
                                      element_type = "li", labels = False)
    
    room_elements = [{'value type': 'span', 'value index': 1},
                     {'level': {'value type': 'span', 'value attr': {"class": "row-1"}, 'value index': 0}, 
                      'area': {'value type': 'span', 'value attr': {"class": "metre metre-or-feet"}, 'value index': 0}}
                     ]
    
    rooms.set_elements(room_elements)
    
    # Specify Crawler Properties
    field_names = ["Address", "Style", "Building Type", "Basement Development", "Exterior Finish", "Fireplace", 
                   "OwnershipType", "Property Type", "Bedrooms", "Bathrooms", "Amenities Nearby", "Lot Size", "Parking Type", "No. of Parking Spaces",
                   "Storeys", "Floor Area (m^2)", "Features", "Condo Fees", "Community Features", "Price"]

    homes_link = ["https://www.royallepage.ca/en/on/", "/condos/properties/", "/"]
    city_key = 'Toronto'
    
    scraper_particulars = {
            'Price': {'type': 'span', 'attr': {'class':'title title--h1 price'}, 'index': 0, 'sibling': None, 'child': 'span', 'child index': 0},
            'Address': {'type': 'h2', 'attr': {'class': "title--h2 u-no-margins"}, 'index': 0, 'sibling': None, 'child': None, 'child index': None }
    }
    
    scraper_containers = [building_features, property_features, rooms]
    
    # Construct Crawler and Set Properties
    crawl_attributes = {'class': "link link--with-icon link--icon-right"}
    
    crawler = RealEstateCrawler(city_key, homes_link, total_pages = total_pages, limit_per_page = limit_per_page)
    
    crawler.set_crawler_property(html_type = 'a', html_attr = crawl_attributes)
    crawler.set_scraper_particulars(scraper_particulars)
    crawler.set_scraper_containers(scraper_containers)
    crawler.crawl() #Engage Crawl
    
    crawler.write("TorontoCondos-August2020Listings.csv", field_names)
    
if __name__ == '__main__':
    
    main()

    


    
