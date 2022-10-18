import sys
#importing Widgets
from PyQt5.QtWidgets import *
#importing Engine Widgets
from PyQt5.QtWebEngineWidgets import *
#importing QtCore to use Qurl
from PyQt5.QtCore import *

PLACEHOLDER_TEXT_SEARCH_TEXT="Type here your questions to Zoltar!"

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
        url = QUrl.fromLocalFile("/home/pierrem/Documents/github_meta/personal-timeline/src/gui/main.html")
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
    def home(self):
        self.searchBar.setPlaceholderText(PLACEHOLDER_TEXT_SEARCH_TEXT)
        self.searchBar.setText("")
        url = QUrl.fromLocalFile("/home/pierrem/Documents/github_meta/personal-timeline/src/gui/main.html")
        self.browser.setUrl(url)

    #method to load the required url
    def loadUrl(self):
        #fetching entered url from searchBar
        url = self.searchBar.text()
        print(f"The user questions is: {url}")
        #TODO (process and prepare HTML page to visualize)
        # - url contains the question from the user
        # - update the page X.html and display it
        url = QUrl.fromLocalFile("/home/pierrem/Documents/github_meta/personal-timeline/src/gui/index.html")
        self.browser.setUrl(QUrl(url))


MyApp = QApplication(sys.argv)
#setting application name
QApplication.setApplicationName('Personal data explorer')
#creating window
window = Window()
#executing created app
MyApp.exec_()
