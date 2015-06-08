# -*- coding: utf-8 -*-
"""
Created on Thu May 14 16:26:29 2015

@author: Ian Spielman
"""
 
#-------------------------------------------------------------------------
# qsci_simple_pythoneditor.pyw
#
# QScintilla sample with PyQt
#
# Eli Bendersky (eliben@gmail.com)
# This code is in the public domain
#-------------------------------------------------------------------------
import sys
import os 

from PyQt4 import QtCore, QtGui
from PyQt4.QtCore import pyqtSignal


from PyQt4.Qsci import QsciScintilla, QsciLexerPython
from qtutils import UiLoader

class SimplePythonEditor(QtGui.QWidget):

    # New signals
    filenameTrigger = pyqtSignal(str)

    def __init__(self, parent=None):
        super(SimplePythonEditor, self).__init__()

        loader = UiLoader()
        loader.registerCustomWidget(SimplePythonEditorTextField)
        self._ui = loader.load('simplepythoneditor.ui', self)
                
        # Connections
        self._ui.save_toolButton.clicked.connect(self.on_save)
        self._ui.sendFilename_toolButton.clicked.connect(self.on_filenameTrigger)
        self._ui.editor_tabWidget.tabCloseRequested.connect(self.closeTab)

    #        
    # Functionality special to this object
    #

    @property
    def _currentEditor(self):
        return self._ui.editor_tabWidget.currentWidget()

    @property 
    def _currentIndex(self):
        return self._ui.editor_tabWidget.currentIndex()
        
    def createTab(self, tabText=''):
        """
        Creates a new tab with an editor in it
        """
        editor = SimplePythonEditorTextField(self._ui.editor_tabWidget)
        index = self._ui.editor_tabWidget.addTab(editor, tabText)
        self._ui.editor_tabWidget.setCurrentIndex(index)
    
    def closeTab(self, index):
        """
        closedown the current tab
        """
        widget = self._ui.editor_tabWidget.widget(index)

        # see if this widget is changed and wants to close:
        if widget._changed:
            # see if user wants to save changed file
            msgBox = QtGui.QMessageBox(self)
            
            msgBox.setText("The document has been modified.")
            msgBox.setInformativeText("Do you want to save your changes?")
            msgBox.setStandardButtons(QtGui.QMessageBox.Save | QtGui.QMessageBox.Discard | QtGui.QMessageBox.Cancel)
            msgBox.setDefaultButton(QtGui.QMessageBox.Save)
            reply = msgBox.exec_()
                
            if reply == QtGui.QMessageBox.Cancel:
                return
            
            if reply == QtGui.QMessageBox.Save:
                widget.on_save(True)



        self._ui.editor_tabWidget.removeTab(index)
        
        # Inform child to shutdown need to be widget at index
        if widget:
            widget.close()
            widget.deleteLater()
    
    # TODO need close tab functionality
    
    
    #
    # Functionality passed on from editor children
    #

    def on_filenameTrigger(self, checked=True):
        """
        When this is called emit a signal containg the current filename
        """
        if self._currentEditor:
            self.filenameTrigger.emit(self._currentEditor.filename)

    def setText(self, text, *args, **kwargs):   
        """
        sets the text contents of a new tab
        """
        self.createTab()
        self._currentEditor.filename = ''
        self._currentEditor.setText(text, *args, **kwargs)

    def text(self):
        """
        Returns text contents of current tab
        """
        if self._currentEditor:
            return self._currentEditor.text()

    def on_open(self, checked=True):
        self.createTab()
        self._currentEditor.on_open(checked)

    def on_save(self, checked=True):
        if self._currentEditor:
            self._currentEditor.on_save(checked)
        
    def on_save_as(self, checked=True):
        if self._currentEditor:
            self._currentEditor.on_save_as(checked)


            


class SimplePythonEditorTextField(QsciScintilla):

    ARROW_MARKER_NUM = 8

    def __init__(self, parent=None):
        super(SimplePythonEditorTextField, self).__init__(parent)

        # defaults
        self._filename = ''
        self._name = ''
        self._folder = ''
        self._changed = False
        self._parent = parent

        # Connect some actions
        self.textChanged.connect(self.on_textChanged)

        # disk file monitor
        self.fileWatcher = QtCore.QFileSystemWatcher()
        self.fileWatcher.fileChanged.connect(self.on_fileChanged)

        #
        # Setup the editor 
        #

        # Set the default font
        font = QtGui.QFont()
        font.setFamily('Courier')
        font.setFixedPitch(True)
        font.setPointSize(9.5)
        self.setFont(font)
        self.setMarginsFont(font)

        # Margin 0 is used for line numbers
        fontmetrics = QtGui.QFontMetrics(font)
        self.setMarginsFont(font)
        self.setMarginWidth(0, fontmetrics.width("0000") + 6)
        self.setMarginLineNumbers(0, True)
        self.setMarginsBackgroundColor(QtGui.QColor("#cccccc"))

        # Brace matching: enable for a brace immediately before or after
        # the current position
        #
        self.setBraceMatching(QsciScintilla.SloppyBraceMatch)

        # Current line visible with special background color
        self.setCaretLineVisible(True)
        self.setCaretLineBackgroundColor(QtGui.QColor("#ffe4e4"))

        # Unix end of line chars
        self.setEolMode(self.EolUnix)
        
        # Set Python lexer
        # Set style for Python comments (style number 1) to a fixed-width
        # courier.
        #
        lexer = QsciLexerPython()
        lexer.setDefaultFont(font)
        lexer.setFoldCompact(False) # so folding ends at the end of functions
                                    # not at the start of the next object
        self.setLexer(lexer)
        self.SendScintilla(QsciScintilla.SCI_STYLESETFONT, 1, 'Courier')

        # Set python tabs
        self.setTabIndents(True)
        self.setTabWidth(4)
        self.setIndentationsUseTabs(False)

        #AutoIndentation
        self.setAutoIndent(True)
        self.setIndentationGuides(True)
        self.setIndentationWidth(4)

        # Code folding
        self.setMarginWidth(1, 14)
        self.setFolding(QsciScintilla.BoxedTreeFoldStyle)

        # Edge Mode shows a red vetical bar at 80 chars
        self.setEdgeMode(QsciScintilla.EdgeLine)
        self.setEdgeColumn(80)
        # self.setEdgeColor(QtGui.QColor("#FF0000"))

        # Don't want to see the horizontal scrollbar at all
        # Use raw message to Scintilla here (all messages are documented
        # here: http://www.scintilla.org/ScintillaDoc.html)
        self.SendScintilla(QsciScintilla.SCI_SETHSCROLLBAR, 1)

        # not too small
        self.setMinimumSize(fontmetrics.averageCharWidth()*92, 450)

    #
    # Helpers
    #

    #
    # Control enclosing tab widget to set the labels indicating file changed
    #

    def getIndex(self):
        return self._parent.indexOf(self)
        
    def setParentTitle(self, text):
        self._parent.setTabText(self.getIndex(), text)

    #
    # setup monitor for file name changed, and block direct changes to 
    # self.filename 
    #

    @property
    def filename(self):
        return self._filename
    
    @filename.setter
    def filename(self, newname):
        self._filename = newname
        
        # empty watcher (it should contain only the current file)
        # and fill with current file
        files = self.fileWatcher.files()
        if len(files) > 0:
            self.fileWatcher.removePaths(self.fileWatcher.files())
            
        directories = self.fileWatcher.directories()
        if len(directories) > 0:
            self.fileWatcher.removePaths(self.fileWatcher.directories())
            
        self.fileWatcher.addPath(newname)

    def on_fileChanged(self, filename):
        """
        reload when disk file is changed
        """
        self.openFile(filename)

    # 
    # Define behavior
    #
    
    def on_textChanged(self, changed=True):
 
        status_changed = changed != self._changed

        if status_changed:

            self._changed = changed
            if changed:
                self._name = os.path.basename(self.filename) + '*'
            else:
                self._name = os.path.basename(self.filename)
            
            self.setParentTitle(self._name)
            
    def setText(self, text, *args, **kwargs):
        super(SimplePythonEditorTextField, self).setText(text, *args, **kwargs)
        
        # Convert EOL chars        
        self.convertEols(self.eolMode())        
        self._changed = True
        self.on_textChanged(False)

    def openFile(self, filename):
        try:
            with open(filename, 'r') as f:
                text = f.read()
        except:
            pass
        else:
            self.filename = filename
            self._folder = os.path.dirname(filename)
            self.setText(text)
            
    def saveFile(self, filename):

        # Write file
        with open(filename, 'w') as f:
            f.write(self.text())

        self._folder = os.path.dirname(filename)
        self.filename = filename
        self.on_textChanged(False)


    def on_save(self, checked=True):
        
        # Ignore if no file selected
        if not self.filename:
            return

        # save file
        self.saveFile(self.filename)

    def on_save_as(self, checked=True):
        filename = QtGui.QFileDialog.getSaveFileName(self,
                                                     'Select python file',
                                                     self._folder,
                                                     "Python files (*.py)")
        if not filename:
            # User cancelled selection
            return
            
        # Convert to standard platform specific path, otherwise Qt likes forward slashes:
        current_filename = os.path.abspath(filename)

        # save current file
        self.saveFile(current_filename)

    def on_open(self, checked=True):
        filename = QtGui.QFileDialog.getOpenFileName(self,
                                                     'Select python file',
                                                     self._folder,
                                                     "Python files (*.py)")
        if not filename:
            # User cancelled selection
            return
            
        # Convert to standard platform specific path, otherwise Qt likes forward slashes:
        current_filename = os.path.abspath(filename)

        # save current file
        self.openFile(current_filename)
