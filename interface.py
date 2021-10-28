import sys
import os
from PyQt5.uic import loadUi
from PyQt5 import QtWidgets
from PyQt5.QtWidgets import QDialog, QApplication,QTextEdit


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
        self.submitButton.clicked.connect(self.clickSubmit)
        self.backButton.clicked.connect(self.goToWelcomeScreen)

    def clickSubmit(self):
        # pass the text
        self.text = self.queryInput.toPlainText()

        # go to next screen
        self.goToQEPScreen()

    def goToWelcomeScreen(self):
        widgetStack.removeWidget(widgetStack.currentWidget())

    def goToQEPScreen(self):
        qepScreen = QEPScreen(self.text)
        widgetStack.addWidget(qepScreen)
        widgetStack.setCurrentIndex(widgetStack.currentIndex()+1)

class QEPScreen(QDialog):
    def __init__(self, query: str):
        super(QEPScreen, self).__init__()

        # the query input from Query Screen
        self.query = query

        loadUi(os.path.join(os.path.dirname(__file__), 'QEPScreen.ui'),self)

        # display the annotation
        self.displayAnnotation(self.query)
        self.backButton.clicked.connect(self.goToQueryScreen)

    def goToQueryScreen(self):
        widgetStack.removeWidget(widgetStack.currentWidget())

    def displayAnnotation(self, query: str):
        """ display the annotation to the query """

        if self.isAnnotationValid(query):
            self.titleText.setText(query)
        else:
            self.titleText.setText("The query is invalid, please try again")

    def isAnnotationValid(self, query: str) -> bool:
        """decide whether a query is valid or not"""

        # for now the placeholder value is true
        return True


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