# coding=utf-8
from selenium import webdriver
from selenium.webdriver.support.ui import Select
 
driver = webdriver.Firefox()
driver.get("https://www.iasmembership.org/donation/")
 
#element = driver.find_element("name", "donate-frequency")
#element.select_by_value("donate-once")

#uncheck "I am a member"
member_check = driver.find_element("id", "i_am_lifetime_member").click()

donation = driver.find_element("name", "donation")
donation.clear()
donation.click()
donation.send_keys("1")

driver.find_element("xpath", "/html/body/div[2]/div/div[7]/main/div/div/div/div/button").click()

#member_check.deselect_all()
#print(element)

#.findElement(By.id("hobbies-checkbox-1")).click()