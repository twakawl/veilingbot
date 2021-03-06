import time
from selenium import webdriver
from selenium.common.exceptions import StaleElementReferenceException
from tv_credentials import USERNAME, PASSWORD
from veilingbotcore import log, make_screenshot, ravenclient, click_element_when_available, wait_for_element, VeilingAPI


class TicketVeiling(VeilingAPI):
    def get_remaining_secs(self):
        seconds_left = ''
        while not seconds_left.isdigit():
            countdownbox = self.browser.find_element_by_class_name("countdownbox")
            counter = countdownbox.text
            splitted_remaining_time = counter.split()

            if not splitted_remaining_time or splitted_remaining_time == [u'Gesloten'] or splitted_remaining_time[:10] == u"Een moment":
                log('Auction has ended.')
                make_screenshot(self.browser)
                return 0

            if len(splitted_remaining_time) == 3:
                # includes hour
                remaining_hours = int(splitted_remaining_time[0].split("uur")[0])
            elif len(splitted_remaining_time) == 2:
                # excludes hour
                remaining_hours = 0
            else:
                # something is wrong
                log("DEBUG: Could not parse splitted_remaining_time '%s', auction is probably ending."
                    % splitted_remaining_time)
            try:
                remaining_mins = int(splitted_remaining_time[-2].split("min")[0])
                remaining_secs = int(splitted_remaining_time[-1].split("sec")[0])
                seconds_left = remaining_secs
                seconds_left += (remaining_mins * 60)
                seconds_left += ((remaining_hours * 60) * 60)
                seconds_left = int(seconds_left)
                return seconds_left
            except ValueError:
                log("Caught ValueError")
                log(counter)
                raise

    def get_current_bid(self):
        for price in self.browser.find_elements_by_class_name('priceVeiling'):
            if price.is_displayed() and price.text:
                return int(price.text)

    def get_latest_bidder(self):
        bids = wait_for_element(self.browser.find_element_by_xpath, '//div[@id="bidWrapper"]/div[@id="bids"]')
        splitted_bids = bids.text.split("\n")
        # List is now in format:
        # [u'1'                  <-- number of bid in list,
        # u'\u20ac 17',          <-- EUR <amount>
        # u'15:11:04 Odettaah',  <-- time and bidder
        # ... and this for every bid

        # So, pick the third item of the list, split it by space and fetch the last part (and join it by spaces).
        try:
            last_bidder = ' '.join(splitted_bids[2].split()[1:])
        except:
            log("FAILING ON: %s" % splitted_bids)
            raise

        return last_bidder

    def do_login(self):
        log('Signing in')
        email = self.browser.find_element_by_id("loginEmail")
        passwd = self.browser.find_element_by_id('loginPassword')
        button = self.browser.find_element_by_id('login')

        email.send_keys(USERNAME)
        passwd.send_keys(PASSWORD)
#        button.click()
        keys = webdriver.common.keys.Keys()
        passwd.send_keys(keys.ENTER)

        counter = 0
        log('Waiting max. 30 seconds')
        while not self.browser.find_elements_by_id("loggedinContainer"):
            time.sleep(1)
            counter += 1
            log(counter)
            if counter > 30:
                log('Login failed.')
                make_screenshot(self.browser)
                return False
        else:
            log('Logged in successfully.')
            return True

    def do_place_bid(self, price):
        log("ACTION is %s" % self.action)
        if self.action != "bid":
            log("We are doing a dry run. Not bidding! Creating screenshot instead.")
            make_screenshot(self.browser)
            return

        if int(price) > int(self.max_price):
            log("FAILSAFE (this should not happen): not placing bid of %s, it's higher than %s" % (price, self.max_price))
        else:
            log("Placing bid of '%s' euro" % price )
            ub = self.browser.find_element_by_id('userBid')
            # first clear the input field!
            log('DEBUG: Clearing input field')
            ub.clear()
            log('DEBUG: Sending %s to input field' % price)
            ub.send_keys(price)

#            log('DEBUG: Sending ENTER to input field')
#            keys = webdriver.common.keys.Keys()
#            ub.send_keys(keys.ENTER)

            log("DEBUG: Clicking Bid button")
            bb = self.browser.find_element_by_id('bidButton')
            bb.click()

            time.sleep(0.1)
            log('DEBUG: Clicking YES')
            click_element_when_available(self.browser.find_element_by_class_name, "yesButton")

            time.sleep(0.1)
            log('DEBUG: Clicking OK')
            click_element_when_available(self.browser.find_element_by_class_name, "yesButtonCentered")

            log('Placed bid for %s EUR' % price)
            time.sleep(0.2)
