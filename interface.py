import sys
import os
from PyQt5.uic import loadUi
from PyQt5 import QtWidgets
from PyQt5.QtWidgets import QDialog, QApplication


class WelcomeScreen(QDialog):
    def __init__(self):
        super(WelcomeScreen, self).__init__()
        loadUi(os.path.join(os.path.dirname(__file__), 'WelcomeScreen.ui'), self)
        self.loadDatabaseButton.clicked.connect(self.goToQueryScreen)
        self.quitButton.clicked.connect(self.quit)

    def goToQueryScreen(self):
        queryScreen = QueryScreen()
        widgetStack.addWidget(queryScreen)
        widgetStack.setCurrentIndex(widgetStack.currentIndex()+1)

    def quit(self):
        app.quit()

class QueryScreen(QDialog):
    def __init__(self):
        super(QueryScreen, self).__init__()
        loadUi(os.path.join(os.path.dirname(__file__), 'QueryScreen.ui'), self)
        self.submitButton.clicked.connect(self.goToQEPScreen)
        self.backButton.clicked.connect(self.goToWelcomeScreen)

    def goToWelcomeScreen(self):
        widgetStack.removeWidget(widgetStack.currentWidget())

    def goToQEPScreen(self):
        qepScreen = QEPScreen()
        widgetStack.addWidget(qepScreen)
        widgetStack.setCurrentIndex(widgetStack.currentIndex()+1)

class QEPScreen(QDialog):
    def __init__(self):
        super(QEPScreen, self).__init__()
        loadUi(os.path.join(os.path.dirname(__file__), 'QEPScreen.ui'),self)
        self.backButton.clicked.connect(self.goToQueryScreen)

    def goToQueryScreen(self):
        widgetStack.removeWidget(widgetStack.currentWidget())

if __name__ == "__main__":
    app = QApplication(sys.argv)
    welcome = WelcomeScreen()
    widgetStack = QtWidgets.QStackedWidget()
    widgetStack.addWidget(welcome)
    widgetStack.setFixedHeight(454)
    widgetStack.setFixedWidth(758)
    widgetStack.show()
    try:
        sys.exit(app.exec_())
    except:
        print("Exiting")