import json
import logging
import selenium
from time import sleep
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.select import Select
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC


def wait_for_element_by_id(driver, _id):
    WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.ID, _id))
    )

# Get configuration
with open("config.json", "r") as fp:
    config = json.load(fp)

address        = config["address"]
appliances     = config["appliances"]
logging_config = config["logging"]
delay          = config["delay"]

# Set up logging
log = logging.getLogger(__name__)
log.setLevel(logging_config["level"])

if logging_config["stdout"]:
    handler = logging.StreamHandler()
    handler.setLevel(logging_config["level"])
    formatter = logging.Formatter(
        '[%(relativeCreated)s] %(levelname)s: %(message)s'
    )
    handler.setFormatter(formatter)
    log.addHandler(handler)

if "filename" in logging_config:
    handler = logging.FileHandler(filename=logging_config["filename"],
                                  mode=logging_config["mode"])
    handler.setLevel(logging_config["level"])
    formatter = logging.Formatter("; ".join((
        "'level'='%(levelname)s'",
        "'datetime'='%(asctime)s'",
        "'process_name'='%(processName)s'",
        "'pid'='%(process)d'",
        "'thread'='%(thread)d'",
        "'module'='%(module)s'",
        "'line'='%(lineno)d'",
        "'message'='%(message)s'")))
    handler.setFormatter(formatter)
    log.addHandler(handler)

# Initialize driver
driver = webdriver.Firefox()
driver.implicitly_wait(30)
driver.get(address)
driver.maximize_window()


##############################################################################
# TESTS BELOW; BOILERPLATE ABOVE
##############################################################################

##########################################
# Test 1: Sanity check for page title
##########################################
log.info("Testing page title")
expected_text = "M.A.S.T. for DP"
if expected_text in driver.title:
    log.info("Page title valid.")
else:
    log.error('Page title not valid! expected "{}", got "{}"')
#
# # Add appliances
for appliance in appliances:
    log.info("Adding appliance {}".format(appliance["hostname"]))
    elem = driver.find_element_by_name("hostname")
    elem.clear()
    elem.send_keys(appliance["hostname"])
    elem = driver.find_element_by_name("username")
    elem.clear()
    elem.send_keys(appliance["username"])
    elem = driver.find_element_by_name("password")
    elem.clear()
    elem.send_keys(appliance["password"])
    elem = driver.find_element_by_name("global_no_check_hostname")
    if not elem.is_selected():
        elem.click()
    elem = driver.find_element_by_id("addAppliance")
    elem.click()
    wait_for_element_by_id(driver, appliance["hostname"])

######################################
# test 2: All tabs should be there
######################################
sleep(delay)
tabs = [
    "accounts",
    "backups",
    "crypto",
    "deployment",
    "developer",
    "network",
    "ssh",
    "status",
    "system"
]
for tab in tabs:
    try:
        driver.find_element_by_link_text(tab)
        log.info("Found tab {}.".format(tab))
    except selenium.common.exceptions.NoSuchElementException:
        log.error("tab {} not found!".format(tab))

#######################
# test 3: status tab
#######################
sleep(delay)
driver.find_element_by_link_text("status").click()
driver.find_element_by_name("metrics").click()
for elem in driver.find_elements_by_css_selector("input[type='checkbox']"):
    log.debug("Checking checkbox {}".format(elem.get_attribute("value")))
    if not elem.is_selected():
        elem.click()
driver.find_element_by_name("metrics").click()
log.info("Starting the status chart")
driver.find_element_by_name("statusCharting").click()

panes = [
    "status_CPUUsage.tenSeconds_container",
    "status_MemoryStatus.Usage_container",
    "status_TCPSummary.established_container",
    "status_FilesystemStatus.FreeTemporary_container",
    "status_FilesystemStatus.FreeEncrypted_container",
    "status_FilesystemStatus.FreeInternal_container",
    "status_SystemUsage.Load_container",
    "status_SystemUsage.WorkList_container"
]

for pane in panes:
    try:
        driver.find_element_by_id(pane)
        log.info("Pane {} exists.".format(pane))
    except selenium.common.exceptions.NoSuchElementException:
        log.error("Pane {} does not exist!".format(pane))
# TODO: Find a way to test that this has been running during the entire demo

###################################################
# test 4: system -> get status -> DateTimeStatus
###################################################
sleep(delay)
log.debug("Testing system -> get status -> DateTimeStatus")
driver.find_element_by_link_text("system").click()
driver.find_element_by_id("get status").click()

log.debug("Finding form")
form = driver.find_element_by_name("get_status")

log.debug("Selecting Provider")
provider = Select(form.find_element_by_class_name("multiSelect"))
provider.select_by_visible_text("DateTimeStatus")
form.find_element_by_class_name("multiSelect").click()

log.debug("Selecting default domain")
domain = Select(form.find_element_by_name("Domain"))
domain.select_by_visible_text("default")
form.find_element_by_name("Domain").click()

log.debug("Selecting no-check-hostname")
form.find_element_by_name("no_check_hostname").click()

log.debug("Submitting form")
form.find_element_by_id("systemFormSubmit").click()

log.debug("Form submitted, waiting at most 30 seconds for results to appear")
results = driver.find_element_by_xpath("/html/body/div[3]/div/div[9]/table/tbody/tr/td[3]/pre/div")

log.debug("Found results. Testing")
for appliance in appliances:
    log.debug("Looking for hostname {}.".format(appliance["hostname"]))
    assert appliance["hostname"] in results.text
log.info("all hostnames were found in output")

log.debug("closing output table")
results.find_element_by_class_name("output_close").click()

#########################
# Test 5: List domains
#########################
sleep(delay)
log.info("Testing system -> list domains")
driver.find_element_by_id("list domains").click()

log.debug("Finding form")
form = driver.find_element_by_name("list_domains")

log.debug("Selecting no-check-hostname")
form.find_element_by_name("no_check_hostname").click()

log.debug("Submitting form")
form.find_element_by_id("systemFormSubmit").click()

log.debug("Form submitted, waiting at most 30 seconds for results to appear")
results = driver.find_element_by_xpath("/html/body/div[3]/div/div[9]/table/tbody/tr/td[3]/pre/div")

log.debug("Found results. Testing")
expected_texts = [appliance["hostname"] for appliance in appliances]
expected_texts += ["All", "default"]
for expected_text in expected_texts:
    log.debug("Looking for '{}' in results".format(expected_text))
    assert expected_text in results.text
log.info("All expected text was found in results")

log.debug("closing output table")
results.find_element_by_class_name("output_close").click()

########################
# Test 6: Add domain
########################
sleep(delay)
log.info("Testing system -> add domain")
driver.find_element_by_id("add domain").click()

log.debug("Finding form")
form = driver.find_element_by_name("add_domain")

log.debug("Typing name for new domain 'demo'")
form.find_element_by_name("domain_name").send_keys("demo")

log.debug("Selecting no-check-hostname")
form.find_element_by_name("no_check_hostname").click()

log.debug("Submitting form")
form.find_element_by_id("systemFormSubmit").click()

log.debug("Form submitted, waiting at most 30 seconds for results to appear")
results = driver.find_element_by_xpath("/html/body/div[3]/div/div[9]/table/tbody/tr/td[3]/pre/div")

log.debug("Found results. Testing")
expected_texts = [appliance["hostname"] for appliance in appliances]
expected_texts += ["Succeeded"]
for expected_text in expected_texts:
    log.debug("Looking for '{}' in results".format(expected_text))
    assert expected_text in results.text
log.info("All expected text was found in results")

log.debug("closing output table")
results.find_element_by_class_name("output_close").click()

#########################
# Test 7: List domains
#########################
sleep(delay)
log.info("Testing system -> list domains "
         "(looking for domain demo which should have been added)")
driver.find_element_by_id("list domains").click()

log.debug("Finding form")
form = driver.find_element_by_name("list_domains")

log.debug("Selecting no-check-hostname")
form.find_element_by_name("no_check_hostname").click()

log.debug("Submitting form")
form.find_element_by_id("systemFormSubmit").click()

log.debug("Form submitted, waiting at most 30 seconds for results to appear")
results = driver.find_element_by_xpath("/html/body/div[3]/div/div[9]/table/tbody/tr/td[3]/pre/div")

log.debug("Found results. Testing")
expected_texts = [appliance["hostname"] for appliance in appliances]
expected_texts += ["All", "default", "demo"]
for expected_text in expected_texts:
    log.debug("Looking for '{}' in results".format(expected_text))
    assert expected_text in results.text
log.info("All expected text was found in results")

log.debug("closing output table")
results.find_element_by_class_name("output_close").click()

##########################
# Test 8: get filestore
##########################
sleep(delay)
log.info("Testing system -> get filestore")
driver.find_element_by_id("get filestore").click()

log.debug("Finding form")
form = driver.find_element_by_name("get_filestore")

log.debug("Selecting default domain")
domain = Select(form.find_element_by_name("Domain"))
domain.select_by_visible_text("default")
form.find_element_by_name("Domain").click()

log.debug("Setting location to pubcert:")
location = form.find_element_by_name("location")
location.clear()
location.send_keys("pubcert:")

log.debug("Selecting no-check-hostname")
form.find_element_by_name("no_check_hostname").click()

log.debug("Submitting form")
form.find_element_by_id("systemFormSubmit").click()

log.debug("Form submitted, waiting at most 30 seconds for results to appear")
results = driver.find_element_by_xpath("/html/body/div[3]/div/div[9]/table/tbody/tr/td[3]/pre/div")

log.debug("Found results. Testing")
expected_texts = [appliance["hostname"] for appliance in appliances]
expected_texts += ["See Download"]
for expected_text in expected_texts:
    log.debug("Looking for '{}' in results".format(expected_text))
    assert expected_text in results.text
log.info("All expected text was found in results")

log.debug("closing output table")
results.find_element_by_class_name("output_close").click()


##########################
# Test 9: cleanup
##########################
sleep(delay)
log.info("Testing system -> clean up")
driver.find_element_by_xpath("/html/body/div[3]/div/div[9]/table/tbody/tr/td[1]/input[43]").click()

log.debug("Finding form")
form = driver.find_element_by_name("clean_up")

for checkbox in form.find_elements_by_css_selector("input[type=checkbox]"):
    checkbox.click()

log.debug("Selecting default domain")
domain = Select(form.find_element_by_name("Domain"))
domain.select_by_visible_text("default")
form.find_element_by_name("Domain").click()

log.debug("Submitting form")
form.find_element_by_id("systemFormSubmit").click()

log.debug("Form submitted, waiting at most 30 seconds for results to appear")
results = driver.find_element_by_xpath("/html/body/div[3]/div/div[9]/table/tbody/tr/td[3]/pre/div")

log.debug("Found results. Testing")

expected_texts = [appliance["hostname"] for appliance in appliances]
expected_texts += [
    "chkpoints:/",
    "export:/",
    "logtemp:/",
    "logstore:/",
    "ErrorReports",
    "Cleaned"
]
for expected_text in expected_texts:
    log.debug("Looking for '{}' in results".format(expected_text))
    assert expected_text in results.text
log.info("All expected text was found in results")

log.debug("closing output table")
results.find_element_by_class_name("output_close").click()

##########################
# Test 10: list groups
##########################
sleep(delay)
log.debug("Testing accounts -> list groups")
driver.find_element_by_link_text("accounts").click()
driver.find_element_by_id("list groups").click()

log.debug("Finding form")
form = driver.find_element_by_name("list_groups")

log.debug("Selecting no-check-hostname")
form.find_element_by_name("no_check_hostname").click()

log.debug("Submitting form")
form.find_element_by_id("accountsFormSubmit").click()

log.debug("Form submitted, waiting at most 30 seconds for results to appear")
results = driver.find_element_by_xpath("/html/body/div[3]/div/div[1]/table/tbody/tr/td[3]/pre/div")

log.debug("Found results. Testing")
expected_texts = [appliance["hostname"] for appliance in appliances]
expected_texts += ["All"]
for expected_text in expected_texts:
    log.debug("Looking for '{}' in results".format(expected_text))
    assert expected_text in results.text
log.info("All expected text was found in results")

log.debug("closing output table")
results.find_element_by_class_name("output_close").click()

###########################
# Test 11: add group
###########################
sleep(delay)
log.debug("Testing accounts -> add group")
driver.find_element_by_id("add group").click()

log.debug("Finding form")
form = driver.find_element_by_name("add_group")

log.debug("Adding name for group 'demoRO'")
form.find_element_by_name("name").send_keys("demoRO")

log.debug("Adding Access Policy for group 'demoRO'")
form.find_element_by_class_name("multiTextTextbox").send_keys("*/*/*?Access=r")
form.find_element_by_class_name("multiTextButton").click()

log.debug("Selecting no-check-hostname")
form.find_element_by_name("no_check_hostname").click()

log.debug("Submitting form")
form.find_element_by_id("accountsFormSubmit").click()

log.debug("Form submitted, waiting at most 30 seconds for results to appear")
results = driver.find_element_by_xpath("/html/body/div[3]/div/div[1]/table/tbody/tr/td[3]/pre/div")

log.debug("Found results. Testing")
expected_texts = [appliance["hostname"] for appliance in appliances]
expected_texts += ["Succeeded"]

for expected_text in expected_texts:
    log.debug("Looking for '{}' in results".format(expected_text))
    assert expected_text in results.text
log.info("All expected text was found in results")

log.debug("closing output table")
results.find_element_by_class_name("output_close").click()

###########################
# Test 12: add user
###########################
sleep(delay)
log.debug("Testing accounts -> add user")
driver.find_element_by_id("add user").click()

log.debug("Finding form")
form = driver.find_element_by_name("add_user")

log.debug("Adding name for user 'demoTest'")
form.find_element_by_name("username").send_keys("demoTest")

log.debug("Adding password for user 'demoTest'")
form.find_element_by_name("password").send_keys("Pa$$W0rd")

log.debug("Adding user 'demoTest' to group 'demoRO'")
form.find_element_by_name("group").send_keys("demoRO")

log.debug("Selecting save-config")
form.find_element_by_name("save_config").click()

log.debug("Selecting no-check-hostname")
form.find_element_by_name("no_check_hostname").click()

log.debug("Submitting form")
form.find_element_by_id("accountsFormSubmit").click()

log.debug("Form submitted, waiting at most 30 seconds for results to appear")
results = driver.find_element_by_xpath("/html/body/div[3]/div/div[1]/table/tbody/tr/td[3]/pre/div")

log.debug("Found results. Testing")
expected_texts = [appliance["hostname"] for appliance in appliances]
expected_texts += ["Succeeded"]

for expected_text in expected_texts:
    log.debug("Looking for '{}' in results".format(expected_text))
    assert expected_text in results.text
log.info("All expected text was found in results")

log.debug("closing output table")
results.find_element_by_class_name("output_close").click()

####################################################################
# Test 13: list groups (looking for group which should exist now)
####################################################################
sleep(delay)
log.debug("Testing accounts -> list groups "
          "(looking for group which should exist now)")
driver.find_element_by_id("list groups").click()

log.debug("Finding form")
form = driver.find_element_by_name("list_groups")

log.debug("Selecting no-check-hostname")
form.find_element_by_name("no_check_hostname").click()

log.debug("Submitting form")
form.find_element_by_id("accountsFormSubmit").click()

log.debug("Form submitted, waiting at most 30 seconds for results to appear")
results = driver.find_element_by_xpath("/html/body/div[3]/div/div[1]/table/tbody/tr/td[3]/pre/div")

log.debug("Found results. Testing")
expected_texts = [appliance["hostname"] for appliance in appliances]
expected_texts += ["All", "demoRO"]
for expected_text in expected_texts:
    log.debug("Looking for '{}' in results".format(expected_text))
    assert expected_text in results.text
log.info("All expected text was found in results")

log.debug("closing output table")
results.find_element_by_class_name("output_close").click()

#############################################################
# Test 14: list users (looking for user which should exist)
#############################################################
sleep(delay)
log.debug("Testing accounts -> list users "
          "(looking for user which should exist now)")
driver.find_element_by_id("list users").click()

log.debug("Finding form")
form = driver.find_element_by_name("list_users")

log.debug("Selecting no-check-hostname")
form.find_element_by_name("no_check_hostname").click()

log.debug("Submitting form")
form.find_element_by_id("accountsFormSubmit").click()

log.debug("Form submitted, waiting at most 30 seconds for results to appear")
results = driver.find_element_by_xpath("/html/body/div[3]/div/div[1]/table/tbody/tr/td[3]/pre/div")

log.debug("Found results. Testing")
expected_texts = [appliance["hostname"] for appliance in appliances]
expected_texts += ["All", "demoTest"]
for expected_text in expected_texts:
    log.debug("Looking for '{}' in results".format(expected_text))
    assert expected_text in results.text
log.info("All expected text was found in results")

log.debug("closing output table")
results.find_element_by_class_name("output_close").click()

#######################
# Test 15: del user
#######################
sleep(delay)
log.debug("Testing accounts -> del user "
          "(looking for user which should exist now)")
driver.find_element_by_id("del user").click()

log.debug("Finding form")
form = driver.find_element_by_name("del_user")

log.debug("Selecting save-config")
form.find_element_by_name("save_config").click()

log.debug("Selecting no-check-hostname")
form.find_element_by_name("no_check_hostname").click()

log.debug("Selecting user demoTest")
domain = Select(form.find_element_by_name("User"))
domain.select_by_visible_text("demoTest")
form.find_element_by_name("User").click()

log.debug("Submitting form")
form.find_element_by_id("accountsFormSubmit").click()

log.debug("Form submitted, waiting at most 30 seconds for results to appear")
results = driver.find_element_by_xpath("/html/body/div[3]/div/div[1]/table/tbody/tr/td[3]/pre/div")

log.debug("Found results. Testing")
expected_texts = [appliance["hostname"] for appliance in appliances]
expected_texts += ["Succeeded"]
for expected_text in expected_texts:
    log.debug("Looking for '{}' in results".format(expected_text))
    assert expected_text in results.text
log.info("All expected text was found in results")

log.debug("closing output table")
results.find_element_by_class_name("output_close").click()

#######################
# Test 15: del group
#######################
sleep(delay)
log.debug("Testing accounts -> del group "
          "(looking for user which should exist now)")
driver.find_element_by_id("del group").click()

log.debug("Finding form")
form = driver.find_element_by_name("del_group")

log.debug("Selecting save-config")
form.find_element_by_name("save_config").click()

log.debug("Selecting no-check-hostname")
form.find_element_by_name("no_check_hostname").click()

log.debug("Selecting user group demoRO")
group = Select(form.find_element_by_name("UserGroup"))
group.select_by_visible_text("demoRO")
form.find_element_by_name("UserGroup").click()

log.debug("Submitting form")
form.find_element_by_id("accountsFormSubmit").click()

log.debug("Form submitted, waiting at most 30 seconds for results to appear")
results = driver.find_element_by_xpath("/html/body/div[3]/div/div[1]/table/tbody/tr/td[3]/pre/div")

log.debug("Found results. Testing")
expected_texts = [appliance["hostname"] for appliance in appliances]
expected_texts += ["Succeeded"]
for expected_text in expected_texts:
    log.debug("Looking for '{}' in results".format(expected_text))
    assert expected_text in results.text
log.info("All expected text was found in results")

log.debug("closing output table")
results.find_element_by_class_name("output_close").click()

###############################
# Test 16: get normal backup
###############################
sleep(delay)
log.debug("Testing backups -> get normal backup`")
driver.find_element_by_link_text("backups").click()
driver.find_element_by_id("get normal backup").click()

log.debug("Finding form")
form = driver.find_element_by_name("get_normal_backup")

log.debug("Adding comment")
form.find_element_by_name("comment").send_keys("test")

log.debug("Selecting domain")
domain = Select(form.find_element_by_class_name("multiSelect"))
domain.select_by_visible_text("demo")
form.find_element_by_class_name("multiSelect").click()

log.debug("Selecting no-check-hostname")
form.find_element_by_name("no_check_hostname").click()

log.debug("Submitting form")
form.find_element_by_id("backupsFormSubmit").click()

log.debug("Form submitted, waiting at most 30 seconds for results to appear")
results = driver.find_element_by_xpath("/html/body/div[3]/div/div[2]/table/tbody/tr/td[3]/pre/div")

log.debug("Found results. Testing")
expected_texts = [appliance["hostname"] for appliance in appliances]
expected_texts += ["Verified"]
for expected_text in expected_texts:
    log.debug("Looking for '{}' in results".format(expected_text))
    assert expected_text in results.text
log.info("All expected text was found in results")

log.debug("closing output table")
results.find_element_by_class_name("output_close").click()

#############################
# Test 17: set checkpoint
#############################
sleep(delay)
log.debug("Testing backups -> set checkpoint`")
driver.find_element_by_id("set checkpoint").click()

log.debug("Finding form")
form = driver.find_element_by_name("set_checkpoint")

log.debug("Adding comment")
form.find_element_by_name("comment").send_keys("test")

log.debug("Selecting domain")
domain = Select(form.find_element_by_class_name("multiSelect"))
domain.select_by_visible_text("demo")
form.find_element_by_class_name("multiSelect").click()

log.debug("Selecting no-check-hostname")
form.find_element_by_name("no_check_hostname").click()

log.debug("Submitting form")
form.find_element_by_id("backupsFormSubmit").click()

log.debug("Form submitted, waiting at most 30 seconds for results to appear")
results = driver.find_element_by_xpath("/html/body/div[3]/div/div[2]/table/tbody/tr/td[3]/pre/div")

log.debug("Found results. Testing")
expected_texts = [appliance["hostname"] for appliance in appliances]
expected_texts += ["Succeeded"]
for expected_text in expected_texts:
    log.debug("Looking for '{}' in results".format(expected_text))
    assert expected_text in results.text
log.info("All expected text was found in results")

log.debug("closing output table")
results.find_element_by_class_name("output_close").click()

#################################
# Test 18: flush document cache
#################################
sleep(delay)
log.debug("Testing developer -> flush document cache`")
driver.find_element_by_link_text("developer").click()
driver.find_element_by_id("flush document cache").click()

log.debug("Finding form")
form = driver.find_element_by_name("flush_document_cache")

log.debug("Adding xml manager")
form.find_element_by_name("xml_manager").send_keys("default")

log.debug("Selecting domain")
domain = Select(form.find_element_by_name("Domain"))
domain.select_by_visible_text("demo")
form.find_element_by_name("Domain").click()

log.debug("Selecting no-check-hostname")
form.find_element_by_name("no_check_hostname").click()

log.debug("Submitting form")
form.find_element_by_id("developerFormSubmit").click()

log.debug("Form submitted, waiting at most 30 seconds for results to appear")
results = driver.find_element_by_xpath("/html/body/div[3]/div/div[5]/table/tbody/tr/td[3]/pre/div")

log.debug("Found results. Testing")
expected_texts = [appliance["hostname"] for appliance in appliances]
expected_texts += ["Succeeded"]
for expected_text in expected_texts:
    log.debug("Looking for '{}' in results".format(expected_text))
    assert expected_text in results.text
log.info("All expected text was found in results")

log.debug("closing output table")
results.find_element_by_class_name("output_close").click()

#################################
# Test 19: show probes
#################################
sleep(delay)
log.debug("Testing developer -> list probes`")
driver.find_element_by_id("list probes").click()

log.debug("Finding form")
form = driver.find_element_by_name("list_probes")

log.debug("Selecting domain")
domain = Select(form.find_element_by_class_name("multiSelect"))
domain.select_by_visible_text("demo")
form.find_element_by_class_name("multiSelect").click()

log.debug("Selecting no-check-hostname")
form.find_element_by_name("no_check_hostname").click()

log.debug("Submitting form")
form.find_element_by_id("developerFormSubmit").click()

log.debug("Form submitted, waiting at most 30 seconds for results to appear")
results = driver.find_element_by_xpath("/html/body/div[3]/div/div[5]/table/tbody/tr/td[3]/pre/div")

log.debug("Found results. Testing")
expected_texts = ["Appliance", "Result"]
for expected_text in expected_texts:
    log.debug("Looking for '{}' in results".format(expected_text))
    assert expected_text in results.text
log.info("All expected text was found in results")

log.debug("closing output table")
results.find_element_by_class_name("output_close").click()

#################################
# Test 20: display routing table
#################################
sleep(delay)
log.debug("Testing network -> display routing table`")
driver.find_element_by_link_text("network").click()
driver.find_element_by_id("display routing table").click()

log.debug("Finding form")
form = driver.find_element_by_name("display_routing_table")

log.debug("Selecting no-check-hostname")
form.find_element_by_name("no_check_hostname").click()

log.debug("Submitting form")
form.find_element_by_id("networkFormSubmit").click()

log.debug("Form submitted, waiting at most 30 seconds for results to appear")
results = driver.find_element_by_xpath("/html/body/div[3]/div/div[6]/table/tbody/tr/td[3]/pre/div")

log.debug("Found results. Testing")
expected_texts = [appliance["hostname"] for appliance in appliances]
expected_texts += ["Appliance",
                   "IPType",
                   "Destination",
                   "PrefixLength",
                   "InterfaceType",
                   "MacInterface",
                   "GatewayIPType",
                   "Gateway",
                   "Metric"]
for expected_text in expected_texts:
    log.debug("Looking for '{}' in results".format(expected_text))
    assert expected_text in results.text
log.info("All expected text was found in results")

log.debug("closing output table")
results.find_element_by_class_name("output_close").click()

##################################
# Test 21: tcp connection test
##################################
sleep(delay)
log.debug("Testing network -> tcp connection test")
driver.find_element_by_id("tcp connection test").click()

log.debug("Finding form")
form = driver.find_element_by_name("tcp_connection_test")

log.debug("Adding remote hosts")
for appliance in appliances:
    form.find_element_by_xpath("/html/body/div[3]/div/div[6]/table/tbody/tr/td[2]/div/div/div[2]/input[1]").send_keys(appliance["hostname"])
    form.find_element_by_xpath("/html/body/div[3]/div/div[6]/table/tbody/tr/td[2]/div/div/div[2]/input[2]").click()

log.debug("Adding remote ports")
for port in ["22", "5550", "9090"]:
    form.find_element_by_xpath("/html/body/div[3]/div/div[6]/table/tbody/tr/td[2]/div/div/div[3]/input[1]").send_keys(port)
    form.find_element_by_xpath("/html/body/div[3]/div/div[6]/table/tbody/tr/td[2]/div/div/div[3]/input[2]").click()

log.debug("Selecting no-check-hostname")
form.find_element_by_name("no_check_hostname").click()

log.debug("Submitting form")
form.find_element_by_id("networkFormSubmit").click()

log.debug("Form submitted, waiting at most 30 seconds for results to appear")
results = driver.find_element_by_xpath("/html/body/div[3]/div/div[6]/table/tbody/tr/td[3]/pre/div")

log.debug("Found results. Testing")
expected_texts = [appliance["hostname"] for appliance in appliances]
expected_texts += ["Appliance",
                   "Remote Host",
                   "Remote Port",
                   "Success",
                   "True"]
for expected_text in expected_texts:
    log.debug("Looking for '{}' in results".format(expected_text))
    assert expected_text in results.text
log.info("All expected text was found in results")

log.debug("closing output table")
results.find_element_by_class_name("output_close").click()

################################
# Test 22: ssh
################################
sleep(delay)
log.debug("Testing ssh")
driver.find_element_by_link_text("ssh").click()

command = driver.find_element_by_name("sshCommand")
submit = driver.find_element_by_name("sshCommandButton")

command.send_keys("show clock")
submit.click()

while True:
    name = "textarea_{}".format(appliances[0]["hostname"])
    textarea = driver.find_element_by_name(name)
    if textarea.get_attribute("value"):
        break
    sleep(0.5)

command.send_keys("config")
submit.click()
sleep(delay)

command.send_keys("switch domain demo")
submit.click()
sleep(delay)

command.send_keys("dir local:///ondisk/")
submit.click()
sleep(delay)

command.send_keys("mkdir local:///ondisk/SimpleStatus")
submit.click()
sleep(delay)

command.send_keys("switch domain default")
submit.click()
sleep(delay)

command.send_keys("exit")
submit.click()
sleep(delay)

command.send_keys("exit")
submit.click()
sleep(delay)

results = [driver.find_element_by_name("textarea_" + appliance["hostname"]).get_attribute("value") for appliance in appliances]

log.debug("Found results. Testing")
expected_texts = [
    "show clock",
    "config",
    "switch domain demo",
    "dir local:///ondisk/",
    "mkdir local:///ondisk/SimpleStatus",
    "switch domain default",
    "exit",
    "Goodbye."
]
for result in results:
    for expected_text in expected_texts:
        log.debug("Looking for '{}' in results".format(expected_text))
        assert expected_text in result
log.info("All expected text was found in results")

#############################################################################
driver.find_element_by_link_text("status").click()

# log.info("Tests complete, closing browser.")
# driver.close()
# log.info("Browser closed.")
