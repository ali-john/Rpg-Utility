"""rpg utility configurations page"""

# ----- IMPORTS ---------------------------------------------------------------
import json
import wx
from fnmatch import fnmatch

from rpg.rpgcore import RPGConfig

# ===== GLOBALS ===============================================================

rpg = RPGConfig()  # Configuration settings

# ----- CONSTANTS ---------------------------------------------------------------

config_file = open("config.json")
CONFIG = json.load(config_file)
config_file.close()

NUMBER_OF_COLUMNS = 2

# ===== FUNCTIONS =============================================================

def show_error(parent, message):
    wx.MessageBox(message, "Error", wx.OK | wx.ICON_ERROR, parent)


def show_success(parent, message):
    wx.MessageBox(message, "Success", wx.OK | wx.ICON_INFORMATION, parent)


# ----- CLASSES ---------------------------------------------------------------


class AddChangeParameterDialog(wx.Dialog):
    """
    Add a new parameter to the record.
    """
    def __init__(self, parent, title, parameter_data = None):
        super().__init__(parent, title=title, size=(350, 300))
        self.init_gui(parameter_data)


    def init_gui(self, parameter_data) -> None:
        panel = wx.Panel(self)
        self.key_label = wx.StaticText(panel, label = "Parameter Key:")
        self.key_text = wx.TextCtrl(panel)
        self.value_label = wx.StaticText(panel, label = "Value:")
        self.value_text = wx.TextCtrl(panel)
        self.encrypt_label = wx.StaticText(panel, label = "Encrypt:")
        self.encrypt_choice = wx.Choice(panel, choices=["True", "False"])

        self.ok_btn = wx.Button(panel, wx.ID_OK, "OK")
        self.cancel_btn = wx.Button(panel, wx.ID_CANCEL, "Cancel")

        if parameter_data: # pre-fill text if parameter data is provided
            self.key_text.SetValue(parameter_data["key"])
            self.value_text.SetValue(parameter_data["value"])
            self.encrypt_choice.SetStringSelection(parameter_data["encrypt"])

            self.key_text.Enable(False)


        grid = wx.FlexGridSizer(6, 2, 10, 10)
        grid.AddMany([
            (self.key_label), (self.key_text,1,wx.EXPAND),
             (self.value_label), (self.value_text,1,wx.EXPAND),
            (self.encrypt_label), (self.encrypt_choice, 1, wx.EXPAND),
        ])
        
        grid.AddGrowableCol(1, 1)
        btn_sizer = wx.StdDialogButtonSizer()
        main_sizer = wx.BoxSizer(wx.VERTICAL)
        
        btn_sizer.AddButton(self.ok_btn)
        btn_sizer.AddButton(self.cancel_btn)
        btn_sizer.Realize()

        main_sizer.Add(grid, 1, wx.ALL | wx.EXPAND, 15)
        main_sizer.Add(btn_sizer, 0, wx.ALIGN_CENTER | wx.ALL, 10)
        panel.SetSizer(main_sizer)


    def get_parameter_data(self) -> dict:
        """
        Returns parameter record as a dictionary.
        """
        return {
            "key": self.key_text.GetValue(),
            "value": self.value_text.GetValue(),
            "encrypt":self.encrypt_choice.GetStringSelection()
        }

class Configuration(wx.Frame):
    """
    The main configurations page.
    """
    def __init__(self, parent, id, title, size):
        super().__init__(parent, title=title, size=size)
        self.init_gui(parent)
        self.bind_events()
        self.populate_parameter_list()
        self.adjust_column_widths() 
        self.Show()
 

    def init_gui(self, parent):
        self.panel = wx.Panel(self)
        self.parent = parent
        self.add_parameter_button = wx.Button(parent = self.panel, label = "Add Parameter")
        self.delete_parameter_button = wx.Button(parent = self.panel, label = 'Delete Parameter')
        self.back_button = wx.Button(parent = self.panel, label= 'Go Back')

        # set title for window
        title = wx.StaticText(self.panel, label="Available Parameters", style=wx.ALIGN_CENTER)
        font = title.GetFont()
        font.PointSize += 6
        font = font.Bold()
        title.SetFont(font)

        # add columns to the page
        self.list_ctrl = wx.ListCtrl(self.panel, style=wx.LC_REPORT | wx.BORDER_SUNKEN)
        self.list_ctrl.SetBackgroundColour(wx.Colour(CONFIG["COLORS"]["BACKGROUND_COLOR"]))
        self.list_ctrl.InsertColumn(0, "Parameter Name")
        self.list_ctrl.InsertColumn(1, "Parameter Value")
        
        # create sizers
        button_sizer = wx.BoxSizer(wx.HORIZONTAL)
        main_sizer = wx.BoxSizer(wx.VERTICAL)

        button_sizer.Add(self.back_button, flag=wx.ALL, border=5)
        button_sizer.Add(self.add_parameter_button, flag=wx.ALL, border=5)
        button_sizer.Add(self.delete_parameter_button, flag=wx.ALL, border=5)
        
        main_sizer.Add(title, flag=wx.ALIGN_CENTER | wx.TOP, border=12)
        main_sizer.Add(self.list_ctrl, proportion=1, flag=wx.EXPAND | wx.ALL, border=10)
        main_sizer.Add(button_sizer, flag=wx.ALIGN_CENTER | wx.BOTTOM, border=10)
        
        self.panel.SetSizer(main_sizer)
        self.SetBackgroundColour(wx.Colour(CONFIG["COLORS"]["BACKGROUND_COLOR"]))
        self.Center()
         
        
    def bind_events(self) -> None:
        """
        Triggers an event when an item is interacted with.
        """
        self.add_parameter_button.Bind(wx.EVT_BUTTON, self.on_add_parameter_button_click)
        self.delete_parameter_button.Bind(wx.EVT_BUTTON,self.on_delete_parameter_button_click)
        self.back_button.Bind(wx.EVT_BUTTON, self.on_back_button_click)
        self.Bind(wx.EVT_SIZE, self.on_resize)
        self.list_ctrl.Bind(wx.EVT_LIST_ITEM_ACTIVATED, self.on_parameter_double_click)


    def populate_parameter_list(self) -> None:
        """
        Fetches Parameter data and populates the ListCtrl.
        """
        self.list_ctrl.DeleteAllItems()
        key_pattern = ""
        for idx,key in enumerate(rpg.parameters()):
            if fnmatch(key, key_pattern + "*"):
                value = rpg.get_param(key, decrypt=False)
                self.list_ctrl.InsertItem(idx,key)
                self.list_ctrl.SetItem(idx,1,value)


    def adjust_column_widths(self):
        """
        Adjusts column widths dynamically to be 1/4 of window width.
        """
        total_width = self.GetSize().Width - 20 
        col_width = total_width // NUMBER_OF_COLUMNS
        for i in range(NUMBER_OF_COLUMNS):
            self.list_ctrl.SetColumnWidth(i, col_width)


    def on_resize(self, event):
        """
        Handles window resize to adjust column widths.
        """
        event.Skip()
        self.adjust_column_widths()


    def on_close(self, event):
        """
        Closes the dialog.
        """
        # TODO: Delete the parent window as well
        self.Destroy()
    
    
    def on_add_parameter_button_click(self,event) -> None:
        """
        Add a new parameter to the record.
        """

        dialog = AddChangeParameterDialog(self, title = "Add a Parameter")
        if dialog.ShowModal() == wx.ID_OK:
            parameter_data = dialog.get_parameter_data()
            # TODO: Add checks on the data
            key = parameter_data["key"]
            value = parameter_data["value"]
            encrypt = parameter_data["encrypt"] == "True"
            rpg.set_param(
                    param = key,
                    value = value,
                    encrypt=encrypt,
                )
            self.populate_parameter_list()
            wx.Yield()
            show_success(self,message=f"Parameter '{key}' added successfully.")
        
        dialog.Destroy()

    
    def on_delete_parameter_button_click(self,event) -> None:
        """
        Delete a parameter from the record.
        """
        selected_index = self.list_ctrl.GetFirstSelected()
        if selected_index == -1: # if no selection is made
            show_error(self,"Please select a Parameter to delete.")
            return
        
        key = self.list_ctrl.GetItemText(selected_index)
        
        confirmation = wx.MessageBox(
            f"Are you sure you want to delete Parameter '{key}'?",
            "Confirm Delete",
            wx.YES_NO | wx.ICON_QUESTION,
            self
            )
        if confirmation == wx.YES:
            rpg.remove_option("CONFIG", key)
            rpg.save()
            self.populate_parameter_list()
            wx.Yield()
            show_success(self, f"Parameter '{key}' deleted successfully.")

    
    def on_parameter_double_click(self,event) -> None:
        """
        Change an existing parameter values.
        """
        selected_index = event.GetIndex()
        if selected_index == -1:  # if no selection is made
            show_error(self, "Please select a parameter to change.")
            return
       
        parameter_data = {
            "key": self.list_ctrl.GetItemText(selected_index),
            "value": self.list_ctrl.GetItemText(selected_index, 1),
        }
        value = parameter_data.get("value","")
        if value == "<encrypted>":
            encrypted = "True"
        else:
            encrypted = "False"
        parameter_data["encrypt"] = encrypted
        dialog = AddChangeParameterDialog(self, title = "Change Parameter", parameter_data = parameter_data)
        if dialog.ShowModal() != wx.ID_OK:
            return 
        
        updated_data = dialog.get_parameter_data()
        key = updated_data.get('key', '')
        new_value = updated_data.get('value', '')
        new_encrypted = updated_data.get('encrypt', 'False')
        
        if not new_value:
            show_error(self, "Parameter value cannot be empty.")
            return

        if new_value == parameter_data.get('value','') and new_encrypted == encrypted: # no changes made to the parameter value
            show_success(self, message=f' No changes in parameter {key}.')
            return

        if not rpg.has_param(key):
            show_error(self, message=f'Parameter {key} does not exist.')
            return

        rpg.set_param(param = key, value = new_value, encrypt = new_encrypted == "True")
        self.populate_parameter_list()
        wx.Yield()
        show_success(self,message=f"Parameter '{key}' changed successfully.")
        
    def on_back_button_click(self,event) -> None:
            """
            Go back to the main page.
            """
            # TODO: Delete the current page.
            self.Hide()
            self.parent.Show()
    
