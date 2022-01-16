import sys

from PySide6 import QtWebChannel
from PySide6.QtCore import QUrl, QFile, QIODevice

from PySide6.QtWebEngineWidgets import QWebEngineView
from PySide6.QtWidgets import QMainWindow, QApplication, QMessageBox
from bs4 import BeautifulSoup
from icecream import ic
from string import Template

COUNT = 'count'

debug = True

MESSAGE_TYPES = {
    0: 'Debug',
    1: 'Warning',
    2: 'Critical',
    3: 'Fatal',
    4: 'Info'

}

QtCore.QMessageLogContext = 'QT_MESSAGELOGCONTEXT'

def my_handler(type, context, message):
    global debug

    if debug:
        shown_header = False
        for i, line in enumerate(message.split('\n')):
            empty =  len(line.strip()) == 0

            type_reported = f'{MESSAGE_TYPES[type]} from QT:'
            context_reported = f' [file: {context.file} line: {context.line} function: {context.function}, category {context.category}]'
            if context.file is None:
                context_reported =  ''
            if not shown_header:
                if not empty:
                    print(f'{type_reported} {line}{context_reported}')
                    shown_header = True
            else:
                print(' ' * (len(type_reported)-2), '|', line)

qInstallMessageHandler(my_handler)


values = {
    "first_name"                            :   'Gary',
    "last_name"                             :   'Thompson',
    "position"                              :   'Principal Investigator',
    "organization"                          :   'University of Kent',
    "department"                            :   '$school',
    "principal_investigator_first_name"     :   '$first_name',
    "principal_investigator_last_name"      :   '$last_name',
    "unit"                                  :   'Wellcome Trust Biomolecular NMR Facility',
    "school"                                :   'School of Biosciences',
    "faculty"                               :   'Natural Sciences',
    "city"                                  :   'Canterbury',
    "post_code"                             :   'CT2 7NZ',
    "country"                               :   'UK',
    "telephone"                             :   '01227 82 7117',
    "fax"                                   :   '$telephone',
    "email"                                 :   'g.s.thompson@kent.ac.uk'
}

cns_templates  = {
    "First_Name" 		: "$first_name",
    "Last_Name" 		: "$last_name",
    "Organization" 		: "$organization",
    "Department" 		: "$department",
    "PI_First_Name" 	: "$principal_investigator_first_name",
    "PI_Last_Name" 		: "$principal_investigator_last_name",
    "Position"          : '$position',
    "Address" 			: "$unit, $school, $faculty, $organization",
    "City" 				: "$city",
    "Post_Code" 		: "$post_code",
    "Country" 			: "$country",
    "Telephone_Number" 	: "$telephone",
    "Fax_Number" 		: "$fax",
    "Email"             : "$email"
}

buttons = {
    'OK_license' : True,
    'OK_Academic': True
}

selectors =  {
    'Position' : 'principal-investigator'
}

class CustomWebEnginePage(QWebEnginePage):


    def __init__(self, *args, internal_urls=(), **kwargs):

        super(CustomWebEnginePage, self).__init__(*args,**kwargs)
        self._internal_urls = internal_urls

    def acceptNavigationRequest(self, url,  _type, isMainFrame):

        try:
            if url in self._internal_urls:
                print('ok navigation', url, _type, isMainFrame)
                result = super().acceptNavigationRequest(url, _type, isMainFrame)
            else:
                print('bad navigation', url, _type, isMainFrame)
                result = False
                QDesktopServices.openUrl(QUrl("https://qt.io/"))

        except Exception as e:
            print(f'error, {e}')

        return result

class Window(QMainWindow):

    #defining constructor function
    def __init__(self):
        #creating connnection with parent class constructor
        super(Window,self).__init__()

        self._page_name = 'cns',
        self._page_url = 'http://cns-online.org/cns_request/'

        #---------------------adding browser-------------------
        self.browser = QWebEngineView()

        #setting url for browser, you can use any other url also
        self.browser.setPage(CustomWebEnginePage(self, internal_urls=[self._page_url, cns_submit_url]))
        self.browser.setUrl(QUrl(self._page_url))

        self.browser.loadFinished.connect(self.process_load_finished)
        self.browser.page().urlChanged.connect(self.page_navigated)


        #to display google search engine on our browser
        self.setCentralWidget(self.browser)

        #-------------------full screen mode------------------
        #to display browser in full screen mode, you may comment below line if you don't want to open your browser in full screen mode
        self.showMaximized()

        self._timer = None



    # #method to load the required url
    # def loadUrl(self):
    #     #fetching entered url from searchBar
    #     url = self.searchBar.text()
    #     #loading url
    #     self.browser.setUrl(QUrl(url))
    #
    # #method to update the url
    # def updateUrl(self, url):
    #     #changing the content(text) of searchBar
    #     self.searchBar.setText(url.toString())
    def page_navigated(self,url):
        print(url)

    def process_load_finished(self, ok):
        self.browser.page().toHtml(self.process_page)


    def get_fields(self, form):
        return  [input for input in form.find_all('input') if input['type'] =='text']

    def get_field_names(self, form):
        return  [input['name'] for input in form.find_all('input') if input['type'] =='text']

    def get_checkboxes(self, form):
        return [input for input in form.find_all('input') if input['type'] =='checkbox']

    def get_checkbox_names(self, form):
        return [input['name'] for input in form.find_all('input') if input['type'] =='checkbox']

    def get_selector_names(selfself,form):
        return [select['name'] for select in form.find_all('select')]

    def set_named_element_value(self, name, value, browser=None):
        browser = self.browser if browser is None else browser
        browser.page().runJavaScript(f'''
            var els=document.getElementsByName("{name}")
            for (var i=0;i<els.length;i++) {{
            els[i].value = "{value}";}}
        ''')

    def check_named_checkbox(self, name, checked, browser=None):
        browser = self.browser if browser is None else browser
        checked = 'true' if checked else 'false'
        print(browser.page().runJavaScript(f'''
             var els=document.getElementsByName("{name}")'''))

        browser.page().runJavaScript(f'''
            var els=document.getElementsByName("{name}")
            for (var i=0;i<els.length;i++) {{
            els[i].checked = "{checked}";}}
        ''')

    def substitute_strings(self, templates, values):
        result = {}
        for name, template in templates.items():
            result[name] = Template(template).safe_substitute(values)
        return result

    def substitute_placeholders(self, templates, values):

        values = self.substitute_strings(values,values)

        return self.substitute_strings(templates, values)

    def display_error_dialog(self, message, icon):
        msgBox = QMessageBox()
        msgBox.setText(message)
        msgBox.setTextFormat(Qt.RichText)
        msgBox.setIcon(icon)
        msgBox.exec()

    def process_page(self, text):


        processed_text = ' '.join(text.split('\n'))

        soup = BeautifulSoup(processed_text, 'html.parser')

        if 'CNS Request Form for Academic (Non-Profit) Institutions' in processed_text:
            self.setup_page(soup)
        elif cns_submit_success in processed_text:
            print('success')
        else:

            self.browser.setUrl(self._page_url)

            QTimer.singleShot(0, lambda: self.display_error_dialog(text, QMessageBox.Warning))



    def setup_page(self, soup):
        form = soup.find('form')
        fields = self.get_field_names(form)
        checkboxes = self.get_checkbox_names(form)
        selectors = self.get_selector_names(form)
        field_values = self.substitute_placeholders(cns_templates, values)
        for field in fields:
            value = field_values[field]
            self.set_named_element_value(field, value)
        for checkbox in checkboxes:
            self.check_named_checkbox(checkbox, True)
        for selector in selectors:
            selector_values = self.substitute_strings(cns_templates, values)
            value = selector_values[selector]
            self.set_named_element_value(selector, value)

def read_args():
    # noinspection PyTypeChecker
    parser = argparse.ArgumentParser(description='calculate hashes from web links.',
                                     formatter_class=argparse.RawTextHelpFormatter)
    parser.add_argument('-d', '--debug', dest='debug', default=0, action=COUNT,
                        help='debug output')
    return parser.parse_args()

if __name__ == '__main__':

    args = read_args()

    if not args.debug:
       debug = False

    MyApp = QApplication(sys.argv)

    #setting application name
    QApplication.setApplicationName('NMRPack Register')

    #creating window
    window = Window()

    #executing created app
    MyApp.exec_()
