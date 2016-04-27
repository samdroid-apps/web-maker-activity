# Copyright 2016 Sam Parkinson <sam@sam.today>
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA  02110-1301  USA

import os
import time
import json
import logging
from gettext import gettext as _

from gi.repository import Gtk
from gi.repository import Pango
from gi.repository import Gdk
from gi.repository import GtkSource
from gi.repository import WebKit2

from sugar3.activity import activity
from sugar3.graphics.alert import Alert
from sugar3.graphics.toolbutton import ToolButton
from sugar3.graphics.toolbarbox import ToolbarBox
from sugar3.activity.widgets import ActivityToolbarButton
from sugar3.activity.widgets import StopButton


class WebMakerActivity(activity.Activity):

    def __init__(self, handle):
        activity.Activity.__init__(self, handle)
        self._has_read_file = False

        screen = Gdk.Screen.get_default()
        css_provider = Gtk.CssProvider.get_default()
        css_provider.load_from_path('style.css')
        context = Gtk.StyleContext()
        context.add_provider_for_screen(screen, css_provider,
                                        Gtk.STYLE_PROVIDER_PRIORITY_USER)
        toolbar_box = ToolbarBox()

        activity_button = ActivityToolbarButton(self)
        toolbar_box.toolbar.insert(activity_button, 0)
        activity_button.show()

        run = ToolButton('computer-xo')
        run.props.accelerator = _('<alt>r')
        run.props.tooltip = _('Run')
        run.connect('clicked', self.__run_cb)
        toolbar_box.toolbar.insert(run, -1)
        run.show()

        separator = Gtk.SeparatorToolItem()
        separator.props.draw = False
        separator.set_expand(True)
        toolbar_box.toolbar.insert(separator, -1)
        separator.show()

        stop_button = StopButton(self)
        toolbar_box.toolbar.insert(stop_button, -1)
        stop_button.show()

        self.set_toolbar_box(toolbar_box)
        toolbar_box.show()

        self._build_canvas()

    def _build_canvas(self):
        grid = Gtk.Grid()
        self.set_canvas(grid)

        self._html = CodeView('html', '<!-- Add your HTML Content here -->')
        self._css = CodeView('css', '/* Add your CSS Styles here */')
        self._js = CodeView('javascript', '// Add your JavaScript Code here')
        self._webview = WebKit2.WebView()

        grid.attach(self._html, 0, 0, 1, 1)
        grid.attach(self._js, 0, 1, 1, 1)
        grid.attach(self._css, 1, 0, 1, 1)
        grid.attach(self._webview, 1, 1, 1, 1)

        grid.show_all()

    def __run_cb(self, button):
        html = '''
            <html><head>
                <style>{}</style>
            </head><body>
                {}
                <script>{}</script>
            </body></html>
        '''.format(str(self._css), str(self._html), str(self._js))
        self._webview.load_html(html, None)

    def write_file(self, file_path):
        data = dict(
            js=str(self._js),
            html=str(self._html),
            css=str(self._css)
        )
        with open(file_path, 'w') as f:
            json.dump(data, f)

        self.metadata['mime_type'] == 'application/json+webtest'

    def read_file(self, file_path):
        # FIXME: Why does sugar call read_file so many times?
        if self._has_read_file:
            return
        self._has_read_file = True

        with open(file_path) as f:
            j = json.load(f)
        self._js.set(j['js'])
        self._html.set(j['html'])
        self._css.set(j['css'])


class CodeView(Gtk.ScrolledWindow):

    def __init__(self, code_type, text=None):
        Gtk.ScrolledWindow.__init__(self)
        self._view = GtkSource.View()
        self.add(self._view)
        text_buffer = GtkSource.Buffer()

        lang_manager = GtkSource.LanguageManager.get_default()
        lang_ids = lang_manager.get_language_ids()
        langs = [lang_manager.get_language(lang_id)
                 for lang_id in lang_ids]
        for lang in langs:
            for m in lang.get_mime_types():
                if m == 'text/' + code_type:
                    text_buffer.set_language(lang)
        text_buffer.set_highlight_syntax(True)

        self.set_size_request(int(Gdk.Screen.width() * 0.5), int(Gdk.Screen.height() * 0.4))
        self._view.set_buffer(text_buffer)
        self._view.set_editable(True)
        self._view.set_cursor_visible(True)
        self._view.set_wrap_mode(Gtk.WrapMode.CHAR)
        self._view.set_insert_spaces_instead_of_tabs(True)
        self._view.set_tab_width(4)
        self._view.set_can_focus(True)
        self._view.modify_font(Pango.FontDescription('Monospace 14'))

        if text is not None:
            self.set(text)

    def __str__(self):
        b = self._view.props.buffer
        return b.get_text(*b.get_bounds(), include_hidden_chars=False)

    def set(self, text):
        self._view.props.buffer.set_text(text)
        self._view.props.buffer.set_modified(False)
