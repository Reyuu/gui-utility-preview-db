# -*- coding: utf-8 -*-
import wx
import wx.xrc
import wx.grid
import wx.html
import wx.html2
import wx.xrc
import wx.adv
import sqlite3
import random
import jinja2
import os
import functools
import time

debug = True

###########################################################################
## Class MainFrame
###########################################################################

def create_html(*args, **kwargs):
    templateloader = jinja2.FileSystemLoader(searchpath="./")
    templateEnv = jinja2.Environment(loader=templateloader)
    TEMPLATE_FILE = "template.html"
    template = templateEnv.get_template(TEMPLATE_FILE)
    outputText = template.render(*args, **kwargs)
    if debug:
        with open("debug.html", "w") as f:
            f.write(outputText)
    return outputText

class SQLHelperClass():
    def __init__(self, connection=sqlite3.connect("dummy.db"), comment_table="comments"):
        self.connection = connection
        self.cursor = self.connection.cursor()
        self.comment_table = comment_table
        self.page_size = 50

        ## define SQL queries you'd need
        self.select_all = f"select * from {self.comment_table}"
        self.select_all_distinct = f"select DISTINCT id, subject, description from {self.comment_table}"
        self.select_distinct_matching_pattern = lambda pattern: f"""select DISTINCT id, subject, description from {self.comment_table} where (
                                                                                                subject like ("%{pattern}%") or
                                                                                                description like ("%{pattern}%") or
                                                                                                id like ("%{pattern}%") or
                                                                                                comment_html_body like ("%{pattern}%")
                                                                                                )"""

        self.select_distinct_matching_pattern_pagination = lambda pattern, page: f"""select DISTINCT id, subject, description from {self.comment_table} where (
                                                                                                subject like ("%{pattern}%") or
                                                                                                description like ("%{pattern}%") or
                                                                                                id like ("%{pattern}%") or
                                                                                                comment_html_body like ("%{pattern}%")
                                                                                                ) limit {self.page_size} offset {self.page_size*page}"""
        self.select_all_by_id = lambda pattern: f"select * from {self.comment_table} where id = \"{pattern}\" order by comment_created_at asc"
    
    def get_all(self):
        c = self.cursor.execute(self.select_all)
        return c.fetchall()

    def get_all_distinct(self):
        c = self.cursor.execute(self.select_all_distinct)
        return c.fetchall()

    def get_based_on_pattern(self, pattern):
        c = self.cursor.execute(self.select_distinct_matching_pattern(pattern))
        return c.fetchall()
    
    def get_based_on_pattern_by_page(self, pattern, page):
        c = self.cursor.execute(self.select_distinct_matching_pattern_pagination(pattern, page))
        return c.fetchall()
    
    def get_all_by_id_date_asc(self, pattern):
        query = self.select_all_by_id(pattern)
        #print(query)
        c = self.cursor.execute(query)
        return c.fetchall()

    def make_data_human_readable(self, data):
        comments = []
        labels = ["id", "subject", "description", "submitter", "submitter_email",
                  "assignee", "assignee_email", "collaborators", "group",
                  "comment_author_id", "comment_html_body", "comment_public",
                  "comment_created_at"]
        for comment in data:
            comments += [dict(zip(labels, comment))]
        return comments

class LoadingPanel ( wx.Panel ):

	def __init__( self, parent, id = wx.ID_ANY, pos = wx.DefaultPosition, size = wx.Size( 32,50 ), style = wx.TAB_TRAVERSAL, name = wx.EmptyString ):
		wx.Panel.__init__ ( self, parent, id = id, pos = pos, size = size, style = style, name = name )

		bSizer4 = wx.BoxSizer( wx.VERTICAL )

		self.m_animCtrl1 = wx.adv.AnimationCtrl( self, wx.ID_ANY, wx.adv.NullAnimation, wx.DefaultPosition, wx.DefaultSize, wx.adv.AC_DEFAULT_STYLE )
		self.m_animCtrl1.LoadFile( u"./loader.gif" )

		self.m_animCtrl1.Play()
		bSizer4.Add( self.m_animCtrl1, 0, wx.EXPAND, 5 )


		self.SetSizer( bSizer4 )
		self.Layout()

	def __del__( self ):
		pass

class MainFrame ( wx.Frame ):

    def __init__( self, parent, loading_panel=None ):
        ## Utilities
        self.sql = SQLHelperClass()
        self.vertical_size_grid = -1
        self.last_query = ""

        ## GUI init
        wx.Frame.__init__ ( self, parent, id = wx.ID_ANY, title = wx.EmptyString, pos = wx.DefaultPosition, size = wx.Size( 1200, 800 ), style = wx.DEFAULT_FRAME_STYLE|wx.TAB_TRAVERSAL )
        self.loading_panel = LoadingPanel(self, pos=(self.GetSizeTuple()[0]/2, self.GetSizeTuple()[1]/2-50) )

        #self.SetForegroundColour( wx.SystemSettings.GetColour( wx.SYS_COLOUR_WINDOW ) )
        self.SetBackgroundColour( wx.SystemSettings.GetColour( wx.SYS_COLOUR_WINDOW ) )

        self.SetSizeHints( wx.DefaultSize, wx.DefaultSize )

        flexbox_parent = wx.FlexGridSizer( 2, 2, 0, 0 )
        flexbox_parent.SetFlexibleDirection( wx.BOTH )
        flexbox_parent.SetNonFlexibleGrowMode( wx.FLEX_GROWMODE_ALL )

        verticalbox_child = wx.BoxSizer( wx.VERTICAL )

        self.m_searchCtrl1 = wx.SearchCtrl( self, wx.ID_ANY, u"", wx.DefaultPosition, wx.Size( 490,-1 ), style=wx.TE_PROCESS_ENTER)
        self.m_searchCtrl1.ShowSearchButton( True )
        self.m_searchCtrl1.ShowCancelButton( True )
        verticalbox_child.Add( self.m_searchCtrl1, 0, wx.ALL, 5 )

        self.m_grid1 = wx.grid.Grid( self, wx.ID_ANY, wx.DefaultPosition, wx.Size( 500,600 ), 0 )

        # Grid
        self.m_grid1.CreateGrid( 5, 5 )
        self.m_grid1.EnableEditing( False )
        self.m_grid1.EnableGridLines( True )
        self.m_grid1.EnableDragGridSize( True )
        self.m_grid1.SetMargins( 0, 0 )

        # Columns
        self.m_grid1.EnableDragColMove( False )
        self.m_grid1.EnableDragColSize( True )
        self.m_grid1.SetColLabelSize( 30 )
        self.m_grid1.SetColLabelAlignment( wx.ALIGN_CENTER, wx.ALIGN_CENTER )

        # Rows
        self.m_grid1.EnableDragRowSize( True )
        self.m_grid1.SetRowLabelSize( 80 )
        self.m_grid1.SetRowLabelAlignment( wx.ALIGN_CENTER, wx.ALIGN_CENTER )

        # Label Appearance

        # Cell Defaults
        self.m_grid1.SetDefaultCellAlignment( wx.ALIGN_LEFT, wx.ALIGN_TOP )
        verticalbox_child.Add( self.m_grid1, 1, wx.EXPAND, 5 )

        bSizer2 = wx.BoxSizer( wx.VERTICAL )

        self.m_staticText1 = wx.StaticText( self, wx.ID_ANY, u"Page", wx.DefaultPosition, wx.DefaultSize, 0 )
        self.m_staticText1.Wrap( -1 )

        bSizer2.Add( self.m_staticText1, 0, wx.ALL|wx.ALIGN_CENTER_HORIZONTAL, 5 )

        self.m_spinCtrl1 = wx.SpinCtrl( self, wx.ID_ANY, wx.EmptyString, wx.DefaultPosition, wx.DefaultSize, wx.SP_ARROW_KEYS, 0, 999, 0 )
        bSizer2.Add( self.m_spinCtrl1, 0, wx.ALIGN_CENTER_HORIZONTAL|wx.ALL, 5 )


        verticalbox_child.Add( bSizer2, 0, wx.ALIGN_BOTTOM|wx.EXPAND, 5 )


        flexbox_parent.Add( verticalbox_child, 1, wx.EXPAND, 5 )

        self.m_htmlWin1 = wx.html2.WebView.New( self, wx.ID_ANY, "about:", wx.DefaultPosition, wx.Size(2000, 2000), wx.html2.WebViewBackendDefault, wx.html.HW_SCROLLBAR_AUTO )
        flexbox_parent.Add( self.m_htmlWin1, 0, wx.EXPAND, 5 )
        self.SetSizer( flexbox_parent )
        self.Layout()

        self.Centre( wx.BOTH )

        # Connect Events
        self.m_searchCtrl1.Bind( wx.EVT_SEARCHCTRL_CANCEL_BTN, self.clear_search_bar )
        self.m_searchCtrl1.Bind( wx.EVT_SEARCHCTRL_SEARCH_BTN, self.get_search_results )
        self.m_searchCtrl1.Bind( wx.EVT_TEXT_ENTER, self.get_search_results )
        self.m_searchCtrl1.Bind( wx.EVT_CHAR, self.get_search_result_keyboard)
        self.m_grid1.Bind( wx.grid.EVT_GRID_CELL_LEFT_CLICK, self.left_click_on_cell_grid )
        self.m_spinCtrl1.Bind( wx.EVT_SPINCTRL, self.change_pagination )

        # reinit grid
        self.fill_grid([("database loaded, use the searchbar", "", "")])

    def __del__( self ):
        pass

    ## decorator
    def loading_decorator(func):
        def wrapper_decorator(self, *args, **kwargs):
            self.loading_panel.Show()
            self.loading_panel.m_animCtrl1.Play()
            self.loading_panel.Center()
            self.loading_panel.Layout()
            func(self, *args, **kwargs)
            self.loading_panel.m_animCtrl1.Stop()
            self.loading_panel.Hide()
            self.Layout()
        return wrapper_decorator

    @loading_decorator
    def fill_grid(self, grid_data):
        #self.loading_panel.Show()
        self.m_grid1.ClearGrid()
        try:
            self.m_grid1.DeleteCols(0, -1)
            self.m_grid1.DeleteRows(0, -1)
        except wx._core.wxAssertionError:
            pass
        self.vertical_size_grid = len(grid_data)
        self.m_grid1.AppendCols(3)
        self.m_grid1.AppendRows(self.vertical_size_grid)
        for i in range(self.vertical_size_grid):
            for j in range(3):
                self.m_grid1.SetCellValue(i, j, str(grid_data[i][j]))
        self.m_grid1.SetColLabelValue(0, "ID")
        self.m_grid1.SetColLabelValue(1, "Subject")
        self.m_grid1.SetColLabelValue(2, "Description")
        self.m_grid1.AutoSizeColumn(1)
        self.m_grid1.EnableDragColSize( True )
        #self.loading_panel.Hide()
        return True

    # Virtual event handlers, overide them in your derived class
    def change_pagination(self, event):
        val = self.m_searchCtrl1.GetValue()
        data = self.sql.get_based_on_pattern_by_page(val, self.m_spinCtrl1.GetValue())
        #print(val)
        self.fill_grid(data)
        event.Skip()

    @loading_decorator
    def left_click_on_cell_grid( self, event ):
        selected_row = event.GetRow()
        id = self.m_grid1.GetCellValue(selected_row, 0)
        data = self.sql.get_all_by_id_date_asc(id)
        human_readable_data = self.sql.make_data_human_readable(data)
        #self.m_htmlWin1.SetPage(str(human_readable_data), "")
        self.m_htmlWin1.SetPage(create_html(comments=human_readable_data), f"file:///{os.curdir}/")
        event.Skip()

    @loading_decorator
    def clear_search_bar( self, event ):
        time.sleep(5)
        event.Skip()

    def get_search_results( self, event ):
        self.m_spinCtrl1.SetValue(0)

        val = self.m_searchCtrl1.GetValue()
        data = self.sql.get_based_on_pattern_by_page(val, self.m_spinCtrl1.GetValue())
        #print(val)
        self.fill_grid(data)
        event.Skip()

    def get_search_result_keyboard(self, event):
        if event.GetKeyCode() == 13:
            self.get_search_results(event)
        event.Skip()

if __name__ == "__main__":
    app = wx.App()
    frame = MainFrame(None)
    frame.Show()
    app.MainLoop()