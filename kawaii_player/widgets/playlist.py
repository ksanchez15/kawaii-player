"""
Copyright (C) 2017 kanishka-linux kanishka.linux@gmail.com

This file is part of kawaii-player.

kawaii-player is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

kawaii-player is distributed in the hope that it will be useful, 
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with kawaii-player.  If not, see <http://www.gnu.org/licenses/>.
"""

import os
import re
import sqlite3
import shutil
import subprocess
import base64
import urllib.parse
from bs4 import BeautifulSoup
from PyQt5 import QtCore, QtGui, QtWidgets
from player_functions import write_files, open_files, ccurl, send_notification


class PlaylistWidget(QtWidgets.QListWidget):

    def __init__(self, parent, uiwidget=None, home_var=None, tmp=None, logr=None):
        super(PlaylistWidget, self).__init__(parent)
        global MainWindow, home, TMPDIR, logger, ui
        self.setDefaultDropAction(QtCore.Qt.MoveAction)
        self.setAcceptDrops(True)
        self.setDragEnabled(True)
        self.setDragDropMode(QtWidgets.QAbstractItemView.InternalMove)
        self.downloadWget = []
        self.downloadWget_cnt = 0
        MainWindow = parent
        ui = uiwidget
        TMPDIR = tmp
        home = home_var
        logger = logr
        self.upcount = 0
        self.downcount = 0
        self.count_limit = 1

    def mouseMoveEvent(self, event): 
        if ui.auto_hide_dock and not ui.dockWidget_3.isHidden():
            ui.dockWidget_3.hide()
        if ui.tab_5.arrow_timer.isActive():
            ui.tab_5.arrow_timer.stop()
        self.setFocus()

    def init_offline_mode(self):
        print(self.currentRow(), '--init--offline--')
        param_dict = ui.get_parameters_value(s='site', w='wget')
        site = param_dict['site']
        wget = param_dict['wget']
        if (site.lower() != "Local" and site.lower() != 'video' 
                and site.lower() != 'music'):
            if wget.processId() == 0 and not ui.epn_wait_thread.isRunning():
                ui.download_video = 1
                r = self.currentRow()
                item = self.item(r)
                if item:
                    ui.start_offline_mode(r)
            else:
                if not ui.queue_url_list:
                    ui.list6.clear()
                r = self.currentRow()
                item = self.item(r)
                if item:
                    ui.queue_url_list.append(r)
                    txt = ui.epn_arr_list[r].split('	')[0].replace('_', ' ')
                    if txt.startswith('#'):
                        txt = txt.replace('#', '', 1)
                    ui.list6.addItem(txt)
    
    def open_in_file_manager(self, row):
        param_dict = ui.get_parameters_value(s='site', sn='siteName', o='opt')
        site = param_dict['site']
        siteName = param_dict['siteName']
        opt = param_dict['opt']
        path_dir = ''
        if (site.lower() == 'video' or site.lower() == 'music' or 
                site.lower() == 'playlists' or site.lower() == 'none'):
            path = ui.epn_arr_list[row].split('\t')[1]
            if path.startswith('abs_path='):
                path = path.split('abs_path=', 1)[1]
                path = str(base64.b64decode(path).decode('utf-8'))
            if path.startswith('"'):
                path = path[1:]
            if path.endswith('"'):
                path = path[:-1]
            if os.path.exists(path):
                path_dir, path_file = os.path.split(path)
        elif opt.lower() == 'history':
            if ui.list1.currentItem():
                itemlist = ui.list1.currentItem()
                if  itemlist:
                    new_row = ui.list1.currentRow()
                    item_value = ui.original_path_name[new_row]
                    if '\t' in item_value:
                        old_name = item_value.split('\t')[0]
                    else:
                        old_name = item_value
                    if site.lower() == 'subbedanime' or site.lower() == 'dubbedanime':
                        history_txt = os.path.join(home, 'History', site, siteName, 'history.txt')
                        path_dir = os.path.join(home, 'History', site, siteName, old_name)
                    else:
                        history_txt = os.path.join(home, 'History', site, 'history.txt')
                        path_dir = os.path.join(home, 'History', site, old_name)
        if os.path.exists(path_dir):
            if os.name == 'posix':
                subprocess.Popen(['xdg-open', path_dir])
            elif os.name == 'nt':
                subprocess.Popen(['start', path_dir], shell=True)
        else:
            msg = 'local file path does not exists: {0}'.format(path)
            send_notification(msg)
            
    def queue_item(self):
        param_dict = ui.get_parameters_value(s='site', v='video_local_stream')
        site = param_dict['site']
        video_local_stream = param_dict['video_local_stream']
        if (site == "Music" or site == "Video" or site == "Local" 
                or site == "PlayLists" or site == "None"):
            file_path = os.path.join(home, 'Playlists', 'Queue')
            if not os.path.exists(file_path):
                f = open(file_path, 'w')
                f.close()
            if not ui.queue_url_list:
                ui.list6.clear()
            r = self.currentRow()
            item = self.item(r)
            if item:
                ui.queue_url_list.append(ui.epn_arr_list[r])
                ui.list6.addItem(ui.epn_arr_list[r].split('	')[0])
                logger.info(ui.queue_url_list)
                write_files(file_path, ui.epn_arr_list[r], line_by_line=True)
        elif video_local_stream:
            if ui.list6.count() > 0:
                txt = ui.list6.item(0).text()
                if txt.startswith('Queue Empty:'):
                    ui.list6.clear()
            if self.currentItem():
                ui.list6.addItem(self.currentItem().text()+':'+str(self.currentRow()))
        else:
            if not ui.queue_url_list:
                ui.list6.clear()
            r = self.currentRow()
            item = self.item(r)
            if item:
                ui.queue_url_list.append(ui.epn_arr_list[r])
                ui.list6.addItem(ui.epn_arr_list[r].split('	')[0])
                
    def edit_name_list2(self, row):
        site = ui.get_parameters_value(s='site')['site']
        if '	' in ui.epn_arr_list[row]:
            default_text = ui.epn_arr_list[row].split('	')[0]
            default_path_name = ui.epn_arr_list[row].split('	')[1]
            default_basename = os.path.basename(default_path_name)
            default_display = 'Enter Episode Name Manually\nFile Name:\n{0}'.format(default_basename)
        else:
            default_text = ui.epn_arr_list[row]
            default_display = 'Enter Episode Name Manually\nDefault Name:\n{0}'.format(default_text)
        item, ok = QtWidgets.QInputDialog.getText(
            MainWindow, 'Input Dialog', default_display, 
            QtWidgets.QLineEdit.Normal, default_text)
            
        if ok and item:
            if '::' in item:
                nm = item.split('::')[0]
                artist = item.split('::')[1]
            else:
                nm = item
                artist = None
            logger.debug('{0}::{1}'.format(nm, artist))
            t = ui.epn_arr_list[row]
            logger.info("4282--{0}-{1}-{2}".format(nm, row, t))
            if ('	' in t and '	' not in nm and site != "Video" 
                    and site != "None" and site != 'PlayLists'
                    and not ui.music_playlist):
                r = t.split('	')[1]
                ui.epn_arr_list[row] = nm + '	'+r
                ui.mark_History()
            elif site == 'PlayLists' or ui.music_playlist:
                if artist is None:
                    tmp = ui.epn_arr_list[row]
                    tmp = re.sub('[^	]*', nm, tmp, 1)
                else:
                    tmp_arr = ui.epn_arr_list[row].split('\t')
                    tmp = nm + '\t' + tmp_arr[1] + '\t' + artist
                    logger.debug(tmp_arr)
                    logger.debug(tmp)
                logger.debug(tmp)
                ui.epn_arr_list[row] = tmp
                if ui.list1.currentItem():
                    pls_n = os.path.join(
                        home, 'Playlists', ui.list1.currentItem().text())
                    ui.update_playlist_original(pls_n)
                    self.setCurrentRow(row)
                listitem = self.item(row)
                if listitem:
                    listitem.setText(item)
            elif site == "Video":
                video_db = os.path.join(home, 'VideoDB', 'Video.db')
                conn = sqlite3.connect(video_db)
                cur = conn.cursor()
                txt = ui.epn_arr_list[row].split('	')[1]
                qr = 'Update Video Set EP_NAME=? Where Path=?'
                cur.execute(qr, (item, txt))
                conn.commit()
                conn.close()
                tmp = ui.epn_arr_list[row]
                tmp = re.sub('[^	]*', item, tmp, 1)
                ui.epn_arr_list[row] = tmp
                dir_path, file_path = os.path.split(txt)
                if dir_path in ui.video_dict:
                    del ui.video_dict[dir_path]
                listitem = self.item(row)
                if listitem:
                    listitem.setText(item)
            
    def get_default_name(self, row, mode=None):
        site = ui.get_parameters_value(s='site')['site']
        if site == "Video" and mode == 'default':
            video_db = os.path.join(home, 'VideoDB', 'Video.db')
            conn = sqlite3.connect(video_db)
            cur = conn.cursor()
            txt = ui.epn_arr_list[row].split('	')[1]
            item = os.path.basename(txt)
            item = item.replace('_', ' ')
            qr = 'Update Video Set EP_NAME=? Where Path=?'
            cur.execute(qr, (item, txt))
            conn.commit()
            conn.close()
            tmp = ui.epn_arr_list[row]
            tmp = re.sub('[^	]*', item, tmp, 1)
            ui.epn_arr_list[row] = tmp
            dir_path, file_path = os.path.split(txt)
            if dir_path in ui.video_dict:
                del ui.video_dict[dir_path]
            listitem = self.item(row)
            if listitem:
                listitem.setText(item)
        elif site == "Video" and mode == 'default_all':
            video_db = os.path.join(home, 'VideoDB', 'Video.db')
            conn = sqlite3.connect(video_db)
            cur = conn.cursor()
            for row, row_item in enumerate(ui.epn_arr_list):
                txt = row_item.split('	')[1]
                item = os.path.basename(txt)
                item = item.replace('_', ' ')
                qr = 'Update Video Set EP_NAME=? Where Path=?'
                cur.execute(qr, (item, txt))
                tmp = row_item
                tmp = re.sub('[^	]*', item, tmp, 1)
                ui.epn_arr_list[row] = tmp
            conn.commit()
            conn.close()
            dir_path, file_path = os.path.split(txt)
            if dir_path in ui.video_dict:
                del ui.video_dict[dir_path]
            ui.update_list2()
        elif site == 'Music' or site == 'PlayLists' or site == 'NONE':
            pass
        else:
            file_path = ''
            param_dict = ui.get_parameters_value(s='siteName', n='name')
            siteName = param_dict['siteName']
            name = param_dict['name']
            if site.lower() == "subbedanime" or site == "dubbedanime":
                file_path = os.path.join(home, 'History', site, siteName, name, 'Ep.txt')
            else:
                file_path = os.path.join(home, 'History', site, name, 'Ep.txt')
            if os.path.isfile(file_path):
                if mode == 'default':
                    old_value = ui.epn_arr_list[row]
                    if '\t' in old_value:
                        new_name = old_name = old_value.split('\t')[1]
                        if '::' in new_name:
                            new_name = new_name.split('::')[0]
                        if new_name.startswith('http'):
                            new_name = new_name.rsplit('/')[-1]
                            new_name = urllib.parse.unquote(new_name)
                        new_value = new_name + '\t' + old_name
                        ui.epn_arr_list[row] = new_value
                        listitem = self.item(row)
                        if listitem:
                            listitem.setText(new_name)
                        write_files(file_path, ui.epn_arr_list, line_by_line=True)
                elif mode == 'default_all':
                    for row, val in enumerate(ui.epn_arr_list):
                        old_value = val
                        if '\t' in old_value:
                            new_name = old_name = old_value.split('\t')[1]
                            if '::' in new_name:
                                new_name = new_name.split('::')[0]
                            if new_name.startswith('http'):
                                new_name = new_name.rsplit('/')[-1]
                                new_name = urllib.parse.unquote(new_name)
                            new_value = new_name + '\t' + old_name
                            ui.epn_arr_list[row] = new_value
                            listitem = self.item(row)
                            if listitem:
                                listitem.setText(new_name)
                    write_files(file_path, ui.epn_arr_list, line_by_line=True)
    
    def edit_name_in_group(self, row):
        site = ui.get_parameters_value(s='site')['site']
        start_point = row
        end_point = len(ui.epn_arr_list)
        default_text = 'Episode-{'+str(row)+'-'+str(end_point-1)+'}'
        item, ok = QtWidgets.QInputDialog.getText(
            MainWindow, 'Input Dialog', 'Enter Naming pattern', 
            QtWidgets.QLineEdit.Normal, default_text)
        if item and ok:
            try:
                nmval = re.search('[^\{]*', item).group()
                nmval2 = re.search('\}[^"]*', item).group()
                nmval2 = re.sub('\}', '', nmval2, 1)
                range_val = re.search('\{[^}]*', item).group()
                range_val = re.sub('\{', '', range_val)
                range_start, range_end = range_val.split('-')
                range_start = int(range_start.strip())
                range_end = int(range_end.strip())
                if range_end > 100:
                    size = 3
                else:
                    size = 2
                error_in_processing = False
            except Exception as err:
                print(err, '--141---')
                error_in_processing = True
            
            if error_in_processing:
                msg = 'Bad Input Data Entered. Enter in format: NewName{start-end}'
                send_notification(msg)
            elif site.lower() == 'video':
                video_db = os.path.join(home, 'VideoDB', 'Video.db')
                conn = sqlite3.connect(video_db)
                cur = conn.cursor()
                end_point = len(ui.epn_arr_list)
                new_row = range_start
                for row in range(start_point, end_point):
                    old_value = ui.epn_arr_list[row]
                    path = old_value.split('	')[1]
                    if size == 2:
                        if new_row < 10:
                            new_name = '{0}0{1}{2}'.format(nmval, new_row, nmval2)
                        else:
                            new_name = nmval + str(new_row) + nmval2
                    elif size == 3:
                        if new_row < 10:
                            new_name = '{0}00{1}{2}'.format(nmval, new_row, nmval2)
                        elif new_row >= 10 and new_row < 100:
                            new_name = '{0}0{1}{2}'.format(nmval, new_row, nmval2)
                        else:
                            new_name = nmval + str(new_row) + nmval2
                    qr = 'Update Video Set EP_NAME=? Where Path=?'
                    cur.execute(qr, (new_name, path))
                    tmp = re.sub('[^	]*', new_name, old_value, 1)
                    ui.epn_arr_list[row] = tmp
                    listitem = ui.list2.item(row)
                    if listitem:
                        listitem.setText(new_name)
                    new_row = new_row + 1
                    if new_row > range_end:
                        break
                conn.commit()
                conn.close()
                old_value = ui.epn_arr_list[start_point]
                path = old_value.split('	')[1]
                dir_path, file_path = os.path.split(path)
                if dir_path in ui.video_dict:
                    del ui.video_dict[dir_path]
            elif (site.lower() == 'playlists' or site.lower() == 'music' 
                    or site.lower() == 'none'):
                msg = 'Batch Renaming not allowed in Music and Playlist section'
                send_notification(msg)
            else:
                file_path = ''
                param_dict = ui.get_parameters_value(s='siteName', n='name')
                siteName = param_dict['siteName']
                name = param_dict['name']
                if site.lower() == "subbedanime" or site == "dubbedanime":
                    file_path = os.path.join(home, 'History', site, siteName, name, 'Ep.txt')
                else:
                    file_path = os.path.join(home, 'History', site, name, 'Ep.txt')
                if os.path.isfile(file_path):
                    end_point = len(ui.epn_arr_list)
                    new_row = range_start
                    for row in range(start_point, end_point):
                        old_value = ui.epn_arr_list[row]
                        if '\t' in old_value:
                            path = old_value.split('\t')[1]
                        else:
                            path = old_value
                        if size == 2:
                            if new_row < 10:
                                new_name = '{0}0{1}{2}'.format(nmval, new_row, nmval2)
                            else:
                                new_name = nmval + str(new_row) + nmval2
                        elif size == 3:
                            if new_row < 10:
                                new_name = '{0}00{1}{2}'.format(nmval, new_row, nmval2)
                            elif new_row >= 10 and new_row < 100:
                                new_name = '{0}0{1}{2}'.format(nmval, new_row, nmval2)
                            else:
                                new_name = nmval + str(new_row) + nmval2
                        if '\t' in old_value:
                            tmp = re.sub('[^	]*', new_name, old_value, 1)
                        else:
                            tmp = new_name + '\t' + old_value
                        ui.epn_arr_list[row] = tmp
                        listitem = ui.list2.item(row)
                        if listitem:
                            listitem.setText(new_name)
                        new_row = new_row + 1
                        if new_row > range_end:
                            break
                    write_files(file_path, ui.epn_arr_list, line_by_line=True)
                    
    def keyPressEvent(self, event):
        if (event.modifiers() == QtCore.Qt.ControlModifier 
                and event.key() == QtCore.Qt.Key_Left):
            ui.tab_5.setFocus()
        elif (event.key() == QtCore.Qt.Key_F2):
            if ui.epn_arr_list:
                print('F2 Pressed')
                if self.currentItem():
                    self.edit_name_list2(self.currentRow())
        elif (event.key() == QtCore.Qt.Key_F3):
            if ui.epn_arr_list:
                print('F3 Pressed')
                if self.currentItem():
                    self.edit_name_in_group(self.currentRow())
        elif (event.key() == QtCore.Qt.Key_F4):
            if ui.epn_arr_list:
                print('Default Name')
                if self.currentItem():
                    self.get_default_name(self.currentRow(), mode='default')
        elif (event.key() == QtCore.Qt.Key_F5):
            if ui.epn_arr_list:
                print('Batch Renaming in database')
                if self.currentItem():
                    self.get_default_name(self.currentRow(), mode='default_all')
        elif (event.key() == QtCore.Qt.Key_F6):
            if self.currentItem():
                self.find_info(0)
        elif (event.key() == QtCore.Qt.Key_F7):
            if self.currentItem():
                self.find_info(1)
        elif (event.modifiers() == QtCore.Qt.ControlModifier 
                and event.key() == QtCore.Qt.Key_Up):
            self.setCurrentRow(0)
        elif (event.modifiers() == QtCore.Qt.ControlModifier 
                and event.key() == QtCore.Qt.Key_Down):
            self.setCurrentRow(self.count()-1)
        elif (event.modifiers() == QtCore.Qt.ControlModifier 
                and event.key() == QtCore.Qt.Key_D):
            item, ok = QtWidgets.QInputDialog.getText(
                MainWindow, 'Input Dialog', 'Enter Upload Speed in KB\n0 means unlimited', 
                QtWidgets.QLineEdit.Normal, str(ui.setuploadspeed))
            if item and ok:
                if item.isnumeric():
                    ui.setuploadspeed = int(item)
                else:
                    send_notification('wrong values')
        elif event.key() == QtCore.Qt.Key_Return:
            ui.epnClicked(dock_check=True)
        elif event.key() == QtCore.Qt.Key_Backspace:
            if ui.list1.isHidden() and ui.list1.count() > 0:
                ui.list2.hide()
                ui.goto_epn.hide()
                ui.list1.show()
                ui.list1.setFocus()
                show_hide_playlist = 0
                show_hide_titlelist = 1
                ui.set_parameters_value(show_hide_pl=show_hide_playlist,
                                        show_hide_tl=show_hide_titlelist)
        elif event.key() == QtCore.Qt.Key_Down:
            nextr = self.currentRow() + 1
            if nextr == self.count():
                self.downcount += 1
                if self.downcount > self.count_limit:
                    self.setCurrentRow(0)
                    self.downcount = 0
            else:
                self.downcount = 0
                self.setCurrentRow(nextr)
        elif event.key() == QtCore.Qt.Key_Up:
            prev_r = self.currentRow() - 1
            if prev_r == -1:
                self.upcount += 1
                if self.upcount > self.count_limit:
                    self.setCurrentRow(self.count()-1)
                    self.upcount = 0
            else:
                self.upcount = 0
                self.setCurrentRow(prev_r)
        elif event.key() == QtCore.Qt.Key_W:
            ui.watchToggle()
        elif (event.modifiers() == QtCore.Qt.ControlModifier and 
                event.key() == QtCore.Qt.Key_Q):
            self.queue_item()
        elif event.key() == QtCore.Qt.Key_Delete:
            param_dict = ui.get_parameters_value(s='site', b='bookmark', o='opt')
            site = param_dict['site']
            bookmark = param_dict['bookmark']
            opt = param_dict['opt']
            if site == 'None':
                print("Nothing To Delete")
            elif site == "Video":
                r = self.currentRow()
                item = self.item(r)
                if item:
                    if not bookmark:
                        video_db = os.path.join(home, 'VideoDB', 'Video.db')
                        conn = sqlite3.connect(video_db)
                        cur = conn.cursor()
                        txt = ui.epn_arr_list[r].split('	')[1]
                        cur.execute('Delete FROM Video Where Path=?', (txt, ))
                        logger.info('Deleting Directory From Database : '+txt)
                        del ui.epn_arr_list[r]
                        conn.commit()
                        conn.close()
                        self.takeItem(r)
                        del item
                        dir_path, file_path = os.path.split(txt)
                        if dir_path in ui.video_dict:
                            del ui.video_dict[dir_path]
            elif (site != "PlayLists" and site != "Video" and site != "Music" 
                    and opt == "History"):
                row = self.currentRow()
                file_path = ""
                param_dict = ui.get_parameters_value(sn='siteName', nm='name')
                siteName = param_dict['siteName']
                name = param_dict['name']
                if site == "SubbedAnime" or site == "DubbedAnime":
                    if os.path.exists(os.path.join(home, 'History', site, siteName, name, 'Ep.txt')):
                        file_path = os.path.join(home, 'History', site, siteName, name, 'Ep.txt')
                else:
                    if os.path.exists(os.path.join(home, 'History', site, name, 'Ep.txt')):
                        file_path = os.path.join(home, 'History', site, name, 'Ep.txt')
                if file_path and ui.epn_arr_list:
                    item = self.item(row)
                    self.takeItem(row)
                    del ui.epn_arr_list[row]
                    del item
                    write_files(file_path, ui.epn_arr_list, line_by_line=True)
                    ui.update_list2()
                else:
                    pass
            elif site == "PlayLists" or (site == "Music" and ui.list3.currentItem()):
                go_next = True
                if site == 'Music' and ui.list3.currentItem():
                    if ui.list3.currentItem().text() == "Playlist":
                        go_next = True
                    else:
                        go_next = False
                if go_next:
                    pls = ''
                    if site == "Music":
                        r = ui.list1.currentRow()
                        if ui.list1.item(r):
                            pls = str(ui.list1.item(r).text())
                    else:
                        if ui.list1.currentItem():
                            pls = ui.list1.currentItem().text()
                    if pls:
                        file_path = os.path.join(home, 'Playlists', pls)
                        row = self.currentRow()
                        item = self.item(row)
                        if item and os.path.exists(file_path):
                            self.takeItem(row)
                            del item
                            del ui.epn_arr_list[row]
                            write_files(file_path, ui.epn_arr_list, line_by_line=True)
        elif event.key() == QtCore.Qt.Key_PageUp:
            row = self.currentRow()
            nRow = self.currentRow()-1
            param_dict = ui.get_parameters_value(s='site', o='opt', b='bookmark')
            site = param_dict['site']
            opt = param_dict['opt']
            bookmark = param_dict['bookmark']
            if site == 'Music':
                if ui.list3.currentItem():
                    if ui.list3.currentItem().text() == 'Playlist':
                        opt = 'History'
                        ui.set_parameters_value(op=opt)
            print(opt, row, site)
            if (opt == "History" or site == "PlayLists") and row > 0 and site != "Video":
                file_path = ""
                param_dict = ui.get_parameters_value(sn='siteName', nm='name')
                siteName = param_dict['siteName']
                name = param_dict['name']
                if site == "SubbedAnime" or site == "DubbedAnime":
                    if os.path.exists(os.path.join(home, 'History', site, siteName, name, 'Ep.txt')):
                        file_path = os.path.join(home, 'History', site, siteName, name, 'Ep.txt')
                elif site == "PlayLists" or site == "Music":
                    pls = ''
                    if site == "PlayLists":
                        if ui.list1.currentItem():
                            pls = ui.list1.currentItem().text()
                    else:
                        if ui.list1.currentItem():
                            pls = ui.list1.currentItem().text()
                    if pls:
                        file_path = os.path.join(home, 'Playlists', pls)
                else:
                    if os.path.exists(os.path.join(home, 'History', site, name, 'Ep.txt')):
                        file_path = os.path.join(home, 'History', site, name, 'Ep.txt')
                if os.path.exists(file_path):
                    lines = open_files(file_path, True)
                    length = len(lines)
                    if row == length - 1:
                        t = lines[row].replace('\n', '')+'\n'
                        lines[row] = lines[nRow].replace('\n', '')
                        lines[nRow] = t
                    else:
                        t = lines[row]
                        lines[row] = lines[nRow]
                        lines[nRow] = t
                    ui.epn_arr_list[:] = []
                    for i in lines:
                        j = i.strip()
                        ui.epn_arr_list.append(j)
                    write_files(file_path, lines, line_by_line=True)
                    ui.update_list2()
                    self.setCurrentRow(nRow)
            elif site == "Video":
                r = self.currentRow()
                item = self.item(r)
                bookmark = ui.get_parameters_value(b='bookmark')['bookmark']
                if item:
                    if not bookmark:
                        video_db = os.path.join(home, 'VideoDB', 'Video.db')
                        conn = sqlite3.connect(video_db)
                        cur = conn.cursor()
                        if r > 0:
                            txt = ui.epn_arr_list[r].split('	')[1]
                            cur.execute('Select EPN FROM Video Where Path=?', (txt, ))
                            rows = cur.fetchall()
                            num1 = int(rows[0][0])
                            txt1 = ui.epn_arr_list[r-1].split('	')[1]
                            ui.epn_arr_list[r], ui.epn_arr_list[r-1] = ui.epn_arr_list[r-1], ui.epn_arr_list[r]
                            cur.execute('Select EPN FROM Video Where Path=?', (txt1, ))
                            rows = cur.fetchall()
                            num2 = int(rows[0][0])
                            print(num2, '---num2')
                            qr = 'Update Video Set EPN=? Where Path=?'
                            cur.execute(qr, (num2, txt))
                            qr = 'Update Video Set EPN=? Where Path=?'
                            cur.execute(qr, (num1, txt1))
                            conn.commit()
                            conn.close()
                            self.takeItem(r)
                            self.insertItem(r-1, item)
                            row_n = r-1
                        else:
                            txt = ui.epn_arr_list[-1].split('	')[1]
                            length = len(ui.epn_arr_list)
                            for row, row_item in enumerate(ui.epn_arr_list):
                                txt = row_item.split('\t')[1]
                                num = row - 1
                                if num < 0:
                                    num = num % length
                                print(num, '---num2')
                                qr = 'Update Video Set EPN=? Where Path=?'
                                cur.execute(qr, (num, txt))
                            first_txt = ui.epn_arr_list[0]
                            del ui.epn_arr_list[0]
                            ui.epn_arr_list.append(first_txt)
                            conn.commit()
                            conn.close()
                            self.takeItem(r)
                            self.addItem(item)
                            row_n = len(ui.epn_arr_list)-1
                        self.setCurrentRow(row_n)
                        dir_path, file_path = os.path.split(txt)
                        if dir_path in ui.video_dict:
                            del ui.video_dict[dir_path]
        elif event.key() == QtCore.Qt.Key_PageDown:
            row = self.currentRow()
            nRow = self.currentRow()+1
            param_dict = ui.get_parameters_value(s='site', o='opt', b='bookmark')
            site = param_dict['site']
            opt = param_dict['opt']
            bookmark = param_dict['bookmark']
            if site == 'Music':
                if ui.list3.currentItem():
                    if ui.list3.currentItem().text() == 'Playlist':
                        opt = 'History'
                        ui.set_parameters_value(op=opt)
            print(opt, row, site)
            if ((opt == "History" or site == "PlayLists") 
                    and row < self.count()-1 and site != "Video"):
                file_path = ""
                param_dict = ui.get_parameters_value(s='siteName', n='name')
                siteName = param_dict['siteName']
                name = param_dict['name']
                if site == "SubbedAnime" or site == "DubbedAnime":
                    if os.path.exists(os.path.join(home, 'History', site, siteName, name, 'Ep.txt')):
                        file_path = os.path.join(home, 'History', site, siteName, name, 'Ep.txt')
                elif site == "PlayLists" or site == "Music":
                    if site == "PlayLists":
                        pls = ui.list1.currentItem().text()
                    else:
                        pls = ui.list1.currentItem().text()
                    file_path = os.path.join(home, 'Playlists', pls)
                else:
                    if os.path.exists(os.path.join(home, 'History', site, name, 'Ep.txt')):
                        file_path = os.path.join(home, 'History', site, name, 'Ep.txt')
                if os.path.exists(file_path):
                    lines = open_files(file_path, True)
                    length = len(lines)
                    if nRow == length - 1:
                        t = lines[row].replace('\n', '')
                        lines[row] = lines[nRow].replace('\n', '')+'\n'
                        lines[nRow] = t
                    else:
                        t = lines[row]
                        lines[row] = lines[nRow]
                        lines[nRow] = t
                    ui.epn_arr_list[:] = []
                    for i in lines:
                        j = i.strip()
                        ui.epn_arr_list.append(j)
                    write_files(file_path, lines, line_by_line=True)
                    ui.update_list2()
                    self.setCurrentRow(nRow)
            elif site == "Video":
                r = self.currentRow()
                item = self.item(r)
                if item:
                    if not bookmark:
                        video_db = os.path.join(home, 'VideoDB', 'Video.db')
                        conn = sqlite3.connect(video_db)
                        cur = conn.cursor()
                        if r < len(ui.epn_arr_list) - 1:
                            txt = ui.epn_arr_list[r].split('	')[1]
                            cur.execute('Select EPN FROM Video Where Path=?', (txt, ))
                            rows = cur.fetchall()
                            num1 = int(rows[0][0])
                            print(num1, '--num1')
                            print(self.count()-1, '--cnt-1')
                            txt1 = ui.epn_arr_list[r+1].split('	')[1]
                            ui.epn_arr_list[r], ui.epn_arr_list[r+1] = ui.epn_arr_list[r+1], ui.epn_arr_list[r]
                            cur.execute('Select EPN FROM Video Where Path=?', (txt1, ))
                            rows = cur.fetchall()
                            num2 = int(rows[0][0])
                            print(num2, '---num2')
                            qr = 'Update Video Set EPN=? Where Path=?'
                            cur.execute(qr, (num2, txt))
                            qr = 'Update Video Set EPN=? Where Path=?'
                            cur.execute(qr, (num1, txt1))
                            conn.commit()
                            conn.close()
                            self.takeItem(r)
                            self.insertItem(r+1, item)
                            row_n = r+1
                        else:
                            length = len(ui.epn_arr_list)
                            txt = ui.epn_arr_list[0].split('\t')[1]
                            for row, row_item in enumerate(ui.epn_arr_list):
                                txt = row_item.split('\t')[1]
                                num = row+1
                                if num >= length:
                                    num = num % length
                                print(num, '---num2')
                                qr = 'Update Video Set EPN=? Where Path=?'
                                cur.execute(qr, (num, txt))
                            last_txt = ui.epn_arr_list[-1]
                            del ui.epn_arr_list[-1]
                            ui.epn_arr_list.insert(0, last_txt)
                            self.takeItem(r)
                            self.insertItem(0, item)
                            conn.commit()
                            conn.close()
                            #ui.update_list2()
                            row_n = 0
                        self.setCurrentRow(row_n)
                        dir_path, file_path = os.path.split(txt)
                        if dir_path in ui.video_dict:
                            del ui.video_dict[dir_path]
        elif event.key() == QtCore.Qt.Key_Left:
            if ui.float_window.isHidden():
                if ui.list1.isHidden():
                    ui.list1.show()
                ui.list1.setFocus()
            else:
                prev_r = self.currentRow() - 1
                if self.currentRow() == 0:
                    self.setCurrentRow(0)
                else:
                    self.setCurrentRow(prev_r)
        elif event.key() == QtCore.Qt.Key_Right:
            if ui.float_window.isHidden():
                pass
            else:
                nextr = self.currentRow() + 1
                if nextr == self.count():
                    self.setCurrentRow(self.count()-1)
                else:
                    self.setCurrentRow(nextr)
            if ui.auto_hide_dock:
                ui.dockWidget_3.hide()
        elif (event.modifiers() == QtCore.Qt.ControlModifier and 
                event.key() == QtCore.Qt.Key_O):
            self.init_offline_mode()
        elif event.key() == QtCore.Qt.Key_2: 
            mirrorNo = 2
            msg = "Mirror No. 2 Selected"
            ui.set_parameters_value(mir=mirrorNo)
            send_notification(msg)
        elif event.key() == QtCore.Qt.Key_4: 
            mirrorNo = 4
            msg = "Mirror No. 4 Selected"
            send_notification(msg)
            ui.set_parameters_value(mir=mirrorNo)
        elif event.key() == QtCore.Qt.Key_5: 
            mirrorNo = 5
            msg = "Mirror No. 5 Selected"
            send_notification(msg)
            ui.set_parameters_value(mir=mirrorNo)
        elif event.key() == QtCore.Qt.Key_3: 
            mirrorNo = 3
            msg = "Mirror No. 3 Selected"
            send_notification(msg)
            ui.set_parameters_value(mir=mirrorNo)
        elif event.key() == QtCore.Qt.Key_1: 
            mirrorNo = 1
            msg = "Mirror No. 1 Selected"
            send_notification(msg)
            ui.set_parameters_value(mir=mirrorNo)
        elif event.key() == QtCore.Qt.Key_6: 
            mirrorNo = 6
            msg = "Mirror No. 6 Selected"
            send_notification(msg)
            ui.set_parameters_value(mir=mirrorNo)
        elif event.key() == QtCore.Qt.Key_7: 
            mirrorNo = 7
            msg = "Mirror No. 7 Selected"
            send_notification(msg)
            ui.set_parameters_value(mir=mirrorNo)
        elif event.key() == QtCore.Qt.Key_8: 
            mirrorNo = 8
            msg = "Mirror No. 8 Selected"
            send_notification(msg)
            ui.set_parameters_value(mir=mirrorNo)
        elif event.key() == QtCore.Qt.Key_9: 
            mirrorNo = 9
            msg = "Mirror No. 9 Selected"
            send_notification(msg)
            ui.set_parameters_value(mir=mirrorNo)
        elif event.key() == QtCore.Qt.Key_F and ui.mpvplayer_val.processId() > 0:
            if not MainWindow.isHidden():
                param_dict = ui.get_parameters_value(w='wget', v='video_local_stream',
                                                     t='total_till')
                wget = param_dict['wget']
                video_local_stream = param_dict['video_local_stream']
                total_till = param_dict['total_till']
                if not MainWindow.isFullScreen():
                    ui.gridLayout.setSpacing(0)
                    ui.superGridLayout.setSpacing(0)
                    ui.gridLayout.setContentsMargins(0, 0, 0, 0)
                    ui.superGridLayout.setContentsMargins(0, 0, 0, 0)
                    ui.text.hide()
                    ui.label.hide()
                    ui.frame1.hide()
                    ui.tab_6.hide()
                    ui.goto_epn.hide()
                    #ui.btn20.hide()
                    if wget.processId() > 0 or video_local_stream:
                        ui.progress.hide()
                        if not ui.torrent_frame.isHidden():
                            ui.torrent_frame.hide()
                    ui.list2.hide()
                    ui.list6.hide()
                    ui.list1.hide()
                    ui.frame.hide()
                    ui.tab_5.show()
                    ui.tab_5.setFocus()
                    if (ui.player_val == "mplayer" or ui.player_val == "mpv"):
                        MainWindow.setCursor(QtGui.QCursor(QtCore.Qt.BlankCursor))
                    MainWindow.showFullScreen()
                else:
                    ui.gridLayout.setSpacing(5)
                    ui.superGridLayout.setSpacing(0)
                    ui.superGridLayout.setContentsMargins(5, 5, 5, 5)
                    ui.list2.show()
                    ui.btn20.show()
                    if wget:
                        if wget.processId() > 0:
                            ui.goto_epn.hide()
                            ui.progress.show()

                    ui.frame1.show()
                    if ui.player_val == "mplayer" or ui.player_val == "mpv":
                        MainWindow.setCursor(QtGui.QCursor(QtCore.Qt.ArrowCursor))
                    MainWindow.showNormal()
                    MainWindow.showMaximized()
                    if total_till != 0:
                        ui.tab_6.show()
                        ui.list2.hide()
                        ui.goto_epn.hide()
            else:
                if not ui.float_window.isHidden():
                    if not ui.float_window.isFullScreen():
                        ui.float_window.showFullScreen()
                    else:
                        ui.float_window.showNormal()
        else:
            super(PlaylistWidget, self).keyPressEvent(event)
    
    def name_adjust(self, name):
        nam = re.sub('-|_| ', '+', name)
        nam = nam.lower()
        nam = re.sub('\[[^\]]*\]|\([^\)]*\)', '', nam)
        nam = re.sub(
            '\+sub|\+dub|subbed|dubbed|online|720p|1080p|480p|.mkv|.mp4|', '', nam)
        nam = nam.strip()
        return nam
        
    def get_ddglinks(self, nam, src=None):
        m = []
        if src == 'tmdb' or src == 'tmdb+ddg':
            new_url = 'https://duckduckgo.com/html/?q='+nam+'+themoviedb'
        else:
            new_url = 'https://duckduckgo.com/html/?q='+nam+'+tvdb'
        content = ccurl(new_url)
        soup = BeautifulSoup(content, 'lxml')
        div_val = soup.findAll('h2', {'class':'result__title'})
        logger.info(div_val)
        for div_l in div_val:
            new_url = div_l.find('a')
            if 'href' in str(new_url):
                new_link = new_url['href']
                final_link = re.search('http[^"]*', new_link).group()
                if src == 'tmdb' or src == 'tmdb+ddg':
                    if 'themoviedb.org' in final_link:
                        m.append(final_link)
                else:
                    if ('tvdb.com' in final_link and 'tab=episode' not in final_link 
                            and 'tab=seasonall' not in final_link):
                        m.append(final_link)
                if m:
                    break
        return m
        
    def get_glinks(self, nam, src=None):
        if src == 'tmdb+g':
            url = "https://www.google.co.in/search?q="+nam+"+themoviedb"
        else:
            url = "https://www.google.co.in/search?q="+nam+"+tvdb"
        content = ccurl(url)
        soup = BeautifulSoup(content, 'lxml')
        m = soup.findAll('a')
        links = []
        for i in m:
            if 'href' in str(i):
                x = urllib.parse.unquote(i['href'])
                y = ''
                src = 'tvdb'
                if 'thetvdb.com' in x:
                    y = re.search('thetvdb.com[^"]*tab=series[^"]*', x)
                    src = 'tvdb'
                elif 'themoviedb.org' in x:
                    y = re.search('www.themoviedb.org[^"]*', x)
                    src = 'tmdb'
                if y:
                    y = y.group()
                    if src == 'tvdb':
                        y = 'http://'+y
                    else:
                        y = 'https://'+y
                    y = urllib.parse.unquote(y)
                    y = y.replace(' ', '%20')
                    y = re.sub('\&sa[^"]*', '', y)
                    links.append(y)
        return links
        
    def find_info(self, mode):
        param_dict = ui.get_parameters_value(n='name')
        name = param_dict['name']
        nam = self.name_adjust(name)
        nam1 = nam
        logger.info(nam)
        index = ""
        final_link_found = False
        final_link_arr = []
        if mode == 0:
            link = "http://thetvdb.com/index.php?seriesname="+nam+"&fieldlocation=1&language=7&genre=Animation&year=&network=&zap2it_id=&tvcom_id=&imdb_id=&order=translation&addedBy=&searching=Search&tab=advancedsearch"
            logger.info(link)
            content = ccurl(link)
            m = re.findall('/index.php[^"]tab=[^"]*', content)
            if not m:
                link = "http://thetvdb.com/index.php?seriesname="+nam+"&fieldlocation=2&language=7&genre=Animation&year=&network=&zap2it_id=&tvcom_id=&imdb_id=&order=translation&addedBy=&searching=Search&tab=advancedsearch"
                content = ccurl(link)
                m = re.findall('/index.php[^"]tab=[^"]*', content)
                if not m:
                    link = "http://thetvdb.com/?string="+nam+"&searchseriesid=&tab=listseries&function=Search"
                    content = ccurl(link)
                    m = re.findall('/[^"]tab=series[^"]*lid=7', content)
                    if not m:
                        final_link_found = False
                    else:
                        final_link_found = True
                        final_link_arr = m
                else:
                    final_link_found = True
                    final_link_arr = m
            else:
                final_link_found = True
                final_link_arr = m
        elif mode == 1:
            final_link_arr = self.get_ddglinks(nam)
            if final_link_arr:
                final_link_found = True
        elif mode == 2:
            final_link_arr = self.get_glinks(nam)
            if final_link_arr:
                final_link_found = True
                
        logger.info(final_link_arr)
        if final_link_found and final_link_arr:
            n = re.sub('amp;', '', final_link_arr[0])
            elist = re.sub('tab=series', 'tab=seasonall', n)
            if not n.startswith('http'):
                url = "http://thetvdb.com" + n
                elist_url = "http://thetvdb.com" + elist
            else:
                url = n
                elist_url = elist
            site = ui.get_parameters_value(s='site')['site']
            ui.getTvdbEpnInfo(elist_url, epn_arr=ui.epn_arr_list,
                              site=site, name=name)

    def triggerPlaylist(self, value):
        print('Menu Clicked')
        print(value)
        file_path = os.path.join(home, 'Playlists', str(value))
        logger.info(file_path)
        site = ui.get_parameters_value(s='site')['site']
        if (site == "Music" or site == "Video" or site == "Local" 
                or site == "None" or site == 'PlayLists' or site == 'MyServer'):
            if os.path.exists(file_path):
                i = self.currentRow()
                sumr = ui.epn_arr_list[i].split('	')[0]
                try:
                    rfr_url = ui.epn_arr_list[i].split('	')[2]
                except:
                    rfr_url = "NONE"
                sumry = ui.epn_arr_list[i].split('	')[1]
                sumry = sumry.replace('"', '')
                sumry = '"'+sumry+'"'
                t = sumr+'	'+sumry+'	'+rfr_url
                write_files(file_path, t, line_by_line=True)
        else:
            param_dict = ui.get_parameters_value(f='finalUrlFound', r='refererNeeded')
            finalUrlFound = param_dict['finalUrlFound']
            refererNeeded = param_dict['refererNeeded']
            finalUrl = ui.epn_return(self.currentRow())
            t = ''
            sumr = self.item(self.currentRow()).text().replace('#', '', 1)
            sumr = sumr.replace(ui.check_symbol, '')
            if os.path.exists(file_path):
                if isinstance(finalUrl, list):
                    if finalUrlFound and refererNeeded:
                        rfr_url = finalUrl[1]
                        sumry = str(finalUrl[0])
                        t = sumr+'	'+sumry+'	'+rfr_url
                    else:
                        rfr_url = "NONE"
                        j = 1
                        t = ''
                        for i in finalUrl:
                            p = "-Part-"+str(j)
                            sumry = str(i)
                            if j == 1:
                                t = sumr+p+'	'+sumry+'	'+rfr_url
                            else:
                                t = t + '\n' + sumr+p+'	'+sumry+'	'+rfr_url
                            j = j+1
                else:
                    rfr_url = "NONE"
                    sumry = str(finalUrl)
                    t = sumr+'	'+sumry+'	'+rfr_url
                write_files(file_path, t, line_by_line=True)

    def fix_order(self):
        param_dict = ui.get_parameters_value(o='opt', s='site', b='bookmark',
                                             n='name')
        opt = param_dict['opt']
        site = param_dict['site']
        bookmark = param_dict['bookmark']
        name = param_dict['name']
        row = self.currentRow()
        item = self.item(row)
        if item:
            if site == "Video":
                if not bookmark:
                    video_db = os.path.join(home, 'VideoDB', 'Video.db')
                    conn = sqlite3.connect(video_db)
                    cur = conn.cursor()
                    for num in range(len(ui.epn_arr_list)):
                        txt = ui.epn_arr_list[num].split('	')[1]
                        qr = 'Update Video Set EPN=? Where Path=?'
                        cur.execute(qr, (num, txt))
                    conn.commit()
                    conn.close()
            elif site == "Music" and ui.list3.currentItem():
                go_next = True
                if ui.list3.currentItem().text() == "Playlist":
                    go_next = True
                else:
                    go_next = False
                if go_next:
                    pls = ''
                    file_path = ''
                    if ui.list1.currentItem():
                        pls = ui.list1.currentItem().text()
                    if pls:
                        file_path = os.path.join(home, 'Playlists', pls)
                    if os.path.exists(file_path):
                        write_files(file_path, ui.epn_arr_list, line_by_line=True)
            elif (opt == "History" or site == "PlayLists") and row > 0 and site != "Video":
                file_path = ""
                if site == "PlayLists":
                    if ui.list1.currentItem():
                        pls = ui.list1.currentItem().text()
                        file_path = os.path.join(home, 'Playlists', pls)
                elif site == "Local":
                    if os.path.exists(os.path.join(home, 'History', site, name, 'Ep.txt')):
                        file_path = os.path.join(home, 'History', site, name, 'Ep.txt')
                if os.path.exists(file_path):
                    abs_path = os.path.join(TMPDIR, 'tmp.txt')
                    logger.info('--file-path--{0}'.format(file_path))
                    writing_failed = False
                    if os.path.exists(file_path):
                        write_files(file_path, ui.epn_arr_list, line_by_line=True)
    
    def remove_thumbnails(self, row, row_item):
        dest = ui.get_thumbnail_image_path(row, row_item, only_name=True)
        if os.path.exists(dest):
            os.remove(dest)
            small_nm_1, new_title = os.path.split(dest)
            small_nm_2 = '128px.'+new_title
            small_nm_3 = '480px.'+new_title
            small_nm_4 = 'label.'+new_title
            new_small_thumb = os.path.join(small_nm_1, small_nm_2)
            small_thumb = os.path.join(small_nm_1, small_nm_3)
            small_label = os.path.join(small_nm_1, small_nm_4)
            logger.info(new_small_thumb)
            if os.path.exists(new_small_thumb):
                os.remove(new_small_thumb)
            if os.path.exists(small_thumb):
                os.remove(small_thumb)
            if os.path.exists(small_label):
                os.remove(small_label)
    
    def contextMenuEvent(self, event):
        param_dict = ui.get_parameters_value(s='site', n='name')
        site = param_dict['site']
        name = param_dict['name']
        if site == "Music":
            menu = QtWidgets.QMenu(self)
            submenuR = QtWidgets.QMenu(menu)
            submenuR.setTitle("Add To Playlist")
            menu.addMenu(submenuR)
            view_menu = QtWidgets.QMenu(menu)
            view_menu.setTitle("View Mode")
            menu.addMenu(view_menu)
            view_list = view_menu.addAction("List Mode (Default)")
            view_list_thumbnail = view_menu.addAction("List With Thumbnail")
            thumb = view_menu.addAction("Thumbnail Grid Mode (Shift+Z)")
            save_pls = menu.addAction('Save Current Playlist')
            go_to = menu.addAction("Go To Last.fm")
            qitem = menu.addAction("Queue Item (Ctrl+Q)")
            fix_ord = menu.addAction("Lock Order (Playlist Only)")
            pls = os.listdir(os.path.join(home, 'Playlists'))
            home_n = os.path.join(home, 'Playlists')
            pls = sorted(
                pls, key=lambda x: os.path.getmtime(os.path.join(home_n, x)), 
                reverse=True)
            j = 0
            item_m = []
            for i in pls:
                item_m.append(submenuR.addAction(i))
            submenuR.addSeparator()
            new_pls = submenuR.addAction("Create New Playlist")
            file_manager = menu.addAction("Open in File Manager")
            default = menu.addAction("Set Default Background")
            delPosters = menu.addAction("Delete Poster")
            delInfo = menu.addAction("Delete Info")
            thumb_menu = QtWidgets.QMenu(menu)
            thumb_menu.setTitle("Remove Thumbnails")
            menu.addMenu(thumb_menu)
            remove_all = thumb_menu.addAction("Remove All")
            remove_selected = thumb_menu.addAction("Remove Selected")
            
            action = menu.exec_(self.mapToGlobal(event.pos()))
            for i in range(len(item_m)):
                if action == item_m[i]:
                    self.triggerPlaylist(pls[i])
            if action == new_pls:
                print("creating")
                item, ok = QtWidgets.QInputDialog.getText(
                    MainWindow, 'Input Dialog', 'Enter Playlist Name')
                if ok and item:
                    file_path = os.path.join(home, 'Playlists', item)
                    if not os.path.exists(file_path):
                        f = open(file_path, 'w')
                        f.close()
            elif action == save_pls:
                    print("creating")
                    item, ok = QtWidgets.QInputDialog.getText(
                        MainWindow, 'Input Dialog', 'Enter New Playlist Name')
                    if ok and item:
                        file_path = os.path.join(home, 'Playlists', item)
                        write_files(file_path, ui.epn_arr_list, True)
            elif action == qitem:
                self.queue_item()
            elif action == view_list:
                ui.list2.setStyleSheet("""QListWidget{font: bold 12px;
                color:white;background:rgba(0, 0, 0, 30%);
                border:rgba(0, 0, 0, 30%);border-radius: 3px;}
                QListWidget:item {height: 30px;}
                QListWidget:item:selected:active {background:rgba(0, 0, 0, 20%);
                color: violet;}
                QListWidget:item:selected:inactive {border:rgba(0, 0, 0, 30%);}
                QMenu{font: bold 12px;color:black;
                background-image:url('1.png');}""")
                ui.list_with_thumbnail = False
                if not ui.float_window.isHidden():
                    if ui.new_tray_widget.cover_mode.text() == ui.player_buttons['down']: 
                        self.setMaximumHeight(30)
                    else:
                        self.setMaximumHeight(16777215)
                ui.update_list2()
            elif action == view_list_thumbnail:
                ui.list2.setStyleSheet("""QListWidget{font: bold 12px;
                color:white;background:rgba(0, 0, 0, 30%);
                border:rgba(0, 0, 0, 30%);border-radius: 3px;}
                QListWidget:item {height: 128px;}
                QListWidget:item:selected:active {background:rgba(0, 0, 0, 20%);
                color: violet;}
                QListWidget:item:selected:inactive {border:rgba(0, 0, 0, 30%);}
                QMenu{font: bold 12px;color:black;
                background-image:url('1.png');}""")
                ui.list_with_thumbnail = True
                if not ui.float_window.isHidden():
                    self.setMaximumHeight(16777215)
                ui.update_list2()
            elif action == thumb:
                if self.currentItem() and ui.float_window.isHidden():
                    ui.IconViewEpn()
                    ui.scrollArea1.setFocus()
            elif action == file_manager:
                if ui.epn_arr_list:
                    if self.currentItem():
                        self.open_in_file_manager(self.currentRow())
            elif action == go_to:
                if ui.list3.currentItem():
                    nam1 = ''
                    if str(ui.list3.currentItem().text()) == "Artist":
                        nam1 = str(ui.list1.currentItem().text())
                    else:
                        r = self.currentRow()
                        try:
                            nam1 = ui.epn_arr_list[r].split('	')[2]
                        except:
                            nam1 = ''
                    logger.info(nam1)
                    ui.reviewsWeb(srch_txt=nam1, review_site='last.fm', 
                                  action='search_by_name')
            elif action == fix_ord:
                self.fix_order()
            elif action == remove_all:
                for i, j in enumerate(ui.epn_arr_list):
                    self.remove_thumbnails(i ,j)
            elif action == remove_selected:
                r = self.currentRow()
                self.remove_thumbnails(r ,ui.epn_arr_list[r])
            elif action == delInfo or action == delPosters or action == default:
                if (ui.list3.currentItem()):
                    if str(ui.list3.currentItem().text()) == "Artist":
                        if '/' in name:
                            nam = name.replace('/', '-')
                        else:
                            nam = name
                    else:
                        try:
                            r = ui.list2.currentRow()
                            nam = ui.epn_arr_list[r].split('	')[2]
                        except:
                            nam = ""
                        if '/' in nam:
                            nam = nam.replace('/', '-')
                        else:
                            nam = nam
                    if nam:
                        picn = os.path.join(home, 'Music', 'Artist', nam, 'poster.jpg')
                        fanart = os.path.join(home, 'Music', 'Artist', nam, 'fanart.jpg')
                        default_wall = os.path.join(home, 'default.jpg')
                        sumr = os.path.join(home, 'Music', 'Artist', nam, 'bio.txt')
                        dir_n = os.path.join(home, 'Music', 'Artist', nam)
                        if os.path.exists(dir_n):
                            if action == delInfo:
                                m = os.listdir(dir_n)
                                for i in m:
                                    if i.endswith('.txt'):
                                        f = open(os.path.join(dir_n, 'bio.txt'), 'w')
                                        f.write('No Information Available')
                                        f.close()
                                m = os.listdir(TMPDIR)
                                for i in m:
                                    if i.endswith('.jpg') or i.endswith('.txt'):
                                        t = os.path.join(TMPDIR, i)
                                        os.remove(t)
                            elif action == delPosters:
                                m = os.listdir(dir_n)
                                for i in m:
                                    if i.endswith('.jpg') or i.endswith('256px') or i.endswith('128px'):
                                        os.remove(os.path.join(dir_n, i))
                                m = os.listdir(TMPDIR)
                                for i in m:
                                    if i.endswith('.jpg') or i.endswith('.txt'):
                                        os.remove(os.path.join(TMPDIR, i)) 
                            elif action == default:
                                shutil.copy(default_wall, picn)
                                shutil.copy(default_wall, fanart)
                                ui.videoImage(
                                    picn, os.path.join(home, 'Music', 'Artist', 
                                    nam, 'thumbnail.jpg'), fanart, '')
        else:
            menu = QtWidgets.QMenu(self)
            submenuR = QtWidgets.QMenu(menu)
            submenuR.setTitle("Add To Playlist")
            menu.addMenu(submenuR)
            view_menu = QtWidgets.QMenu(menu)
            view_menu.setTitle("View Mode")
            menu.addMenu(view_menu)
            view_list = view_menu.addAction("List Mode (Default)")
            view_list_thumbnail = view_menu.addAction("List With Thumbnail")
            thumb = view_menu.addAction("Thumbnail Grid Mode (Shift+Z)")
            pls = os.listdir(os.path.join(home, 'Playlists'))
            home_n = os.path.join(home, 'Playlists')

            pls = sorted(
                pls, key=lambda x: os.path.getmtime(os.path.join(home_n, x)), 
                reverse=True)

            item_m = []
            for i in pls:
                item_m.append(submenuR.addAction(i))
            submenuR.addSeparator()
            new_pls = submenuR.addAction("Create New Playlist")
            r = self.currentRow()
            goto_web_mode = False
            offline_mode = False
            if ui.epn_arr_list and self.currentItem():
                epn_arr = ui.epn_arr_list[r].split('	')
                if len(epn_arr) > 2:
                    url_web = ui.epn_arr_list[r].split('	')[1]
                else:
                    url_web = 'none'
            else:
                url_web = 'none'
            save_pls_entry = None
            if 'youtube.com' in url_web:
                goto_web = menu.addAction('Open in Youtube Browser')
                goto_web_mode = True
            if (site.lower() == 'video' or site.lower() == 'local' 
                    or site.lower() == 'none' 
                    or site.lower().startswith('playlist')):
                save_pls = menu.addAction('Save Current Playlist')
                save_pls_entry = True
            if (site.lower() != 'video' and site.lower() != 'music' 
                    and site.lower() != 'local'):
                if (ui.btn1.currentText().lower() == 'addons' 
                        or url_web.startswith('http') 
                        or url_web.startswith('"http')):
                    start_offline = menu.addAction('Start In Offline Mode')
                    offline_mode = True
                    
            qitem = menu.addAction("Queue Item (Ctrl+Q)")
            fix_ord = menu.addAction("Lock Order")
            submenu = QtWidgets.QMenu(menu)
            submenu.setTitle('TVDB options')
            eplist_info = False
            if (site.lower() == 'video' or site.lower() == 'local'):
                eplist = submenu.addAction("Get Episode Title(TVDB) (F6)")
                eplist_info = True
            elif site.lower().startswith('playlist') or site.lower() == 'none':
                eplist_info = False
            else:
                eplist = submenu.addAction("Get Episode Thumbnails(TVDB)")
                eplist_info = True
            
            eplistM = QtWidgets.QAction("Go To TVDB", self)
            if site.lower() != 'playlists' and site.lower() != 'none':
                submenu.addAction(eplistM)
                menu.addMenu(submenu)
            file_manager = menu.addAction("Open in File Manager")
            rm_menu = QtWidgets.QMenu(menu)
            rm_menu.setTitle("Rename Options")
            editN = rm_menu.addAction("Rename Single Entry (F2)")
            group_rename = rm_menu.addAction("Rename in Group (F3)")
            default_name = rm_menu.addAction("Set Default Name (F4)")
            default_name_all = rm_menu.addAction("Set Default Name For All (F5)")
            menu.addMenu(rm_menu)
            thumb_menu = QtWidgets.QMenu(menu)
            thumb_menu.setTitle("Remove Thumbnails")
            menu.addMenu(thumb_menu)
            remove_all = thumb_menu.addAction("Remove All")
            remove_selected = thumb_menu.addAction("Remove Selected")
            upspeed = menu.addAction("Set Upload Speed (Ctrl+D)")
            action = menu.exec_(self.mapToGlobal(event.pos()))
            
            if self.currentItem():
                for i in range(len(item_m)):
                    if action == item_m[i]:
                        self.triggerPlaylist(pls[i])
            if offline_mode:
                if action == start_offline:
                    self.init_offline_mode()
            if goto_web_mode:
                if action == goto_web:
                    ui.reviewsWeb(srch_txt=url_web, review_site='yt', action='open')
            if save_pls_entry:
                if action == save_pls:
                    print("creating")
                    item, ok = QtWidgets.QInputDialog.getText(
                        MainWindow, 'Input Dialog', 'Enter Playlist Name')
                    if ok and item:
                        file_path = os.path.join(home, 'Playlists', item)
                        write_files(file_path, ui.epn_arr_list, True)
            if eplist_info:
                if action == eplist:
                    if self.currentItem():
                        self.find_info(0)
            if action == new_pls:
                print("creating")
                item, ok = QtWidgets.QInputDialog.getText(
                    MainWindow, 'Input Dialog', 'Enter Playlist Name')
                if ok and item:
                    file_path = os.path.join(home, 'Playlists', item)
                    if not os.path.exists(file_path):
                        f = open(file_path, 'w')
                        f.close()
            elif action == qitem:
                self.queue_item()
            elif action == upspeed:
                item, ok = QtWidgets.QInputDialog.getText(
                    MainWindow, 'Input Dialog', 'Enter Upload Speed in KB\n0 means unlimited', 
                    QtWidgets.QLineEdit.Normal, str(ui.setuploadspeed))
                if item and ok:
                    if item.isnumeric():
                        ui.setuploadspeed = int(item)
                    else:
                        send_notification('wrong values')
            elif action == view_list:
                ui.list2.setStyleSheet("""QListWidget{font: bold 12px;
                color:white;background:rgba(0, 0, 0, 30%);
                border:rgba(0, 0, 0, 30%);border-radius: 3px;}
                QListWidget:item {height: 30px;}
                QListWidget:item:selected:active {background:rgba(0, 0, 0, 20%);
                color: violet;}
                QListWidget:item:selected:inactive {border:rgba(0, 0, 0, 30%);}
                QMenu{font: bold 12px;color:black;
                background-image:url('1.png');}""")
                ui.list_with_thumbnail = False
                if not ui.float_window.isHidden():
                    if ui.new_tray_widget.cover_mode.text() == ui.player_buttons['down']: 
                        self.setMaximumHeight(30)
                    else:
                        self.setMaximumHeight(16777215)
                ui.update_list2()
            elif action == view_list_thumbnail:
                ui.list2.setStyleSheet("""QListWidget{font: bold 12px;
                color:white;background:rgba(0, 0, 0, 30%);border:rgba(0, 0, 0, 30%);
                border-radius: 3px;}
                QListWidget:item {height: 128px;}
                QListWidget:item:selected:active {background:rgba(0, 0, 0, 20%);
                color: violet;}
                QListWidget:item:selected:inactive {border:rgba(0, 0, 0, 30%);}
                QMenu{font: bold 12px;color:black;
                background-image:url('1.png');}""")
                ui.list_with_thumbnail = True
                if not ui.float_window.isHidden():
                    self.setMaximumHeight(16777215)
                ui.update_list2()
            elif action == remove_all:
                for i, j in enumerate(ui.epn_arr_list):
                    self.remove_thumbnails(i ,j)
            elif action == remove_selected:
                self.remove_thumbnails(r ,ui.epn_arr_list[r])
            elif action == editN and not ui.list1.isHidden():
                if ui.epn_arr_list:
                    print('Editing Name')
                    if self.currentItem():
                        self.edit_name_list2(self.currentRow())
            elif action == group_rename and not ui.list1.isHidden():
                if ui.epn_arr_list:
                    print('Batch Renaming in database')
                    if self.currentItem():
                        self.edit_name_in_group(self.currentRow())
            elif action == default_name and not ui.list1.isHidden():
                if ui.epn_arr_list:
                    print('Default Name')
                    if self.currentItem():
                        self.get_default_name(self.currentRow(), mode='default')
            elif action == default_name_all and not ui.list1.isHidden():
                if ui.epn_arr_list:
                    print('Batch Renaming in database')
                    if self.currentItem():
                        self.get_default_name(self.currentRow(), mode='default_all')
            elif action == file_manager:
                if ui.epn_arr_list:
                    if self.currentItem():
                        self.open_in_file_manager(self.currentRow())
            elif action == eplistM:
                if ui.list1.currentItem():
                    name1 = (ui.list1.currentItem().text())
                    ui.reviewsWeb(
                        srch_txt=name1, review_site='tvdb', action='search_by_name')
            elif action == thumb:
                if self.currentItem() and ui.float_window.isHidden():
                    ui.IconViewEpn()
                    ui.scrollArea1.setFocus()
            elif action == fix_ord:
                if self.currentItem():
                    self.fix_order()
