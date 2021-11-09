import sys
import os
import re
import copy
from PyQt5.uic import loadUi
from PyQt5 import QtWidgets
from PyQt5.QtCore import Qt, QEvent, pyqtSignal, QPersistentModelIndex, QModelIndex
from PyQt5.QtWidgets import QDialog, QApplication, QHeaderView, QTableWidget, QTableWidgetItem, QAbstractItemView
from PyQt5.QtGui import QFont, QSyntaxHighlighter, QTextCharFormat, QBrush, QColor

from annotation import Annotator
from preprocessing import QueryProcessor

QApplication.setAttribute(Qt.AA_EnableHighDpiScaling) # DPI Support for high DPI screens
app = QApplication(sys.argv)
widgetStack = QtWidgets.QStackedWidget()
sample_queries = ["SELECT * \nFROM customer, nation, supplier \nWHERE nation.n_nationkey = 0",
"SELECT * \nFROM customer c, orders o \nWHERE c.c_custkey = o.o_custkey",
"SELECT AVG(c_acctbal) \nFROM customer \nWHERE c_custkey < 5",
"UPDATE customer \nSET c_name = 'tom' \nWHERE c_custkey = 1",
"SELECT c_nationkey, c_mktsegment, SUM(c_acctbal) \nFROM customer \nWHERE c_custkey < 10 \nGROUP BY c_nationkey, c_mktsegment",
"SELECT * \nFROM customer c, lineitem l1 \nWHERE c.c_custkey = ( \n    SELECT o_orderkey \n    FROM orders, lineitem l2 \n    WHERE o_custkey = 4 and l2.l_partkey = 5\n) and l1.l_suppkey = 7",
"SELECT * \nFROM customer c, lineitem l1 \nWHERE c.c_custkey = ( \n    SELECT o_orderkey \n    FROM orders \n    WHERE o_custkey = 4 and l1.l_partkey = 5 \n) and l1.l_suppkey = ( \n    SELECT ps_suppkey \n    FROM partsupp \n    WHERE ps_availqty = 4 \n)"]

class WelcomeScreen(QDialog):
    def __init__(self):
        super(WelcomeScreen, self).__init__()
        loadUi(os.path.join(os.path.dirname(__file__), 'WelcomeScreen.ui'), self)
        self.loadDatabaseButton.clicked.connect(self.validate_login)
        self.quitButton.clicked.connect(self.quit)

    def validate_login(self):
        self.username = self.username_input.toPlainText()
        self.password = self.password_input.text()
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
            error_screen = ErrorScreen(e)
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

    def __init__(self, error_message: str):
        super(ErrorScreen, self).__init__()
        loadUi(os.path.join(os.path.dirname(__file__), 'ErrorScreen.ui'), self)
        self.backButton.clicked.connect(self.goto_welcome_screen)
        self.errorMessage.setText(str(error_message))

    def goto_welcome_screen(self):
        widgetStack.removeWidget(widgetStack.currentWidget())


class QueryScreen(QDialog):
    def __init__(self, processor: QueryProcessor, annotator: Annotator):
        super(QueryScreen, self).__init__()
        loadUi(os.path.join(os.path.dirname(__file__), 'QueryScreen.ui'), self)

        self.processor = processor
        self.annotator = annotator

        self.submitButton.clicked.connect(self.click_submit)
        self.backButton.clicked.connect(self.goto_welcome_screen)

        self.highlighter = Highlighter()
        self.highlighter.setDocument(self.queryInput.document())
        self.set_up_editor()
        self.comboBox.currentIndexChanged.connect(self.on_currentIndexChanged)

    # On select of sample query, populate queryText with the query
    def on_currentIndexChanged(self, ix):
        combobox_index = self.comboBox.currentIndex()
        if not combobox_index == 0:
            self.queryInput.clear()
            self.queryInput.appendPlainText(sample_queries[combobox_index-1])

    def set_up_editor(self):
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

    def get_annotated_query(self, query, processor, annotator):
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

    def click_submit(self):
        self.text = self.queryInput.toPlainText()
        try:
            annotated_dict, tokenized_query = self.get_annotated_query(self.text, self.processor, self.annotator)
            if annotated_dict:
                self.errorMessage.setText("")
                self.goto_QEP_screen(annotated_dict, list(enumerate(tokenized_query)))
            else:
                # Query has no annotations 
                self.errorMessage.setStyleSheet("color: #4BB543")
                self.errorMessage.setText("Query executed successfully, but has no annotations for viewing!")
        except Exception as e:
            # Query execution has error, display error message
            error_message = self.get_annotated_query(self.text, self.processor, self.annotator)
            self.errorMessage.setStyleSheet("color: #FF0000")
            self.errorMessage.setText(str(error_message))

    def goto_welcome_screen(self):
        widgetStack.removeWidget(widgetStack.currentWidget())

    def goto_QEP_screen(self, annotatedDict, tokenizedQuery):
        qepScreen = QEPScreen(annotatedDict, tokenizedQuery)
        widgetStack.addWidget(qepScreen)
        widgetStack.setCurrentIndex(widgetStack.currentIndex()+1)

class TableWidget(QTableWidget):
    cellExited = pyqtSignal(int, int)
    itemExited = pyqtSignal(QTableWidgetItem)

    def __init__(self, rows, columns, parent=None):
        QTableWidget.__init__(self, rows, columns, parent)

        self._last_index = QPersistentModelIndex()
        self.viewport().installEventFilter(self)

        # Fixing height and width for table widget
        self.setFixedHeight(261)
        self.setFixedWidth(371)

        # Formatting of table widget items
        self.horizontalHeader().hide()
        self.verticalHeader().hide()
        self.verticalHeader().setMinimumSectionSize(1)
        self.verticalHeader().setDefaultSectionSize(55)
        self.verticalHeader().stretchLastSection()
        self.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)

        # Disable selection within table widget
        self.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.setFocusPolicy(Qt.NoFocus)
        self.setSelectionMode(QAbstractItemView.NoSelection)

    def eventFilter(self, widget, event):
        if widget is self.viewport():
            index = self._last_index
            if event.type() == QEvent.MouseMove:
                index = self.indexAt(event.pos())
            elif event.type() == QEvent.Leave:
                index = QModelIndex()
            if index != self._last_index:
                row = self._last_index.row()
                column = self._last_index.column()
                item = self.item(row, column)
                if item is not None:
                    self.itemExited.emit(item)
                self.cellExited.emit(row, column)
                self._last_index = QPersistentModelIndex(index)
        return QTableWidget.eventFilter(self, widget, event)

class QEPScreen(QDialog):

    def __init__(self, annotated_dict: dict, tokenized_query: list):
        super(QEPScreen, self).__init__()

        self.annotated_dict = annotated_dict
        self.tokenized_query = tokenized_query
        self.highlighter = Highlighter()
        self.color_allocation = {}
        self.current_color = {}
        loadUi(os.path.join(os.path.dirname(__file__), 'QEPScreen.ui'),self)

        # Initialise table, annotation and highlighter
        self.table = TableWidget(len(self.annotated_dict), 1, self)
        self.table.move(440,120)
        self.display_annotation()
        self.backButton.clicked.connect(self.goto_query_screen)
        self.highlighter.setDocument(self.queryText.document())
        self.set_up_editor()
        
    # When user hovers over an item in the table
    def handle_item_entered(self, item):
        index = item.row()
        tuple_list = list(self.color_allocation.items())
        if index < len(self.color_allocation):
            key_value = tuple_list[index]
            new = {}
            new[key_value[0]] = key_value[1]
            self.current_color = new.copy()
            self.display_query()

    # When user stops hovering over an item in the table
    def handle_item_exited(self, item):
        item.setBackground(QTableWidgetItem().background())
        self.current_color = copy.deepcopy(self.color_allocation)
        self.display_query()

    def set_up_editor(self):
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

    def goto_query_screen(self):
        widgetStack.removeWidget(widgetStack.currentWidget())

    def display_query(self):

        self.queryText.clear()
        indent_amount = 0
        tempString = ""
        tokens_to_newline = ["select", "where", "from", "group", "order", "set", "SELECT", "WHERE", "FROM", "GROUP", "ORDER", "SET"]
        
        # Iterate through query tokens and highlight if necessary by checking color_allocation
        for idx, value in enumerate(self.tokenized_query):
            
            # "&lt;" needs to be used for printing "<" in HTML
            if value[1] == "<":
                token_to_add = "<font>&lt;</font>"
            else:
                # Check if token needs to be highlighted
                highlight = ""
                
                for key in self.current_color.keys():
                    if isinstance(key, tuple):
                        if value[0] in key:
                            highlight = self.current_color[key]
                            break
                    elif value[0] == key:
                        highlight = self.current_color[key]
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
                elif self.tokenized_query[idx-2][1] == "(": # Closing bracket is from aggregate function, don't newline
                    tempString += token_to_add + " "
                else: # Closing bracket is from subplan, append after newline
                    self.queryText.appendHtml(tempString)
                    tempString = "<font>" + indent_amount * "&nbsp;" + "</font>" + token_to_add + " "
            else:
                tempString += token_to_add + " "
 
        # Print out last line of query
        self.queryText.appendHtml(tempString)

    def display_annotation(self):

        color_array= ["#62EC0A", "#BD9FDF", "#FFFF00", "#ED6A13" ,"#59F0FF", "#12EC83", "#EDAF13", "#EC0A2F", "#DE9EA3", "#423FDA", "#DE9EC1"]
        counter = 0
        array_index = 0

        # Iterate through annotations, set the colors for each annotation, and add to table
        for key, value in self.annotated_dict.items():

            if (key != "cost"):
                if ("alias" in value): # Also highlight actual name
                    self.color_allocation[(key - 1, key)] = color_array[array_index]
                elif ("aggregation" in value): # Highlight entire aggregation
                    self.color_allocation[(key, key+1, key+2, key+3)] = color_array[array_index]
                else: # Highlight token as per normal
                    self.color_allocation[key] = color_array[array_index]

                item = QTableWidgetItem("-> " + value)
                item.setForeground(QBrush(QColor(color_array[array_index])))
                self.table.setItem(counter, 0, item)
                array_index += 1
            else:
                item = QTableWidgetItem(value)
                item.setForeground(QBrush(QColor("#FFFFFF")))
                self.table.setItem(counter, 0, item)

            counter += 1

        # Set up mouse tracking and onHover functions
        self.current_color = copy.deepcopy(self.color_allocation)
        self.table.setMouseTracking(True)
        self.table.itemEntered.connect(self.handle_item_entered)
        self.table.itemExited.connect(self.handle_item_exited)
        self.display_query()

class GUI():
    
    #Initialise with WelcomeScreen and set width/height
    welcome = WelcomeScreen()
    widgetStack.setWindowTitle("SQL Query Annotator")
    widgetStack.addWidget(welcome)
    widgetStack.setFixedHeight(550)
    widgetStack.setFixedWidth(850)
    widgetStack.show()

    try:
        sys.exit(app.exec_())
    except:
        print("Exiting")