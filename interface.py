import sys
import os
import re
from PyQt5.uic import loadUi
from PyQt5 import QtWidgets
from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QDialog, QApplication
from PyQt5.QtGui import QFont, QSyntaxHighlighter, QTextCharFormat

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

class Highlighter(QSyntaxHighlighter):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._mapping = {}
    
    def add_mapping(self, pattern, pattern_format):
        self._mapping[pattern] = pattern_format

    # Reimplementing highlightBlock() with own rules
    def highlightBlock(self, text_block):
        for pattern, fmt in self._mapping.items():
            for match in re.finditer(pattern, text_block):
                start, end = match.span()
                self.setFormat(start, end-start, fmt)

class QueryScreen(QDialog):
    def __init__(self):
        super(QueryScreen, self).__init__()
        loadUi(os.path.join(os.path.dirname(__file__), 'QueryScreen.ui'), self)
        self.submitButton.clicked.connect(self.clickSubmit)
        self.backButton.clicked.connect(self.goToWelcomeScreen)

        self.highlighter = Highlighter()
        self.highlighter.setDocument(self.queryInput.document())
        self.setUpEditor()

    def setUpEditor(self):
        # Formatting of keywords
        keyword_format = QTextCharFormat()
        keyword_format.setForeground(Qt.darkMagenta)
        keyword_format.setFontWeight(QFont.Bold)
        pattern = r'\bselect\b|\bfrom\b|\bwhere\b|\bgroup by\b|\bhaving\b'
        self.highlighter.add_mapping(pattern, keyword_format)

        and_format = QTextCharFormat()
        and_format.setForeground(Qt.blue)
        pattern = r'\band\b'
        self.highlighter.add_mapping(pattern, and_format)

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
        self.highlighter = Highlighter()

        loadUi(os.path.join(os.path.dirname(__file__), 'QEPScreen.ui'),self)

        # display the annotation
        self.displayAnnotation(self.query)
        self.backButton.clicked.connect(self.goToQueryScreen)
        self.highlighter.setDocument(self.queryText.document())
        self.setUpEditor()

    def setUpEditor(self):
        # Formatting of keywords
        keyword_format = QTextCharFormat()
        keyword_format.setForeground(Qt.darkMagenta)
        keyword_format.setFontWeight(QFont.Bold)
        pattern = r'\bselect\b|\bfrom\b|\bwhere\b|\bgroup by\b|\bhaving\b'
        self.highlighter.add_mapping(pattern, keyword_format)

        and_format = QTextCharFormat()
        and_format.setForeground(Qt.blue)
        pattern = r'\band\b'
        self.highlighter.add_mapping(pattern, and_format)

    def goToQueryScreen(self):
        widgetStack.removeWidget(widgetStack.currentWidget())

    def displayAnnotation(self, query: str):
        tempString = ""

        if self.isAnnotationValid(query):
            for value in self.tokenized_query:

                # Check if token needs to be highlighted
                if value[0] in self.annotated_dict.keys():
                    token_to_add = "<font style='background-color: #FFFF00'>" + value[1] + "</font>"
                else:
                    token_to_add = "<font>" + value[1] + "</font>"

                # Once a new keyword appears, print out previous tokens and start newline
                if value[1] == "where" or value[1] == "from" or value[1] == "(":
                    #self.queryText.appendPlainText(tempString)
                    self.queryText.appendHtml(tempString)
                    tempString = token_to_add + " "
                else:
                    tempString += token_to_add
                    tempString += " "
            
            # Print out last line of query
            self.queryText.appendHtml(tempString)
            # self.queryText.appendPlainText(tempString)

            # To-do: Add legend for annotations at side
            for value in self.annotated_dict.values():
                self.annotation.append(value + "\n")

        else:
            self.queryText.appendPlainText("The query is invalid, please try again")
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