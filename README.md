# CondoPricePrediction

This repository contains all the relevant files for collecting, exploring, cleaning and modelling the real estate data for the purpose of predicting condominium prices.

<b> Web Scraping : web_scraper.py </b>

I was particularly interested in the Toronto Housing market and finding a 2020 dataset with relevant fields proved to be a bit difficult. This further incentivized me to simply collect my own data by scraping it off the web. However, I wanted to make a web scraper that was quite general and that I can return to for further use in the future for new projects down the road. 

The two main classes in web_scraper.py are DataContainers and RealEstateCrawler:
<ul>
  <li> 
    <b> DataContainers: </b>
    Websites often have particular regions falling under some sort of categorical heading with fields contained therein. For instance 'Property Features' was  one such heading I came across. As the name suggests, this class was introduced as a way to organize these 'data regions' more effectively. They contain information for the general template of these regions so that when I am parsing a webpage, it can confirm that it found the container and extract the relevant fields I have specified. 
  </li>
  <li>
    <b> RealEstateCrawler: </b>
    This class is the main web crawler / scraper that does all the heavy lifting. It contains several functions to extract the information specified by the user. It is responsible for finding the buttons that take you to new webpages, sending http requests to those links and crawling over those webpages and scraping off all relevant information. Once the task is completed, it will write the data onto a "csv" file.
  </li>
</ul>
