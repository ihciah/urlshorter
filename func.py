# -*- coding: utf-8 -*-
#!/usr/bin/env python
#
#__author__= 'ihciah@gmail.com'
#__author__= 'BaiduID-ihciah'
#__author__= 'http://www.ihcblog.com'
import web,time,string,json,re,random
blocklist=['admin','add','check','about','login','jump','index','default','help','logout','checktextpwd','shownote','home']
def en(x):
    if not isinstance(x, int) and x is not None:
        x=x.encode('utf-8')
    return x
class MemStore(web.session.Store):
    def __init__(self, memcache):
        self.mc = memcache
    def __contains__(self, key):
        data = self.mc.get(key)
        return bool(data)
    def __getitem__(self, key):
        now = time.time()
        value = self.mc.get(key)
        if not value:
            raise KeyError
        else:
            value['attime'] = now
            self.mc.set(key,value)
            return value
    def __setitem__(self, key, value):
        now = time.time()
        value['attime'] = now
        s = self.mc.get(key)
        self.mc.set(key, value, web.config.session_parameters['timeout'])
    def __delitem__(self, key):
        self.mc.delete(key)
    def cleanup(self, timeout):
        pass
def addurl(kv,surl,url,pwd,ip,choose):
    rb=lambda x:x.replace(' ','')
    surl=rb(surl)
    #----------Check url if type is URL---------------------
    if choose=='url':
        url=rb(url).replace('\n','')
        n = re.match(r"\Ahttp://.*|\Ahttps://.*|\A.*",url.lower())
        if not n:
            return ('','formaterror',url)
        else:
            if not re.match(r"\Ahttp.*",url.lower()):
                url='http://'+url
    #-------------------------------------------------------
    #-----------Check short url or generate a new unique short url-----------
    if surl!='':
        if len(surl)>30:
            return ('','toolong',url)#maybe useless.Filter short url in Addlink class.
        if len(surl)<3:
            return ('','tooshort',url)
        if surl.lower() in blocklist:
            return ('','blocked',url)


    else:
        wordlist=string.ascii_lowercase+string.digits
        if random.choice([1,0,0])==1:
            wordlist=string.ascii_uppercase+string.digits
        surl=''
        while(not surl or kv.get('l'+surl) or surl.lower() in blocklist):
            surl=''
            for i in range(4):
                surl+=(random.choice(wordlist))
    #-------------------------------------------------------------------------
    #--------check url data key word---------
    bl=kv.get('cblacklist')
    if bl is None:
        kv.set('cblacklist','{"key":"epochtime.com"}') ##默认黑名单
        bl=kv.get('cblacklist')
    blist=json.loads(bl)['key'].split(',')
    for i in blist:
        if url.lower().find(i)!=-1:
            return ('','blockedv2',url)
    #---------------------------------------
    #---------Add data-----------
    if kv.get(en('l'+surl)):#short link exists
        d=json.loads(kv.get('l'+surl))
        if d['p']==pwd and pwd!='':#Entered right pwd and pwd is not NULL.
            kv.replace('l'+surl,json.dumps({'u':url,'i':ip,'p':pwd,'c':d['c'],'t':int(time.time()),'type':choose}))#Counter not changed.Change ip or save ip list as json?Maybe useless...
            return (surl,pwd,url)
        else:
            return ('','taken',url)
    else:#short link not exists
        addcount(kv,'link','')#link
        kv.add('l'+surl,json.dumps({'u':url,'i':ip,'p':pwd,'c':0,'t':int(time.time()),'type':choose}))
        return (surl,pwd,url)

def addcount(kv,linkorclick,data):#data=[surl,{'u':url...}]
    if linkorclick=='link':#link
        alllink=kv.get('calllink') or 0
        kv.set('calllink',alllink+1)
    else:
        if not isinstance(data[1]['c'], int):
            data[1]['c']=int(data[1]['c'].encode("utf-8"))
        data[1]['c']+=1
        kv.replace('l'+data[0],json.dumps(data[1]))
        allclick=kv.get('callclick') or 0
        kv.set('callclick',allclick+1)
def checksurl(kv,url):
    '''返回一个双元素列表
        首元素表示是否可行，第二个是原来的url(仅后缀)'''
    m = re.match(r"\A\w{3,30}\Z|\A\Z",url)
    if not m:
        return (0,'formaterror')#格式不对
    if url.lower() in blocklist:
        return (0,'blocked')#封禁列表
    if kv.get('l'+url):
        return (0,'taken')#已占用
    else:
        return (1,url)
class adminclass():
    def __init__(self,data,kv):
        self.data=data
        self.kv=kv
    def requestlink(self):
        r={}
        perfix='l'
        li=[]
        limit=100
        marker='l'+self.data.marker
        link=self.kv.get_by_prefix(perfix,limit,marker)
        if link is not None:
            liori=list(link)
            li=[{'k':i[0][1:],'v':i[1]} for i in liori]#去掉key中的l，并返回字典的列表[{k:aaa,v:{json}},{k:aaa,v:{json}}]
            r['ok']=1
            r['result']=li
        else:
            r['ok']=0
            r['errinfo']='Error when fetching data.'
        return json.dumps(r)
    def requestone(self):
        link=self.kv.get('l'+self.data.k)
        r={}
        if link is not None:
            r['ok']=1
            r['result']=link
        else:
            r['ok']=0
            r['errinfo']='Error when fetching data.'
        return json.dumps(r)
    def requestblack(self):
        link=self.kv.get('cblacklist')#{'key':'aa,bb,cc'}
        if link is None:
            self.kv.set('cblacklist','{"key":"epochtime.com"}') ##默认黑名单
            link=self.kv.get('cblacklist')
        r={}
        if link is not None:
            r['ok']=1
            r['result']=link
        else:
            r['ok']=0
            r['errinfo']='Error when fetching data.'
        return json.dumps(r)
    def dellink(self):
        perfix=self.data.perfix
        self.kv.delete('l'+perfix)
        alllink=self.kv.get('calllink') or 0
        self.kv.set('calllink',alllink-1)#统计数自减1
        r={}
        r['ok']=1
        return json.dumps(r)
    def changepwd(self):
        oldpwd=self.data.oldpwd
        uid=self.data.uid
        newpwd=self.data.newpwd
        if newpwd=='':
            newpwd='none'#防止提交空密码
        link=self.kv.get('u'+uid) or ''
        r={}
        r['ok']=0
        if link=='':
            r['errinfo']='User does not exist.'
        elif link!=oldpwd:
            r['errinfo']='Old password is not correct.Please try again.'
        else:
            self.kv.replace('u'+uid,newpwd)
            r['ok']=1
        return json.dumps(r)
    def submitlink(self):
        perfix=self.data.perfix
        jsondata=self.data.jsondata #直接存入
        self.kv.replace('l'+perfix,jsondata)
        r={}
        r['ok']=1
        return json.dumps(r)
    def submitblacklist(self):
        blacklist=self.data.wordlist #json格式,直接存入数据库{'key':'aa,bb,cc'}
        self.kv.set('cblacklist',blacklist)
        r={}
        r['ok']=1
        return json.dumps(r)
    def useredit(self):
        user=self.data.user#json格式{uid:xx,pwd:xx}
        userl=json.loads(user)
        username=userl['uid']
        pwd=userl['pwd']
        r={}
        r['ok']=1
        if pwd=='del':
            self.kv.delete('u'+user)#密码为del时删除该用户
            r['info']="User deleted."
        elif pwd!='':
            self.kv.replace('u'+user,pwd)
            r['info']="Password changed."
        else:
            r['info']="Password not changed - pwd is NULL"
        return json.dumps(r)
    def nope(self):
        r={}
        r['ok']=0
        r['errinfo']='Error Command:Nope'
        return json.dumps(r)