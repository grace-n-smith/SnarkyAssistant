# coding=utf-8
from selenium import webdriver
from selenium.webdriver.support.ui import Select
from time import sleep
 
driver = webdriver.Firefox()
driver.get("https://www.iasmembership.org/donation/")
 
#element = driver.find_element("name", "donate-frequency")
#element.select_by_value("donate-once")

#uncheck "I am a member"
member_check = driver.find_element("id", "i_am_lifetime_member").click()

#set donation amount
donation = driver.find_element("name", "donation")
donation.clear()
donation.click()
donation.send_keys("1")

#press DONATE button
driver.find_element("xpath", "/html/body/div[2]/div/div[7]/main/div/div/div/div/button").click()

#now we go to the next donation page
sleep(1)

### COOKIES ###
#close the popup
driver.find_element("xpath", "/html/body/div[2]/div/div[11]/div/div[1]").click()

### 1 ###
#not necessary, should already be filled in

### 2 ###
#CONSIDER STORING THIS INFO LOCALLY (like OpenAI keys)

#credit card number

#name on card

#card expiry date

#CVV

### 3 ### 

####   PERSONAL INFORMATION   ####

#first name
driver.find_element("id", "firstName").send_keys("Grace")

#last name
driver.find_element("id", "lastName").send_keys("Smith")

#street address
driver.find_element("id", "address").send_keys("290 Massachusetts Ave.")

#country (correct from afganistan)
#driver.find_element("id", "countryCode").selectByValue("US")
country = Select(driver.find_element("id", 'countryCode'))
country.select_by_value("US")

#state
state = Select(driver.find_element("id", 'stateProvince'))
state.select_by_value("US-MA")


#state.find_elements(By.TAG_NAME, "Massachusetts")

#city
driver.find_element("id", "city").send_keys("Cambridge")

#zip
driver.find_element("id", "postalCode").send_keys("02139")

#email
driver.find_element("id", "email").send_keys("gnsmith@mit.edu")

#language
language = Select(driver.find_element("id", 'languageCode'))
language.select_by_index(10)

### legal statement checkbox ###
driver.find_element("id", "read_and_understood_policy").click()

### SUBMIT ###
driver.find_element("xpath", "/html/body/div[2]/div/div[7]/main/form/div[3]/div[2]/button[2]").click()
