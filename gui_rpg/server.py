"""rpg utility server page"""

# ----- IMPORTS ---------------------------------------------------------------
import json
import re
import ipaddress
import wx

from rpg.rpgcore import RPGConfig

# ===== GLOBALS ===============================================================

rpg = RPGConfig()  # Configuration settings

# ----- CONSTANTS ---------------------------------------------------------------

with open("config.json", encoding='utf-8') as config_file:
    CONFIG = json.load(config_file)

NUMBER_OF_COLUMNS = 4
IP_PATTERN = re.compile(r'^\d+(\.\d+){3}$')
HOSTNAME_PATTERN = re.compile(r'^(?=.{1,253}$)(?!-)[A-Za-z0-9]([A-Za-z0-9-]{0,61}[A-Za-z0-9])?'
                              r'(\.[A-Za-z0-9]([A-Za-z0-9-]{0,61}[A-Za-z0-9])?)*$')


# ===== FUNCTIONS =============================================================

def show_error(parent, message):
    wx.MessageBox(message, "Error", wx.OK | wx.ICON_ERROR, parent)


def show_success(parent, message):
    wx.MessageBox(message, "Success", wx.OK | wx.ICON_INFORMATION, parent)

def validate_ip(address) -> int:
    """
    Validates a given IP address.

     Args:
        address (str): The IP address
    
     Returns:
        int: 0 if the IP address is valid else return -1

    """
    if IP_PATTERN.match(address):
        try:
            ipaddress.IPv4Network(address)
        except:
            return -1
    else:
        if not HOSTNAME_PATTERN.match(address):
            return -1
    return 0


def validate_port(port_number) -> int:
    """
    Validates a given port number.

     Args:
        port number (str): The port number
    
     Returns:
        int: 0 if the port number is valid else return -1

    """
    if not port_number.isdigit():
        return -1
    port_number = int(port_number)
    if not 1<= port_number <= 32767:
        return -1
    return 0



# ----- CLASSES ---------------------------------------------------------------

class AddChangeServerDialog(wx.Dialog):
    """
    Add a new server or change an existing server
    """
    def __init__(self, parent, title, server_data = None):
        super().__init__(parent, title=title, size=(350, 300))
        self.init_gui(server_data = server_data)


    def init_gui(self, server_data) -> None:
        """
        Initializes the GUI window.
        """
        panel = wx.Panel(self)
        self.id_label = wx.StaticText(panel, label = "Server ID:")
        self.id_text = wx.TextCtrl(panel)
        self.ip_label = wx.StaticText(panel, label = "Server IP:")
        self.ip_text = wx.TextCtrl(panel)
        self.port_label = wx.StaticText(panel, label = "Port:")
        self.port_text = wx.TextCtrl(panel)
        self.type_label = wx.StaticText(panel, label = "Type:")
        self.type_choice = wx.Choice(panel, choices = ["Oracle", "MS-SQL", "API"])
        self.username_label = wx.StaticText(panel, label = "Username:")
        self.username_text = wx.TextCtrl(panel)
        self.password_label = wx.StaticText(panel, label = "Password:")
        self.password_text = wx.TextCtrl(panel, style=wx.TE_PASSWORD)

        self.ok_btn = wx.Button(panel, wx.ID_OK, "OK")
        self.cancel_btn = wx.Button(panel, wx.ID_CANCEL, "Cancel")

        if server_data: # pre-fill text if server data is provided
            self.id_text.SetValue(server_data["server_id"])
            self.ip_text.SetValue(server_data["address"].split(':')[0]) 
            self.port_text.SetValue(server_data["address"].split(':')[1])
            self.type_choice.SetStringSelection(server_data["server_type"])
            self.username_text.SetValue(server_data["user"])

            self.id_text.Enable(False)
  
        grid = wx.FlexGridSizer(6, 2, 10, 10)
        grid.AddMany([
            (self.id_label), (self.id_text,1,wx.EXPAND),
            (self.ip_label), (self.ip_text, 1, wx.EXPAND),
            (self.port_label), (self.port_text, 1, wx.EXPAND),
            (self.type_label), (self.type_choice, 1, wx.EXPAND),
            (self.username_label), (self.username_text, 1, wx.EXPAND),
            (self.password_label), (self.password_text, 1, wx.EXPAND)
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

    def get_server_data(self) -> dict:
        """
        Returns filled server data as a dictionary.
        """
        return {
            "server_id": self.id_text.GetValue(),
            "address": self.ip_text.GetValue(),
            "port": self.port_text.GetValue(),
            "server_type": self.type_choice.GetStringSelection().lower(),
            "user": self.username_text.GetValue(),
            "password": self.password_text.GetValue(),
        }


class Server(wx.Frame):
    """
    The main server class. 
    """
    def __init__(self, parent, id, title, size):
        super().__init__(parent, title=title, size=size)
        self.init_gui(parent)
        self.bind_events()
        self.populate_server_list()
        self.adjust_column_widths()
        self.Show()


    def init_gui(self,parent) -> None:
        """
        Create the GUI for server page.
        """
        self.panel = wx.Panel(self)
        self.parent = parent
        self.add_server_button = wx.Button(parent = self.panel, label = "Add Server")
        self.delete_server_button = wx.Button(parent = self.panel, label = 'Delete Server')
        self.back_button = wx.Button(parent = self.panel, label = 'Go Back')

        # set title for window
        title = wx.StaticText(self.panel, label="Available Servers", style=wx.ALIGN_CENTER) 
        font = title.GetFont()
        font.PointSize += 6
        font = font.Bold()
        title.SetFont(font)

        # add columns to page
        self.list_ctrl = wx.ListCtrl(self.panel, style=wx.LC_REPORT | wx.BORDER_SUNKEN)
        self.list_ctrl.SetBackgroundColour(wx.Colour(CONFIG["COLORS"]["BACKGROUND_COLOR"]))
        self.list_ctrl.InsertColumn(0, "Server ID")
        self.list_ctrl.InsertColumn(1, "Server Address")
        self.list_ctrl.InsertColumn(2, "Type")
        self.list_ctrl.InsertColumn(3, "User")

        # add buttons to horizontal sizer
        button_sizer = wx.BoxSizer(wx.HORIZONTAL)

        button_sizer.Add(self.back_button, flag=wx.ALL, border=5)
        button_sizer.Add(self.add_server_button, flag=wx.ALL, border=5)
        button_sizer.Add(self.delete_server_button, flag=wx.ALL, border=5)

        # add a main sizer
        main_sizer = wx.BoxSizer(wx.VERTICAL)

        main_sizer.Add(title, flag=wx.ALIGN_CENTER | wx.TOP, border=12)
        main_sizer.Add(self.list_ctrl, proportion=1, flag=wx.EXPAND | wx.ALL, border=10)
        main_sizer.Add(button_sizer, flag=wx.ALIGN_CENTER | wx.BOTTOM, border=10)

        self.panel.SetSizer(main_sizer)
        self.SetBackgroundColour(wx.Colour(CONFIG["COLORS"]["BACKGROUND_COLOR"]))
        self.Center()


    def bind_events(self) -> None:
        """
        Trigger an event when an item is interacted with.
        """
        self.add_server_button.Bind(wx.EVT_BUTTON, self.on_add_server_button_click)
        self.delete_server_button.Bind(wx.EVT_BUTTON, self.on_delete_server_button_click)
        self.back_button.Bind(wx.EVT_BUTTON, self.on_back_button_click)
        self.Bind(wx.EVT_SIZE, self.on_resize)
        self.list_ctrl.Bind(wx.EVT_LIST_ITEM_ACTIVATED, self.on_server_double_click)
        self.Bind(wx.EVT_CLOSE, self.on_close)


    def populate_server_list(self) -> None:
        """
        Fetches server data and populates the ListCtrl.
        """
        self.list_ctrl.DeleteAllItems()
        for idx, server_name in enumerate(rpg.servers()):
            try:
                hostname, port, username, _, server_type = rpg.get_server(server_name)
                address = f"{hostname}:{port}"
            except KeyError:
                address, server_type, username = "Decryption Error", "N/A", "N/A"

            self.list_ctrl.InsertItem(idx, server_name)
            self.list_ctrl.SetItem(idx, 1, address)
            self.list_ctrl.SetItem(idx, 2, server_type)
            self.list_ctrl.SetItem(idx, 3, username)


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
        if self.parent:
            self.parent.Destroy()
        self.Destroy()


    def on_add_server_button_click(self, event) -> None:
        """
        Add a new server record
        """
        dialog = AddChangeServerDialog(self, title="Add Server")
        if dialog.ShowModal() == wx.ID_OK:
            server_data = dialog.get_server_data()
            server_id = server_data.get("server_id",'').strip().upper()
            address = server_data.get("address", '').strip()
            port_number = server_data.get("port",'').strip()
            user = server_data.get("user",'').strip()
            password = server_data.get("password",'').strip()
            # perform data checks on server id
            if len(server_id) < 4 or len(server_id) > 16 or not server_id.isalnum():
                show_error(self, message= "Server name must be 4-16 alpha numeric characters.")
                dialog.Destroy()
                return
            if rpg.server_exists(server_id):
                show_error(self, message=f" Server {server_id} already exists.")
                dialog.Destroy()
                return

            # perform data checks on server address
            status = validate_ip(address)
            if status == -1:
                show_error(self, message=f" Address must be a valid IP address or hostname.")
                dialog.Destroy()
                return
            # perform data check on server port number
            status = validate_port(port_number)
            if status == -1:
                show_error(self, message= "Port number must be valid number in range 1-32767.")
                dialog.Destroy()
                return
        
            # perform check on user
            if not user:
                show_error(self, message="User can not be empty.")
                dialog.Destroy()
                return

            # perform check on password:
            if not password:
                show_error(self, message="Password can not be empty.")
                dialog.Destroy()
                return
            rpg.set_server(**server_data)
            self.populate_server_list()
            wx.Yield()
            show_success(self,message='Server added successfully')
        dialog.Destroy()

    def on_server_double_click(self,event) -> None:
        """
        Change an existing server record
        """
        selected_index = event.GetIndex()
        if selected_index == -1: # if no selection is made
            show_error(self,"Please select a server to change.")
            return

        server_data = {
            "server_id": self.list_ctrl.GetItemText(selected_index),
            "address": self.list_ctrl.GetItemText(selected_index, 1),
            "server_type": self.list_ctrl.GetItemText(selected_index, 2),
            "user": self.list_ctrl.GetItemText(selected_index, 3)
        }

        dialog = AddChangeServerDialog(self, title = "Change Server", server_data = server_data)
        if dialog.ShowModal() == wx.ID_OK:
            updated_data = dialog.get_server_data()
            prev_data = rpg.get_server(updated_data['server_id'])
            if len(updated_data['password']) == 0: # if there are no changes to password field
                updated_data['password'] = prev_data[3]

            server_name = updated_data['server_id'].strip().upper() # server id is not editable.
            address = updated_data.get("address",'').strip()
            port_number = updated_data.get("port",'').strip()
            user = updated_data.get("user",'').strip()
            password = updated_data.get("password",'').strip()

            if not rpg.server_exists(server_name):
                show_error(self,message=f'Server name {server_name} does not exists.')

            # perform check on server ip
            status = validate_ip(address)
            if status == -1:
                show_error(self, message=" Address must be a valid IP address or hostname.")
                dialog.Destroy()
                return
            # perform data check on server port number
            status = validate_port(port_number)
            if status == -1:
                show_error(self, message = "Port number must be valid number in range 1-32767.")
                dialog.Destroy()
                return
  
            # perform check on user
            if not user:
                show_error(self, message="User can not be empty.")
                dialog.Destroy()
                return

            # perform check on password:
            if not password:
                show_error(self, message="Password can not be empty.")
                dialog.Destroy()
                return

            rpg.set_server(**updated_data)
            self.populate_server_list()
            wx.Yield()
            show_success(self,message = f'Server {server_name} changed successfully.')
                

    def on_delete_server_button_click(self,event) -> None:
        """
        Delete a server record.
        """
        selected_index = self.list_ctrl.GetFirstSelected()
        if selected_index == -1: # if no selection is made
            show_error(self,"Please select a server to delete.")
            return

        server_id = self.list_ctrl.GetItemText(selected_index)
        confirmation = wx.MessageBox(
            f"Are you sure you want to delete server '{server_id}'?",
            "Confirm Delete",
            wx.YES_NO | wx.ICON_QUESTION,
            self
            )
        if confirmation == wx.YES:
            rpg.delete_server(server_id)
            self.populate_server_list()
            wx.Yield()
            show_success(self, f"Server '{server_id}' deleted successfully.")


    def on_back_button_click(self,event) -> None:
        """
        Go back to the main page.
        """
        self.Hide()
        self.parent.Show()

