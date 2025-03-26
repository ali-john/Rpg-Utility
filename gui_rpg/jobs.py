"""rpg utility jobs page"""

# ----- IMPORTS ---------------------------------------------------------------
import json
import re
from fnmatch import fnmatch
import wx


from rpg.rpgcore import RPGConfig

# ===== GLOBALS ===============================================================

rpg = RPGConfig()  # Configuration settings

# ----- CONSTANTS ---------------------------------------------------------------

with open("config.json", encoding="utf-8") as config_file:
    CONFIG = json.load(config_file)

NUMBER_OF_COLUMNS = 4
JOBS_PATTERN1 = re.compile(r'^[A-Z]{4,12}$')
JOBS_PATTERN2 = re.compile(r'^[A-Z]{2,8}[0-9]{2}[A-Z]?$')
WEEKDAYS = {"MON", "TUE", "WED", "THU", "FRI", "SAT", "SUN"}

# ===== FUNCTIONS =============================================================

def show_error(parent, message):
    wx.MessageBox(message, "Error", wx.OK | wx.ICON_ERROR, parent)


def show_success(parent, message):
    wx.MessageBox(message, "Success", wx.OK | wx.ICON_INFORMATION, parent)


# ----- CLASSES ---------------------------------------------------------------

class AddJobDialog(wx.Dialog):
    """
    Add a new job record window.
    """
    def __init__(self, parent, title):
        super().__init__(parent, title=title, size=(350, 300))
        self.init_gui()

    def init_gui(self):
        """
        Initializes the GUI window.
        """
        panel = wx.Panel(self)
        self.id_label = wx.StaticText(panel,label = "Job ID:")
        self.id_text = wx.TextCtrl(panel)
        self.frequency_label = wx.StaticText(panel, label = "Frequency:")
        self.frequency_text = wx.TextCtrl(panel)

        self.ok_btn = wx.Button(panel, wx.ID_OK, "OK")
        self.cancel_btn = wx.Button(panel, wx.ID_CANCEL, "Cancel")


        grid = wx.FlexGridSizer(6, 2, 10, 10)
        grid.AddMany([
            (self.id_label), (self.id_text,1,wx.EXPAND),
            (self.frequency_label), (self.frequency_text, 1, wx.EXPAND),
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


    def get_job_data(self) -> dict:
        """
        Returns job details as a dictionary.
        """
        return {
            "job_id": self.id_text.GetValue(),
            "frequency": self.frequency_text.GetValue(),
        }


class ChangeJobDialog(wx.Dialog):
    """
    Change an existing job record.
    """
    def __init__(self, parent, title, job_data):
        super().__init__(parent, title=title, size=(350, 300))
        self.init_gui(job_data)


    def init_gui(self, job_data) -> None:
        panel = wx.Panel(self)
        self.id_label = wx.StaticText(panel,label = "Job ID:")
        self.id_text = wx.TextCtrl(panel)
        self.last_run_label = wx.StaticText(panel, label = "Last Run:")
        self.last_run_text = wx.TextCtrl(panel)
        self.next_run_label = wx.StaticText(panel, label = "Next Run:")
        self.next_run_text = wx.TextCtrl(panel)
        self.frequency_label = wx.StaticText(panel, label = "Frequency:")
        self.frequency_text = wx.TextCtrl(panel)
        self.id_text.Enable(False) # disable editing job ID

        self.ok_btn = wx.Button(panel, wx.ID_OK, "OK")
        self.cancel_btn = wx.Button(panel, wx.ID_CANCEL, "Cancel")

        self.id_text.SetValue(job_data["job_id"])
        self.last_run_text.SetValue(job_data["last_run"])  
        self.next_run_text.SetValue(job_data["next_run"])
        self.frequency_text.SetValue(job_data["frequency"])


        # Add to layout
        grid = wx.FlexGridSizer(6, 2, 10, 10)
        grid.AddMany([
            (self.id_label), (self.id_text,1,wx.EXPAND),
            (self.last_run_label), (self.last_run_text, 1, wx.EXPAND),
            (self.next_run_label), (self.next_run_text, 1, wx.EXPAND),
            (self.frequency_label), (self.frequency_text, 1, wx.EXPAND),
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


    def get_job_data(self) -> dict:
        """
        Returns an existing job record as a dictionary.
        """
        return {
            "job_id": self.id_text.GetValue(),
            "last_run": self.last_run_text.GetValue(),
            "next_run": self.next_run_text.GetValue(),
            "frequency": self.frequency_text.GetValue(),
        }


class Jobs(wx.Frame):
    """
    The main Jobs class.
    """
    def __init__(self, parent, id, title, size):
        super().__init__(parent, title=title, size=size)
        self.init_gui(parent)
        self.bind_events()
        self.populate_jobs_list()
        self.adjust_column_widths()
        self.Show()

    def init_gui(self, parent):
        self.panel = wx.Panel(self)
        self.parent = parent
        self.add_job_button = wx.Button(parent = self.panel, label = "Add Job")
        self.delete_job_button = wx.Button(parent = self.panel, label = 'Delete Job')
        self.back_button = wx.Button(parent = self.panel, label = 'Go Back')

        # set title for window
        title = wx.StaticText(self.panel, label = "Available Jobs", style=wx.ALIGN_CENTER)
        font = title.GetFont()
        font.PointSize += 6
        font = font.Bold()
        title.SetFont(font)

        # add columns to page
        self.list_ctrl = wx.ListCtrl(self.panel, style=wx.LC_REPORT | wx.BORDER_SUNKEN)
        self.list_ctrl.SetBackgroundColour(wx.Colour(CONFIG["COLORS"]["BACKGROUND_COLOR"]))
        self.list_ctrl.InsertColumn(0, "Job Name")
        self.list_ctrl.InsertColumn(1, "Last Run")
        self.list_ctrl.InsertColumn(2, "Next Run")
        self.list_ctrl.InsertColumn(3, "Frequency")

        # add a button sizer
        button_sizer = wx.BoxSizer(wx.HORIZONTAL)

        button_sizer.Add(self.back_button, flag=wx.ALL, border=5)
        button_sizer.Add(self.add_job_button, flag=wx.ALL, border=5)
        button_sizer.Add(self.delete_job_button, flag=wx.ALL, border=5)

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
        self.back_button.Bind(wx.EVT_BUTTON, self.on_back_button_click)
        self.add_job_button.Bind(wx.EVT_BUTTON, self.on_add_job_button_click)
        self.delete_job_button.Bind(wx.EVT_BUTTON,self.on_delete_job_button_click)
        self.Bind(wx.EVT_SIZE, self.on_resize)
        self.list_ctrl.Bind(wx.EVT_LIST_ITEM_ACTIVATED, self.on_job_double_click)
        self.Bind(wx.EVT_CLOSE, self.on_close)


    def populate_jobs_list(self) -> None:
        """
        Fetches jobs data and populates the ListCtrl.
        """
        self.list_ctrl.DeleteAllItems()
        name_pattern = ""
        for idx, job_id in enumerate(rpg.jobs()):
            if fnmatch(job_id, name_pattern + "*"):
                _, _, last_run, next_run = rpg.get_job(job_id)
                freq = "Every " + rpg.get_job_day_text(job_id)
                last_run = last_run.strftime("%Y-%m-%d %H:%M") if last_run else "Never"
                next_run = next_run.strftime("%Y-%m-%d %H:%M")

                self.list_ctrl.InsertItem(idx,job_id)
                self.list_ctrl.SetItem(idx,1,last_run)
                self.list_ctrl.SetItem(idx,2,next_run)
                self.list_ctrl.SetItem(idx,3,freq)


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


    def on_add_job_button_click(self,event) -> None:
        """"
        Add a new job record.
        """
        dialog = AddJobDialog(self, title = "Add Job")
        if dialog.ShowModal() == wx.ID_OK:
            job_data = dialog.get_job_data()
            job_id = job_data.get("job_id",'').strip().upper()
            day = job_data.get("frequency",'').strip()

            if not (JOBS_PATTERN1.match(job_id) or JOBS_PATTERN2.match(job_id)):
                show_error(self, message='Invalid Job format. Must be 4-12 letters or follow format: 2-8 letters, 2 digits, optional letter.')
                dialog.Destroy()
                return
            if rpg.job_exists(job_id):
                show_error(self, f" Job {job_id} already exists.")
                dialog.Destroy()
                return
            if day.isdigit():
                if not (1 <= int(day) <=28 ):
                    show_error(self, message= "Frequency must be in range 1-28")
                    dialog.Destroy()
                    return
            elif day.upper() not in WEEKDAYS:
                show_error(self, message= "Frequency must be three letter weekday (Mon, Tue, etc.) or number in range 1-28")
                dialog.Destroy()
                return

            rpg.set_job(job_id= job_id, day= day.upper())
            self.populate_jobs_list()
            wx.Yield()
            show_success(self,message='Job added successfully.')
        dialog.Destroy()


    def on_job_double_click(self,event) -> None:
        """
        Change an existing job record.
        """
        selected_index = event.GetIndex()
        if selected_index == -1:  # if no selection is made
            show_error(self, "Please select a Job to change.")
            return

        job_data = {
            "job_id": self.list_ctrl.GetItemText(selected_index),
            "last_run": self.list_ctrl.GetItemText(selected_index, 1),
            "next_run": self.list_ctrl.GetItemText(selected_index, 2),
            "frequency": self.list_ctrl.GetItemText(selected_index, 3)
        }

        dialog = ChangeJobDialog(self, title = "Change Server", job_data = job_data)
        if dialog.ShowModal() != wx.ID_OK:
            return 

        updated_data = dialog.get_job_data()
        job_id = updated_data.get('job_id')
        new_frequency = updated_data.get('frequency', '').strip()

        if not new_frequency:
            show_error(self, "Job frequency cannot be empty.")
            return

        if new_frequency == job_data["frequency"]: # no changes made to the job
            show_success(self, message=f' No changes in Job {job_id}.')
            return

        if new_frequency.isdigit():
            if not (1<= int(new_frequency) <= 28):
                show_error(self, message= "Frequency must be in range 1-28")
                dialog.Destroy()
                return
            normalized_frequency = new_frequency 
        elif new_frequency.upper() in WEEKDAYS:
            normalized_frequency = new_frequency.upper()
        else:
            show_error(self, message= "Frequency must be three letter weekday (Mon, Tue, etc.) or number in range 1-28")
            dialog.Destroy()
            return

        if not rpg.job_exists(job_id):
            show_error(self, message=f'Job ID {job_id} does not exist.')
            return

        rpg.set_job(job_id=job_id, day=normalized_frequency)
        self.populate_jobs_list()
        wx.Yield()
        show_success(self, message=f'Job {job_id} changed successfully.')


    def on_delete_job_button_click(self,event) -> None:
        """
        Delete a Job record.
        """
        selected_index = self.list_ctrl.GetFirstSelected()
        if selected_index ==-1: # if no selection is made
            show_error(self,"Please select a Job to delete.")
            return

        job_id = self.list_ctrl.GetItemText(selected_index)
        confirmation = wx.MessageBox(
            f"Are you sure you want to delete job '{job_id}'?",
            "Confirm Delete",
            wx.YES_NO | wx.ICON_QUESTION,
            self
            )

        if confirmation == wx.YES:
            rpg.delete_job(job_id)
            self.populate_jobs_list()
            wx.Yield()
            show_success(self, f"Job '{job_id}' deleted successfully.")


    def on_back_button_click(self,event) -> None:
        """
        Go back to the main page.
        """
        self.Hide()
        self.parent.Show()