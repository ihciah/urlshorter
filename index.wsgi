# -*- coding: utf-8 -*-
#!/usr/bin/env python
#
#__author__= 'ihciah@gmail.com'
#__author__= 'BaiduID-ihciah'
#__author__= 'http://www.ihcblog.com'
#使用前需初始化Memcache、KVDB
import urllib2,urllib,web
web.config.debug = True
import time,json,base64
import sae.kvdb
from func import *
import pylibmc as memcache
urls=(
'/admin','Admin',
'/add','Addlink',
'/about','About',
'/check','Checklink',
'/','Home',
'/index\.html','Home',
'/login','Login',
'/help','Help',
'/logout','Logout',
'/i','Test',
'/checktextpwd','Checktextpwd',
'/shownote','Shownote',
r"\A/(.{3,30})\Z",'Jump',
r".*",'Er'
)
app = web.application(urls, globals())
render = web.template.render('html')

mc = memcache.Client()
store = MemStore(mc)
session = web.session.Session(app, store, initializer={'login': 0,'id':''})
infof={'toolong':'网址太长啦',
       'tooshort':'至少要写3位哦',
       'taken':'Oops!该地址已被使用...如果当时设置了密码,键入正确的密码可以覆盖哦',
       'nolink':'该链接不存在...敲错了没?',
       'blocked':'该地址为系统保留地址哦...',
       'blockedv2':'请不要包含被封锁的关键字哦~',
       'formaterror':'格式错误啦!'}
class utf8KVDB():
    def __init__(self):
        self.k=sae.kvdb.KVClient()
    def add(self,a,b):
        return self.k.add(a.encode('utf-8'),en(b))
    def replace(self,a,b):
        try:
            return self.k.replace(en(a),en(b))
        except:
            return None
    def get(self,a):
        try:
            return self.k.get(en(a))
        except:
            return None
    def delete(self,a):
        try:
            return self.k.delete(en(a))
        except:
            return None
    def set(self,a,b):
        try:
            return self.k.set(en(a),en(b))
        except:
            return None
    def get_by_prefix(self,prefix,limit,marker=None):
        try:
            if marker is not None:
                return self.k.get_by_prefix(en(prefix), limit=int(limit),marker=en(marker))
            else:
                return self.k.get_by_prefix(en(prefix), limit=int(limit))
        except:
            return None
    def get_multi(self,keys,key_prefix=''):
        try:
            return self.k.get_multi(en(keys),en(key_prefix))
        except:
            return None
kv = utf8KVDB()
class Login:
    def GET(self):
        if session.login==1:
            raise web.seeother('/admin')
        else:
            data=web.input(info=''.replace('<','&lt;').replace('>','&gt;'))
            return render.login(data.info)
    def POST(self):
        if session.login==1:
            raise web.seeother('/admin')
        data=web.input(uid='',pwd='')
        f=lambda x:x[:20]
        id=f(data.uid)
        pwd=f(data.pwd)
        r=kv.get(en('u'+id))
        if r is None:
            raise web.seeother('/login?info=e')#用户不存在-输出至页面?安全性
        if r!=pwd:
            raise web.seeother('/login?info=e')
        else:
            session.id=id
            session.login=1
            raise web.seeother('/admin')
class Logout:
    def GET(self):
        session.login=0
        raise web.seeother('/login?info=q')
class Home:
    def GET(self):
        alllink=kv.get('calllink') or 0
        allclick=kv.get('callclick') or 0
        return render.home(alllink,allclick,'')
class Help:
    def GET(self):
        alllink=kv.get('calllink') or 0
        allclick=kv.get('callclick') or 0
        return render.help(alllink,allclick)
class Addlink:
    #AJAX
    def POST(self):
        data=web.input(shorturl='',pwd='',url='',choose='url')
        if data.choose!='url':
            choose='text'#Avoid attack
        else:
            choose='url'
        f=lambda x:x[:30]
        shorturl=f(data.shorturl).replace("<",'').replace("?",'').replace("%",'')#防止通过短链进行XSS
        pwd=f(data.pwd)
        if choose=='url':
            url=data.url[:1000]
        else:
            url=data.url[:20000]#便笺条上限2W字？KVDB好像最大4M
            choose='text'
        (surl,pwd,url)=addurl(kv,shorturl,url,pwd,web.ctx.ip,choose)#('','errinfo','url') or ('surl',pwd,'url')
        if surl=='':
            pwd=infof[pwd]#pwd now is error info
            return json.dumps({'ok':0,'errinfo':pwd})
        return json.dumps({'ok':1,'pwd':pwd,'surl':surl})
class Checklink:
    #AJAX
    def GET(self):
        url=web.input(url='').url
        (a,b)=checksurl(kv,url)#(0,'errorinfo') or (1,'url')
        if a==0:
            b=infof[b]
        return json.dumps({'ok':a,'url':b})
class Checktextpwd:
    def POST(self):
        data=web.input(surl='',pwd='')
        surl=data.surl
        pwd=data.pwd
        link=kv.get('l'+surl) or ''
        returndata={}
        if link=='':#链接不存在
            returndata['ok']=0
            returndata['errinfo']="Text does not exist!"
        else:#存在该链接
            link=json.loads(link)
            if link['p']==pwd and pwd!='':
                returndata['ok']=1
            else:
                returndata['ok']=0
                returndata['errinfo']="Password is not correct."
        return json.dumps(returndata)

class About:
    def GET(self):
        alllink=kv.get('calllink') or 0
        allclick=kv.get('callclick') or 0
        return render.about(alllink,allclick)
class Jump:
    def GET(self,arg):
        if arg.find('?')!=-1:
            arg=arg[:arg.find('?')]#过滤参数
        link=kv.get('l'+arg) or ''
        alllink=kv.get('calllink') or 0
        allclick=kv.get('callclick') or 0
        if link=='':#链接不存在
            return render.home(alllink,allclick,infof['nolink'])#output error info
        else:#存在该链接
            link=json.loads(link)
            addcount(kv,'click',[arg,link])#新增链接统计
            if link.has_key('type') and link['type']!='url':
                return render.showtext(link['c'],arg,alllink,allclick)#显示文本.参数：点击量,短网址,总链接数,总点击数
            else:
                raise web.seeother(link['u'])#跳转
class Er:
    def GET(self):
        alllink=kv.get('calllink') or 0
        allclick=kv.get('callclick') or 0
        return render.home(alllink,allclick,infof['nolink'])#output error info
class Shownote:
    def GET(self):
        surl=web.input(url='').surl
        if surl.find('?')!=-1:
            surl=surl[:surl.find('?')]#过滤参数
        link=kv.get('l'+surl) or ''
        if link=='':#链接不存在
            return "No such thing."#output error info
        else:#存在该链接
            link=json.loads(link)
            #addcount(kv,'click',[surl,link])#新增链接统计-已计数，无需重复
            if link.has_key('type') and link['type']=='text':
                return link['u']

class Admin:
    def GET(self):
        users=list(kv.get_by_prefix('u',100,''))
        if len(users)==0:
            kv.add('uadmin','ihciah')#添加默认用户
        if session.login!=1:
            raise web.seeother('/login')
        else:
            alllink=kv.get('calllink') or 0
            allclick=kv.get('callclick') or 0


            return render.adminhome(session.id,alllink,allclick)#待修改，输出更多系统信息
    def POST(self):
        if session.login!=1:
            raise web.seeother('/login')
        else:
            data=web.input(action='')
            p=adminclass(data,kv)
            switch={'requestlink':p.requestlink,
                    'dellink':p.dellink,
                    'submitlink':p.submitlink,
                    'submitblacklist':p.submitblacklist,
                    'useredit':p.useredit,
                    'requestone':p.requestone,
                    'requestblack':p.requestblack,
                    'pwdsub':p.changepwd,
                    '':p.nope}
            return switch[data.action]()
class Test:
    def GET(self):
        pass
application = sae.create_wsgi_app(app.wsgifunc())