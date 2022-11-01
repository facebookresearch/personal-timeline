import sys
import json
#importing Widgets
from PyQt5.QtWidgets import *
#importing Engine Widgets
from PyQt5.QtWebEngineWidgets import *
#importing QtCore to use Qurl
from PyQt5.QtCore import *
from src.objects.LLEntry_obj import LLEntrySummary
from src.qa import QAEngine

from src.visualization import TimelineRenderer
from typing import List


PLACEHOLDER_TEXT_SEARCH_TEXT="Type here questions to your personal timeline!"

#main window class (to create a window)-sub class of QMainWindow class
class Window(QMainWindow):
    #defining constructor function
    def __init__(self):
        #creating connection with parent class constructor
        super(Window,self).__init__()
        #---------------------adding browser-------------------
        self.browser = QWebEngineView()
        #setting url for browser, you can use any other url also
        #By default loading a page locally on the machine
        self.main_path = QFileInfo("src/gui/main.html").absoluteFilePath()

        url = QUrl.fromLocalFile(self.main_path)
        self.browser.setUrl(url)
        self.setCentralWidget(self.browser)
        #-------------------full screen mode------------------
        #to display browser in full screen mode, you may comment below line if you don't want to open your browser in full screen mode
        self.showMaximized()
        #----------------------navbar-------------------------
        #creating a navigation bar for the browser
        navbar = QToolBar()
        #adding created navbar
        self.addToolBar(navbar)
        #-----------refresh Button--------------------
        refreshBtn = QAction('Refresh',self)
        refreshBtn.triggered.connect(self.browser.reload)
        navbar.addAction(refreshBtn)
        #-----------home button----------------------
        homeBtn = QAction('Home',self)
        #when triggered call home method
        homeBtn.triggered.connect(self.home)
        navbar.addAction(homeBtn)
        #---------------------search bar---------------------------------
        #to maintain a single line
        self.searchBar = QLineEdit()
        self.searchBar.setPlaceholderText(PLACEHOLDER_TEXT_SEARCH_TEXT)
        #when someone presses return(enter) call loadUrl method
        self.searchBar.returnPressed.connect(self.loadUrl)
        #adding created search bar to navbar
        navbar.addWidget(self.searchBar)

        # timeline render
        self.renderer = TimelineRenderer()

        # QA engine
        self.qa_engine = QAEngine()

    def home(self):
        self.searchBar.setPlaceholderText(PLACEHOLDER_TEXT_SEARCH_TEXT)
        self.searchBar.setText("")
        url = QUrl.fromLocalFile(self.main_path)
        self.browser.setUrl(url)

    #method to load the required url
    def loadUrl(self):
        #fetching entered url from searchBar
        url = self.searchBar.text()
        print(f"The user questions is: {url}")
        # - url contains the question from the user
        # - update the page X.html and display it

        query_results: List[LLEntrySummary] = self.qa_engine.query(url, k=9)

        # create result page
        cards = self.renderer.create_cards(query_results)
        template = open('search_result.html.template').read()
        template = template.replace("<!-- card template -->", " ".join(cards))
        fout = open('search_result.html', 'w')
        fout.write(template)
        fout.close()

        # create page for each result
        for summary in query_results:
            json_obj = self.renderer.create_timeline(query_time_range=(summary.startTime, summary.endTime), 
                                                     add_LLEntries=True)
            template = open('index.html.template').read()
            template = template.replace('"timeline object template"', json.dumps(json_obj))
            fn = f'summary_{self.renderer.get_uid(summary)}.html'
            fout = open(fn, 'w')
            fout.write(template)
            fout.close()

        index_path = QFileInfo("search_result.html").absoluteFilePath()
        url = QUrl.fromLocalFile(index_path)
        self.browser.setUrl(QUrl(url))


if __name__ == '__main__':
    MyApp = QApplication(sys.argv)
    #setting application name
    QApplication.setApplicationName('Personal data explorer')
    #creating window
    window = Window()
    #executing created app
    MyApp.exec_()
