import sys
import os
import re
from PyQt5.uic import loadUi
from PyQt5 import QtWidgets
from PyQt5.QtCore import Qt, QEvent
from PyQt5.QtWidgets import QDialog, QApplication, QWidget
from PyQt5.QtGui import QFont, QSyntaxHighlighter, QTextCharFormat

from annotation import Annotator
from preprocessing import QueryProcessor

def get_annotated_query(query, processor, annotator):
    '''
    Gets annotations for the input query
    :param query: 
    SQL query to be analyzed
    :returns tup: 
    tuple[0] = dictionary where the keys represent a token's index, and the value represents the annotation for that token
    tuple[1]= list of tokens that the query has been split into
    '''
    try:
        query_plan = processor.process_query(query)
        tokenized_query = processor.tokenize_query(query)
        annotation_dict = annotator.annotate(query_plan, tokenized_query)
        return annotation_dict, tokenized_query
    except Exception as e:
        return e

class WelcomeScreen(QDialog):
    def __init__(self):
        super(WelcomeScreen, self).__init__()
        loadUi(os.path.join(os.path.dirname(__file__), 'WelcomeScreen.ui'), self)
        self.loadDatabaseButton.clicked.connect(self.validateLogin)
        self.quitButton.clicked.connect(self.quit)

    def validateLogin(self):
        self.username = self.username_input.toPlainText()
        self.password = self.password_input.toPlainText()
        self.host = self.host_input.toPlainText()
        self.database = self.database_input.toPlainText()

        try:   
            # Load QueryScreen if successful
            self.processor = QueryProcessor(self.username, self.password, self.host, self.database)
            self.annotator = Annotator()
            queryScreen = QueryScreen(self.processor, self.annotator)
            widgetStack.addWidget(queryScreen)
            widgetStack.setCurrentIndex(widgetStack.currentIndex()+1)
        except Exception as e:
            # Load ErrorScreen if unsuccessful
            error_screen = ErrorScreen()
            widgetStack.addWidget(error_screen)
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
            for match in re.finditer(pattern, text_block, re.IGNORECASE):
                start, end = match.span()
                self.setFormat(start, end-start, fmt)

class ErrorScreen(QDialog):
    ''' 
    The screen that shows the error window for invalid input in the welcome screen
    '''

    def __init__(self):
        super(ErrorScreen, self).__init__()
        loadUi(os.path.join(os.path.dirname(__file__), 'ErrorScreen.ui'), self)
        self.backButton.clicked.connect(self.goToWelcomeScreen)

    def goToWelcomeScreen(self):
        widgetStack.removeWidget(widgetStack.currentWidget())


class QueryScreen(QDialog):
    def __init__(self, processor: QueryProcessor, annotator: Annotator):
        super(QueryScreen, self).__init__()
        loadUi(os.path.join(os.path.dirname(__file__), 'QueryScreen.ui'), self)

        self.processor = processor
        self.annotator = annotator

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
        pattern = r'\bselect\b|\bfrom\b|\bwhere\b|\bgroup by\b|\border by\b|\bhaving\b|\bdistinct\b|\bin\b|\bbetween\b|\blike\b|\bas\b|\bin\b|\ball\b|\bsome\b|\bexists\b|\bunion\b|\bintersect\b|\bexcept\b|\binto\b|\bjoin\b|\binner\b|\bnatural\b|\bouter\b|\bleft\b|\bright\b|\bfull\b|\bcreate\b|\binsert\b|\bset\b|\bdelete\b|\bupdate\b|\bset\b'
        self.highlighter.add_mapping(pattern, keyword_format)

        and_format = QTextCharFormat()
        and_format.setForeground(Qt.blue)
        pattern = r'\band\b|\bor\b'
        self.highlighter.add_mapping(pattern, and_format)

        aggregate_format = QTextCharFormat()
        aggregate_format.setForeground(Qt.red)
        pattern = r'\bcount\b|\bavg\b|\bmax\b|\bmin\b|\bsum\b'
        self.highlighter.add_mapping(pattern, aggregate_format)

    def clickSubmit(self):
        self.text = self.queryInput.toPlainText()
        try:
            annotated_dict, tokenized_query = get_annotated_query(self.text, self.processor, self.annotator)
            if annotated_dict:
                self.errorMessage.setText("")
                self.goToQEPScreen(annotated_dict, list(enumerate(tokenized_query)))
            else:
                # Query has no annotations 
                self.errorMessage.setStyleSheet("color: #4BB543")
                self.errorMessage.setText("Query executed successfully, but has no annotations for viewing!")
        except Exception:
            # Query execution has error, display error message
            error_message = get_annotated_query(self.text, self.processor, self.annotator)
            self.errorMessage.setStyleSheet("color: #FF0000")
            self.errorMessage.setText(str(error_message))

    def goToWelcomeScreen(self):
        widgetStack.removeWidget(widgetStack.currentWidget())

    def goToQEPScreen(self, annotatedDict, tokenizedQuery):
        qepScreen = QEPScreen(annotatedDict, tokenizedQuery)
        widgetStack.addWidget(qepScreen)
        widgetStack.setCurrentIndex(widgetStack.currentIndex()+1)

class QEPScreen(QDialog):
    def __init__(self, annotated_dict: dict, tokenized_query: list):
        super(QEPScreen, self).__init__()

        # the query input from Query Screen
        self.annotated_dict = annotated_dict
        self.tokenized_query = tokenized_query
        self.highlighter = Highlighter()

        loadUi(os.path.join(os.path.dirname(__file__), 'QEPScreen.ui'),self)

        # display the annotation
        self.displayAnnotation()
        self.backButton.clicked.connect(self.goToQueryScreen)
        self.highlighter.setDocument(self.queryText.document())
        self.setUpEditor()

        # self.backButton_2.clicked.connect(self.clearStuff)
        # self.activeHighlight = 2

    def setUpEditor(self):
        # Formatting of keywords
        keyword_format = QTextCharFormat()
        keyword_format.setForeground(Qt.darkMagenta)
        keyword_format.setFontWeight(QFont.Bold)
        pattern = r'\bselect\b|\bfrom\b|\bwhere\b|\bgroup by\b|\border by\b|\bhaving\b|\bdistinct\b|\bin\b|\bbetween\b|\blike\b|\bas\b|\bin\b|\ball\b|\bsome\b|\bexists\b|\bunion\b|\bintersect\b|\bexcept\b|\binto\b|\bjoin\b|\binner\b|\bnatural\b|\bouter\b|\bleft\b|\bright\b|\bfull\b|\bcreate\b|\binsert\b|\bset\b|\bdelete\b|\bupdate\b|\bset\b'
        self.highlighter.add_mapping(pattern, keyword_format)

        and_format = QTextCharFormat()
        and_format.setForeground(Qt.blue)
        pattern = r'\band\b|\bor\b'
        self.highlighter.add_mapping(pattern, and_format)

        aggregate_format = QTextCharFormat()
        aggregate_format.setForeground(Qt.red)
        pattern = r'\bcount\b|\bavg\b|\bmax\b|\bmin\b|\bsum\b'
        self.highlighter.add_mapping(pattern, aggregate_format)

    def goToQueryScreen(self):
        widgetStack.removeWidget(widgetStack.currentWidget())

    def displayAnnotation(self):

        colorArray= ["#FFFF00", "#DE9EC1", "#ED6A13" ,"#59F0FF", "#12EC83", "#EDAF13", "#BD9FDF" , "#DE9EA3"]
        tempString = ""
        arrayIndex = 0
        colorAllocation = {}
        tokens_to_newline = ["select", "where", "from", "group", "order"]

        # Iterate through annotations and set the colors for each annotation before printing
        for key, value in self.annotated_dict.items():
            if (key != "cost"):
                value = value.replace("<", "&lt;") # "&lt;" needs to be used for printing "<" in HTML
                colorAllocation[key] = colorArray[arrayIndex]
                self.annotation.appendHtml("<font style='background-color: " + colorArray[arrayIndex] + "'>" + str(arrayIndex+1) + ")</font>" + "<font> " + value + "</font>")
                self.annotation.appendHtml("<font></font>")
                arrayIndex += 1
            else:
                self.annotation.appendHtml("<font>------------</font>")
                self.annotation.appendHtml("<font></font>")
                self.annotation.appendHtml("<font> " + value + "</font>")
 
        # Keeps track of how much indentation to add for a newline
        indent_amount = 0

        # Iterate through query tokens and highlight if necessary by checking colorAllocation
        for idx, value in enumerate(self.tokenized_query):
            
            # "&lt;" needs to be used for printing "<" in HTML
            if value[1] == "<":
                token_to_add = "<font style='background-color: " + highlight + "'>" +  "&lt;" + "</font>"
            else:
                # Check if token needs to be highlighted
                highlight = ""
                
                for key in colorAllocation.keys():
                    if isinstance(key, tuple):
                        if value[0] in key:
                            highlight = colorAllocation[key]
                            break
                    elif value[0] == key:
                        highlight = colorAllocation[key]
                        break

                if highlight != "":
                    token_to_add = "<font style='background-color: " + highlight + "'>" + value[1] + "</font>"
                else:
                    token_to_add = "<font>" + value[1] + "</font>"

            # Once a new keyword appears, print out previous tokens and start newline
            if value[1] in tokens_to_newline:
                self.queryText.appendHtml(tempString)
                tempString = "<font>" + indent_amount * "&nbsp;" + "</font>" + token_to_add + " "
            elif value[1] == "(":
                tempString += token_to_add + " "
                indent_amount += 4
            elif value[1] == ")":
                indent_amount -= 4
                if len(self.tokenized_query) == idx + 1: # Closing bracket is last token, append after newline
                    self.queryText.appendHtml(tempString)
                    tempString = "<font>" + indent_amount * "&nbsp;" + "</font>" + token_to_add + " "
                elif not self.tokenized_query[idx+1][1] == "from": # Closing bracket is from subplan, append after newline
                    self.queryText.appendHtml(tempString)
                    tempString = "<font>" + indent_amount * "&nbsp;" + "</font>" + token_to_add + " "
                else: # Closing bracket is from aggregate function, append without newline
                    tempString += token_to_add + " "
            else:
                tempString += token_to_add + " "
 
        # Print out last line of query
        self.queryText.appendHtml(tempString)

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