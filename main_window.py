import os
from tkinter import *
from tkinter.ttk import *
import tkinter.scrolledtext
import tkinter.messagebox
import re
import urllib
import json
from urllib import request
from urllib.error import URLError, HTTPError
import threading
import time


headers = {
    'Referer': 'http://appapi.jifenfu.net/pos/h5/weixin/barcode.html?phone=13680564447&orderId=2019121210552885685200',
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/79.0.3945.117 Safari/537.36'
}


class MainWindow(threading.Thread):
    def getCardNumber(self, str):
        cardNumber = re.findall('cardNumber=(.+?)$', str)
        if len(cardNumber) == 0:
            tkinter.messagebox.showwarning(title='错误', message='链接中需要包含cardNumber参数！')
            return None
        return cardNumber[0]

    def getPhoneNumber(self, str):
        phone = re.findall('phone=(.+?)&', str)
        if len(phone) == 0:
            tkinter.messagebox.showwarning(title='错误', message='链接中需要包含phone参数！')
            return None
        return phone[0]

    def getOrderId(self, str):
        orderId = re.findall('orderId=(.+?)$', str)
        if len(orderId) == 0:
            tkinter.messagebox.showwarning(title='错误', message='链接中需要包含orderId参数！')
            return None
        return orderId[0]

    def getNextUrl(self, url):
        try:
            headers['Referer'] = url
            time.sleep(5)
            req = urllib.request.Request(url, None, headers)
            resp = urllib.request.urlopen(req, timeout=10)
            return resp.geturl()
        except HTTPError as e:
            return None
        except URLError as e:
            return None

    def openUrl(self, url):
        try:
            time.sleep(5)
            req = urllib.request.Request(url, None, headers)
            resp = urllib.request.urlopen(req, timeout=10)
            status = resp.getcode()
            if status != 200:
                tkinter.messagebox.showwarning(title='错误', message='提取代码出错%d，可能是网络问题，也可能是接口已经改变！' % status)
                return None
            return resp.read().decode('utf-8')
        except HTTPError as e:
            return None
        except URLError as e:
            return None

    def getCouponList(self, jsonStr):
        obj = json.loads(jsonStr)
        coupons = obj['data']
        couponList = []
        for c in coupons:
            couponList.append(c['cardNumber'])
        return couponList

    def onResize(self, event):
        if event.widget == self.window:
            self.w, self.h = event.width, event.height
            self.resizeWidgets()

    def onClose(self):
        pass

    def run(self):
        self.btn1['state'] = tkinter.DISABLED
        self.text2.delete('0.0', 'end')
        originUrl: str = self.text1.get('0.0', 'end')
        urls = originUrl.splitlines(False)
        if len(originUrl) < 10 or len(urls) == 0:
            tkinter.messagebox.showwarning(title='提示', message='需要至少填写一个链接！')
            self.btn1['state'] = tkinter.NORMAL
            self.setError('错误，请至少填写一个链接')
            return
        self.current = 0
        self.total = 0
        self.succeed = 0
        self.failed = 0
        self.onProgress(0, 100)
        self.setError('正在计算总数...')
        for url in urls:
            url = url.replace('\t', ' ')
            cols = url.split(' ')
            if len(cols) < 1:
                continue
            url = cols[0]
            if url.startswith('http') is False:
                continue
            self.total += 1
        for url in urls:
            url = url.replace('\t', ' ')
            cols = url.split(' ')
            if len(cols) < 1:
                continue
            url = cols[0]
            if url.startswith('http') is False:
                continue
            self.current += 1
            self.setStatusBar(self.current, self.total, self.succeed, self.failed)
            # 获取302之后的url
            url = self.getNextUrl(url)
            if url is None:
                self.failed += 1
                continue
            if 'barcode.html?' in url:
                phone = self.getPhoneNumber(url)
                if phone is None:
                    self.failed += 1
                    continue
                orderId = self.getOrderId(url)
                if orderId is None:
                    self.failed += 1
                    continue
                headers['Referer'] = url
                url = r'http://appapi.jifenfu.net/pos/api/icommon/queryCardsV2.do?orderId=%s&phone=%s' % (orderId, phone)
                data = self.openUrl(url)
                if data is None:
                    self.failed += 1
                    continue
                coupons = self.getCouponList(data)
                self.text2.insert(tkinter.END, '\n'.join(coupons))
                self.text2.insert(tkinter.END, '\n')
                self.text2.see(tkinter.END)
                self.succeed += 1
                self.setStatusBar(self.current, self.total, self.succeed, self.failed)
            elif 'code_qrbr.html?' in url:
                headers['Referer'] = url
                cardNumber = self.getCardNumber(url)
                self.text2.insert(tkinter.END, cardNumber)
                self.text2.insert(tkinter.END, '\n')
                self.text2.see(tkinter.END)
                self.succeed += 1
                self.setStatusBar(self.current, self.total, self.succeed, self.failed)
            else:
                continue
        self.setStatusBar(self.current+1, self.total, self.succeed, self.failed)
        self.btn1['state'] = tkinter.NORMAL

    def onProgress(self, current, total):
        self.progress['maximum'] = total
        self.progress['value'] = current

    def setError(self, msg):
        self.strStatusCurrent.set(msg)
        self.resizeWidgets()

    def setStatusBar(self, current, total, succeed, failed):
        self.strStatusTotal.set('总数：%d' % total)
        self.strStatusSucceed.set('成功：%d' % succeed)
        self.strStatusFailed.set('失败：%d' % failed)
        if current > total:
            self.onProgress(total, total)
            self.strStatusCurrent.set('处理完成')
        else:
            self.onProgress(current-1, total)
            self.strStatusCurrent.set('正在处理第%d个' % current)

    def onProcess(self):
        t = threading.Thread.__init__(self)
        self.start()

    def resizeWidgets(self):
        # 输入
        padx = 10
        pady = 0
        self.lb1.place(x=padx, y=pady, width=60, height=35)
        padx = 10
        pady += 35
        width = self.w - padx - 10
        height = (self.h - pady - 30 - 70 - 20) / 2
        self.frm1.place(x=padx, y=pady, width=width, height=height)
        self.text1.pack(fill=tkinter.BOTH, expand=1)

        # 按钮
        pady += height + 5
        self.btn1.place(x=padx, y=pady, width=60, height=35)

        # 输出
        padx = 10
        pady += 35 + 5
        self.lb2.place(x=padx, y=pady, width=60, height=35)
        padx = 10
        pady += 35
        self.frm2.place(x=padx, y=pady, width=self.w - padx - 10, height=height)
        self.text2.pack(fill=tkinter.BOTH, expand=1)

        padx = 0
        pady = self.h - 25
        self.frmStatus.place(x=padx, y=pady, width=self.w, height=1)

        # 状态栏
        padx = self.w - 160
        pady = self.h - 24 + 4
        self.progress.place(x=padx, y=pady, width=150, height=24-8)

        padx = 10
        pady = self.h - 24  # 状态栏高24
        l = len(self.strStatusCurrent.get())
        w = l * 12 + 10
        self.lbStatusCurrent.place(x=padx, y=pady, width=w, height=24)
        if l == 0:
            return
        padx += w
        padx += 10
        self.sep1.place(x=padx, y=pady + 4, height=16)
        padx += 10
        l = len(self.strStatusTotal.get())
        w = l * 12 + 10
        self.lbStatusTotal.place(x=padx, y=pady, width=w, height=24)
        if l == 0:
            return
        padx += w + 10
        self.sep2.place(x=padx, y=pady + 4, height=16)
        padx += 10
        l = len(self.strStatusSucceed.get())
        w = l * 12 + 10
        self.lbStatusSucceed.place(x=padx, y=pady, width=w, height=24)
        if l == 0:
            return
        padx += w + 10
        self.sep3.place(x=padx, y=pady + 4, height=16)
        padx += 10
        l = len(self.strStatusFailed.get())
        w = l * 12 + 10
        self.lbStatusFailed.place(x=padx, y=pady, width=w, height=24)

    def popupMenu1(self, event):
        self.menu1.post(event.x_root, event.y_root)

    def popupMenu2(self, event):
        self.menu2.post(event.x_root, event.y_root)

    def onPaste(self):
        try:
            text = self.window.clipboard_get()
            n = self.text1.index(INSERT)
            self.text1.insert(n, text)
        except TclError:
            pass

    def onCopy(self):
        try:
            text = self.text2.get('0.0', END)
            self.window.clipboard_clear()
            self.window.clipboard_append(text)
        except TclError:
            pass


    def __init__(self):
        self.window = tkinter.Tk()
        # init
        self.current = 0
        self.total = 0
        self.succeed = 0
        self.failed = 0
        self.w = 700
        self.h = 400
        self.cx = self.window.winfo_screenwidth()
        self.cy = self.window.winfo_screenheight()
        self.window.title('批量提取券码 v1.0.1 by Autogensh')
        path = r'C:\server\git\urlbar'
        if hasattr(sys, '_MEIPASS'):
            path = sys._MEIPASS
        self.window.iconbitmap(os.path.join(path, r'icon.ico'))
        self.window.geometry('%dx%d+%d+%d' % (self.w, self.h, (self.cx-self.w)/2-20, (self.cy-self.h)/2-20))
        self.window.resizable()
        self.window.bind('<Configure>', self.onResize)
        style = Style()
        style.configure("red.TLabel", foreground='#f00')
        style.configure("blue.TLabel", foreground='#00f')
        style.configure("green.TLabel", foreground='#0f0')
        style.configure('red.TSeparator', background='red')
        style.configure('blue.TSeparator', background='blue')
        style.configure('green.TSeparator', background='green')
        self.menu1 = Menu(self.window, tearoff=0)
        self.menu1.add_command(label='粘贴', command=self.onPaste)
        self.menu2 = Menu(self.window, tearoff=0)
        self.menu2.add_command(label='复制到剪贴板', command=self.onCopy)
        self.lb1 = Label(self.window, text='输入链接：')
        self.frm1 = tkinter.Frame(self.window, highlightthickness=1, highlightcolor='#ccc', highlightbackground='#ccc')
        self.text1 = tkinter.scrolledtext.ScrolledText(self.frm1, relief=FLAT)
        self.text1.bind('<Button-3>', self.popupMenu1)
        self.btn1 = Button(self.window, text='开始提取', command=self.onProcess)
        self.lb2 = Label(self.window, text='提取结果：')
        self.frm2 = tkinter.Frame(self.window, highlightthickness=1, highlightcolor='#ccc', highlightbackground='#ccc')
        self.text2 = tkinter.scrolledtext.ScrolledText(self.frm2, relief=FLAT)
        self.text2.bind('<Button-3>', self.popupMenu2)
        self.frmStatus = tkinter.Frame(self.window, bg='#ccc')
        self.strStatusCurrent = StringVar()
        self.strStatusCurrent.set('当前：0')
        self.strStatusTotal = StringVar()
        self.strStatusTotal.set('总数：0')
        self.strStatusSucceed = StringVar()
        self.strStatusSucceed.set('成功：0')
        self.strStatusFailed = StringVar()
        self.strStatusFailed.set('失败：0')
        self.lbStatusCurrent = Label(self.window, textvariable=self.strStatusCurrent, anchor=tkinter.W)
        self.lbStatusTotal = Label(self.window, textvariable=self.strStatusTotal, anchor=tkinter.W, style='blue.TLabel')
        self.lbStatusSucceed = Label(self.window, textvariable=self.strStatusSucceed, anchor=tkinter.W, style='green.TLabel')
        self.lbStatusFailed = Label(self.window, textvariable=self.strStatusFailed, anchor=tkinter.W, style='red.TLabel')
        self.sep1 = Separator(self.window, orient=VERTICAL)
        self.sep2 = Separator(self.window, orient=VERTICAL)
        self.sep3 = Separator(self.window, orient=VERTICAL)
        self.progress = Progressbar(self.window, orient=HORIZONTAL, mode='determinate', maximum=100, value=0, length=100)
        self.resizeWidgets()
        self.window.mainloop()
