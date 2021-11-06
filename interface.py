import sys
import os
from PyQt5.uic import loadUi
from PyQt5 import QtWidgets
from PyQt5.QtWidgets import QDialog, QApplication,QTextEdit

# Temp sample data
tempAnnotatedDict = {4: 'The table "customer" (alias "c") is read using an Index Scan. The index condition is "c_custkey = $1".', 7: 'The table "lineitem" (alias "l1") is read using an Index Scan. The index condition is "l_suppkey = 7".', 2: 'This join is carried out with a Nested Loop Join.', 15: 'The table "orders" is read using a Sequential Scan. The filter "o_custkey = 4" is applied.', 18: 'The table "lineitem" (alias "l2") is read using an Index Only Scan. The index condition is "l_partkey = 5".', 14: 'This join is carried out with a Nested Loop Join.', (11, 27): 'Results of this group are stored in "$1"'}
tempTokenizedQuery = [(0, 'select'), (1, '*'), (2, 'from'), (3, 'customer'), (4, 'c'), (5, ','), (6, 'lineitem'), (7, 'l1'), (8, 'where'), (9, 'c.c_custkey'), (10, '='), (11, '('), (12, 'select'), (13, 'o_orderkey'), (14, 'from'), (15, 'orders'), (16, ','), (17, 'lineitem'), (18, 'l2'), (19, 'where'), (20, 'o_custkey'), (21, '='), (22, '4'), (23, 'and'), (24, 'l2.l_partkey'), (25, '='), (26, '5'), (27, ')'), (28, 'and'), (29, 'l1.l_suppkey'), (30, '='), (31, '7')]

class WelcomeScreen(QDialog):
    def __init__(self):
        super(WelcomeScreen, self).__init__()
        loadUi(os.path.join(os.path.dirname(__file__), 'WelcomeScreen.ui'), self)
        self.loadDatabaseButton.clicked.connect(self.goToQueryScreen)
        self.quitButton.clicked.connect(self.quit)


    def goToQueryScreen(self):
        self.username = self.username_input.toPlainText()
        self.password = self.password_input.toPlainText()
        self.host = self.host_input.toPlainText()
        self.database = self.database_input.toPlainText()

        # for testing
        print("hello")
        print(self.username)
        print(self.password)
        print(self.host)
        print(self.database)
        
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
        qepScreen = QEPScreen(self.text, tempAnnotatedDict, tempTokenizedQuery) # To change to real data
        widgetStack.addWidget(qepScreen)
        widgetStack.setCurrentIndex(widgetStack.currentIndex()+1)

class QEPScreen(QDialog):
    def __init__(self, query: str, annotated_dict: dict, tokenized_query: list):
        super(QEPScreen, self).__init__()

        # the query input from Query Screen
        self.query = query
        self.annotated_dict = annotated_dict
        self.tokenized_query = tokenized_query

        loadUi(os.path.join(os.path.dirname(__file__), 'QEPScreen.ui'),self)

        # display the annotation
        self.displayAnnotation(self.query)
        self.backButton.clicked.connect(self.goToQueryScreen)

    def goToQueryScreen(self):
        widgetStack.removeWidget(widgetStack.currentWidget())

    def displayAnnotation(self, query: str):
        """ display the annotation to the query """

        tempString = ""

        if self.isAnnotationValid(query):
            for value in self.tokenized_query:
                if value[1] == "where" or value[1] == "from" or value[1] == "(":
                    self.queryText.append(tempString)
                    tempString = value[1] + " "
                else:
                    tempString += value[1]
                    tempString += " "
            self.queryText.append(tempString)

            for value in self.annotated_dict.values():
                self.annotation.append(value + "\n")

        else:
            self.queryText.append("The query is invalid, please try again")
            self.annotation.append("The query is invalid, please try again")

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