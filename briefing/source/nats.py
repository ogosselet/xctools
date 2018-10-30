'''NOTAM Briefing Source (NATS Module)

'''

from __future__ import absolute_import, division, print_function
from base import NotamSource
from lxml import html

import time
import datetime
import re

import logging
logger = logging.getLogger(__name__)

# CONSTANT
NATS_FQDN = "www.nats-uk.ead-it.com"
NATS_PROTO = "http://"
LOGIN_REF = "/public/index.php%3Foption=com_content&task=blogcategory&id=166&Itemid=4.html"
LOGIN_URI = "/fwf-natsuk/public/user/account/login.faces"
AREA_BRIEF_URI = "/fwf-natsuk/restricted/user/ino/brief_area.faces"
# We will look for this string to confirm the successfull login
LOGIN_CONFIRM_STRING = "Delivers a briefing containing FIR NOTAM"


class NATS(NotamSource):
    '''NATS implementation

    The NATS specific class will overwrite all the method as described in the base class documentation

    Args:
        NotamSource ([object]): The NotamSource superclass defining the common interface of all sources

    Raises:
        UserWarning: [description]
        ValueError: [description]
        ValueError: [description]
        an: [description]

    Returns:
        [type]: [description]

    Other parameters:
        lower_fl: '0'
        upper_fl: '999'
        ifr': True
        vfr: True
        firs: ['EBBU', 'LFFF']
        utc_from: datetime.datetime(2018, 9, 12, 12, 0)
        utc_to: datetime.datetime(2018, 9, 12, 17, 0)

    '''

    source_name = "NATS"

    #def print_source(self):
    #    print("NATS Class Source " + self.source_name)

    def _login_sequence(self):
        # Login URL
        logger.debug("Login %s with password to %s", self.username, self.source_name)

        # PREPARE LOGIN
        # GET login page, prepare the session
        url = "{}{}{}".format(NATS_PROTO, NATS_FQDN, LOGIN_URI)
        headers = {
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8',
            'Accept-Encoding': 'gzip, deflate, sdch',
            'Accept-Language': 'en-US,en;q=0.9,fr;q=0.8',
            'Cache-Control': 'max-age=0',
            'Connection': 'keep-alive',
            'Host': NATS_FQDN,
            'Origin': '{}{}'.format(NATS_PROTO, NATS_FQDN),
            'Referer': '{}{}{}'.format(NATS_PROTO, NATS_FQDN, LOGIN_REF),
            'Upgrade-Insecure-Requests': '1',
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_13_4) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/65.0.3325.181 Safari/537.36'
        }
        r = self.req_session.get(url, headers=headers)

        # Second GET required (need to see if we can lower/suppress this timer)
        #time.sleep(2)
        r = self.req_session.get(url, headers=headers)

        # PERFORM LOGIN
        # POST login form
        # Updating the referer in the header - LOGIN_REF becomes LOGIN_URI
        headers['Referer'] = '{}{}{}'.format(NATS_PROTO, NATS_FQDN, LOGIN_URI)
        # Building our payload
        payload = {
            'j_username': self.username,
            'j_password': self.password,
	        'mainForm:login': 'Login',
	        'mainForm_SUBMIT': '1',
	        'mainForm:_idcl': '',
	        'mainForm:_link_hidden_': '',
            'javax.faces.ViewState': 'rO0ABXVyABNbTGphdmEubGFuZy5PYmplY3Q7kM5YnxBzKWwCAAB4cAAAAAN0AAEzcHQAHy9wdWJsaWMvdXNlci9hY2NvdW50L2xvZ2luLmpzcHg='
            }
        r = self.req_session.post(url, data=payload, headers=headers)
        time.sleep(2)
        r = self.req_session.post(url, data=payload, headers=headers)

        # Our session has a cookie now :-)
        # print(self.req_session.cookies)
        # Despite obvious Exceptions we need to find something "stable" in the content
        # to confirm the login
        if not re.search(LOGIN_CONFIRM_STRING, r.text):
            raise UserWarning('NATS successfull login not confirmed')

    def _download_area_briefing(self):

        # Building a valid filter
        filter_data = {}
        filter_data['lower_fl'] = self.prefilter.get('lower_fl', '0')
        filter_data['upper_fl'] = self.prefilter.get('upper_fl', '999')
        filter_data['ifr'] = self.prefilter.get('ifr', False)
        filter_data['vfr'] = self.prefilter.get('vfr', True)
        filter_data['utc_from'] = self.prefilter.get('utc_from', datetime.datetime.now())
        filter_data['utc_to'] = self.prefilter.get('utc_to', datetime.datetime.now() + datetime.timedelta(days=1))
        # Yes ... this is developped in Belgium :-)
        filter_data['firs'] = self.prefilter.get('firs', ['EBBU'])

        # Making sure the filter is not specifying a criteria we don't support
        supported_keys = set(filter_data.keys())
        provided_keys = set(self.prefilter.keys())
        if len(provided_keys - supported_keys) > 0:
            raise ValueError('Unsuported filter operation required', provided_keys - supported_keys)

        # In the case of NATS, FIR list can contain a max. of 20 entries
        if len(filter_data['firs']) > 20:
            raise ValueError('Too many FIRS requested ({} max 20)'.format(len(filter_data['firs'])))

        # There should be a bit more validation on these data
        # ifr vfr cannot be both False

        # ToDo: Initial GET on the are_briefing URL
        # => would allow us to retrieve:
        #  - 'briefingId'
        #  - 'faces.ViewState'
        # This could be better to have a POST 100% compliant
        # Until now this has not generated any bug.

        # Building the "POST" Payload based on the filter

        traffic = ''
        if filter_data['ifr']:
            traffic = traffic + 'I'
        if filter_data['vfr']:
            traffic = traffic + 'V'

        payload = {
            'mainForm:briefingId': '1809040556', # we should extract this from the GET
            'mainForm:startValidityDay': str(filter_data['utc_from'].day),
            'mainForm:startValidityMonth': str(filter_data['utc_from'].month-1),
            'mainForm:startValidityYear': str(filter_data['utc_from'].year),
            'mainForm:startValidityHour': str(filter_data['utc_from'].hour),
            'mainForm:startValidityMinute': str(filter_data['utc_from'].minute),
            'mainForm:endValidityDay': str(filter_data['utc_to'].day),
            'mainForm:endValidityMonth': str(filter_data['utc_to'].month-1),
            'mainForm:endValidityYear': str(filter_data['utc_to'].year),
            'mainForm:endValidityHour': str(filter_data['utc_to'].hour),
            'mainForm:endValidityMinute': str(filter_data['utc_to'].minute),
            'mainForm:traffic': traffic,
            'mainForm:lowerFL': filter_data['lower_fl'],
            'mainForm:upperFL': filter_data['upper_fl'],
            # FIRS fields will be constructed with a loop
            # 'mainForm:fir_0..19': value
            # Some "hardcoded" fields value
            'mainForm:generate': 'Submit',
            'searchId': '',
            'mainForm:checkMsg': 'checkMsg',
            'mainForm_SUBMIT': '1',
            'mainForm:_idcl': '',
            'formRef': '',
            'mainForm:_link_hidden_': '',
            'javax.faces.ViewState': 'rO0ABXVyABNbTGphdmEubGFuZy5PYmplY3Q7kM5YnxBzKWwCAAB4cAAAAAN0AAE3cHQAJC9yZXN0cmljdGVkL3VzZXIvaW5vL2JyaWVmX2FyZWEuanNweA=='
        }

        for i in range(len(filter_data['firs'])):
            #print(i)
            #print('mainForm:fir_{}'.format(i))
            payload['mainForm:fir_{}'.format(i)] = filter_data['firs'][i]
            payload['searchVal'] = filter_data['firs'][i]
            j = i
        for i in range(j+1, 20):
            #print(i)
            #print('mainForm:fir_{}'.format(i))
            payload['mainForm:fir_{}'.format(i)] = ''

        # PREPARE DOWNLOAD
        # GET "brief_area" page
        url = "{}{}{}".format(NATS_PROTO, NATS_FQDN, AREA_BRIEF_URI)
        headers = {
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8',
            'Accept-Encoding': 'gzip, deflate, sdch',
            'Accept-Language': 'en-US,en;q=0.9,fr;q=0.8',
            'Cache-Control': 'max-age=0',
            'Connection': 'keep-alive',
            'Host': NATS_FQDN,
            'Origin': '{}{}'.format(NATS_PROTO, NATS_FQDN),
            'Referer': '{}{}{}'.format(NATS_PROTO, NATS_FQDN, AREA_BRIEF_URI),
            'Upgrade-Insecure-Requests': '1',
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_13_4) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/65.0.3325.181 Safari/537.36'
        }
        r = self.req_session.get(url, headers=headers)

        # PERFORM DOWNLOAD
        # POST "download" form
        print(payload)
        r = self.req_session.post(url, data=payload, headers=headers, cookies=self.req_session.cookies)
        # Looks like this sleep is required !
        time.sleep(5)
        # Looks like the second post is required !
        # This "duplicate" stuff needs to be investigated !
        r = self.req_session.post(url, data=payload, headers=headers, cookies=self.req_session.cookies)

        # ToDo: Check that the result looks valid, if not raise an exception ?
        self.raw_area_briefing = r.content

        #file_briefing = open("briefing.html", "w")
        #file_briefing.write(r.content)
        #file_briefing.close()

    def _parse_area_briefing(self):

        #file_briefing = open("briefing.html", "r")
        #self.raw_area_briefing = file_briefing.read()
        #file_briefing.close()

        # Loading the briefing with lxml
        tree = html.fromstring(self.raw_area_briefing)

        # Extracting all html "tables" with Notams
        notam_tables = tree.xpath('//div[@class="fullTableContainer"]')
        # Table 0, 2, 4 ... are En-Route
        # Table 1, 3, 5 ... are Warnings
        # The structure of the html is slightly different in those 2 tables
        # => we use 2 different "parse" method

        i = 0
        for notam_table in notam_tables:
            table_rows = notam_table.xpath('./table/tr')
            if i % 2 == 0:
                parse_row = self._parse_row_even_table_notam
            else:
                parse_row = self._parse_row_odd_table_notam
            i = i + 1
            for table_row in table_rows:
                parsed_row = parse_row(table_row)
                #print(parsed_row['e_line'])
                # Finalize the split & clean of this dict of "lines"
                notam_row = self._finalize_row(parsed_row)
                #if notam_row <> '':
                if notam_row:
                    self.parsed_briefing.append(notam_row)

    def _finalize_row(self, line_dict):
        # Notam Ref
        final_notam = {}
        final_notam['ref'] = line_dict['notam_ref']
        # Q Line
        #a_match = re.search('(Q\)) (.*)', line_dict['q_line'])
        a_match = re.search(r'(Q\)) (.*)', line_dict['q_line'])
        if a_match:
            final_notam['q'] = a_match.group(2)
        else:
            final_notam['q'] = ''

        #final_notam['q'] = line_dict['q_line']
        # Our abc_line is multiline and it doesn't work well with search
        # Let's remove our extra \n first
        abc_line = line_dict['abc_line'].replace('\n', ' ')

        # Extracting A)
        a_match = re.search(r'(A\)) (.*) (B\))', abc_line)
        if a_match:
            final_notam['a'] = a_match.group(2)
        else:
            final_notam['a'] = ''

        # Extracting B)
        b_match = re.search(r'(B\) FROM:) (.*)(C\))', abc_line)
        if b_match:
            final_notam['b'] = b_match.group(2)
        else:
            final_notam['b'] = ''

        # Extracting C)
        c_match = re.search(r'(C\) TO:) (.*)', abc_line)
        if c_match:
            final_notam['c'] = c_match.group(2)
        else:
            final_notam['c'] = ''

        # Extracting E)
        e_line = line_dict['e_line'].replace('\n', ' ')
        e_match = re.search(r'(E\)) (.*)', e_line)
        if e_match:
            final_notam['e'] = e_match.group(2)
        else:
            final_notam['e'] = ''


        # Clean LOWER, UPPER, ...
        try:
            final_notam['lower'] = line_dict['lower_line'].replace('LOWER: ', '')
        except:
            final_notam['lower'] = ''

        try:
            final_notam['upper'] = line_dict['upper_line'].replace('UPPER: ', '')
        except:
            final_notam['upper'] = ''

        try:
            final_notam['sched'] = line_dict['schedule_line'].replace('SCHEDULE: ', '')
        except:
            final_notam['sched'] = ''


        final_notam['src'] = self.source_name

        return final_notam


    def _parse_row_even_table_notam(self, table_row):
        # The NOTAM ref (directly accessible)
        td_notam_ref = table_row.xpath('./td[@class="right"]')[0]
        notam_ref = td_notam_ref.text_content()

        # The full Q line (directly accessible)
        div_q = table_row.xpath('./td[@class="middle"]/div')[0]
        q_line = div_q.text_content()
        #print(q_line)

        # The ABC "fields"
        div_abc = table_row.xpath('./td[@class="middle"]/div[2]')[0]
        abc_line = div_abc.text_content()
        #print(abc_line)

        # The E block (directly accessible)
        pre_e = table_row.xpath('./td[@class="middle"]/pre')[0]
        e_line = pre_e.text_content()
        #print(e_line)

        return {
            'notam_ref': notam_ref,
            'q_line': q_line,
            'abc_line': abc_line,
            'e_line': e_line
            }


    def _parse_row_odd_table_notam(self, table_row):
        # The NOTAM ref (directly accessible)
        td_notam_ref = table_row.xpath('./td[@class="right"]')[0]
        notam_ref = td_notam_ref.text_content()

        # The full Q line (directly accessible)
        div_q = table_row.xpath('./td[@class="middle"]/div')[0]
        q_line = div_q.text_content()
        #print(q_line)

        # The ABC "fields"
        div_abc = table_row.xpath('./td[@class="middle"]/div[2]')[0]
        abc_line = div_abc.text_content()
        #print(abc_line)

        # The E block (directly accessible)
        pre_e = table_row.xpath('./td[@class="middle"]/pre')[0]
        e_line = pre_e.text_content()

        # The "Lower" limit
        div_lower = table_row.xpath('./td[@class="middle"]/div[3]')[0]
        lower_line = div_lower.text_content()

        # The "Upper" limit
        div_upper = table_row.xpath('./td[@class="middle"]/div[4]')[0]
        upper_line = div_upper.text_content()

        # The "Schedule" can be optional
        try:
            div_schedule = table_row.xpath('./td[@class="middle"]/div[5]')[0]
            schedule_line = div_schedule.text_content()
        except Exception:
            schedule_line = ''

        return {
            'notam_ref': notam_ref,
            'q_line': q_line,
            'abc_line': abc_line,
            'e_line': e_line,
            'lower_line': lower_line,
            'upper_line': upper_line,
            'schedule_line': schedule_line
            }