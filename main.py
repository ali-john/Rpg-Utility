"""RPG GUI Main frame"""

# ----- IMPORTS ---------------------------------------------------------------
import json
import wx 

from gui_rpg.jobs import Jobs
from gui_rpg.server import Server
from gui_rpg.configuration import Configuration

# ----- CONSTANTS ---------------------------------------------------------------

config_file = open("config.json")
CONFIG = json.load(config_file)
config_file.close()


# ----- CLASSES ---------------------------------------------------------------

class MainFrame(wx.Frame):
    """
    The class for main window of GUI
    """
    def __init__(self):
        super().__init__(parent=None,id=1,title = "RPG Utility",size=(700,700))
        self.init_gui()
        self.bind_events()
        
    def init_gui(self):
        """
        Initializes the GUI layout.
        """
        self.panel = wx.Panel(self)
        self.job_button = wx.Button(parent=self.panel,label = "Jobs")
        self.server_button = wx.Button(parent=self.panel,label="Server")
        self.utilities_button = wx.Button(parent=self.panel,label="Utilities")

        self.button_sizer = wx.BoxSizer(wx.HORIZONTAL)
        self.button_sizer.Add(self.job_button, proportion=0, flag=wx.ALL, border=10)
        self.button_sizer.Add(self.server_button, proportion=0, flag=wx.ALL , border=10)
        self.button_sizer.Add(self.utilities_button, proportion=0, flag=wx.ALL, border=10)

        main_sizer = wx.BoxSizer(wx.VERTICAL)
        main_sizer.AddStretchSpacer() 
        main_sizer.Add(self.button_sizer, proportion=0, flag=wx.ALIGN_CENTER, border=5)
        main_sizer.AddStretchSpacer()

        self.panel.SetSizer(main_sizer)
        self.SetBackgroundColour(wx.Colour(CONFIG["COLORS"]["BACKGROUND_COLOR"]))
        self.Center()
        self.Show()
    
    def bind_events(self) -> None:
        """
        Bind each item to an event.
        """
        self.job_button.Bind(wx.EVT_BUTTON, self.on_job_button_click)
        self.server_button.Bind(wx.EVT_BUTTON, self.on_server_button_click)
        self.utilities_button.Bind(wx.EVT_BUTTON,self.on_configuration_button_click)
    
    def on_job_button_click(self,event):
        """
        Display Jobs page. 
        """
        jobs_page = Jobs(parent=self,id=2,title="Jobs Utility",size=(700,700) )
        self.Hide()
        jobs_page.Show()
    
    def on_server_button_click(self,event):
        """
        Display Server page. 
        """
        server_page = Server(parent=self,id=3,title="Servers Utility",size=(700,700) )
        self.Hide()
        server_page.Show()
    
    def on_configuration_button_click(self,event):
        """
        Display Configurations page.
        """
        utilities_page = Configuration(parent=self,id=4,title="Configurations",size=(700,700) )
        self.Hide()
        utilities_page.Show()

# ===== MAINLINE EXECUTION ====================================================

def main():
    """
    Entry point for the program.
    """
    app = wx.App()
    main_frame = MainFrame()
    app.MainLoop()

if __name__=="__main__":
    main()
