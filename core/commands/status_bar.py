import time
import sublime
from sublime_plugin import TextCommand, EventListener

from ..git_command import GitCommand
from ...common.util import debug


class GsStatusBarEventListener(EventListener):

    # these methods should be run synchronously to check if the
    # view is transient.
    def on_new(self, view):
        view.run_command("gs_update_status_bar")

    def on_load(self, view):
        view.run_command("gs_update_status_bar")

    def on_activated(self, view):
        view.run_command("gs_update_status_bar")

    def on_post_save(self, view):
        view.run_command("gs_update_status_bar")


last_execution = 0
update_status_bar_soon = False


class GsUpdateStatusBarCommand(TextCommand, GitCommand):

    """
    Update the short Git status in the Sublime status bar.
    """

    def run(self, edit):
        if self.view.settings().get('is_widget'):
            return

        window = self.view.window()
        if not window or \
            (self.view.file_name() and
                self.view == window.transient_view_in_group(window.active_group())):
            # it means it is an transient view of a regular file
            return

        global last_execution, update_status_bar_soon
        if sublime.load_settings("GitSavvy.sublime-settings").get("git_status_in_status_bar"):

            millisec = int(round(time.time() * 1000))
            # If we updated to less then 100 ms we don't need to update now but
            # should update in 100 ms in case of current file change.
            #
            # So if this get called 4 timer with 20 ms in between each call
            # it will only update twice. Once at time 0 and one at time 100
            # even if it got called at 0, 20, 40, 60 and 80.

            if millisec - 100 > last_execution:
                sublime.set_timeout_async(self.run_async, 0)
            else:
                if not update_status_bar_soon:
                    update_status_bar_soon = True
                    sublime.set_timeout_async(self.run_async, 100)

            last_execution = int(round(time.time() * 1000))

    def run_async(self):
        # disable logging and git raise error
        with debug.disable_logging():
            # ignore all other possible errors
            try:
                self.repo_path  # check for ValueError
                short_status = self.get_branch_status_short()
                self.view.set_status("gitsavvy-repo-status", short_status)
            except Exception as e:
                self.view.erase_status("gitsavvy-repo-status")

        global update_status_bar_soon
        update_status_bar_soon = False
