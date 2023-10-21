import subprocess
from gi.repository import GObject, Gedit

def format_with_clang(document):
    if document and document.get_mime_type() in ["text/x-csrc", "text/x-c++src"]:
        # Get current cursor position.
        cursor_mark = document.get_insert()
        cursor_iter = document.get_iter_at_mark(cursor_mark)
        cursor_offset = cursor_iter.get_offset()
        
        # Determine the directory of the current document.
        gedit_file = document.get_file()
        location = gedit_file.get_location()
        if location:
            file_directory = location.get_parent().get_path()
        else:
            file_directory = None

        try:
            source_code = document.get_text(document.get_start_iter(), document.get_end_iter(), True)
            formatted_code = subprocess.check_output(["clang-format"], input=source_code.encode(), stderr=subprocess.PIPE, cwd=file_directory)
            document.begin_user_action()
            document.set_text(formatted_code.decode())
            document.end_user_action()

            # Restore cursor position.
            cursor_iter = document.get_iter_at_offset(cursor_offset)
            document.place_cursor(cursor_iter)
        except Exception as e:
            # Handle or print exception.
            print(e)

class ClangFormatOnSavePlugin(GObject.Object, Gedit.WindowActivatable):
    __gtype_name__ = "ClangFormatOnSavePlugin"
    window = GObject.property(type=Gedit.Window)

    def __init__(self):
        GObject.Object.__init__(self)
        self._handler_ids = []

    def do_activate(self):
        for doc in self.window.get_documents():
            handler_id = doc.connect("saving", self.on_document_saving)
            self._handler_ids.append((doc, handler_id))
        
        self.window.connect("tab-added", self.on_tab_added)

    def do_deactivate(self):
        for doc, handler_id in self._handler_ids:
            doc.disconnect(handler_id)
        self._handler_ids.clear()

    def on_document_saving(self, document, *args):
        format_with_clang(document)

    def on_tab_added(self, window, tab):
        doc = tab.get_document()
        handler_id = doc.connect("save", self.on_document_saving)
        self._handler_ids.append((doc, handler_id))

